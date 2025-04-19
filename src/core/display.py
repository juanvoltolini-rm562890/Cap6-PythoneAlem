####################################
##### Arquivo: nome_do_arquivo
##### Desenvolvedor: Juan F. Voltolini
##### Instituição: FIAP
##### Trabalho: Cap 6 - Python e Além
##### Grupo: Alexander Dorneles de Oliveira, Felipe Sabino da Silva, Juan Felipe Voltolini, Luiz Henrique Ribeiro de Oliveira e Marco Aurélio Eberhardt Assumpção, 
####################################

"""Gerenciamento de exibição para interface do sistema.

Este módulo lida com a exibição do status do sistema e leituras de sensores
nas interfaces LCD e CLI.
"""
import enum
import logging
import os
import time
from datetime import datetime
from typing import List, Optional

from ..models.device import DeviceStatus
from ..models.sensor_data import SensorReading
from .control import ControlAction

logger = logging.getLogger(__name__)


class DisplayMode(enum.Enum):
    """Modos de exibição do sistema."""
    STATUS = "status"  # Modo de exibição de status normal
    MENU = "menu"     # Modo de menu interativo


class DisplayManager:
    """Gerencia a saída de exibição do sistema."""

    def __init__(self, use_lcd: bool = True):
        """Inicializa o gerenciador de exibição.

        Args:
            use_lcd: Indica se deve tentar usar a saída de exibição LCD
        """
        self.use_lcd = use_lcd
        self._last_reading: Optional[SensorReading] = None
        self._last_action: Optional[ControlAction] = None
        self._last_devices: List[DeviceStatus] = []
        self._display_mode = DisplayMode.STATUS
        self._update_enabled = True

    def set_display_mode(self, mode: DisplayMode):
        """Define o modo de exibição atual.

        Args:
            mode: Novo modo de exibição
        """
        self._display_mode = mode
        if mode == DisplayMode.MENU:
            self._update_enabled = False
        else:
            self._update_enabled = True
            self._update_cli()  # Atualiza imediatamente ao sair do menu

    def enable_updates(self):
        """Habilita atualizações de exibição."""
        self._update_enabled = True

    def disable_updates(self):
        """Desabilita atualizações de exibição."""
        self._update_enabled = False

    def update(
        self,
        reading: Optional[SensorReading] = None,
        action: Optional[ControlAction] = None,
        devices: Optional[List[DeviceStatus]] = None,
    ):
        """Atualiza a exibição com novos dados.

        Args:
            reading: Leitura atual do sensor
            action: Ação de controle atual
            devices: Status atuais dos dispositivos
        """
        if reading:
            self._last_reading = reading
        if action:
            self._last_action = action
        if devices:
            self._last_devices = devices

        if self.use_lcd:
            self._update_lcd()
        if self._update_enabled and self._display_mode == DisplayMode.STATUS:
            self._update_cli()

    def _update_lcd(self):
        """Atualiza a exibição LCD com os dados atuais.

        Nota: Esta é uma implementação simulada. Em um sistema real,
        isso faria interface com hardware LCD real.
        """
        if not self._last_reading:
            return

        # Simulação de exibição LCD - na realidade, isso usaria hardware LCD
        lcd_lines = [
            f"T:{self._last_reading.temperature:4.1f}C  H:{self._last_reading.humidity:4.1f}%",
            f"CO2:{self._last_reading.co2_level:4.0f} NH3:{self._last_reading.ammonia_level:3.1f}",
            f"Pa:{self._last_reading.pressure:4.1f} {self._get_status_summary()}",
            f"{self._get_alarm_message() or 'System OK':20s}",
        ]

        logger.debug("Exibição LCD:")
        for line in lcd_lines:
            logger.debug(line)

    def _update_cli(self):
        """Atualiza a exibição CLI com os dados atuais."""
        # Limpa a tela
        os.system("cls" if os.name == "nt" else "clear")

        # Imprime o cabeçalho
        print("=" * 50)
        print("Status do Sistema de Controle do Aviário")
        print("=" * 50)
        print()

        # Imprime a hora atual
        print(f"Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()

        # Imprime leituras dos sensores
        if self._last_reading:
            print("Condições Ambientais:")
            print(f"  Temperatura: {self._last_reading.temperature:5.1f} °C")
            print(f"  Umidade:     {self._last_reading.humidity:5.1f} %")
            print(f"  CO2:         {self._last_reading.co2_level:5.0f} ppm")
            print(f"  Amônia:      {self._last_reading.ammonia_level:5.1f} ppm")
            print(f"  Pressão:     {self._last_reading.pressure:5.1f} Pa")
            print()

        # Imprime ações de controle
        if self._last_action:
            print("Ações de Controle:")
            print(f"  Velocidade do Ventilador:  {self._last_action.fan_speed:5.1f} %")
            print(f"  Posição da Cortina:        {self._last_action.curtain_position:5.1f} %")
            print(f"  Posição da Entrada de Ar:  {self._last_action.inlet_position:5.1f} %")
            print(f"  Aquecedores:               {'LIGADO' if self._last_action.heaters_on else 'DESLIGADO'}")
            print(f"  Nebulizadores:             {'LIGADO' if self._last_action.nebulizers_on else 'DESLIGADO'}")
            print()

        # Imprime resumo do status dos dispositivos
        if self._last_devices:
            print("Status dos Dispositivos:")
            for device in self._last_devices:
                status_text = (
                    f"{device.value:4.1f}%" if device.value is not None else device.state.name
                )
                print(f"  {device.device_id}: {status_text:8s}", end="")
                if device.error_message:
                    print(f" (ERRO: {device.error_message})")
                else:
                    print()
            print()

        # Imprime mensagem de alarme, se houver
        if self._last_action and self._last_action.alarm_message:
            print("!" * 50)
            print(f"ALARME: {self._last_action.alarm_message}")
            print("!" * 50)
            print()

    def _get_status_summary(self) -> str:
        """Obter um breve resumo do status para exibição LCD.

        Returns:
            str: Texto de resumo do status
        """
        if not self._last_action:
            return "ESPERA"

        if self._last_action.alarm_message:
            return "ALARME"
        elif self._last_action.heaters_on:
            return "AQUECENDO"
        elif self._last_action.fan_speed > 80:
            return "RESFRIANDO"
        elif self._last_action.nebulizers_on:
            return "NEBULIZANDO"
        else:
            return "NORMAL"

    def _get_alarm_message(self) -> Optional[str]:
        """Obter mensagem de alarme atual, se houver.

        Returns:
            Optional[str]: Mensagem de alarme ou None
        """
        return (
            self._last_action.alarm_message if self._last_action else None
        )


