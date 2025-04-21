####################################
##### Arquivo: config.py
##### Desenvolvedor: Juan F. Voltolini
##### Instituição: FIAP
##### Trabalho: Cap 6 - Python e Além
##### Grupo: Alexander Dorneles de Oliveira, Felipe Sabino da Silva, Juan Felipe Voltolini, Luiz Henrique Ribeiro de Oliveira e Marco Aurélio Eberhardt Assumpção, 
####################################

"""Modelos de configuração para o sistema de controle do aviário.

Este módulo define as estruturas de dados e a lógica de validação para os parâmetros
de configuração do sistema e os limites ambientais.
"""
from dataclasses import dataclass
from typing import Dict, Optional


@dataclass
class EnvironmentalLimits:
    """Define os intervalos aceitáveis para parâmetros ambientais.

    Atributos:
        temp_target: Temperatura desejada (°C)
        temp_min: Temperatura mínima aceitável (°C)
        temp_max: Temperatura máxima aceitável (°C)
        humidity_min: Umidade mínima aceitável (%)
        humidity_max: Umidade máxima aceitável (%)
        co2_max: Nível máximo aceitável de CO2 (ppm)
        ammonia_max: Nível máximo aceitável de amônia (ppm)
        pressure_target: Pressão estática alvo (Pa)
    """

    temp_target: float
    temp_min: float
    temp_max: float
    humidity_min: float
    humidity_max: float
    co2_max: float
    ammonia_max: float
    pressure_target: float

    def __post_init__(self):
        """Validar valores de configuração."""
        self._validate_temperature_range()
        self._validate_humidity_range()
        self._validate_gas_levels()
        self._validate_pressure()

    def _validate_temperature_range(self):
        """Garantir que os limites de temperatura são válidos."""
        if not -10 <= self.temp_min <= self.temp_max <= 50:
            raise ValueError(
                f"Faixa de temperatura inválida: {self.temp_min}°C a {self.temp_max}°C"
            )

    def _validate_humidity_range(self):
        """Garantir que os limites de umidade são válidos."""
        if not 0 <= self.humidity_min <= self.humidity_max <= 100:
            raise ValueError(
                f"Faixa de umidade inválida: {self.humidity_min}% a {self.humidity_max}%"
            )

    def _validate_gas_levels(self):
        """Garantir que os limites de concentração de gases são válidos."""
        if not 0 <= self.co2_max <= 5000:
            raise ValueError(f"Máximo de CO2 inválido: {self.co2_max} ppm")
        if not 0 <= self.ammonia_max <= 100:
            raise ValueError(f"Máximo de amônia inválido: {self.ammonia_max} ppm")

    def _validate_pressure(self):
        """Garantir que o alvo de pressão é válido."""
        if not -50 <= self.pressure_target <= 50:
            raise ValueError(f"Alvo de pressão inválido: {self.pressure_target} Pa")


@dataclass
class SystemConfig:
    """Configurações gerais do sistema.

    Atributos:
        environmental_limits: Limites dos parâmetros ambientais
        reading_interval: Segundos entre leituras dos sensores
        log_level: Nível de detalhamento dos logs
        alarm_enabled: Se os alarmes estão ativos
        backup_power_threshold: Percentual da bateria para disparar avisos
    """

    environmental_limits: EnvironmentalLimits
    reading_interval: int = 60
    log_level: str = "INFO"
    alarm_enabled: bool = True
    backup_power_threshold: int = 20

    def __post_init__(self):
        """Validar valores de configuração."""
        self._validate_intervals()
        self._validate_log_level()
        self._validate_thresholds()

    def _validate_intervals(self):
        """Garantir que os intervalos de tempo são válidos."""
        if self.reading_interval < 1:
            raise ValueError(f"Intervalo de leitura inválido: {self.reading_interval} segundos")

    def _validate_log_level(self):
        """Garantir que o nível de log é válido."""
        valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if self.log_level not in valid_levels:
            raise ValueError(f"Nível de log inválido: {self.log_level}")

    def _validate_thresholds(self):
        """Garantir que os valores de limite são válidos."""
        if not 0 <= self.backup_power_threshold <= 100:
            raise ValueError(
                f"Limite de energia de backup inválido: {self.backup_power_threshold}%"
            )

    @classmethod
    def from_dict(cls, config_dict: Dict) -> "SystemConfig":
        """Criar uma instância de SystemConfig a partir de um dicionário.

        Args:
            config_dict: Dicionário contendo valores de configuração

        Returns:
            SystemConfig: Nova instância de configuração
        """
        env_limits = EnvironmentalLimits(
            temp_target=float(config_dict.get("temp_target", 25.0)),
            temp_min=float(config_dict.get("temp_min", 18.0)),
            temp_max=float(config_dict.get("temp_max", 32.0)),
            humidity_min=float(config_dict.get("humidity_min", 50.0)),
            humidity_max=float(config_dict.get("humidity_max", 70.0)),
            co2_max=float(config_dict.get("co2_max", 2000.0)),
            ammonia_max=float(config_dict.get("ammonia_max", 25.0)),
            pressure_target=float(config_dict.get("pressure_target", 25.0)),
        )

        return cls(
            environmental_limits=env_limits,
            reading_interval=int(config_dict.get("reading_interval", 60)),
            log_level=str(config_dict.get("log_level", "INFO")),
            alarm_enabled=bool(config_dict.get("alarm_enabled", True)),
            backup_power_threshold=int(config_dict.get("backup_power_threshold", 20)),
        )












