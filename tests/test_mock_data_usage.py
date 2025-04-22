####################################
##### Arquivo: test_mock_data_usage.py
##### Desenvolvedor: AI Assistant
##### Instituição: FIAP
##### Trabalho: Cap 6 - Python e Além
####################################

"""Testes unitários para verificar o uso forçado de dados simulados."""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import unittest
from unittest.mock import MagicMock, patch

from src.storage.oracle_db import OracleStorage
from main import AviaryControlSystem


class TestMockDataUsage(unittest.TestCase):
    """Testes para verificar o uso forçado de dados simulados."""

    @patch('src.storage.oracle_db.oracledb.connect')
    def test_force_mock_data_flag(self, mock_connect):
        """Testa se o flag force_mock_data força o uso de dados simulados."""
        # Configura o mock para simular uma conexão bem-sucedida
        mock_connection = MagicMock()
        mock_connect.return_value = mock_connection
        
        # Configura o mock do cursor para retornar informações de versão
        mock_cursor = MagicMock()
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
        mock_cursor.fetchone.return_value = ["Oracle Database 19c Enterprise Edition"]
        
        # Cria o sistema com force_mock_data=True
        with patch('src.sensors.reader.SensorReader'):  # Mock para evitar threads reais
            system = AviaryControlSystem(use_oracle=True, force_mock_data=True)
            
            # Verifica se using_mock_data está True mesmo com Oracle disponível
            self.assertTrue(system.using_mock_data)
            
            # Verifica se não tentou conectar ao Oracle
            mock_connect.assert_not_called()

    @patch('src.storage.oracle_db.oracledb.connect')
    def test_oracle_connection_failure_sets_mock_data(self, mock_connect):
        """Testa se uma falha na conexão Oracle ativa o uso de dados simulados."""
        # Configura o mock para simular uma falha na conexão
        mock_connect.side_effect = Exception("Erro de conexão simulado")
        
        # Cria o sistema com use_oracle=True
        with patch('src.sensors.reader.SensorReader'):  # Mock para evitar threads reais
            system = AviaryControlSystem(use_oracle=True, force_mock_data=False)
            
            # Verifica se using_mock_data está True devido à falha na conexão
            self.assertTrue(system.using_mock_data)

    @patch('src.storage.oracle_db.oracledb.connect')
    def test_configure_oracle_respects_mock_data_flag(self, mock_connect):
        """Testa se o método configure_oracle respeita o flag using_mock_data."""
        # Configura o mock para simular uma conexão bem-sucedida
        mock_connection = MagicMock()
        mock_connect.return_value = mock_connection
        
        # Configura o mock do cursor
        mock_cursor = MagicMock()
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
        mock_cursor.fetchone.return_value = ["Oracle Database 19c Enterprise Edition"]
        
        # Cria o sistema com force_mock_data=True
        with patch('src.sensors.reader.SensorReader'):  # Mock para evitar threads reais
            system = AviaryControlSystem(use_oracle=False, force_mock_data=True)
            
            # Tenta configurar Oracle
            system.configure_oracle("test_user", "test_password", "test_dsn")
            
            # Verifica se não tentou conectar ao Oracle
            mock_connect.assert_not_called()
            
            # Verifica se using_mock_data ainda está True
            self.assertTrue(system.using_mock_data)

    @patch('src.storage.oracle_db.oracledb.connect')
    def test_handle_reading_respects_mock_data_flag(self, mock_connect):
        """Testa se o método _handle_reading respeita o flag using_mock_data."""
        # Configura o mock para simular uma conexão bem-sucedida
        mock_connection = MagicMock()
        mock_connect.return_value = mock_connection
        
        # Configura o mock do cursor
        mock_cursor = MagicMock()
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
        
        # Cria o sistema com force_mock_data=True
        with patch('src.sensors.reader.SensorReader'), \
             patch('src.storage.file_storage.FileStorage.log_sensor_reading'), \
             patch('src.models.sensor_data.SensorReading'), \
             patch('src.core.control.EnvironmentController.process_reading'), \
             patch('src.core.control.EnvironmentController.get_last_action'):
            
            # Cria o sistema com Oracle disponível mas usando dados simulados
            system = AviaryControlSystem(use_oracle=True, force_mock_data=True)
            
            # Configura o Oracle Storage como mock para verificar se é chamado
            system.oracle_storage = MagicMock()
            
            # Cria uma leitura simulada
            mock_reading = MagicMock()
            mock_reading.sensor_id = "TEST001"
            
            # Chama _handle_reading
            system._handle_reading(mock_reading)
            
            # Verifica se store_reading não foi chamado no Oracle Storage
            system.oracle_storage.store_reading.assert_not_called()


if __name__ == "__main__":
    unittest.main()