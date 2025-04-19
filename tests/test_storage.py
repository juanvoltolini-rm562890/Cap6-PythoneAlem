####################################
##### Arquivo: test_storage.py
##### Desenvolvedor: Juan F. Voltolini
##### Instituição: FIAP
##### Trabalho: Cap 6 - Python e Além
##### Grupo: Alexander Dorneles de Oliveira, Felipe Sabino da Silva, Juan Felipe Voltolini, Luiz Henrique Ribeiro de Oliveira e Marco Aurélio Eberhardt Assumpção
####################################

"""Testes unitários para funcionalidades de armazenamento em arquivo."""
import os
import tempfile
from datetime import datetime
from pathlib import Path
import pytest

from src.storage.file_storage import FileStorage, parse_sensor_reading
from src.models.sensor_data import SensorReading

def test_parse_sensor_reading_old_format():
    """Testa a análise de leitura de sensor no formato antigo."""
    line = "2025-04-19 10:00:54,25.8,59.5,786,10.3,24.5,ARRAY001"
    reading = parse_sensor_reading(line)
    assert reading is not None
    assert reading.timestamp == datetime(2025, 4, 19, 10, 0, 54)
    assert reading.temperature == 25.8
    assert reading.external_temp == 25.8  # Deve usar temperatura como temperatura externa
    assert reading.humidity == 59.5
    assert reading.co2_level == 786
    assert reading.ammonia_level == 10.3
    assert reading.pressure == 24.5
    assert reading.power_ok is True  # Deve padrão para True
    assert reading.sensor_id == "ARRAY001"


def test_parse_sensor_reading_new_format():
    """Testa a análise de leitura de sensor no formato novo."""
    line = "2025-04-19 10:00:54,25.8,24.5,59.5,786,10.3,24.5,true,ARRAY001"
    reading = parse_sensor_reading(line)
    assert reading is not None
    assert reading.timestamp == datetime(2025, 4, 19, 10, 0, 54)
    assert reading.temperature == 25.8
    assert reading.external_temp == 24.5
    assert reading.humidity == 59.5
    assert reading.co2_level == 786
    assert reading.ammonia_level == 10.3
    assert reading.pressure == 24.5
    assert reading.power_ok is True
    assert reading.sensor_id == "ARRAY001"


def test_parse_sensor_reading_invalid_format():
    """Testa a análise de leitura de sensor com formato inválido."""
    line = "2025-04-19 10:00:54,25.8,59.5,786,10.3"  # Campos insuficientes
    reading = parse_sensor_reading(line)
    assert reading is None


def test_parse_sensor_reading_invalid_values():
    """Testa a análise de leitura de sensor com valores numéricos inválidos."""
    line = "2025-04-19 10:00:54,invalid,59.5,786,10.3,24.5,ARRAY001"
    reading = parse_sensor_reading(line)
    assert reading is None


class TestFileStorage:
    """Casos de teste para a classe FileStorage."""

    @pytest.fixture
    def temp_dir(self):
        """Cria um diretório temporário para arquivos de teste."""
        with tempfile.TemporaryDirectory() as tmpdirname:
            yield tmpdirname

    @pytest.fixture
    def storage(self, temp_dir):
        """Cria uma instância de FileStorage usando diretório temporário."""
        return FileStorage(temp_dir)

    def test_get_readings_for_day_old_format(self, storage, temp_dir):
        """Testa a leitura de dados de sensor no formato antigo."""
        # Cria arquivo de dados de teste
        log_file = Path(temp_dir) / "logs" / "readings_20250419.txt"
        log_file.parent.mkdir(exist_ok=True)
        with open(log_file, "w") as f:
            f.write("Timestamp,Temperature,Humidity,CO2,Ammonia,Pressure,Sensor_ID\n")
            f.write("2025-04-19 10:00:54,25.8,59.5,786,10.3,24.5,ARRAY001\n")
            f.write("2025-04-19 10:01:54,26.1,58.2,790,10.5,24.8,ARRAY001\n")

        readings = storage.get_readings_for_day(datetime(2025, 4, 19))
        assert len(readings) == 2
        assert readings[0].temperature == 25.8
        assert readings[0].external_temp == 25.8  # Deve usar temperatura como temperatura externa
        assert readings[0].humidity == 59.5
        assert readings[0].power_ok is True  # Deve padrão para True

    def test_get_readings_for_day_new_format(self, storage, temp_dir):
        """Testa a leitura de dados de sensor no formato novo."""
        # Cria arquivo de dados de teste
        log_file = Path(temp_dir) / "logs" / "readings_20250419.txt"
        log_file.parent.mkdir(exist_ok=True)
        with open(log_file, "w") as f:
            f.write("Timestamp,Temperature,External_Temp,Humidity,CO2,Ammonia,Pressure,Power_OK,Sensor_ID\n")
            f.write("2025-04-19 10:00:54,25.8,24.5,59.5,786,10.3,24.5,true,ARRAY001\n")
            f.write("2025-04-19 10:01:54,26.1,25.0,58.2,790,10.5,24.8,false,ARRAY001\n")

        readings = storage.get_readings_for_day(datetime(2025, 4, 19))
        assert len(readings) == 2
        assert readings[0].temperature == 25.8
        assert readings[0].external_temp == 24.5
        assert readings[0].humidity == 59.5
        assert readings[0].power_ok is True
        assert readings[1].power_ok is False

    def test_export_readings(self, storage, temp_dir):
        """Testa a exportação de leituras de sensor."""
        # Cria arquivo de dados de teste
        log_file = Path(temp_dir) / "logs" / "readings_20250419.txt"
        log_file.parent.mkdir(exist_ok=True)
        with open(log_file, "w") as f:
            f.write("Timestamp,Temperature,Humidity,CO2,Ammonia,Pressure,Sensor_ID\n")
            f.write("2025-04-19 10:00:54,25.8,59.5,786,10.3,24.5,ARRAY001\n")

        # Exporta as leituras
        result = storage.export_readings(datetime(2025, 4, 19))
        assert result is True

        # Verifica arquivo exportado
        export_file = Path(temp_dir) / "exports" / "readings_20250419_export.csv"
        assert export_file.exists()

        # Verifica conteúdo exportado
        with open(export_file) as f:
            lines = f.readlines()
            assert len(lines) == 2  # Cabeçalho + 1 leitura
            assert lines[0].strip() == "Timestamp,Temperature,External_Temp,Humidity,CO2,Ammonia,Pressure,Power_OK,Sensor_ID"
            # Dados no formato antigo devem ser convertidos para o novo formato
            parts = lines[1].strip().split(",")
            assert len(parts) == 9
            assert parts[1] == "25.8"  # Temperatura
            assert parts[2] == "25.8"  # Temperatura externa deve ser igual à temperatura
            assert parts[7] == "true"  # Power OK deve padrão para true