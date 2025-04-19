####################################
##### Arquivo: reader.py
##### Desenvolvedor: Juan F. Voltolini
##### Instituição: FIAP
##### Trabalho: Cap 6 - Python e Além
##### Grupo: Alexander Dorneles de Oliveira, Felipe Sabino da Silva, Juan Felipe Voltolini, Luiz Henrique Ribeiro de Oliveira e Marco Aurélio Eberhardt Assumpção
####################################

"""Gerenciamento e agendamento de leituras de sensores.

Este módulo fornece funcionalidade para leitura periódica de sensores e coleta de dados
no sistema de controle de aviário.
"""
import logging
import threading
import time
from datetime import datetime
from queue import Queue
from typing import Callable, Optional

from ..models.sensor_data import SensorReading
from .mock_sensor import SensorArray

logger = logging.getLogger(__name__)


class SensorReader:
    """Gerencia leituras periódicas de sensores e coleta de dados."""

    def __init__(
        self,
        reading_interval: int = 60,
        callback: Optional[Callable[[SensorReading], None]] = None,
    ):
        """Inicializa o leitor de sensores.

        Args:
            reading_interval: Segundos entre leituras
            callback: Função opcional para chamar com novas leituras
        """
        self.reading_interval = reading_interval
        self.callback = callback
        self.sensor_array = SensorArray()
        self.reading_queue: Queue = Queue()
        self._stop_event = threading.Event()
        self._reader_thread: Optional[threading.Thread] = None

    def start(self):
        """Inicia a thread de leitura periódica de sensores."""
        if self._reader_thread is not None and self._reader_thread.is_alive():
            logger.warning("Leitor de sensores já está em execução")
            return

        self._stop_event.clear()
        self._reader_thread = threading.Thread(target=self._reading_loop)
        self._reader_thread.daemon = True
        self._reader_thread.start()
        logger.info("Leitor de sensores iniciado")

    def stop(self):
        """Para a thread de leitura periódica de sensores."""
        self._stop_event.set()
        if self._reader_thread is not None:
            self._reader_thread.join()
            self._reader_thread = None
        logger.info("Leitor de sensores parado")

    def _reading_loop(self):
        """Loop principal para leitura periódica de sensores."""
        while not self._stop_event.is_set():
            try:
                reading = self.sensor_array.read_sensor_data()
                if reading is not None:
                    self.reading_queue.put(reading)
                    if self.callback is not None:
                        try:
                            self.callback(reading)
                        except Exception as e:
                            logger.error(f"Erro no callback: {e}")
                else:
                    logger.warning("Falha ao obter leitura completa do sensor")
            except Exception as e:
                logger.error(f"Erro ao ler sensores: {e}")

            # Aguarda o próximo intervalo de leitura
            self._stop_event.wait(self.reading_interval)

    def get_latest_reading(self) -> Optional[SensorReading]:
        """Obtém a leitura mais recente do sensor.

        Returns:
            Optional[SensorReading]: Última leitura ou None se a fila estiver vazia
        """
        try:
            return self.reading_queue.get_nowait()
        except Queue.Empty:
            return None

    def get_current_reading(self) -> Optional[SensorReading]:
        """Obtém uma leitura imediata do sensor.

        Returns:
            Optional[SensorReading]: Leitura atual ou None se a leitura falhar
        """
        return self.sensor_array.read_sensor_data()


class ReadingBuffer:
    """Buffer circular para armazenar leituras recentes de sensores."""

    def __init__(self, max_size: int = 60):
        """Inicializa o buffer de leituras.

        Args:
            max_size: Número máximo de leituras para armazenar
        """
        self.max_size = max_size
        self.readings: list[SensorReading] = []

    def add_reading(self, reading: SensorReading):
        """Adiciona uma nova leitura ao buffer.

        Args:
            reading: Leitura do sensor para adicionar
        """
        self.readings.append(reading)
        if len(self.readings) > self.max_size:
            self.readings.pop(0)

    def get_average_temperature(self, minutes: int = 5) -> Optional[float]:
        """Calcula a temperatura média nas leituras recentes.

        Args:
            minutes: Número de minutos para calcular a média

        Returns:
            Optional[float]: Temperatura média ou None se não houver leituras
        """
        recent = self._get_recent_readings(minutes)
        if not recent:
            return None
        return sum(r.temperature for r in recent) / len(recent)

    def get_average_humidity(self, minutes: int = 5) -> Optional[float]:
        """Calcula a umidade média nas leituras recentes.

        Args:
            minutes: Número de minutos para calcular a média

        Returns:
            Optional[float]: Umidade média ou None se não houver leituras
        """
        recent = self._get_recent_readings(minutes)
        if not recent:
            return None
        return sum(r.humidity for r in recent) / len(recent)

    def _get_recent_readings(self, minutes: int) -> list[SensorReading]:
        """Obtém leituras dos últimos N minutos.

        Args:
            minutes: Número de minutos para retroceder

        Returns:
            list[SensorReading]: Lista de leituras recentes
        """
        if not self.readings:
            return []

        cutoff = datetime.now().timestamp() - (minutes * 60)
        return [r for r in self.readings if r.timestamp.timestamp() >= cutoff]