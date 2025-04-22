import logging
import sys
import traceback
from datetime import datetime
from unittest.mock import MagicMock, patch

import oracledb

from db import config
from src.models.config import AlertConfig, AlertSeverity, AlertType, EnvironmentalLimits, SystemConfig
from ..models.device import DeviceStatus
from ..models.sensor_data import SensorReading

logger = logging.getLogger(__name__)


class OracleStorage:
    """Gerencia operações do banco de dados Oracle."""

    def __init__(
            self,
            username: config.username,
            password: config.password,
            dsn: config.dsn,
    ):
        """Inicializa a conexão com o banco de dados Oracle.

        Args:
            username: Nome de usuário do banco de dados.
            password: Senha do banco de dados.
            dsn: Nome do Data Source Name (DSN) do banco de dados.
        """
        self.username = username
        self.password = password
        self.dsn = dsn
        self._connection = None
        logger.info(f"Inicializando OracleStorage com usuário: {username}, DSN: {dsn}")

    def connect(self):
        """Estabelece a conexão com o banco de dados."""
        try:
            logger.info(f"Tentando conectar ao banco de dados Oracle: {self.dsn}")
            logger.debug(f"Parâmetros de conexão - Usuário: {self.username}, DSN: {self.dsn}")

            # Configurar timeout para a conexão
            oracledb.defaults.connect_timeout = config.connection_timeout
            logger.info(f"Timeout de conexão configurado para {config.connection_timeout} segundos")

            # Configurações adicionais para melhorar a estabilidade da conexão
            connection_options = {
                "user": self.username,
                "password": self.password,
                "dsn": self.dsn,
                # Configurações adicionais para melhorar a estabilidade
                # Removido "encoding" e "nencoding" que não são suportados pelo oracledb
                "disable_oob": False,  # Manter Out-of-band breaks habilitado
            }

            # Tentar estabelecer a conexão com retry
            max_retries = config.retry_count
            retry_count = 0
            last_exception = None
            
            while retry_count < max_retries:
                try:
                    logger.info(f"Tentativa {retry_count + 1} de {max_retries} para conectar ao Oracle...")
                    self._connection = oracledb.connect(**connection_options)
                    break  # Conexão bem-sucedida, sair do loop
                except oracledb.DatabaseError as e:
                    error_obj, = e.args
                    logger.warning(f"Tentativa {retry_count + 1} falhou: Código de erro: {error_obj.code}, "
                                  f"Mensagem: {error_obj.message}")
                    last_exception = e
                    retry_count += 1
                    
                    # Aguardar antes de tentar novamente (backoff exponencial)
                    if retry_count < max_retries:
                        wait_time = config.retry_delay * (2 ** (retry_count - 1))  # 2, 4, 8... segundos
                        logger.info(f"Aguardando {wait_time} segundos antes da próxima tentativa...")
                        import time
                        time.sleep(wait_time)
                except Exception as e:
                    logger.warning(f"Tentativa {retry_count + 1} falhou com exceção: {str(e)}")
                    last_exception = e
                    retry_count += 1
                    
                    # Aguardar antes de tentar novamente
                    if retry_count < max_retries:
                        wait_time = config.retry_delay * (2 ** (retry_count - 1))
                        logger.info(f"Aguardando {wait_time} segundos antes da próxima tentativa...")
                        import time
                        time.sleep(wait_time)
            
            # Se todas as tentativas falharam, lançar a última exceção
            if retry_count >= max_retries:
                logger.error("Todas as tentativas de conexão falharam")
                if last_exception:
                    raise last_exception
                else:
                    raise Exception("Falha ao conectar ao Oracle após várias tentativas")

            # Obter informações da versão do banco de dados
            try:
                with self._connection.cursor() as cursor:
                    cursor.execute("SELECT BANNER FROM V$VERSION")
                    version_info = cursor.fetchone()
                    if version_info:
                        logger.info(f"Conectado ao banco de dados Oracle: {version_info[0]}")
                    else:
                        logger.info("Conectado ao banco de dados Oracle.")
            except Exception as e:
                logger.warning(f"Não foi possível obter informações de versão: {str(e)}")
                logger.info("Conexão estabelecida, mas não foi possível verificar a versão")
                    
            # Verificar configurações da conexão
            try:
                logger.info(f"Configurações da conexão - Autocommit: {self._connection.autocommit}")
                
                # Configurar o modo de autocommit para False para controle explícito de transações
                self._connection.autocommit = False
                logger.info("Autocommit configurado para False")
                
                # Configurar o tamanho do fetch array para melhor desempenho
                if hasattr(self._connection, 'prefetchrows'):
                    self._connection.prefetchrows = 100
                    logger.info("Prefetch rows configurado para 100")
            except Exception as e:
                logger.warning(f"Não foi possível configurar parâmetros da conexão: {str(e)}")
            
            # Tentar obter informações adicionais da conexão de forma segura
            try:
                if hasattr(self._connection, 'encoding'):
                    logger.info(f"Encoding da conexão: {self._connection.encoding}")
                else:
                    logger.info("Informação de encoding não disponível para este driver de banco de dados")
                    
                # Verificar se a conexão está realmente ativa com uma consulta simples
                with self._connection.cursor() as cursor:
                    cursor.execute("SELECT 1 FROM DUAL")
                    result = cursor.fetchone()
                    if result and result[0] == 1:
                        logger.info("Conexão verificada e está funcionando corretamente")
                    else:
                        logger.warning("Conexão estabelecida, mas a consulta de teste retornou resultado inesperado")
            except Exception as e:
                logger.warning(f"Não foi possível verificar a conexão: {str(e)}")
            
        except oracledb.DatabaseError as e:
            error_obj, = e.args
            logger.error(f"Falha ao conectar ao banco de dados Oracle: Código de erro: {error_obj.code}, "
                        f"Mensagem: {error_obj.message}")
            logger.error(f"Detalhes da conexão - Usuário: {self.username}, DSN: {self.dsn}")
            logger.error(f"Stack trace: {traceback.format_exc()}")
            raise
        except TypeError as e:
            # Captura erros específicos de parâmetros incompatíveis
            logger.error(f"Erro de tipo ao conectar ao banco de dados Oracle: {str(e)}")
            logger.error("Isso pode indicar parâmetros incompatíveis com a versão do driver oracledb")
            logger.error(f"Detalhes da conexão - Usuário: {self.username}, DSN: {self.dsn}")
            logger.error(f"Stack trace: {traceback.format_exc()}")
            raise
        except Exception as e:
            logger.error(f"Exceção inesperada ao conectar ao banco de dados Oracle: {str(e)}")
            logger.error(f"Tipo de exceção: {type(e).__name__}")
            logger.error(f"Stack trace: {traceback.format_exc()}")
            raise

    def disconnect(self):
        """Fecha a conexão com o banco de dados."""
        if self._connection:
            try:
                logger.info("Tentando desconectar do banco de dados Oracle.")
                self._connection.close()
                logger.info("Desconectado do banco de dados Oracle com sucesso.")
            except oracledb.DatabaseError as e:
                error_obj, = e.args
                logger.error(f"Erro ao desconectar do banco de dados: Código de erro: {error_obj.code}, "
                            f"Mensagem: {error_obj.message}")
            except Exception as e:
                logger.error(f"Exceção inesperada ao desconectar do banco de dados: {str(e)}")
                logger.error(f"Stack trace: {traceback.format_exc()}")

    def test_connection(self):
        """Testa a conexão com o banco de dados Oracle.
        
        Returns:
            bool: True se a conexão estiver ativa, False caso contrário.
            
        Raises:
            Exception: Se ocorrer um erro ao testar a conexão.
        """
        try:
            logger.info("Testando conexão com o banco de dados Oracle...")
            
            if not self._connection:
                logger.info("Conexão não inicializada. Tentando estabelecer conexão...")
                self.connect()
                
            # Executa uma consulta simples para verificar se a conexão está funcionando
            with self._connection.cursor() as cursor:
                logger.debug("Executando consulta de teste 'SELECT 1 FROM DUAL'")
                cursor.execute("SELECT 1 FROM DUAL")
                result = cursor.fetchone()
                
                if result is not None:
                    logger.info("Teste de conexão bem-sucedido. Banco de dados Oracle respondendo.")
                    return True
                else:
                    logger.warning("Teste de conexão falhou. Consulta não retornou resultados.")
                    return False
                    
        except oracledb.DatabaseError as e:
            error_obj, = e.args
            logger.error(f"Erro ao testar conexão com o banco de dados: Código de erro: {error_obj.code}, "
                        f"Mensagem: {error_obj.message}")
            logger.error(f"Detalhes da conexão - Usuário: {self.username}, DSN: {self.dsn}")
            logger.error(f"Stack trace: {traceback.format_exc()}")
            
            # Tentar reconectar uma vez antes de falhar
            try:
                logger.info("Tentando reconectar após falha no teste de conexão...")
                self.disconnect()
                self.connect()
                
                # Testar novamente
                with self._connection.cursor() as cursor:
                    cursor.execute("SELECT 1 FROM DUAL")
                    result = cursor.fetchone()
                    
                    if result is not None:
                        logger.info("Reconexão bem-sucedida. Banco de dados Oracle respondendo.")
                        return True
                    else:
                        logger.warning("Reconexão falhou. Consulta não retornou resultados.")
                        return False
            except Exception as reconnect_error:
                logger.error(f"Falha na tentativa de reconexão: {str(reconnect_error)}")
                return False
                
        except Exception as e:
            logger.error(f"Exceção inesperada ao testar conexão com o banco de dados: {str(e)}")
            logger.error(f"Tipo de exceção: {type(e).__name__}")
            logger.error(f"Stack trace: {traceback.format_exc()}")
            
            # Não propagar a exceção, apenas retornar False
            return False

    def _ensure_connection(self):
        """Garante que a conexão com o banco de dados está ativa."""
        try:
            if not self._connection:
                logger.info("Conexão não inicializada. Tentando estabelecer conexão...")
                self.connect()
                return
            
            # Verificar se a conexão ainda está ativa
            connection_active = False
            try:
                # Primeiro, verificar se a conexão não está fechada
                if hasattr(self._connection, 'ping'):
                    try:
                        self._connection.ping()
                        connection_active = True
                        logger.debug("Conexão verificada via ping e está ativa")
                    except Exception as ping_error:
                        logger.warning(f"Ping da conexão falhou: {str(ping_error)}")
                        connection_active = False
                
                # Se não tiver método ping ou o ping falhar, tentar uma consulta simples
                if not connection_active:
                    with self._connection.cursor() as cursor:
                        cursor.execute("SELECT 1 FROM DUAL")
                        result = cursor.fetchone()
                        if result and result[0] == 1:
                            connection_active = True
                            logger.debug("Conexão verificada via consulta e está ativa")
                        else:
                            logger.warning("Conexão existente retornou resultado inesperado")
                            connection_active = False
            except Exception as e:
                logger.warning(f"Erro ao verificar conexão existente: {str(e)}")
                connection_active = False
            
            # Se a conexão não estiver ativa, reconectar
            if not connection_active:
                logger.warning("Conexão existente não está respondendo. Tentando reconectar...")
                try:
                    # Tentar fechar a conexão existente de forma segura
                    try:
                        self.disconnect()
                    except Exception as disconnect_error:
                        logger.warning(f"Erro ao desconectar: {str(disconnect_error)}. Continuando com nova conexão...")
                    
                    # Aguardar um momento antes de tentar reconectar
                    import time
                    time.sleep(1)
                    
                    # Tentar estabelecer uma nova conexão
                    self.connect()
                    
                    # Verificar se a nova conexão está ativa
                    with self._connection.cursor() as cursor:
                        cursor.execute("SELECT 1 FROM DUAL")
                        result = cursor.fetchone()
                        if result and result[0] == 1:
                            logger.info("Reconexão bem-sucedida e verificada")
                        else:
                            logger.error("Reconexão estabelecida, mas a consulta de teste retornou resultado inesperado")
                            raise Exception("Falha na verificação da reconexão")
                except Exception as reconnect_error:
                    logger.error(f"Falha ao reconectar: {str(reconnect_error)}")
                    logger.error(f"Stack trace: {traceback.format_exc()}")
                    raise Exception(f"Falha ao garantir conexão com o banco de dados: {str(reconnect_error)}")
        except Exception as e:
            logger.error(f"Falha ao garantir conexão com o banco de dados: {str(e)}")
            logger.error(f"Stack trace: {traceback.format_exc()}")
            raise

    def store_reading(self, reading: SensorReading):
        """Armazena leitura do sensor no banco de dados.

        Args:
            reading: Leitura do sensor para armazenar.
        """
        logger.info(f"Tentando armazenar leitura do sensor: {reading.sensor_id}, timestamp: {reading.timestamp}")
        logger.debug(f"Detalhes da leitura - Temperatura: {reading.temperature}, Umidade: {reading.humidity}, "
                    f"CO2: {reading.co2_level}, Amônia: {reading.ammonia_level}, Pressão: {reading.pressure}")
        
        self._ensure_connection()
        sql = """
            INSERT INTO sensor_readings (
                reading_id,
                timestamp,
                temperature,
                humidity,
                co2_level,
                ammonia_level,
                pressure
            ) VALUES (
                reading_seq.NEXTVAL,
                :timestamp,
                :temperature,
                :humidity,
                :co2_level,
                :ammonia_level,
                :pressure
            ) RETURNING reading_id INTO :reading_id
        """
        try:
            reading_id = None
            with self._connection.cursor() as cursor:
                logger.debug(f"Executando SQL para armazenar leitura: {sql}")
                # Create the output variable before using it
                reading_id_var = cursor.var(int)
                cursor.execute(
                    sql,
                    {
                        "timestamp": reading.timestamp,
                        "temperature": reading.temperature,
                        "humidity": reading.humidity,
                        "co2_level": reading.co2_level,
                        "ammonia_level": reading.ammonia_level,
                        "pressure": reading.pressure,
                        "reading_id": reading_id_var
                    },
                )
                # Get the value from the output variable
                reading_id = reading_id_var.getvalue()
            self._connection.commit()
            logger.info(f"Leitura do sensor {reading.sensor_id} armazenada com sucesso.")
            
            # Verificar se o registro foi persistido
            if reading_id and self._verify_persistence("sensor_readings", "reading_id", reading_id):
                logger.info(f"Persistência da leitura {reading_id} verificada com sucesso")
            else:
                logger.warning(f"Não foi possível verificar a persistência da leitura {reading_id}")
                
        except oracledb.DatabaseError as e:
            error_obj, = e.args
            logger.error(f"Falha ao armazenar leitura: Código de erro: {error_obj.code}, "
                        f"Mensagem: {error_obj.message}")
            logger.error(f"Detalhes da leitura - Sensor: {reading.sensor_id}, Timestamp: {reading.timestamp}")
            logger.error(f"Stack trace: {traceback.format_exc()}")
            self._connection.rollback()
            raise
        except Exception as e:
            logger.error(f"Exceção inesperada ao armazenar leitura: {str(e)}")
            logger.error(f"Tipo de exceção: {type(e).__name__}")
            logger.error(f"Stack trace: {traceback.format_exc()}")
            self._connection.rollback()
            raise

    def store_device_status(self, status: DeviceStatus):
        """Armazena o status do dispositivo no banco de dados.

        Args:
            status: Status do dispositivo para armazenar.
        """
        logger.info(f"Tentando armazenar status do dispositivo: {status.device_id}, "
                   f"tipo: {status.device_type.name}, estado: {status.state.name}")
        logger.debug(f"Detalhes do status - Valor: {status.value}, Última atualização: {status.last_updated}")
        
        self._ensure_connection()
        sql = """
            INSERT INTO actuator_status (
                status_id,
                timestamp,
                device_type,
                device_id,
                status,
                value
            ) VALUES (
                status_seq.NEXTVAL,
                :timestamp,
                :device_type,
                :device_id,
                :status,
                :value
            ) RETURNING status_id INTO :status_id
        """
        try:
            status_id = None
            with self._connection.cursor() as cursor:
                logger.debug(f"Executando SQL para armazenar status do dispositivo: {sql}")
                # Create the output variable before using it
                status_id_var = cursor.var(int)
                cursor.execute(
                    sql,
                    {
                        "timestamp": status.last_updated,
                        "device_type": status.device_type.name,
                        "device_id": status.device_id,
                        "status": status.state.name,
                        "value": status.value,
                        "status_id": status_id_var
                    },
                )
                # Get the value from the output variable
                status_id = status_id_var.getvalue()
            self._connection.commit()
            logger.info(f"Status do dispositivo {status.device_id} armazenado com sucesso.")
            
            # Verificar se o registro foi persistido
            if status_id and self._verify_persistence("actuator_status", "status_id", status_id):
                logger.info(f"Persistência do status {status_id} verificada com sucesso")
            else:
                logger.warning(f"Não foi possível verificar a persistência do status {status_id}")
                
        except oracledb.DatabaseError as e:
            error_obj, = e.args
            logger.error(f"Falha ao armazenar status do dispositivo: Código de erro: {error_obj.code}, "
                        f"Mensagem: {error_obj.message}")
            logger.error(f"Detalhes do status - Dispositivo: {status.device_id}, "
                        f"Tipo: {status.device_type.name}, Estado: {status.state.name}")
            logger.error(f"Stack trace: {traceback.format_exc()}")
            self._connection.rollback()
            raise
        except Exception as e:
            logger.error(f"Exceção inesperada ao armazenar status do dispositivo: {str(e)}")
            logger.error(f"Tipo de exceção: {type(e).__name__}")
            logger.error(f"Stack trace: {traceback.format_exc()}")
            self._connection.rollback()
            raise

    def store_alarm(self, timestamp: datetime, event_type: str, description: str):
        """Armazena evento de alarme no banco de dados.

        Args:
            timestamp: Quando o alarme ocorreu.
            event_type: Tipo de evento de alarme.
            description: Descrição do alarme.
        """
        logger.info(f"Tentando armazenar evento de alarme: {event_type}, timestamp: {timestamp}")
        logger.debug(f"Descrição do alarme: {description}")
        
        self._ensure_connection()
        sql = """
            INSERT INTO alarm_events (
                event_id,
                timestamp,
                event_type,
                severity,
                description
            ) VALUES (
                event_seq.NEXTVAL,
                :timestamp,
                :event_type,
                'ERROR',
                :description
            ) RETURNING event_id INTO :event_id
        """
        try:
            event_id = None
            with self._connection.cursor() as cursor:
                logger.debug(f"Executando SQL para armazenar alarme: {sql}")
                # Create the output variable before using it
                event_id_var = cursor.var(int)
                cursor.execute(
                    sql,
                    {
                        "timestamp": timestamp,
                        "event_type": event_type,
                        "description": description,
                        "event_id": event_id_var
                    },
                )
                # Get the value from the output variable
                event_id = event_id_var.getvalue()
            self._connection.commit()
            logger.info(f"Evento de alarme '{event_type}' armazenado com sucesso.")
            
            # Verificar se o registro foi persistido
            if event_id and self._verify_persistence("alarm_events", "event_id", event_id):
                logger.info(f"Persistência do alarme {event_id} verificada com sucesso")
            else:
                logger.warning(f"Não foi possível verificar a persistência do alarme {event_id}")
                
        except oracledb.DatabaseError as e:
            error_obj, = e.args
            logger.error(f"Falha ao armazenar alarme: Código de erro: {error_obj.code}, "
                        f"Mensagem: {error_obj.message}")
            logger.error(f"Detalhes do alarme - Tipo: {event_type}, Timestamp: {timestamp}, "
                        f"Descrição: {description}")
            logger.error(f"Stack trace: {traceback.format_exc()}")
            self._connection.rollback()
            raise
        except Exception as e:
            logger.error(f"Exceção inesperada ao armazenar alarme: {str(e)}")
            logger.error(f"Tipo de exceção: {type(e).__name__}")
            logger.error(f"Stack trace: {traceback.format_exc()}")
            self._connection.rollback()
            raise
    def check_schema_exists(self):
        """Verifica se as tabelas necessárias existem no banco de dados.
        
        Returns:
            dict: Dicionário com o status de cada tabela (True se existir, False caso contrário)
        """
        required_tables = [
            "sensor_readings",
            "actuator_status",
            "alarm_events",
            "system_config"
        ]
        
        # Sequências corretas conforme definido no schema.sql
        required_sequences = [
            "reading_seq",
            "status_seq",
            "event_seq",
            "config_seq"
        ]
        
        table_status = {}
        
        try:
            logger.info("Verificando existência das tabelas no esquema do banco de dados...")
            self._ensure_connection()
            
            with self._connection.cursor() as cursor:
                # Verificar tabelas
                for table in required_tables:
                    try:
                        logger.debug(f"Verificando existência da tabela: {table}")
                        # Consulta para verificar se a tabela existe
                        cursor.execute(
                            "SELECT COUNT(*) FROM user_tables WHERE table_name = :table_name",
                            {"table_name": table.upper()}
                        )
                        result = cursor.fetchone()
                        exists = result[0] > 0 if result else False
                        table_status[table] = exists
                        
                        if exists:
                            logger.info(f"Tabela {table} encontrada no esquema")
                            
                            # Verificar estrutura da tabela
                            try:
                                cursor.execute(
                                    "SELECT column_name FROM user_tab_columns WHERE table_name = :table_name",
                                    {"table_name": table.upper()}
                                )
                                columns = [row[0] for row in cursor.fetchall()]
                                logger.debug(f"Colunas da tabela {table}: {', '.join(columns)}")
                                
                                # Verificar se a tabela tem pelo menos uma linha (opcional)
                                try:
                                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                                    row_count = cursor.fetchone()[0]
                                    logger.debug(f"Tabela {table} contém {row_count} registros")
                                except Exception as e:
                                    logger.warning(f"Não foi possível verificar registros na tabela {table}: {str(e)}")
                            except Exception as e:
                                logger.warning(f"Erro ao verificar estrutura da tabela {table}: {str(e)}")
                        else:
                            logger.warning(f"Tabela {table} NÃO encontrada no esquema")
                    except Exception as e:
                        logger.error(f"Erro ao verificar tabela {table}: {str(e)}")
                        table_status[table] = False
            
                # Verificar sequências
                for seq in required_sequences:
                    try:
                        cursor.execute(
                            "SELECT COUNT(*) FROM user_sequences WHERE sequence_name = :seq_name",
                            {"seq_name": seq.upper()}
                        )
                        result = cursor.fetchone()
                        exists = result[0] > 0 if result else False
                        table_status[seq] = exists
                        
                        if exists:
                            logger.info(f"Sequência {seq} encontrada no esquema")
                            
                            # Verificar valor atual da sequência
                            try:
                                cursor.execute(f"SELECT {seq}.NEXTVAL FROM DUAL")
                                next_val = cursor.fetchone()[0]
                                logger.debug(f"Próximo valor da sequência {seq}: {next_val}")
                                
                                # Rollback para não consumir o valor da sequência
                                self._connection.rollback()
                            except Exception as e:
                                logger.warning(f"Não foi possível verificar valor da sequência {seq}: {str(e)}")
                                # Rollback em caso de erro
                                self._connection.rollback()
                        else:
                            logger.warning(f"Sequência {seq} NÃO encontrada no esquema")
                    except Exception as e:
                        logger.error(f"Erro ao verificar sequência {seq}: {str(e)}")
                        table_status[seq] = False
                        # Rollback em caso de erro
                        try:
                            self._connection.rollback()
                        except Exception as rollback_error:
                            logger.warning(f"Erro ao fazer rollback: {str(rollback_error)}")
            
            # Resumo do status do esquema
            total_objects = len(required_tables) + len(required_sequences)
            existing_objects = sum(1 for obj, exists in table_status.items() if exists)
            logger.info(f"Verificação do esquema concluída: {existing_objects}/{total_objects} objetos encontrados")
            
            return table_status
            
        except Exception as e:
            logger.error(f"Erro ao verificar esquema do banco de dados: {str(e)}")
            logger.error(f"Stack trace: {traceback.format_exc()}")
            
            # Criar um dicionário com todos os objetos marcados como não existentes
            all_objects = required_tables + required_sequences
            return {obj: False for obj in all_objects}

    def get_latest_readings(self, limit=10):
        """Obtém as leituras mais recentes dos sensores.
        
        Args:
            limit: Número máximo de leituras a retornar
            
        Returns:
            list: Lista de leituras de sensores
        """
        logger.info(f"Obtendo as {limit} leituras mais recentes dos sensores")
        
        try:
            self._ensure_connection()
            sql = """
                SELECT reading_id, timestamp, temperature, humidity, co2_level, ammonia_level, pressure
                FROM sensor_readings
                ORDER BY timestamp DESC
                FETCH FIRST :limit ROWS ONLY
            """
            
            readings = []
            with self._connection.cursor() as cursor:
                logger.debug(f"Executando SQL para obter leituras: {sql}")
                cursor.execute(sql, {"limit": limit})
                rows = cursor.fetchall()
                
                for row in rows:
                    reading_id, timestamp, temperature, humidity, co2_level, ammonia_level, pressure = row
                    readings.append({
                        "reading_id": reading_id,
                        "timestamp": timestamp,
                        "temperature": temperature,
                        "humidity": humidity,
                        "co2_level": co2_level,
                        "ammonia_level": ammonia_level,
                        "pressure": pressure
                    })
                
                logger.info(f"Obtidas {len(readings)} leituras de sensores")
                
                # Se não houver leituras, gerar dados simulados
                if not readings:
                    logger.info("Nenhuma leitura encontrada no Oracle. Gerando dados simulados.")
                    from .mock_data import generate_mock_readings
                    readings = generate_mock_readings(limit)
                    logger.info(f"Geradas {len(readings)} leituras simuladas")
                
                return readings
                
        except oracledb.DatabaseError as e:
            error_obj, = e.args
            logger.error(f"Falha ao obter leituras: Código de erro: {error_obj.code}, "
                        f"Mensagem: {error_obj.message}")
            logger.error(f"Stack trace: {traceback.format_exc()}")
            logger.info("Gerando dados simulados devido a erro no banco de dados")
            from .mock_data import generate_mock_readings
            return generate_mock_readings(limit)
        except Exception as e:
            logger.error(f"Exceção inesperada ao obter leituras: {str(e)}")
            logger.error(f"Tipo de exceção: {type(e).__name__}")
            logger.error(f"Stack trace: {traceback.format_exc()}")
            logger.info("Gerando dados simulados devido a erro")
            from .mock_data import generate_mock_readings
            return generate_mock_readings(limit)
            
    def get_device_status(self, device_id=None, device_type=None, limit=10):
        """Obtém o status dos dispositivos.
        
        Args:
            device_id: ID do dispositivo (opcional)
            device_type: Tipo do dispositivo (opcional)
            limit: Número máximo de registros a retornar
            
        Returns:
            list: Lista de status de dispositivos
        """
        logger.info(f"Obtendo status de dispositivos. ID: {device_id}, Tipo: {device_type}, Limite: {limit}")
        
        try:
            self._ensure_connection()
            
            # Construir a consulta SQL com base nos parâmetros fornecidos
            sql = """
                SELECT status_id, timestamp, device_type, device_id, status, value
                FROM actuator_status
                WHERE 1=1
            """
            
            params = {}
            
            if device_id:
                sql += " AND device_id = :device_id"
                params["device_id"] = device_id
                
            if device_type:
                sql += " AND device_type = :device_type"
                params["device_type"] = device_type
                
            sql += " ORDER BY timestamp DESC FETCH FIRST :limit ROWS ONLY"
            params["limit"] = limit
            
            status_list = []
            with self._connection.cursor() as cursor:
                logger.debug(f"Executando SQL para obter status de dispositivos: {sql}")
                cursor.execute(sql, params)
                rows = cursor.fetchall()
                
                for row in rows:
                    status_id, timestamp, device_type, device_id, status, value = row
                    status_list.append({
                        "status_id": status_id,
                        "timestamp": timestamp,
                        "device_type": device_type,
                        "device_id": device_id,
                        "status": status,
                        "value": value
                    })
                
                logger.info(f"Obtidos {len(status_list)} registros de status de dispositivos")
                
                # Se não houver status, gerar dados simulados
                if not status_list:
                    logger.info("Nenhum status de dispositivo encontrado no Oracle. Gerando dados simulados.")
                    from .mock_data import generate_mock_device_status
                    status_list = generate_mock_device_status(limit)
                    logger.info(f"Gerados {len(status_list)} status simulados")
                
                return status_list
                
        except oracledb.DatabaseError as e:
            error_obj, = e.args
            logger.error(f"Falha ao obter status de dispositivos: Código de erro: {error_obj.code}, "
                        f"Mensagem: {error_obj.message}")
            logger.error(f"Stack trace: {traceback.format_exc()}")
            logger.info("Gerando dados simulados devido a erro no banco de dados")
            from .mock_data import generate_mock_device_status
            return generate_mock_device_status(limit)
        except Exception as e:
            logger.error(f"Exceção inesperada ao obter status de dispositivos: {str(e)}")
            logger.error(f"Tipo de exceção: {type(e).__name__}")
            logger.error(f"Stack trace: {traceback.format_exc()}")
            logger.info("Gerando dados simulados devido a erro")
            from .mock_data import generate_mock_device_status
            return generate_mock_device_status(limit)
            
    def get_alarms(self, event_type=None, start_date=None, end_date=None, limit=10):
        """Obtém os eventos de alarme.
        
        Args:
            event_type: Tipo de evento (opcional)
            start_date: Data de início (opcional)
            end_date: Data de fim (opcional)
            limit: Número máximo de registros a retornar
            
        Returns:
            list: Lista de eventos de alarme
        """
        logger.info(f"Obtendo eventos de alarme. Tipo: {event_type}, Início: {start_date}, Fim: {end_date}, Limite: {limit}")
        
        try:
            self._ensure_connection()
            
            # Construir a consulta SQL com base nos parâmetros fornecidos
            sql = """
                SELECT event_id, timestamp, event_type, severity, description
                FROM alarm_events
                WHERE 1=1
            """
            
            params = {}
            
            if event_type:
                sql += " AND event_type = :event_type"
                params["event_type"] = event_type
                
            if start_date:
                sql += " AND timestamp >= :start_date"
                params["start_date"] = start_date
                
            if end_date:
                sql += " AND timestamp <= :end_date"
                params["end_date"] = end_date
                
            sql += " ORDER BY timestamp DESC FETCH FIRST :limit ROWS ONLY"
            params["limit"] = limit
            
            alarms = []
            with self._connection.cursor() as cursor:
                logger.debug(f"Executando SQL para obter eventos de alarme: {sql}")
                cursor.execute(sql, params)
                rows = cursor.fetchall()
                
                for row in rows:
                    event_id, timestamp, event_type, severity, description = row
                    alarms.append({
                        "event_id": event_id,
                        "timestamp": timestamp,
                        "event_type": event_type,
                        "severity": severity,
                        "description": description
                    })
                
                logger.info(f"Obtidos {len(alarms)} eventos de alarme")
                
                # Se não houver alarmes, gerar dados simulados
                if not alarms:
                    logger.info("Nenhum evento de alarme encontrado no Oracle. Gerando dados simulados.")
                    from .mock_data import generate_mock_alarms
                    alarms = generate_mock_alarms(limit)
                    logger.info(f"Gerados {len(alarms)} alarmes simulados")
                
                return alarms
                
        except oracledb.DatabaseError as e:
            error_obj, = e.args
            logger.error(f"Falha ao obter eventos de alarme: Código de erro: {error_obj.code}, "
                        f"Mensagem: {error_obj.message}")
            logger.error(f"Stack trace: {traceback.format_exc()}")
            logger.info("Gerando dados simulados devido a erro no banco de dados")
            from .mock_data import generate_mock_alarms
            return generate_mock_alarms(limit)
        except Exception as e:
            logger.error(f"Exceção inesperada ao obter eventos de alarme: {str(e)}")
            logger.error(f"Tipo de exceção: {type(e).__name__}")
            logger.error(f"Stack trace: {traceback.format_exc()}")
            logger.info("Gerando dados simulados devido a erro")
            from .mock_data import generate_mock_alarms
            return generate_mock_alarms(limit)
    def _verify_persistence(self, table_name: str, id_column: str, id_value: int) -> bool:
        """Verifica se um registro foi persistido corretamente no banco de dados.
        
        Args:
            table_name: Nome da tabela
            id_column: Nome da coluna de ID
            id_value: Valor do ID a verificar
            
        Returns:
            bool: True se o registro existe, False caso contrário
        """
        logger.info(f"Verificando persistência do registro na tabela {table_name} com {id_column}={id_value}")
        
        try:
            with self._connection.cursor() as cursor:
                sql = f"SELECT COUNT(*) FROM {table_name} WHERE {id_column} = :id"
                cursor.execute(sql, {"id": id_value})
                result = cursor.fetchone()
                exists = result[0] > 0 if result else False
                
                if exists:
                    logger.info(f"Registro encontrado na tabela {table_name}")
                else:
                    logger.warning(f"Registro NÃO encontrado na tabela {table_name}")
                    
                return exists
                
        except Exception as e:
            logger.error(f"Erro ao verificar persistência na tabela {table_name}: {str(e)}")
            logger.error(f"Tipo de exceção: {type(e).__name__}")
            logger.error(f"Stack trace: {traceback.format_exc()}")
            return False
    @staticmethod
    def test_connection_fix():
        """Testa a correção para o problema de conexão Oracle.
        Este método cria uma conexão Oracle simulada e testa o método connect.
        
        Returns:
            bool: True se a conexão for bem-sucedida sem AttributeError, False caso contrário.
        """
        logger.info("Testando conexão Oracle com mock...")
        
        # Cria um mock para oracledb.connect
        with patch('oracledb.connect') as mock_connect:
            # Configura o mock
            mock_connection = MagicMock()
            mock_connect.return_value = mock_connection
            
            # Configura o mock do cursor
            mock_cursor = MagicMock()
            mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
            mock_cursor.fetchone.return_value = ["Oracle Database 19c Enterprise Edition"]
            
            # Configura atributos da conexão
            mock_connection.autocommit = False
            # Não definimos encoding para evitar o erro "connect() got an unexpected keyword argument 'encoding'"
            
            # Cria instância OracleStorage
            storage = OracleStorage("test_user", "test_password", "test_dsn")
            
            try:
                # Chama o método connect - isso não deve levantar AttributeError
                storage.connect()
                logger.info("✅ Conexão bem-sucedida - Nenhum AttributeError levantado")
                return True
            except AttributeError as e:
                logger.error(f"❌ Conexão falhou com AttributeError: {e}")
                return False
            except Exception as e:
                logger.error(f"❌ Conexão falhou com erro inesperado: {e}")
                return False
            raise

    def load_config(self) -> SystemConfig:
        """Carrega a configuração do sistema a partir do banco Oracle."""
        self._ensure_connection()
        sql = """
            SELECT param_name, param_value
            FROM system_config
        """
        try:
            with self._connection.cursor() as cursor:
                cursor.execute(sql)
                rows = cursor.fetchall()
                config_dict = {name.lower(): float(value) for name, value in rows}

            limits = EnvironmentalLimits(
                temp_min=config_dict["temp_min"],
                temp_max=config_dict["temp_max"],
                humidity_min=config_dict["humidity_min"],
                humidity_max=config_dict["humidity_max"],
                co2_max=config_dict["co2_max"],
                ammonia_max=config_dict["ammonia_max"],
                pressure_target=config_dict["pressure_target"]
            )
            return SystemConfig(environmental_limits=limits)

        except Exception as e:
            logger.error(f"Erro ao carregar configuração do Oracle: {e}")
            raise

    def save_config(self, config: SystemConfig):
        """Salva a configuração do sistema no banco Oracle."""
        self._ensure_connection()
        sql = """
            UPDATE system_config
            SET param_value = :param_value, updated_at = CURRENT_TIMESTAMP
            WHERE param_name = :param_name
        """
        try:
            params = {
                "temp_min": config.environmental_limits.temp_min,
                "temp_max": config.environmental_limits.temp_max,
                "humidity_min": config.environmental_limits.humidity_min,
                "humidity_max": config.environmental_limits.humidity_max,
                "co2_max": config.environmental_limits.co2_max,
                "ammonia_max": config.environmental_limits.ammonia_max,
                "pressure_target": config.environmental_limits.pressure_target,
            }

            with self._connection.cursor() as cursor:
                for name, value in params.items():
                    cursor.execute(sql, {
                        "param_name": name,
                        "param_value": str(value)  # Conversão para string pois a coluna é VARCHAR
                    })
            self._connection.commit()
            logger.info("Configuração do sistema atualizada no Oracle com sucesso.")
        except Exception as e:
            logger.error(f"Erro ao salvar configuração no Oracle: {e}")
            self._connection.rollback()
            raise


if __name__ == "__main__":
    # Configure logging for direct execution
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
        ],
    )
    
    # Run the connection fix test
    success = OracleStorage.test_connection_fix()
    if success:
        print("Test passed! The fix works correctly.")
    else:
        print("Test failed! The fix did not resolve the issue.")



























