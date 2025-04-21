####################################
##### Arquivo: test_logging_config.py
##### Desenvolvedor: Juan F. Voltolini
##### Instituição: FIAP
##### Trabalho: Cap 6 - Python e Além
##### Grupo: Alexander Dorneles de Oliveira, Felipe Sabino da Silva, Juan Felipe Voltolini, Luiz Henrique Ribeiro de Oliveira e Marco Aurélio Eberhardt Assumpção
####################################

"""Testes unitários para verificar a configuração de logging."""
import logging
import os
import pytest
import tempfile
from unittest.mock import patch, MagicMock

import main


class TestLoggingConfiguration:
    """Casos de teste para a configuração de logging."""

    def test_logging_config_no_console_output(self):
        """Testa se a configuração de logging não inclui saída para o console."""
        # Salvar handlers atuais
        root_logger = logging.getLogger()
        original_handlers = root_logger.handlers.copy()
        
        try:
            # Limpar handlers existentes
            for handler in root_logger.handlers[:]:
                root_logger.removeHandler(handler)
            
            # Criar diretório temporário para logs
            with tempfile.TemporaryDirectory() as temp_dir:
                # Patch os.makedirs para não criar diretórios reais
                with patch('os.makedirs') as mock_makedirs:
                    # Patch logging.FileHandler para não criar arquivos reais
                    with patch('logging.FileHandler') as mock_file_handler:
                        # Patch logging.StreamHandler para detectar se é usado
                        with patch('logging.StreamHandler') as mock_stream_handler:
                            # Reconfigurar logging como no main.py
                            logging.basicConfig(
                                level=logging.INFO,
                                format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
                                handlers=[
                                    logging.FileHandler("data/logs/aviary_control.log"),
                                ],
                            )
                            
                            # Verificar se FileHandler foi chamado
                            mock_file_handler.assert_called_once()
                            
                            # Verificar se StreamHandler não foi chamado
                            mock_stream_handler.assert_not_called()
                            
                            # Verificar se não há handlers do tipo StreamHandler
                            stream_handlers = [h for h in logging.getLogger().handlers 
                                              if isinstance(h, logging.StreamHandler) and not isinstance(h, logging.FileHandler)]
                            assert len(stream_handlers) == 0
        finally:
            # Restaurar handlers originais
            for handler in root_logger.handlers[:]:
                root_logger.removeHandler(handler)
            for handler in original_handlers:
                root_logger.addHandler(handler)

    def test_display_manager_no_terminal_output(self):
        """Testa se o DisplayManager não produz saída no terminal."""
        from src.core.display import DisplayManager
        from src.models.sensor_data import SensorReading
        from datetime import datetime
        
        # Criar uma instância do DisplayManager
        display_manager = DisplayManager()
        
        # Criar dados de teste
        reading = SensorReading(
            timestamp=datetime(2025, 4, 19, 10, 0, 0),
            temperature=25.8,
            external_temp=24.5,
            humidity=59.5,
            co2_level=786,
            ammonia_level=10.3,
            pressure=24.5,
            power_ok=True,
            sensor_id="ARRAY001"
        )
        
        # Patch a função print para detectar se é chamada
        with patch('builtins.print') as mock_print:
            # Chamar update para acionar _update_cli
            display_manager.update(reading=reading)
            
            # Verificar se print não foi chamado
            mock_print.assert_not_called()