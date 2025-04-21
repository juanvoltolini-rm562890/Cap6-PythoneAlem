import logging
import sys
import traceback
from datetime import datetime
from unittest.mock import MagicMock, patch

import oracledb

from db import config
from src.models.config import EnvironmentalLimits, SystemConfig
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

            self._connection = oracledb.connect(
                user=self.username,
                password=self.password,
                dsn=self.dsn,
            )

            # Obter informações da versão do banco de dados
            with self._connection.cursor() as cursor:
                cursor.execute("SELECT BANNER FROM V$VERSION")
                version_info = cursor.fetchone()
                if version_info:
                    logger.info(f"Conectado ao banco de dados Oracle: {version_info[0]}")
                else:
                    logger.info("Conectado ao banco de dados Oracle.")
                    
            # Verificar configurações da conexão
            logger.info(f"Configurações da conexão - Autocommit: {self._connection.autocommit}")
            
            # Tentar obter informações adicionais da conexão de forma segura
            try:
                if hasattr(self._connection, 'encoding'):
                    logger.info(f"Encoding da conexão: {self._connection.encoding}")
                else:
                    logger.info("Informação de encoding não disponível para este driver de banco de dados")
            except Exception as e:
                logger.debug(f"Não foi possível obter informações adicionais da conexão: {str(e)}")
            
        except oracledb.DatabaseError as e:
            error_obj, = e.args
            logger.error(f"Falha ao conectar ao banco de dados Oracle: Código de erro: {error_obj.code}, "
                        f"Mensagem: {error_obj.message}")
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
            raise
        except Exception as e:
            logger.error(f"Exceção inesperada ao testar conexão com o banco de dados: {str(e)}")
            logger.error(f"Tipo de exceção: {type(e).__name__}")
            logger.error(f"Stack trace: {traceback.format_exc()}")
            raise

    def _ensure_connection(self):
        """Garante que a conexão com o banco de dados está ativa."""
        try:
            if not self._connection:
                logger.info("Conexão não inicializada. Tentando estabelecer conexão...")
                self.connect()
            else:
                # Verificar se a conexão ainda está ativa
                try:
                    with self._connection.cursor() as cursor:
                        cursor.execute("SELECT 1 FROM DUAL")
                        if cursor.fetchone() is None:
                            logger.warning("Conexão existente não está respondendo. Reconectando...")
                            self.disconnect()
                            self.connect()
                except Exception as e:
                    logger.warning(f"Erro ao verificar conexão existente: {str(e)}. Tentando reconectar...")
                    self.disconnect()
                    self.connect()
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
                sensor_readings_seq.NEXTVAL,
                :timestamp,
                :temperature,
                :humidity,
                :co2_level,
                :ammonia_level,
                :pressure
            )
        """
        try:
            with self._connection.cursor() as cursor:
                logger.debug(f"Executando SQL para armazenar leitura: {sql}")
                cursor.execute(
                    sql,
                    {
                        "timestamp": reading.timestamp,
                        "temperature": reading.temperature,
                        "humidity": reading.humidity,
                        "co2_level": reading.co2_level,
                        "ammonia_level": reading.ammonia_level,
                        "pressure": reading.pressure,
                    },
                )
            self._connection.commit()
            logger.info(f"Leitura do sensor {reading.sensor_id} armazenada com sucesso.")
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
                actuator_status_seq.NEXTVAL,
                :timestamp,
                :device_type,
                :device_id,
                :status,
                :value
            )
        """
        try:
            with self._connection.cursor() as cursor:
                logger.debug(f"Executando SQL para armazenar status do dispositivo: {sql}")
                cursor.execute(
                    sql,
                    {
                        "timestamp": status.last_updated,
                        "device_type": status.device_type.name,
                        "device_id": status.device_id,
                        "status": status.state.name,
                        "value": status.value,
                    },
                )
            self._connection.commit()
            logger.info(f"Status do dispositivo {status.device_id} armazenado com sucesso.")
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
                alarm_events_seq.NEXTVAL,
                :timestamp,
                :event_type,
                'ERROR',
                :description
            )
        """
        try:
            with self._connection.cursor() as cursor:
                logger.debug(f"Executando SQL para armazenar alarme: {sql}")
                cursor.execute(
                    sql,
                    {
                        "timestamp": timestamp,
                        "event_type": event_type,
                        "description": description,
                    },
                )
            self._connection.commit()
            logger.info(f"Evento de alarme '{event_type}' armazenado com sucesso.")
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
            "alarm_events"
        ]
        
        table_status = {}
        
        try:
            logger.info("Verificando existência das tabelas no esquema do banco de dados...")
            self._ensure_connection()
            
            with self._connection.cursor() as cursor:
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
                            cursor.execute(
                                "SELECT column_name FROM user_tab_columns WHERE table_name = :table_name",
                                {"table_name": table.upper()}
                            )
                            columns = [row[0] for row in cursor.fetchall()]
                            logger.debug(f"Colunas da tabela {table}: {', '.join(columns)}")
                        else:
                            logger.warning(f"Tabela {table} NÃO encontrada no esquema")
                    except Exception as e:
                        logger.error(f"Erro ao verificar tabela {table}: {str(e)}")
                        table_status[table] = False
            
            # Verificar sequências
            required_sequences = [
                "sensor_readings_seq",
                "actuator_status_seq",
                "alarm_events_seq"
            ]
            
            for seq in required_sequences:
                try:
                    cursor.execute(
                        "SELECT COUNT(*) FROM user_sequences WHERE sequence_name = :seq_name",
                        {"seq_name": seq.upper()}
                    )
                    result = cursor.fetchone()
                    exists = result[0] > 0 if result else False
                    table_status[f"{seq}"] = exists
                    
                    if exists:
                        logger.info(f"Sequência {seq} encontrada no esquema")
                    else:
                        logger.warning(f"Sequência {seq} NÃO encontrada no esquema")
                except Exception as e:
                    logger.error(f"Erro ao verificar sequência {seq}: {str(e)}")
                    table_status[f"{seq}"] = False
                    
            return table_status
            
        except Exception as e:
            logger.error(f"Erro ao verificar esquema do banco de dados: {str(e)}")
            logger.error(f"Stack trace: {traceback.format_exc()}")
            return {table: False for table in required_tables}

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
            # Nota: Não estamos definindo o atributo encoding para simular o ambiente real
            
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

