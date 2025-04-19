####################################
##### Arquivo: mock_sensor.py
##### Desenvolvedor: Juan F. Voltolini
##### Instituição: FIAP
##### Trabalho: Cap 6 - Python e Além
##### Grupo: Alexander Dorneles de Oliveira, Felipe Sabino da Silva, Juan Felipe Voltolini, Luiz Henrique Ribeiro de Oliveira e Marco Aurélio Eberhardt Assumpção
####################################

"""Implementações de sensores simulados para leituras ambientais.

Este módulo fornece classes de sensores simulados que geram leituras fictícias para
temperatura, umidade, CO2, amônia e pressão no sistema de controle de aviário.
"""
import random
from datetime import datetime
from typing import Optional, Tuple

from ..models.sensor_data import EnvironmentalConditions, SensorReading

class BaseSensor:
    """Classe base para sensores simulados com funcionalidades comuns."""

    def __init__(self, sensor_id: str, error_rate: float = 0.05):
        """Inicializa o sensor.

        Args:
            sensor_id: Identificador único para este sensor
            error_rate: Probabilidade de falha na leitura do sensor (0-1)
        """
        self.sensor_id = sensor_id
        self.error_rate = error_rate
        self._last_value: Optional[float] = None

    def _simulate_error(self) -> bool:
        """Determina se uma leitura deve falhar com base na taxa de erro.

        Returns:
            bool: True se a leitura deve falhar, False caso contrário
        """
        return random.random() < self.error_rate

    def _add_noise(self, value: float, noise_percent: float = 0.02) -> float:
        """Adiciona ruído aleatório a uma leitura do sensor.

        Args:
            value: Valor base para adicionar ruído
            noise_percent: Ruído máximo como porcentagem do valor

        Returns:
            float: Valor com ruído adicionado
        """
        noise = random.uniform(-value * noise_percent, value * noise_percent)
        return value + noise


class TemperatureSensor(BaseSensor):
    """Implementação simulada de sensor de temperatura."""

    def __init__(self, sensor_id: str, initial_temp: float = 25.0):
        """Inicializa o sensor de temperatura.

        Args:
            sensor_id: Identificador único para este sensor
            initial_temp: Temperatura inicial em Celsius
        """
        super().__init__(sensor_id)
        self._last_value = initial_temp

    def read(self) -> Optional[float]:
        """Obtém uma leitura simulada de temperatura.

        Returns:
            Optional[float]: Temperatura em Celsius, ou None se a leitura falhar
        """
        if self._simulate_error():
            return None

        # Simula variações graduais de temperatura
        drift = random.uniform(-0.5, 0.5)
        new_temp = self._add_noise(self._last_value + drift)
        
        # Mantém a temperatura em faixa realista
        new_temp = max(min(new_temp, 40.0), 10.0)
        self._last_value = new_temp
        
        return round(new_temp, 1)


class HumiditySensor(BaseSensor):
    """Implementação simulada de sensor de umidade."""

    def __init__(self, sensor_id: str, initial_humidity: float = 60.0):
        """Inicializa o sensor de umidade.

        Args:
            sensor_id: Identificador único para este sensor
            initial_humidity: Umidade relativa inicial em porcentagem
        """
        super().__init__(sensor_id)
        self._last_value = initial_humidity

    def read(self) -> Optional[float]:
        """Obtém uma leitura simulada de umidade.

        Returns:
            Optional[float]: Umidade relativa em porcentagem, ou None se a leitura falhar
        """
        if self._simulate_error():
            return None

        # Simula variações graduais de umidade
        drift = random.uniform(-2.0, 2.0)
        new_humidity = self._add_noise(self._last_value + drift)
        
        # Mantém a umidade em faixa válida
        new_humidity = max(min(new_humidity, 100.0), 0.0)
        self._last_value = new_humidity
        
        return round(new_humidity, 1)


