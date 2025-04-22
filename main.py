####################################
##### Arquivo: main.py
##### Desenvolvedor: Juan F. Voltolini
##### Instituição: FIAP
##### Trabalho: Cap 6 - Python e Além
##### Grupo: Alexander Dorneles de Oliveira, Felipe Sabino da Silva, Juan Felipe Voltolini, Luiz Henrique Ribeiro de Oliveira e Marco Aurélio Eberhardt Assumpção, 
####################################

"""Ponto de entrada principal para o sistema de controle de aviário.

Este módulo fornece a interface de linha de comando e o loop principal
de controle para o sistema de controle ambiental do aviário.
"""
import argparse
import logging
import os
import signal
import sys
import threading
from datetime import datetime
from typing import Optional

from db import config
from src.actuators.controller import DeviceController
from src.core.control import EnvironmentController
from src.core.display import DisplayManager
from src.models.config import EnvironmentalLimits, SystemConfig
from src.sensors.reader import ReadingBuffer, SensorReader
from src.storage.file_storage import FileStorage
from src.storage.oracle_db import OracleStorage

# Ensure logs directory exists
os.makedirs("data/logs", exist_ok=True)

# Configure logging - only to file, no terminal output
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    handlers=[
        logging.FileHandler("data/logs/aviary_control.log"),
    ],
)

# Configure specific loggers
logging.getLogger('src.storage.oracle_db').setLevel(logging.DEBUG)

logger = logging.getLogger(__name__)


