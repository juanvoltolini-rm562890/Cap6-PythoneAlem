import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import unittest
from unittest.mock import MagicMock, patch

from src.storage.oracle_db import OracleStorage
from db.setup_db import initialize_schema
from main import AviaryControlSystem


class TestOracleConnectionFixes(unittest.TestCase):
    """Testes para as correções de conexão Oracle."""

    @patch("src.storage.oracle_db.oracledb.connect")
    def test_connect_with_retry_mechanism(self, mock_connect):
        """Testa o mecanismo de retry na conexão Oracle."""
        # Configura o mock para falhar nas primeiras tentativas e depois ter sucesso
        mock_connect.side_effect = [
            Exception("Falha na primeira tentativa"),
            Exception("Falha na segunda tentativa"),
            MagicMock()  # Sucesso na terceira tentativa
        ]
        
        # Configura o mock do cursor
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
        mock_cursor.fetchone.return_value = ["Oracle Database 19c Enterprise Edition"]
        
        # Substitui o último item da side_effect pelo mock_connection
        mock_connect.side_effect[-1] = mock_connection
        
        # Cria a instância e tenta conectar
        with patch('time.sleep') as mock_sleep:  # Mock sleep para não atrasar o teste
            storage = OracleStorage("test_user", "test_password", "test_dsn")
            storage.connect()
        
        # Verifica se connect foi chamado três vezes (duas falhas + sucesso)
        self.assertEqual(mock_connect.call_count, 3)
        
        # Verifica se sleep foi chamado para esperar entre tentativas
        self.assertEqual(mock_sleep.call_count, 2)

    @patch("src.storage.oracle_db.oracledb.connect")
    def test_ensure_connection_reconnects_on_failure(self, mock_connect):
        """Testa se _ensure_connection reconecta quando a conexão falha."""
        # Configura o mock para simular uma conexão inicial bem-sucedida
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_connection
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
        
        # Configura o cursor para falhar na primeira verificação e ter sucesso na segunda
        mock_cursor.execute.side_effect = [
            Exception("Conexão perdida"),  # Falha na verificação
            None,  # Sucesso na reconexão
            [1]    # Resultado da consulta após reconexão
        ]
        mock_cursor.fetchone.return_value = [1]
        
        # Cria a instância e conecta
        storage = OracleStorage("test_user", "test_password", "test_dsn")
        storage._connection = mock_connection  # Simula uma conexão já existente
        
        # Tenta garantir a conexão
        with patch('time.sleep') as mock_sleep:  # Mock sleep para não atrasar o teste
            storage._ensure_connection()
        
        # Verifica se disconnect e connect foram chamados para reconectar
        mock_connection.close.assert_called_once()
        self.assertEqual(mock_connect.call_count, 1)

    @patch("oracledb.connect")
    @patch("builtins.open", create=True)
    def test_initialize_schema_handles_errors(self, mock_open, mock_connect):
        """Testa se initialize_schema lida corretamente com erros nos comandos SQL."""
        # Configura o mock para a conexão
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_connection
        mock_connection.cursor.return_value = mock_cursor
        
        # Configura o mock para o arquivo SQL
        mock_file = MagicMock()
        mock_file.read.return_value = """
        CREATE TABLE test_table (id NUMBER);
        CREATE TABLE existing_table (id NUMBER);
        CREATE SEQUENCE test_seq;
        INSERT INTO test_table VALUES (1);
        """
        mock_open.return_value.__enter__.return_value = mock_file
        
        # Configura o cursor para simular sucesso e falha em diferentes comandos
        def execute_side_effect(sql):
            if "existing_table" in sql:
                # Simula erro ORA-00955 (objeto já existe)
                error = MagicMock()
                error.code = 955
                error.message = "name is already used by an existing object"
                raise type('oracledb.DatabaseError', (Exception,), {})(error,)
            elif "INSERT INTO" in sql:
                # Simula outro tipo de erro
                raise Exception("Erro ao inserir dados")
            # Outros comandos têm sucesso
            return None
            
        mock_cursor.execute.side_effect = execute_side_effect
        
        # Executa a função
        with patch('time.sleep') as mock_sleep:  # Mock sleep para não atrasar o teste
            result = initialize_schema("test_user", "test_password", "test_dsn")
        
        # Verifica se o resultado é True (sucesso parcial)
        self.assertTrue(result)
        
        # Verifica se commit foi chamado
        mock_connection.commit.assert_called()
        
        # Verifica se rollback foi chamado para o comando com erro
        mock_connection.rollback.assert_called()

    @patch("src.storage.oracle_db.oracledb.connect")
    def test_check_schema_exists_handles_errors(self, mock_connect):
        """Testa se check_schema_exists lida corretamente com erros nas consultas."""
        # Configura o mock para a conexão
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_connection
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
        
        # Configura o cursor para simular sucesso e falha em diferentes consultas
        def execute_side_effect(sql, params=None):
            if "user_tables" in sql and params and params.get("table_name") == "SENSOR_READINGS":
                return None  # Sucesso
            elif "user_tables" in sql:
                # Simula erro na consulta
                raise Exception("Erro ao verificar tabela")
            elif "user_sequences" in sql:
                # Simula erro na consulta de sequências
                raise Exception("Erro ao verificar sequência")
            return None
            
        mock_cursor.execute.side_effect = execute_side_effect
        mock_cursor.fetchone.return_value = [1]  # Simula que encontrou o objeto
        
        # Cria a instância e executa a função
        storage = OracleStorage("test_user", "test_password", "test_dsn")
        storage._connection = mock_connection
        result = storage.check_schema_exists()
        
        # Verifica se o resultado contém pelo menos a tabela sensor_readings
        self.assertTrue(result.get("sensor_readings", False))
        
        # Verifica se as outras tabelas e sequências estão marcadas como False
        self.assertFalse(result.get("actuator_status", True))
        self.assertFalse(result.get("reading_seq", True))

    @patch("src.storage.oracle_db.oracledb.connect")
    @patch("time.sleep")
    def test_configure_oracle_with_improved_error_handling(self, mock_sleep, mock_connect):
        """Testa o método configure_oracle com o tratamento de erros melhorado."""
        # Configura o mock para simular uma conexão bem-sucedida
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_connection
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
        mock_cursor.fetchone.return_value = [1]  # Simula resultado bem-sucedido
        
        # Configura mocks adicionais
        with patch('src.sensors.reader.SensorReader'), \
             patch('src.storage.oracle_db.OracleStorage.test_connection', return_value=True), \
             patch('src.storage.oracle_db.OracleStorage.check_schema_exists', 
                   return_value={"sensor_readings": True, "actuator_status": True, "alarm_events": True, "system_config": True,
                                "reading_seq": True, "status_seq": True, "event_seq": True, "config_seq": True}):
            
            # Cria o sistema
            system = AviaryControlSystem(use_oracle=False)
            
            # Configura o mock para simular um erro na primeira tentativa e sucesso na segunda
            mock_connect.side_effect = [
                Exception("Falha na primeira tentativa"),
                mock_connection  # Sucesso na segunda tentativa
            ]
            
            # Tenta configurar Oracle
            result = system.configure_oracle("test_user", "test_password", "test_dsn")
            
            # Verifica se o resultado é True (sucesso após retry)
            self.assertTrue(result)
            
            # Verifica se using_mock_data está False
            self.assertFalse(system.using_mock_data)
            
            # Verifica se connect foi chamado duas vezes (falha + sucesso)
            self.assertEqual(mock_connect.call_count, 2)
            
            # Verifica se sleep foi chamado para esperar entre tentativas
            mock_sleep.assert_called()


if __name__ == "__main__":
    unittest.main()