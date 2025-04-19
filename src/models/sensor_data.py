####################################
##### Arquivo: sensor_data.py
##### Desenvolvedor: Juan F. Voltolini
##### Instituição: FIAP
##### Trabalho: Cap 6 - Python e Além
##### Grupo: Alexander Dorneles de Oliveira, Felipe Sabino da Silva, Juan Felipe Voltolini, Luiz Henrique Ribeiro de Oliveira e Marco Aurélio Eberhardt Assumpção, 
####################################

"""Modelos para dados de sensores e medições ambientais.

Este módulo define as estruturas de dados e lógica de validação para leituras de sensores ambientais
no sistema de controle de aviário.
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class SensorReading:
    """Representa uma única leitura de sensor ambiental.

    Atributos:
        timestamp: Quando a leitura foi realizada
        temperature: Temperatura em Celsius
        external_temp: Temperatura externa em Celsius
        humidity: Porcentagem de umidade relativa
        co2_level: Concentração de CO2 em ppm
        ammonia_level: Concentração de amônia em ppm
        pressure: Pressão estática em Pascals
        power_ok: Status da energia
        sensor_id: Identificador único do sensor
    """

    timestamp: datetime
    temperature: float
    external_temp: float
    humidity: float
    co2_level: float
    ammonia_level: float
    pressure: float
    power_ok: bool
    sensor_id: str

    def __post_init__(self):
        """Valida se as leituras de sensor estão dentro dos intervalos aceitáveis."""
        self._validate_temperature()
        self._validate_external_temp()
        self._validate_humidity()
        self._validate_co2()
        self._validate_ammonia()
        self._validate_pressure()

    def _validate_temperature(self):
        """Garante que a temperatura esteja dentro do intervalo válido (-10 a 50°C)."""
        if not -10 <= self.temperature <= 50:
            raise ValueError(f"Temperatura {self.temperature}°C está fora do intervalo válido (-10 a 50)")

    def _validate_external_temp(self):
        """Garante que a temperatura externa esteja dentro do intervalo válido (-20 a 50°C)."""
        if not -20 <= self.external_temp <= 50:
            raise ValueError(f"Temperatura externa {self.external_temp}°C está fora do intervalo válido (-20 a 50)")

    def _validate_humidity(self):
        """Garante que a umidade esteja dentro do intervalo válido (0-100%)."""
        if not 0 <= self.humidity <= 100:
            raise ValueError(f"Umidade {self.humidity}% está fora do intervalo válido (0-100)")

    def _validate_co2(self):
        """Garante que o nível de CO2 esteja dentro do intervalo válido (0-5000 ppm)."""
        if not 0 <= self.co2_level <= 5000:
            raise ValueError(f"Nível de CO2 {self.co2_level} ppm está fora do intervalo válido (0-5000)")

    def _validate_ammonia(self):
        """Garante que o nível de amônia esteja dentro do intervalo válido (0-100 ppm)."""
        if not 0 <= self.ammonia_level <= 100:
            raise ValueError(f"Nível de amônia {self.ammonia_level} ppm está fora do intervalo válido (0-100)")

    def _validate_pressure(self):
        """Garante que a pressão esteja dentro do intervalo válido (-50 a 50 Pa)."""
        if not -50 <= self.pressure <= 50:
            raise ValueError(f"Pressão {self.pressure} Pa está fora do intervalo válido (-50 a 50)")


@dataclass
class EnvironmentalConditions:
    """Representa o estado ambiental atual com valores opcionais.

    Esta classe é usada quando algumas leituras de sensor podem estar indisponíveis.

    Atributos:
        timestamp: Quando as condições foram registradas
        temperature: Temperatura opcional em Celsius
        external_temp: Temperatura externa opcional em Celsius
        humidity: Porcentagem de umidade relativa opcional
        co2_level: Concentração de CO2 opcional em ppm
        ammonia_level: Concentração de amônia opcional em ppm
        pressure: Pressão estática opcional em Pascals
        power_ok: Status opcional da energia
    """

    timestamp: datetime
    temperature: Optional[float] = None
    external_temp: Optional[float] = None
    humidity: Optional[float] = None
    co2_level: Optional[float] = None
    ammonia_level: Optional[float] = None
    pressure: Optional[float] = None
    power_ok: Optional[bool] = None

    def is_complete(self) -> bool:
        """Verifica se todas as leituras de sensor estão disponíveis.

        Returns:
            bool: True se todas as leituras estiverem presentes, False caso contrário
        """
        return all(
            value is not None
            for value in [
                self.temperature,
                self.external_temp,
                self.humidity,
                self.co2_level,
                self.ammonia_level,
                self.pressure,
                self.power_ok,
            ]
        )

    def to_sensor_reading(self, sensor_id: str) -> SensorReading:
        """Converte para um SensorReading se todos os valores estiverem presentes.

        Args:
            sensor_id: Identificador para o conjunto de sensores

        Returns:
            SensorReading: Objeto completo de leitura de sensor

        Raises:
            ValueError: Se alguma leitura estiver faltando
        """
        if not self.is_complete():
            raise ValueError("Não é possível converter para SensorReading: valores ausentes")

        return SensorReading(
            timestamp=self.timestamp,
            temperature=self.temperature,
            external_temp=self.external_temp,
            humidity=self.humidity,
            co2_level=self.co2_level,
            ammonia_level=self.ammonia_level,
            pressure=self.pressure,
            power_ok=True,  # Assume que a energia está OK para leituras convertidas
            sensor_id=sensor_id,
        )