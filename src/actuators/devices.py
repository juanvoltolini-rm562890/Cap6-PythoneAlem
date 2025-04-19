####################################
##### Arquivo: devices.py
##### Desenvolvedor: Juan F. Voltolini
##### Instituição: FIAP
##### Trabalho: Cap 6 - Python e Além
##### Grupo: Alexander Dorneles de Oliveira, Felipe Sabino da Silva, Juan Felipe Voltolini, Luiz Henrique Ribeiro de Oliveira e Marco Aurélio Eberhardt Assumpção, 
####################################

"""Implementações concretas de atuadores para dispositivos de aviário.

Este módulo fornece implementações específicas para cada tipo de dispositivo
no sistema de controle de aviário.
"""
from typing import Optional

from ..models.device import DeviceCommand, DeviceState, DeviceType
from .base import BinaryActuator, VariableActuator

class ExhaustFan(VariableActuator):
    """Controla os ventiladores de exaustão de velocidade variável."""

    def __init__(self, device_id: str):
        """Inicializa o atuador do ventilador de exaustão.

        Args:
            device_id: Identificador único para este ventilador
        """
        super().__init__(device_id, DeviceType.EXHAUST_FAN)
        self._current_speed: float = 0.0

    def _execute(self, command: DeviceCommand):
        """Executa o comando de controle do ventilador.

        Args:
            command: Comando a ser executado

        Raises:
            ValueError: Se o comando for inválido
        """
        super()._execute(command)
        
        if command.action == DeviceState.OFF:
            self._current_speed = 0.0
        elif command.action == DeviceState.ON:
            self._current_speed = 100.0
        else:  # PARTIAL
            self._current_speed = command.value


class Curtain(VariableActuator):
    """Controla cortinas motorizadas."""

    def __init__(self, device_id: str):
        """Inicializa o atuador da cortina.

        Args:
            device_id: Identificador único para esta cortina
        """
        super().__init__(device_id, DeviceType.CURTAIN)
        self._position: float = 0.0  # 0 = fechada, 100 = totalmente aberta

    def _execute(self, command: DeviceCommand):
        """Executa o comando de controle da cortina.

        Args:
            command: Comando a ser executado

        Raises:
            ValueError: Se o comando for inválido
        """
        super()._execute(command)
        
        if command.action == DeviceState.OFF:
            self._position = 0.0  # Fecha a cortina
        elif command.action == DeviceState.ON:
            self._position = 100.0  # Abre a cortina
        else:  # PARTIAL
            self._position = command.value


class Inlet(VariableActuator):
    """Controla entradas de ar motorizadas."""

    def __init__(self, device_id: str):
        """Inicializa o atuador da entrada de ar.

        Args:
            device_id: Identificador único para esta entrada de ar
        """
        super().__init__(device_id, DeviceType.INLET)
        self._position: float = 0.0  # 0 = fechada, 100 = totalmente aberta

    def _execute(self, command: DeviceCommand):
        """Executa o comando de controle da entrada de ar.

        Args:
            command: Comando a ser executado

        Raises:
            ValueError: Se o comando for inválido
        """
        super()._execute(command)
        
        if command.action == DeviceState.OFF:
            self._position = 0.0  # Fecha a entrada
        elif command.action == DeviceState.ON:
            self._position = 100.0  # Abre a entrada
        else:  # PARTIAL
            self._position = command.value


class Heater(BinaryActuator):
    """Controla elementos de aquecimento."""

    def __init__(self, device_id: str):
        """Inicializa o atuador do aquecedor.

        Args:
            device_id: Identificador único para este aquecedor
        """
        super().__init__(device_id, DeviceType.HEATER)


class Nebulizer(BinaryActuator):
    """Controla o sistema de nebulização de água."""

    def __init__(self, device_id: str):
        """Inicializa o atuador do nebulizador.

        Args:
            device_id: Identificador único para este nebulizador
        """
        super().__init__(device_id, DeviceType.NEBULIZER)


class Alarm(BinaryActuator):
    """Controla o sistema de alarme."""

    def __init__(self, device_id: str):
        """Inicializa o atuador do alarme.

        Args:
            device_id: Identificador único para este alarme
        """
        super().__init__(device_id, DeviceType.ALARM)
        self._message: Optional[str] = None

    def set_message(self, message: str):
        """Define a mensagem do alarme.

        Args:
            message: Mensagem do alarme a ser exibida
        """
        self._message = message

    def get_message(self) -> Optional[str]:
        """Obtém a mensagem atual do alarme.

        Returns:
            Optional[str]: Mensagem atual do alarme ou None se não definida
        """
        return self._message