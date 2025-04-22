####################################
##### Arquivo: test_oracle_mock_data.py
##### Desenvolvedor: AI Assistant
##### Instituição: FIAP
##### Trabalho: Cap 6 - Python e Além
##### Grupo: Alexander Dorneles de Oliveira, Felipe Sabino da Silva, Juan Felipe Voltolini, Luiz Henrique Ribeiro de Oliveira e Marco Aurélio Eberhardt Assumpção
####################################

"""Testes unitários para a integração entre OracleStorage e dados simulados."""
import unittest
from unittest.mock import MagicMock, patch

from src.storage.oracle_db import OracleStorage


class TestOracleMockData(unittest.TestCase):
    """Testes para a integração entre OracleStorage e dados simulados."""

    @patch('oracledb.connect')
    def test_get_latest_readings_with_empty_result(self, mock_connect):
        """Testa se dados simulados são gerados quando não há leituras no Oracle."""
        # Configurar mock para simular conexão bem-sucedida
        mock_connection = MagicMock()
        mock_connect.return_value = mock_connection
        
        # Configurar cursor para retornar lista vazia (sem leituras)
        mock_cursor = MagicMock()
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
        mock_cursor.fetchall.return_value = []
        
        # Criar instância de OracleStorage
        storage = OracleStorage("test_user", "test_password", "test_dsn")
        storage._connection = mock_connection
        
        # Chamar método que deve gerar dados simulados
        readings = storage.get_latest_readings(5)
        
        # Verificar se foram gerados dados simulados
        self.assertEqual(len(readings), 5)
        self.assertTrue(all(reading['reading_id'] <= 0 for reading in readings))
        
        # Verificar se os campos esperados estão presentes
        for reading in readings:
            self.assertIn('timestamp', reading)
            self.assertIn('temperature', reading)
            self.assertIn('humidity', reading)
            self.assertIn('co2_level', reading)
            self.assertIn('ammonia_level', reading)
            self.assertIn('pressure', reading)

    @patch('oracledb.connect')
    def test_get_device_status_with_empty_result(self, mock_connect):
        """Testa se dados simulados são gerados quando não há status de dispositivos no Oracle."""
        # Configurar mock para simular conexão bem-sucedida
        mock_connection = MagicMock()
        mock_connect.return_value = mock_connection
        
        # Configurar cursor para retornar lista vazia (sem status)
        mock_cursor = MagicMock()
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
        mock_cursor.fetchall.return_value = []
        
        # Criar instância de OracleStorage
        storage = OracleStorage("test_user", "test_password", "test_dsn")
        storage._connection = mock_connection
        
        # Chamar método que deve gerar dados simulados
        status_list = storage.get_device_status(limit=5)
        
        # Verificar se foram gerados dados simulados
        self.assertEqual(len(status_list), 5)
        self.assertTrue(all(status['status_id'] <= 0 for status in status_list))
        
        # Verificar se os campos esperados estão presentes
        for status in status_list:
            self.assertIn('timestamp', status)
            self.assertIn('device_type', status)
            self.assertIn('device_id', status)
            self.assertIn('status', status)
            self.assertIn('value', status)

    @patch('oracledb.connect')
    def test_get_alarms_with_empty_result(self, mock_connect):
        """Testa se dados simulados são gerados quando não há alarmes no Oracle."""
        # Configurar mock para simular conexão bem-sucedida
        mock_connection = MagicMock()
        mock_connect.return_value = mock_connection
        
        # Configurar cursor para retornar lista vazia (sem alarmes)
        mock_cursor = MagicMock()
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
        mock_cursor.fetchall.return_value = []
        
        # Criar instância de OracleStorage
        storage = OracleStorage("test_user", "test_password", "test_dsn")
        storage._connection = mock_connection
        
        # Chamar método que deve gerar dados simulados
        alarms = storage.get_alarms(limit=3)
        
        # Verificar se foram gerados dados simulados
        self.assertEqual(len(alarms), 3)
        self.assertTrue(all(alarm['event_id'] <= 0 for alarm in alarms))
        
        # Verificar se os campos esperados estão presentes
        for alarm in alarms:
            self.assertIn('timestamp', alarm)
            self.assertIn('event_type', alarm)
            self.assertIn('severity', alarm)
            self.assertIn('description', alarm)

    @patch('oracledb.connect')
    def test_get_latest_readings_with_database_error(self, mock_connect):
        """Testa se dados simulados são gerados quando ocorre erro no banco de dados."""
        # Configurar mock para simular conexão bem-sucedida
        mock_connection = MagicMock()
        mock_connect.return_value = mock_connection
        
        # Configurar cursor para lançar exceção
        mock_cursor = MagicMock()
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
        mock_cursor.execute.side_effect = Exception("Erro simulado de banco de dados")
        
        # Criar instância de OracleStorage
        storage = OracleStorage("test_user", "test_password", "test_dsn")
        storage._connection = mock_connection
        
        # Chamar método que deve gerar dados simulados
        readings = storage.get_latest_readings(5)
        
        # Verificar se foram gerados dados simulados
        self.assertEqual(len(readings), 5)
        self.assertTrue(all(reading['reading_id'] <= 0 for reading in readings))


if __name__ == "__main__":
    unittest.main()