import os
import oracledb

# Credenciais do banco de dados
username = "rm563348"
password = "220982"
dsn = "oracle.fiap.com.br/orcl"
schema = "rm563348"

# Caminho do arquivo SQL
script_path = "db/schema.sql"

try:
    # Conectar ao banco de dados
    print("Conectando ao banco de dados...")
    connection = oracledb.connect(user=username, password=password, dsn=dsn)
    cursor = connection.cursor()

    # Ler o script SQL completo
    with open(script_path, "r") as file:
        sql_script = file.read()

    # Substituir o placeholder :SCHEMA pelo nome real do schema
    sql_script = sql_script.replace(":SCHEMA", schema)

    print("Executando o script...")

    # Executar os comandos SQL (dividindo por ;)
    for statement in sql_script.split(";"):
        if statement.strip():  # Ignorar instruções vazias
            try:
                cursor.execute(statement.strip())
                print(f"Executado: {statement.strip()[:50]}...")  # Log do comando
            except Exception as e:
                print(f"Erro ao executar: {statement.strip()[:50]}...")
                print(f"Detalhes: {e}")

    # Confirmar as alterações
    connection.commit()
    print("Todas as alterações foram salvas com sucesso.")

except Exception as e:
    print(f"Erro ao executar o script do banco de dados: {e}")

finally:
    # Fechar a conexão e o cursor
    if cursor:
        cursor.close()
    if connection:
        connection.close()
    print("Conexão ao banco de dados encerrada.")
