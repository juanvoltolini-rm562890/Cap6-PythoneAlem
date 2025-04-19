####################################
##### Arquivo: controller.py
##### Desenvolvedor: Juan F. Voltolini
##### Instituição: FIAP
##### Trabalho: Cap 6 - Python e Além
##### Grupo: Alexander Dorneles de Oliveira, Felipe Sabino da Silva, Juan Felipe Voltolini, Luiz Henrique Ribeiro de Oliveira e Marco Aurélio Eberhardt Assumpção, 
####################################

"""Controlador de dispositivos para gerenciar múltiplos atuadores.

Este módulo fornece controle centralizado e gerenciamento de todos os atuadores
no sistema de aviário.
"""
import logging
from typing import Dict, List, Optional, Tuple

from ..models.device import DeviceCommand, DeviceError, DeviceState, DeviceStatus, DeviceType
from .devices import Alarm, Curtain, ExhaustFan, Heater, Inlet, Nebulizer

logger = logging.getLogger(__name__)


class DeviceController:
    """Gerencia todos os atuadores no sistema."""

    def __init__(self):
        """Inicializa o controlador de dispositivos com dispositivos padrão."""
        # Inicializa ventiladores de exaustão
        self._fans: Dict[str, ExhaustFan] = {
            f"FAN{i:03d}": ExhaustFan(f"FAN{i:03d}") for i in range(1, 5)
        }

        # Inicializa cortinas
        self._curtains: Dict[str, Curtain] = {
            f"CUR{i:03d}": Curtain(f"CUR{i:03d}") for i in range(1, 3)
        }

        # Inicializa entradas de ar
        self._inlets: Dict[str, Inlet] = {
            f"INL{i:03d}": Inlet(f"INL{i:03d}") for i in range(1, 5)
        }

        # Inicializa aquecedores
        self._heaters: Dict[str, Heater] = {
            f"HTR{i:03d}": Heater(f"HTR{i:03d}") for i in range(1, 3)
        }

        # Inicializa nebulizadores
        self._nebulizers: Dict[str, Nebulizer] = {
            f"NEB{i:03d}": Nebulizer(f"NEB{i:03d}") for i in range(1, 3)
        }

        # Inicializa alarmes
        self._alarms: Dict[str, Alarm] = {
            "ALM001": Alarm("ALM001"),  # Alarme principal
            "ALM002": Alarm("ALM002"),  # Alarme de backup
        }

        # Busca combinada de dispositivos
        self._devices = {
            **self._fans,
            **self._curtains,
            **self._inlets,
            **self._heaters,
            **self._nebulizers,
            **self._alarms,
        }

    def get_device_status(self, device_id: str) -> Optional[DeviceStatus]:
        """Obtém o status atual de um dispositivo específico.

        Args:
            device_id: Identificador do dispositivo

        Returns:
            Optional[DeviceStatus]: Status do dispositivo ou None se não encontrado
        """
        device = self._devices.get(device_id)
        return device.status if device else None

    def get_all_status(self) -> List[DeviceStatus]:
        """Obtém o status atual de todos os dispositivos.

        Returns:
            List[DeviceStatus]: Lista de status de todos os dispositivos
        """
        return [device.status for device in self._devices.values()]

    def execute_command(self, command: DeviceCommand) -> DeviceStatus:
        """Executa um comando em um dispositivo específico.

        Args:
            command: Comando a ser executado

        Returns:
            DeviceStatus: Status atualizado do dispositivo

        Raises:
            DeviceError: Se o dispositivo não for encontrado ou o comando falhar
        """
        device = self._devices.get(command.device_id)
        if not device:
            raise DeviceError(command.device_id, "Dispositivo não encontrado")

        try:
            status = device.execute_command(command)
            logger.info(
                f"Comando executado em {command.device_id}: {command.action.name}"
                + (f" ({command.value}%)" if command.value is not None else "")
            )
            return status
        except Exception as e:
            logger.error(f"Comando falhou em {command.device_id}: {str(e)}")
            raise

    def set_fan_speeds(self, speed: float) -> List[Tuple[str, DeviceStatus]]:
        """Define a velocidade de todos os ventiladores de exaustão.

        Args:
            speed: Porcentagem da velocidade do ventilador (0-100)

        Returns:
            List[Tuple[str, DeviceStatus]]: Lista de tuplas (fan_id, status)
        """
        results = []
        for fan_id in self._fans:
            try:
                command = DeviceCommand(
                    device_id=fan_id,
                    action=DeviceState.PARTIAL,
                    value=speed,
                )
                status = self.execute_command(command)
                results.append((fan_id, status))
            except DeviceError as e:
                logger.error(f"Falha ao definir ventilador {fan_id}: {e}")
                results.append((fan_id, self._fans[fan_id].status))
        return results

    def set_curtain_positions(self, position: float) -> List[Tuple[str, DeviceStatus]]:
        """Define a posição de todas as cortinas.

        Args:
            position: Porcentagem da posição da cortina (0-100)

        Returns:
            List[Tuple[str, DeviceStatus]]: Lista de tuplas (curtain_id, status)
        """
        results = []
        for curtain_id in self._curtains:
            try:
                command = DeviceCommand(
                    device_id=curtain_id,
                    action=DeviceState.PARTIAL,
                    value=position,
                )
                status = self.execute_command(command)
                results.append((curtain_id, status))
            except DeviceError as e:
                logger.error(f"Falha ao definir cortina {curtain_id}: {e}")
                results.append((curtain_id, self._curtains[curtain_id].status))
        return results

    def set_inlet_positions(self, position: float) -> List[Tuple[str, DeviceStatus]]:
        """Define a posição de todas as entradas de ar.

        Args:
            position: Porcentagem da posição da entrada (0-100)

        Returns:
            List[Tuple[str, DeviceStatus]]: Lista de tuplas (inlet_id, status)
        """
        results = []
        for inlet_id in self._inlets:
            try:
                command = DeviceCommand(
                    device_id=inlet_id,
                    action=DeviceState.PARTIAL,
                    value=position,
                )
                status = self.execute_command(command)
                results.append((inlet_id, status))
            except DeviceError as e:
                logger.error(f"Failed to set inlet {inlet_id}: {e}")
                results.append((inlet_id, self._inlets[inlet_id].status))
        return results

    def set_heaters(self, state: DeviceState) -> List[Tuple[str, DeviceStatus]]:
        """Set all heaters to specified state.

        Args:
            state: Target state (ON/OFF only)

        Returns:
            List[Tuple[str, DeviceStatus]]: List of (heater_id, status) tuples
        """
        if state == DeviceState.PARTIAL:
            raise ValueError("Heaters only support ON/OFF states")

        results = []
        for heater_id in self._heaters:
            try:
                command = DeviceCommand(device_id=heater_id, action=state)
                status = self.execute_command(command)
                results.append((heater_id, status))
            except DeviceError as e:
                logger.error(f"Failed to set heater {heater_id}: {e}")
                results.append((heater_id, self._heaters[heater_id].status))
        return results

    def set_nebulizers(self, state: DeviceState) -> List[Tuple[str, DeviceStatus]]:
        """Set all nebulizers to specified state.

        Args:
            state: Target state (ON/OFF only)

        Returns:
            List[Tuple[str, DeviceStatus]]: List of (nebulizer_id, status) tuples
        """
        if state == DeviceState.PARTIAL:
            raise ValueError("Nebulizers only support ON/OFF states")

        results = []
        for nebulizer_id in self._nebulizers:
            try:
                command = DeviceCommand(device_id=nebulizer_id, action=state)
                status = self.execute_command(command)
                results.append((nebulizer_id, status))
            except DeviceError as e:
                logger.error(f"Failed to set nebulizer {nebulizer_id}: {e}")
                results.append((nebulizer_id, self._nebulizers[nebulizer_id].status))
        return results

    def trigger_alarm(self, message: str) -> List[Tuple[str, DeviceStatus]]:
        """Activate all alarms with specified message.

        Args:
            message: Alarm message to display

        Returns:
            List[Tuple[str, DeviceStatus]]: List of (alarm_id, status) tuples
        """
        results = []
        for alarm_id, alarm in self._alarms.items():
            try:
                alarm.set_message(message)
                command = DeviceCommand(device_id=alarm_id, action=DeviceState.ON)
                status = self.execute_command(command)
                results.append((alarm_id, status))
            except DeviceError as e:
                logger.error(f"Failed to trigger alarm {alarm_id}: {e}")
                results.append((alarm_id, alarm.status))
        return results

    def clear_alarms(self) -> List[Tuple[str, DeviceStatus]]:
        """Deactivate all alarms.

        Returns:
            List[Tuple[str, DeviceStatus]]: List of (alarm_id, status) tuples
        """
        results = []
        for alarm_id, alarm in self._alarms.items():
            try:
                alarm.set_message(None)
                command = DeviceCommand(device_id=alarm_id, action=DeviceState.OFF)
                status = self.execute_command(command)
                results.append((alarm_id, status))
            except DeviceError as e:
                logger.error(f"Failed to clear alarm {alarm_id}: {e}")
                results.append((alarm_id, alarm.status))
        return results