class AviaryControlSystem:
    """Classe principal do controlador do sistema."""

    def __init__(self, config_path: Optional[str] = None, use_oracle: bool = True, force_mock_data: bool = False):
        """Inicializa o sistema de controle.

        Args:
            config_path: Caminho opcional para o arquivo de configuração
            use_oracle: Se True, tenta inicializar o armazenamento Oracle com credenciais padrão
            force_mock_data: Se True, força o uso de dados simulados mesmo com Oracle disponível
        """
        # Inicializar armazenamento
        self.file_storage = FileStorage("data")
        self.oracle_storage = None
        self.using_mock_data = force_mock_data
        
        # Se forçar dados simulados, não tenta conectar ao Oracle
        if force_mock_data:
            logger.info("Uso de dados simulados forçado por configuração. Oracle Storage não será utilizado.")
            self.using_mock_data = True
            print("AVISO: Usando dados simulados conforme solicitado. Os dados NÃO serão persistidos no Oracle.")
        # Inicializar Oracle Storage com credenciais padrão se habilitado
        elif use_oracle:
            try:
                logger.info("Tentando inicializar Oracle Storage com credenciais padrão")
                print("Tentando conectar ao Oracle Database com credenciais padrão...")
                self.oracle_storage = OracleStorage(config.username, config.password, config.dsn)
                self.oracle_storage.connect()
                connection_ok = self.oracle_storage.test_connection()
                if connection_ok:
                    logger.info("Oracle Storage inicializado com sucesso")
                    print("Conexão com Oracle Database estabelecida com sucesso.")
                    # Verificar esquema
                    schema_status = self.oracle_storage.check_schema_exists()
                    logger.info(f"Status do esquema Oracle: {schema_status}")
                    
                    # Verificar se todas as tabelas existem
                    required_tables = ["sensor_readings", "actuator_status", "alarm_events", "system_config"]
                    all_tables_exist = all(schema_status.get(table, False) for table in required_tables)
                    
                    # Verificar se todas as sequências existem
                    required_sequences = ["reading_seq", "status_seq", "event_seq", "config_seq"]
                    all_sequences_exist = all(schema_status.get(seq, False) for seq in required_sequences)
                    
                    if not (all_tables_exist and all_sequences_exist):
                        missing_objects = [obj for obj in required_tables + required_sequences if not schema_status.get(obj, False)]
                        logger.warning(f"Esquema do banco de dados Oracle incompleto. Objetos ausentes: {', '.join(missing_objects)}")
                        print(f"AVISO: Esquema do banco de dados Oracle incompleto. Tentando criar...")
                        
                        # Tentar inicializar o esquema
                        try:
                            from db.setup_db import initialize_schema
                            schema_success = initialize_schema(config.username, config.password, config.dsn)
                            if schema_success:
                                print("Esquema do banco de dados Oracle criado com sucesso.")
                                self.using_mock_data = False
                            else:
                                print("ERRO: Falha ao criar esquema do banco de dados Oracle.")
                                print("      Os dados serão salvos localmente.")
                                self.using_mock_data = True
                        except Exception as e:
                            logger.error(f"Falha ao inicializar esquema: {e}")
                            print(f"ERRO: Falha ao criar esquema do banco de dados Oracle: {str(e)}")
                            print("      Os dados serão salvos localmente.")
                            self.using_mock_data = True
                    else:
                        print("Esquema do banco de dados Oracle verificado com sucesso.")
                        self.using_mock_data = False
                    
                    # Verificar se há dados reais ou se serão usados dados simulados
                    try:
                        readings = self.oracle_storage.get_latest_readings(1)
                        if not readings:
                            logger.info("Nenhum dado encontrado no Oracle. Serão usados dados simulados.")
                            print("AVISO: Nenhum dado encontrado no Oracle. Serão usados dados simulados inicialmente.")
                            self.using_mock_data = True
                        else:
                            logger.info(f"Dados encontrados no Oracle: {len(readings)} leituras.")
                            print(f"Dados encontrados no Oracle: {len(readings)} leituras.")
                            self.using_mock_data = False
                    except Exception as e:
                        logger.warning(f"Erro ao verificar dados no Oracle: {e}")
                        print(f"AVISO: Erro ao verificar dados no Oracle: {str(e)}")
                        print("       Serão usados dados simulados inicialmente.")
                        self.using_mock_data = True
                else:
                    logger.warning("Falha no teste de conexão com Oracle. Oracle Storage não será utilizado.")
                    print("ERRO: Falha no teste de conexão com Oracle Database.")
                    print("      Os dados serão salvos localmente.")
                    self.oracle_storage = None
                    self.using_mock_data = True
            except Exception as e:
                logger.warning(f"Não foi possível inicializar Oracle Storage: {e}")
                print(f"ERRO: Não foi possível conectar ao Oracle Database: {str(e)}")
                print("      Os dados serão salvos localmente.")
                self.oracle_storage = None
                self.using_mock_data = True
        else:
            logger.info("Oracle Storage desabilitado por configuração")
            print("Oracle Storage desabilitado por configuração. Os dados serão salvos localmente.")
            self.using_mock_data = True

        # Carregar ou criar configuração
        self.config = self._load_config(config_path)
        logger.info("Configuração do sistema carregada")

        # Inicializar componentes
        self.reading_buffer = ReadingBuffer()
        self.device_controller = DeviceController()
        self.environment_controller = EnvironmentController(
            self.device_controller,
            self.config.environmental_limits,
            self.reading_buffer,
        )
        self.display_manager = DisplayManager()
        self.sensor_reader = SensorReader(
            reading_interval=self.config.reading_interval,
            callback=self._handle_reading,
        )

        # Flags de controle
        self._running = False
        self._stop_event = threading.Event()

    def _load_config(self, config_path: Optional[str]) -> SystemConfig:
        """Carrega a configuração do sistema.

        Args:
            config_path: Caminho opcional para o arquivo de configuração

        Returns:
            SystemConfig: Configuração do sistema
        """
        if config_path:
            config = self.file_storage.load_config()
            if config:
                return config

        # Configuração padrão se nenhuma for carregada
        return SystemConfig(
            environmental_limits=EnvironmentalLimits(
                temp_min=18.0,
                temp_max=32.0,
                humidity_min=50.0,
                humidity_max=70.0,
                co2_max=2000.0,
                ammonia_max=25.0,
                pressure_target=25.0,
            )
        )

    def _handle_reading(self, reading):
        """Processa nova leitura do sensor.

        Args:
            reading: Nova leitura do sensor
        """
        # Armazenar leitura
        self.reading_buffer.add_reading(reading)
        self.file_storage.log_sensor_reading(reading)
        
        # Se estiver usando dados simulados, não tenta armazenar no Oracle
        if self.oracle_storage and not self.using_mock_data:
            try:
                logger.info(f"Tentando armazenar leitura do sensor {reading.sensor_id} no Oracle")
                self.oracle_storage.store_reading(reading)
                logger.info(f"Leitura do sensor {reading.sensor_id} armazenada com sucesso no Oracle")
            except Exception as e:
                logger.error(f"Falha ao armazenar leitura no banco de dados Oracle: {e}")
                logger.error(f"Detalhes da leitura - Sensor: {reading.sensor_id}, Timestamp: {reading.timestamp}")
                logger.error(f"Tipo de exceção: {type(e).__name__}")
                import traceback
                logger.error(f"Stack trace: {traceback.format_exc()}")
                
                # Exibir mensagem de erro para o usuário
                print(f"ERRO: Falha ao armazenar leitura no Oracle Database: {str(e)}")
                print("      Os dados continuarão sendo salvos localmente.")
                
                # Marcar para usar dados simulados após falha
                self.using_mock_data = True
        elif self.using_mock_data:
            logger.info(f"Usando dados simulados - leitura do sensor {reading.sensor_id} não será armazenada no Oracle")

        # Processar leitura e atualizar dispositivos
        try:
            device_status = self.environment_controller.process_reading(reading)
            action = self.environment_controller.get_last_action()

            # Registrar status dos dispositivos
            for device_id, status in device_status:
                self.file_storage.log_device_status(status)
                # Se estiver usando dados simulados, não tenta armazenar no Oracle
                if self.oracle_storage and not self.using_mock_data:
                    try:
                        logger.info(f"Tentando armazenar status do dispositivo {status.device_id} no Oracle")
                        self.oracle_storage.store_device_status(status)
                        logger.info(f"Status do dispositivo {status.device_id} armazenado com sucesso no Oracle")
                    except Exception as e:
                        logger.error(f"Falha ao armazenar status do dispositivo no Oracle: {e}")
                        logger.error(f"Detalhes do status - Dispositivo: {status.device_id}, "
                                    f"Tipo: {status.device_type.name}, Estado: {status.state.name}")
                        logger.error(f"Tipo de exceção: {type(e).__name__}")
                        import traceback
                        logger.error(f"Stack trace: {traceback.format_exc()}")
                        
                        # Exibir mensagem de erro para o usuário
                        print(f"ERRO: Falha ao armazenar status do dispositivo no Oracle Database: {str(e)}")
                        print("      Os dados continuarão sendo salvos localmente.")
                        
                        # Marcar para usar dados simulados após falha
                        self.using_mock_data = True
                elif self.using_mock_data:
                    logger.info(f"Usando dados simulados - status do dispositivo {status.device_id} não será armazenado no Oracle")

            # Registrar alarmes
            if action and action.alarm_message:
                self.file_storage.log_alarm(action.alarm_message)
                # Se estiver usando dados simulados, não tenta armazenar no Oracle
                if self.oracle_storage and not self.using_mock_data:
                    try:
                        logger.info(f"Tentando armazenar alarme no Oracle: {action.alarm_message}")
                        self.oracle_storage.store_alarm(
                            datetime.now(),
                            "AMBIENTAL",
                            action.alarm_message,
                        )
                        logger.info("Alarme armazenado com sucesso no Oracle")
                    except Exception as e:
                        logger.error(f"Falha ao armazenar alarme no Oracle: {e}")
                        logger.error(f"Detalhes do alarme - Mensagem: {action.alarm_message}")
                        logger.error(f"Tipo de exceção: {type(e).__name__}")
                        import traceback
                        logger.error(f"Stack trace: {traceback.format_exc()}")
                        
                        # Exibir mensagem de erro para o usuário
                        print(f"ERRO: Falha ao armazenar alarme no Oracle Database: {str(e)}")
                        print("      Os dados continuarão sendo salvos localmente.")
                        
                        # Marcar para usar dados simulados após falha
                        self.using_mock_data = True
                elif self.using_mock_data:
                    logger.info(f"Usando dados simulados - alarme não será armazenado no Oracle")

            # Atualizar display
            self.display_manager.update(reading, action, [s for _, s in device_status])

        except Exception as e:
            logger.error(f"Erro ao processar leitura: {e}")
            logger.error(f"Tipo de exceção: {type(e).__name__}")
            import traceback
            logger.error(f"Stack trace: {traceback.format_exc()}")
            
            # Exibir mensagem de erro para o usuário
            print(f"ERRO: Falha ao processar leitura do sensor: {str(e)}")

    def start(self):
        """Inicia o sistema de controle."""
        if self._running:
            logger.warning("Sistema já está em execução")
            return

        self._running = True
        self._stop_event.clear()
        self.sensor_reader.start()
        logger.info("Sistema de controle iniciado")

    def stop(self):
        """Para o sistema de controle."""
        if not self._running:
            return

        self._running = False
        self._stop_event.set()
        self.sensor_reader.stop()
        if self.oracle_storage:
            self.oracle_storage.disconnect()
        logger.info("Sistema de controle parado")

    def configure_oracle(self, username: str, password: str, host: str) -> bool:
        """Configura a conexão com o banco de dados Oracle.

        Args:
            username: Nome de usuário do banco de dados
            password: Senha do banco de dados
            host: Host do banco de dados
            
        Returns:
            bool: True se a conexão foi estabelecida com sucesso, False caso contrário
        """
        # Se estiver usando dados simulados, não configura Oracle
        if self.using_mock_data and self.oracle_storage is None:
            logger.info("Sistema configurado para usar dados simulados. Configuração Oracle ignorada.")
            return False
            
        try:
            logger.info(f"Iniciando configuração da conexão Oracle com host: {host}, usuário: {username}")
            
            # Se já existe uma conexão, desconectar primeiro
            if self.oracle_storage:
                try:
                    logger.info("Desconectando da conexão Oracle existente...")
                    self.oracle_storage.disconnect()
                except Exception as e:
                    logger.warning(f"Erro ao desconectar da conexão existente: {e}")
            
            # Criar nova instância do OracleStorage
            self.oracle_storage = OracleStorage(username, password, host)
            
            # Tenta estabelecer a conexão com retry
            max_retries = 3
            retry_count = 0
            connection_ok = False
            last_exception = None
            
            while retry_count < max_retries and not connection_ok:
                try:
                    logger.info(f"Tentativa {retry_count + 1} de {max_retries} para conectar ao banco de dados Oracle...")
                    self.oracle_storage.connect()
                    
                    # Testa a conexão para garantir que está funcionando
                    logger.info("Testando conexão com o banco de dados Oracle...")
                    connection_ok = self.oracle_storage.test_connection()
                    
                    if connection_ok:
                        logger.info("Teste de conexão bem-sucedido")
                        break
                    else:
                        logger.warning("Teste de conexão falhou. A conexão não está respondendo corretamente.")
                        last_exception = Exception("Conexão estabelecida, mas não está respondendo corretamente")
                    
                except Exception as e:
                    logger.warning(f"Tentativa {retry_count + 1} falhou: {str(e)}")
                    last_exception = e
                    
                # Incrementar contador de tentativas
                retry_count += 1
                
                # Aguardar antes de tentar novamente (backoff exponencial)
                if retry_count < max_retries and not connection_ok:
                    import time
                    wait_time = 2 * (2 ** (retry_count - 1))  # 2, 4, 8... segundos
                    logger.info(f"Aguardando {wait_time} segundos antes da próxima tentativa...")
                    time.sleep(wait_time)
            
            if connection_ok:
                logger.info("Conexão com banco de dados Oracle configurada e testada com sucesso")
                
                # Verificar se o esquema do banco de dados está correto
                logger.info("Verificando esquema do banco de dados Oracle...")
                schema_status = self.oracle_storage.check_schema_exists()
                
                # Verificar se todas as tabelas existem
                required_tables = ["sensor_readings", "actuator_status", "alarm_events", "system_config"]
                all_tables_exist = all(schema_status.get(table, False) for table in required_tables)
                
                # Verificar se todas as sequências existem
                required_sequences = ["reading_seq", "status_seq", "event_seq", "config_seq"]
                all_sequences_exist = all(schema_status.get(seq, False) for seq in required_sequences)
                
                if all_tables_exist and all_sequences_exist:
                    logger.info("Esquema do banco de dados Oracle verificado com sucesso")
                    # Desativa o uso de dados simulados, pois tudo está correto
                    self.using_mock_data = False
                    return True
                else:
                    missing_objects = [obj for obj in required_tables + required_sequences if not schema_status.get(obj, False)]
                    logger.warning(f"Esquema do banco de dados Oracle incompleto. Objetos ausentes: {', '.join(missing_objects)}")
                    logger.warning("As operações de banco de dados podem falhar devido ao esquema incompleto")
                    
                    # Tentar inicializar o esquema
                    try:
                        logger.info("Tentando inicializar o esquema do banco de dados Oracle...")
                        from db.setup_db import initialize_schema
                        schema_success = initialize_schema(username, password, host)
                        
                        if schema_success:
                            logger.info("Esquema do banco de dados Oracle inicializado com sucesso")
                            
                            # Verificar novamente o esquema
                            schema_status = self.oracle_storage.check_schema_exists()
                            all_tables_exist = all(schema_status.get(table, False) for table in required_tables)
                            all_sequences_exist = all(schema_status.get(seq, False) for seq in required_sequences)
                            
                            if all_tables_exist and all_sequences_exist:
                                logger.info("Esquema do banco de dados Oracle inicializado com sucesso")
                                # Desativa o uso de dados simulados, pois o esquema foi criado
                                self.using_mock_data = False
                                return True
                            else:
                                still_missing = [obj for obj in required_tables + required_sequences if not schema_status.get(obj, False)]
                                logger.warning(f"Esquema ainda incompleto após inicialização. Objetos ausentes: {', '.join(still_missing)}")
                                logger.warning("Não foi possível inicializar completamente o esquema do banco de dados Oracle")
                                # Como o esquema está incompleto, vamos usar dados simulados
                                self.using_mock_data = True
                                return False
                        else:
                            logger.error("Falha ao inicializar esquema do banco de dados Oracle")
                            # Como houve falha, vamos usar dados simulados
                            self.using_mock_data = True
                            return False
                    except Exception as e:
                        logger.error(f"Falha ao inicializar esquema do banco de dados Oracle: {e}")
                        logger.error(f"Tipo de exceção: {type(e).__name__}")
                        import traceback
                        logger.error(f"Stack trace: {traceback.format_exc()}")
                        # Como houve exceção, vamos usar dados simulados
                        self.using_mock_data = True
                        return False
            else:
                logger.warning("Conexão com banco de dados Oracle configurada, mas o teste de conexão falhou")
                if last_exception:
                    logger.error(f"Último erro encontrado: {str(last_exception)}")
                # Como a conexão falhou, vamos usar dados simulados
                self.using_mock_data = True
                logger.info("Usando dados simulados devido à falha na conexão")
                return False
                
        except Exception as e:
            logger.error(f"Falha ao configurar conexão Oracle: {e}")
            logger.error(f"Detalhes da conexão - Host: {host}, Usuário: {username}")
            logger.error(f"Tipo de exceção: {type(e).__name__}")
            import traceback
            logger.error(f"Stack trace: {traceback.format_exc()}")
            self.oracle_storage = None
            # Como houve exceção, vamos usar dados simulados
            self.using_mock_data = True
            logger.info("Usando dados simulados devido a erro na configuração Oracle")
            return False


