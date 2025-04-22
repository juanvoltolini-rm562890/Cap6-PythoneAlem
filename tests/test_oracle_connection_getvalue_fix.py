import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import unittest
from unittest.mock import MagicMock, patch
from datetime import datetime

from src.storage.oracle_db import OracleStorage
from src.models.sensor_data import SensorReading
from src.models.device import DeviceStatus, DeviceType, DeviceState


class TestOracleGetValueFix(unittest.TestCase):
    """Testes para a correção do erro 'function' object has no attribute 'getvalue'."""

    @patch("src.storage.oracle_db.oracledb.connect")
    def test_store_reading_with_output_variable(self, mock_connect):
        """Testa se store_reading usa corretamente a variável de saída."""
        # Configura o mock para a conexão
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_connection
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
        
        # Cria um mock para a variável de saída
        mock_var = MagicMock()
        mock_var.getvalue.return_value = 123  # ID retornado
        mock_cursor.var.return_value = mock_var
        
        # Cria a instância e conecta
        storage = OracleStorage("test_user", "test_password", "test_dsn")
        storage._connection = mock_connection  # Simula uma conexão já existente
        
        # Cria uma leitura de teste
        reading = SensorReading(
            sensor_id="sensor1",
            timestamp=datetime.now(),
            temperature=25.0,
            humidity=60.0,
            co2_level=400.0,
            ammonia_level=5.0,
            pressure=1013.0
        )
        
        # Tenta armazenar a leitura
        storage.store_reading(reading)
        
        # Verifica se var foi chamado para criar a variável de saída
        mock_cursor.var.assert_called_once_with(int)
        
        # Verifica se getvalue foi chamado na variável de saída
        mock_var.getvalue.assert_called_once()
        
        # Verifica se commit foi chamado
        mock_connection.commit.assert_called_once()

    @patch("src.storage.oracle_db.oracledb.connect")
    def test_store_device_status_with_output_variable(self, mock_connect):
        """Testa se store_device_status usa corretamente a variável de saída."""
        # Configura o mock para a conexão
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_connection
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
        
        # Cria um mock para a variável de saída
        mock_var = MagicMock()
        mock_var.getvalue.return_value = 456  # ID retornado
        mock_cursor.var.return_value = mock_var
        
        # Cria a instância e conecta
        storage = OracleStorage("test_user", "test_password", "test_dsn")
        storage._connection = mock_connection  # Simula uma conexão já existente
        
        # Cria um status de dispositivo de teste
        status = DeviceStatus(
            device_id="device1",
            device_type=DeviceType.VENTILATOR,
            state=DeviceState.ON,
            value=100.0,
            last_updated=datetime.now()
        )
        
        # Tenta armazenar o status
        storage.store_device_status(status)
        
        # Verifica se var foi chamado para criar a variável de saída
        mock_cursor.var.assert_called_once_with(int)
        
        # Verifica se getvalue foi chamado na variável de saída
        mock_var.getvalue.assert_called_once()
        
        # Verifica se commit foi chamado
        mock_connection.commit.assert_called_once()

    @patch("src.storage.oracle_db.oracledb.connect")
    def test_store_alarm_with_output_variable(self, mock_connect):
        """Testa se store_alarm usa corretamente a variável de saída."""
        # Configura o mock para a conexão
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_connection
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
        
        # Cria um mock para a variável de saída
        mock_var = MagicMock()
        mock_var.getvalue.return_value = 789  # ID retornado
        mock_cursor.var.return_value = mock_var
        
        # Cria a instância e conecta
        storage = OracleStorage("test_user", "test_password", "test_dsn")
        storage._connection = mock_connection  # Simula uma conexão já existente
        
        # Tenta armazenar um alarme
        timestamp = datetime.now()
        event_type = "TEMPERATURE_HIGH"
        description = "Temperatura acima do limite"
        storage.store_alarm(timestamp, event_type, description)
        
        # Verifica se var foi chamado para criar a variável de saída
        mock_cursor.var.assert_called_once_with(int)
        
        # Verifica se getvalue foi chamado na variável de saída
        mock_var.getvalue.assert_called_once()
        
        # Verifica se commit foi chamado
        mock_connection.commit.assert_called_once()

    @patch("src.storage.oracle_db.oracledb.connect")
    def test_integration_all_storage_methods(self, mock_connect):
        """Testa a integração de todos os métodos de armazenamento."""
        # Configura o mock para a conexão
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_connection
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
        
        # Cria mocks para as variáveis de saída
        mock_var1 = MagicMock()
        mock_var1.getvalue.return_value = 111
        mock_var2 = MagicMock()
        mock_var2.getvalue.return_value = 222
        mock_var3 = MagicMock()
        mock_var3.getvalue.return_value = 333
        
        # Configura o cursor.var para retornar diferentes variáveis em cada chamada
        mock_cursor.var.side_effect = [mock_var1, mock_var2, mock_var3]
        
        # Cria a instância e conecta
        storage = OracleStorage("test_user", "test_password", "test_dsn")
        storage._connection = mock_connection  # Simula uma conexão já existente
        
        # Configura o mock para _verify_persistence sempre retornar True
        with patch.object(storage, '_verify_persistence', return_value=True):
            # Cria objetos de teste
            reading = SensorReading(
                sensor_id="sensor1",
                timestamp=datetime.now(),
                temperature=25.0,
                humidity=60.0,
                co2_level=400.0,
                ammonia_level=5.0,
                pressure=1013.0
            )
            
            status = DeviceStatus(
                device_id="device1",
                device_type=DeviceType.VENTILATOR,
                state=DeviceState.ON,
                value=100.0,
                last_updated=datetime.now()
            )
            
            timestamp = datetime.now()
            event_type = "TEMPERATURE_HIGH"
            description = "Temperatura acima do limite"
            
            # Executa os três métodos de armazenamento
            storage.store_reading(reading)
            storage.store_device_status(status)
            storage.store_alarm(timestamp, event_type, description)
            
            # Verifica se var foi chamado três vezes
            self.assertEqual(mock_cursor.var.call_count, 3)
            
            # Verifica se getvalue foi chamado em cada variável
            mock_var1.getvalue.assert_called_once()
            mock_var2.getvalue.assert_called_once()
            mock_var3.getvalue.assert_called_once()
            
            # Verifica se commit foi chamado três vezes
            self.assertEqual(mock_connection.commit.call_count, 3)


if __name__ == "__main__":
    unittest.main()