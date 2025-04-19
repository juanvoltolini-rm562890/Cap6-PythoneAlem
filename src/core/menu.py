####################################
##### Arquivo: menu.py
##### Desenvolvedor: Juan F. Voltolini
##### Instituição: FIAP
##### Trabalho: Cap 6 - Python e Além
##### Grupo: Alexander Dorneles de Oliveira, Felipe Sabino da Silva, Juan Felipe Voltolini, Luiz Henrique Ribeiro de Oliveira e Marco Aurélio Eberhardt Assumpção, 
####################################

"""
Módulo de gerenciamento do menu interativo do sistema.

Este módulo fornece a interface de usuário baseada em texto para
interagir com o sistema de controle do aviário.
"""
import sys
from datetime import datetime
from typing import Optional

from src.models.config import SystemConfig
from src.models.device import DeviceStatus, DeviceState, DeviceType
from src.models.sensor_data import SensorReading
from src.storage.file_storage import FileStorage
from src.storage.oracle_db import OracleStorage
from .display import DisplayManager, DisplayMode


class MenuManager:
    """Gerenciador do menu interativo do sistema."""

    def __init__(
        self,
        config: SystemConfig,
        file_storage: FileStorage,
        oracle_storage: Optional[OracleStorage] = None,
        display_manager: Optional['DisplayManager'] = None,
    ):
        """Inicializa o gerenciador de menu.

        Args:
            config: Configuração do sistema
            file_storage: Instância do armazenamento em arquivo
            oracle_storage: Instância opcional do armazenamento Oracle
            display_manager: Instância opcional do gerenciador de exibição
        """
        self.config = config
        self.file_storage = file_storage
        self.oracle_storage = oracle_storage
        self.display_manager = display_manager

    def display_menu(self):
        """Exibe e processa o menu interativo."""
        # Configura modo de menu se houver display manager
        if self.display_manager:
            from .display import DisplayMode
            self.display_manager.set_display_mode(DisplayMode.MENU)

        try:
            while True:
                print("\n=== Sistema de Controle de Aviário ===")
                print("1. Gerenciar Dados do Sistema")
                print("2. Visualizar Status do Sistema")
                print("3. Configurações do Sistema")
                print("0. Sair")

                try:
                    choice = input("\nEscolha uma opção: ")
                    if choice == "0":
                        print("Encerrando o sistema...")
                        break
                    elif choice == "1":
                        self._data_management_menu()
                    elif choice == "2":
                        self._system_status_menu()
                    elif choice == "3":
                        self._system_config_menu()
                    else:
                        print("Opção inválida. Por favor, tente novamente.")
                except KeyboardInterrupt:
                    print("\nOperação cancelada pelo usuário.")
                    break
                except Exception as e:
                    print(f"Erro ao processar opção: {e}")
        finally:
            # Restaura modo de status ao sair do menu
            if self.display_manager:
                from .display import DisplayMode
                self.display_manager.set_display_mode(DisplayMode.STATUS)

    def _system_config_menu(self):
        """Menu de configurações do sistema."""
        while True:
            print("\n=== Configurações do Sistema ===")
            print("1. Visualizar configurações atuais")
            print("2. Menu de Parâmetros")
            print("3. Menu de Histórico")
            print("0. Voltar")

            try:
                choice = input("\nEscolha uma opção: ")
                if choice == "0":
                    break
                elif choice == "1":
                    self._show_current_config()
                elif choice == "2":
                    self._parameters_menu()
                elif choice == "3":
                    self._history_menu()
                else:
                    print("Opção inválida. Por favor, tente novamente.")
            except Exception as e:
                print(f"Erro ao processar opção: {e}")

    def _parameters_menu(self):
        """Menu de configuração de parâmetros."""
        print("\n=== Menu de Parâmetros ===")
        limits = self.config.environmental_limits
        
        try:
            # Temperatura
            print("\n--- Configurações de Temperatura ---")
            temp_target = float(input(f"Temperatura desejada [{(limits.temp_min + limits.temp_max) / 2}°C]: ") or (limits.temp_min + limits.temp_max) / 2)
            temp_max = float(input(f"Temperatura máxima (+5°C) [{temp_target + 5}°C]: ") or temp_target + 5)
            temp_min = float(input(f"Temperatura mínima (-5°C) [{temp_target - 5}°C]: ") or temp_target - 5)
            
            # Umidade
            print("\n--- Configurações de Umidade ---")
            humidity_target = float(input(f"Umidade desejada [{(limits.humidity_min + limits.humidity_max) / 2}%]: ") or (limits.humidity_min + limits.humidity_max) / 2)
            humidity_max = float(input(f"Umidade máxima [{humidity_target + 10}%]: ") or humidity_target + 10)
            humidity_min = float(input(f"Umidade mínima [{humidity_target - 10}%]: ") or humidity_target - 10)
            
            # Gases e Pressão
            print("\n--- Configurações de Gases e Pressão ---")
            co2_max = float(input(f"CO₂ máximo (ppm) [{limits.co2_max}]: ") or limits.co2_max)
            ammonia_max = float(input(f"Amônia máxima (ppm) [{limits.ammonia_max}]: ") or limits.ammonia_max)
            pressure_target = float(input(f"Pressão alvo (Pa) [{limits.pressure_target}]: ") or limits.pressure_target)
            
            # Atualizar configurações
            limits.temp_min = temp_min
            limits.temp_max = temp_max
            limits.humidity_min = humidity_min
            limits.humidity_max = humidity_max
            limits.co2_max = co2_max
            limits.ammonia_max = ammonia_max
            limits.pressure_target = pressure_target
            
            # Salvar configurações
            self.file_storage.save_config(self.config)
            print("\nParâmetros atualizados com sucesso!")
            
        except ValueError:
            print("Erro: Por favor, insira apenas valores numéricos.")
        except Exception as e:
            print(f"Erro ao atualizar parâmetros: {e}")
        
        input("\nPressione Enter para continuar...")

    def _history_menu(self):
        """Menu de gerenciamento de histórico."""
        while True:
            print("\n=== Menu de Histórico ===")
            print("1. Ver histórico")
            print("2. Apagar histórico")
            print("0. Voltar")

            try:
                choice = input("\nEscolha uma opção: ")
                if choice == "0":
                    break
                elif choice == "1":
                    self._view_history()
                elif choice == "2":
                    self._delete_history()
                else:
                    print("Opção inválida. Por favor, tente novamente.")
            except Exception as e:
                print(f"Erro ao processar opção: {e}")

    def _view_history(self):
        """Visualiza o histórico de leituras."""
        print("\n=== Histórico de Leituras ===")
        try:
            # Obter lista de dias com leituras
            days = self.file_storage.get_available_days()
            if not days:
                print("Nenhum histórico disponível.")
                return

            print("\nDias disponíveis:")
            for i, day in enumerate(days, 1):
                print(f"{i}. {day:%Y-%m-%d}")

            # Selecionar dia
            choice = int(input("\nEscolha um dia para visualizar (0 para voltar): "))
            if choice == 0 or choice > len(days):
                return

            selected_day = days[choice - 1]
            readings = self.file_storage.get_readings_for_day(selected_day)

            print(f"\nLeituras para {selected_day:%Y-%m-%d}:")
            for reading in readings:
                print(f"\nHorário: {reading.timestamp:%H:%M:%S}")
                print(f"Temperatura: {reading.temperature}°C (Externa: {reading.external_temp}°C)")
                print(f"Umidade: {reading.humidity}%")
                print(f"CO₂: {reading.co2_level} ppm")
                print(f"Amônia: {reading.ammonia_level} ppm")
                print(f"Pressão: {reading.pressure} Pa")
                print(f"Energia: {'OK' if reading.power_ok else 'Bateria'}")

        except ValueError:
            print("Erro: Por favor, insira um número válido.")
        except Exception as e:
            print(f"Erro ao visualizar histórico: {e}")
        
        input("\nPressione Enter para continuar...")

    def _delete_history(self):
        """Apaga o histórico de leituras."""
        print("\n=== Apagar Histórico ===")
        try:
            # Confirmar exclusão
            confirm = input("Tem certeza que deseja apagar todo o histórico? (s/N): ")
            if confirm.lower() != 's':
                print("\nOperação cancelada.")
                return

            # Apagar histórico
            self.file_storage.clear_history()
            print("\nHistórico apagado com sucesso!")

        except Exception as e:
            print(f"Erro ao apagar histórico: {e}")
        
        input("\nPressione Enter para continuar...")

    def _system_status_menu(self):
        """Menu de visualização do status do sistema."""
        while True:
            print("\n=== Status do Sistema ===")
            print("1. Leituras Atuais dos Sensores")
            print("2. Status dos Dispositivos")
            print("3. Saúde do Sistema")
            print("0. Voltar")

            try:
                choice = input("\nEscolha uma opção: ")
                if choice == "0":
                    break
                elif choice == "1":
                    self._show_current_readings()
                elif choice == "2":
                    self._show_device_status()
                elif choice == "3":
                    self._show_system_health()
                else:
                    print("Opção inválida. Por favor, tente novamente.")
            except Exception as e:
                print(f"Erro ao processar opção: {e}")

    def _show_current_readings(self):
        """Exibe as leituras atuais dos sensores."""
        print("\n=== Leituras Atuais dos Sensores ===")
        try:
            # Tentar obter a leitura mais recente
            reading = self.file_storage.get_latest_reading()
            if reading:
                print(f"\nHorário da Leitura: {reading.timestamp:%Y-%m-%d %H:%M:%S}")
                print(f"Temperatura Interna: {reading.temperature:.1f}°C")
                print(f"Temperatura Externa: {reading.external_temp:.1f}°C")
                print(f"Umidade: {reading.humidity:.1f}%")
                print(f"Nível de CO₂: {reading.co2_level} ppm")
                print(f"Nível de Amônia: {reading.ammonia_level} ppm")
                print(f"Pressão: {reading.pressure} Pa")
                print(f"Status de Energia: {'Normal' if reading.power_ok else 'Bateria'}")
            else:
                print("\nNenhuma leitura disponível.")
        except Exception as e:
            print(f"Erro ao obter leituras: {e}")
        input("\nPressione Enter para continuar...")

    def _show_device_status(self):
        """Exibe o status atual dos dispositivos."""
        print("\n=== Status dos Dispositivos ===")
        try:
            devices = self.file_storage.get_device_status()
            if devices:
                # Group devices by type
                ventilation_devices = [d for d in devices if d.device_type in (DeviceType.EXHAUST_FAN, DeviceType.INLET)]
                climate_devices = [d for d in devices if d.device_type in (DeviceType.HEATER, DeviceType.NEBULIZER)]
                
                # Display ventilation system status
                print("\n--- Sistema de Ventilação ---")
                exhaust_fans = [d for d in ventilation_devices if d.device_type == DeviceType.EXHAUST_FAN]
                inlets = [d for d in ventilation_devices if d.device_type == DeviceType.INLET]
                
                if exhaust_fans:
                    print("Exaustores:")
                    for fan in exhaust_fans:
                        status = "Ligado" if fan.state == DeviceState.ON else "Desligado"
                        if fan.state == DeviceState.ERROR:
                            status = f"Erro: {fan.error_message}"
                        print(f"  - {fan.device_id}: {status}")
                else:
                    print("Exaustores: Não disponível")
                    
                if inlets:
                    print("\nEntradas de Ar:")
                    for inlet in inlets:
                        status = "Ligado" if inlet.state == DeviceState.ON else "Desligado"
                        if inlet.state == DeviceState.PARTIAL:
                            status = f"Parcial ({inlet.value}%)"
                        elif inlet.state == DeviceState.ERROR:
                            status = f"Erro: {inlet.error_message}"
                        print(f"  - {inlet.device_id}: {status}")
                else:
                    print("\nEntradas de Ar: Não disponível")
                
                # Display climate control system status
                print("\n--- Sistema de Climatização ---")
                heaters = [d for d in climate_devices if d.device_type == DeviceType.HEATER]
                nebulizers = [d for d in climate_devices if d.device_type == DeviceType.NEBULIZER]
                
                if heaters:
                    print("Aquecedores:")
                    for heater in heaters:
                        status = "Ligado" if heater.state == DeviceState.ON else "Desligado"
                        if heater.state == DeviceState.ERROR:
                            status = f"Erro: {heater.error_message}"
                        print(f"  - {heater.device_id}: {status}")
                else:
                    print("Aquecedores: Não disponível")
                    
                if nebulizers:
                    print("\nNebulizadores:")
                    for neb in nebulizers:
                        status = "Ligado" if neb.state == DeviceState.ON else "Desligado"
                        if neb.state == DeviceState.ERROR:
                            status = f"Erro: {neb.error_message}"
                        print(f"  - {neb.device_id}: {status}")
                else:
                    print("\nNebulizadores: Não disponível")
            else:
                print("\nStatus dos dispositivos não disponível.")
        except Exception as e:
            print(f"Erro ao obter status dos dispositivos: {e}")
        input("\nPressione Enter para continuar...")

    def _show_system_health(self):
        """Exibe informações sobre a saúde do sistema."""
        print("\n=== Saúde do Sistema ===")
        try:
            # Verificar conexão com sensores
            reading = self.file_storage.get_latest_reading()
            sensor_status = "OK" if reading and (datetime.now() - reading.timestamp).seconds < 300 else "Falha"
            
            # Verificar armazenamento
            storage_ok = True
            try:
                self.file_storage.get_available_days()
            except:
                storage_ok = False
            
            # Verificar banco Oracle se disponível
            oracle_status = "N/A"
            if self.oracle_storage:
                try:
                    self.oracle_storage.test_connection()
                    oracle_status = "Conectado"
                except:
                    oracle_status = "Falha"
            
            print("\n--- Status dos Componentes ---")
            print(f"Sensores: {sensor_status}")
            print(f"Armazenamento Local: {'OK' if storage_ok else 'Falha'}")
            print(f"Banco de Dados Oracle: {oracle_status}")
            
            if reading:
                print("\n--- Alertas ---")
                limits = self.config.environmental_limits
                if reading.temperature > limits.temp_max:
                    print("⚠️ Temperatura acima do limite!")
                if reading.temperature < limits.temp_min:
                    print("⚠️ Temperatura abaixo do limite!")
                if reading.humidity > limits.humidity_max:
                    print("⚠️ Umidade acima do limite!")
                if reading.humidity < limits.humidity_min:
                    print("⚠️ Umidade abaixo do limite!")
                if reading.co2_level > limits.co2_max:
                    print("⚠️ Nível de CO₂ acima do limite!")
                if reading.ammonia_level > limits.ammonia_max:
                    print("⚠️ Nível de Amônia acima do limite!")
                if not reading.power_ok:
                    print("⚠️ Sistema operando com energia de backup!")
            
        except Exception as e:
            print(f"Erro ao verificar saúde do sistema: {e}")
        input("\nPressione Enter para continuar...")

    def _data_management_menu(self):
        """Menu de gerenciamento de dados do sistema."""
        while True:
            print("\n=== Gerenciamento de Dados ===")
            print("1. Exportar Dados")
            print("2. Importar Dados")
            print("3. Backup do Sistema")
            print("4. Limpar Dados")
            print("0. Voltar")

            try:
                choice = input("\nEscolha uma opção: ")
                if choice == "0":
                    break
                elif choice == "1":
                    self._export_data()
                elif choice == "2":
                    self._import_data()
                elif choice == "3":
                    self._backup_system()
                elif choice == "4":
                    self._clear_data()
                else:
                    print("Opção inválida. Por favor, tente novamente.")
            except Exception as e:
                print(f"Erro ao processar opção: {e}")

    def _export_data(self):
        """Exporta dados do sistema."""
        print("\n=== Exportar Dados ===")
        try:
            # Obter lista de dias com leituras
            days = self.file_storage.get_available_days()
            if not days:
                print("Nenhum dado disponível para exportação.")
                input("\nPressione Enter para continuar...")
                return

            print("\nDias disponíveis:")
            for i, day in enumerate(days, 1):
                print(f"{i}. {day:%Y-%m-%d}")

            print("\nOpções de exportação:")
            print("1. Exportar dia específico")
            print("2. Exportar todos os dados")
            print("0. Voltar")

            choice = input("\nEscolha uma opção: ")
            if choice == "0":
                return
            elif choice == "1":
                day_choice = int(input("\nEscolha o número do dia para exportar: "))
                if 1 <= day_choice <= len(days):
                    selected_day = days[day_choice - 1]
                    self.file_storage.export_readings(selected_day)
                    print(f"\nDados do dia {selected_day:%Y-%m-%d} exportados com sucesso!")
                else:
                    print("\nDia inválido selecionado.")
            elif choice == "2":
                self.file_storage.export_all_readings()
                print("\nTodos os dados foram exportados com sucesso!")
            else:
                print("\nOpção inválida.")

        except Exception as e:
            print(f"\nErro ao exportar dados: {e}")
        input("\nPressione Enter para continuar...")

    def _import_data(self):
        """Importa dados para o sistema."""
        print("\n=== Importar Dados ===")
        try:
            print("\nOpções de importação:")
            print("1. Importar arquivo de leituras")
            print("2. Importar configurações")
            print("0. Voltar")

            choice = input("\nEscolha uma opção: ")
            if choice == "0":
                return
            elif choice == "1":
                filepath = input("\nDigite o caminho do arquivo de leituras: ")
                self.file_storage.import_readings(filepath)
                print("\nDados importados com sucesso!")
            elif choice == "2":
                filepath = input("\nDigite o caminho do arquivo de configurações: ")
                self.file_storage.import_config(filepath)
                print("\nConfigurações importadas com sucesso!")
            else:
                print("\nOpção inválida.")

        except Exception as e:
            print(f"\nErro ao importar dados: {e}")
        input("\nPressione Enter para continuar...")

    def _backup_system(self):
        """Realiza backup do sistema."""
        print("\n=== Backup do Sistema ===")
        try:
            print("\nOpções de backup:")
            print("1. Backup completo")
            print("2. Backup apenas de dados")
            print("3. Backup apenas de configurações")
            print("0. Voltar")

            choice = input("\nEscolha uma opção: ")
            if choice == "0":
                return
            elif choice in ["1", "2", "3"]:
                backup_path = self.file_storage.create_backup(
                    include_data=choice in ["1", "2"],
                    include_config=choice in ["1", "3"]
                )
                print(f"\nBackup criado com sucesso em: {backup_path}")
            else:
                print("\nOpção inválida.")

        except Exception as e:
            print(f"\nErro ao criar backup: {e}")
        input("\nPressione Enter para continuar...")

    def _clear_data(self):
        """Limpa dados do sistema."""
        print("\n=== Limpar Dados ===")
        try:
            print("\nOpções de limpeza:")
            print("1. Limpar histórico de leituras")
            print("2. Restaurar configurações padrão")
            print("3. Limpar todos os dados")
            print("0. Voltar")

            choice = input("\nEscolha uma opção: ")
            if choice == "0":
                return

            confirm = input("\nATENÇÃO: Esta operação não pode ser desfeita!\nDigite 'CONFIRMAR' para prosseguir: ")
            if confirm != "CONFIRMAR":
                print("\nOperação cancelada.")
                return

            if choice == "1":
                self.file_storage.clear_history()
                print("\nHistórico de leituras apagado com sucesso!")
            elif choice == "2":
                self.file_storage.restore_default_config()
                print("\nConfigurações restauradas para o padrão!")
            elif choice == "3":
                self.file_storage.clear_all_data()
                print("\nTodos os dados foram apagados com sucesso!")
            else:
                print("\nOpção inválida.")

        except Exception as e:
            print(f"\nErro ao limpar dados: {e}")
        input("\nPressione Enter para continuar...")

    def _show_current_config(self):
        """Exibe as configurações atuais do sistema."""
        print("\n=== Configurações Atuais ===")
        limits = self.config.environmental_limits
        print("\n--- Temperatura ---")
        print(f"Temperatura desejada: {(limits.temp_min + limits.temp_max) / 2}°C")
        print(f"Temperatura máxima: {limits.temp_max}°C")
        print(f"Temperatura mínima: {limits.temp_min}°C")
        
        print("\n--- Umidade ---")
        print(f"Umidade desejada: {(limits.humidity_min + limits.humidity_max) / 2}%")
        print(f"Umidade máxima: {limits.humidity_max}%")
        print(f"Umidade mínima: {limits.humidity_min}%")
        
        print("\n--- Gases e Pressão ---")
        print(f"CO₂ máximo: {limits.co2_max} ppm")
        print(f"Amônia máxima: {limits.ammonia_max} ppm")
        print(f"Pressão alvo: {limits.pressure_target} Pa")
        input("\nPressione Enter para continuar...")



