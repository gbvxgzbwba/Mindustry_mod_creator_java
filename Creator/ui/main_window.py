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
from tkinter import filedialog, messagebox
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
        
        # Загружаем настройки ДО создания UI
        self.settings_file = None
        self.settings = self.load_settings()
        
        # Устанавливаем язык из настроек ДО создания UI
        saved_lang = self.settings.get("language", "ru")
        from Creator.utils.lang_system import set_language, get_current_language
        if saved_lang != get_current_language():
            set_language(saved_lang)
        
        # Используем путь из настроек или по умолчанию
        save_folder = self.settings.get("save_folder", "mods")
        Path(save_folder).mkdir(parents=True, exist_ok=True)
        
        # Проверяем Java при запуске
        self.find_and_setup_java()
        
        # Инициализация автообновления (после загрузки настроек)
        self.init_autoupdater()
        
        self.show_main_ui()
    
    def init_autoupdater(self):
        """Инициализирует модуль автообновления"""
        try:
            from Creator.utils.updater import AutoUpdater
            
            # Настройки репозитория
            REPO_URL = "gbvxgzbwba/Mindustry_mod_creator_java"
            EXE_CONFIGS = [
                {"name": "MindustryModCreator.exe", "version_prefix": "noConsole"},
                {"name": "MindustryModCreatorConsole.exe", "version_prefix": "Console"}
            ]
            
            self.updater = AutoUpdater(REPO_URL, EXE_CONFIGS)
            
            # Проверяем обновления при запуске (если включено в настройках)
            if self.settings.get("autoupdate", True):
                print("🔍 Проверка обновлений при запуске...")
                # Запускаем проверку в отдельном потоке, чтобы не блокировать UI
                def check_updates():
                    try:
                        self.updater.check_and_update_autostart()
                    except Exception as e:
                        print(f"Ошибка проверки обновлений: {e}")
                
                thread = threading.Thread(target=check_updates, daemon=True)
                thread.start()
            else:
                print("⏭️ Автообновление отключено в настройках")
                
        except ImportError as e:
            print(f"⚠️ Модуль автообновления не найден: {e}")
            self.updater = None
        except Exception as e:
            print(f"⚠️ Ошибка инициализации автообновления: {e}")
            self.updater = None
    
    def load_settings(self):
        """Загружает настройки из TXT файла"""
        default_settings = {
            "language": "ru",
            "save_folder": "mods",
            "hide_content": False,
            "game_path": "",
            "autoupdate": True
        }

        appdata = os.getenv('APPDATA') or os.path.expanduser("~")
        settings_dir = Path(appdata) / "MindustryModCreator"
        settings_dir.mkdir(parents=True, exist_ok=True)
        self.settings_file = settings_dir / "settings.txt"  # <-- ТЕПЕРЬ TXT!
        
        print(f"[load_settings] Путь: {self.settings_file}")

        settings = default_settings.copy()
        
        if self.settings_file.exists():
            try:
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if not line or line.startswith('#'):
                            continue
                        
                        if ':' in line:
                            key, value = line.split(':', 1)
                            key = key.strip()
                            value = value.strip()
                            
                            # Преобразуем типы
                            if key == 'language':
                                settings[key] = value
                            elif key == 'save_folder':
                                settings[key] = value
                            elif key == 'game_path':
                                settings[key] = value
                            elif key == 'hide_content':
                                settings[key] = value.lower() == 'true'
                            elif key == 'autoupdate':
                                settings[key] = value.lower() == 'true'
                            else:
                                settings[key] = value
                            
                            print(f"[load_settings] Загружено: {key} = {value}")
                            
            except Exception as e:
                print(f"[load_settings] Ошибка загрузки: {e}")
                # Если ошибка, создаём новый файл
                self._save_to_txt(default_settings)
                return default_settings.copy()
        
        # Добавляем недостающие ключи
        for key, value in default_settings.items():
            if key not in settings:
                settings[key] = value
                print(f"[load_settings] Добавлен ключ: {key} = {value}")
        
        self.settings = settings
        return self.settings.copy()

    def _save_to_txt(self, settings):
        """ВНУТРЕННИЙ метод: сохраняет настройки в TXT файл"""
        try:
            self.settings_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                f.write("# Настройки Mindustry Mod Creator\n")
                f.write(f"# Сохранено: {__import__('datetime').datetime.now()}\n\n")
                
                for key, value in settings.items():
                    if isinstance(value, bool):
                        value = str(value).lower()
                    f.write(f"{key}: {value}\n")
            
            print(f"[_save_to_txt] Сохранено: {settings}")
            return True
        except Exception as e:
            print(f"[_save_to_txt] Ошибка: {e}")
            return False

    def save_settings(self, settings=None):
        """Сохраняет настройки (публичный метод)"""
        if settings is None:
            settings = self.settings
        else:
            self.settings = settings.copy()
        
        return self._save_to_txt(self.settings)

    def open_settings_window(self):
        """Открывает окно настроек"""
        from Creator.utils.lang_system import get_available_languages, set_language, LangT
        
        # ПЕРЕЗАГРУЖАЕМ НАСТРОЙКИ ПЕРЕД ОТКРЫТИЕМ
        self.load_settings()
        
        settings_window = ctk.CTkToplevel(self.root)
        settings_window.title(LangT("Настройки"))
        settings_window.geometry("450x650")
        settings_window.transient(self.root)
        settings_window.grab_set()
        
        # Центрируем окно
        settings_window.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - (450 // 2)
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - (650 // 2)
        settings_window.geometry(f"450x650+{x}+{y}")
        
        # Основной фрейм с прокруткой
        main_scroll = ctk.CTkScrollableFrame(settings_window, fg_color="transparent")
        main_scroll.pack(fill="both", expand=True, padx=20, pady=10)
        
        # === ЯЗЫК ===
        ctk.CTkLabel(main_scroll, text=LangT("Язык / Language:"), font=("Arial", 14)).pack(pady=(10, 5))
        
        available_langs = get_available_languages()
        lang_display_names = {
            "ru": "Русский",
            "en": "English",
        }
        
        display_values = [lang_display_names.get(lang, lang) for lang in available_langs]
        current_display = lang_display_names.get(self.settings.get("language", "ru"), self.settings.get("language", "ru"))
        
        language_var = ctk.StringVar(value=current_display)
        language_combo = ctk.CTkComboBox(
            main_scroll,
            values=display_values,
            variable=language_var,
            width=250
        )
        language_combo.pack(pady=5)
        
        # === РАЗДЕЛИТЕЛЬ ===
        ctk.CTkFrame(main_scroll, height=2, fg_color="#404040").pack(fill="x", pady=15)
        
        # === ПАПКА СОХРАНЕНИЯ ===
        ctk.CTkLabel(main_scroll, text=LangT("Папка сохранения модов:"), font=("Arial", 14)).pack(pady=(10, 5))
        
        appdata_roaming = os.getenv('APPDATA')
        
        folder_options = {
            LangT("Программа"): "mods",
            LangT("Игра Steam"): r"C:\Program Files (x86)\Steam\steamapps\common\Mindustry\saves\mods",
            LangT("Игра Free"): os.path.join(appdata_roaming, "Mindustry", "mods") if appdata_roaming else "mods"
        }
        
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
            main_scroll,
            values=list(folder_options.keys()),
            variable=display_var,
            width=250
        )
        folder_combo.pack(pady=5)
        
        # === РАЗДЕЛИТЕЛЬ ===
        ctk.CTkFrame(main_scroll, height=2, fg_color="#404040").pack(fill="x", pady=15)
        
        # === ПЕРЕКЛЮЧАТЕЛЬ ПОКАЗА КОНТЕНТА (БЕЗ ИНВЕРСИИ) ===
        hide_content_frame = ctk.CTkFrame(main_scroll, fg_color="transparent")
        hide_content_frame.pack(fill="x", pady=10)
        
        ctk.CTkLabel(
            hide_content_frame,
            text=LangT("Показывать контент в редакторе:"),
            font=("Arial", 14)
        ).pack(side="left", padx=(0, 10))
        
        # ПРЯМАЯ ЛОГИКА: show_content = not hide_content
        show_content = not self.settings.get("hide_content", False)
        show_content_var = ctk.BooleanVar(value=show_content)
        
        show_content_switch = ctk.CTkSwitch(
            hide_content_frame,
            text=LangT("Вкл") if show_content_var.get() else LangT("Выкл"),
            variable=show_content_var,
            command=lambda: show_content_switch.configure(
                text=LangT("Вкл") if show_content_var.get() else LangT("Выкл")
            ),
            onvalue=True,
            offvalue=False,
            width=60
        )
        show_content_switch.pack(side="left")
        
        ctk.CTkLabel(
            main_scroll,
            text=LangT("Отключите для скрытия списка блоков/предметов в редакторе"),
            font=("Arial", 10),
            text_color="#888888"
        ).pack(pady=(0, 5))
        
        # === РАЗДЕЛИТЕЛЬ ===
        ctk.CTkFrame(main_scroll, height=2, fg_color="#404040").pack(fill="x", pady=15)
        
        # === АВТООБНОВЛЕНИЕ ===
        autoupdate_frame = ctk.CTkFrame(main_scroll, fg_color="transparent")
        autoupdate_frame.pack(fill="x", pady=10)
        
        ctk.CTkLabel(
            autoupdate_frame,
            text=LangT("Автоматическая проверка обновлений:"),
            font=("Arial", 14)
        ).pack(side="left", padx=(0, 10))
        
        autoupdate_var = ctk.BooleanVar(value=self.settings.get("autoupdate", True))
        
        autoupdate_switch = ctk.CTkSwitch(
            autoupdate_frame,
            text=LangT("Вкл") if autoupdate_var.get() else LangT("Выкл"),
            variable=autoupdate_var,
            command=lambda: autoupdate_switch.configure(
                text=LangT("Вкл") if autoupdate_var.get() else LangT("Выкл")
            ),
            onvalue=True,
            offvalue=False,
            width=60
        )
        autoupdate_switch.pack(side="left")
        
        ctk.CTkLabel(
            main_scroll,
            text=LangT("Включите для автоматической проверки обновлений \n при запуске программы и установки"),
            font=("Arial", 10),
            text_color="#888888"
        ).pack(pady=(0, 5))
        
        # Кнопка ручной проверки обновлений
        def check_updates_now():
            """Ручная проверка обновлений"""
            if hasattr(self, 'updater') and self.updater:
                if messagebox.askyesno(
                    LangT("Проверка обновлений"),
                    LangT("Проверить наличие обновлений сейчас?")
                ):
                    def check_thread():
                        try:
                            self.root.after(0, lambda: messagebox.showinfo(
                                LangT("Проверка обновлений"),
                                LangT("Проверка обновлений запущена...\nПожалуйста, подождите.")
                            ))
                            result = self.updater.check_and_update(show_dialog=True, parent=self.root, check_autoupdate=False)
                            if not result:
                                self.root.after(0, lambda: messagebox.showinfo(
                                    LangT("Проверка обновлений"),
                                    LangT("Обновлений не найдено или произошла ошибка.")
                                ))
                        except Exception as e:
                            self.root.after(0, lambda: messagebox.showerror(
                                LangT("Ошибка"),
                                LangT("Ошибка проверки обновлений: {err}").format(err=str(e))
                            ))
                    
                    thread = threading.Thread(target=check_thread, daemon=True)
                    thread.start()
            else:
                messagebox.showwarning(
                    LangT("Ошибка"),
                    LangT("Модуль обновления не инициализирован.")
                )
        
        ctk.CTkButton(
            main_scroll,
            text=LangT("🔄 Проверить обновления сейчас"),
            command=check_updates_now,
            width=200,
            height=35,
            fg_color="#555555",
            hover_color="#666666"
        ).pack(pady=10)
        
        # === РАЗДЕЛИТЕЛЬ ===
        ctk.CTkFrame(main_scroll, height=2, fg_color="#404040").pack(fill="x", pady=15)
        
        # === ПУТЬ К ИГРЕ ===
        ctk.CTkLabel(main_scroll, text=LangT("Путь к исполняемому файлу Mindustry:"), font=("Arial", 14)).pack(pady=(10, 5))
        
        game_path_frame = ctk.CTkFrame(main_scroll, fg_color="transparent")
        game_path_frame.pack(fill="x", pady=5)
        
        game_path_var = ctk.StringVar(value=self.settings.get("game_path", ""))
        
        game_path_entry = ctk.CTkEntry(
            game_path_frame,
            textvariable=game_path_var,
            placeholder_text=LangT("Выберите путь к Mindustry.exe или Mindustry.jar"),
            width=200,
            height=35
        )
        game_path_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))
        
        def browse_game_path():
            filetypes = []
            if platform.system() == "Windows":
                filetypes = [(LangT("Исполняемые файлы"), "*.exe"), (LangT("JAR файлы"), "*.jar"), (LangT("Все файлы"), "*.*")]
            elif platform.system() == "Darwin":
                filetypes = [(LangT("Приложения"), "*.app"), (LangT("JAR файлы"), "*.jar"), (LangT("Все файлы"), "*.*")]
            else:
                filetypes = [(LangT("Все файлы"), "*.*")]
            
            selected_file = filedialog.askopenfilename(
                title=LangT("Выберите Mindustry"),
                filetypes=filetypes
            )
            if selected_file:
                game_path_var.set(selected_file)
        
        browse_btn = ctk.CTkButton(
            game_path_frame,
            text=LangT("Обзор..."),
            command=browse_game_path,
            width=80,
            height=35
        )
        browse_btn.pack(side="right")
        
        def check_game_path():
            path = game_path_var.get().strip()
            if not path:
                messagebox.showwarning(LangT("Предупреждение"), LangT("Путь не указан!"))
                return
            
            if os.path.exists(path):
                messagebox.showinfo(LangT("Успех"), LangT("✅ Файл найден!"))
            else:
                messagebox.showerror(LangT("Ошибка"), LangT("❌ Файл не найден!"))
        
        check_btn = ctk.CTkButton(
            main_scroll,
            text=LangT("Проверить путь"),
            command=check_game_path,
            width=150,
            height=30,
            fg_color="#555555"
        )
        check_btn.pack(pady=5)
        
        ctk.CTkLabel(
            main_scroll,
            text=LangT("Укажите путь к Mindustry.exe (Windows) или Mindustry.jar для запуска игры"),
            font=("Arial", 10),
            text_color="#888888"
        ).pack(pady=(0, 5))
        
        # === РАЗДЕЛИТЕЛЬ ===
        ctk.CTkFrame(main_scroll, height=2, fg_color="#404040").pack(fill="x", pady=15)
        
        # === КНОПКИ ===
        button_frame = ctk.CTkFrame(main_scroll, fg_color="transparent")
        button_frame.pack(pady=20)
        
        def save_settings():
            # Получаем выбранный язык
            selected_display = language_var.get()
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
            
            # Получаем состояние переключателя показа контента (ПРЯМАЯ ЛОГИКА)
            hide_content = not show_content_var.get()
            
            # Получаем состояние автообновления
            autoupdate_enabled = autoupdate_var.get()
            
            # Получаем путь к игре
            game_path = game_path_var.get().strip()
            
            # Сохраняем настройки
            self.settings["language"] = selected_lang if selected_lang else "ru"
            self.settings["save_folder"] = save_path
            self.settings["hide_content"] = hide_content
            self.settings["game_path"] = game_path
            self.settings["autoupdate"] = autoupdate_enabled
            self.save_settings()
            
            # Обновляем настройку автообновления в updater
            if hasattr(self, 'updater') and self.updater:
                try:
                    self.updater.set_autoupdate(autoupdate_enabled)
                except Exception as e:
                    print(f"Ошибка обновления настроек автообновления: {e}")
            
            # Меняем язык в системе
            if selected_lang and selected_lang != get_current_language():
                set_language(selected_lang)
            
            # Создаём папку если её нет
            try:
                Path(save_path).mkdir(parents=True, exist_ok=True)
                
                game_status = LangT("Не указан")
                if game_path:
                    if os.path.exists(game_path):
                        game_status = LangT("✅ Найден")
                    else:
                        game_status = LangT("❌ Не найден")
                
                messagebox.showinfo(
                    LangT("Успех"),
                    LangT("Настройки сохранены\nПапка: {save_path}\nПоказ контента: {status}\nАвтообновление: {autoupdate_status}\nПуть к игре: {game_status}").format(
                        save_path=save_path,
                        status=LangT("Включен") if not hide_content else LangT("Отключен"),
                        autoupdate_status=LangT("Включено") if autoupdate_enabled else LangT("Отключено"),
                        game_status=game_status
                    )
                )
                settings_window.destroy()
                
                # Обновляем интерфейс с новым языком
                self.show_main_ui()
            except Exception as e:
                messagebox.showerror(
                    LangT("Ошибка"),
                    LangT("Не удалось создать папку:\n{save_path}\n\nОшибка: {e}").format(
                        save_path=save_path,
                        e=e
                    )
                )
        
        ctk.CTkButton(
            button_frame,
            text=LangT("Сохранить"),
            command=save_settings,
            width=120,
            height=35
        ).pack(side="left", padx=10)
        
        ctk.CTkButton(
            button_frame,
            text=LangT("Отмена"),
            command=settings_window.destroy,
            width=120,
            height=35
        ).pack(side="left", padx=10)
       
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