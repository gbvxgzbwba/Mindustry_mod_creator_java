import os
import sys
import json
import requests
import tempfile
import subprocess
import shutil
from pathlib import Path
from datetime import datetime
from packaging import version

class AutoUpdater:
    def __init__(self, repo_url, exe_configs=None, version_file_name="version.json"):
        """
        Инициализация автообновления с поддержкой нескольких EXE файлов
        
        Args:
            repo_url: URL репозитория GitHub (например, "username/repo")
            exe_configs: Список словарей с конфигурациями EXE файлов
                       [{"name": "MindustryModCreator.exe", "version_prefix": "noConsole"}, 
                        {"name": "MindustryModCreatorConsole.exe", "version_prefix": "Console"}]
            version_file_name: Имя файла для хранения версии
        """
        self.repo_url = repo_url
        self.version_file_name = version_file_name
        
        # Если exe_configs не передан, используем стандартные
        if exe_configs is None:
            self.exe_configs = [
                {"name": "MindustryModCreator.exe", "version_prefix": "noConsole"},
                {"name": "MindustryModCreatorConsole.exe", "version_prefix": "Console"}
            ]
        else:
            self.exe_configs = exe_configs
            
        # Правильный URL для GitHub API
        self.api_url = f"https://api.github.com/repos/{repo_url}/releases/latest"
        
        # Определяем директории
        if getattr(sys, 'frozen', False):
            self.current_dir = os.path.dirname(sys.executable)
        else:
            self.current_dir = os.path.dirname(os.path.abspath(__file__))
            # Поднимаемся к корню проекта
            self.current_dir = os.path.dirname(os.path.dirname(self.current_dir))
        
        self.version_path = os.path.join(self.current_dir, version_file_name)
        
        # Определяем текущий EXE файл
        self.current_exe = os.path.basename(sys.executable) if getattr(sys, 'frozen', False) else None
        self.current_config = self._find_current_config()
        
        # Загружаем настройки (используем тот же путь, что и в creator_editor.py)
        self.settings = self._load_settings()
        
        # Флаг автообновления (по умолчанию True, если настройка не найдена)
        self.autoupdate_enabled = self._get_autoupdate_setting()
        
        print(f"Текущая директория: {self.current_dir}")
        print(f"Текущий EXE: {self.current_exe}")
        print(f"Файл версии: {self.version_path}")
        print(f"Автообновление: {'Включено' if self.autoupdate_enabled else 'Отключено'}")
    
    def _load_settings(self):
        """Загрузить настройки из файла settings.json в APPDATA"""
        try:
            # Используем тот же путь, что и в creator_editor.py
            appdata = os.getenv('APPDATA') or os.path.expanduser("~")
            settings_dir = Path(appdata) / "MindustryModCreator"
            settings_dir.mkdir(parents=True, exist_ok=True)
            settings_file = settings_dir / "settings.json"
            
            if settings_file.exists():
                with open(settings_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                # Если файла нет, создаем с настройками по умолчанию
                default_settings = {
                    "autoupdate": True,
                    "language": "ru",
                    "save_folder": "mods",
                    "hide_content": False,
                    "game_path": ""
                }
                self._save_settings(default_settings)
                return default_settings
        except Exception as e:
            print(f"Ошибка при загрузке настроек: {e}")
            return {"autoupdate": True}
    
    def _save_settings(self, settings):
        """Сохранить настройки в файл settings.json в APPDATA"""
        try:
            appdata = os.getenv('APPDATA') or os.path.expanduser("~")
            settings_dir = Path(appdata) / "MindustryModCreator"
            settings_dir.mkdir(parents=True, exist_ok=True)
            settings_file = settings_dir / "settings.json"
            
            with open(settings_file, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Ошибка при сохранении настроек: {e}")
            return False
    
    def _get_autoupdate_setting(self):
        """Получить значение настройки автообновления"""
        return self.settings.get("autoupdate", True)
    
    def set_autoupdate(self, enabled):
        """Установить настройку автообновления"""
        self.settings["autoupdate"] = enabled
        self.autoupdate_enabled = enabled
        return self._save_settings(self.settings)
    
    def toggle_autoupdate(self):
        """Переключить настройку автообновления"""
        new_value = not self.autoupdate_enabled
        return self.set_autoupdate(new_value)
    
    def _find_current_config(self):
        """Найти конфигурацию для текущего EXE файла"""
        if not self.current_exe:
            # Если запущено как скрипт, используем первую конфигурацию
            return self.exe_configs[0] if self.exe_configs else None
        
        for config in self.exe_configs:
            if config.get('name') == self.current_exe:
                return config
        return None
    
    def get_current_version(self): 
        """Получить текущую версию из файла"""
        try:
            if os.path.exists(self.version_path):
                with open(self.version_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # Если есть несколько версий для разных EXE
                    exe_name = self.current_exe or self.exe_configs[0]['name']
                    return data.get(exe_name, {}).get('version', '4.5.0')
        except Exception as e:
            print(f"Ошибка чтения версии: {e}")
        return '4.5.0'
    
    def save_current_version(self, version_str):
        """Сохранить текущую версию в файл"""
        try:
            # Загружаем существующие данные
            data = {}
            if os.path.exists(self.version_path):
                with open(self.version_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            
            # Обновляем версию для текущего EXE
            exe_name = self.current_exe or self.exe_configs[0]['name']
            if exe_name not in data:
                data[exe_name] = {}
            data[exe_name]['version'] = version_str
            data[exe_name]['last_update'] = str(datetime.now())
            
            with open(self.version_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Ошибка при сохранении версии: {e}")
            return False
    
    def get_latest_release(self):
        """Получить информацию о последнем релизе с GitHub"""
        try:
            print(f"Запрос к GitHub API: {self.api_url}")
            headers = {
                'Accept': 'application/vnd.github.v3+json',
                'User-Agent': 'Mindustry-Java-Mod-Creator'
            }
            
            response = requests.get(self.api_url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                # Получаем версию релиза
                version_tag = data.get('tag_name', '').lstrip('v')
                
                # Фильтруем активы для нашего EXE
                assets_by_name = {}
                for config in self.exe_configs:
                    exe_name = config['name']
                    # Ищем актив с соответствующим именем
                    for asset in data.get('assets', []):
                        asset_name = asset.get('name', '')
                        if asset_name == exe_name:
                            assets_by_name[exe_name] = {
                                'name': asset_name,
                                'download_url': asset.get('browser_download_url'),
                                'size': asset.get('size', 0)
                            }
                            break
                
                return {
                    'version': version_tag,
                    'assets': assets_by_name,
                    'all_assets': data.get('assets', [])
                }
            else:
                print(f"Ошибка API: {response.status_code}")
                return None
        except Exception as e:
            print(f"Ошибка при проверке обновлений: {e}")
            return None
    
    def find_exe_asset(self, assets_by_name):
        """Найти EXE файл в активах релиза для текущей конфигурации"""
        if not self.current_config:
            print("Не найдена конфигурация для текущего EXE файла")
            return None
        
        exe_name = self.current_config['name']
        return assets_by_name.get(exe_name)
    
    def download_update(self, download_url, target_path):
        """Скачать обновление"""
        try:
            print(f"Скачивание обновления для {os.path.basename(target_path)}")
            response = requests.get(download_url, stream=True, timeout=30)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            
            with open(target_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total_size > 0:
                            progress = (downloaded / total_size) * 100
                            print(f"Прогресс: {progress:.1f}%", end='\r')
            
            print("\nСкачивание завершено!")
            return True
        except Exception as e:
            print(f"Ошибка при скачивании: {e}")
            return False
    
    def create_updater_script(self, new_exe_path, old_exe_path):
        """Создать временный скрипт для обновления"""
        try:
            temp_dir = tempfile.mkdtemp()
            updater_script = os.path.join(temp_dir, "updater.bat")
            
            old_exe_name = os.path.basename(old_exe_path)
            new_exe_name = os.path.basename(new_exe_path)
            
            script_content = f"""@echo off
chcp 65001 >nul
title Обновление Mindustry Java Mod Creator

echo ========================================
echo    Обновление программы ({old_exe_name})
echo ========================================
echo.

:retry
echo Попытка закрыть программу...
taskkill /f /im "{old_exe_name}" 2>nul
timeout /t 2 /nobreak > nul

if exist "{old_exe_path}" (
    echo Удаление старой версии...
    attrib -r -h -s "{old_exe_path}" 2>nul
    del /f /q "{old_exe_path}" 2>nul
    
    if exist "{old_exe_path}" (
        echo Повторная попытка удаления...
        goto retry
    )
)

echo Копирование новой версии...
copy /y "{new_exe_path}" "{old_exe_path}"

if exist "{old_exe_path}" (
    echo Запуск новой версии...
    start "" "{old_exe_path}"
) else (
    echo ОШИБКА: Не удалось скопировать файл!
    pause
)

echo Удаление временных файлов...
del /f /q "{new_exe_path}" 2>nul
rd /s /q "{temp_dir}" 2>nul

echo Обновление завершено!
del /f /q "%~f0"
"""
            
            with open(updater_script, 'w', encoding='utf-8') as f:
                f.write(script_content)
            
            return updater_script
        except Exception as e:
            print(f"Ошибка при создании скрипта обновления: {e}")
            return None
    
    def perform_update(self, new_exe_path, latest_version):
        """Выполнить обновление"""
        try:
            old_exe_path = os.path.join(self.current_dir, self.current_exe or self.exe_configs[0]['name'])
            
            # Создаем скрипт обновления
            updater_script = self.create_updater_script(new_exe_path, old_exe_path)
            
            if not updater_script:
                print("Не удалось создать скрипт обновления")
                return False
            
            # Сохраняем новую версию в файл
            self.save_current_version(latest_version)
            
            # Запускаем скрипт обновления
            print("Запуск обновления...")
            subprocess.Popen([updater_script], shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
            
            # Закрываем текущее приложение
            sys.exit(0)
            
            return True
        except Exception as e:
            print(f"Ошибка при обновлении: {e}")
            return False
    
    def check_and_update(self, show_dialog=False, parent=None, check_autoupdate=True):
        """
        Проверить наличие обновлений и выполнить обновление если нужно
        
        Args:
            show_dialog: Показывать ли диалог с запросом подтверждения
            parent: Родительское окно для диалога
            check_autoupdate: Проверять ли настройку автообновления
        """
        # Проверяем настройку автообновления
        if check_autoupdate and not self.autoupdate_enabled:
            print("=" * 50)
            print("Автообновление отключено в настройках")
            print("=" * 50)
            return False
        
        print("=" * 50)
        print("Проверка обновлений...")
        print("=" * 50)
        
        if not self.current_config:
            print("Не удалось определить текущую конфигурацию EXE файла")
            return False
        
        # Получаем текущую версию
        current_version = self.get_current_version()
        exe_name = self.current_config['name']
        print(f"Текущий EXE: {exe_name}")
        print(f"Текущая версия: {current_version}")
        
        # Получаем последний релиз
        release_info = self.get_latest_release()
        if not release_info:
            print("Не удалось получить информацию о последнем релизе")
            return False
        
        latest_version = release_info['version']
        print(f"Последняя версия: {latest_version}")
        
        # Сравниваем версии
        try:
            if version.parse(current_version) >= version.parse(latest_version):
                print("Программа уже обновлена до последней версии")
                return False
        except Exception as e:
            print(f"Ошибка сравнения версий: {e}")
            # В случае ошибки считаем, что нужно обновить
            pass
        
        print(f"Доступно обновление: {current_version} -> {latest_version}")
        
        # Если нужно показать диалог
        if show_dialog and parent:
            try:
                import tkinter.messagebox as messagebox
                response = messagebox.askyesno(
                    "Доступно обновление",
                    f"Доступна новая версия {latest_version}!\n"
                    f"Текущая версия: {current_version}\n\n"
                    "Хотите обновить программу сейчас?"
                )
                if not response:
                    return False
            except:
                pass
        
        # Ищем EXE файл в активах
        exe_asset = self.find_exe_asset(release_info['assets'])
        if not exe_asset:
            print(f"EXE файл '{exe_name}' не найден в релизе")
            print("Доступные активы:")
            for asset_name in release_info['assets'].keys():
                print(f"  - {asset_name}")
            return False
        
        print(f"Найден файл: {exe_asset['name']}")
        print(f"Размер: {exe_asset['size'] / 1024 / 1024:.2f} MB")
        
        # Создаем временный файл для скачивания
        temp_exe_path = os.path.join(tempfile.gettempdir(), f"update_{exe_asset['name']}")
        
        # Скачиваем обновление
        if not self.download_update(exe_asset['download_url'], temp_exe_path):
            print("Ошибка при скачивании обновления")
            return False
        
        # Проверяем, что файл скачался
        if not os.path.exists(temp_exe_path) or os.path.getsize(temp_exe_path) == 0:
            print("Скачанный файл поврежден или пуст")
            return False
        
        # Выполняем обновление
        return self.perform_update(temp_exe_path, latest_version)
    
    def check_and_update_autostart(self):
        """Проверить обновления при автоматическом запуске (с учетом настройки)"""
        return self.check_and_update(show_dialog=False, check_autoupdate=True)
    
    def get_all_exe_names(self):
        """Получить список всех доступных EXE файлов"""
        return [config['name'] for config in self.exe_configs]
    
    def get_autoupdate_status(self):
        """Получить статус автообновления"""
        return self.autoupdate_enabled


if __name__ == "__main__":
    # Тестирование модуля
    print("Тестирование модуля обновления...")
    
    # Настройки
    REPO_URL = "gbvxgzbwba/Mindustry_mod_creator_java"
    
    # Конфигурации для двух EXE файлов
    EXE_CONFIGS = [
        {"name": "MindustryModCreator.exe", "version_prefix": "noConsole"},
        {"name": "MindustryModCreatorConsole.exe", "version_prefix": "Console"}
    ]
    
    # Создаем экземпляр обновления
    updater = AutoUpdater(REPO_URL, EXE_CONFIGS)
    
    # Выводим информацию о текущем EXE
    print(f"Текущий EXE файл: {updater.current_exe}")
    print(f"Доступные EXE файлы: {updater.get_all_exe_names()}")
    print(f"Статус автообновления: {'Включено' if updater.autoupdate_enabled else 'Отключено'}")
    
    # Проверяем обновления с учетом настройки автообновления
    if updater.check_and_update_autostart():
        print("Обновление выполнено успешно!")
    else:
        print("Обновление не требуется или автообновление отключено")