def main():
    """Ponto de entrada principal."""
    parser = argparse.ArgumentParser(description="Sistema de Controle de Aviário")
    parser.add_argument(
        "--config",
        help="Caminho para o arquivo de configuração",
        default=None,
    )
    parser.add_argument(
        "--oracle-user",
        help="Nome de usuário do banco de dados Oracle",
        default=None,
    )
    parser.add_argument(
        "--oracle-password",
        help="Senha do banco de dados Oracle",
        default=None,
    )
    parser.add_argument(
        "--oracle-host",
        help="Host do banco de dados Oracle",
        default=None,
    )
    parser.add_argument(
        "--no-menu",
        action="store_true",
        help="Executar sem interface interativa",
    )
    parser.add_argument(
        "--no-oracle",
        action="store_true",
        help="Desabilitar conexão com banco de dados Oracle",
    )
    parser.add_argument(
        "--use-mock-data",
        action="store_true",
        help="Forçar o uso de dados simulados mesmo com Oracle disponível",
    )
    args = parser.parse_args()

    # Inicializar sistema
    use_oracle = not args.no_oracle
    force_mock_data = args.use_mock_data
    system = AviaryControlSystem(args.config, use_oracle=use_oracle, force_mock_data=force_mock_data)
    
    # Log do status do Oracle e dados simulados
    if system.oracle_storage and not system.using_mock_data:
        logger.info("Sistema inicializado com suporte a Oracle Database usando dados reais")
    elif system.oracle_storage and system.using_mock_data:
        logger.info("Sistema inicializado com suporte a Oracle Database mas usando dados simulados")
    else:
        logger.info("Sistema inicializado sem suporte a Oracle Database, usando dados simulados")

    # Configurar Oracle com credenciais específicas se fornecidas
    if all([args.oracle_user, args.oracle_password, args.oracle_host]) and not force_mock_data:
        logger.info("Reconfigurando Oracle com credenciais fornecidas via linha de comando")
        print(f"Configurando conexão com Oracle Database: {args.oracle_host}")
        connection_result = system.configure_oracle(
            args.oracle_user,
            args.oracle_password,
            args.oracle_host,
        )
        
        if not connection_result:
            print("ERRO: Não foi possível conectar ao Oracle Database. Os dados serão salvos localmente.")
            print("      Verifique suas credenciais e a disponibilidade do servidor Oracle.")
        elif system.using_mock_data:
            print("AVISO: Conectado ao Oracle Database, mas usando dados simulados.")
            print("       O esquema do banco de dados pode estar incompleto.")
        else:
            print("Conexão com Oracle Database estabelecida com sucesso.")
            print("Os dados serão persistidos no Oracle Database.")

    # Tratar desligamento graciosamente
    def signal_handler(signum, frame):
        logger.info("Sinal de desligamento recebido")
        system.stop()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Iniciar sistema
    try:
        system.start()
        
        logger.info(f"Menu flag status: no_menu = {args.no_menu}")
        if not args.no_menu:
            logger.info("Iniciando modo interativo com menu")
            # Inicializar e executar menu interativo
            from src.core.menu import MenuManager
            menu = MenuManager(
                system.config,
                system.file_storage,
                system.oracle_storage,
                system.display_manager,
                using_mock_data=system.using_mock_data
            )
            menu.display_menu()
            system.stop()
        else:
            logger.info("Iniciando modo não-interativo")
            # Modo não-interativo
            while True:
                signal.pause()
                
    except KeyboardInterrupt:
        system.stop()


if __name__ == "__main__":
    main()




























