import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import unittest
from unittest.mock import MagicMock, patch

from src.storage.oracle_db import OracleStorage
from src.models.config import EnvironmentalLimits, SystemConfig
from main import AviaryControlSystem


class TestOracleStorageConfigPersistence(unittest.TestCase):
    @patch("src.storage.oracle_db.oracledb.connect")
    def test_save_config_executes_correct_updates(self, mock_connect):
        # Arrange - simula conexão e cursor
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

        # Cria instância com mocks
        storage = OracleStorage("user", "pass", "dsn")
        storage.connect()  # chama mockado
        config = SystemConfig(environmental_limits=EnvironmentalLimits(
            temp_min=18.0,
            temp_max=32.0,
            humidity_min=50.0,
            humidity_max=70.0,
            co2_max=2000.0,
            ammonia_max=25.0,
            pressure_target=25.0
        ))

        # Act - chama a função alvo
        mock_cursor.reset_mock()
        storage.save_config(config)

        # Assert - verifica se foram feitos updates
        expected_calls = [
            (('UPDATE system_config SET param_value = :param_value, updated_at = CURRENT_TIMESTAMP '
              'WHERE param_name = :param_name',), {'param_name': 'temp_min', 'param_value': '18.0'}),
            ({'param_name': 'temp_max', 'param_value': '32.0'}),
            ({'param_name': 'humidity_min', 'param_value': '50.0'}),
            ({'param_name': 'humidity_max', 'param_value': '70.0'}),
            ({'param_name': 'co2_max', 'param_value': '2000.0'}),
            ({'param_name': 'ammonia_max', 'param_value': '25.0'}),
            ({'param_name': 'pressure_target', 'param_value': '25.0'}),
        ]

        # Verifica que cada parâmetro foi atualizado
        executed_param_names = []
        for call in mock_cursor.execute.call_args_list:
            if len(call.args) >= 2 and isinstance(call.args[1], dict):
                params = call.args[1]
                if "param_name" in params:
                    executed_param_names.append(params["param_name"])

        for expected_param in [
            "temp_min", "temp_max", "humidity_min", "humidity_max",
            "co2_max", "ammonia_max", "pressure_target"
        ]:
            self.assertIn(expected_param, executed_param_names)

        # Verifica se commit foi chamado
        mock_conn.commit.assert_called_once()

    @patch("src.storage.oracle_db.oracledb.connect")
    @patch("time.sleep")  # Mock sleep para não atrasar o teste
    def test_configure_oracle_retry_mechanism(self, mock_sleep, mock_connect):
        """Testa o mecanismo de retry na configuração do Oracle."""
        # Configura o mock para falhar nas primeiras tentativas e depois ter sucesso
        mock_connect.side_effect = [
            Exception("Falha na primeira tentativa"),
            MagicMock()  # Sucesso na segunda tentativa
        ]
        
        # Configura mocks adicionais
        with patch('src.sensors.reader.SensorReader'), \
             patch('src.storage.oracle_db.OracleStorage.test_connection', return_value=True), \
             patch('src.storage.oracle_db.OracleStorage.check_schema_exists', 
                   return_value={"sensor_readings": True, "actuator_status": True, "alarm_events": True, "system_config": True,
                                "reading_seq": True, "status_seq": True, "event_seq": True, "config_seq": True}):
            
            # Cria o sistema
            system = AviaryControlSystem(use_oracle=False)
            
            # Tenta configurar Oracle
            result = system.configure_oracle("test_user", "test_password", "test_dsn")
            
            # Verifica se o resultado é True (sucesso após retry)
            self.assertTrue(result)
            
            # Verifica se connect foi chamado duas vezes (falha + sucesso)
            self.assertEqual(mock_connect.call_count, 2)
            
            # Verifica se using_mock_data está False
            self.assertFalse(system.using_mock_data)


if __name__ == "__main__":
    unittest.main()


