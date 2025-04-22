import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import unittest
from unittest.mock import MagicMock, patch

from src.storage.oracle_db import OracleStorage


class TestOracleConnectionEncodingFix(unittest.TestCase):
    """Testes para a correção do problema de encoding na conexão Oracle."""

    @patch("src.storage.oracle_db.oracledb.connect")
    def test_connect_without_encoding_parameter(self, mock_connect):
        """Testa se o método connect não usa mais o parâmetro encoding."""
        # Configura o mock
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_connection
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
        mock_cursor.fetchone.return_value = ["Oracle Database 19c Enterprise Edition"]
        
        # Cria a instância e tenta conectar
        with patch('time.sleep') as mock_sleep:  # Mock sleep para não atrasar o teste
            storage = OracleStorage("test_user", "test_password", "test_dsn")
            storage.connect()
        
        # Verifica se connect foi chamado com os parâmetros corretos
        mock_connect.assert_called_once()
        
        # Verifica se os parâmetros 'encoding' e 'nencoding' não estão presentes
        args, kwargs = mock_connect.call_args
        self.assertNotIn("encoding", kwargs)
        self.assertNotIn("nencoding", kwargs)
        
        # Verifica se os parâmetros obrigatórios estão presentes
        self.assertIn("user", kwargs)
        self.assertIn("password", kwargs)
        self.assertIn("dsn", kwargs)

    def test_connection_fix_method(self):
        """Testa o método test_connection_fix."""
        # Executa o método estático que testa a correção
        result = OracleStorage.test_connection_fix()
        
        # Verifica se o resultado é True (conexão bem-sucedida)
        self.assertTrue(result)


if __name__ == "__main__":
    unittest.main()