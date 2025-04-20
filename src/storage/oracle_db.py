import logging
from datetime import datetime

import oracledb

from ..models.device import DeviceStatus
from ..models.sensor_data import SensorReading

logger = logging.getLogger(__name__)


class OracleStorage:
    """Gerencia operações do banco de dados Oracle."""

    def __init__(
            self,
            username: str = "rm563348",
            password: str = "220982",
            dsn: str = "oracle.fiap.com.br/orcl",
    ):
        """Inicializa a conexão com o banco de dados Oracle.

        Args:
            username: Nome de usuário do banco de dados.
            password: Senha do banco de dados.
            dsn: Nome do Data Source Name (DSN) do banco de dados.
        """
        self.username = username
        self.password = password
        self.dsn = dsn
        self._connection = None

    def connect(self):
        """Estabelece a conexão com o banco de dados."""
        try:
            self._connection = oracledb.connect(
                user=self.username,
                password=self.password,
                dsn=self.dsn,
            )
            logger.info("Conectado ao banco de dados Oracle.")
        except oracledb.DatabaseError as e:
            logger.error(f"Falha ao conectar ao banco de dados: {e}")
            raise

    def disconnect(self):
        """Fecha a conexão com o banco de dados."""
        if self._connection:
            try:
                self._connection.close()
                logger.info("Desconectado do banco de dados Oracle.")
            except oracledb.DatabaseError as e:
                logger.error(f"Erro ao desconectar do banco de dados: {e}")

    def _ensure_connection(self):
        """Garante que a conexão com o banco de dados está ativa."""
        if not self._connection:
            self.connect()

    def store_reading(self, reading: SensorReading):
        """Armazena leitura do sensor no banco de dados.

        Args:
            reading: Leitura do sensor para armazenar.
        """
        self._ensure_connection()
        sql = """
            INSERT INTO sensor_readings (
                reading_id,
                timestamp,
                temperature,
                humidity,
                co2_level,
                ammonia_level,
                pressure
            ) VALUES (
                sensor_readings_seq.NEXTVAL,
                :timestamp,
                :temperature,
                :humidity,
                :co2_level,
                :ammonia_level,
                :pressure
            )
        """
        try:
            with self._connection.cursor() as cursor:
                cursor.execute(
                    sql,
                    {
                        "timestamp": reading.timestamp,
                        "temperature": reading.temperature,
                        "humidity": reading.humidity,
                        "co2_level": reading.co2_level,
                        "ammonia_level": reading.ammonia_level,
                        "pressure": reading.pressure,
                    },
                )
            self._connection.commit()
            logger.info("Leitura do sensor armazenada com sucesso.")
        except oracledb.DatabaseError as e:
            logger.error(f"Falha ao armazenar leitura: {e}")
            self._connection.rollback()
            raise

    def store_device_status(self, status: DeviceStatus):
        """Armazena o status do dispositivo no banco de dados.

        Args:
            status: Status do dispositivo para armazenar.
        """
        self._ensure_connection()
        sql = """
            INSERT INTO actuator_status (
                status_id,
                timestamp,
                device_type,
                device_id,
                status,
                value
            ) VALUES (
                actuator_status_seq.NEXTVAL,
                :timestamp,
                :device_type,
                :device_id,
                :status,
                :value
            )
        """
        try:
            with self._connection.cursor() as cursor:
                cursor.execute(
                    sql,
                    {
                        "timestamp": status.last_updated,
                        "device_type": status.device_type.name,
                        "device_id": status.device_id,
                        "status": status.state.name,
                        "value": status.value,
                    },
                )
            self._connection.commit()
            logger.info("Status do dispositivo armazenado com sucesso.")
        except oracledb.DatabaseError as e:
            logger.error(f"Falha ao armazenar status do dispositivo: {e}")
            self._connection.rollback()
            raise

    def store_alarm(self, timestamp: datetime, event_type: str, description: str):
        """Armazena evento de alarme no banco de dados.

        Args:
            timestamp: Quando o alarme ocorreu.
            event_type: Tipo de evento de alarme.
            description: Descrição do alarme.
        """
        self._ensure_connection()
        sql = """
            INSERT INTO alarm_events (
                event_id,
                timestamp,
                event_type,
                severity,
                description
            ) VALUES (
                alarm_events_seq.NEXTVAL,
                :timestamp,
                :event_type,
                'ERROR',
                :description
            )
        """
        try:
            with self._connection.cursor() as cursor:
                cursor.execute(
                    sql,
                    {
                        "timestamp": timestamp,
                        "event_type": event_type,
                        "description": description,
                    },
                )
            self._connection.commit()
            logger.info("Evento de alarme armazenado com sucesso.")
        except oracledb.DatabaseError as e:
            logger.error(f"Falha ao armazenar alarme: {e}")
            self._connection.rollback()
            raise
