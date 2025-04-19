####################################
##### Arquivo: device.py
##### Desenvolvedor: Juan F. Voltolini
##### Instituição: FIAP
##### Trabalho: Cap 6 - Python e Além
##### Grupo: Alexander Dorneles de Oliveira, Felipe Sabino da Silva, Juan Felipe Voltolini, Luiz Henrique Ribeiro de Oliveira e Marco Aurélio Eberhardt Assumpção, 
####################################

"""Modelos de dispositivos para controle de atuadores e rastreamento de status.

Este módulo define as estruturas de dados para representar e controlar vários
dispositivos no sistema de controle do aviário.
"""
from dataclasses import dataclass
from datetime import datetime
from enum import Enum, auto
from typing import Optional


class DeviceType(Enum):
    """Enumeração dos tipos de dispositivos disponíveis."""

    EXHAUST_FAN = auto()
    INLET = auto()
    CURTAIN = auto()
    HEATER = auto()
    NEBULIZER = auto()
    ALARM = auto()


class DeviceState(Enum):
    """Enumeração dos possíveis estados dos dispositivos."""

    OFF = auto()
    ON = auto()
    ERROR = auto()
    PARTIAL = auto()  # Para dispositivos com configurações variáveis


@dataclass
class DeviceStatus:
    """Represents the current status of a control device.

    Attributes:
        device_id: Unique identifier for the device
        device_type: Type of device (fan, curtain, etc.)
        state: Current operational state
        value: Optional value for variable devices (e.g., curtain position)
        last_updated: Timestamp of last status update
        error_message: Optional error description if state is ERROR
    """

    device_id: str
    device_type: DeviceType
    state: DeviceState
    value: Optional[float] = None
    last_updated: datetime = None
    error_message: Optional[str] = None

    def __post_init__(self):
        """Initialize timestamp if not provided and validate state."""
        if self.last_updated is None:
            self.last_updated = datetime.now()
        self._validate_status()

    def _validate_status(self):
        """Ensure device status is consistent."""
        if self.state == DeviceState.ERROR and not self.error_message:
            raise ValueError("Error state requires an error message")
        if self.state == DeviceState.PARTIAL and self.value is None:
            raise ValueError("Partial state requires a value")
        if self.value is not None and not 0 <= self.value <= 100:
            raise ValueError(f"Invalid device value: {self.value}")


@dataclass
class DeviceCommand:
    """Represents a command to be sent to a device.

    Attributes:
        device_id: Target device identifier
        action: Requested state change
        value: Optional value for variable devices
        timestamp: When the command was created
    """

    device_id: str
    action: DeviceState
    value: Optional[float] = None
    timestamp: datetime = None

    def __post_init__(self):
        """Initialize timestamp if not provided and validate command."""
        if self.timestamp is None:
            self.timestamp = datetime.now()
        self._validate_command()

    def _validate_command(self):
        """Ensure command is valid."""
        if self.action == DeviceState.PARTIAL and self.value is None:
            raise ValueError("Partial state command requires a value")
        if self.value is not None and not 0 <= self.value <= 100:
            raise ValueError(f"Invalid command value: {self.value}")


class DeviceError(Exception):
    """Custom exception for device-related errors."""

    def __init__(self, device_id: str, message: str):
        """Initialize with device ID and error message.

        Args:
            device_id: Identifier of the device that encountered an error
            message: Description of the error
        """
        self.device_id = device_id
        self.message = message
        super().__init__(f"Device {device_id}: {message}")



