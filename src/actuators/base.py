####################################
##### Arquivo: base.py
##### Desenvolvedor: Juan F. Voltolini
##### Instituição: FIAP
##### Trabalho: Cap 6 - Python e Além
##### Grupo: Alexander Dorneles de Oliveira, Felipe Sabino da Silva, Juan Felipe Voltolini, Luiz Henrique Ribeiro de Oliveira e Marco Aurélio Eberhardt Assumpção, 
####################################

"""Classes base para implementações de atuadores.

Este módulo fornece as classes base e interfaces para implementar
o controle de dispositivos no sistema de aviário.
"""
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional

from ..models.device import DeviceCommand, DeviceError, DeviceState, DeviceStatus, DeviceType


class BaseActuator(ABC):
    """Classe base abstrata para todos os atuadores."""

    def __init__(self, device_id: str, device_type: DeviceType):
        """Inicializa o atuador.

        Args:
            device_id: Identificador único para este dispositivo
            device_type: Tipo de dispositivo que este atuador controla
        """
        self.device_id = device_id
        self.device_type = device_type
        self._state = DeviceState.OFF
        self._value: Optional[float] = None
        self._error_message: Optional[str] = None
        self._last_updated = datetime.now()

    @property
    def status(self) -> DeviceStatus:
        """Obtém o status atual do dispositivo.

        Returns:
            DeviceStatus: Status atual do dispositivo
        """
        return DeviceStatus(
            device_id=self.device_id,
            device_type=self.device_type,
            state=self._state,
            value=self._value,
            last_updated=self._last_updated,
            error_message=self._error_message,
        )

    def execute_command(self, command: DeviceCommand) -> DeviceStatus:
        """Executa um comando do dispositivo.

        Args:
            command: Comando a ser executado

        Returns:
            DeviceStatus: Status atualizado do dispositivo

        Raises:
            DeviceError: Se a execução do comando falhar
        """
        if command.device_id != self.device_id:
            raise DeviceError(
                self.device_id, f"ID do dispositivo do comando não corresponde: {command.device_id}"
            )

        try:
            self._execute(command)
            self._state = command.action
            self._value = command.value
            self._error_message = None
        except Exception as e:
            self._state = DeviceState.ERROR
            self._error_message = str(e)
            raise DeviceError(self.device_id, str(e))

        self._last_updated = datetime.now()
        return self.status

    @abstractmethod
    def _execute(self, command: DeviceCommand):
        """Executa a implementação específica do comando do dispositivo.

        Args:
            command: Comando a ser executado

        Raises:
            Exception: Se a execução do comando falhar
        """
        pass


class MockActuator(BaseActuator):
    """Implementação simulada de atuador para testes."""

    def _execute(self, command: DeviceCommand):
        """Simula a execução do comando.

        Args:
            command: Comando a ser executado
        """
        # Simula atraso na execução do comando
        import time
        time.sleep(0.1)

        # Valida o valor do comando se fornecido
        if command.value is not None and not 0 <= command.value <= 100:
            raise ValueError(f"Valor de comando inválido: {command.value}")


class BinaryActuator(BaseActuator):
    """Classe base para dispositivos simples liga/desliga."""

    def _execute(self, command: DeviceCommand):
        """Executa comando de dispositivo binário.

        Args:
            command: Comando a ser executado

        Raises:
            ValueError: Se o comando for inválido para um dispositivo binário
        """
        if command.action == DeviceState.PARTIAL:
            raise ValueError(f"Dispositivo {self.device_id} suporta apenas estados LIGADO/DESLIGADO")
        if command.value is not None:
            raise ValueError(f"Dispositivo {self.device_id} não aceita parâmetro de valor")


class VariableActuator(BaseActuator):
    """Classe base para dispositivos com configurações variáveis."""

    def _execute(self, command: DeviceCommand):
        """Executa comando de dispositivo variável.

        Args:
            command: Comando a ser executado

        Raises:
            ValueError: Se o comando for inválido para um dispositivo variável
        """
        if command.action == DeviceState.PARTIAL and command.value is None:
            raise ValueError("Estado parcial requer um valor")
        if command.value is not None and not 0 <= command.value <= 100:
            raise ValueError(f"Valor inválido: {command.value}")


class ActuatorError(Exception):
    """Exceção personalizada para erros relacionados a atuadores."""

    def __init__(self, device_id: str, message: str):
        """Inicializa com ID do dispositivo e mensagem de erro.

        Args:
            device_id: Identificador do dispositivo que encontrou um erro
            message: Descrição do erro
        """
        self.device_id = device_id
        self.message = message
        super().__init__(f"Atuador {device_id}: {message}")