class CO2Sensor(BaseSensor):
    """Implementação simulada de sensor de CO2."""

    def __init__(self, sensor_id: str, initial_co2: float = 800.0):
        """Inicializa o sensor de CO2.

        Args:
            sensor_id: Identificador único para este sensor
            initial_co2: Nível inicial de CO2 em ppm
        """
        super().__init__(sensor_id)
        self._last_value = initial_co2

    def read(self) -> Optional[float]:
        """Obtém uma leitura simulada de CO2.

        Returns:
            Optional[float]: Nível de CO2 em ppm, ou None se a leitura falhar
        """
        if self._simulate_error():
            return None

        # Simula variações de CO2
        drift = random.uniform(-50.0, 50.0)
        new_co2 = self._add_noise(self._last_value + drift)
        
        # Mantém o CO2 em faixa realista
        new_co2 = max(min(new_co2, 3000.0), 400.0)
        self._last_value = new_co2
        
        return round(new_co2, 0)


class AmmoniaSensor(BaseSensor):
    """Implementação simulada de sensor de amônia."""

    def __init__(self, sensor_id: str, initial_nh3: float = 10.0):
        """Inicializa o sensor de amônia.

        Args:
            sensor_id: Identificador único para este sensor
            initial_nh3: Nível inicial de amônia em ppm
        """
        super().__init__(sensor_id)
        self._last_value = initial_nh3

    def read(self) -> Optional[float]:
        """Obtém uma leitura simulada de amônia.

        Returns:
            Optional[float]: Nível de amônia em ppm, ou None se a leitura falhar
        """
        if self._simulate_error():
            return None

        # Simula variações de amônia
        drift = random.uniform(-1.0, 1.0)
        new_nh3 = self._add_noise(self._last_value + drift)
        
        # Mantém a amônia em faixa realista
        new_nh3 = max(min(new_nh3, 50.0), 0.0)
        self._last_value = new_nh3
        
        return round(new_nh3, 1)


class PressureSensor(BaseSensor):
    """Implementação simulada de sensor de pressão."""

    def __init__(self, sensor_id: str, initial_pressure: float = 25.0):
        """Inicializa o sensor de pressão.

        Args:
            sensor_id: Identificador único para este sensor
            initial_pressure: Pressão inicial em Pascals
        """
        super().__init__(sensor_id)
        self._last_value = initial_pressure

    def read(self) -> Optional[float]:
        """Obtém uma leitura simulada de pressão.

        Returns:
            Optional[float]: Pressão estática em Pascals, ou None se a leitura falhar
        """
        if self._simulate_error():
            return None

        # Simula variações de pressão
        drift = random.uniform(-2.0, 2.0)
        new_pressure = self._add_noise(self._last_value + drift)
        
        # Mantém a pressão em faixa realista
        new_pressure = max(min(new_pressure, 50.0), -10.0)
        self._last_value = new_pressure
        
        return round(new_pressure, 1)


class SensorArray:
    """Conjunto de todos os sensores ambientais."""

    def __init__(self):
        """Inicializa o conjunto de sensores com sensores padrão."""
        self.temp_sensor = TemperatureSensor("TEMP001")
        self.humidity_sensor = HumiditySensor("HUM001")
        self.co2_sensor = CO2Sensor("CO2001")
        self.ammonia_sensor = AmmoniaSensor("NH3001")
        self.pressure_sensor = PressureSensor("PRES001")

    def read_all(self) -> EnvironmentalConditions:
        """Lê todos os sensores e retorna as condições atuais.

        Returns:
            EnvironmentalConditions: Leituras ambientais atuais
        """
        return EnvironmentalConditions(
            timestamp=datetime.now(),
            temperature=self.temp_sensor.read(),
            external_temp=self.temp_sensor.read(),  # Usa o mesmo sensor para temp externa por enquanto
            humidity=self.humidity_sensor.read(),
            co2_level=self.co2_sensor.read(),
            ammonia_level=self.ammonia_sensor.read(),
            pressure=self.pressure_sensor.read(),
            power_ok=True  # Assume que a energia está sempre OK para sensor simulado
        )

    def read_sensor_data(self) -> Optional[SensorReading]:
        """Lê todos os sensores e retorna uma leitura completa se todos os valores forem válidos.

        Returns:
            Optional[SensorReading]: Leitura completa do sensor ou None se alguma leitura falhar
        """
        conditions = self.read_all()
        if conditions.is_complete():
            return conditions.to_sensor_reading("ARRAY001")
        return None