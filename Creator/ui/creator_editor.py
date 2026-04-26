#p/Creator/ui/creator_editor.py
import customtkinter as ctk
import tkinter as tk
import os, re, json
import platform
import subprocess
import threading
import ctypes
from ctypes import wintypes
import shutil
from pathlib import Path
from tkinter import messagebox
from datetime import datetime
import time
import sys
import os

def resource_path(relative_path):
    """Получить абсолютный путь к ресурсу (работает и в .py, и в .exe)"""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

class CreatorEditor:
    def __init__(self, root, mod_folder, main_app): 
        self.root = root
        self.mod_folder = mod_folder
        self.main_app = main_app
        self.mod_name = mod_folder.name
        
        # Используем Path для кроссплатформенности
        self.TP_source_folder = Path(mod_folder) / "build" / "libs"
        self.TP_filename = f"{self.mod_name}Desktop.jar"
        self.TP_new_name = f"{self.mod_name}.jar"
        
        # Флаг для отслеживания состояния компиляции
        self.compiling = False
        
        # Для хранения окна прогресса
        self.progress_window = None

        # Загружаем настройки
        self.settings_file = Path("Creator/settings.json")
        self.settings = self.load_settings()
    
        # Инициализация создания блоков
        try:
            from .block_creator import create_block_creator
            self.block_creator = create_block_creator(self)
        except ImportError as e:
            print(f"Ошибка импорта block_creator: {e}")
            self.block_creator = None

    def load_image(self, filename, size=(80, 80)):
        """
        Загружает изображение или создает цветной блок
        """
        try:
            from PIL import Image, ImageDraw, ImageFont
            import io
            
            # Пробуем разные пути
            possible_paths = [
                Path(resource_path("Creator/icons")) / filename,
                Path("icons") / filename,
                Path(".") / filename,
                Path(__file__).parent.parent / "icons" / filename,
            ]
            
            for path in possible_paths:
                if path.exists():
                    #print(f"Загружаю иконку: {path}")
                    img = Image.open(path)
                    img = img.resize(size, Image.Resampling.LANCZOS)
                    return ctk.CTkImage(img)
            
            # Если файл не найден, создаем цветной блок с текстом
            print(f"Создаю заглушку для: {filename}")
            
            # Создаем цветной квадрат
            colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7', '#DDA0DD']
            color = colors[hash(filename) % len(colors)]
            
            img = Image.new('RGB', size, color=color)
            draw = ImageDraw.Draw(img)
            
            # Добавляем первые буквы имени файла
            try:
                # Берем первые 2 буквы без расширения
                letters = Path(filename).stem[:2].upper()
                font = ImageFont.load_default()
                
                # Вычисляем размер текста
                bbox = draw.textbbox((0, 0), letters, font=font)
                text_width = bbox[2] - bbox[0]
                text_height = bbox[3] - bbox[1]
                
                # Центрируем текст
                x = (size[0] - text_width) / 2
                y = (size[1] - text_height) / 2
                
                draw.text((x, y), letters, fill='white', font=font)
            except:
                pass
            
            return ctk.CTkImage(img)
            
        except Exception as e:
            print(f"Ошибка создания изображения: {e}")
            # Создаем простой серый квадрат
            img = Image.new('RGB', size, color='#363636')
            return ctk.CTkImage(img)

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
                print(f"Ошибка загрузки настроек: {e}")
                return default_settings
        else:
            self.save_settings(default_settings)
            return default_settings
        
    # Функции-обертки для блоков
    def create_wall(self):
        """Создание стены (обертка)"""
        if self.block_creator:
            self.block_creator.create_wall()
        else:
            print("Ошибка: block_creator не инициализирован")
            messagebox.showinfo("Информация", "Модуль создания стен пока не доступен")

    def create_solar_panel(self):
        """Создание стены (обертка)"""
        if self.block_creator:
            self.block_creator.create_solar_panel()
        else:
            print("Ошибка: block_creator не инициализирован")
            messagebox.showinfo("Информация", "Модуль создания солнечной панели пока не доступен")
    
    def create_battery(self):
        """Создание стены (обертка)"""
        if self.block_creator:
            self.block_creator.create_battery()
        else:
            print("Ошибка: block_creator не инициализирован")
            messagebox.showinfo("Информация", "Модуль создания батареи панели пока не доступен")

    def create_consume_generator(self):
        """Создание стены (обертка)"""
        if self.block_creator:
            self.block_creator.create_consume_generator()
        else:
            print("Ошибка: block_creator не инициализирован")
            messagebox.showinfo("Информация", "Модуль создания генератора пока не доступен")
    
    def create_beam_node(self):
        """Создание стены (обертка)"""
        if self.block_creator:
            self.block_creator.create_beam_node()
        else:
            print("Ошибка: block_creator не инициализирован")
            messagebox.showinfo("Информация", "Модуль создания энергитического башни пока не доступен")
    
    def create_power_node(self):
        """Создание стены (обертка)"""
        if self.block_creator:
            self.block_creator.create_power_node()
        else:
            print("Ошибка: block_creator не инициализирован")
            messagebox.showinfo("Информация", "Модуль создания энергитического узла пока не доступен")
    
    def create_shield_wall(self):
        """Создание стены (обертка)"""
        if self.block_creator:
            self.block_creator.create_shield_wall()
        else:
            print("Ошибка: block_creator не инициализирован")
            messagebox.showinfo("Информация", "Модуль создания Экранированой стены пока не доступен")
    
    def create_generic_crafter(self):
        """Создание стены (обертка)"""
        if self.block_creator:
            self.block_creator.create_generic_crafter()
        else:
            print("Ошибка: block_creator не инициализирован")
            messagebox.showinfo("Информация", "Модуль создания Завода пока не доступен")
    
    def create_bridge(self):
        """Создание стены (обертка)"""
        if self.block_creator:
            self.block_creator.create_bridge()
        else:
            print("Ошибка: block_creator не инициализирован")
            messagebox.showinfo("Информация", "Модуль создания моста пока не доступен")

    def create_conveyor(self):
        """Создание стены (обертка)"""
        if self.block_creator:
            self.block_creator.create_conveyor()
        else:
            print("Ошибка: block_creator не инициализирован")
            messagebox.showinfo("Информация", "Модуль создания конвеера пока не доступен")

    # ===================
    def move_and_rename_file(self):
        """
        Функция для перемещения и переименования файла
        """
        source_path = self.TP_source_folder / self.TP_filename
        
        print(f"Исходный файл: {source_path}")
        
        if not source_path.exists():
            print(f"Файл не найден: {source_path}")
            return False
        
        # Получаем путь сохранения из настроек
        save_folder = self.settings.get("save_folder", "mods")
        self.TP_target_folder = Path(save_folder)
        
        # Создаем папку назначения
        self.TP_target_folder.mkdir(parents=True, exist_ok=True)
        
        # Целевой путь
        target_path = self.TP_target_folder / self.TP_new_name
        
        try:
            # Если файл уже существует, удаляем его
            if target_path.exists():
                target_path.unlink()
            
            # Перемещаем файл
            shutil.move(str(source_path), str(target_path))
            print(f"Файл перемещен: {source_path} -> {target_path}")
            return True
        except Exception as e:
            print(f"Ошибка перемещения: {e}")
            return False

    def teleporte(self):
        """
        Метод для перемещения скомпилированного JAR файла
        """
        try:
            success = self.move_and_rename_file()
            
            if success:
                save_folder = self.settings.get("save_folder", "mods")
                messagebox.showinfo("Успех", f"Файл перемещен в {save_folder}/{self.TP_new_name}")
            else:
                messagebox.showwarning("Предупреждение", "Не удалось переместить файл. Возможно, он не найден.")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка при перемещении: {e}")

    def compile_mod(self):
        """Запуск компиляции в отдельном потоке с окном логов"""
        if self.compiling:
            messagebox.showwarning("Внимание", "Компиляция уже выполняется")
            return
        
        self.compiling = True
        
        # Создаем окно для логов
        log_window = ctk.CTkToplevel(self.root)
        log_window.title(f"Компиляция {self.mod_name}")
        log_window.geometry("800x600")
        log_window.minsize(600, 400)
        
        # Делаем окно модальным
        log_window.transient(self.root)
        log_window.grab_set()
        
        # Фрейм для логов
        log_frame = ctk.CTkFrame(log_window)
        log_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Фрейм для кнопок
        button_frame = ctk.CTkFrame(log_frame, fg_color="transparent", height=40)
        button_frame.pack(fill="x", padx=5, pady=(0, 5))
        
        # Кнопка копирования
        def copy_logs():
            log_window.clipboard_clear()
            log_window.clipboard_append(log_text.get("1.0", "end-1c"))
            copy_btn.configure(text="✅ Скопировано!", state="disabled")
            log_window.after(1500, lambda: copy_btn.configure(text="📋 Копировать", state="normal"))
        
        copy_btn = ctk.CTkButton(
            button_frame,
            text="📋 Копировать",
            command=copy_logs,
            width=120,
            height=30,
            font=("Arial", 12)
        )
        copy_btn.pack(side="left", padx=5)
        
        # Прогресс-бар
        progress = ctk.CTkProgressBar(log_frame, mode='indeterminate')
        progress.pack(fill="x", padx=5, pady=(0, 5))
        progress.start()
        
        # Текстовое поле для логов (только для чтения)
        log_text = ctk.CTkTextbox(
            log_frame,
            wrap="word",
            font=("Consolas", 11),
            fg_color="#1e1e1e",
            text_color="#d4d4d4",
            state="disabled"
        )
        log_text.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Кнопка закрытия (изначально неактивна)
        close_btn = ctk.CTkButton(
            log_frame,
            text="Закрыть",
            state="disabled",
            command=log_window.destroy,
            height=35,
            font=("Arial", 12)
        )
        close_btn.pack(pady=5)
        
        def log_to_window(message, level="INFO"):
            """Добавляет сообщение в окно логов с цветом"""
            colors = {
                "INFO": "#d4d4d4",
                "SUCCESS": "#6a9955",
                "WARNING": "#dcdcaa",
                "ERROR": "#f48771",
                "GRADLE": "#9cdcfe",
                "HEADER": "#c586c0"
            }
            
            def update():
                log_text.configure(state="normal")
                timestamp = datetime.now().strftime('%H:%M:%S')
                log_text.insert("end", f"[{timestamp}] ", "timestamp")
                log_text.insert("end", f"{message}\n", level)
                log_text.see("end")
                log_text.configure(state="disabled")
            
            log_text.tag_config("timestamp", foreground="#808080")
            for lvl, clr in colors.items():
                log_text.tag_config(lvl, foreground=clr)
            
            log_window.after(0, update)
        
        def sort_registration_lines(file_content):
            """
            Сортирует строки после //Registration_add:
            1. ModItems.Load(); и ModLiquid.Load(); - первые строки
            2. Tree.Load(); - должен быть в самом низу
            3. Все остальные строки - между ними
            """
            print("\n📝 Анализ файла...")
            lines = file_content.split('\n')
            
            # Находим маркер //Registration_add
            registration_marker_line = -1
            for i, line in enumerate(lines):
                if "//Registration_add" in line:
                    registration_marker_line = i
                    break
            
            if registration_marker_line == -1:
                print("⚠️ Маркер //Registration_add не найден")
                return file_content
            
            print(f"✅ Найден маркер //Registration_add на строке {registration_marker_line + 1}")
            
            # Ищем строки после маркера до конца метода или пустой строки
            start_line = registration_marker_line + 1
            end_line = len(lines)
            
            # Определяем границы блока (до пустой строки или закрывающей скобки)
            for i in range(start_line, len(lines)):
                line = lines[i].strip()
                if line == "" or "}" in line or ("//" in line and i != registration_marker_line):
                    end_line = i
                    break
            
            if start_line >= end_line:
                print(f"⚠️ Блок после маркера пуст (строки {start_line}-{end_line})")
                return file_content
            
            print(f"📦 Найден блок строк {start_line + 1}-{end_line + 1}")
            
            # Собираем все строки в блоке
            moditems_line = None
            modliquid_line = None
            tree_line = None
            other_lines = []
            
            for i in range(start_line, end_line):
                line = lines[i]
                stripped = line.strip()
                
                if stripped:  # Только непустые строки
                    if "ModItems.Load();" in stripped:
                        moditems_line = (i, line)
                        print(f"  🔹 Найден ModItems.Load() на строке {i + 1}")
                    elif "ModLiquid.Load();" in stripped:
                        modliquid_line = (i, line)
                        print(f"  🔹 Найден ModLiquid.Load() на строке {i + 1}")
                    elif any(tree_name in stripped for tree_name in ["Tree.Load();", "WallsTree.Load();", "BatteryTree.Load();", "SolarTree.Load();", "ShieldTree.Load();", "PowerNodeTree.Load();", "BeamTree.Load();", "GeneratorTree.Load();", "CrafterTree.Load();"]):
                        tree_line = (i, line)
                        print(f"  🔻 Найден Tree.Load() на строке {i + 1}")
                    else:
                        other_lines.append((i, line))
                        print(f"  🔸 Обычная строка [{i + 1}]: {stripped}")
            
            # Если не найдено ни одного из нужных методов
            if moditems_line is None and modliquid_line is None and tree_line is None and not other_lines:
                print("⚠️ В блоке нет строк для сортировки")
                return file_content
            
            # Определяем, нужно ли что-то менять
            changes_needed = False
            
            # Проверяем текущие позиции для ModItems и ModLiquid
            if moditems_line:
                moditems_pos, _ = moditems_line
                if moditems_pos != start_line and (modliquid_line is None or moditems_pos != start_line + 1):
                    changes_needed = True
                    print("❌ ModItems не на правильной позиции")
            
            if modliquid_line:
                modliquid_pos, _ = modliquid_line
                if moditems_line:
                    if modliquid_pos != start_line + 1:
                        changes_needed = True
                        print("❌ ModLiquid не на правильной позиции")
                else:
                    if modliquid_pos != start_line:
                        changes_needed = True
                        print("❌ ModLiquid не на правильной позиции")
            
            # Проверяем позицию Tree - должна быть последней
            if tree_line:
                tree_pos, _ = tree_line
                max_other_pos = max([pos for pos, _ in other_lines]) if other_lines else start_line - 1
                if tree_pos <= max_other_pos:
                    changes_needed = True
                    print(f"❌ Tree не внизу (позиция {tree_pos + 1}, последняя обычная строка {max_other_pos + 1})")
            
            if not changes_needed:
                print("✅ Порядок уже правильный")
                return file_content
            
            # СОРТИРУЕМ
            print("\n🔄 Выполняется сортировка...")
            
            sorted_lines = []
            
            # 1. ModItems (если есть)
            if moditems_line:
                _, line_str = moditems_line
                sorted_lines.append(line_str)
                print(f"  📌 ModItems на позицию 1")
            
            # 2. ModLiquid (если есть)
            if modliquid_line:
                _, line_str = modliquid_line
                sorted_lines.append(line_str)
                print(f"  📌 ModLiquid на позицию {2 if moditems_line else 1}")
            
            # 3. Все остальные (кроме Tree) - сортируем по алфавиту
            other_texts = [line for _, line in other_lines]
            other_texts.sort(key=lambda x: x.strip().lower())
            sorted_lines.extend(other_texts)
            if other_texts:
                print(f"  📌 {len(other_texts)} обычных строк (отсортированы)")
            
            # 4. Tree (в самом конце)
            if tree_line:
                _, tree_str = tree_line
                sorted_lines.append(tree_str)
                print(f"  📌 Tree в конец")
            
            # Создаем новый список строк
            new_lines = lines[:start_line] + sorted_lines + lines[end_line:]
            
            print("✅ Сортировка завершена")
            return '\n'.join(new_lines)
        
        def compile_thread():
            try:
                original_cwd = os.getcwd()
                
                log_to_window("="*60, "HEADER")
                log_to_window("🚀 НАЧАЛО КОМПИЛЯЦИИ", "HEADER")
                log_to_window("="*60, "HEADER")
                log_to_window(f"📁 Мод: {self.mod_name}", "INFO")
                log_to_window(f"📂 Папка: {self.mod_folder}", "INFO")
                
                # ПЕРЕД ВСЕМ - сортируем строки в главном файле
                mod_name_lower = self.mod_name.lower() if self.mod_name else self.mod_name
                main_mod_path = Path(self.mod_folder) / "src" / mod_name_lower / f"{self.mod_name}JavaMod.java"
                
                log_to_window(f"\n📄 Проверка файла: {main_mod_path}", "HEADER")
                
                if main_mod_path.exists():
                    try:
                        with open(main_mod_path, 'r', encoding='utf-8') as file:
                            content = file.read()
                        
                        log_to_window(f"📊 Размер файла: {len(content)} символов", "INFO")
                        
                        # Сортируем строки после //Registration_add
                        sorted_content = sort_registration_lines(content)
                        
                        if sorted_content != content:
                            with open(main_mod_path, 'w', encoding='utf-8') as file:
                                file.write(sorted_content)
                            log_to_window("✅ Файл обновлен: строки отсортированы", "SUCCESS")
                        else:
                            log_to_window("✅ Файл уже в правильном порядке", "SUCCESS")
                            
                    except Exception as e:
                        log_to_window(f"❌ Ошибка при обработке файла: {e}", "ERROR")
                else:
                    log_to_window(f"⚠️ Файл не найден: {main_mod_path}", "WARNING")
                
                # ТЕПЕРЬ переходим в папку мода и компилируем
                log_to_window("\n" + "="*60, "HEADER")
                log_to_window("⚙️ ЗАПУСК GRADLE", "HEADER")
                log_to_window("="*60, "HEADER")
                
                os.chdir(str(self.mod_folder))
                
                gradle_script = "gradlew.bat" if platform.system() == "Windows" else "./gradlew"
                
                if not Path(gradle_script).exists():
                    log_to_window(f"❌ {gradle_script} не найден в папке мода!", "ERROR")
                    self.root.after(0, lambda: messagebox.showerror(
                        "Ошибка", 
                        f"{gradle_script} не найден в папке мода!"
                    ))
                    self.compiling = False
                    os.chdir(original_cwd)
                    close_btn.configure(state="normal")
                    progress.stop()
                    return
                
                log_to_window(f"✅ Gradle найден: {gradle_script}", "SUCCESS")
                
                # Компилируем с выводом в реальном времени
                cmd = [gradle_script, "jar"]
                log_to_window(f"📋 Команда: {' '.join(cmd)}", "INFO")
                log_to_window("\n⏳ Компиляция выполняется...\n", "HEADER")
                
                # Запускаем процесс с pipe для чтения вывода в реальном времени
                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    bufsize=1,
                    universal_newlines=True,
                    shell=True if platform.system() == "Windows" else False
                )
                
                # Читаем stdout в реальном времени
                for line in process.stdout:
                    if line.strip():
                        log_to_window(line.strip(), "GRADLE")
                
                # Ждем завершения и читаем stderr
                return_code = process.wait()
                stderr = process.stderr.read()
                
                if stderr:
                    for line in stderr.split('\n'):
                        if line.strip():
                            log_to_window(line.strip(), "ERROR" if return_code != 0 else "GRADLE")
                
                os.chdir(original_cwd)
                
                log_to_window("\n" + "="*60, "HEADER")
                
                # Обрабатываем результат
                if return_code == 0:
                    log_to_window("✅ КОМПИЛЯЦИЯ УСПЕШНА!", "SUCCESS")
                    
                    jar_files = list(Path(self.mod_folder).glob("build/libs/*.jar"))
                    if jar_files:
                        jar_name = jar_files[0].name
                        jar_size = jar_files[0].stat().st_size / 1024
                        log_to_window(f"📦 JAR: {jar_name}", "SUCCESS")
                        log_to_window(f"📊 Размер: {jar_size:.2f} KB", "SUCCESS")
                        
                        self.root.after(0, lambda: messagebox.showinfo(
                            "Успех", 
                            f"✅ Мод скомпилирован!\n\n📦 JAR: {jar_name}\n📊 Размер: {jar_size:.2f} KB"
                        ))
                        
                        # Запускаем перемещение файла - ТАК ЖЕ КАК В СТАРОМ КОДЕ
                        log_to_window("📦 Запуск перемещения JAR...", "INFO")
                        self.teleporte()  # Прямой вызов, как в старом коде
                    else:
                        log_to_window("⚠️ JAR файл не найден в build/libs/", "WARNING")
                        self.root.after(0, lambda: messagebox.showinfo(
                            "Успех", 
                            "Компиляция завершена, но JAR файл не найден"
                        ))
                else:
                    error_msg = stderr[:500] if stderr else "Неизвестная ошибка"
                    log_to_window(f"❌ ОШИБКА КОМПИЛЯЦИИ! Код: {return_code}", "ERROR")
                    log_to_window(f"📄 Ошибка: {error_msg}", "ERROR")
                    
                    self.root.after(0, lambda: messagebox.showerror(
                        "Ошибка", 
                        f"Ошибка компиляции:\n{error_msg}"
                    ))
                
                log_to_window("="*60, "HEADER")
                
            except subprocess.TimeoutExpired:
                log_to_window("⏰ ТАЙМАУТ! Компиляция превысила время ожидания (5 минут)", "ERROR")
                self.root.after(0, lambda: messagebox.showerror(
                    "Таймаут", 
                    "Компиляция превысила время ожидания (5 минут)"
                ))
            
            except Exception as e:
                log_to_window(f"❌ КРИТИЧЕСКАЯ ОШИБКА: {e}", "ERROR")
                import traceback
                log_to_window(traceback.format_exc(), "ERROR")
                self.root.after(0, lambda: messagebox.showerror(
                    "Ошибка", 
                    f"Ошибка: {str(e)}"
                ))
            
            finally:
                try:
                    os.chdir(os.path.dirname(os.path.abspath(__file__)))
                except:
                    pass
                
                self.compiling = False
                close_btn.configure(state="normal")
                progress.stop()
                log_to_window("\n🏁 Компиляция завершена", "HEADER")
        
        # Запускаем компиляцию в отдельном потоке
        thread = threading.Thread(target=compile_thread, daemon=True)
        thread.start()

    def create_progress_window(self):
        """Создание окна прогресса в главном потоке"""
        # Сначала безопасно закрываем старое окно, если оно есть
        self.safe_close_progress_window()
        
        # Создаем новое окно
        self.progress_window = ctk.CTkToplevel(self.root)
        self.progress_window.title("Компиляция")
        self.progress_window.geometry("400x150")
        self.progress_window.resizable(False, False)
        
        # Делаем модальным
        self.progress_window.transient(self.root)
        self.progress_window.grab_set()
        
        # Центрируем окно
        self.progress_window.update_idletasks()
        width = self.progress_window.winfo_width()
        height = self.progress_window.winfo_height()
        x = (self.progress_window.winfo_screenwidth() // 2) - (width // 2)
        y = (self.progress_window.winfo_screenheight() // 2) - (height // 2)
        self.progress_window.geometry(f'{width}x{height}+{x}+{y}')
        
        ctk.CTkLabel(
            self.progress_window, 
            text="Компиляция мода...", 
            font=("Arial", 14, "bold")
        ).pack(pady=20)
        
        self.progress_bar = ctk.CTkProgressBar(self.progress_window, width=300)
        self.progress_bar.pack(pady=10)
        self.progress_bar.set(0)
        self.progress_bar.start()
        
        # Обработчик закрытия окна
        self.progress_window.protocol("WM_DELETE_WINDOW", self.on_progress_window_close)

    def safe_close_progress_window(self):
        """Безопасное закрытие окна прогресса"""
        try:
            if hasattr(self, 'progress_window') and self.progress_window:
                try:
                    # Останавливаем прогресс-бар
                    if hasattr(self, 'progress_bar'):
                        self.progress_bar.stop()
                except:
                    pass
                
                # Снимаем захват
                try:
                    self.progress_window.grab_release()
                except:
                    pass
                
                # Уничтожаем окно
                self.progress_window.destroy()
                
        except Exception as e:
            print(f"Ошибка при закрытии окна прогресса: {e}")
        finally:
            self.progress_window = None

    def on_progress_window_close(self):
        """Обработчик закрытия окна прогресса пользователем"""
        if self.compiling:
            if messagebox.askyesno("Подтверждение", "Прервать компиляцию?"):
                self.compiling = False
                self.safe_close_progress_window()
        else:
            self.safe_close_progress_window()

    def open_creator(self):
        """Открытие интерфейса редактора"""
        self.clear_window()
        
        left_frame = ctk.CTkFrame(self.root, width=220)
        right_frame = ctk.CTkFrame(self.root)
        left_frame.pack(side="left", fill="y", padx=5, pady=5)
        right_frame.pack(side="right", fill="both", expand=True, padx=5, pady=5)
        
        self.setup_actions_panel(left_frame)
        self.setup_content_panel(right_frame)

    def create_item(self):
        """Создает или добавляет новый предмет в ModItems.java"""

        PATEH_FOLDER = [
            "consume_generators", "walls",
            "solar_panels", "batterys",
            "beam_nodes", "power_nodes",
            "shield_walls"
        ]
        
        # Очищаем всё окно
        self.clear_window()
        
        # Основной фрейм с прокруткой
        main_frame = ctk.CTkFrame(self.root, fg_color="#2b2b2b")  # Темный фон
        main_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Фрейм для прокрутки
        scroll_frame = ctk.CTkScrollableFrame(
            main_frame,
            width=500,
            height=600,
            fg_color="#2b2b2b"  # Темный фон
        )
        scroll_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Заголовок
        title_frame = ctk.CTkFrame(scroll_frame, fg_color="transparent")
        title_frame.pack(fill="x", pady=(0, 20))
        
        title_label = ctk.CTkLabel(
            title_frame,
            text="Создание предмета",
            font=("Arial", 24, "bold"),
            text_color="#4CAF50"  # Зеленый цвет
        )
        title_label.pack(pady=10)
        
        # Карточка для основной информации
        info_card = ctk.CTkFrame(
            scroll_frame,
            corner_radius=15,
            border_width=2,
            border_color="#404040",  # Темная граница
            fg_color="#363636"  # Серый фон карточки
        )
        info_card.pack(fill="x", pady=(0, 20))
        
        # Заголовок карточки
        card_title = ctk.CTkLabel(
            info_card,
            text="Основная информация",
            font=("Arial", 18, "bold"),
            text_color="#E0E0E0"  # Светло-серый текст
        )
        card_title.pack(pady=(15, 10), padx=20, anchor="w")
        
        # Поле ввода названия
        name_frame = ctk.CTkFrame(info_card, fg_color="transparent")
        name_frame.pack(fill="x", padx=20, pady=(0, 15))
        
        name_label = ctk.CTkLabel(
            name_frame,
            text="Название предмета (английское, можно пробел, первая буква маленькая):",
            font=("Arial", 16),
            text_color="#BDBDBD"  # Серый текст
        )
        name_label.pack(anchor="w", pady=(0, 5))
        
        entry_name = ctk.CTkEntry(
            name_frame,
            width=400,
            height=40,
            placeholder_text="item name",
            font=("Arial", 15),
            border_width=2,
            corner_radius=8,
            fg_color="#424242",  # Темный фон поля ввода
            border_color="#555555",  # Цвет границы
            text_color="#FFFFFF",  # Белый текст
            placeholder_text_color="#888888"  # Серый placeholder
        )
        entry_name.pack(fill="x", pady=(0, 5))
        
        # Функция форматирования названий
        def format_to_lower_camel(text):
            """Преобразует текст в формат: первое слово с маленькой буквы, остальные с большой (без пробелов)
            Примеры:
            'item' → 'item'
            'big item' → 'bigItem'
            'very big item' → 'veryBigItem'
            'energy core' → 'energyCore'
            """
            words = text.strip().split()
            if not words:
                return ""
            
            # Первое слово в нижнем регистре
            result = words[0].lower()
            
            # Остальные слова с заглавной буквы
            for word in words[1:]:
                result += word.capitalize()
            
            return result
        
        # Функция валидации
        def validate_float_input(value):
            """Проверяет, является ли значение допустимым float с максимум 2 знаками после точки"""
            if value == "" or value == ".":
                return True
            
            # Проверяем формат числа
            pattern = r'^\d*\.?\d{0,2}$'
            if not re.match(pattern, value):
                return False
            
            # Проверяем максимальное значение
            try:
                num = float(value)
                if num > 5000.00:
                    return False
            except ValueError:
                return False
            
            return True

        # Функция форматирования
        def format_float(value):
            """Форматирует значение до 2 знаков после точки"""
            if not value:
                return ""
            
            try:
                num = float(value)
                # Ограничиваем максимальное значение
                num = min(num, 5000.00)
                # Форматируем до 2 знаков
                formatted = f"{num:.2f}"
                # Убираем лишние нули
                if formatted.endswith(".00"):
                    formatted = formatted[:-3]
                elif formatted.endswith(".0"):
                    formatted = formatted[:-2]
                return formatted
            except ValueError:
                return value

        # Регистрируем функцию валидации
        vcmd = (self.root.register(validate_float_input), '%P')

        # Карточка для свойств
        properties_card = ctk.CTkFrame(
            scroll_frame,
            corner_radius=15,
            border_width=2,
            border_color="#404040",  # Темная граница
            fg_color="#363636"  # Серый фон карточки
        )
        properties_card.pack(fill="x", pady=(0, 20))

        # Заголовок карточки свойств
        properties_title = ctk.CTkLabel(
            properties_card,
            text="Свойства предмета",
            font=("Arial", 18, "bold"),
            text_color="#E0E0E0"  # Светло-серый текст
        )
        properties_title.pack(pady=(15, 10), padx=20, anchor="w")

        # Грид для свойств
        properties_grid = ctk.CTkFrame(properties_card, fg_color="transparent")
        properties_grid.pack(fill="x", padx=20, pady=(0, 15))

        # Метка и поле для заряда
        charge_frame = ctk.CTkFrame(properties_grid, fg_color="transparent")
        charge_frame.grid(row=0, column=0, padx=10, pady=5, sticky="ew")
        
        charge_label = ctk.CTkLabel(
            charge_frame,
            text="⚡ Заряд (charge):",
            font=("Arial", 15),
            text_color="#BDBDBD"  # Серый текст
        )
        charge_label.pack(anchor="w", pady=(0, 5))
        
        entry_charge = ctk.CTkEntry(
            charge_frame,
            width=180,
            height=38,
            placeholder_text="0.00",
            font=("Arial", 14),
            validate="key",
            validatecommand=vcmd,
            fg_color="#424242",  # Темный фон поля ввода
            border_color="#555555",  # Цвет границы
            text_color="#FFFFFF",  # Белый текст
            placeholder_text_color="#888888"  # Серый placeholder
        )
        entry_charge.pack(fill="x")

        # Метка и поле для воспламеняемости
        flammability_frame = ctk.CTkFrame(properties_grid, fg_color="transparent")
        flammability_frame.grid(row=0, column=1, padx=10, pady=5, sticky="ew")
        
        flammability_label = ctk.CTkLabel(
            flammability_frame,
            text="🔥 Воспламеняемость (flammability):",
            font=("Arial", 15),
            text_color="#BDBDBD"  # Серый текст
        )
        flammability_label.pack(anchor="w", pady=(0, 5))
        
        entry_flammability = ctk.CTkEntry(
            flammability_frame,
            width=180,
            height=38,
            placeholder_text="0.00",
            font=("Arial", 14),
            validate="key",
            validatecommand=vcmd,
            fg_color="#424242",  # Темный фон поля ввода
            border_color="#555555",  # Цвет границы
            text_color="#FFFFFF",  # Белый текст
            placeholder_text_color="#888888"  # Серый placeholder
        )
        entry_flammability.pack(fill="x")

        # Метка и поле для взрывоопасности
        explosiveness_frame = ctk.CTkFrame(properties_grid, fg_color="transparent")
        explosiveness_frame.grid(row=1, column=0, padx=10, pady=5, sticky="ew")
        
        explosiveness_label = ctk.CTkLabel(
            explosiveness_frame,
            text="💥 Взрывоопасность (explosiveness):",
            font=("Arial", 15),
            text_color="#BDBDBD"  # Серый текст
        )
        explosiveness_label.pack(anchor="w", pady=(0, 5))
        
        entry_explosiveness = ctk.CTkEntry(
            explosiveness_frame,
            width=180,
            height=38,
            placeholder_text="0.00",
            font=("Arial", 14),
            validate="key",
            validatecommand=vcmd,
            fg_color="#424242",  # Темный фон поля ввода
            border_color="#555555",  # Цвет границы
            text_color="#FFFFFF",  # Белый текст
            placeholder_text_color="#888888"  # Серый placeholder
        )
        entry_explosiveness.pack(fill="x")

        # Метка и поле для радиоактивности
        radioactivity_frame = ctk.CTkFrame(properties_grid, fg_color="transparent")
        radioactivity_frame.grid(row=1, column=1, padx=10, pady=5, sticky="ew")
        
        radioactivity_label = ctk.CTkLabel(
            radioactivity_frame,
            text="☢️ Радиоактивность (radioactivity):",
            font=("Arial", 15),
            text_color="#BDBDBD"  # Серый текст
        )
        radioactivity_label.pack(anchor="w", pady=(0, 5))
        
        entry_radioactivity = ctk.CTkEntry(
            radioactivity_frame,
            width=180,
            height=38,
            placeholder_text="0.00",
            font=("Arial", 14),
            validate="key",
            validatecommand=vcmd,
            fg_color="#424242",  # Темный фон поля ввода
            border_color="#555555",  # Цвет границы
            text_color="#FFFFFF",  # Белый текст
            placeholder_text_color="#888888"  # Серый placeholder
        )
        entry_radioactivity.pack(fill="x")

        # Привязываем форматирование при потере фокуса
        def on_focus_out_charge(event):
            value = entry_charge.get()
            formatted = format_float(value)
            if formatted != value:
                entry_charge.delete(0, "end")
                entry_charge.insert(0, formatted)

        entry_charge.bind("<FocusOut>", on_focus_out_charge)

        def on_focus_out_flammability(event):
            value = entry_flammability.get()
            formatted = format_float(value)
            if formatted != value:
                entry_flammability.delete(0, "end")
                entry_flammability.insert(0, formatted)

        entry_flammability.bind("<FocusOut>", on_focus_out_flammability)

        def on_focus_out_explosiveness(event):
            value = entry_explosiveness.get()
            formatted = format_float(value)
            if formatted != value:
                entry_explosiveness.delete(0, "end")
                entry_explosiveness.insert(0, formatted)

        entry_explosiveness.bind("<FocusOut>", on_focus_out_explosiveness)

        def on_focus_out_radioactivity(event):
            value = entry_radioactivity.get()
            formatted = format_float(value)
            if formatted != value:
                entry_radioactivity.delete(0, "end")
                entry_radioactivity.insert(0, formatted)

        entry_radioactivity.bind("<FocusOut>", on_focus_out_radioactivity)

        # Карточка для дополнительных опций
        options_card = ctk.CTkFrame(
            scroll_frame,
            corner_radius=15,
            border_width=2,
            border_color="#404040",  # Темная граница
            fg_color="#363636"  # Серый фон карточки
        )
        options_card.pack(fill="x", pady=(0, 20))

        # Заголовок карточки опций
        options_title = ctk.CTkLabel(
            options_card,
            text="Дополнительные опции",
            font=("Arial", 18, "bold"),
            text_color="#E0E0E0"  # Светло-серый текст
        )
        options_title.pack(pady=(15, 10), padx=20, anchor="w")

        # Чекбокс для alwaysUnlocked
        always_unlocked_var = ctk.BooleanVar(value=False)
        
        always_unlocked_frame = ctk.CTkFrame(options_card, fg_color="transparent")
        always_unlocked_frame.pack(fill="x", padx=20, pady=(0, 15))
        
        always_unlocked_checkbox = ctk.CTkCheckBox(
            always_unlocked_frame,
            text="🔓 Always Unlocked",
            variable=always_unlocked_var,
            font=("Arial", 15),
            text_color="#BDBDBD",  # Серый текст
            border_width=2,
            corner_radius=6,
            fg_color="#4CAF50",  # Зеленый цвет фона
            hover_color="#45a049",
            border_color="#555555"  # Цвет границы
        )
        always_unlocked_checkbox.pack(anchor="w", pady=5)

        # Метка для статуса
        status_frame = ctk.CTkFrame(scroll_frame, fg_color="transparent")
        status_frame.pack(fill="x", pady=(0, 20))
        
        status_label = ctk.CTkLabel(
            status_frame,
            text="",
            font=("Arial", 14),
            wraplength=450,
            justify="left",
            text_color="#E0E0E0"  # Светло-серый текст
        )
        status_label.pack()
        
        # Фрейм для кнопок
        button_frame = ctk.CTkFrame(scroll_frame, fg_color="transparent")
        button_frame.pack(fill="x", pady=20)
        
        def copy_icon(item_name):
            """
            Копирует иконку из creator/icons/ 
            в assets/sprites/items/ с именем предмета
            """
            try:
                # Форматируем имя для текстуры
                formatted_name = format_to_lower_camel(item_name)
                
                # Путь к папке с иконками
                icons_dir = Path(resource_path("Creator/icons/items"))
                
                # Проверяем существование папки
                if not icons_dir.exists():
                    print(f"Папка с иконками не найдена: {icons_dir}")
                    return False
                
                # Получаем список всех файлов изображений
                image_extensions = ['.png', '.jpg', '.jpeg']
                image_files = []
                
                for ext in image_extensions:
                    image_files.extend(list(icons_dir.glob(f"*{ext}")))
                
                if not image_files:
                    print(f"Нет изображений в папке: {icons_dir}")
                    return False
                
                # Выбираем иконку
                icon = resource_path("Creator/icons/items/copper.png")
                
                # Путь назначения в папке мода
                # Используем отформатированное имя в нижнем регистре
                target_name = formatted_name + ".png"
                target_dir = Path(self.mod_folder) / "assets" / "sprites" / "items"
                target_dir.mkdir(parents=True, exist_ok=True)
                
                target_path = target_dir / target_name
                
                # Копируем файл
                shutil.copy2(icon, target_path)
                
                print(f"Иконка скопирована: {icon} -> {target_path}")
                return True
                
            except Exception as e:
                print(f"Ошибка при копировании иконки: {e}")
                return False

        def check_if_name_exists(name):
            """Проверяет, существует ли имя по текстурам в sprites"""
            # Форматируем имя для проверки
            formatted_name = format_to_lower_camel(name)
            
            # Проверяем существование текстуры в разных местах
            name_lower = formatted_name
            
            # Пути для проверки
            check_paths = [
                Path(self.mod_folder) / "assets" / "sprites" / "items" / f"{name_lower}.png",
                Path(self.mod_folder) / "assets" / "sprites" / "liquids" / f"{name_lower}.png",
                Path(self.mod_folder) / "assets" / "sprites" / "blocks" / f"{PATEH_FOLDER}" / f"{name_lower}.png",
                Path(self.mod_folder) / "assets" / "sprites" / "blocks" / f"{PATEH_FOLDER}" / f"{name_lower}" / f"{name_lower}.png",
            ]
            
            for path in check_paths:
                if path.exists():
                    return True
            
            return False

        def process_item():
            """Обрабатывает создание предмета"""
            original_name = entry_name.get().strip()
            
            if not original_name:
                status_label.configure(
                    text="❌ Ошибка: Введите имя предмета!", 
                    text_color="#F44336"  # Красный цвет для ошибки
                )
                return
            
            # Форматируем имя для использования в коде
            constructor_name = format_to_lower_camel(original_name)
            
            if not constructor_name:
                status_label.configure(
                    text="❌ Ошибка: Некорректное название!", 
                    text_color="#F44336"
                )
                return

            # Проверка имени по текстурам
            if check_if_name_exists(original_name):
                status_label.configure(
                    text=f"❌ Ошибка: Имя '{constructor_name}' уже используется (текстура существует)!", 
                    text_color="#F44336"
                )
                return
            
            # Копируем случайную иконку
            icon_copied = copy_icon(original_name)
            icon_status = "✅ Иконка создана" if icon_copied else "⚠️ Иконка не создана"
            
            # Получаем значения свойств
            charge_value = entry_charge.get().strip() or "0"
            flammability_value = entry_flammability.get().strip() or "0"
            explosiveness_value = entry_explosiveness.get().strip() or "0"
            radioactivity_value = entry_radioactivity.get().strip() or "0"
            
            # Форматируем значения
            charge_value = format_float(charge_value)
            flammability_value = format_float(flammability_value)
            explosiveness_value = format_float(explosiveness_value)
            radioactivity_value = format_float(radioactivity_value)
            
            # Получаем значение alwaysUnlocked
            always_unlocked_value = "true" if always_unlocked_var.get() else "false"

            # Имя переменной (с заглавной буквы - UpperCamelCase)
            if constructor_name and len(constructor_name) > 0:
                var_name = constructor_name[0].lower() + constructor_name[1:] if constructor_name else ""
            else:
                var_name = ""
            
            # Создаем properties строку с правильными значениями
            properties = f"""    charge = {charge_value}f;
            flammability = {flammability_value}f;
            explosiveness = {explosiveness_value}f;
            radioactivity = {radioactivity_value}f;
            alwaysUnlocked = {always_unlocked_value};
            
            localizedName = Core.bundle.get("{var_name}.name", "OH NO");
            description = Core.bundle.get("{var_name}.description", "OH NO");"""
            
            # Путь к файлу ModItems.java
            mod_name_lower = self.mod_name.lower() if self.mod_name else self.mod_name
            item_registration_path = f"{self.mod_folder}/src/{mod_name_lower}/init/items/ModItems.java"
            
            # Путь к главному файлу мода
            main_mod_path = f"{self.mod_folder}/src/{mod_name_lower}/{self.mod_name}JavaMod.java"
            
            # Создаем директории, если их нет
            os.makedirs(os.path.dirname(item_registration_path), exist_ok=True)
            
            # Читаем или создаем файл ModItems.java
            try:
                with open(item_registration_path, 'r', encoding='utf-8') as file:
                    content = file.read()
            except FileNotFoundError:
                # Базовый шаблон файла
                content = f"""package {mod_name_lower}.init.items;

import arc.graphics.Color;
import mindustry.type.Item;
import arc.Core;

public class ModItems {{
    public static Item;
                                    
    public static void Load() {{
        // Регистрация предметов
    }}
}}"""
            
            # Проверяем, есть ли уже этот предмет
            item_exists = var_name in content
            
            if not item_exists:
                # 1. Добавляем в объявления (public static Item)
                if "public static Item;" in content:
                    # Заменяем на первое объявление
                    content = content.replace(
                        "public static Item;",
                        f"public static Item {var_name};"
                    )
                elif "public static Item " in content:
                    # Находим строку с объявлениями
                    lines = content.split('\n')
                    for i, line in enumerate(lines):
                        if "public static Item " in line and var_name not in line:
                            # Добавляем через запятую
                            lines[i] = line.rstrip(';') + f", {var_name};"
                            content = '\n'.join(lines)
                            break
                
                # 2. Добавляем инициализацию в метод Load()
                # Находим метод Load()
                load_start = content.find("public static void Load() {")
                if load_start != -1:
                    # Находим открывающую скобку метода
                    open_brace = content.find('{', load_start)
                    if open_brace != -1:
                        # Вставляем после открывающей скобки с правильными отступами
                        insert_pos = open_brace + 1
                        indent = "        "  # 8 пробелов
                        
                        # Создаем код предмета с properties
                        # В кавычках используем отформатированное имя constructor_name
                        item_code = f'\n{indent}{var_name} = new Item("{constructor_name}"){{{{\n{indent}{properties}\n{indent}}}}};'
                        
                        content = content[:insert_pos] + item_code + content[insert_pos:]
                
                # Записываем файл ModItems.java
                with open(item_registration_path, 'w', encoding='utf-8') as file:
                    file.write(content)
                
                # Теперь работаем с главным файлом мода
                try:
                    with open(main_mod_path, 'r', encoding='utf-8') as file:
                        main_content = file.read()
                    
                    original_main_content = main_content  # Сохраняем оригинал для сравнения
                    modified = False
                    import_added = False
                    registration_added = False
                    
                    # Проверяем наличие импорта ModItems
                    import_statement = f"import {mod_name_lower}.init.items.ModItems;"
                    
                    if import_statement not in main_content:
                        # Ищем маркер //import_add
                        import_add_pos = main_content.find("//import_add")
                        
                        if import_add_pos != -1:
                            # Находим позицию после маркера (учитываем новую строку)
                            insert_pos = import_add_pos + len("//import_add")
                            # Проверяем, есть ли перевод строки после маркера
                            if insert_pos < len(main_content) and main_content[insert_pos] == '\n':
                                # Уже есть перевод строки, просто добавляем импорт
                                main_content = main_content[:insert_pos] + f"\n{import_statement}" + main_content[insert_pos:]
                            else:
                                # Добавляем перевод строки и импорт
                                main_content = main_content[:insert_pos] + f"\n{import_statement}" + main_content[insert_pos:]
                            import_added = True
                            modified = True
                        else:
                            # Ищем последний импорт перед public class
                            class_declaration = f"public class {self.mod_name}JavaMod extends Mod{{"
                            class_pos = main_content.find(class_declaration)
                            
                            if class_pos != -1:
                                # Ищем последний import перед классом
                                last_import_pos = main_content.rfind("import", 0, class_pos)
                                
                                if last_import_pos != -1:
                                    # Находим конец строки этого импорта
                                    line_end = main_content.find("\n", last_import_pos)
                                    if line_end == -1:
                                        line_end = len(main_content)
                                    
                                    # Вставляем новый импорт после последнего импорта
                                    main_content = main_content[:line_end] + f"\n{import_statement}" + main_content[line_end:]
                                    import_added = True
                                    modified = True
                    
                    # Проверяем наличие регистрации ModItems.Load()
                    load_statement = "ModItems.Load();"
                    
                    if load_statement not in main_content:
                        # Ищем маркер //Registration_add
                        registration_add_pos = main_content.find("//Registration_add")
                        
                        if registration_add_pos != -1:
                            # Находим позицию после маркера
                            insert_pos = registration_add_pos + len("//Registration_add")
                            # Проверяем, есть ли перевод строки после маркера
                            if insert_pos < len(main_content) and main_content[insert_pos] == '\n':
                                # Уже есть перевод строки, просто добавляем регистрацию
                                main_content = main_content[:insert_pos] + f"\n        {load_statement}" + main_content[insert_pos:]
                            else:
                                # Добавляем перевод строки и регистрацию
                                main_content = main_content[:insert_pos] + f"\n        {load_statement}" + main_content[insert_pos:]
                            registration_added = True
                            modified = True
                        else:
                            # Ищем метод loadContent()
                            load_content_pos = main_content.find("public void loadContent()")
                            
                            if load_content_pos != -1:
                                # Находим открывающую скобку метода
                                open_brace = main_content.find('{', load_content_pos)
                                
                                if open_brace != -1:
                                    # Находим закрывающую скобку метода
                                    close_brace = main_content.find('}', open_brace)
                                    
                                    if close_brace != -1:
                                        # Ищем позицию перед закрывающей скобкой
                                        # Пропускаем пустые строки и комментарии
                                        insert_pos = close_brace
                                        
                                        # Добавляем перед закрывающей скобкой
                                        indent = "        "  # 8 пробелов
                                        main_content = main_content[:insert_pos] + f"\n{indent}{load_statement}" + main_content[insert_pos:]
                                        registration_added = True
                                        modified = True
                    
                    # Если были изменения, сохраняем главный файл
                    if modified:
                        with open(main_mod_path, 'w', encoding='utf-8') as file:
                            file.write(main_content)
                    
                    # Формируем статус с информацией о добавленных элементах
                    status_messages = [
                        f"✅ Предмет '{var_name}' успешно создан!",
                        f'📋 Имя в игре: "{constructor_name}"',
                        f"🖼️ {icon_status} (имя текстуры: {constructor_name.lower()}.png)",
                        f"🔧 Always Unlocked: {always_unlocked_value}",
                        "📊 Свойства предмета:",
                        f"  • ⚡ Заряд: {charge_value}",
                        f"  • 🔥 Воспламеняемость: {flammability_value}",
                        f"  • 💥 Взрывоопасность: {explosiveness_value}",
                        f"  • ☢️ Радиоактивность: {radioactivity_value}"
                    ]
                    
                    if import_added:
                        status_messages.append("📥 Импорт добавлен в главный файл (через //import_add)")
                    else:
                        status_messages.append("ℹ️ Импорт уже присутствует в главном файле")
                    
                    if registration_added:
                        status_messages.append("📝 Регистрация добавлена в главный файл (через //Registration_add)")
                    else:
                        status_messages.append("ℹ️ Регистрация уже присутствует в главном файле")
                    
                    status_text = "\n".join(status_messages)
                    status_label.configure(text=status_text, text_color="#4CAF50")
                    
                except FileNotFoundError:
                    print(f"Главный файл мода не найден: {main_mod_path}")
                    status_text = f"""✅ Предмет '{var_name}' создан!
    📋 Имя в игре: '{constructor_name}'
    🖼️ {icon_status}
    ⚠️ Главный файл мода не найден: {main_mod_path}
    🔧 Always Unlocked: {always_unlocked_value}
    📊 Свойства предмета:
    • ⚡ Заряд: {charge_value}
    • 🔥 Воспламеняемость: {flammability_value}
    • 💥 Взрывоопасность: {explosiveness_value}
    • ☢️ Радиоактивность: {radioactivity_value}"""
                    status_label.configure(text=status_text, text_color="#FF9800")
                except Exception as e:
                    print(f"Ошибка при работе с главным файлом: {e}")
                    status_text = f"""✅ Предмет '{var_name}' создан!
    📋 Имя в игре: '{constructor_name}'
    🖼️ {icon_status}
    ⚠️ Ошибка при обновлении главного файла: {e}
    🔧 Always Unlocked: {always_unlocked_value}
    📊 Свойства предмета:
    • ⚡ Заряд: {charge_value}
    • 🔥 Воспламеняемость: {flammability_value}
    • 💥 Взрывоопасность: {explosiveness_value}
    • ☢️ Радиоактивность: {radioactivity_value}"""
                    status_label.configure(text=status_text, text_color="#FF9800")
            else:
                status_label.configure(
                    text="⚠️ Предмет уже существует", 
                    text_color="#FF9800"
                )
            
            # Очищаем статус через 5 секунд
            self.root.after(5000, lambda: status_label.configure(text=""))

        def back_to_main():
            """Возврат к основному интерфейсу редактора"""
            self.open_creator()
        
        # Кнопки действий
        buttons_frame = ctk.CTkFrame(button_frame, fg_color="transparent")
        buttons_frame.pack(pady=10)
        
        # Кнопка создания
        create_btn = ctk.CTkButton(
            buttons_frame,
            text="🚀 Создать предмет",
            command=process_item,
            height=45,
            width=200,
            font=("Arial", 16, "bold"),
            fg_color="#2E7D32",
            hover_color="#1B5E20",
            corner_radius=10,
            border_width=2,
            border_color="#1B5E20",
            text_color="#FFFFFF"
        )
        create_btn.pack(side="left", padx=15)
        
        # Кнопка назад
        back_btn = ctk.CTkButton(
            buttons_frame,
            text="← Назад",
            command=back_to_main,
            height=45,
            width=120,
            font=("Arial", 14),
            fg_color="#424242",
            hover_color="#616161",
            corner_radius=10,
            text_color="#FFFFFF"
        )
        back_btn.pack(side="left", padx=15)
        
        # Подсказки внизу
        tips_frame = ctk.CTkFrame(scroll_frame, fg_color="transparent")
        tips_frame.pack(fill="x", pady=(10, 5))
        
        tips_label = ctk.CTkLabel(
            tips_frame,
            text="💡 Формат названий: первое слово с маленькой буквы, остальные с большой (без пробелов). Примеры: 'item', 'bigItem', 'energyCore'",
            font=("Arial", 12),
            text_color="#9E9E9E",  # Серый текст
            wraplength=450
        )
        tips_label.pack()

    def create_liquid(self):
        """Создает или добавляет новую жидкость в ModLiquid.java"""

        PATEH_FOLDER = [
            "consume_generators", "walls",
            "solar_panels", "batterys",
            "beam_nodes", "power_nodes",
            "shield_walls"
        ]
        
        # Очищаем всё окно
        self.clear_window()
        
        # Основной фрейм с прокруткой
        main_frame = ctk.CTkFrame(self.root, fg_color="#2b2b2b")  # Темный фон
        main_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Фрейм для прокрутки
        scroll_frame = ctk.CTkScrollableFrame(
            main_frame,
            width=500,
            height=600,
            fg_color="#2b2b2b"  # Темный фон
        )
        scroll_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Заголовок
        title_frame = ctk.CTkFrame(scroll_frame, fg_color="transparent")
        title_frame.pack(fill="x", pady=(0, 20))
        
        title_label = ctk.CTkLabel(
            title_frame,
            text="Создание жидкости",
            font=("Arial", 24, "bold"),
            text_color="#2196F3"  # Синий цвет для жидкости
        )
        title_label.pack(pady=10)
        
        # Карточка для основной информации
        info_card = ctk.CTkFrame(
            scroll_frame,
            corner_radius=15,
            border_width=2,
            border_color="#404040",  # Темная граница
            fg_color="#363636"  # Серый фон карточки
        )
        info_card.pack(fill="x", pady=(0, 20))
        
        # Заголовок карточки
        card_title = ctk.CTkLabel(
            info_card,
            text="Основная информация",
            font=("Arial", 18, "bold"),
            text_color="#E0E0E0"  # Светло-серый текст
        )
        card_title.pack(pady=(15, 10), padx=20, anchor="w")
        
        # Поле ввода названия
        name_frame = ctk.CTkFrame(info_card, fg_color="transparent")
        name_frame.pack(fill="x", padx=20, pady=(0, 15))
        
        name_label = ctk.CTkLabel(
            name_frame,
            text="Название жидкости (английское, можно пробел, первая буква маленькая):",
            font=("Arial", 16),
            text_color="#BDBDBD"  # Серый текст
        )
        name_label.pack(anchor="w", pady=(0, 5))
        
        entry_name = ctk.CTkEntry(
            name_frame,
            width=400,
            height=40,
            placeholder_text="liquid name",
            font=("Arial", 15),
            border_width=2,
            corner_radius=8,
            fg_color="#424242",  # Темный фон поля ввода
            border_color="#555555",  # Цвет границы
            text_color="#FFFFFF",  # Белый текст
            placeholder_text_color="#888888"  # Серый placeholder
        )
        entry_name.pack(fill="x", pady=(0, 5))
        
        # Функция форматирования названий
        def format_to_lower_camel(text):
            """Преобразует текст в формат: первое слово с маленькой буквы, остальные с большой (без пробелов)
            Примеры:
            'liquid' → 'liquid'
            'cool liquid' → 'coolLiquid'
            'very cool liquid' → 'veryCoolLiquid'
            'energy fluid' → 'energyFluid'
            """
            words = text.strip().split()
            if not words:
                return ""
            
            # Первое слово в нижнем регистре
            result = words[0].lower()
            
            # Остальные слова с заглавной буквы
            for word in words[1:]:
                result += word.capitalize()
            
            return result

        # Функция валидации для обычных значений (0-5000)
        def validate_float_input(value):
            """Проверяет, является ли значение допустимым float с максимум 2 знаками после точки (0-5000)"""
            if value == "" or value == ".":
                return True
            
            # Проверяем формат числа
            pattern = r'^\d*\.?\d{0,2}$'
            if not re.match(pattern, value):
                return False
            
            # Проверяем максимальное значение
            try:
                num = float(value)
                if num > 5000.00:
                    return False
            except ValueError:
                return False
            
            return True

        # Функция валидации для вязкости (0-1)
        def validate_viscosity_input(value):
            """Проверяет, является ли значение допустимым float для вязкости (0-1)"""
            if value == "" or value == ".":
                return True
            
            # Проверяем формат числа
            pattern = r'^\d*\.?\d{0,2}$'
            if not re.match(pattern, value):
                return False
            
            # Проверяем диапазон значения (0-1)
            try:
                num = float(value)
                if num < 0 or num > 1.0:
                    return False
            except ValueError:
                return False
            
            return True

        # Функция форматирования для обычных значений
        def format_float(value):
            """Форматирует значение до 2 знаков после точки"""
            if not value:
                return ""
            
            try:
                num = float(value)
                # Ограничиваем максимальное значение
                num = min(num, 5000.00)
                # Форматируем до 2 знаков
                formatted = f"{num:.2f}"
                # Убираем лишние нули
                if formatted.endswith(".00"):
                    formatted = formatted[:-3]
                elif formatted.endswith(".0"):
                    formatted = formatted[:-2]
                return formatted
            except ValueError:
                return value

        # Функция форматирования для вязкости
        def format_viscosity(value):
            """Форматирует значение вязкости до 2 знаков после точки (0-1)"""
            if not value:
                return "0"  # Вязкость по умолчанию 0
            
            try:
                num = float(value)
                # Ограничиваем диапазон 0-1
                num = max(0.0, min(num, 1.0))
                # Форматируем до 2 знаков
                formatted = f"{num:.2f}"
                # Убираем лишние нули
                if formatted.endswith(".00"):
                    formatted = formatted[:-3]
                elif formatted.endswith("0"):
                    formatted = formatted[:-1]
                return formatted
            except ValueError:
                return "0"

        # Регистрируем функции валидации
        vcmd_float = (self.root.register(validate_float_input), '%P')
        vcmd_viscosity = (self.root.register(validate_viscosity_input), '%P')

        # Карточка для свойств жидкости
        properties_card = ctk.CTkFrame(
            scroll_frame,
            corner_radius=15,
            border_width=2,
            border_color="#404040",  # Темная граница
            fg_color="#363636"  # Серый фон карточки
        )
        properties_card.pack(fill="x", pady=(0, 20))

        # Заголовок карточки свойств
        properties_title = ctk.CTkLabel(
            properties_card,
            text="Свойства жидкости",
            font=("Arial", 18, "bold"),
            text_color="#E0E0E0"  # Светло-серый текст
        )
        properties_title.pack(pady=(15, 10), padx=20, anchor="w")

        # Грид для свойств
        properties_grid = ctk.CTkFrame(properties_card, fg_color="transparent")
        properties_grid.pack(fill="x", padx=20, pady=(0, 15))

        # Метка и поле для воспламеняемости
        flammability_frame = ctk.CTkFrame(properties_grid, fg_color="transparent")
        flammability_frame.grid(row=0, column=0, padx=10, pady=5, sticky="ew")
        
        flammability_label = ctk.CTkLabel(
            flammability_frame,
            text="🔥 Воспламеняемость (flammability):",
            font=("Arial", 15),
            text_color="#BDBDBD"  # Серый текст
        )
        flammability_label.pack(anchor="w", pady=(0, 5))
        
        entry_flammability = ctk.CTkEntry(
            flammability_frame,
            width=180,
            height=38,
            placeholder_text="0.00",
            font=("Arial", 14),
            validate="key",
            validatecommand=vcmd_float,
            fg_color="#424242",  # Темный фон поля ввода
            border_color="#555555",  # Цвет границы
            text_color="#FFFFFF",  # Белый текст
            placeholder_text_color="#888888"  # Серый placeholder
        )
        entry_flammability.pack(fill="x")

        # Метка и поле для взрывоопасности
        explosiveness_frame = ctk.CTkFrame(properties_grid, fg_color="transparent")
        explosiveness_frame.grid(row=0, column=1, padx=10, pady=5, sticky="ew")
        
        explosiveness_label = ctk.CTkLabel(
            explosiveness_frame,
            text="💥 Взрывоопасность (explosiveness):",
            font=("Arial", 15),
            text_color="#BDBDBD"  # Серый текст
        )
        explosiveness_label.pack(anchor="w", pady=(0, 5))
        
        entry_explosiveness = ctk.CTkEntry(
            explosiveness_frame,
            width=180,
            height=38,
            placeholder_text="0.00",
            font=("Arial", 14),
            validate="key",
            validatecommand=vcmd_float,
            fg_color="#424242",  # Темный фон поля ввода
            border_color="#555555",  # Цвет границы
            text_color="#FFFFFF",  # Белый текст
            placeholder_text_color="#888888"  # Серый placeholder
        )
        entry_explosiveness.pack(fill="x")

        # Метка и поле для температуры
        temperature_frame = ctk.CTkFrame(properties_grid, fg_color="transparent")
        temperature_frame.grid(row=1, column=0, padx=10, pady=5, sticky="ew")
        
        temperature_label = ctk.CTkLabel(
            temperature_frame,
            text="🌡️ Температура (temperature):",
            font=("Arial", 15),
            text_color="#BDBDBD"  # Серый текст
        )
        temperature_label.pack(anchor="w", pady=(0, 5))
        
        entry_temperature = ctk.CTkEntry(
            temperature_frame,
            width=180,
            height=38,
            placeholder_text="0.00",
            font=("Arial", 14),
            validate="key",
            validatecommand=vcmd_float,
            fg_color="#424242",  # Темный фон поля ввода
            border_color="#555555",  # Цвет границы
            text_color="#FFFFFF",  # Белый текст
            placeholder_text_color="#888888"  # Серый placeholder
        )
        entry_temperature.pack(fill="x")
        
        # Метка и поле для вязкости (0-1)
        viscosity_frame = ctk.CTkFrame(properties_grid, fg_color="transparent")
        viscosity_frame.grid(row=1, column=1, padx=10, pady=5, sticky="ew")
        
        viscosity_label = ctk.CTkLabel(
            viscosity_frame,
            text="💧 Вязкость (viscosity):",
            font=("Arial", 15),
            text_color="#BDBDBD"  # Серый текст
        )
        viscosity_label.pack(anchor="w", pady=(0, 5))
        
        entry_viscosity = ctk.CTkEntry(
            viscosity_frame,
            width=180,
            height=38,
            placeholder_text="0.00",
            font=("Arial", 14),
            validate="key",
            validatecommand=vcmd_viscosity,
            fg_color="#424242",  # Темный фон поля ввода
            border_color="#555555",  # Цвет границы
            text_color="#FFFFFF",  # Белый текст
            placeholder_text_color="#888888"  # Серый placeholder
        )
        entry_viscosity.pack(fill="x")

        # Привязываем форматирование при потере фокуса
        def on_focus_out_flammability(event):
            value = entry_flammability.get()
            formatted = format_float(value)
            if formatted != value:
                entry_flammability.delete(0, "end")
                entry_flammability.insert(0, formatted)

        entry_flammability.bind("<FocusOut>", on_focus_out_flammability)

        def on_focus_out_explosiveness(event):
            value = entry_explosiveness.get()
            formatted = format_float(value)
            if formatted != value:
                entry_explosiveness.delete(0, "end")
                entry_explosiveness.insert(0, formatted)

        entry_explosiveness.bind("<FocusOut>", on_focus_out_explosiveness)

        def on_focus_out_temperature(event):
            value = entry_temperature.get()
            formatted = format_float(value)
            if formatted != value:
                entry_temperature.delete(0, "end")
                entry_temperature.insert(0, formatted)

        entry_temperature.bind("<FocusOut>", on_focus_out_temperature)
        
        def on_focus_out_viscosity(event):
            value = entry_viscosity.get()
            formatted = format_viscosity(value)
            if formatted != value:
                entry_viscosity.delete(0, "end")
                entry_viscosity.insert(0, formatted)

        entry_viscosity.bind("<FocusOut>", on_focus_out_viscosity)

        # Карточка для дополнительных опций
        options_card = ctk.CTkFrame(
            scroll_frame,
            corner_radius=15,
            border_width=2,
            border_color="#404040",  # Темная граница
            fg_color="#363636"  # Серый фон карточки
        )
        options_card.pack(fill="x", pady=(0, 20))

        # Заголовок карточки опций
        options_title = ctk.CTkLabel(
            options_card,
            text="Дополнительные опции",
            font=("Arial", 18, "bold"),
            text_color="#E0E0E0"  # Светло-серый текст
        )
        options_title.pack(pady=(15, 10), padx=20, anchor="w")

        # Чекбокс для alwaysUnlocked
        always_unlocked_var = ctk.BooleanVar(value=False)
        
        always_unlocked_frame = ctk.CTkFrame(options_card, fg_color="transparent")
        always_unlocked_frame.pack(fill="x", padx=20, pady=(0, 15))
        
        always_unlocked_checkbox = ctk.CTkCheckBox(
            always_unlocked_frame,
            text="🔓 Always Unlocked",
            variable=always_unlocked_var,
            font=("Arial", 15),
            text_color="#BDBDBD",  # Серый текст
            border_width=2,
            corner_radius=6,
            fg_color="#2196F3",  # Синий цвет для жидкости
            hover_color="#1976D2",
            border_color="#555555"  # Цвет границы
        )
        always_unlocked_checkbox.pack(anchor="w", pady=5)
            
        # Метка для статуса
        status_frame = ctk.CTkFrame(scroll_frame, fg_color="transparent")
        status_frame.pack(fill="x", pady=(0, 20))
        
        status_label = ctk.CTkLabel(
            status_frame,
            text="",
            font=("Arial", 14),
            wraplength=450,
            justify="left",
            text_color="#E0E0E0"  # Светло-серый текст
        )
        status_label.pack()
        
        # Фрейм для кнопок
        button_frame = ctk.CTkFrame(scroll_frame, fg_color="transparent")
        button_frame.pack(fill="x", pady=20)
        
        def check_if_name_exists(name):
            """Проверяет, существует ли имя по текстурам в sprites"""
            # Форматируем имя для проверки
            formatted_name = format_to_lower_camel(name)
            
            # Проверяем существование текстуры в разных местах
            name_lower = formatted_name
            
            # Пути для проверки
            check_paths = [
                Path(self.mod_folder) / "assets" / "sprites" / "items" / f"{name_lower}.png",
                Path(self.mod_folder) / "assets" / "sprites" / "liquids" / f"{name_lower}.png",
                Path(self.mod_folder) / "assets" / "sprites" / "blocks" / f"{PATEH_FOLDER}" / f"{name_lower}.png",
                Path(self.mod_folder) / "assets" / "sprites" / "blocks" / f"{PATEH_FOLDER}" / f"{name_lower}" / f"{name_lower}.png",
            ]
            
            for path in check_paths:
                if path.exists():
                    return True
            
            return False
        
        def copy_liquid_icon(liquid_name):
            """
            Копирует иконку из creator/icons/liquids/ 
            в assets/sprites/liquids/ с именем жидкости
            """
            try:
                # Форматируем имя для текстуры
                formatted_name = format_to_lower_camel(liquid_name)
                
                # Путь к папке с иконками
                icons_dir = Path(resource_path("Creator/icons/liquids"))
                
                # Проверяем существование папки
                if not icons_dir.exists():
                    print(f"Папка с иконками не найдена: {icons_dir}")
                    # Создаем папку, если ее нет
                    icons_dir.mkdir(parents=True, exist_ok=True)
                    return False
                
                # Получаем список всех файлов изображений
                image_extensions = ['.png', '.jpg', '.jpeg']
                image_files = []
                
                for ext in image_extensions:
                    image_files.extend(list(icons_dir.glob(f"*{ext}")))
                
                if not image_files:
                    print(f"Нет изображений в папке: {icons_dir}")
                    return False
                
                # Выбираем иконку (water.png или первый доступный)
                icon_path = icons_dir / "water.png"
                if not icon_path.exists():
                    icon_path = image_files[0]  # Берем первую доступную
                
                # Путь назначения в папке мода
                # Используем отформатированное имя в нижнем регистре
                target_name = formatted_name + ".png"
                target_dir = Path(self.mod_folder) / "assets" / "sprites" / "liquids"
                target_dir.mkdir(parents=True, exist_ok=True)
                
                target_path = target_dir / target_name
                
                # Проверяем, не существует ли уже такая текстура
                if target_path.exists():
                    return False  # Не копируем, если уже существует
                
                # Копируем файл
                shutil.copy2(icon_path, target_path)
                
                print(f"Иконка скопирована: {icon_path} -> {target_path}")
                return True
                
            except Exception as e:
                print(f"Ошибка при копировании иконки: {e}")
                return False

        def process_liquid():
            """Обрабатывает создание жидкости"""
            original_name = entry_name.get().strip()
            
            if not original_name:
                status_label.configure(
                    text="❌ Ошибка: Введите имя жидкости!", 
                    text_color="#F44336"  # Красный цвет для ошибки
                )
                return
            
            # Форматируем имя для использования в коде
            constructor_name = format_to_lower_camel(original_name)
            
            if not constructor_name:
                status_label.configure(
                    text="❌ Ошибка: Некорректное название!", 
                    text_color="#F44336"
                )
                return
            
            # Проверка имени по текстурам
            if check_if_name_exists(original_name):
                status_label.configure(
                    text=f"❌ Ошибка: Имя '{constructor_name}' уже используется (текстура существует)!", 
                    text_color="#F44336"
                )
                return
            
            # Копируем иконку
            icon_copied = copy_liquid_icon(original_name)
            icon_status = "✅ Иконка создана" if icon_copied else "⚠️ Иконка не создана"
            
            # Получаем значения свойств
            flammability_value = entry_flammability.get().strip() or "0"
            explosiveness_value = entry_explosiveness.get().strip() or "0"
            temperature_value = entry_temperature.get().strip() or "0"
            viscosity_value = entry_viscosity.get().strip() or "0"  # По умолчанию 0
            
            # Форматируем значения
            flammability_value = format_float(flammability_value)
            explosiveness_value = format_float(explosiveness_value)
            temperature_value = format_float(temperature_value)
            viscosity_value = format_viscosity(viscosity_value)
            
            # Получаем значение alwaysUnlocked
            always_unlocked_value = "true" if always_unlocked_var.get() else "false"

            # Имя переменной (с заглавной буквы - UpperCamelCase)
            if constructor_name and len(constructor_name) > 0:
                var_name = constructor_name[0].lower() + constructor_name[1:] if constructor_name else ""
            else:
                var_name = ""
            
            # Создаем properties строку с правильными значениями
            properties = f"""    flammability = {flammability_value}f;
                explosiveness = {explosiveness_value}f;
                temperature = {temperature_value}f;
                viscosity = {viscosity_value}f;
                alwaysUnlocked = {always_unlocked_value};
                
                localizedName = Core.bundle.get("{var_name}.name", "OH NO");
                description = Core.bundle.get("{var_name}.description", "OH NO");"""
            
            # Путь к файлу ModLiquid.java
            mod_name_lower = self.mod_name.lower() if self.mod_name else self.mod_name
            liquid_registration_path = f"{self.mod_folder}/src/{mod_name_lower}/init/liquids/ModLiquid.java"
            
            # Путь к главному файлу мода
            main_mod_path = f"{self.mod_folder}/src/{mod_name_lower}/{self.mod_name}JavaMod.java"
            
            # Создаем директории, если их нет
            os.makedirs(os.path.dirname(liquid_registration_path), exist_ok=True)
            
            # Читаем или создаем файл ModLiquid.java
            try:
                with open(liquid_registration_path, 'r', encoding='utf-8') as file:
                    content = file.read()
            except FileNotFoundError:
                # Базовый шаблон файла
                content = f"""package {mod_name_lower}.init.liquids;

import arc.graphics.Color;
import mindustry.type.Liquid;
import arc.Core;

public class ModLiquid {{
    public static Liquid;
                                        
    public static void Load() {{
        // Регистрация жидкостей
    }}
}}"""
            
            # Проверяем, есть ли уже эта жидкость
            liquid_exists = False
            if f'new Liquid("{constructor_name}")' in content or f'Liquid {var_name}' in content:
                liquid_exists = True
            
            if not liquid_exists:
                # 1. Добавляем в объявления (public static Liquid)
                if "public static Liquid;" in content:
                    # Заменяем на первое объявление
                    content = content.replace(
                        "public static Liquid;",
                        f"public static Liquid {var_name};"
                    )
                elif "public static Liquid " in content:
                    # Находим строку с объявлениями
                    lines = content.split('\n')
                    for i, line in enumerate(lines):
                        if "public static Liquid " in line and var_name not in line:
                            # Добавляем через запятую
                            lines[i] = line.rstrip(';') + f", {var_name};"
                            content = '\n'.join(lines)
                            break
                
                # 2. Добавляем инициализацию в метод Load()
                # Находим метод Load()
                load_start = content.find("public static void Load() {")
                if load_start != -1:
                    # Находим открывающую скобку метода
                    open_brace = content.find('{', load_start)
                    if open_brace != -1:
                        # Вставляем после открывающей скобки с правильными отступами
                        insert_pos = open_brace + 1
                        indent = "        "  # 8 пробелов
                        
                        # Создаем код жидкости с properties
                        # В кавычках используем отформатированное имя constructor_name
                        liquid_code = f'\n{indent}{var_name} = new Liquid("{constructor_name}"){{{{\n{indent}{properties}\n{indent}}}}};'
                        
                        content = content[:insert_pos] + liquid_code + content[insert_pos:]
                
                # Записываем файл ModLiquid.java
                with open(liquid_registration_path, 'w', encoding='utf-8') as file:
                    file.write(content)
                
                # Теперь работаем с главным файлом мода
                try:
                    with open(main_mod_path, 'r', encoding='utf-8') as file:
                        main_content = file.read()
                    
                    original_main_content = main_content  # Сохраняем оригинал для сравнения
                    modified = False
                    import_added = False
                    registration_added = False
                    
                    # Проверяем наличие импорта ModLiquid
                    import_statement = f"import {mod_name_lower}.init.liquids.ModLiquid;"
                    
                    if import_statement not in main_content:
                        # Ищем маркер //import_add
                        import_add_pos = main_content.find("//import_add")
                        
                        if import_add_pos != -1:
                            # Находим позицию после маркера (учитываем новую строку)
                            insert_pos = import_add_pos + len("//import_add")
                            # Проверяем, есть ли перевод строки после маркера
                            if insert_pos < len(main_content) and main_content[insert_pos] == '\n':
                                # Уже есть перевод строки, просто добавляем импорт
                                main_content = main_content[:insert_pos] + f"\n{import_statement}" + main_content[insert_pos:]
                            else:
                                # Добавляем перевод строки и импорт
                                main_content = main_content[:insert_pos] + f"\n{import_statement}" + main_content[insert_pos:]
                            import_added = True
                            modified = True
                        else:
                            # Ищем последний импорт перед public class
                            class_declaration = f"public class {self.mod_name}JavaMod extends Mod{{"
                            class_pos = main_content.find(class_declaration)
                            
                            if class_pos != -1:
                                # Ищем последний import перед классом
                                last_import_pos = main_content.rfind("import", 0, class_pos)
                                
                                if last_import_pos != -1:
                                    # Находим конец строки этого импорта
                                    line_end = main_content.find("\n", last_import_pos)
                                    if line_end == -1:
                                        line_end = len(main_content)
                                    
                                    # Вставляем новый импорт после последнего импорта
                                    main_content = main_content[:line_end] + f"\n{import_statement}" + main_content[line_end:]
                                    import_added = True
                                    modified = True
                    
                    # Проверяем наличие регистрации ModLiquid.Load()
                    load_statement = "ModLiquid.Load();"
                    
                    if load_statement not in main_content:
                        # Ищем маркер //Registration_add
                        registration_add_pos = main_content.find("//Registration_add")
                        
                        if registration_add_pos != -1:
                            # Находим позицию после маркера
                            insert_pos = registration_add_pos + len("//Registration_add")
                            # Проверяем, есть ли перевод строки после маркера
                            if insert_pos < len(main_content) and main_content[insert_pos] == '\n':
                                # Уже есть перевод строки, просто добавляем регистрацию
                                main_content = main_content[:insert_pos] + f"\n        {load_statement}" + main_content[insert_pos:]
                            else:
                                # Добавляем перевод строки и регистрацию
                                main_content = main_content[:insert_pos] + f"\n        {load_statement}" + main_content[insert_pos:]
                            registration_added = True
                            modified = True
                        else:
                            # Ищем метод loadContent()
                            load_content_pos = main_content.find("public void loadContent()")
                            
                            if load_content_pos != -1:
                                # Находим открывающую скобку метода
                                open_brace = main_content.find('{', load_content_pos)
                                
                                if open_brace != -1:
                                    # Находим закрывающую скобку метода
                                    close_brace = main_content.find('}', open_brace)
                                    
                                    if close_brace != -1:
                                        # Ищем позицию перед закрывающей скобкой
                                        # Пропускаем пустые строки и комментарии
                                        insert_pos = close_brace
                                        
                                        # Добавляем перед закрывающей скобкой
                                        indent = "        "  # 8 пробелов
                                        main_content = main_content[:insert_pos] + f"\n{indent}{load_statement}" + main_content[insert_pos:]
                                        registration_added = True
                                        modified = True
                    
                    # Если были изменения, сохраняем главный файл
                    if modified:
                        with open(main_mod_path, 'w', encoding='utf-8') as file:
                            file.write(main_content)
                    
                    # Формируем статус с информацией о добавленных элементах
                    status_messages = [
                        f"✅ Жидкость '{var_name}' успешно создана!",
                        f'📋 Имя в игре: "{constructor_name}"',
                        f"🖼️ {icon_status} (имя текстуры: {constructor_name.lower()}.png)",
                        f"🔧 Always Unlocked: {always_unlocked_value}",
                        "📊 Свойства жидкости:",
                        f"  • 🔥 Воспламеняемость: {flammability_value}",
                        f"  • 💥 Взрывоопасность: {explosiveness_value}",
                        f"  • 🌡️ Температура: {temperature_value}",
                        f"  • 💧 Вязкость: {viscosity_value}"
                    ]
                    
                    if import_added:
                        status_messages.append("📥 Импорт добавлен в главный файл (через //import_add)")
                    else:
                        status_messages.append("ℹ️ Импорт уже присутствует в главном файле")
                    
                    if registration_added:
                        status_messages.append("📝 Регистрация добавлена в главный файл (через //Registration_add)")
                    else:
                        status_messages.append("ℹ️ Регистрация уже присутствует в главном файле")
                    
                    status_text = "\n".join(status_messages)
                    status_label.configure(text=status_text, text_color="#2196F3")
                    
                except FileNotFoundError:
                    print(f"Главный файл мода не найден: {main_mod_path}")
                    status_text = f"""✅ Жидкость '{var_name}' создана!
    📋 Имя в игре: '{constructor_name}'
    🖼️ {icon_status}
    ⚠️ Главный файл мода не найден: {main_mod_path}
    🔧 Always Unlocked: {always_unlocked_value}
    📊 Свойства жидкости:
    • 🔥 Воспламеняемость: {flammability_value}
    • 💥 Взрывоопасность: {explosiveness_value}
    • 🌡️ Температура: {temperature_value}
    • 💧 Вязкость: {viscosity_value}"""
                    status_label.configure(text=status_text, text_color="#FF9800")
                except Exception as e:
                    print(f"Ошибка при работе с главным файлом: {e}")
                    status_text = f"""✅ Жидкость '{var_name}' создана!
    📋 Имя в игре: '{constructor_name}'
    🖼️ {icon_status}
    ⚠️ Ошибка при обновлении главного файла: {e}
    🔧 Always Unlocked: {always_unlocked_value}
    📊 Свойства жидкости:
    • 🔥 Воспламеняемость: {flammability_value}
    • 💥 Взрывоопасность: {explosiveness_value}
    • 🌡️ Температура: {temperature_value}
    • 💧 Вязкость: {viscosity_value}"""
                    status_label.configure(text=status_text, text_color="#FF9800")
            else:
                status_label.configure(
                    text="⚠️ Жидкость уже существует", 
                    text_color="#FF9800"
                )
            
            # Очищаем статус через 5 секунд
            self.root.after(5000, lambda: status_label.configure(text=""))

        def back_to_main():
            """Возврат к основному интерфейсу редактора"""
            self.open_creator()
        
        # Кнопки действий
        buttons_frame = ctk.CTkFrame(button_frame, fg_color="transparent")
        buttons_frame.pack(pady=10)
        
        # Кнопка создания
        create_btn = ctk.CTkButton(
            buttons_frame,
            text="🚀 Создать жидкость",
            command=process_liquid,
            height=45,
            width=200,
            font=("Arial", 16, "bold"),
            fg_color="#1565C0",
            hover_color="#0D47A1",
            corner_radius=10,
            border_width=2,
            border_color="#0D47A1",
            text_color="#FFFFFF"
        )
        create_btn.pack(side="left", padx=15)
        
        # Кнопка назад
        back_btn = ctk.CTkButton(
            buttons_frame,
            text="← Назад",
            command=back_to_main,
            height=45,
            width=120,
            font=("Arial", 14),
            fg_color="#424242",
            hover_color="#616161",
            corner_radius=10,
            text_color="#FFFFFF"
        )
        back_btn.pack(side="left", padx=15)
        
        # Подсказки внизу
        tips_frame = ctk.CTkFrame(scroll_frame, fg_color="transparent")
        tips_frame.pack(fill="x", pady=(10, 5))
        
        tips_label = ctk.CTkLabel(
            tips_frame,
            text="💡 Формат названий: первое слово с маленькой буквы, остальные с большой (без пробелов). Примеры: 'liquid', 'coolLiquid', 'energyFluid'",
            font=("Arial", 12),
            text_color="#9E9E9E",  # Серый текст
            wraplength=450
        )
        tips_label.pack()

    def choose_mod_icon_tkinter(self):
        """
        Альтернативная версия через tkinter (кросс-платформенная)
        Выбирает файл, копирует в папку мода как mod.png
        """
        try:
            # Создаем временное окно tkinter
            import tkinter as tk
            from tkinter import filedialog
            
            temp_root = tk.Tk()
            temp_root.withdraw()  # Скрываем главное окно
            temp_root.attributes('-topmost', True)  # Поверх других окон
            
            # Открываем диалог выбора файла
            selected_file = filedialog.askopenfilename(
                title="Выберите иконку для мода",
                filetypes=[
                    ("PNG изображения", "*.png"),
                    ("JPEG изображения", "*.jpg *.jpeg"),
                    ("Все файлы", "*.*")
                ]
            )
            
            temp_root.destroy()  # Закрываем временное окно
            
            if selected_file:
                # Проверяем существование файла
                if not os.path.exists(selected_file):
                    messagebox.showerror("Ошибка", f"Файл не найден:\n{selected_file}")
                    return None
                
                # Целевой путь: папка мода + mod.png
                target_path = Path(self.mod_folder) / "assets" / "sprites" / "icon.png"
                
                # Если файл уже существует, спрашиваем подтверждение
                if target_path.exists():
                    response = messagebox.askyesno("Подтверждение",
                        f"Файл {target_path.name} уже существует.\nЗаменить?")
                    if not response:
                        return None
                
                try:
                    # Копируем файл
                    shutil.copy2(selected_file, target_path)
                    
                    messagebox.showinfo("Успех",
                        f"✅ Иконка успешно загружена!\n\n"
                        f"Исходный файл: {os.path.basename(selected_file)}\n"
                        f"Сохранен как: {target_path.name}\n"
                        f"Путь: {target_path}")
                    
                    return str(target_path)
                    
                except Exception as e:
                    messagebox.showerror("Ошибка", f"Не удалось скопировать файл:\n{e}")
                    return None
            
            return None  # Пользователь отменил выбор
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка при выборе файла:\n{e}")
            return None

    def show_blocks_selection(self):
        """Окно выбора типа блока для создания"""
        
        # Очищаем всё окно
        self.clear_window()
        
        # Основной фрейм
        main_frame = ctk.CTkFrame(self.root, fg_color="#2b2b2b")
        main_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Заголовок
        title_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        title_frame.pack(fill="x", pady=(0, 20))
        
        title_label = ctk.CTkLabel(
            title_frame,
            text="🏗️ Создание блока",
            font=("Arial", 26, "bold"),
            text_color="#FF9800"  # Оранжевый цвет для блоков
        )
        title_label.pack(pady=10)
        
        subtitle_label = ctk.CTkLabel(
            title_frame,
            text="Выберите тип блока для создания:",
            font=("Arial", 16),
            text_color="#BDBDBD"
        )
        subtitle_label.pack(pady=5)
        
        def back_to_main():
            """Возврат к основному интерфейсу редактора"""
            self.open_creator()
        
        # Кнопка назад
        back_btn = ctk.CTkButton(
            title_frame,
            text="← Назад в редактор",
            command=back_to_main,  # Возврат к основному редактору
            height=35,
            width=140,
            font=("Arial", 12),
            fg_color="#424242",
            hover_color="#616161",
            corner_radius=8,
            text_color="#FFFFFF"
        )
        back_btn.pack(pady=10)
        
        # Canvas для прокрутки
        canvas_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        canvas_frame.pack(fill="both", expand=True)
        
        # Используем CTkScrollableFrame вместо Canvas
        scroll_frame = ctk.CTkScrollableFrame(canvas_frame, fg_color="#2b2b2b")
        scroll_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Определяем блоки с прямыми вызовами функций
        blocks = [
            ("🧱 Стена", "blocks/copper-wall.png", self.create_wall),
            ("Солнечная панель", "blocks/solar-panel.png", self.create_solar_panel),
            ("Батарея", "blocks/battery.png", self.create_battery),
            ("Генератор", "blocks/steam-generator.png", self.create_consume_generator),
            ("Энергитический башня", "blocks/beam-node.png", self.create_beam_node),
            ("Энергитический узел", "blocks/power-node.png", self.create_power_node),
            ("Экранированую стену", "blocks/shielded-wall.png", self.create_shield_wall),
            ("Завод", "blocks/kiln.png", self.create_generic_crafter),
            ("мост", "blocks/bridge-conveyor.png", self.create_bridge),
            ("конвеер", "blocks/conveyor-0-0.png", self.create_conveyor)
        ]

        blocks_container = ctk.CTkFrame(scroll_frame, fg_color="transparent")
        blocks_container.pack(fill="both", expand=True, pady=10, padx=10)

        def create_block_button(parent, text, icon_name, command):
            """Создает кнопку блока с изображением"""
            btn_frame = ctk.CTkFrame(parent, fg_color="transparent")
            btn_frame.pack_propagate(False)
            btn_frame.configure(width=140, height=160)
            
            # Загружаем изображение
            img = self.load_image(icon_name, size=(80, 80))
            
            # Основная кнопка
            btn = ctk.CTkButton(
                btn_frame,
                text="",  # Без текста
                image=img,
                width=120,
                height=120,
                font=("Arial", 11),
                fg_color="#363636",
                border_color="#404040",
                border_width=2,
                hover_color="#424242",
                corner_radius=12,
                command=command
            )
            btn.pack(pady=(0, 5))
            
            # Сохраняем ссылку на изображение, чтобы не удалилось сборщиком мусора
            if not hasattr(self, 'button_images'):
                self.button_images = []
            self.button_images.append(img)

            # Название блока
            name_label = ctk.CTkLabel(
                btn_frame,
                text=text,
                font=("Arial", 12),
                text_color="#E0E0E0",
                wraplength=130,
                justify="center"
            )
            name_label.pack()
            
            return btn_frame

        # Создаем сетку блоков (4 колонки)
        for i in range(0, len(blocks), 4):
            row_frame = ctk.CTkFrame(blocks_container, fg_color="transparent")
            row_frame.pack(fill="x", pady=10)
            
            row_blocks = blocks[i:i+4]
            for block in row_blocks:
                btn = create_block_button(
                    row_frame,
                    text=block[0],
                    icon_name=block[1],
                    command=block[2]
                )
                btn.pack(side="left", padx=15, expand=True, fill="x")
        
        # Информационная панель внизу
        info_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        info_frame.pack(fill="x", pady=(10, 5))
        
        info_label = ctk.CTkLabel(
            info_frame,
            text=f"💡 Выберите тип блока для создания. Всего доступно {len(blocks)} типов блоков.",
            font=("Arial", 12),
            text_color="#9E9E9E",
            wraplength=500
        )
        info_label.pack()

    def create_bundle_editor(self):
        """Создание редактора bundle файлов"""
        self.clear_window()
        
        # Основной фрейм
        main_frame = ctk.CTkFrame(self.root, fg_color="#2b2b2b")
        main_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Заголовок
        title_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        title_frame.pack(fill="x", pady=(0, 20))
        
        ctk.CTkLabel(
            title_frame,
            text="🌐 Создание Bundle файлов",
            font=("Arial", 24, "bold"),
            text_color="#4CAF50"
        ).pack(pady=10)
        
        ctk.CTkLabel(
            title_frame,
            text="Автоматический поиск предметов и создание локализации",
            font=("Arial", 14),
            text_color="#BDBDBD"
        ).pack()
        
        # === ВКЛАДКИ ===
        tabview = ctk.CTkTabview(main_frame, fg_color="#363636", border_width=2, border_color="#404040")
        tabview.pack(fill="both", expand=True, pady=(0, 20))
        
        # Вкладки
        tabview.add("EN Английский (EN)")
        tabview.add("RU Русский (RU)")
        
        # === ЛОКАЛЬНЫЕ ПЕРЕМЕННЫЕ ДЛЯ ЭТОЙ ФУНКЦИИ ===
        found_items = {}
        en_translations = {}
        ru_translations = {}
        en_descriptions = {}
        ru_descriptions = {}
        en_entries = {}
        ru_entries = {}
        en_desc_entries = {}
        ru_desc_entries = {}
        en_frame = None
        ru_frame = None
        
        # === КОНФИГУРАЦИЯ ПОИСКА - ПРОСТО ТИП, КЛАСС И ПУТЬ ===
        SEARCH_CONFIGS = [
            # Предметы
            {
                "type": "item",
                "class": "Item",
                "path": "src/{mod_name}/init/items/ModItems.java"
            },
            # Жидкости
            {
                "type": "liquid",
                "class": "Liquid",
                "path": "src/{mod_name}/init/liquids/ModLiquid.java"
            },
            # Стены
            {
                "type": "wall",
                "class": "Wall",
                "path": "src/{mod_name}/init/blocks/walls/Walls.java"
            },
            # Солнечные панели
            {
                "type": "solar_panel",
                "class": "SolarGenerator",
                "path": "src/{mod_name}/init/blocks/solar_panels/SolarPanels.java"
            },
            # Батареи
            {
                "type": "battery",
                "class": "Battery",
                "path": "src/{mod_name}/init/blocks/batterys/Batterys.java"
            },
            #генератор
            {
                "type": "consume_generator",
                "class": "ConsumeGenerator",
                "path": "src/{mod_name}/init/blocks/consume_generators/ConsumeGenerators.java"
            },
            #Энерго башня
            {
                "type": "beam_node",
                "class": "BeamNode",
                "path": "src/{mod_name}/init/blocks/beam_nodes/BeamNodes.java"
            },
            #Энерго узел
            {
                "type": "power_node",
                "class": "PowerNode",
                "path": "src/{mod_name}/init/blocks/power_nodes/PowerNodes.java"
            },
            #Стена с шитом
            {
                "type": "shield_wall",
                "class": "ShieldWall",
                "path": "src/{mod_name}/init/blocks/shield_walls/ShieldWalls.java"
            },
            #Завод
            {
                "type": "generic_crafter",
                "class": "GenericCrafter",
                "path": "src/{mod_name}/init/blocks/generic_crafters/GenericCrafters.java"
            },
            #мост
            {
                "type": "circular_bridge",
                "class": "CircularBridge",
                "path": "src/{mod_name}/init/blocks/bridges/Bridges.java"
            },
            {
                "type": "conveyor",
                "class": "Conveyor",
                "path": "src/{mod_name}/init/blocks/conveyors/Conveyors.java"
            }
        ]
        
        # ==== ФУНКЦИЯ АВТОМАТИЧЕСКОГО ПОИСКА ====
        def auto_search():
            """Автоматический поиск всех предметов при открытии"""
            try:
                mod_name_lower = self.mod_name.lower() if self.mod_name else ""
                found_items.clear()
                
                # Проходим по всем конфигам
                for config in SEARCH_CONFIGS:
                    try:
                        # Формируем путь
                        file_path = Path(self.mod_folder) / config["path"].format(mod_name=mod_name_lower)
                        
                        if file_path.exists():
                            with open(file_path, 'r', encoding='utf-8') as f:
                                content = f.read()
                            
                            # Паттерны для поиска переменных
                            patterns = [
                                rf'public\s+static\s+{config["class"]}\s+(\w+);',
                                rf'public\s+static\s+final\s+{config["class"]}\s+(\w+);',
                                rf'(\w+)\s*=\s*new\s+{config["class"]}\("[^"]*"\)',
                                rf'{config["class"]}\s+(\w+)\s*=',
                                rf'public\s+static\s+\w+<{config["class"]}>\s+(\w+);'
                            ]
                            
                            # Ищем совпадения
                            for pattern in patterns:
                                matches = re.findall(pattern, content)
                                for match in matches:
                                    if isinstance(match, str):
                                        # Разбираем множественные объявления через запятую
                                        items = [i.strip() for i in match.split(',')]
                                        for item in items:
                                            if item and item not in found_items:
                                                found_items[item] = {
                                                    "type": config["type"],
                                                    "key": f"{item}.name",
                                                    "class": config["class"]
                                                }
                                                
                    except Exception as e:
                        print(f"⚠️ Ошибка при поиске {config['type']}: {e}")
                        continue
                
                # === ЗАГРУЗКА СУЩЕСТВУЮЩИХ ПЕРЕВОДОВ ===
                load_existing_translations()
                
                # === ДОБАВЛЯЕМ НАЙДЕННЫЕ ЭЛЕМЕНТЫ В ПЕРЕВОДЫ ===
                for item_name, item_info in found_items.items():
                    key = item_info['key']
                    
                    # Добавляем название (только если еще нет)
                    default_name = item_name.replace("_", " ").title()
                    
                    if key not in en_translations:
                        en_translations[key] = default_name
                    if key not in ru_translations:
                        ru_translations[key] = default_name
                    
                    # Добавляем описание
                    desc_key = f"{item_name}.description"
                    if desc_key not in en_descriptions:
                        en_descriptions[desc_key] = ""
                    if desc_key not in ru_descriptions:
                        ru_descriptions[desc_key] = ""
                
                # Обновляем вкладки
                update_translation_tabs()
                
                # Показываем статистику по типам
                type_stats = {}
                for item_info in found_items.values():
                    item_type = item_info['type']
                    type_stats[item_type] = type_stats.get(item_type, 0) + 1
                
                stats_text = f"✅ Найдено {len(found_items)} элементов:\n"
                for t, count in sorted(type_stats.items()):
                    stats_text += f"  • {t}: {count}\n"
                print(stats_text)
                
            except Exception as e:
                print(f"❌ Ошибка автоматического поиска: {e}")
        
        # ==== ФУНКЦИЯ ЗАГРУЗКИ СУЩЕСТВУЮЩИХ ПЕРЕВОДОВ ====
        def load_existing_translations():
            """Загружает существующие переводы из bundle файлов"""
            # Создаем папку bundles если ее нет
            bundles_dir = Path(self.mod_folder) / "assets" / "bundles"
            bundles_dir.mkdir(parents=True, exist_ok=True)
            
            # Загружаем английские переводы
            en_bundle_path = bundles_dir / "bundle.properties"
            if en_bundle_path.exists():
                with open(en_bundle_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#') and '=' in line:
                            key, value = line.split('=', 1)
                            key = key.strip()
                            value = value.strip()
                            
                            if key.endswith('.description'):
                                en_descriptions[key] = value
                            else:
                                en_translations[key] = value
            
            # Загружаем русские переводы
            ru_bundle_path = bundles_dir / "bundle_ru.properties"
            if ru_bundle_path.exists():
                with open(ru_bundle_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#') and '=' in line:
                            key, value = line.split('=', 1)
                            key = key.strip()
                            value = value.strip()
                            
                            if key.endswith('.description'):
                                ru_descriptions[key] = value
                            else:
                                ru_translations[key] = value
            
            # Также проверяем старые пути (для обратной совместимости)
            old_en_path = Path(self.mod_folder) / "assets" / "bundle.properties"
            old_ru_path = Path(self.mod_folder) / "assets" / "bundle_ru.properties"
            
            if old_en_path.exists() and not en_bundle_path.exists():
                with open(old_en_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#') and '=' in line:
                            key, value = line.split('=', 1)
                            key = key.strip()
                            value = value.strip()
                            
                            if key.endswith('.description'):
                                en_descriptions[key] = value
                            else:
                                en_translations[key] = value
            
            if old_ru_path.exists() and not ru_bundle_path.exists():
                with open(old_ru_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#') and '=' in line:
                            key, value = line.split('=', 1)
                            key = key.strip()
                            value = value.strip()
                            
                            if key.endswith('.description'):
                                ru_descriptions[key] = value
                            else:
                                ru_translations[key] = value
        
        # ==== ФУНКЦИИ ДЛЯ ВКЛАДОК ====
        def update_translation_tabs():
            """Обновляет обе вкладки переводов"""
            update_translation_tab("en", en_translations, en_descriptions, en_entries, en_desc_entries, en_frame)
            update_translation_tab("ru", ru_translations, ru_descriptions, ru_entries, ru_desc_entries, ru_frame)
        
        def update_translation_tab(lang_code, translations, descriptions, name_entries, desc_entries, frame):
            """Обновляет конкретную вкладку перевода"""
            if not frame:
                return
            
            # Очищаем фрейм
            for widget in frame.winfo_children():
                widget.destroy()
            
            # Заголовок
            ctk.CTkLabel(
                frame,
                text=f"Переводы ({len(translations)} элементов)",
                font=("Arial", 16, "bold"),
                text_color="#4CAF50"
            ).pack(anchor="w", pady=(0, 10))
            
            ctk.CTkLabel(
                frame,
                text="Формат: itemname.name = Название\n       itemname.description = Описание",
                font=("Arial", 11),
                text_color="#888888"
            ).pack(anchor="w", pady=(0, 20))
            
            # Создаем поля для каждого перевода
            name_entries.clear()
            desc_entries.clear()
            
            for key, name_value in translations.items():
                # Пропускаем ключи .description - они обрабатываются отдельно
                if key.endswith('.description'):
                    continue
                
                # Основной фрейм для элемента
                item_frame = ctk.CTkFrame(frame, fg_color="#3a3a3a", corner_radius=8)
                item_frame.pack(fill="x", pady=5, padx=5)
                
                # Заголовок с ключом
                ctk.CTkLabel(
                    item_frame,
                    text=key,
                    font=("Arial", 10, "bold"),
                    text_color="#4CAF50"
                ).pack(anchor="w", padx=10, pady=(10, 5))
                
                # Название
                name_frame = ctk.CTkFrame(item_frame, fg_color="transparent")
                name_frame.pack(fill="x", padx=10, pady=5)
                
                ctk.CTkLabel(
                    name_frame,
                    text="Название:",
                    font=("Arial", 10),
                    width=80
                ).pack(side="left")
                
                name_var = tk.StringVar(value=name_value)
                name_entry = ctk.CTkEntry(
                    name_frame,
                    textvariable=name_var,
                    font=("Arial", 11),
                    placeholder_text="Введите название..."
                )
                name_entry.pack(side="left", fill="x", expand=True, padx=(5, 0))
                name_entries[key] = name_var
                
                # Описание
                item_base_name = key.replace('.name', '')
                desc_key = f"{item_base_name}.description"
                desc_value = descriptions.get(desc_key, "")
                
                desc_frame = ctk.CTkFrame(item_frame, fg_color="transparent")
                desc_frame.pack(fill="x", padx=10, pady=(0, 10))
                
                ctk.CTkLabel(
                    desc_frame,
                    text="Описание:",
                    font=("Arial", 10),
                    width=80
                ).pack(side="left")
                
                desc_var = tk.StringVar(value=desc_value)
                desc_entry = ctk.CTkEntry(
                    desc_frame,
                    textvariable=desc_var,
                    font=("Arial", 11),
                    placeholder_text="Введите описание..."
                )
                desc_entry.pack(side="left", fill="x", expand=True, padx=(5, 0))
                desc_entries[desc_key] = desc_var
            
            # Если нет переводов
            if not translations:
                ctk.CTkLabel(
                    frame,
                    text="Переводы не найдены. Автоматический поиск уже выполнен.",
                    font=("Arial", 12),
                    text_color="#888888"
                ).pack(pady=50)
        
        # ==== ФУНКЦИЯ СОХРАНЕНИЯ ====
        def collect_translations_from_ui():
            """Собирает переводы из полей ввода UI"""
            # Английский
            for key, name_var in en_entries.items():
                name = name_var.get().strip()
                if name:
                    en_translations[key] = name
            
            for key, desc_var in en_desc_entries.items():
                desc = desc_var.get().strip()
                if desc:
                    en_descriptions[key] = desc
            
            # Русский
            for key, name_var in ru_entries.items():
                name = name_var.get().strip()
                if name:
                    ru_translations[key] = name
            
            for key, desc_var in ru_desc_entries.items():
                desc = desc_var.get().strip()
                if desc:
                    ru_descriptions[key] = desc
        
        def save_all_bundles():
            """Сохраняет все bundle файлы"""
            try:
                # Получаем текущие переводы из полей ввода
                collect_translations_from_ui()
                
                # Создаем папку bundles если нужно
                bundles_dir = Path(self.mod_folder) / "assets" / "bundles"
                bundles_dir.mkdir(parents=True, exist_ok=True)
                
                # === BUNDLE.PROPERTIES (АНГЛИЙСКИЙ) ===
                bundle_path = bundles_dir / "bundle.properties"
                with open(bundle_path, 'w', encoding='utf-8') as f:
                    f.write("# English translations\n")
                    f.write(f"# Generated by Mindustry Mod Creator\n")
                    f.write(f"# {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                    
                    # Сначала названия
                    for key, value in sorted(en_translations.items()):
                        if value:  # Пишем только если есть значение
                            f.write(f"{key}={value}\n")
                    
                    f.write("\n")
                    
                    # Затем описания
                    for key, value in sorted(en_descriptions.items()):
                        if value:  # Пишем только если есть значение
                            f.write(f"{key}={value}\n")
                
                # === BUNDLE_RU.PROPERTIES (РУССКИЙ) ===
                bundle_ru_path = bundles_dir / "bundle_ru.properties"
                with open(bundle_ru_path, 'w', encoding='utf-8') as f:
                    f.write("# Russian translations\n")
                    f.write(f"# Generated by Mindustry Mod Creator\n")
                    f.write(f"# {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                    
                    # Сначала названия
                    for key, value in sorted(ru_translations.items()):
                        if value:  # Пишем только если есть значение
                            f.write(f"{key}={value}\n")
                    
                    f.write("\n")
                    
                    # Затем описания
                    for key, value in sorted(ru_descriptions.items()):
                        if value:  # Пишем только если есть значение
                            f.write(f"{key}={value}\n")
                
                # Показываем сообщение об успехе
                total_en = len([v for v in en_translations.values() if v]) + len([v for v in en_descriptions.values() if v])
                total_ru = len([v for v in ru_translations.values() if v]) + len([v for v in ru_descriptions.values() if v])
                
                messagebox.showinfo(
                    "✅ Успех", 
                    f"Bundle файлы успешно созданы в папке /assets/bundles/\n\n"
                    f"• bundle.properties: {total_en} записей\n"
                    f"• bundle_ru.properties: {total_ru} записей\n\n"
                    f"Пример использования в игре:\n"
                    f"ModItems.redStone = \"redStone.name\""
                )
                
            except Exception as e:
                messagebox.showerror("❌ Ошибка", f"Не удалось сохранить bundle файлы:\n{str(e)}")
        
        # ===== ВКЛАДКА 2: АНГЛИЙСКИЙ =====
        en_tab = tabview.tab("EN Английский (EN)")
        
        # Основной фрейм с прокруткой для английского
        en_main_scroll = ctk.CTkScrollableFrame(en_tab, fg_color="transparent")
        en_main_scroll.pack(fill="both", expand=True)
        
        en_translations_container = ctk.CTkFrame(en_main_scroll, fg_color="transparent")
        en_translations_container.pack(fill="both", expand=True, padx=10, pady=10)
        
        en_frame = ctk.CTkFrame(en_translations_container, fg_color="transparent")
        en_frame.pack(fill="both", expand=True)
        
        # ===== ВКЛАДКА 3: РУССКИЙ =====
        ru_tab = tabview.tab("RU Русский (RU)")
        
        # Основной фрейм с прокруткой для русского
        ru_main_scroll = ctk.CTkScrollableFrame(ru_tab, fg_color="transparent")
        ru_main_scroll.pack(fill="both", expand=True)
        
        ru_translations_container = ctk.CTkFrame(ru_main_scroll, fg_color="transparent")
        ru_translations_container.pack(fill="both", expand=True, padx=10, pady=10)
        
        ru_frame = ctk.CTkFrame(ru_translations_container, fg_color="transparent")
        ru_frame.pack(fill="both", expand=True)
        
        # === КНОПКИ ДЕЙСТВИЙ ===
        button_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        button_frame.pack(fill="x", pady=10)
        
        # Кнопка обновить поиск
        ctk.CTkButton(
            button_frame,
            text="🔄 Обновить поиск",
            command=auto_search,
            height=45,
            width=140,
            font=("Arial", 14),
            fg_color="#2196F3",
            hover_color="#1976D2",
            corner_radius=10
        ).pack(side="left", padx=15)
        
        # Кнопка сохранить
        ctk.CTkButton(
            button_frame,
            text="💾 Сохранить Bundle файлы",
            command=save_all_bundles,
            height=45,
            width=180,
            font=("Arial", 14, "bold"),
            fg_color="#2E7D32",
            hover_color="#1B5E20",
            corner_radius=10
        ).pack(side="left", padx=15)
        
        ctk.CTkButton(
            button_frame,
            text="← Назад",
            command=self.open_creator,
            height=45,
            width=120,
            font=("Arial", 14),
            fg_color="#424242",
            hover_color="#616161",
            corner_radius=10
        ).pack(side="left", padx=15)
        
        # === ЗАПУСКАЕМ АВТОМАТИЧЕСКИЙ ПОИСК ПРИ ОТКРЫТИИ ===
        self.root.after(100, auto_search)

    def setup_actions_panel(self, parent):
        """Настройка панели действий"""
        ctk.CTkLabel(parent, text="Действия", font=("Arial", 14, "bold")).pack(pady=8)
        
        buttons_frame = ctk.CTkFrame(parent, fg_color="transparent")
        buttons_frame.pack(pady=5)

        ctk.CTkButton(
            buttons_frame,
            text="Создать предмет",
            width=180,
            height=35,
            font=("Arial", 12),
            command=self.create_item
        ).pack(pady=4)

        ctk.CTkButton(
            buttons_frame,
            text="Создать жидкость",
            width=180,
            height=35,
            font=("Arial", 12),
            command=self.create_liquid
        ).pack(pady=4)

        ctk.CTkButton(
            buttons_frame,
            text="Создать блок",
            width=180,
            height=35,
            font=("Arial", 12),
            command=self.show_blocks_selection
        ).pack(pady=4)
        
        ctk.CTkButton(
            buttons_frame,
            text="📁 Открыть папку",
            width=180,
            height=35,
            font=("Arial", 12),
            command=self.open_mod_folder
        ).pack(pady=4)

        ctk.CTkButton(
            buttons_frame,
            text="Переводы",
            width=180,
            height=35,
            font=("Arial", 12),
            command=self.create_bundle_editor
        ).pack(pady=4)
        
        ctk.CTkButton(
            buttons_frame,
            text="🔧 Компилировать",
            width=180,
            height=35,
            font=("Arial", 12),
            command=self.compile_mod
        ).pack(pady=4)

        ctk.CTkButton(
            buttons_frame,
            text="Загрузить иконку мода",
            width=180,
            height=35,
            font=("Arial", 12),
            command=self.choose_mod_icon_tkinter
        ).pack(pady=4)
        
        ctk.CTkButton(
            buttons_frame,
            text="← Назад",
            width=180,
            height=35,
            font=("Arial", 12),
            command=self.go_back
        ).pack(pady=16)

    def check_if_name_exists(self, name):
        """Проверяет, существует ли уже такой предмет"""
        name_lower = name.lower()
        mod_name_lower = self.mod_name.lower() if self.mod_name else self.mod_name
        
        # Проверяем в ModItems.java
        items_file_path = Path(self.mod_folder) / "src" / mod_name_lower / "init" / "items" / "ModItems.java"
        if items_file_path.exists():
            try:
                with open(items_file_path, 'r', encoding='utf-8') as file:
                    content = file.read()
                    # Проверяем объявление предмета
                    if f'public static Item {name}' in content or f'Item {name}' in content:
                        return True
                    # Проверяем создание предмета
                    if f'new Item("{name_lower}")' in content:
                        return True
            except:
                pass
        
        # Проверяем в текстурах предметов
        items_texture_path = Path(self.mod_folder) / "assets" / "sprites" / "items"
        if items_texture_path.exists():
            for ext in ['.png', '.jpg', '.jpeg']:
                if (items_texture_path / f"{name_lower}{ext}").exists():
                    return True
        
        return False  # Имя свободно

    def show_context_menu(self, element_name, element_type, x, y, folder_path=None):
        """Показывает контекстное меню для элемента с функциями print и delete"""
        
        # Создаем всплывающее окно
        menu_window = ctk.CTkToplevel(self.root)
        menu_window.title(f"Действия для {element_name}")
        menu_window.geometry("450x450")
        menu_window.resizable(False, False)
        
        # Позиционируем окно рядом с курсором
        menu_window.geometry(f"+{x+10}+{y+10}")
        
        # Делаем окно поверх всех
        menu_window.attributes('-topmost', True)
        menu_window.grab_set()
        
        # Основной фрейм
        main_frame = ctk.CTkFrame(menu_window)
        main_frame.pack(fill="both", expand=True, padx=15, pady=15)
        
        # Заголовок
        ctk.CTkLabel(
            main_frame,
            text=f"Выберите действие для: {element_name}",
            font=("Arial", 14, "bold"),
            text_color="#4CAF50"
        ).pack(pady=(0, 15))
        
        # Информация о типе элемента
        type_text = "📦 Предмет" if element_type == "item" else \
                    "💧 Жидкость" if element_type == "liquid" else \
                    "🧱 Блок"
        
        ctk.CTkLabel(
            main_frame,
            text=type_text,
            font=("Arial", 12),
            text_color="#888888"
        ).pack(pady=(0, 15))
        
        # Разделитель
        ctk.CTkFrame(main_frame, height=2, fg_color="#404040").pack(fill="x", pady=10)
        
        # Фрейм для кнопок действий
        actions_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        actions_frame.pack(fill="both", expand=True)
        
        def format_to_lower_camel(text):
            """Преобразует текст в lowerCamelCase"""
            if not text or not isinstance(text, str):
                return ""
            text = text.replace('-', ' ').replace('_', ' ')
            words = text.strip().split()
            if not words:
                return ""
            result = words[0].lower()
            for word in words[1:]:
                if word:
                    result += word.capitalize()
            return result
        
        # Функция для удаления (вся логика внутри)
        def action_delete():
            """Полное удаление элемента"""
            
            # Подтверждение удаления
            result = messagebox.askyesno(
                "Подтверждение удаления",
                f"Вы уверены, что хотите удалить элемент '{element_name}'?\n\n"
                f"Будут удалены:\n"
                f"• Все текстуры элемента\n"
                f"• Код в Java файлах\n\n"
                f"⚠️ Это действие необратимо!",
                icon='warning'
            )
            
            if not result:
                return
            
            menu_window.destroy()
            
            try:
                import re
                mod_name_lower = self.mod_name.lower() if self.mod_name else self.mod_name
                formatted_name = format_to_lower_camel(element_name)
                deleted_items = []
                errors = []
                warnings = []
                
                # ========== ПРОВЕРКА НАЛИЧИЯ В ДЕРЕВЕ ТЕХНОЛОГИЙ ==========
                if element_type not in ["item", "liquid"]:
                    tree_files = {
                        "wall": "WallsTree",
                        "battery": "BatteryTree",
                        "solar_panel": "SolarTree",
                        "generator": "ConsumeGeneratorTree",
                        "beam_node": "BeamNodeTree",
                        "power_node": "PowerNodeTree",
                        "shield_wall": "ShieldWallTree",
                        "generic_crafter": "GenericCrafterTree",
                        "conveyor": "ConveyorTree",
                        "circular_bridge": "BridgesTree"
                    }
                    
                    if element_type in tree_files:
                        tree_class = tree_files[element_type]
                        tree_file_path = Path(self.mod_folder) / "src" / mod_name_lower / "content" / f"{tree_class}.java"
                        
                        if tree_file_path.exists():
                            with open(tree_file_path, 'r', encoding='utf-8') as f:
                                tree_content = f.read()
                            
                            if formatted_name in tree_content:
                                warnings.append(f"⚠️ Блок найден в дереве технологий ({tree_class}.java)")
                                warnings.append(f"   Рекомендуется сначала удалить его из дерева вручную")
                                
                                result2 = messagebox.askyesno(
                                    "Предупреждение",
                                    f"Элемент '{element_name}' найден в дереве технологий ({tree_class}.java)!\n\n"
                                    f"Если вы продолжите, удаление из дерева может вызвать ошибки.\n\n"
                                    f"Продолжить удаление (только текстуры и Java код)?",
                                    icon='warning'
                                )
                                
                                if not result2:
                                    return
                
                # ========== 1. УДАЛЕНИЕ ТЕКСТУР ==========
                texture_count = 0
                search_paths = []
                
                if element_type == "item":
                    search_paths = [
                        Path(self.mod_folder) / "assets" / "sprites" / "items" / f"{formatted_name}.png",
                        Path(self.mod_folder) / "assets" / "sprites" / "items" / f"{formatted_name}.jpg",
                        Path(self.mod_folder) / "sprites" / "items" / f"{formatted_name}.png",
                    ]
                elif element_type == "liquid":
                    search_paths = [
                        Path(self.mod_folder) / "assets" / "sprites" / "liquids" / f"{formatted_name}.png",
                        Path(self.mod_folder) / "assets" / "sprites" / "liquids" / f"{formatted_name}.jpg",
                        Path(self.mod_folder) / "sprites" / "liquids" / f"{formatted_name}.png",
                    ]
                else:
                    block_folders = {
                        "wall": "walls",
                        "battery": "batterys",
                        "solar_panel": "solar_panels",
                        "generator": "consume_generators",
                        "beam_node": "beam_nodes",
                        "power_node": "power_nodes",
                        "shield_wall": "shield_walls",
                        "generic_crafter": "generic_crafter",
                        "bridge": "bridges",
                        "conveyor": "conveyors",
                        "circular_bridge": "bridges"
                    }
                    target_folder = folder_path or block_folders.get(element_type, "")
                    
                    if target_folder:
                        base_dir = Path(self.mod_folder) / "assets" / "sprites" / "blocks" / target_folder
                        if base_dir.exists():
                            # Для жидкостного моста и моста ищем файлы с разными суффиксами
                            if element_type in ["circular_bridge", "circular_bridge_liquid"]:
                                # Ищем все файлы, начинающиеся с имени блока
                                for file in base_dir.glob(f"{formatted_name}*.*"):
                                    if file.suffix in ['.png', '.jpg', '.jpeg']:
                                        search_paths.append(file)
                                # Проверяем подпапку
                                sub_dir = base_dir / formatted_name
                                if sub_dir.exists():
                                    for file in sub_dir.glob(f"*.*"):
                                        if file.suffix in ['.png', '.jpg', '.jpeg']:
                                            search_paths.append(file)
                            else:
                                # Обычные блоки
                                for file in base_dir.glob(f"{formatted_name}.png"):
                                    if file.suffix in ['.png', '.jpg', '.jpeg']:
                                        search_paths.append(file)
                                sub_dir = base_dir / formatted_name
                                if sub_dir.exists():
                                    for file in sub_dir.glob(f"*.*"):
                                        if file.suffix in ['.png', '.jpg', '.jpeg']:
                                            search_paths.append(file)
                
                for path in search_paths:
                    if path and path.exists():
                        path.unlink()
                        texture_count += 1
                
                for path in search_paths:
                    if path and path.parent.exists() and not any(path.parent.iterdir()):
                        path.parent.rmdir()
                
                if texture_count > 0:
                    deleted_items.append(f"🖼️ Удалено текстур: {texture_count}")
                else:
                    errors.append(f"⚠️ Текстуры не найдены")
                
                # ========== 2. УДАЛЕНИЕ ИЗ JAVA ФАЙЛА ==========
                java_deleted = False
                
                if element_type == "item":
                    items_file_path = Path(self.mod_folder) / "src" / mod_name_lower / "init" / "items" / "ModItems.java"
                    if items_file_path.exists():
                        with open(items_file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                        original = content
                        
                        # Удаляем инициализацию
                        pattern = rf'{formatted_name}\s*=\s*new\s+Item\("[^"]*"\)\s*\{{\s*[^}}]*\s*\}}\s*;'
                        content = re.sub(pattern, '', content, flags=re.DOTALL)
                        
                        # Удаляем из объявления
                        lines = content.split('\n')
                        new_lines = []
                        for line in lines:
                            if 'public static Item' in line and formatted_name in line:
                                if ',' in line:
                                    match = re.search(r'public static Item\s+(.+?);', line)
                                    if match:
                                        vars_str = match.group(1)
                                        var_list = [v.strip() for v in vars_str.split(',')]
                                        remaining_vars = [v for v in var_list if v != formatted_name]
                                        if remaining_vars:
                                            indent = ' ' * (len(line) - len(line.lstrip()))
                                            new_line = f"{indent}public static Item {', '.join(remaining_vars)};"
                                            new_lines.append(new_line)
                            else:
                                new_lines.append(line)
                        content = '\n'.join(new_lines)
                        
                        if content != original:
                            with open(items_file_path, 'w', encoding='utf-8') as f:
                                f.write(content)
                            java_deleted = True
                            
                elif element_type == "liquid":
                    liquids_file_path = Path(self.mod_folder) / "src" / mod_name_lower / "init" / "liquids" / "ModLiquids.java"
                    if not liquids_file_path.exists():
                        liquids_file_path = Path(self.mod_folder) / "src" / mod_name_lower / "init" / "liquids" / "ModLiquid.java"
                    
                    if liquids_file_path.exists():
                        with open(liquids_file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                        original = content
                        
                        pattern = rf'{formatted_name}\s*=\s*new\s+Liquid\("[^"]*"\)\s*\{{\s*[^}}]*\s*\}}\s*;'
                        content = re.sub(pattern, '', content, flags=re.DOTALL)
                        
                        lines = content.split('\n')
                        new_lines = []
                        for line in lines:
                            if 'public static Liquid' in line and formatted_name in line:
                                if ',' in line:
                                    match = re.search(r'public static Liquid\s+(.+?);', line)
                                    if match:
                                        vars_str = match.group(1)
                                        var_list = [v.strip() for v in vars_str.split(',')]
                                        remaining_vars = [v for v in var_list if v != formatted_name]
                                        if remaining_vars:
                                            indent = ' ' * (len(line) - len(line.lstrip()))
                                            new_line = f"{indent}public static Liquid {', '.join(remaining_vars)};"
                                            new_lines.append(new_line)
                            else:
                                new_lines.append(line)
                        content = '\n'.join(new_lines)
                        
                        if content != original:
                            with open(liquids_file_path, 'w', encoding='utf-8') as f:
                                f.write(content)
                            java_deleted = True
                            
                else:
                    # Удаление из файла блоков
                    block_files = {
                        "wall": ("Walls", "walls"),
                        "battery": ("Batterys", "batterys"),
                        "solar_panel": ("SolarPanels", "solar_panels"),
                        "generator": ("ConsumeGenerators", "consume_generators"),
                        "beam_node": ("BeamNodes", "beam_nodes"),
                        "power_node": ("PowerNodes", "power_nodes"),
                        "shield_wall": ("ShieldWalls", "shield_walls"),
                        "generic_crafter": ("GenericCrafters", "generic_crafter"),
                        "bridge": ("Bridges", "bridges"),
                        "conveyor": ("Conveyors", "conveyors"),
                        "circular_bridge": ("Bridges", "bridges")
                    }
                    
                    if element_type in block_files:
                        class_name, folder_name = block_files[element_type]
                        block_file_path = Path(self.mod_folder) / "src" / mod_name_lower / "init" / "blocks" / folder_name / f"{class_name}.java"
                        
                        if block_file_path.exists():
                            with open(block_file_path, 'r', encoding='utf-8') as f:
                                content = f.read()
                            
                            original_content = content
                            
                            # Определяем тип блока
                            block_type_match = re.search(r'public static\s+(\w+)\s+', content)
                            block_type_name = block_type_match.group(1) if block_type_match else "Conveyor"
                            
                            # 1. Удаляем блок инициализации
                            lines = content.split('\n')
                            start_line = -1
                            end_line = -1
                            brace_count = 0
                            in_block = False
                            
                            for i, line in enumerate(lines):
                                if not in_block and re.search(rf'{formatted_name}\s*=\s*new\s+{block_type_name}\s*\(', line):
                                    start_line = i
                                    in_block = True
                                    brace_count = 0
                                
                                if in_block:
                                    brace_count += line.count('{') - line.count('}')
                                    if '};' in line and brace_count == 0:
                                        end_line = i
                                        break
                            
                            if start_line != -1 and end_line != -1:
                                new_lines = lines[:start_line] + lines[end_line + 1:]
                                content = '\n'.join(new_lines)
                            
                            # 2. Удаляем из строки объявления
                            lines = content.split('\n')
                            new_lines = []
                            for line in lines:
                                if re.search(rf'public static\s+{block_type_name}\s+.*{formatted_name}', line):
                                    if ',' in line:
                                        match = re.search(rf'public static\s+{block_type_name}\s+(.+?);', line)
                                        if match:
                                            vars_str = match.group(1)
                                            var_list = [v.strip() for v in vars_str.split(',')]
                                            remaining_vars = [v for v in var_list if v != formatted_name]
                                            if remaining_vars:
                                                indent = ' ' * (len(line) - len(line.lstrip()))
                                                new_line = f"{indent}public static {block_type_name} {', '.join(remaining_vars)};"
                                                new_lines.append(new_line)
                                    else:
                                        continue
                                else:
                                    new_lines.append(line)
                            content = '\n'.join(new_lines)
                            
                            # 3. Очищаем пустые строки
                            lines = content.split('\n')
                            cleaned_lines = []
                            prev_empty = False
                            for line in lines:
                                is_empty = line.strip() == ''
                                if is_empty and prev_empty:
                                    continue
                                cleaned_lines.append(line)
                                prev_empty = is_empty
                            content = '\n'.join(cleaned_lines)
                            
                            # Сохраняем изменения
                            if content != original_content:
                                with open(block_file_path, 'w', encoding='utf-8') as f:
                                    f.write(content)
                                java_deleted = True
                                print(f"Обновлен файл: {block_file_path}")
                
                if java_deleted:
                    deleted_items.append(f"📦 Удален из Java файла")
                else:
                    errors.append(f"⚠️ Не удалось удалить из Java файла")
                
                # ========== 3. РЕЗУЛЬТАТ ==========
                if warnings:
                    messagebox.showwarning("Внимание", "\n".join(warnings))
                
                if errors:
                    status_text = f"⚠️ Удаление элемента '{element_name}' выполнено с ошибками:\n\n"
                    status_text += "✅ Успешно:\n" + "\n".join(deleted_items) + "\n\n❌ Ошибки:\n" + "\n".join(errors)
                    messagebox.showwarning("Предупреждение", status_text)
                else:
                    status_text = f"✅ Элемент '{element_name}' успешно удален!\n\n"
                    status_text += "\n".join(deleted_items)
                    messagebox.showinfo("Успех", status_text)
                
                # Обновляем отображение
                self.open_creator()
                
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось удалить элемент: {str(e)}")

        # Кнопка Delete
        delete_btn = ctk.CTkButton(
            actions_frame,
            text="🗑️ Удалить элемент",
            command=action_delete,
            height=45,
            font=("Arial", 14),
            fg_color="#F44336",
            hover_color="#D32F2F",
            corner_radius=10
        )
        delete_btn.pack(fill="x", pady=8)
        
        # Разделитель
        ctk.CTkFrame(main_frame, height=1, fg_color="#404040").pack(fill="x", pady=10)
        
        # Закрыть
        close_btn = ctk.CTkButton(
            main_frame,
            text="Закрыть",
            command=menu_window.destroy,
            height=35,
            font=("Arial", 12),
            fg_color="#424242",
            hover_color="#616161"
        )
        close_btn.pack(side="bottom", fill="x", pady=(10, 0))
        
        # Привязываем нажатие Escape для закрытия
        def on_escape(event):
            menu_window.destroy()
        
        menu_window.bind("<Escape>", on_escape)

    def on_element_right_click(self, event, element_name, element_type, widget, folder_path=None):
        """Обработчик правого клика по элементу"""
        x = event.x_root
        y = event.y_root
        self.show_context_menu(element_name, element_type, x, y, folder_path)
        return "break"

    def setup_content_panel(self, right_frame):
        """Настройка панели контента - отображение существующего контента с ПКМ меню"""
        scroll_frame = ctk.CTkScrollableFrame(right_frame, fg_color="#2b2b2b")
        scroll_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        mod_name_lower = self.mod_name.lower() if self.mod_name else self.mod_name
        blocks_config = {
            "item": {
                "paths": [f"{self.mod_folder}/src/{mod_name_lower}/init/items/ModItems.java"], 
                "class": "Item", 
                "icon": "📦", 
                "display": "Предмет", 
                "sprite_folder": "items"},
            "liquid": {
                "paths": [f"{self.mod_folder}/src/{mod_name_lower}/init/liquids/ModLiquid.java"], 
                "class": "Liquid", 
                "icon": "💧", 
                "display": "Жидкость", 
                "sprite_folder": "liquids"},
            "wall": {
                "paths": [f"{self.mod_folder}/src/{mod_name_lower}/init/blocks/walls/Walls.java"], 
                "class": "Wall", 
                "icon": "🧱", 
                "display": "Стена", 
                "sprite_folder": "walls"},
            "solar_panel": {
                "paths": [f"{self.mod_folder}/src/{mod_name_lower}/init/blocks/solar_panels/SolarPanels.java"], 
                "class": "SolarGenerator", 
                "icon": "☀️", 
                "display": "Солнечная панель", 
                "sprite_folder": "solar_panels"},
            "batterys": {
                "paths": [f"{self.mod_folder}/src/{mod_name_lower}/init/blocks/batterys/Batterys.java"], 
                "class": "Battery", 
                "icon": "🔋", 
                "display": "Батарея", 
                "sprite_folder": "batterys"},
            "consume_generators": {
                "paths": [f"{self.mod_folder}/src/{mod_name_lower}/init/blocks/consume_generators/ConsumeGenerators.java"], 
                "class": "ConsumeGenerator", 
                "icon": "⚡", 
                "display": "Генератор", 
                "sprite_folder": "consume_generators"},
            "beam_nodes": {
                "paths": [f"{self.mod_folder}/src/{mod_name_lower}/init/blocks/beam_nodes/BeamNodes.java"], 
                "class": "BeamNode", 
                "icon": "📡", 
                "display": "Энергетическая башня", 
                "sprite_folder": "beam_nodes"},
            "power_nodes": {
                "paths": [f"{self.mod_folder}/src/{mod_name_lower}/init/blocks/power_nodes/PowerNodes.java"], 
                "class": "PowerNode", 
                "icon": "🔌", 
                "display": "Энергетический узел", 
                "sprite_folder": "power_nodes"},
            "shield_walls": {
                "paths": [f"{self.mod_folder}/src/{mod_name_lower}/init/blocks/shield_walls/ShieldWalls.java"], 
                "class": "ShieldWall",
                "icon": "🛡️", 
                "display": "Экранированная стена", 
                "sprite_folder": "shield_walls"},
            "generic_crafter": {
                "paths": [f"{self.mod_folder}/src/{mod_name_lower}/init/blocks/generic_crafters/GenericCrafters.java"], 
                "class": "GenericCrafter", 
                "icon": "🏭", 
                "display": "Завод", 
                "sprite_folder": "generic_crafters"},
            "circular_bridge": {
                "paths": [f"{self.mod_folder}/src/{mod_name_lower}/init/blocks/bridges/Bridges.java"], 
                "class": "CircularBridge", 
                "icon": "🌉", 
                "display": "Мост", 
                "sprite_folder": "bridges"},
            "conveyor": {
                "paths": [f"{self.mod_folder}/src/{mod_name_lower}/init/blocks/conveyors/Conveyors.java"],
                "class": "Conveyor",
                "icon": "➡️", 
                "display": "Конвейер", 
                "sprite_folder": "conveyors"}
        }
        
        def search_blocks(block_type, config):
            found_blocks = []
            class_name, sprite_folder = config["class"], config.get("sprite_folder", "blocks")
            patterns = [
                rf'public\s+static\s+{class_name}\s+([^;]+);', 
                rf'{class_name}\s+(\w+)\s*=', 
                rf'(\w+)\s*=\s*new\s+{class_name}\("[^"]+"\)', 
                rf'public\s+static\s+final\s+{class_name}\s+(\w+)']
            
            for path_template in config["paths"]:
                actual_path = path_template.format(mod=self.mod_folder, mod_low=mod_name_lower, name=self.mod_name, name_low=mod_name_lower)
                if not Path(actual_path).exists(): 
                    continue
                
                try:
                    with open(actual_path, 'r', encoding='utf-8') as file:
                        content = file.read()
                        for pattern in patterns:
                            for match in re.findall(pattern, content):
                                for block_name in [b.strip() for b in (match.split(',') if isinstance(match, str) else [match])]:
                                    if block_name and block_name not in [b[1] for b in found_blocks]:
                                        # Определяем пути к спрайтам в зависимости от типа блока
                                        if block_type == "conveyor":
                                            sprite_paths = [
                                                Path(self.mod_folder) / "assets" / "sprites" / "blocks" / sprite_folder / f"{block_name}-0-0.png",
                                                Path(self.mod_folder) / "assets" / "sprites" / "blocks" / sprite_folder / block_name / f"{block_name}-0-0.png",
                                                Path(self.mod_folder) / "assets" / "sprites" / sprite_folder / f"{block_name}-0-0.png"
                                            ]
                                        else:
                                            sprite_paths = [
                                                Path(self.mod_folder) / "assets" / "sprites" / "blocks" / sprite_folder / f"{block_name}.png",
                                                Path(self.mod_folder) / "assets" / "sprites" / "blocks" / sprite_folder / block_name / f"{block_name}.png",
                                                Path(self.mod_folder) / "assets" / "sprites" / sprite_folder / f"{block_name}.png"
                                            ]
                                        
                                        sprite_found = any(p.exists() for p in sprite_paths)
                                        found_blocks.append((block_type, block_name, sprite_found))
                except Exception as e:
                    print(f"Ошибка при чтении файла {actual_path}: {e}")
                    continue
            
            return found_blocks
        
        all_content = [item for block_type, config in blocks_config.items() for item in search_blocks(block_type, config)]
        
        if all_content:
            # Переменная для хранения выбранных типов (по умолчанию все)
            self.selected_types = set(b[0] for b in all_content)
            
            # Верхняя панель с фильтром и кнопкой настроек
            top_panel = ctk.CTkFrame(scroll_frame, fg_color="transparent")
            top_panel.pack(fill="x", pady=(0, 15))
            
            # Фильтр (слева) - ТОЛЬКО КНОПКА НАСТРОЕК
            filter_frame = ctk.CTkFrame(top_panel, fg_color="#363636", corner_radius=8)
            filter_frame.pack(side="left", fill="x", expand=True)
            
            ctk.CTkLabel(filter_frame, text="Фильтр:", font=("Arial", 12, "bold"), width=60).pack(side="left", padx=10)
            
            # Кнопка настроек (вместо всех категорий)
            def show_settings_window():
                parent_window = self.root.winfo_toplevel()
                
                settings_window = ctk.CTkToplevel(parent_window)
                settings_window.title("Настройки отображения")
                settings_window.geometry("500x450")
                settings_window.transient(parent_window)
                settings_window.grab_set()
                
                settings_window.update_idletasks()
                x = (settings_window.winfo_screenwidth() // 2) - (500 // 2)
                y = (settings_window.winfo_screenheight() // 2) - (450 // 2)
                settings_window.geometry(f'+{x}+{y}')
                
                ctk.CTkLabel(settings_window, text="Выберите типы контента для отображения", 
                            font=("Arial", 16, "bold")).pack(pady=15)
                
                checkboxes_frame = ctk.CTkScrollableFrame(settings_window, fg_color="#2b2b2b", 
                                                        corner_radius=10)
                checkboxes_frame.pack(fill="both", expand=True, padx=20, pady=10)
                
                type_vars = {}
                all_types = sorted(set(b[0] for b in all_content))
                
                def apply_settings():
                    selected = [t for t, var in type_vars.items() if var.get()]
                    self.selected_types = set(selected) if selected else set(all_types)
                    update_filter_from_settings()
                    settings_window.destroy()
                
                def cancel_settings():
                    settings_window.destroy()
                
                def select_all():
                    for var in type_vars.values():
                        var.set(True)
                
                def deselect_all():
                    for var in type_vars.values():
                        var.set(False)
                
                cards_per_row = 3
                current_row_frame = None
                
                for i, block_type in enumerate(all_types):
                    if i % cards_per_row == 0:
                        current_row_frame = ctk.CTkFrame(checkboxes_frame, fg_color="transparent")
                        current_row_frame.pack(fill="x", pady=5)
                    
                    card = ctk.CTkFrame(current_row_frame, width=140, height=100, 
                                    fg_color="#363636", corner_radius=10,
                                    border_width=1, border_color="#404040")
                    card.pack_propagate(False)
                    card.pack(side="left", padx=5)
                    
                    config = blocks_config.get(block_type, {})
                    display_name = config.get("display", block_type)
                    icon = config.get("icon", "📦")
                    
                    ctk.CTkLabel(card, text=icon, font=("Arial", 24)).pack(pady=8)
                    ctk.CTkLabel(card, text=display_name, font=("Arial", 11, "bold"), 
                                wraplength=120).pack()
                    
                    count = sum(1 for item in all_content if item[0] == block_type)
                    ctk.CTkLabel(card, text=f"{count} шт.", font=("Arial", 9), 
                                text_color="#AAAAAA").pack()
                    
                    var = tk.BooleanVar(value=block_type in self.selected_types)
                    type_vars[block_type] = var
                    
                    cb = ctk.CTkCheckBox(card, text="", variable=var, width=20,
                                        fg_color="#397E3C", checkbox_width=18, checkbox_height=18)
                    cb.place(relx=0.9, rely=0.1, anchor="center")
                
                btn_frame = ctk.CTkFrame(settings_window, fg_color="transparent")
                btn_frame.pack(fill="x", padx=20, pady=15)
                
                left_btn_frame = ctk.CTkFrame(btn_frame, fg_color="transparent")
                left_btn_frame.pack(side="left")
                
                ctk.CTkButton(left_btn_frame, text="✓ Выбрать все", command=select_all,
                            fg_color="#424242", width=100, height=32).pack(side="left", padx=2)
                ctk.CTkButton(left_btn_frame, text="✗ Сбросить все", command=deselect_all,
                            fg_color="#424242", width=100, height=32).pack(side="left", padx=2)
                
                right_btn_frame = ctk.CTkFrame(btn_frame, fg_color="transparent")
                right_btn_frame.pack(side="right")
                
                ctk.CTkButton(right_btn_frame, text="Применить", command=apply_settings,
                            fg_color="#397E3C", width=100, height=32).pack(side="left", padx=2)
                ctk.CTkButton(right_btn_frame, text="Отмена", command=cancel_settings,
                            fg_color="#AD4038", width=100, height=32).pack(side="left", padx=2)
            
            settings_btn = ctk.CTkButton(filter_frame, text="⚙️ Настройки", width=120, height=32, 
                                        font=("Arial", 12), fg_color="#397E3C",
                                        command=show_settings_window)
            settings_btn.pack(side="left", padx=5)
            
            def update_filter_label():
                if len(self.selected_types) == len(set(b[0] for b in all_content)):
                    filter_label.configure(text="Все категории")
                else:
                    names = [blocks_config.get(t, {}).get("display", t) for t in sorted(self.selected_types)[:3]]
                    text = ", ".join(names)
                    if len(self.selected_types) > 3:
                        text += f" и ещё {len(self.selected_types) - 3}"
                    filter_label.configure(text=text)
            
            filter_label = ctk.CTkLabel(filter_frame, text="Все категории", 
                                    font=("Arial", 11), text_color="#AAAAAA")
            filter_label.pack(side="left", padx=10)
            
            cards_container = ctk.CTkFrame(scroll_frame, fg_color="transparent")
            cards_container.pack(fill="both", expand=True)
            
            def calculate_grid():
                container_width = cards_container.winfo_width()
                if container_width < 10: return 1, 140, 140
                CARD_WIDTH, CARD_HEIGHT, HORIZONTAL_PADDING = 140, 140, 10
                cards_per_row = max(1, (container_width - HORIZONTAL_PADDING) // (CARD_WIDTH + HORIZONTAL_PADDING))
                return cards_per_row, CARD_WIDTH, CARD_HEIGHT
            
            def update_filter_from_settings():
                for widget in cards_container.winfo_children():
                    widget.destroy()
                
                filtered_content = [item for item in all_content if item[0] in self.selected_types]
                
                update_filter_label()
                
                if not filtered_content:
                    ctk.CTkLabel(cards_container, text="🚫 Нет элементов для отображения", 
                                font=("Arial", 14), text_color="#888888").pack(pady=50)
                    return
                
                cards_per_row, CARD_WIDTH, CARD_HEIGHT = calculate_grid()
                current_row_frame = None
                
                for i, (block_type, block_name, has_sprite) in enumerate(filtered_content):
                    if i % cards_per_row == 0:
                        current_row_frame = ctk.CTkFrame(cards_container, fg_color="transparent")
                        current_row_frame.pack(fill="x", pady=5)
                    
                    card = ctk.CTkFrame(current_row_frame, width=CARD_WIDTH, height=CARD_HEIGHT, 
                                    fg_color="#363636", corner_radius=10, 
                                    border_width=1, border_color="#404040")
                    card.pack_propagate(False)
                    card.pack(side="left", padx=5)
                    
                    config = blocks_config.get(block_type, {})
                    default_icon = config.get("icon", "📦")
                    sprite_folder = config.get("sprite_folder", "blocks")
                    
                    if has_sprite:
                        try:
                            from PIL import Image
                            if block_type == "conveyor":
                                sprite_paths = [
                                    Path(self.mod_folder) / "assets" / "sprites" / "blocks" / sprite_folder / f"{block_name}-0-0.png",
                                    Path(self.mod_folder) / "assets" / "sprites" / "blocks" / sprite_folder / block_name / f"{block_name}-0-0.png",
                                    Path(self.mod_folder) / "assets" / "sprites" / sprite_folder / f"{block_name}-0-0.png"
                                ]
                            else:
                                sprite_paths = [
                                    Path(self.mod_folder) / "assets" / "sprites" / "blocks" / sprite_folder / f"{block_name}.png",
                                    Path(self.mod_folder) / "assets" / "sprites" / "blocks" / sprite_folder / block_name / f"{block_name}.png",
                                    Path(self.mod_folder) / "assets" / "sprites" / sprite_folder / f"{block_name}.png"
                                ]
                            
                            found_img = False
                            for sprite_path in sprite_paths:
                                if sprite_path.exists():
                                    try:
                                        img = Image.open(sprite_path).resize((50, 50), Image.Resampling.LANCZOS)
                                        ctk_img = ctk.CTkImage(img)
                                        img_label = ctk.CTkLabel(card, image=ctk_img, text="")
                                        img_label.pack(pady=8)
                                        found_img = True
                                        break
                                    except Exception as img_error:
                                        print(f"Ошибка загрузки изображения {sprite_path}: {img_error}")
                                        continue
                            
                            if not found_img:
                                ctk.CTkLabel(card, text=default_icon, font=("Arial", 24)).pack(pady=8)
                                has_sprite = False
                        
                        except Exception as e:
                            print(f"Ошибка загрузки текстуры для {block_name}: {e}")
                            ctk.CTkLabel(card, text=default_icon, font=("Arial", 24)).pack(pady=8)
                            has_sprite = False
                    else:
                        ctk.CTkLabel(card, text=default_icon, font=("Arial", 24)).pack(pady=8)
                    
                    name_label = ctk.CTkLabel(card, text=block_name, font=("Arial", 11, "bold"), 
                                wraplength=CARD_WIDTH-20)
                    name_label.pack()
                    
                    ctk.CTkLabel(card, text=config.get("display", block_type), 
                                font=("Arial", 9), text_color="#AAAAAA").pack(pady=3)
                    
                    sprite_status = ctk.CTkLabel(card, text="🖼️" if has_sprite else "❌", 
                                font=("Arial", 10), 
                                text_color="#4CAF50" if has_sprite else "#F44336")
                    sprite_status.pack()
                    
                    # Привязываем ПКМ ко всей карточке
                    def make_right_click_handler(name=block_name, type_name=block_type):
                        return lambda event: self.on_element_right_click(event, name, type_name, card)
                    
                    card.bind("<Button-3>", make_right_click_handler())
                    name_label.bind("<Button-3>", make_right_click_handler())
                    sprite_status.bind("<Button-3>", make_right_click_handler())
            
            def on_resize(event):
                if cards_container.winfo_children():
                    update_filter_from_settings()
            
            cards_container.bind("<Configure>", on_resize)
            
            update_filter_from_settings()
        else:
            ctk.CTkLabel(scroll_frame, text="📭 Нет созданного контента", font=("Arial", 16), text_color="#888888").pack(pady=50)
            ctk.CTkLabel(scroll_frame, text="Используйте создатель блоков для добавления контента", font=("Arial", 12), text_color="#666666").pack()

    def open_mod_folder(self):
        """Открытие папки мода в проводнике"""
        try:
            path = str(self.mod_folder)
            if platform.system() == "Windows":
                os.startfile(path)
            elif platform.system() == "Darwin":
                subprocess.run(["open", path])
            else:
                subprocess.run(["xdg-open", path])
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось открыть папку: {e}")

    def go_back(self):
        """Возврат к главному интерфейсу"""
        # Безопасно закрываем окно прогресса, если оно открыто
        self.safe_close_progress_window()
        self.compiling = False
        self.main_app.show_main_ui()

    def clear_window(self):
        """Очистка окна"""
        for widget in self.root.winfo_children():
            widget.destroy()