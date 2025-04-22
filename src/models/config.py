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
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, List, Optional


class AlertSeverity(Enum):
    """Níveis de severidade para alertas."""
    LOW = auto()
    MEDIUM = auto()
    HIGH = auto()
    CRITICAL = auto()


class AlertType(Enum):
    """Tipos de alertas suportados pelo sistema."""
    TEMPERATURE = auto()
    HUMIDITY = auto()
    CO2 = auto()
    AMMONIA = auto()
    PRESSURE = auto()
    POWER = auto()
    SYSTEM = auto()


@dataclass
class AlertConfig:
    """Configuração de um alerta personalizado.

    Atributos:
        alert_id: Identificador único do alerta
        name: Nome descritivo do alerta
        alert_type: Tipo de alerta (temperatura, umidade, etc.)
        threshold: Valor limite para disparar o alerta
        is_upper_limit: Se True, o alerta dispara quando o valor é maior que o limite
                       Se False, o alerta dispara quando o valor é menor que o limite
        severity: Nível de severidade do alerta
        enabled: Se o alerta está ativo
        notification: Se deve enviar notificação quando o alerta for disparado
    """
    alert_id: str
    name: str
    alert_type: AlertType
    threshold: float
    is_upper_limit: bool
    severity: AlertSeverity = AlertSeverity.MEDIUM
    enabled: bool = True
    notification: bool = True

    def __post_init__(self):
        """Validar valores de configuração."""
        self._validate_threshold()

    def _validate_threshold(self):
        """Garantir que o valor limite é válido para o tipo de alerta."""
        if self.alert_type == AlertType.TEMPERATURE and not -20 <= self.threshold <= 60:
            raise ValueError(f"Limite de temperatura inválido: {self.threshold}°C")
        elif self.alert_type == AlertType.HUMIDITY and not 0 <= self.threshold <= 100:
            raise ValueError(f"Limite de umidade inválido: {self.threshold}%")
        elif self.alert_type == AlertType.CO2 and not 0 <= self.threshold <= 10000:
            raise ValueError(f"Limite de CO2 inválido: {self.threshold} ppm")
        elif self.alert_type == AlertType.AMMONIA and not 0 <= self.threshold <= 200:
            raise ValueError(f"Limite de amônia inválido: {self.threshold} ppm")
        elif self.alert_type == AlertType.PRESSURE and not -100 <= self.threshold <= 100:
            raise ValueError(f"Limite de pressão inválido: {self.threshold} Pa")

    @classmethod
    def from_dict(cls, alert_dict: Dict) -> "AlertConfig":
        """Criar uma instância de AlertConfig a partir de um dicionário.

        Args:
            alert_dict: Dicionário contendo valores de configuração do alerta

        Returns:
            AlertConfig: Nova instância de configuração de alerta
        """
        return cls(
            alert_id=str(alert_dict.get("alert_id", "")),
            name=str(alert_dict.get("name", "")),
            alert_type=AlertType[alert_dict.get("alert_type", "SYSTEM")],
            threshold=float(alert_dict.get("threshold", 0.0)),
            is_upper_limit=bool(alert_dict.get("is_upper_limit", True)),
            severity=AlertSeverity[alert_dict.get("severity", "MEDIUM")],
            enabled=bool(alert_dict.get("enabled", True)),
            notification=bool(alert_dict.get("notification", True)),
        )

    def to_dict(self) -> Dict:
        """Converter a configuração de alerta para um dicionário.

        Returns:
            Dict: Dicionário contendo os valores de configuração do alerta
        """
        return {
            "alert_id": self.alert_id,
            "name": self.name,
            "alert_type": self.alert_type.name,
            "threshold": self.threshold,
            "is_upper_limit": self.is_upper_limit,
            "severity": self.severity.name,
            "enabled": self.enabled,
            "notification": self.notification,
        }


@dataclass
class EnvironmentalLimits:
    """Define os intervalos aceitáveis para parâmetros ambientais.

    Atributos:
        temp_min: Temperatura mínima aceitável (°C)
        temp_max: Temperatura máxima aceitável (°C)
        humidity_min: Umidade mínima aceitável (%)
        humidity_max: Umidade máxima aceitável (%)
        co2_max: Nível máximo aceitável de CO2 (ppm)
        ammonia_max: Nível máximo aceitável de amônia (ppm)
        pressure_target: Pressão estática alvo (Pa)
    """

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

    def to_dict(self) -> Dict:
        """Converter os limites ambientais para um dicionário.

        Returns:
            Dict: Dicionário contendo os valores dos limites ambientais
        """
        return {
            "temp_min": self.temp_min,
            "temp_max": self.temp_max,
            "humidity_min": self.humidity_min,
            "humidity_max": self.humidity_max,
            "co2_max": self.co2_max,
            "ammonia_max": self.ammonia_max,
            "pressure_target": self.pressure_target,
        }


