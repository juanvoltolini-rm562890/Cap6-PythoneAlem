####################################
##### Arquivo: control.py
##### Desenvolvedor: Juan F. Voltolini
##### Instituição: FIAP
##### Trabalho: Cap 6 - Python e Além
##### Grupo: Alexander Dorneles de Oliveira, Felipe Sabino da Silva, Juan Felipe Voltolini, Luiz Henrique Ribeiro de Oliveira e Marco Aurélio Eberhardt Assumpção, 
####################################

"""Lógica de controle principal para o sistema do aviário.

Este módulo implementa a lógica de tomada de decisão que mantém as condições
ambientais ideais com base nas leituras dos sensores e na configuração do sistema.
"""
import logging
from dataclasses import dataclass
from typing import List, Optional, Tuple

from ..actuators.controller import DeviceController
from ..models.config import EnvironmentalLimits
from ..models.device import DeviceState, DeviceStatus
from ..models.sensor_data import SensorReading
from ..sensors.reader import ReadingBuffer

logger = logging.getLogger(__name__)


@dataclass
class ControlAction:
    """Representa uma decisão de ação de controle.

    Atributos:
        fan_speed: Velocidade alvo do ventilador de exaustão (0-100)
        curtain_position: Posição alvo da cortina (0-100)
        inlet_position: Posição alvo da entrada de ar (0-100)
        heaters_on: Se os aquecedores devem estar ligados
        nebulizers_on: Se os nebulizadores devem estar ligados
        alarm_message: Mensagem de alarme opcional se as condições forem críticas
    """

    fan_speed: float
    curtain_position: float
    inlet_position: float
    heaters_on: bool
    nebulizers_on: bool
    alarm_message: Optional[str] = None


class EnvironmentController:
    """Lógica de controle principal para manter as condições ideais."""

    def __init__(
        self,
        device_controller: DeviceController,
        limits: EnvironmentalLimits,
        reading_buffer: ReadingBuffer,
    ):
        """Inicializa o controlador de ambiente.

        Args:
            device_controller: Controlador para gerenciar atuadores
            limits: Limites dos parâmetros ambientais
            reading_buffer: Buffer de leituras recentes dos sensores
        """
        self.device_controller = device_controller
        self.limits = limits
        self.reading_buffer = reading_buffer
        self._last_action: Optional[ControlAction] = None

    def process_reading(self, reading: SensorReading) -> List[Tuple[str, DeviceStatus]]:
        """Processa uma nova leitura do sensor e ajusta o ambiente conforme necessário.

        Args:
            reading: Nova leitura do sensor para processar

        Returns:
            List[Tuple[str, DeviceStatus]]: Lista de IDs dos dispositivos e seus novos status
        """
        # Adicionar leitura ao buffer
        self.reading_buffer.add_reading(reading)

        # Determinar ações necessárias
        action = self._determine_actions(reading)
        self._last_action = action

        # Executar ações e coletar resultados
        results = []
        
        # Definir velocidades dos ventiladores
        results.extend(self.device_controller.set_fan_speeds(action.fan_speed))
        
        # Definir posições das cortinas
        results.extend(self.device_controller.set_curtain_positions(action.curtain_position))
        
        # Definir posições das entradas de ar
        results.extend(self.device_controller.set_inlet_positions(action.inlet_position))
        
        # Controlar aquecedores
        results.extend(
            self.device_controller.set_heaters(
                DeviceState.ON if action.heaters_on else DeviceState.OFF
            )
        )
        
        # Controlar nebulizadores
        results.extend(
            self.device_controller.set_nebulizers(
                DeviceState.ON if action.nebulizers_on else DeviceState.OFF
            )
        )
        
        # Tratar alarmes
        if action.alarm_message:
            results.extend(self.device_controller.trigger_alarm(action.alarm_message))
        else:
            results.extend(self.device_controller.clear_alarms())

        return results

    def _determine_actions(self, reading: SensorReading) -> ControlAction:
        """Determina as ações de controle necessárias com base na leitura do sensor.

        Args:
            reading: Leitura atual do sensor

        Returns:
            ControlAction: Ações de controle necessárias
        """
        action = ControlAction(
            fan_speed=20.0,  # Ventilação mínima
            curtain_position=0.0,
            inlet_position=20.0,  # Posição mínima das entradas
            heaters_on=False,
            nebulizers_on=False,
        )

        # Verificar temperatura
        if reading.temperature > self.limits.temp_max:
            # Temperatura alta
            action.fan_speed = 100.0  # Exaustores no máximo
            action.nebulizers_on = True  # Ativar nebulizadores
            
            # Se temperatura externa for menor, abrir cortinas
            if reading.external_temp < reading.temperature:
                action.curtain_position = 100.0
            
            # Temperatura crítica alta
            if reading.temperature > self.limits.temp_max + 5:
                action.alarm_message = f"Temperatura crítica alta: {reading.temperature}°C"
        
        elif reading.temperature < self.limits.temp_min:
            # Temperatura baixa
            action.heaters_on = True  # Ativar aquecedores
            action.curtain_position = 0.0  # Fechar cortinas
            
            # Temperatura crítica baixa
            if reading.temperature < self.limits.temp_min - 5:
                action.alarm_message = f"Temperatura crítica baixa: {reading.temperature}°C"

        # Verificar umidade
        if reading.humidity > self.limits.humidity_max:
            # Umidade alta - ativar exaustores
            action.fan_speed = max(action.fan_speed, 80.0)
        elif reading.humidity < self.limits.humidity_min:
            # Umidade baixa - nebulizadores e fechar parcialmente inlets
            action.nebulizers_on = True
            action.inlet_position = min(action.inlet_position, 40.0)  # Reduzir abertura

        # Verificar CO2
        if reading.co2_level > self.limits.co2_max:  # > 2000 ppm
            action.fan_speed = 100.0  # Exaustores no máximo
            action.curtain_position = max(action.curtain_position, 50.0)  # Abrir cortinas
            action.alarm_message = f"Nível alto de CO2: {reading.co2_level} ppm"

        # Verificar amônia
        if reading.ammonia_level > self.limits.ammonia_max:  # > 25 ppm
            action.fan_speed = 100.0  # Exaustores no máximo
            action.inlet_position = 100.0  # Abrir inlets totalmente
            action.alarm_message = f"Nível alto de amônia: {reading.ammonia_level} ppm"

        # Controle de pressão (visar 20-30 Pa)
        if reading.pressure > self.limits.pressure_target + 5:  # Pressão alta
            # Aumentar abertura dos inlets proporcionalmente
            pressure_error = reading.pressure - self.limits.pressure_target
            action.inlet_position = max(
                action.inlet_position,
                min(
                    100.0,  # Máximo
                    50.0 + (pressure_error * 2.0),  # Ajuste proporcional
                ),
            )

        # Verificar energia
        if not reading.power_ok:
            action.alarm_message = "ALERTA: Sistema operando com bateria!"
            # Manter operações críticas apenas
            action.fan_speed = min(action.fan_speed, 60.0)  # Reduzir consumo
            action.heaters_on = False  # Desligar aquecedores
            action.nebulizers_on = False  # Desligar nebulizadores

        return action

    def get_last_action(self) -> Optional[ControlAction]:
        """Obtém a ação de controle mais recente tomada.

        Returns:
            Optional[ControlAction]: Última ação ou None se nenhuma ação foi tomada
        """
        return self._last_action









