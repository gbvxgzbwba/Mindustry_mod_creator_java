# p/Creator/ui/main_window.py
import customtkinter as ctk
import os
import platform
import subprocess
import shutil
import threading
import requests
import zipfile
import tarfile
import io
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from tkinter import messagebox
import sys
import re
from Creator.utils.lang_system import LangT, get_current_language

# Проверяем ОС для импорта winreg
if platform.system() == "Windows":
    import winreg

def resource_path(relative_path):
    """Получить абсолютный путь к ресурсу (работает и в .py, и в .exe)"""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

class MainWindow:
    def __init__(self):
        self.root = ctk.CTk()
        self.root.title("Mindustry Java Mod Creator")
        self.root.geometry("900x670")
        
        self.java_path = None
        self.java_version = None
        
        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("blue")
        
        # Загружаем настройки
        self.settings_file = Path("Creator/settings.json")
        self.settings = self.load_settings()
        
        # Используем путь из настроек или по умолчанию
        save_folder = self.settings.get("save_folder", "mods")
        Path(save_folder).mkdir(parents=True, exist_ok=True)
        
        # Проверяем Java при запуске
        self.find_and_setup_java()
        
        # Загружаем иконки
        self.root.after(100, self.load_all_icons_background)
        
        self.show_main_ui()
    
    def load_settings(self):
        """Загружает настройки из файла"""
        default_settings = {
            "language": "ru",
            "save_folder": "mods"
        }

        appdata = os.getenv('APPDATA') or os.path.expanduser("~")
        settings_dir = Path(appdata) / "MindustryModCreator"
        settings_dir.mkdir(parents=True, exist_ok=True)
        self.settings_file = settings_dir / "settings.json"

        if self.settings_file.exists():
            try:
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                    # Добавляем недостающие ключи
                    for key, value in default_settings.items():
                        if key not in settings:
                            settings[key] = value
                    return settings
            except Exception as e:
                print(LangT("Ошибка загрузки настроек:") + str(e))
                return default_settings
        else:
            self.save_settings(default_settings)
            return default_settings
    
    def save_settings(self, settings=None):
        """Сохраняет настройки в файл"""
        if settings is None:
            settings = self.settings
        
        try:
            self.settings_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(settings, f, ensure_ascii=False, indent=4)
            return True
        except Exception as e:
            print(LangT("Ошибка сохранения настроек:") + str(e))
            return False
    
    def open_settings_window(self):
        """Открывает окно настроек"""
        from Creator.utils.lang_system import get_available_languages, set_language, LangT
        
        settings_window = ctk.CTkToplevel(self.root)
        settings_window.title(LangT("Настройки"))
        settings_window.geometry("400x350")
        settings_window.transient(self.root)
        settings_window.grab_set()
        
        # Центрируем окно
        settings_window.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - (400 // 2)
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - (350 // 2)
        settings_window.geometry(f"400x350+{x}+{y}")
        
        # Язык - получаем динамически из доступных файлов
        ctk.CTkLabel(settings_window, text=LangT("Язык / Language:"), font=("Arial", 14)).pack(pady=(20, 5))
        
        available_langs = get_available_languages()
        # Преобразуем коды языков в отображаемые названия
        lang_display_names = {
            "ru": "Русский",
            "en": "English",
            # Можно добавить другие языки
        }
        
        # Создаем список для отображения
        display_values = [lang_display_names.get(lang, lang) for lang in available_langs]
        current_display = lang_display_names.get(self.settings.get("language", "ru"), self.settings.get("language", "ru"))
        
        language_var = ctk.StringVar(value=current_display)
        language_combo = ctk.CTkComboBox(
            settings_window,
            values=display_values,
            variable=language_var,
            width=200
        )
        language_combo.pack(pady=5)
        
        # Папка сохранения
        ctk.CTkLabel(settings_window, text=LangT("Папка сохранения модов:"), font=("Arial", 14)).pack(pady=(20, 5))
        
        appdata_roaming = os.getenv('APPDATA')
        
        # Словарь для отображения: текст для пользователя -> реальный путь
        folder_options = {
            LangT("Программа"): "mods",
            LangT("Игра Steam"): r"C:\Program Files (x86)\Steam\steamapps\common\Mindustry\saves\mods",
            LangT("Игра Free"): os.path.join(appdata_roaming, "Mindustry", "mods") if appdata_roaming else "mods"
        }
        
        # Получаем текущий путь и находим соответствующий отображаемый текст
        current_path = self.settings.get("save_folder", "mods")
        display_value = current_path
        for display_text, path in folder_options.items():
            if path == current_path:
                display_value = display_text
                break
        else:
            display_value = list(folder_options.keys())[0]
        
        display_var = ctk.StringVar(value=display_value)
        
        folder_combo = ctk.CTkComboBox(
            settings_window,
            values=list(folder_options.keys()),
            variable=display_var,
            width=250
        )
        folder_combo.pack(pady=5)
        
        # Кнопки
        button_frame = ctk.CTkFrame(settings_window, fg_color="transparent")
        button_frame.pack(pady=30)
        
        def save_settings():
            # Получаем выбранный язык
            selected_display = language_var.get()
            # Находим код языка по отображаемому имени
            selected_lang = None
            for lang_code, display_name in lang_display_names.items():
                if display_name == selected_display:
                    selected_lang = lang_code
                    break
            if not selected_lang and selected_display in available_langs:
                selected_lang = selected_display
            
            # Получаем папку сохранения
            selected_folder_display = display_var.get()
            save_path = folder_options[selected_folder_display]
            
            # Сохраняем настройки
            self.settings["language"] = selected_lang if selected_lang else "ru"
            self.settings["save_folder"] = save_path
            self.save_settings()
            
            # Меняем язык в системе
            if selected_lang and selected_lang != get_current_language():
                set_language(selected_lang)
            
            # Создаём папку если её нет
            try:
                Path(save_path).mkdir(parents=True, exist_ok=True)
                messagebox.showinfo(LangT("Успех"), LangT("Настройки сохранены\nПапка: {save_path}").format(save_path=save_path))
                settings_window.destroy()
                
                # Обновляем интерфейс с новым языком
                self.show_main_ui()
            except Exception as e:
                messagebox.showerror(
                    LangT("Ошибка"), 
                    LangT("Не удалось создать папку:\n{save_path}\n\nОшибка: {e}").format(save_path=save_path, e=e)
                )
        
        ctk.CTkButton(button_frame, text=LangT("Сохранить"), command=save_settings, width=120).pack(side="left", padx=10)
        ctk.CTkButton(button_frame, text=LangT("Отмена"), command=settings_window.destroy, width=120).pack(side="left", padx=10)

    def find_and_setup_java(self):
        """Находит или устанавливает Java 17"""
        #print("\n" + "="*50)
        #print("ПОИСК JAVA JDK 17")
        #print("="*50)
        
        # 1. Проверяем все возможные пути Java
        java_found = self.find_java_17_in_all_paths()
        
        if java_found:
            print(LangT("✓ JDK 17 найдена:") + self.java_path)
            #print(f"  Версия: {self.java_version}")
            
            # Проверяем JAVA_HOME
            self.check_and_fix_java_home()
            return True
        
        # 2. Если Java не найдена, устанавливаем
        print(LangT("✗ JDK 17 не найдена в системе"))
        print(LangT("Начинается установка..."))
        self.install_java_17()
        return False
    
    def find_java_17_in_all_paths(self):
        """Ищет Java 17 во всех возможных местах"""
        
        # Проверяем в PATH
        java_in_path = self.find_java_in_path()
        if java_in_path:
            version = self.get_java_version(java_in_path)
            if version and version.startswith("17"):
                self.java_path = os.path.dirname(os.path.dirname(java_in_path))
                self.java_version = version
                return True
        
        # Проверяем JAVA_HOME
        java_home = os.environ.get("JAVA_HOME", "")
        if java_home:
            java_exe = os.path.join(java_home, "bin", "java.exe")
            if os.path.exists(java_exe):
                version = self.get_java_version(java_exe)
                if version and version.startswith("17"):
                    self.java_path = java_home
                    self.java_version = version
                    return True
        
        # Проверяем в реестре Windows
        if platform.system() == "Windows":
            java_from_registry = self.find_java_in_registry()
            if java_from_registry:
                java_exe = os.path.join(java_from_registry, "bin", "java.exe")
                if os.path.exists(java_exe):
                    version = self.get_java_version(java_exe)
                    if version and version.startswith("17"):
                        self.java_path = java_from_registry
                        self.java_version = version
                        return True
        
        # Проверяем стандартные пути
        standard_paths = [
            r"C:\Program Files\Java",
            r"C:\Program Files (x86)\Java",
            r"C:\Program Files\Eclipse Adoptium",
            r"C:\java",
            r"C:\jdk",
            r"C:\mmc_java",
            os.path.expanduser("~") + r"\Java",
            os.path.expanduser("~") + r"\jdk",
        ]
        
        for base_path in standard_paths:
            if os.path.exists(base_path):
                try:
                    for item in os.listdir(base_path):
                        item_path = os.path.join(base_path, item)
                        if os.path.isdir(item_path):
                            java_exe = os.path.join(item_path, "bin", "java.exe")
                            if os.path.exists(java_exe):
                                version = self.get_java_version(java_exe)
                                if version and version.startswith("17"):
                                    self.java_path = item_path
                                    self.java_version = version
                                    return True
                except:
                    continue
        
        return False
    
    def check_and_fix_java_home(self):
        """Проверяет и исправляет JAVA_HOME"""
        if not self.java_path:
            return
        
        current_java_home = os.environ.get("JAVA_HOME", "")
        
        # Если JAVA_HOME уже правильный
        if current_java_home == self.java_path:
            #print(f"✓ JAVA_HOME уже установлен правильно: {self.java_path}")
            return
        
        # Если JAVA_HOME не правильный или отсутствует
        print(f"JAVA_HOME: {current_java_home if current_java_home else LangT("не установлен")}")
        print(f"Устанавливаем JAVA_HOME: {self.java_path}")
        
        if platform.system() == "Windows":
            try:
                # Устанавливаем JAVA_HOME
                key = winreg.OpenKey(
                    winreg.HKEY_CURRENT_USER,
                    "Environment",
                    0,
                    winreg.KEY_SET_VALUE | winreg.KEY_READ
                )
                
                winreg.SetValueEx(key, "JAVA_HOME", 0, winreg.REG_SZ, self.java_path)
                os.environ["JAVA_HOME"] = self.java_path
                
                # Добавляем bin в PATH если нужно
                bin_path = os.path.join(self.java_path, "bin")
                try:
                    current_path, path_type = winreg.QueryValueEx(key, "PATH")
                    path_str = current_path if current_path else ""
                    
                    if bin_path not in path_str:
                        new_path = f"{bin_path};{path_str}" if path_str else bin_path
                        winreg.SetValueEx(key, "PATH", 0, path_type, new_path)
                        os.environ["PATH"] = f"{bin_path};{os.environ.get('PATH', '')}"
                except WindowsError:
                    winreg.SetValueEx(key, "PATH", 0, winreg.REG_SZ, bin_path)
                    os.environ["PATH"] = bin_path
                
                winreg.CloseKey(key)
                
                # Уведомляем систему
                self.broadcast_environment_change()
                print(LangT("✓ JAVA_HOME установлен"))
                
            except Exception as e:
                print(LangT("Ошибка при установке JAVA_HOME:") + str(e))
    
    def install_java_17(self):
        """Устанавливает Java 17"""
        # Проверяем права на запись в Program Files
        program_files_java = r"C:\Program Files\Java"
        has_admin_rights = self.check_admin_rights()
        
        if has_admin_rights:
            # Есть права администратора - устанавливаем в Program Files
            install_path = Path(program_files_java) / "jdk-17"
            print(LangT("Установка в Program Files:") + str(install_path))
        else:
            # Нет прав - устанавливаем в C:/mmc_java
            install_path = Path("C:/mmc_java")
            print(LangT("Установка в C:/mmc_java:") + str(install_path))
        
        # Создаем окно прогресса и начинаем установку
        self.show_java_download_ui(install_path)
        
        def download_thread():
            try:
                # Создаем временную папку
                temp_dir = Path(os.environ.get('TEMP', 'C:\\temp'))
                temp_dir.mkdir(exist_ok=True)
                
                self.root.after(0, lambda: self.update_progress(0.1, LangT("Подготовка к установке...")))
                
                # Создаем папку установки
                install_path.mkdir(parents=True, exist_ok=True)
                
                # URL для скачивания JDK 17
                jdk_url = "https://github.com/adoptium/temurin17-binaries/releases/download/jdk-17.0.12%2B7/OpenJDK17U-jdk_x64_windows_hotspot_17.0.12_7.zip"
                
                self.root.after(0, lambda: self.update_progress(0.2, LangT("Скачивание JDK 17...")))
                
                # Скачиваем файл
                response = requests.get(jdk_url, stream=True, timeout=60)
                response.raise_for_status()
                
                total_size = int(response.headers.get('content-length', 0))
                downloaded = 0
                temp_zip = temp_dir / "jdk_temp.zip"
                
                with open(temp_zip, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)
                            if total_size > 0:
                                progress = 0.2 + (downloaded / total_size * 0.6)
                                self.root.after(0, lambda p=progress: self.update_progress(p, 
                                    LangT("Скачивание:")+ f"{downloaded/1024/1024:.1f}MB / {total_size/1024/1024:.1f}MB"))
                
                self.root.after(0, lambda: self.update_progress(0.8, LangT("Распаковка JDK...")))
                
                # Распаковываем архив
                with zipfile.ZipFile(temp_zip, 'r') as zip_ref:
                    if install_path.exists():
                        shutil.rmtree(install_path)
                    
                    zip_ref.extractall(str(install_path.parent))
                    
                    # Переименовываем извлеченную папку
                    extracted_folders = [f for f in install_path.parent.iterdir() if f.is_dir() and "jdk" in f.name.lower()]
                    if extracted_folders:
                        extracted = extracted_folders[0]
                        if extracted != install_path:
                            extracted.rename(install_path)
                
                # Удаляем временный файл
                try:
                    temp_zip.unlink()
                except:
                    pass
                
                self.root.after(0, lambda: self.update_progress(0.9, LangT("Настройка окружения...")))
                
                # Проверяем установку
                java_exe = install_path / "bin" / "java.exe"
                if java_exe.exists():
                    self.java_path = str(install_path)
                    self.java_version = self.get_java_version(str(java_exe))
                    
                    self.root.after(0, lambda: self.update_progress(1.0, LangT("Установка завершена!")))
                    
                    # Устанавливаем JAVA_HOME
                    self.root.after(500, lambda: self.set_java_home_after_install())
                    
                else:
                    self.root.after(0, lambda: self.show_java_error(LangT("JDK не установилась корректно")))
                    self.root.after(3000, self.show_main_ui)
                    
            except Exception as e:
                self.root.after(0, lambda: self.show_java_error(LangT("Ошибка:")+ f"{str(e)[:200]}"))
                self.root.after(3000, self.show_main_ui)
        
        thread = threading.Thread(target=download_thread, daemon=True)
        thread.start()
    
    def set_java_home_after_install(self):
        """Устанавливает JAVA_HOME после установки"""
        if not self.java_path:
            return
        
        print(LangT("Устанавливаем JAVA_HOME:") + self.java_path)
        
        if platform.system() == "Windows":
            try:
                key = winreg.OpenKey(
                    winreg.HKEY_CURRENT_USER,
                    "Environment",
                    0,
                    winreg.KEY_SET_VALUE | winreg.KEY_READ
                )
                
                # Устанавливаем JAVA_HOME
                winreg.SetValueEx(key, "JAVA_HOME", 0, winreg.REG_SZ, self.java_path)
                os.environ["JAVA_HOME"] = self.java_path
                
                # Добавляем bin в PATH
                bin_path = os.path.join(self.java_path, "bin")
                try:
                    current_path, path_type = winreg.QueryValueEx(key, "PATH")
                    path_str = current_path if current_path else ""
                    
                    if bin_path not in path_str:
                        new_path = f"{bin_path};{path_str}" if path_str else bin_path
                        winreg.SetValueEx(key, "PATH", 0, path_type, new_path)
                        os.environ["PATH"] = f"{bin_path};{os.environ.get('PATH', '')}"
                except WindowsError:
                    winreg.SetValueEx(key, "PATH", 0, winreg.REG_SZ, bin_path)
                    os.environ["PATH"] = bin_path
                
                winreg.CloseKey(key)
                
                # Уведомляем систему
                self.broadcast_environment_change()
                
                messagebox.showinfo(
                    LangT("Успех"),
                    LangT("JDK 17 успешно установлена!\n\n") +
                    LangT("Путь:") + self.java_path + "\n" +
                    LangT("Версия:") + self.java_version + "\n\n" +
                    LangT("JAVA_HOME установлен.")
                )
                
                self.show_main_ui()
                
            except Exception as e:
                messagebox.showerror(LangT("Ошибка"), LangT("Не удалось установить JAVA_HOME:")+ f"{e}")
                self.show_main_ui()
    
    def find_java_in_path(self):
        """Ищет Java в системном PATH"""
        for path in os.environ.get("PATH", "").split(os.pathsep):
            java_exe = os.path.join(path, "java.exe")
            if os.path.exists(java_exe):
                return java_exe
        return None
    
    def find_java_in_registry(self):
        """Ищет JDK в реестре Windows"""
        if platform.system() != "Windows":
            return None
        
        try:
            registry_paths = [
                (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\JavaSoft\JDK"),
                (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\JavaSoft\Java Development Kit"),
                (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Eclipse Adoptium\JDK"),
            ]
            
            for hkey, reg_path in registry_paths:
                try:
                    key = winreg.OpenKey(hkey, reg_path, 0, winreg.KEY_READ)
                    try:
                        current_version = winreg.QueryValueEx(key, "CurrentVersion")[0]
                        version_key = winreg.OpenKey(key, current_version)
                        java_home = winreg.QueryValueEx(version_key, "JavaHome")[0]
                        winreg.CloseKey(version_key)
                        winreg.CloseKey(key)
                        if java_home and os.path.exists(java_home):
                            return java_home
                    except:
                        for i in range(winreg.QueryInfoKey(key)[0]):
                            try:
                                subkey_name = winreg.EnumKey(key, i)
                                subkey = winreg.OpenKey(key, subkey_name)
                                try:
                                    java_home = winreg.QueryValueEx(subkey, "JavaHome")[0]
                                    if java_home and os.path.exists(java_home):
                                        winreg.CloseKey(subkey)
                                        winreg.CloseKey(key)
                                        return java_home
                                except:
                                    pass
                                winreg.CloseKey(subkey)
                            except:
                                continue
                        winreg.CloseKey(key)
                except:
                    continue
        except:
            pass
        
        return None
    
    def get_java_version(self, java_exe):
        """Получает версию Java"""
        try:
            result = subprocess.run(
                [java_exe, "-version"], 
                capture_output=True, 
                text=True,
                shell=True
            )
            if result.returncode == 0:
                version_output = result.stderr if result.stderr else result.stdout
                return self.parse_java_version(version_output)
        except:
            pass
        return None
    
    def parse_java_version(self, version_output):
        """Парсит вывод java -version"""
        try:
            patterns = [
                r'version "(\d+\.\d+\.\d+)[^"]*"',
                r'version "(\d+)[^"]*"',
                r'(\d+\.\d+\.\d+)',
                r'(\d+\.\d+)',
                r'(\d+)'
            ]
            
            for pattern in patterns:
                match = re.search(pattern, version_output)
                if match:
                    version = match.group(1)
                    if version.startswith("17") or version == "17":
                        return version
                    return version
            return None
        except:
            return None
    
    def check_admin_rights(self):
        """Проверяет, есть ли права администратора"""
        if platform.system() == "Windows":
            try:
                import ctypes
                return ctypes.windll.shell32.IsUserAnAdmin() != 0
            except:
                pass
        return False
    
    def broadcast_environment_change(self):
        """Уведомляет систему об изменении переменных окружения"""
        if platform.system() == "Windows":
            try:
                import ctypes
                HWND_BROADCAST = 0xFFFF
                WM_SETTINGCHANGE = 0x001A
                SMTO_ABORTIFHUNG = 0x0002
                
                ctypes.windll.user32.SendMessageTimeoutW(
                    HWND_BROADCAST, 
                    WM_SETTINGCHANGE, 
                    0, 
                    "Environment", 
                    SMTO_ABORTIFHUNG, 
                    5000, 
                    None
                )
            except:
                pass
    
    def load_all_icons_background(self):
        """Загружает иконки в фоновом режиме"""
        def load_in_thread():
            try:
                self.load_all_icons(None)
                print(LangT("Иконки успешно загружены"))
            except Exception as e:
                print(LangT("Ошибка при загрузке иконок:")+ f"{e}")
        
        thread = threading.Thread(target=load_in_thread, daemon=True)
        thread.start()
    
    def load_all_icons(self, icons_config=None, parent_window=None):
        """Загружает все иконки из репозитория Mindustry"""
        # Базовая конфигурация
        default_config = {
            "base_url": "https://raw.githubusercontent.com/Anuken/Mindustry/master/core/assets-raw/sprites/",
            "categories": {
                "items": {
                    "dest_dir": "items",
                    "files": [
                        {"name": "copper", "filename": "items/item-copper.png"},
                        {"name": "lead", "filename": "items/item-lead.png"},
                        {"name": "metaglass", "filename": "items/item-metaglass.png"},
                        {"name": "graphite", "filename": "items/item-graphite.png"},
                        {"name": "sand", "filename": "items/item-sand.png"},
                        {"name": "coal", "filename": "items/item-coal.png"},
                        {"name": "titanium", "filename": "items/item-titanium.png"},
                        {"name": "thorium", "filename": "items/item-thorium.png"},
                        {"name": "scrap", "filename": "items/item-scrap.png"},
                        {"name": "silicon", "filename": "items/item-silicon.png"},
                        {"name": "plastanium", "filename": "items/item-plastanium.png"},
                        {"name": "phase-fabric", "filename": "items/item-phase-fabric.png"},
                        {"name": "surge-alloy", "filename": "items/item-surge-alloy.png"},
                        {"name": "spore-pod", "filename": "items/item-spore-pod.png"},
                        {"name": "blast-compound", "filename": "items/item-blast-compound.png"},
                        {"name": "pyratite", "filename": "items/item-pyratite.png"}
                    ]
                },
                "liquids": {
                    "dest_dir": "liquids",
                    "files": [
                        {"name": "water", "filename": "items/liquid-water.png"},
                        {"name": "oil", "filename": "items/liquid-oil.png"},
                        {"name": "slag", "filename": "items/liquid-slag.png"},
                        {"name": "cryofluid", "filename": "items/liquid-cryofluid.png"}
                    ]
                },
                "blocks": {
                    "dest_dir": "blocks",
                    "files": [
                        # Стены
                        {"name": "copper-wall", "filename": "blocks/walls/copper-wall.png"},
                        {"name": "copper-wall-large", "filename": "blocks/walls/copper-wall-large.png"},
                        {"name": "titanium-wall", "filename": "blocks/walls/titanium-wall.png"},
                        {"name": "titanium-wall-large", "filename": "blocks/walls/titanium-wall-large.png"},
                        {"name": "thorium-wall", "filename": "blocks/walls/thorium-wall.png"},
                        {"name": "thorium-wall-large", "filename": "blocks/walls/thorium-wall-large.png"},
                        {"name": "surge-wall", "filename": "blocks/walls/surge-wall.png"},
                        {"name": "surge-wall-large", "filename": "blocks/walls/surge-wall-large.png"},
                        {"name": "plastanium-wall", "filename": "blocks/walls/plastanium-wall.png"},
                        {"name": "plastanium-wall-large", "filename": "blocks/walls/plastanium-wall-large.png"},
                        {"name": "phase-wall", "filename": "blocks/walls/phase-wall.png"},
                        {"name": "phase-wall-large", "filename": "blocks/walls/phase-wall-large.png"},
                        {"name": "shielded-wall", "filename": "blocks/walls/shielded-wall.png"},
                        {"name": "shielded-wall-glow", "filename": "blocks/walls/shielded-wall-glow.png"},
                        
                        # Энергетика
                        {"name": "solar-panel", "filename": "blocks/power/solar-panel.png"},
                        {"name": "solar-panel-large", "filename": "blocks/power/solar-panel-large.png"},
                        {"name": "battery", "filename": "blocks/power/battery.png"},
                        {"name": "battery-large", "filename": "blocks/power/battery-large.png"},
                        {"name": "battery-top", "filename": "blocks/power/battery-top.png"},
                        {"name": "rtg-generator", "filename": "blocks/power/rtg-generator.png"},
                        {"name": "rtg-generator-top", "filename": "blocks/power/rtg-generator-top.png"},
                        {"name": "steam-generator", "filename": "blocks/power/steam-generator.png"},
                        {"name": "combustion-generator", "filename": "blocks/power/combustion-generator.png"},
                        {"name": "thorium-reactor", "filename": "blocks/power/thorium-reactor.png"},
                        {"name": "impact-reactor", "filename": "blocks/power/impact-reactor.png"},
                        {"name": "differential-generator", "filename": "blocks/power/differential-generator.png"},
                        
                        # Передача энергии
                        {"name": "beam-node", "filename": "blocks/power/beam-node.png"},
                        {"name": "surge-tower", "filename": "blocks/power/surge-tower.png"},
                        {"name": "power-node", "filename": "blocks/power/power-node.png"},
                        {"name": "power-node-large", "filename": "blocks/power/power-node-large.png"},
                        
                        # Производство
                        {"name": "cultivator", 
                            "layers": [
                                {"filename": "blocks/production/cultivator-bottom.png"},
                                {"filename": "blocks/production/cultivator.png"},
                                {"filename": "blocks/production/cultivator-top.png"}
                            ]
                        },
                        {"name": "blast-mixer", "filename": "blocks/production/blast-mixer.png"},
                        {"name": "pyratite-mixer", "filename": "blocks/production/pyratite-mixer.png"},
                        {"name": "spore-press", 
                            "layers": [
                                {"filename": "blocks/production/spore-press-bottom.png"},
                                {"filename": "blocks/production/spore-press-piston-icon.png"},
                                {"filename": "blocks/production/spore-press.png"},
                                {"filename": "blocks/production/spore-press-top.png"}
                            ]
                        },
                        {"name": "coal-centrifuge", "filename": "blocks/production/coal-centrifuge.png"},
                        {"name": "multi-press", "filename": "blocks/production/multi-press.png"},
                        {"name": "silicon-crucible", "filename": "blocks/production/silicon-crucible.png"},
                        {"name": "plastanium-compressor", "filename": "blocks/production/plastanium-compressor.png"},
                        {"name": "phase-weaver", 
                            "layers": [
                                {"filename": "blocks/production/phase-weaver-bottom.png"},
                                {"filename": "blocks/production/phase-weaver.png"},
                                {"filename": "blocks/production/phase-weaver-weave.png"}
                            ]
                        },
                        {"name": "graphite-press", "filename": "blocks/production/graphite-press.png"},
                        {"name": "silicon-smelter", "filename": "blocks/production/silicon-smelter.png"},
                        {"name": "kiln", "filename": "blocks/production/kiln.png"},
                        {"name": "pulverizer", 
                            "layers": [
                                {"filename": "blocks/production/pulverizer.png"},
                                {"filename": "blocks/production/pulverizer-rotator.png"},
                                {"filename": "blocks/production/pulverizer-top.png"}
                            ]
                        },
                        {"name": "melter", 
                            "layers": [
                                {"filename": "blocks/production/melter-bottom.png"},
                                {"filename": "blocks/production/melter.png"}
                            ]
                        },
                        {"name": "surge-smelter", "filename": "blocks/production/surge-smelter.png"},
                        {"name": "cryofluid-mixer", 
                            "layers": [
                                {"filename": "blocks/production/cryofluid-mixer-bottom.png"},
                                {"filename": "blocks/production/cryofluid-mixer.png"}
                            ]
                        },
                        
                        # Транспортировка
                        {"name": "bridge-conveyor", "filename": "blocks/distribution/bridge-conveyor.png"},
                        {"name": "bridge-conveyor-end", "filename": "blocks/distribution/bridge-conveyor-end.png"},
                        {"name": "bridge-conveyor-bridge", "filename": "blocks/distribution/bridge-conveyor-bridge.png"},
                        {"name": "bridge-conveyor-arrow", "filename": "blocks/distribution/bridge-conveyor-arrow.png"},
                        {"name": "bridge-conduit", "filename": "blocks/liquid/bridge-conduit.png"},
                        {"name": "phase-conduit", "filename": "blocks/liquid/phase-conduit.png"},
                        {"name": "phase-conveyor", "filename": "blocks/distribution/phase-conveyor.png"},

                        #КОНВЕЕРНЫЫЫ
                        {"name": "armored-conveyor-0-0", "filename": "blocks/distribution/conveyors/armored-conveyor-0-0.png"},
                        {"name": "titanium-conveyor-0-0", "filename": "blocks/distribution/conveyors/titanium-conveyor-0-0.png"},
                        {"name": "conveyor-0-0", "filename": "blocks/distribution/conveyors/conveyor-0-0.png"},
                        {"name": "conveyor-0-1", "filename": "blocks/distribution/conveyors/conveyor-0-0.png"},
                        {"name": "conveyor-0-2", "filename": "blocks/distribution/conveyors/conveyor-0-0.png"},
                        {"name": "conveyor-0-3", "filename": "blocks/distribution/conveyors/conveyor-0-0.png"},
                        {"name": "conveyor-1-0", "filename": "blocks/distribution/conveyors/conveyor-1-0.png"},
                        {"name": "conveyor-1-1", "filename": "blocks/distribution/conveyors/conveyor-1-1.png"},
                        {"name": "conveyor-1-2", "filename": "blocks/distribution/conveyors/conveyor-1-2.png"},
                        {"name": "conveyor-1-3", "filename": "blocks/distribution/conveyors/conveyor-1-3.png"},
                        {"name": "conveyor-2-0", "filename": "blocks/distribution/conveyors/conveyor-2-0.png"},
                        {"name": "conveyor-2-1", "filename": "blocks/distribution/conveyors/conveyor-2-1.png"},
                        {"name": "conveyor-2-2", "filename": "blocks/distribution/conveyors/conveyor-2-2.png"},
                        {"name": "conveyor-2-3", "filename": "blocks/distribution/conveyors/conveyor-2-3.png"},
                        {"name": "conveyor-3-0", "filename": "blocks/distribution/conveyors/conveyor-3-0.png"},
                        {"name": "conveyor-3-1", "filename": "blocks/distribution/conveyors/conveyor-3-1.png"},
                        {"name": "conveyor-3-2", "filename": "blocks/distribution/conveyors/conveyor-3-2.png"},
                        {"name": "conveyor-3-3", "filename": "blocks/distribution/conveyors/conveyor-3-3.png"},
                        {"name": "conveyor-4-0", "filename": "blocks/distribution/conveyors/conveyor-4-0.png"},
                        {"name": "conveyor-4-1", "filename": "blocks/distribution/conveyors/conveyor-4-1.png"},
                        {"name": "conveyor-4-2", "filename": "blocks/distribution/conveyors/conveyor-4-2.png"},
                        {"name": "conveyor-4-3", "filename": "blocks/distribution/conveyors/conveyor-4-3.png"},
                    ]
                }
            }
        }
        
        config = icons_config if icons_config is not None else default_config
        
        # Базовая директория для иконок
        icons_dir = os.path.join(resource_path("Creator"), "icons")
        
        # Создаем директории для каждой категории
        category_dirs = {}
        for category_name, category_config in config["categories"].items():
            category_dir = os.path.join(icons_dir, category_config["dest_dir"])
            os.makedirs(category_dir, exist_ok=True)
            category_dirs[category_name] = category_dir
        
        # Проверяем наличие всех иконок
        print(LangT("Проверка наличия иконок..."))
        
        missing_icons = {}
        total_expected = 0
        total_existing = 0
        
        for category_name, category_config in config["categories"].items():
            category_dir = category_dirs[category_name]
            missing_in_category = []
            
            for file_info in category_config["files"]:
                total_expected += 1
                icon_path = os.path.join(category_dir, f"{file_info['name']}.png")
                
                if os.path.exists(icon_path) and os.path.getsize(icon_path) > 0:
                    total_existing += 1
                else:
                    missing_in_category.append(file_info)
            
            if missing_in_category:
                missing_icons[category_name] = missing_in_category
        
        # Если все иконки уже есть
        if total_existing == total_expected:
            print(LangT("Все иконки уже загружены")+ f"({total_existing}/{total_expected})")
            return True
        
        # Подготавливаем задачи для загрузки
        download_tasks = []
        layer_groups = {}
        temp_dir = os.path.join(icons_dir, "temp_layers")
        os.makedirs(temp_dir, exist_ok=True)
        
        for category_name, category_config in config["categories"].items():
            category_dir = category_dirs[category_name]
            files_to_download = missing_icons.get(category_name, category_config["files"])
            
            for file_info in files_to_download:
                final_path = os.path.join(category_dir, f"{file_info['name']}.png")
                
                if "layers" in file_info:
                    layers = file_info["layers"]
                    layer_files = []
                    
                    for i, layer in enumerate(layers):
                        temp_layer_path = os.path.join(temp_dir, f"{file_info['name']}_layer_{i}_{os.path.basename(layer['filename'])}")
                        full_url = config["base_url"] + layer["filename"]
                        
                        download_tasks.append({
                            "url": full_url,
                            "save_path": temp_layer_path,
                            "name": f"{file_info['name']}_layer_{i}",
                            "category": category_name,
                            "is_layer": True,
                            "layer_index": i,
                            "layer_config": layer
                        })
                        layer_files.append((temp_layer_path, layer))
                    
                    layer_groups[final_path] = {
                        "layers": layer_files,
                        "name": file_info["name"],
                        "category": category_name
                    }
                else:
                    full_url = config["base_url"] + file_info["filename"]
                    download_tasks.append({
                        "url": full_url,
                        "save_path": final_path,
                        "name": file_info["name"],
                        "category": category_name,
                        "is_layer": False
                    })
        
        if not download_tasks:
            return True
        
        # Создаем окно прогресса если есть parent_window
        if parent_window:
            progress_window = ctk.CTkToplevel(parent_window)
            progress_window.title(LangT("Загрузка иконок"))
            progress_window.geometry("400x150")
            progress_window.transient(parent_window)
            progress_window.grab_set()
            
            progress_label = ctk.CTkLabel(progress_window, text=LangT("Загрузка иконок..."))
            progress_label.pack(pady=10)
            
            progress_bar = ctk.CTkProgressBar(progress_window, width=300)
            progress_bar.pack(pady=10)
            progress_bar.set(0)
            
            status_label = ctk.CTkLabel(progress_window, text=LangT("Подготовка..."))
            status_label.pack(pady=5)
            
            progress_window.update()
        
        downloaded = 0
        total_to_download = len(download_tasks)
        errors = []
        
        def update_progress(current, total, name, operation=LangT("Загрузка")):
            if parent_window:
                progress = current / total if total > 0 else 0
                progress_bar.set(progress)
                status_label.configure(text=f"{current}/{total} - {name}")
                progress_label.configure(text=f"{operation}: {name}")
                progress_window.update()
        
        def download_file(task):
            try:
                os.makedirs(os.path.dirname(task["save_path"]), exist_ok=True)
                
                response = requests.get(task["url"], stream=True, timeout=30)
                if response.status_code == 200:
                    with open(task["save_path"], 'wb') as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            f.write(chunk)
                    
                    if os.path.exists(task["save_path"]) and os.path.getsize(task["save_path"]) > 0:
                        return True, task
                    else:
                        return False, (task, LangT("Файл не загружен или пустой"))
                else:
                    return False, (task, f"HTTP {response.status_code}")
            except Exception as e:
                return False, (task, str(e))
        
        def merge_layers(final_path, layers_info):
            try:
                from PIL import Image
                
                images = []
                for layer_path, layer_config in layers_info["layers"]:
                    if os.path.exists(layer_path):
                        img = Image.open(layer_path).convert("RGBA")
                        images.append(img)
                
                if not images:
                    return False
                
                # Находим максимальные размеры
                max_width = max(img.size[0] for img in images)
                max_height = max(img.size[1] for img in images)
                
                # Создаем результат
                result = Image.new("RGBA", (max_width, max_height), (0, 0, 0, 0))
                
                # Накладываем слои
                for img in images:
                    if img.size != (max_width, max_height):
                        new_img = Image.new("RGBA", (max_width, max_height), (0, 0, 0, 0))
                        x_offset = (max_width - img.size[0]) // 2
                        y_offset = (max_height - img.size[1]) // 2
                        new_img.paste(img, (x_offset, y_offset), img)
                        img = new_img
                    result = Image.alpha_composite(result, img)
                
                result.save(final_path, "PNG")
                return True
                
            except Exception as e:
                print(LangT("Ошибка при склейке слоев:")+ f"{e}")
                return False
        
        try:
            # Загружаем файлы
            with ThreadPoolExecutor(max_workers=4) as executor:
                futures = {executor.submit(download_file, task): task for task in download_tasks}
                
                for future in as_completed(futures):
                    task = futures[future]
                    success, result = future.result()
                    
                    if success:
                        downloaded += 1
                        if parent_window:
                            update_progress(downloaded, total_to_download, task["name"])
                    else:
                        if isinstance(result, tuple):
                            failed_task, error = result
                            errors.append((failed_task["name"], failed_task["category"], error))
                        downloaded += 1
            
            # Склеиваем слои
            if layer_groups:
                merged_count = 0
                for final_path, layers_info in layer_groups.items():
                    if parent_window:
                        update_progress(merged_count, len(layer_groups), 
                                      layers_info["name"], operation="Склейка")
                    
                    if merge_layers(final_path, layers_info):
                        merged_count += 1
                    else:
                        errors.append((layers_info["name"], layers_info["category"], LangT("Ошибка склейки")))
            
            # Очищаем временную директорию
            try:
                shutil.rmtree(temp_dir)
            except:
                pass
            
            if errors and parent_window:
                error_msg = "\n".join(f"{name}: {error}" for name, _, error in errors[:5])
                if len(errors) > 5:
                    error_msg += LangT("\n... и еще")+ f"{len(errors)-5}"+ LangT("ошибок")
                messagebox.showwarning(LangT("Ошибки загрузки"), LangT("Не удалось загрузить некоторые иконки:")+f"\n{error_msg}")
            
            if parent_window:
                progress_window.after(2000, progress_window.destroy)
            
            print(LangT("Иконки загружены:")+ f"{downloaded}/{total_to_download}")
            return len(errors) == 0
            
        except Exception as e:
            if parent_window and 'progress_window' in locals():
                progress_window.destroy()
            print(LangT("Ошибка загрузки иконок:")+ f"{e}")
            return False
    
    def show_java_download_ui(self, install_path):
        """Показывает UI для скачивания Java"""
        self.clear_window()
        
        ctk.CTkLabel(self.root, text=LangT("Установка Java JDK 17"), font=("Arial", 20, "bold")).pack(pady=50)
        ctk.CTkLabel(self.root, text=LangT("Java JDK 17 не найдена. Устанавливаю..."), 
                    font=("Arial", 16)).pack(pady=20)
        ctk.CTkLabel(self.root, text=LangT("Путь установки:")+ f"{install_path}", 
                    font=("Arial", 12)).pack(pady=5)
        ctk.CTkLabel(self.root, text=LangT("Пожалуйста, подождите"), 
                    font=("Arial", 14)).pack(pady=10)
        
        self.progress_bar = ctk.CTkProgressBar(self.root, width=400)
        self.progress_bar.pack(pady=20)
        self.progress_bar.set(0)
        
        self.status_label = ctk.CTkLabel(self.root, text=LangT("Подготовка..."), font=("Arial", 12))
        self.status_label.pack(pady=10)
    
    def update_progress(self, value, status):
        """Обновляет прогресс скачивания"""
        try:
            self.progress_bar.set(value)
            self.status_label.configure(text=status)
            self.root.update()
        except:
            pass
    
    def show_java_error(self, message):
        """Показывает сообщение об ошибке"""
        try:
            self.update_progress(0, message)
            self.root.update()
            messagebox.showerror(LangT("Ошибка установки JDK"), message)
        except:
            pass
    
    def show_main_ui(self):
        """Показывает основной интерфейс"""
        self.clear_window()
        
        # Верхняя панель с кнопкой настроек
        top_frame = ctk.CTkFrame(self.root, height=50)
        top_frame.pack(side="top", fill="x", padx=5, pady=5)
        
        settings_btn = ctk.CTkButton(
            top_frame,
            text=LangT("⚙ Настройки"),
            width=100,
            height=35,
            command=self.open_settings_window
        )
        settings_btn.pack(side="right", padx=10, pady=5)
        
        # Левая панель со списком модов
        left_frame = ctk.CTkFrame(self.root, width=300)
        left_frame.pack(side="left", fill="y", padx=5, pady=5)
        
        # Центральная панель
        center_frame = ctk.CTkFrame(self.root)
        center_frame.pack(side="right", fill="both", expand=True, padx=5, pady=5)
        
        self.setup_mods_list(left_frame)
        
        # Показываем соответствующий интерфейс
        if self.java_path and self.java_version and self.java_version.startswith("17"):
            self.setup_create_mod_panel(center_frame)
        else:
            self.setup_install_java_panel(center_frame)
    
    def setup_create_mod_panel(self, parent):
        """Панель для создания мода"""
        ctk.CTkLabel(parent, text="Mindustry Java Mod Creator", font=("Arial", 20, "bold")).pack(pady=30)
        
        # Показываем информацию о Java
        #info_frame = ctk.CTkFrame(parent, fg_color="transparent")
        #info_frame.pack(pady=10)
        #ctk.CTkLabel(info_frame, text=f"Java JDK 17: {self.java_path}", 
                    #font=("Arial", 11), text_color="green").pack()
        #ctk.CTkLabel(info_frame, text=f"Версия: {self.java_version}", 
                    #font=("Arial", 11), text_color="green").pack()
        
        form_frame = ctk.CTkFrame(parent, fg_color="transparent")
        form_frame.pack(pady=30)
        
        ctk.CTkLabel(form_frame, text=LangT("Имя папки мода:"), font=("Arial", 14)).pack(pady=3)
        
        self.mod_name_entry = ctk.CTkEntry(form_frame, width=280, height=35, font=("Arial", 13))
        self.mod_name_entry.pack(pady=8)
        
        ctk.CTkButton(
            form_frame,
            text=LangT("Создать"),
            width=200,
            height=45,
            font=("Arial", 14, "bold"),
            command=self.create_java_mod,
            fg_color="green",
            hover_color="dark green"
        ).pack(pady=20)
    
    def setup_install_java_panel(self, parent):
        """Панель для установки Java"""
        ctk.CTkLabel(parent, text="Mindustry Java Mod Creator", font=("Arial", 20, "bold")).pack(pady=30)
        
        ctk.CTkLabel(parent, text=LangT("Требуется JDK 17"), font=("Arial", 16)).pack(pady=10)
        
        info_frame = ctk.CTkFrame(parent, fg_color="transparent")
        info_frame.pack(pady=20)
        
        ctk.CTkLabel(info_frame, text=LangT("Для создания модов требуется установить JDK 17."), 
                    font=("Arial", 12)).pack(pady=5)
        
        ctk.CTkButton(
            parent,
            text=LangT("Установить JDK 17"),
            width=250,
            height=50,
            font=("Arial", 15, "bold"),
            command=self.install_java_17,
            fg_color="green",
            hover_color="dark green"
        ).pack(pady=30)
    
    def setup_mods_list(self, parent):
        """Настраивает список модов"""
        ctk.CTkLabel(parent, text=LangT("Созданные моды"), font=("Arial", 16, "bold")).pack(pady=10)
        
        scroll_frame = ctk.CTkScrollableFrame(parent, height=500)
        scroll_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        mods_dir = Path("Creator/mods")
        mods = []
        
        if mods_dir.exists():
            for item in mods_dir.iterdir():
                if item.is_dir():
                    mods.append(item)
        
        if not mods:
            ctk.CTkLabel(scroll_frame, text=LangT("Нет модов"), font=("Arial", 12)).pack(pady=20)
        else:
            for mod_folder in sorted(mods, key=lambda x: x.name):
                btn = ctk.CTkButton(
                    scroll_frame,
                    text=mod_folder.name,
                    width=250,
                    height=35,
                    font=("Arial", 11),
                    anchor="w",
                    command=lambda mf=mod_folder: self.open_mod_creator(mf)
                )
                btn.pack(pady=2, padx=5)
    
    def create_java_mod(self):
        """Создает новый Java мод"""
        mod_name = self.mod_name_entry.get().strip()
        
        if not mod_name:
            messagebox.showerror(LangT("Ошибка"), LangT("Введите имя мода!"))
            return
        
        mod_dir = Path("Creator/mods") / mod_name
        
        if mod_dir.exists():
            if not messagebox.askyesno(LangT("Подтверждение"), LangT("Мод ")+f"'{mod_name}'"+LangT(" уже существует. Перезаписать?")):
                return
            shutil.rmtree(mod_dir)
        
        mod_dir.mkdir(parents=True, exist_ok=True)
        
        self.open_mod_editor(mod_dir)
    
    def open_mod_editor(self, mod_dir):
        """Открывает редактор мода"""
        self.mod_folder = mod_dir
        self.clear_window()
        
        from .mod_editor import ModEditor
        editor = ModEditor(self.root, self.mod_folder, self)
        editor.open_mod_editor()
    
    def open_mod_creator(self, mod_folder):
        """Открывает создатель мода"""
        self.mod_folder = mod_folder
        self.clear_window()
        
        from .creator_editor import CreatorEditor
        creator = CreatorEditor(self.root, self.mod_folder, self)
        creator.open_creator()
    
    def clear_window(self):
        """Очищает окно"""
        for widget in self.root.winfo_children():
            widget.destroy()
    
    def run(self):
        """Запускает приложение"""
        self.root.mainloop()

if __name__ == "__main__":
    app = MainWindow()
    app.run()