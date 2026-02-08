import customtkinter as ctk
import tkinter as tk
import os, re
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

class CreatorEditor:
    def __init__(self, root, mod_folder, main_app): 
        self.root = root
        self.mod_folder = mod_folder
        self.main_app = main_app
        self.mod_name = mod_folder.name
        
        # Используем Path для кроссплатформенности
        self.TP_source_folder = Path(mod_folder) / "build" / "libs"
        self.TP_filename = f"{self.mod_name}Desktop.jar"
        self.TP_target_folder = Path("Mods")
        self.TP_new_name = f"{self.mod_name}.jar"
        
        # Флаг для отслеживания состояния компиляции
        self.compiling = False
        
        # Для хранения окна прогресса
        self.progress_window = None
    
        # Инициализация создания блоков
        try:
            from block_creator import create_block_creator
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
                Path("creator/icons") / filename,
                Path("icons") / filename,
                Path(".") / filename,
                Path(__file__).parent.parent / "icons" / filename,
            ]
            
            for path in possible_paths:
                if path.exists():
                    print(f"Загружаю иконку: {path}")
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

    def move_and_rename_file(self):
        """
        Функция для перемещения и переименования файла
        """
        source_path = self.TP_source_folder / self.TP_filename

        print(self.TP_filename)
        
        if not source_path.exists():
            print(f"Файл не найден: {source_path}")
            return False
        
        self.TP_target_folder.mkdir(exist_ok=True)
        target_path = self.TP_target_folder / self.TP_new_name
        
        try:
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
                messagebox.showinfo("Успех", f"Файл перемещен в Mods/{self.TP_new_name}")
            else:
                messagebox.showwarning("Предупреждение", "Не удалось переместить файл. Возможно, он не найден.")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка при перемещении: {e}")

    def compile_mod(self):
        """Запуск компиляции в отдельном потоке"""
        if self.compiling:
            messagebox.showwarning("Внимание", "Компиляция уже выполняется")
            return
        
        self.compiling = True
        
        def sort_registration_lines(file_content):
            """
            Сортирует строки после //Registration_add:
            1. Если оба найдены: ModItems.Load(); и ModLiquid.Load(); - первые две строки
            2. Если найден один: он должен быть первой строкой
            3. Если не найдено: ничего не делать
            """
            lines = file_content.split('\n')
            
            # Находим маркер //Registration_add
            registration_marker_line = -1
            for i, line in enumerate(lines):
                if "//Registration_add" in line:
                    registration_marker_line = i
                    break
            
            if registration_marker_line == -1:
                # Маркер не найден
                print("Маркер //Registration_add не найден")
                return file_content
            
            print(f"Найден маркер //Registration_add на строке {registration_marker_line + 1}")
            
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
                print(f"Блок после маркера пуст (строки {start_line}-{end_line})")
                return file_content
            
            print(f"Найден блок строк {start_line + 1}-{end_line + 1}")
            
            # Собираем все строки в блоке
            block_lines = []
            moditems_line = None
            modliquid_line = None
            other_lines = []
            
            for i in range(start_line, end_line):
                line = lines[i]
                stripped = line.strip()
                
                if stripped:  # Только непустые строки
                    if "ModItems.Load();" in stripped:
                        moditems_line = (i, line)  # Сохраняем позицию и строку
                        print(f"Найден ModItems.Load() на строке {i + 1}")
                    elif "ModLiquid.Load();" in stripped:
                        modliquid_line = (i, line)  # Сохраняем позицию и строку
                        print(f"Найден ModLiquid.Load() на строке {i + 1}")
                    else:
                        other_lines.append((i, line))  # Сохраняем позицию и строку
            
            # Если не найдено ни одного из нужных методов, ничего не делаем
            if moditems_line is None and modliquid_line is None:
                print("Не найдены ModItems.Load() или ModLiquid.Load()")
                return file_content
            
            # Определяем, нужно ли что-то менять
            changes_needed = False
            
            # Проверяем текущие позиции
            if moditems_line:
                moditems_pos, _ = moditems_line
                # Если не первая или вторая строка (при наличии ModLiquid)
                if moditems_pos != start_line and (modliquid_line is None or moditems_pos != start_line + 1):
                    changes_needed = True
            
            if modliquid_line:
                modliquid_pos, _ = modliquid_line
                # Если не первая строка (при отсутствии ModItems) или не вторая (при наличии ModItems)
                if moditems_line:
                    if modliquid_pos != start_line + 1:
                        changes_needed = True
                else:
                    if modliquid_pos != start_line:
                        changes_needed = True
            
            if not changes_needed:
                print("Порядок уже правильный, изменений не требуется")
                return file_content
            
            # Собираем строки в правильном порядке (без учета позиций)
            sorted_lines = []
            
            # Случай 1: Оба найдены
            if moditems_line and modliquid_line:
                _, moditems_str = moditems_line
                _, modliquid_str = modliquid_line
                sorted_lines.append(moditems_str)
                sorted_lines.append(modliquid_str)
                print("Оба метода найдены: ModItems и ModLiquid будут первыми двумя строками")
            
            # Случай 2: Только ModItems
            elif moditems_line and not modliquid_line:
                _, moditems_str = moditems_line
                sorted_lines.append(moditems_str)
                print("Только ModItems найден: будет первой строкой")
            
            # Случай 3: Только ModLiquid
            elif modliquid_line and not moditems_line:
                _, modliquid_str = modliquid_line
                sorted_lines.append(modliquid_str)
                print("Только ModLiquid найден: будет первой строкой")
            
            # Добавляем остальные строки (без ModItems и ModLiquid)
            for pos, line in other_lines:
                sorted_lines.append(line)
            
            # Создаем новый список строк
            new_lines = lines[:start_line] + sorted_lines + lines[end_line:]
            
            print("Строки успешно отсортированы")
            return '\n'.join(new_lines)
        
        def compile_thread():
            try:
                original_cwd = os.getcwd()
                
                # ПЕРЕД ВСЕМ - сортируем строки в главном файле
                mod_name_lower = self.mod_name.lower() if self.mod_name else self.mod_name
                main_mod_path = Path(self.mod_folder) / "src" / mod_name_lower / f"{self.mod_name}JavaMod.java"
                
                print(f"Проверяем файл: {main_mod_path}")
                
                if main_mod_path.exists():
                    try:
                        with open(main_mod_path, 'r', encoding='utf-8') as file:
                            content = file.read()
                        
                        print("Читаем содержимое файла...")
                        
                        # Сортируем строки после //Registration_add
                        sorted_content = sort_registration_lines(content)
                        
                        if sorted_content != content:
                            with open(main_mod_path, 'w', encoding='utf-8') as file:
                                file.write(sorted_content)
                            print("✓ Файл обновлен: строки отсортированы")
                        else:
                            print("✓ Файл уже в правильном порядке")
                        
                    except Exception as e:
                        print(f"✗ Ошибка при обработке файла: {e}")
                else:
                    print(f"✗ Файл не найден: {main_mod_path}")
                
                # ТЕПЕРЬ переходим в папку мода и компилируем
                os.chdir(str(self.mod_folder))
                
                gradle_script = "gradlew.bat" if platform.system() == "Windows" else "./gradlew"
                
                if not Path(gradle_script).exists():
                    # Используем after для UI операций из другого потока
                    self.root.after(0, lambda: messagebox.showerror(
                        "Ошибка", 
                        f"{gradle_script} не найден в папке мода!"
                    ))
                    self.compiling = False
                    os.chdir(original_cwd)
                    return
                
                # Создаем окно прогресса в главном потоке
                self.root.after(0, self.create_progress_window)
                
                # Даем время на создание окна
                time.sleep(0.3)
                
                # Компилируем
                cmd = [gradle_script, "jar"]
                
                print(f"Запуск компиляции: {' '.join(cmd)}")
                
                if platform.system() == "Windows":
                    result = subprocess.run(
                        cmd,
                        capture_output=True,
                        text=True,
                        shell=True,
                        timeout=300
                    )
                else:
                    result = subprocess.run(
                        cmd,
                        capture_output=True,
                        text=True,
                        shell=False,
                        timeout=300
                    )
                
                os.chdir(original_cwd)
                
                # Закрываем окно прогресса в главном потоке
                self.root.after(0, self.safe_close_progress_window)
                
                # Обрабатываем результат
                if result.returncode == 0:
                    jar_files = list(self.mod_folder.glob("build/libs/*.jar"))
                    if jar_files:
                        self.root.after(0, lambda: messagebox.showinfo(
                            "Успех", 
                            f"Мод скомпилирован!\nJAR: {jar_files[0].name}",
                        ))
                        # Запускаем перемещение файла
                        self.root.after(100, self.teleporte)
                    else:
                        self.root.after(0, lambda: messagebox.showinfo(
                            "Успех", 
                            "Компиляция завершена"
                        ))
                else:
                    error_msg = result.stderr[:500] if result.stderr else result.stdout[:500] if result.stdout else "Неизвестная ошибка"
                    self.root.after(0, lambda: messagebox.showerror(
                        "Ошибка", 
                        f"Ошибка компиляции:\n{error_msg}"
                    ))
                time.sleep(3)
                    
            except subprocess.TimeoutExpired:
                self.root.after(0, lambda: messagebox.showerror(
                    "Таймаут", 
                    "Компиляция превысила время ожидания (5 минут)"
                ))
                self.root.after(0, self.safe_close_progress_window)
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror(
                    "Ошибка", 
                    f"Ошибка: {str(e)}"
                ))
                self.root.after(0, self.safe_close_progress_window)
            finally:
                try:
                    os.chdir(os.path.dirname(os.path.abspath(__file__)))
                except:
                    pass
                self.compiling = False
        
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
                icons_dir = Path("creator/icons/items")
                
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
                icon = os.path.join("Creator/icons/items/copper.png")
                
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
                Path(self.mod_folder) / "assets" / "sprites" / "walls" / f"{name_lower}.png",
                Path(self.mod_folder) / "sprites" / "items" / f"{name_lower}.png",
                Path(self.mod_folder) / "sprites" / "liquids" / f"{name_lower}.png",
                Path(self.mod_folder) / "sprites" / "walls" / f"{name_lower}.png",
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
                Path(self.mod_folder) / "assets" / "sprites" / "walls" / f"{name_lower}.png",
                Path(self.mod_folder) / "sprites" / "items" / f"{name_lower}.png",
                Path(self.mod_folder) / "sprites" / "liquids" / f"{name_lower}.png",
                Path(self.mod_folder) / "sprites" / "walls" / f"{name_lower}.png",
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
                icons_dir = Path("creator/icons/liquids")
                
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
                target_path = Path(self.mod_folder) / "assets" / "icon.png"
                
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
            ("Солнечная панель", "blocks/solar-panel.png", self.create_solar_panel)
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
        tabview.add("🇬🇧 Английский (EN)")
        tabview.add("🇷🇺 Русский (RU)")
        
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
        
        # ==== ФУНКЦИЯ АВТОМАТИЧЕСКОГО ПОИСКА ====
        def auto_search():
            """Автоматический поиск всех предметов при открытии"""
            try:
                mod_name_lower = self.mod_name.lower() if self.mod_name else ""
                
                found_items.clear()
                
                # === ПОИСК ПРЕДМЕТОВ ===
                items_path = Path(self.mod_folder) / "src" / mod_name_lower / "init" / "items" / "ModItems.java"
                if items_path.exists():
                    with open(items_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Ищем объявления предметов
                    patterns = [
                        r'public\s+static\s+Item\s+([^;]+);',
                        r'(\w+)\s*=\s*new\s+Item\("[^"]+"\)',
                        r'Item\s+(\w+)\s*='
                    ]
                    
                    for pattern in patterns:
                        matches = re.findall(pattern, content)
                        for match in matches:
                            if isinstance(match, str):
                                items = [i.strip() for i in match.split(',')]
                                for item in items:
                                    if item and item not in found_items:
                                        found_items[item] = {"type": "item", "key": f"{item}.name"}
                
                # === ПОИСК ЖИДКОСТЕЙ ===
                liquids_path = Path(self.mod_folder) / "src" / mod_name_lower / "init" / "liquids" / "ModLiquid.java"
                if liquids_path.exists():
                    with open(liquids_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    patterns = [
                        r'public\s+static\s+Liquid\s+([^;]+);',
                        r'(\w+)\s*=\s*new\s+Liquid\("[^"]+"\)',
                        r'Liquid\s+(\w+)\s*='
                    ]
                    
                    for pattern in patterns:
                        matches = re.findall(pattern, content)
                        for match in matches:
                            if isinstance(match, str):
                                liquids = [l.strip() for l in match.split(',')]
                                for liquid in liquids:
                                    if liquid and liquid not in found_items:
                                        found_items[liquid] = {"type": "liquid", "key": f"{liquid}.name"}
                
                # === ПОИСК СТЕН ===
                walls_path = Path(self.mod_folder) / "src" / mod_name_lower / "init" / "blocks" / "walls" / "Walls.java"
                if walls_path.exists():
                    with open(walls_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    patterns = [
                        r'public\s+static\s+Wall\s+([^;]+);',
                        r'(\w+)\s*=\s*new\s+Wall\("[^"]+"\)',
                        r'Wall\s+(\w+)\s*='
                    ]
                    
                    for pattern in patterns:
                        matches = re.findall(pattern, content)
                        for match in matches:
                            if isinstance(match, str):
                                walls = [w.strip() for w in match.split(',')]
                                for wall in walls:
                                    if wall and wall not in found_items:
                                        found_items[wall] = {"type": "wall", "key": f"{wall}.name"}
                
                # === ПОИСК СОЛНЕЧНЫХ ПАНЕЛЕЙ ===
                solar_path = Path(self.mod_folder) / "src" / mod_name_lower / "init" / "blocks" / "solar_panels" / "SolarPanels.java"
                if solar_path.exists():
                    with open(solar_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    patterns = [
                        r'public\s+static\s+SolarGenerator\s+([^;]+);',
                        r'(\w+)\s*=\s*new\s+SolarGenerator\("[^"]+"\)',
                        r'SolarGenerator\s+(\w+)\s*='
                    ]
                    
                    for pattern in patterns:
                        matches = re.findall(pattern, content)
                        for match in matches:
                            if isinstance(match, str):
                                panels = [p.strip() for p in match.split(',')]
                                for panel in panels:
                                    if panel and panel not in found_items:
                                        found_items[panel] = {"type": "solar_panel", "key": f"{panel}.name"}
                
                # === ЗАГРУЗКА СУЩЕСТВУЮЩИХ ПЕРЕВОДОВ ===
                load_existing_translations()
                
                # === ДОБАВЛЯЕМ НАЙДЕННЫЕ ЭЛЕМЕНТЫ В ПЕРЕВОДЫ ===
                for item_name, item_info in found_items.items():
                    key = item_info['key']  # Пример: "item.name"
                    
                    # Добавляем название (только если еще нет)
                    default_name = item_name.replace("_", " ").title()
                    
                    if key not in en_translations:
                        en_translations[key] = default_name
                    if key not in ru_translations:
                        ru_translations[key] = default_name
                    
                    # Добавляем описание (пустое по умолчанию)
                    # Изменяем формат: вместо item.name.description -> item.description
                    item_base_name = item_name  # Например: "red_stone"
                    desc_key = f"{item_base_name}.description"  # Теперь: "red_stone.description"
                    if desc_key not in en_descriptions:
                        en_descriptions[desc_key] = ""
                    if desc_key not in ru_descriptions:
                        ru_descriptions[desc_key] = ""
                
                # Обновляем вкладки
                update_translation_tabs()
                
                # Показываем статистику
                print(f"✅ Найдено {len(found_items)} элементов для перевода")
                
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
                # Изменяем формат: извлекаем базовое имя из ключа name
                # Пример: из "red_stone.name" получаем "red_stone"
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
        en_tab = tabview.tab("🇬🇧 Английский (EN)")
        
        # Основной фрейм с прокруткой для английского
        en_main_scroll = ctk.CTkScrollableFrame(en_tab, fg_color="transparent")
        en_main_scroll.pack(fill="both", expand=True)
        
        en_translations_container = ctk.CTkFrame(en_main_scroll, fg_color="transparent")
        en_translations_container.pack(fill="both", expand=True, padx=10, pady=10)
        
        en_frame = ctk.CTkFrame(en_translations_container, fg_color="transparent")
        en_frame.pack(fill="both", expand=True)
        
        # ===== ВКЛАДКА 3: РУССКИЙ =====
        ru_tab = tabview.tab("🇷🇺 Русский (RU)")
        
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
        self.root.after(100, auto_search)  # Запускаем через 100мс после создания окна

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

    def setup_content_panel(self, right_frame):
        """Настройка панели контента - отображение существующего контента"""
        # Используем CTkScrollableFrame
        scroll_frame = ctk.CTkScrollableFrame(right_frame, fg_color="#2b2b2b")
        scroll_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Проверяем существование файлов
        mod_name_lower = self.mod_name.lower() if self.mod_name else self.mod_name
        
        # ==== КОНФИГУРАЦИЯ БЛОКОВ ДЛЯ ПОИСКА ====
        # Формат: {тип_блока: {"paths": [список_путей], "class": класс_java, "icon": "🖼️", "display": "Название"}}
        blocks_config = {
            # Стандартные типы
            "item": {
                "paths": [
                    f"{self.mod_folder}/src/{mod_name_lower}/init/items/ModItems.java"
                ],
                "class": "Item",
                "icon": "📦",
                "display": "Предмет",
                "sprite_folder": "items"
            },
            "liquid": {
                "paths": [
                    f"{self.mod_folder}/src/{mod_name_lower}/init/liquids/ModLiquid.java"
                ],
                "class": "Liquid",
                "icon": "💧",
                "display": "Жидкость",
                "sprite_folder": "liquids"
            },
            "wall": {
                "paths": [
                    f"{self.mod_folder}/src/{mod_name_lower}/init/blocks/walls/Walls.java"
                ],
                "class": "Wall",
                "icon": "🧱",
                "display": "Стена",
                "sprite_folder": "walls"
            },
            # Дополнительные блоки (примеры)
            "solar_panel": {
                "paths": [
                    f"{self.mod_folder}/src/{mod_name_lower}/init/blocks/solar_panels/SolarPanels.java"
                ],
                "class": "SolarGenerator",
                "icon": "☀️",
                "display": "Солнечная панель",
                "sprite_folder": "solar_panels"
            }
        }
        
        all_content = []
        
        # ==== УНИВЕРСАЛЬНАЯ ФУНКЦИЯ ПОИСКА ====
        def search_blocks(block_type, config):
            """Поиск блоков по конфигурации"""
            found_blocks = []
            class_name = config["class"]
            sprite_folder = config.get("sprite_folder", "blocks")
            
            # Паттерны для поиска
            patterns = [
                rf'public\s+static\s+{class_name}\s+([^;]+);',
                rf'{class_name}\s+(\w+)\s*=',
                rf'(\w+)\s*=\s*new\s+{class_name}\("[^"]+"\)',
                rf'public\s+static\s+final\s+{class_name}\s+(\w+)'
            ]
            
            # Проверяем все указанные пути
            for path_template in config["paths"]:
                # Заменяем шаблоны в пути
                actual_path = path_template.format(
                    mod=self.mod_folder,
                    mod_low=mod_name_lower,
                    name=self.mod_name,
                    name_low=mod_name_lower
                )
                
                file_path = Path(actual_path)
                if not file_path.exists():
                    continue
                
                try:
                    with open(file_path, 'r', encoding='utf-8') as file:
                        content = file.read()
                    
                    # Ищем все блоки в файле
                    for pattern in patterns:
                        matches = re.findall(pattern, content)
                        for match in matches:
                            if isinstance(match, str):
                                # Обрабатываем несколько блоков через запятую
                                blocks = [b.strip() for b in match.split(',')]
                                for block_name in blocks:
                                    if block_name and block_name not in [b[1] for b in found_blocks]:
                                        # Проверяем наличие спрайта
                                        sprite_found = False
                                        sprite_paths = [
                                            Path(self.mod_folder) / "assets" / "sprites" / sprite_folder / f"{block_name.lower()}.png",
                                            Path(self.mod_folder) / "sprites" / sprite_folder / f"{block_name.lower()}.png",
                                            Path(self.mod_folder) / "assets" / "sprites" / "blocks" / f"{block_name.lower()}.png"
                                        ]
                                        
                                        for sprite_path in sprite_paths:
                                            if sprite_path.exists():
                                                sprite_found = True
                                                break
                                        
                                        found_blocks.append((block_type, block_name, sprite_found))
                                        
                except Exception as e:
                    print(f"Ошибка чтения файла {file_path}: {e}")
                    continue
            
            return found_blocks
        
        # ==== ПОИСК ВСЕХ ТИПОВ БЛОКОВ ====
        for block_type, config in blocks_config.items():
            found = search_blocks(block_type, config)
            all_content.extend(found)
        
        # ==== ОТОБРАЖЕНИЕ ИНТЕРФЕЙСА ====
        if all_content:
            # Заголовок со статистикой
            header_frame = ctk.CTkFrame(scroll_frame, fg_color="transparent")
            header_frame.pack(fill="x", pady=(0, 20))
            
            # Подсчет по типам
            type_counts = {}
            for block_type, _, _ in all_content:
                display_name = blocks_config.get(block_type, {}).get("display", block_type)
                type_counts[display_name] = type_counts.get(display_name, 0) + 1
            
            ctk.CTkLabel(
                header_frame, 
                text=f"📦 Контент мода ({len(all_content)} элементов)", 
                font=("Arial", 18, "bold")
            ).pack(anchor="w")
            
            # Статистика по типам
            stats_text = " | ".join([f"{name}: {count}" for name, count in type_counts.items()])
            ctk.CTkLabel(
                header_frame,
                text=stats_text,
                font=("Arial", 12),
                text_color="#AAAAAA"
            ).pack(anchor="w", pady=(5, 0))
            
            # Фильтр по типам
            filter_frame = ctk.CTkFrame(scroll_frame, fg_color="#363636", corner_radius=8)
            filter_frame.pack(fill="x", pady=(0, 15))
            
            filter_label = ctk.CTkLabel(
                filter_frame,
                text="Фильтр:",
                font=("Arial", 12, "bold"),
                width=60
            )
            filter_label.pack(side="left", padx=10)
            
            # Создаем кнопки фильтра
            filter_buttons = {}
            filter_var = tk.StringVar(value="all")
            
            # Кнопка "Все"
            all_btn = ctk.CTkButton(
                filter_frame,
                text="Все",
                width=60,
                height=25,
                font=("Arial", 10),
                fg_color="#4CAF50" if filter_var.get() == "all" else "#424242",
                command=lambda: filter_var.set("all")
            )
            all_btn.pack(side="left", padx=2)
            filter_buttons["all"] = all_btn
            
            # Кнопки для каждого типа
            for block_type in set(b[0] for b in all_content):
                display_name = blocks_config.get(block_type, {}).get("display", block_type)
                btn = ctk.CTkButton(
                    filter_frame,
                    text=display_name,
                    width=80,
                    height=25,
                    font=("Arial", 10),
                    fg_color="#424242",
                    command=lambda t=block_type: filter_var.set(t)
                )
                btn.pack(side="left", padx=2)
                filter_buttons[block_type] = btn
            
            # ==== КАРТОЧКИ БЛОКОВ ====
            cards_container = ctk.CTkFrame(scroll_frame, fg_color="transparent")
            cards_container.pack(fill="both", expand=True)
            
            # Параметры карточек
            CARD_WIDTH = 140
            CARD_HEIGHT = 140
            CARDS_PER_ROW = 5
            
            # Функция обновления фильтра
            def update_filter(*args):
                selected_filter = filter_var.get()
                
                # Обновляем цвет кнопок
                for btn_type, btn in filter_buttons.items():
                    btn.configure(fg_color="#4CAF50" if btn_type == selected_filter else "#424242")
                
                # Обновляем отображение карточек
                for widget in cards_container.winfo_children():
                    widget.destroy()
                
                # Фильтруем контент
                filtered_content = all_content if selected_filter == "all" else [
                    item for item in all_content if item[0] == selected_filter
                ]
                
                if not filtered_content:
                    empty_label = ctk.CTkLabel(
                        cards_container,
                        text="🚫 Нет элементов для отображения",
                        font=("Arial", 14),
                        text_color="#888888"
                    )
                    empty_label.pack(pady=50)
                    return
                
                # Создаем сетку карточек
                row_frame = None
                for i, (block_type, block_name, has_sprite) in enumerate(filtered_content):
                    if i % CARDS_PER_ROW == 0:
                        row_frame = ctk.CTkFrame(cards_container, fg_color="transparent")
                        row_frame.pack(fill="x", pady=5)
                    
                    # Создаем карточку
                    card = ctk.CTkFrame(
                        row_frame,
                        width=CARD_WIDTH,
                        height=CARD_HEIGHT,
                        fg_color="#363636",
                        corner_radius=10,
                        border_width=1,
                        border_color="#404040"
                    )
                    card.pack_propagate(False)
                    card.pack(side="left", padx=5)
                    
                    # Иконка
                    config = blocks_config.get(block_type, {})
                    default_icon = config.get("icon", "📦")
                    sprite_folder = config.get("sprite_folder", "blocks")
                    
                    if has_sprite:
                        try:
                            from PIL import Image
                            sprite_paths = [
                                Path(self.mod_folder) / "assets" / "sprites" / sprite_folder / f"{block_name.lower()}.png",
                                Path(self.mod_folder) / "sprites" / sprite_folder / f"{block_name.lower()}.png"
                            ]
                            
                            for sprite_path in sprite_paths:
                                if sprite_path.exists():
                                    img = Image.open(sprite_path)
                                    img = img.resize((50, 50), Image.Resampling.LANCZOS)
                                    ctk_img = ctk.CTkImage(img)
                                    
                                    icon_label = ctk.CTkLabel(card, image=ctk_img, text="")
                                    icon_label.image = ctk_img
                                    icon_label.pack(pady=8)
                                    break
                            else:
                                raise FileNotFoundError
                        except:
                            icon_label = ctk.CTkLabel(card, text=default_icon, font=("Arial", 24))
                            icon_label.pack(pady=8)
                    else:
                        icon_label = ctk.CTkLabel(card, text=default_icon, font=("Arial", 24))
                        icon_label.pack(pady=8)
                    
                    # Название блока
                    name_label = ctk.CTkLabel(
                        card,
                        text=block_name,
                        font=("Arial", 11, "bold"),
                        wraplength=CARD_WIDTH-20
                    )
                    name_label.pack()
                    
                    # Тип блока
                    type_label = ctk.CTkLabel(
                        card,
                        text=config.get("display", block_type),
                        font=("Arial", 9),
                        text_color="#AAAAAA"
                    )
                    type_label.pack(pady=3)
                    
                    # Индикатор спрайта
                    sprite_indicator = "🖼️" if has_sprite else "❌"
                    sprite_label = ctk.CTkLabel(
                        card,
                        text=sprite_indicator,
                        font=("Arial", 10),
                        text_color="#4CAF50" if has_sprite else "#F44336"
                    )
                    sprite_label.pack()
            
            # Инициализируем отображение
            filter_var.trace_add("write", update_filter)
            update_filter()
            
        else:
            # Если контента нет
            empty_frame = ctk.CTkFrame(scroll_frame, fg_color="transparent")
            empty_frame.pack(fill="both", expand=True)
            
            ctk.CTkLabel(
                empty_frame,
                text="📭 Нет созданного контента",
                font=("Arial", 16),
                text_color="#888888"
            ).pack(pady=50)
            
            ctk.CTkLabel(
                empty_frame,
                text="Используйте создатель блоков для добавления контента",
                font=("Arial", 12),
                text_color="#666666"
            ).pack()

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