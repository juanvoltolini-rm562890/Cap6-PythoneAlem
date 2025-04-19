####################################
##### Arquivo: oracle_db.py
##### Desenvolvedor: Juan F. Voltolini
##### Instituição: FIAP
##### Trabalho: Cap 6 - Python e Além
##### Grupo: Alexander Dorneles de Oliveira, Felipe Sabino da Silva, Juan Felipe Voltolini, Luiz Henrique Ribeiro de Oliveira e Marco Aurélio Eberhardt Assumpção, 
####################################

"""Implementação de armazenamento em banco de dados Oracle.

Este módulo lida com a persistência de dados usando banco de dados Oracle para armazenamento 
de longo prazo e análise de dados do sistema.
"""
import logging
from datetime import datetime
from typing import List, Optional, Tuple

import cx_Oracle

from ..models.device import DeviceStatus
from ..models.sensor_data import SensorReading

logger = logging.getLogger(__name__)

class OracleStorage:
    """Gerencia operações do banco de dados Oracle."""

    def __init__(
        self,
        username: str,
        password: str,
        host: str,
        port: int = 1521,
        service: str = "XE",
    ):
        """Inicializa a conexão com o banco de dados Oracle.

        Args:
            username: Nome de usuário do banco de dados
            password: Senha do banco de dados
            host: Host do banco de dados
            port: Porta do banco de dados
            service: Nome do serviço Oracle
        """
        self.connection_string = (
            f"{username}/{password}@{host}:{port}/{service}"
        )
        self._connection = None

    def connect(self):
        """Estabelece a conexão com o banco de dados."""
        try:
            self._connection = cx_Oracle.connect(self.connection_string)
            logger.info("Conectado ao banco de dados Oracle")
        except Exception as e:
            logger.error(f"Falha ao conectar ao banco de dados: {e}")
            raise

    def disconnect(self):
        """Fecha a conexão com o banco de dados."""
        if self._connection:
            try:
                self._connection.close()
                logger.info("Desconectado do banco de dados Oracle")
            except Exception as e:
                logger.error(f"Erro ao desconectar do banco de dados: {e}")

    def _ensure_connection(self):
        """Garante que a conexão com o banco de dados está ativa."""
        if not self._connection:
            self.connect()

    def store_reading(self, reading: SensorReading):
        """Armazena leitura do sensor no banco de dados.

        Args:
            reading: Leitura do sensor para armazenar
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
                reading_seq.NEXTVAL,
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
        except Exception as e:
            logger.error(f"Falha ao armazenar leitura: {e}")
            self._connection.rollback()
            raise

    def store_device_status(self, status: DeviceStatus):
        """Armazena o status do dispositivo no banco de dados.

        Args:
            status: Status do dispositivo para armazenar
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
                status_seq.NEXTVAL,
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
        except Exception as e:
            logger.error(f"Falha ao armazenar status do dispositivo: {e}")
            self._connection.rollback()
            raise

    def store_alarm(self, timestamp: datetime, event_type: str, description: str):
        """Armazena evento de alarme no banco de dados.

        Args:
            timestamp: Quando o alarme ocorreu
            event_type: Tipo de evento de alarme
            description: Descrição do alarme
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
                event_seq.NEXTVAL,
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
        except Exception as e:
            logger.error(f"Falha ao armazenar alarme: {e}")
            self._connection.rollback()
            raise

    def get_avg_readings(
        self, start_time: datetime, end_time: datetime
    ) -> List[Tuple[datetime, float, float, float, float, float]]:
        """Obtém leituras médias do sensor para um período de tempo.

        Args:
            start_time: Início do período
            end_time: Fim do período

        Returns:
            List[Tuple]: Lista de (timestamp, temp, umidade, co2, nh3, pressão)
        """
        self._ensure_connection()
        sql = """
            SELECT
                TRUNC(timestamp, 'HH24') as hour,
                AVG(temperature) as avg_temp,
                AVG(humidity) as avg_humidity,
                AVG(co2_level) as avg_co2,
                AVG(ammonia_level) as avg_nh3,
                AVG(pressure) as avg_pressure
            FROM sensor_readings
            WHERE timestamp BETWEEN :start_time AND :end_time
            GROUP BY TRUNC(timestamp, 'HH24')
            ORDER BY hour
        """
        try:
            with self._connection.cursor() as cursor:
                cursor.execute(
                    sql,
                    {
                        "start_time": start_time,
                        "end_time": end_time,
                    },
                )
                return cursor.fetchall()
        except Exception as e:
            logger.error(f"Falha ao obter leituras médias: {e}")
            raise

    def get_device_history(
        self, device_id: str, hours: int = 24
    ) -> List[Tuple[datetime, str, Optional[float]]]:
        """Obtém histórico de status para um dispositivo.

        Args:
            device_id: Dispositivo para obter histórico
            hours: Número de horas para olhar para trás

        Returns:
            List[Tuple]: Lista de (timestamp, status, valor)
        """
        self._ensure_connection()
        sql = """
            SELECT timestamp, status, value
            FROM actuator_status
            WHERE device_id = :device_id
            AND timestamp >= SYSTIMESTAMP - INTERVAL '1' HOUR * :hours
            ORDER BY timestamp DESC
        """
        try:
            with self._connection.cursor() as cursor:
                cursor.execute(
                    sql,
                    {
                        "device_id": device_id,
                        "hours": hours,
                    },
                )
                return cursor.fetchall()
        except Exception as e:
            logger.error(f"Falha ao obter histórico do dispositivo: {e}")
            raise

    def get_recent_alarms(self, count: int = 10) -> List[Tuple[datetime, str, str]]:
        """Obtém eventos de alarme mais recentes.

        Args:
            count: Número de alarmes para recuperar

        Returns:
            List[Tuple]: Lista de (timestamp, tipo_evento, descrição)
        """
        self._ensure_connection()
        sql = """
            SELECT timestamp, event_type, description
            FROM alarm_events
            ORDER BY timestamp DESC
            FETCH FIRST :count ROWS ONLY
        """
        try:
            with self._connection.cursor() as cursor:
                cursor.execute(sql, {"count": count})
                return cursor.fetchall()
        except Exception as e:
            logger.error(f"Falha ao obter alarmes recentes: {e}")
            raise

