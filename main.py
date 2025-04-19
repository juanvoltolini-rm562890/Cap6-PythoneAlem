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
import signal
import sys
import threading
from datetime import datetime
from typing import Optional

from src.actuators.controller import DeviceController
from src.core.control import EnvironmentController
from src.core.display import DisplayManager
from src.models.config import EnvironmentalLimits, SystemConfig
from src.sensors.reader import ReadingBuffer, SensorReader
from src.storage.file_storage import FileStorage
from src.storage.oracle_db import OracleStorage

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("aviary_control.log"),
    ],
)

logger = logging.getLogger(__name__)


class AviaryControlSystem:
    """Classe principal do controlador do sistema."""

    def __init__(self, config_path: Optional[str] = None):
        """Inicializa o sistema de controle.

        Args:
            config_path: Caminho opcional para o arquivo de configuração
        """
        # Inicializar armazenamento
        self.file_storage = FileStorage("data")
        self.oracle_storage = None  # Será inicializado se as credenciais forem fornecidas

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
        if self.oracle_storage:
            try:
                self.oracle_storage.store_reading(reading)
            except Exception as e:
                logger.error(f"Falha ao armazenar leitura no banco de dados: {e}")

        # Processar leitura e atualizar dispositivos
        try:
            device_status = self.environment_controller.process_reading(reading)
            action = self.environment_controller.get_last_action()

            # Registrar status dos dispositivos
            for device_id, status in device_status:
                self.file_storage.log_device_status(status)
                if self.oracle_storage:
                    try:
                        self.oracle_storage.store_device_status(status)
                    except Exception as e:
                        logger.error(f"Falha ao armazenar status do dispositivo: {e}")

            # Registrar alarmes
            if action and action.alarm_message:
                self.file_storage.log_alarm(action.alarm_message)
                if self.oracle_storage:
                    try:
                        self.oracle_storage.store_alarm(
                            datetime.now(),
                            "AMBIENTAL",
                            action.alarm_message,
                        )
                    except Exception as e:
                        logger.error(f"Falha ao armazenar alarme: {e}")

            # Atualizar display
            self.display_manager.update(reading, action, [s for _, s in device_status])

        except Exception as e:
            logger.error(f"Erro ao processar leitura: {e}")

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

    def configure_oracle(self, username: str, password: str, host: str):
        """Configura a conexão com o banco de dados Oracle.

        Args:
            username: Nome de usuário do banco de dados
            password: Senha do banco de dados
            host: Host do banco de dados
        """
        try:
            self.oracle_storage = OracleStorage(username, password, host)
            self.oracle_storage.connect()
            logger.info("Conexão com banco de dados Oracle configurada")
        except Exception as e:
            logger.error(f"Falha ao configurar conexão Oracle: {e}")
            self.oracle_storage = None


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
    args = parser.parse_args()

    # Inicializar sistema
    system = AviaryControlSystem(args.config)

    # Configurar Oracle se as credenciais forem fornecidas
    if all([args.oracle_user, args.oracle_password, args.oracle_host]):
        system.configure_oracle(
            args.oracle_user,
            args.oracle_password,
            args.oracle_host,
        )

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


