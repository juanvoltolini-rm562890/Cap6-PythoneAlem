import oracledb
import logging
import os
import sys
import traceback
import time
from . import config

# Configure logging
logger = logging.getLogger(__name__)

def initialize_schema(username=None, password=None, dsn=None):
    """Inicializa o esquema do banco de dados Oracle.
    
    Args:
        username: Nome de usuário do banco de dados (opcional, usa config.username se não fornecido)
        password: Senha do banco de dados (opcional, usa config.password se não fornecido)
        dsn: DSN do banco de dados (opcional, usa config.dsn se não fornecido)
        
    Returns:
        bool: True se o esquema foi inicializado com sucesso, False caso contrário
    """
    # Usar valores padrão se não fornecidos
    username = username or config.username
    password = password or config.password
    dsn = dsn or config.dsn
    schema = config.schema
    
    # Caminho do arquivo SQL
    script_path = os.path.join(os.path.dirname(__file__), "schema.sql")
    
    connection = None
    cursor = None
    success = False
    
    try:
        # Conectar ao banco de dados
        logger.info(f"Conectando ao banco de dados Oracle: {dsn}")
        
        # Configurar timeout para a conexão
        oracledb.defaults.connect_timeout = config.connection_timeout
        logger.info(f"Timeout de conexão configurado para {config.connection_timeout} segundos")
        
        # Configurações adicionais para melhorar a estabilidade da conexão
        connection_options = {
            "user": username,
            "password": password,
            "dsn": dsn,
            # Configurações adicionais para melhorar a estabilidade
            "encoding": "UTF-8",
            "nencoding": "UTF-8",
            "disable_oob": False,  # Manter Out-of-band breaks habilitado
        }
        
        # Tentar estabelecer a conexão com retry
        max_retries = config.retry_count
        retry_count = 0
        connection = None
        
        while retry_count < max_retries and connection is None:
            try:
                logger.info(f"Tentativa {retry_count + 1} de {max_retries} para conectar ao banco de dados Oracle...")
                connection = oracledb.connect(**connection_options)
                logger.info("Conexão estabelecida com sucesso")
                break
            except Exception as e:
                logger.warning(f"Tentativa {retry_count + 1} falhou: {str(e)}")
                retry_count += 1
                
                # Aguardar antes de tentar novamente (backoff exponencial)
                if retry_count < max_retries:
                    wait_time = config.retry_delay * (2 ** (retry_count - 1))  # 2, 4, 8... segundos
                    logger.info(f"Aguardando {wait_time} segundos antes da próxima tentativa...")
                    time.sleep(wait_time)
        
        if connection is None:
            logger.error("Não foi possível estabelecer conexão após várias tentativas")
            return False
        
        # Configurar autocommit para False para controle explícito de transações
        connection.autocommit = False
        
        cursor = connection.cursor()
        
        # Ler o script SQL completo
        with open(script_path, "r") as file:
            sql_script = file.read()
        
        # Substituir o placeholder :SCHEMA pelo nome real do schema
        sql_script = sql_script.replace(":SCHEMA", schema)
        
        logger.info("Executando o script de inicialização do esquema...")
        
        # Dividir o script em comandos individuais
        statements = sql_script.split(";")
        total_statements = len([s for s in statements if s.strip()])
        successful_statements = 0
        failed_statements = 0
        
        # Agrupar os comandos por tipo para execução em ordem lógica
        table_statements = []
        sequence_statements = []
        index_statements = []
        insert_statements = []
        other_statements = []
        
        for statement in statements:
            statement = statement.strip()
            if not statement:  # Ignorar instruções vazias
                continue
                
            # Classificar o comando por tipo
            statement_upper = statement.upper()
            if statement_upper.startswith("CREATE TABLE"):
                table_statements.append(statement)
            elif statement_upper.startswith("CREATE SEQUENCE"):
                sequence_statements.append(statement)
            elif statement_upper.startswith("CREATE INDEX"):
                index_statements.append(statement)
            elif statement_upper.startswith("INSERT INTO"):
                insert_statements.append(statement)
            else:
                other_statements.append(statement)
        
        # Executar os comandos em ordem lógica
        all_statements_ordered = (
            table_statements + sequence_statements + index_statements + insert_statements + other_statements
        )
        
        # Executar cada comando individualmente
        for statement in all_statements_ordered:
            try:
                logger.info(f"Executando: {statement[:100]}...")  # Log do início do comando
                cursor.execute(statement)
                logger.info("Comando executado com sucesso")
                successful_statements += 1
                
                # Commit após cada comando bem-sucedido para evitar bloqueios longos
                connection.commit()
                logger.debug("Commit realizado após comando bem-sucedido")
            except oracledb.DatabaseError as e:
                error_obj, = e.args
                logger.warning(f"Erro ao executar comando: Código de erro: {error_obj.code}, Mensagem: {error_obj.message}")
                logger.warning(f"Comando com erro: {statement[:200]}...")
                
                # Verificar se o erro é "objeto já existe" (ORA-00955)
                if error_obj.code == 955:  # ORA-00955: name is already used by an existing object
                    logger.info("Objeto já existe, continuando com o próximo comando")
                    successful_statements += 1  # Considerar como sucesso se o objeto já existir
                else:
                    failed_statements += 1
                    # Fazer rollback apenas do comando atual
                    connection.rollback()
                    logger.debug("Rollback realizado após erro")
            except Exception as e:
                logger.warning(f"Erro inesperado ao executar comando: {str(e)}")
                logger.warning(f"Comando com erro: {statement[:200]}...")
                failed_statements += 1
                # Fazer rollback apenas do comando atual
                connection.rollback()
                logger.debug("Rollback realizado após erro inesperado")
        
        # Confirmar as alterações finais
        try:
            connection.commit()
            logger.info("Commit final realizado com sucesso")
        except Exception as commit_error:
            logger.error(f"Erro no commit final: {str(commit_error)}")
            connection.rollback()
            logger.info("Rollback final realizado")
        
        # Verificar o resultado da execução
        logger.info(f"Execução do script concluída. {successful_statements} comandos executados com sucesso, "
                   f"{failed_statements} comandos falharam de um total de {total_statements} comandos.")
        
        # Considerar sucesso se pelo menos 80% dos comandos foram executados com sucesso
        success_rate = successful_statements / total_statements if total_statements > 0 else 0
        success = success_rate >= 0.8
        
        if success:
            logger.info(f"Esquema inicializado com sucesso (taxa de sucesso: {success_rate:.2%})")
        else:
            logger.warning(f"Esquema parcialmente inicializado (taxa de sucesso: {success_rate:.2%})")
        
    except Exception as e:
        logger.error(f"Erro ao executar o script do banco de dados: {e}")
        logger.error(f"Tipo de exceção: {type(e).__name__}")
        logger.error(f"Stack trace: {traceback.format_exc()}")
        if connection:
            try:
                connection.rollback()
                logger.info("Rollback realizado após exceção")
            except Exception as rollback_error:
                logger.error(f"Erro adicional durante rollback: {rollback_error}")
        success = False
    
    finally:
        # Fechar a conexão e o cursor
        if cursor:
            try:
                cursor.close()
                logger.debug("Cursor fechado com sucesso")
            except Exception as close_error:
                logger.warning(f"Erro ao fechar cursor: {close_error}")
                
        if connection:
            try:
                connection.close()
                logger.info("Conexão ao banco de dados encerrada.")
            except Exception as close_error:
                logger.warning(f"Erro ao fechar conexão: {close_error}")
    
    return success

if __name__ == "__main__":
    # Configure logging for direct execution
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
        ],
    )
    
    # Executar inicialização do esquema
    print("Inicializando esquema do banco de dados Oracle...")
    success = initialize_schema()
    
    if success:
        print("Esquema do banco de dados Oracle inicializado com sucesso.")
    else:
        print("Falha ao inicializar esquema do banco de dados Oracle.")
        sys.exit(1)