@dataclass
class SystemConfig:
    """Configurações gerais do sistema.

    Atributos:
        environmental_limits: Limites dos parâmetros ambientais
        reading_interval: Segundos entre leituras dos sensores
        log_level: Nível de detalhamento dos logs
        alarm_enabled: Se os alarmes estão ativos
        backup_power_threshold: Percentual da bateria para disparar avisos
        custom_alerts: Lista de alertas personalizados
        persistence_mode: Modo de persistência dos dados ("local", "oracle", "auto")
    """

    environmental_limits: EnvironmentalLimits
    reading_interval: int = 60
    log_level: str = "INFO"
    alarm_enabled: bool = True
    backup_power_threshold: int = 20
    custom_alerts: List[AlertConfig] = field(default_factory=list)
    persistence_mode: str = "auto"

    def __post_init__(self):
        """Validar valores de configuração."""
        self._validate_intervals()
        self._validate_log_level()
        self._validate_thresholds()
        self._validate_persistence_mode()

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

    def _validate_persistence_mode(self):
        """Garantir que o modo de persistência é válido."""
        valid_modes = {"local", "oracle", "auto"}
        if self.persistence_mode.lower() not in valid_modes:
            raise ValueError(f"Modo de persistência inválido: {self.persistence_mode}")

    def add_alert(self, alert: AlertConfig) -> bool:
        """Adiciona um novo alerta personalizado.

        Args:
            alert: Configuração do alerta a ser adicionado

        Returns:
            bool: True se o alerta foi adicionado com sucesso, False caso contrário
        """
        # Verificar se já existe um alerta com o mesmo ID
        if any(a.alert_id == alert.alert_id for a in self.custom_alerts):
            return False

        self.custom_alerts.append(alert)
        return True

    def update_alert(self, alert_id: str, updated_alert: AlertConfig) -> bool:
        """Atualiza um alerta existente.

        Args:
            alert_id: ID do alerta a ser atualizado
            updated_alert: Nova configuração do alerta

        Returns:
            bool: True se o alerta foi atualizado com sucesso, False caso contrário
        """
        for i, alert in enumerate(self.custom_alerts):
            if alert.alert_id == alert_id:
                self.custom_alerts[i] = updated_alert
                return True
        return False

    def remove_alert(self, alert_id: str) -> bool:
        """Remove um alerta existente.

        Args:
            alert_id: ID do alerta a ser removido

        Returns:
            bool: True se o alerta foi removido com sucesso, False caso contrário
        """
        for i, alert in enumerate(self.custom_alerts):
            if alert.alert_id == alert_id:
                self.custom_alerts.pop(i)
                return True
        return False

    def get_alert(self, alert_id: str) -> Optional[AlertConfig]:
        """Obtém um alerta pelo ID.

        Args:
            alert_id: ID do alerta a ser obtido

        Returns:
            Optional[AlertConfig]: Configuração do alerta ou None se não encontrado
        """
        for alert in self.custom_alerts:
            if alert.alert_id == alert_id:
                return alert
        return None

    @classmethod
    def from_dict(cls, config_dict: Dict) -> "SystemConfig":
        """Criar uma instância de SystemConfig a partir de um dicionário.

        Args:
            config_dict: Dicionário contendo valores de configuração

        Returns:
            SystemConfig: Nova instância de configuração
        """
        env_limits = EnvironmentalLimits(
            temp_min=float(config_dict.get("temp_min", 18.0)),
            temp_max=float(config_dict.get("temp_max", 32.0)),
            humidity_min=float(config_dict.get("humidity_min", 50.0)),
            humidity_max=float(config_dict.get("humidity_max", 70.0)),
            co2_max=float(config_dict.get("co2_max", 2000.0)),
            ammonia_max=float(config_dict.get("ammonia_max", 25.0)),
            pressure_target=float(config_dict.get("pressure_target", 25.0)),
        )

        # Processar alertas personalizados
        custom_alerts = []
        alerts_dict = config_dict.get("custom_alerts", [])
        for alert_dict in alerts_dict:
            try:
                custom_alerts.append(AlertConfig.from_dict(alert_dict))
            except (ValueError, KeyError) as e:
                # Ignorar alertas inválidos
                pass

        return cls(
            environmental_limits=env_limits,
            reading_interval=int(config_dict.get("reading_interval", 60)),
            log_level=str(config_dict.get("log_level", "INFO")),
            alarm_enabled=bool(config_dict.get("alarm_enabled", True)),
            backup_power_threshold=int(config_dict.get("backup_power_threshold", 20)),
            custom_alerts=custom_alerts,
            persistence_mode=str(config_dict.get("persistence_mode", "auto")),
        )

    def to_dict(self) -> Dict:
        """Converter a configuração do sistema para um dicionário.

        Returns:
            Dict: Dicionário contendo os valores de configuração do sistema
        """
        config_dict = {
            **self.environmental_limits.to_dict(),
            "reading_interval": self.reading_interval,
            "log_level": self.log_level,
            "alarm_enabled": self.alarm_enabled,
            "backup_power_threshold": self.backup_power_threshold,
            "persistence_mode": self.persistence_mode,
            "custom_alerts": [alert.to_dict() for alert in self.custom_alerts],
        }
        return config_dict