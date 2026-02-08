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
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from tkinter import messagebox
import sys
import re
import winreg  # Для работы с реестром Windows

class MainWindow:
    def __init__(self):
        self.root = ctk.CTk()
        self.root.title("Mindustry Java Mod Creator")
        self.root.geometry("900x670")
        
        self.java_installed = False
        self.java_is_jdk17 = False
        self.java_path = None
        self.java_version = None
        
        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("blue")
        
        Path("Creator/mods").mkdir(parents=True, exist_ok=True)
        
        # Проверяем Java при запуске
        self.check_java_status()
        
        # Загружаем иконки в фоне после создания окна
        self.root.after(100, self.load_all_icons_background)
        
        self.show_main_ui()

    def load_all_icons_background(self):
        """Загружает иконки в фоновом режиме"""
        def load_in_thread():
            try:
                # Загружаем иконки без отображения прогресса (None передается как parent_window)
                self.load_all_icons(None)
                print("Иконки успешно загружены")
            except Exception as e:
                print(f"Ошибка при загрузке иконок: {e}")
        
        thread = threading.Thread(target=load_in_thread, daemon=True)
        thread.start()

    def load_all_icons(self, parent_window=None):
        icons_dir = os.path.join("Creator", "icons")
        
        # Создаем основные папки для иконок
        items_dir = os.path.join(icons_dir, "items")
        liquids_dir = os.path.join(icons_dir, "liquids")
        blocks_dir = os.path.join(icons_dir, "blocks")
        
        os.makedirs(items_dir, exist_ok=True)
        os.makedirs(liquids_dir, exist_ok=True)
        os.makedirs(blocks_dir, exist_ok=True)
        
        # Проверяем, есть ли уже иконки в соответствующих папках
        items_exist = os.path.exists(items_dir) and len(os.listdir(items_dir)) > 0
        liquids_exist = os.path.exists(liquids_dir) and len(os.listdir(liquids_dir)) > 0
        blocks_exist = os.path.exists(blocks_dir) and len(os.listdir(blocks_dir)) > 0
        
        # Если все иконки уже загружены
        if items_exist and liquids_exist and blocks_exist:
            # ПРОВЕРКА НА ВСЕ ИМЕНА: проверяем наличие всех требуемых файлов
            print("Проверка наличия всех иконок...")
            
            # Список всех ожидаемых имен
            expected_items = ["copper", "lead", "metaglass", "graphite", "sand", "coal",
                            "titanium", "thorium", "scrap", "silicon", "plastanium",
                            "phase-fabric", "surge-alloy", "spore-pod", "blast-compound", "pyratite"]
            expected_liquids = ["water", "oil", "slag", "cryofluid"]
            expected_blocks = ["copper-wall", "copper-wall-large", "titanium-wall", "titanium-wall-large",
                            "thorium-wall", "thorium-wall-large", "surge-wall", "surge-wall-large",
                            "reinforced-surge-wall", "reinforced-surge-wall-large", "plastanium-wall",
                            "plastanium-wall-large", "phase-wall", "phase-wall-large", "solar-panel",
                            "solar-panel-large"]
            
            missing_items = []
            missing_liquids = []
            missing_blocks = []
            
            # Проверяем предметы
            for item in expected_items:
                item_path = os.path.join(items_dir, f"{item}.png")
                if not os.path.exists(item_path):
                    missing_items.append(item)
            
            # Проверяем жидкости
            for liquid in expected_liquids:
                liquid_path = os.path.join(liquids_dir, f"{liquid}.png")
                if not os.path.exists(liquid_path):
                    missing_liquids.append(liquid)
            
            # Проверяем блоки
            for block in expected_blocks:
                block_path = os.path.join(blocks_dir, f"{block}.png")
                if not os.path.exists(block_path):
                    missing_blocks.append(block)
            
            # Если все файлы на месте
            if not missing_items and not missing_liquids and not missing_blocks:
                print("Все иконки уже загружены и проверены")
                return True
            else:
                print(f"Найдены отсутствующие файлы:")
                if missing_items:
                    print(f"  Предметы ({len(missing_items)}): {', '.join(missing_items)}")
                if missing_liquids:
                    print(f"  Жидкости ({len(missing_liquids)}): {', '.join(missing_liquids)}")
                if missing_blocks:
                    print(f"  Блоки ({len(missing_blocks)}): {', '.join(missing_blocks)}")
        
        # Конфигурация загрузки
        download_configs = [
            (
                "https://raw.githubusercontent.com/Anuken/Mindustry/master/core/assets-raw/sprites/items/",
                ["copper", "lead", "metaglass", "graphite", "sand", "coal",
                "titanium", "thorium", "scrap", "silicon", "plastanium",
                "phase-fabric", "surge-alloy", "spore-pod", "blast-compound", "pyratite"],
                "items",
                True
            ),
            (
                "https://raw.githubusercontent.com/Anuken/Mindustry/master/core/assets-raw/sprites/items/",
                ["water", "oil", "slag", "cryofluid"],
                "liquids",
                True
            ),
            (
                "https://raw.githubusercontent.com/Anuken/Mindustry/master/core/assets-raw/sprites/blocks/",
                {
                    # Примеры с двумя слоями - слой 2 накладывается поверх слоя 1
                    "copper-wall": {"layers": [["walls/copper-wall.png", 1]]},
                    "copper-wall-large": {"layers": [["walls/copper-wall-large.png", 1]]},
                    "titanium-wall":{"layers": [["walls/titanium-wall.png", 1]]},
                    "titanium-wall-large":{"layers": [["walls/titanium-wall-large.png", 1]]},
                    "thorium-wall":{"layers": [["walls/thorium-wall.png", 1]]},
                    "thorium-wall-large":{"layers": [["walls/thorium-wall-large.png", 1]]},
                    "surge-wall":{"layers": [["walls/surge-wall.png", 1]]},
                    "surge-wall-large":{"layers": [["walls/surge-wall-large.png", 1]]},
                    "reinforced-surge-wall":{"layers": [["walls/reinforced-surge-wall.png", 1]]},
                    "reinforced-surge-wall-large":{"layers": [["walls/reinforced-surge-wall-large.png", 1]]},
                    "plastanium-wall":{"layers": [["walls/plastanium-wall.png", 1]]},
                    "plastanium-wall-large":{"layers": [["walls/plastanium-wall-large.png", 1]]},
                    "phase-wall": {"layers": [["walls/phase-wall.png", 1]]},
                    "phase-wall-large": {"layers": [["walls/phase-wall-large.png", 1]]},

                    "solar-panel": {"layers": [["power/solar-panel.png", 1]]},
                    "solar-panel-large": {"layers": [["power/solar-panel-large.png", 1]]}
                },
                "blocks",   
                False
            )
        ]

        # Подсчет общего количества иконок
        total_icons = 0
        download_tasks = []
        multi_layer_tasks = []  # Для задач с несколькими слоями
        
        # Списки для отслеживания всех ожидаемых имен
        all_expected_items = []
        all_expected_liquids = []
        all_expected_blocks = []
        
        for base_url, name_icons, dest_folder, is_item in download_configs:
            dest_dir = os.path.join(icons_dir, dest_folder)
            
            if isinstance(name_icons, dict):
                # Для сложных структур с слоями (блоки)
                for name, config in name_icons.items():
                    # Добавляем в список ожидаемых блоков
                    all_expected_blocks.append(name)
                    
                    final_path = os.path.join(dest_dir, f"{name}.png")
                    
                    # Пропускаем если файл уже существует
                    if os.path.exists(final_path):
                        # ПРОВЕРКА НА ВСЕ ИМЕНА: проверяем что файл не пустой
                        if os.path.getsize(final_path) > 0:
                            continue
                        else:
                            print(f"Файл {name} пустой, перезагружаем...")
                    
                    layers = config.get("layers", [])
                    num_layers = len(layers)
                    
                    if num_layers == 1:
                        # Если 1 слой - просто скачиваем
                        layer_path, layer_num = layers[0]
                        total_icons += 1
                        download_tasks.append({
                            "url": base_url + layer_path,
                            "save_path": final_path,
                            "name": name,
                            "dest_folder": dest_folder,
                            "type": "simple",
                            "layer_num": layer_num
                        })
                    elif num_layers >= 2:
                        # Если 2 или больше слоев - добавляем в отдельный список
                        layer_files = []
                        for i, (layer_path, layer_num) in enumerate(layers):
                            temp_filename = f"{name}_temp_layer_{layer_num}.png"
                            temp_path = os.path.join(dest_dir, temp_filename)
                            total_icons += 1
                            
                            # Сначала скачиваем все временные файлы
                            download_tasks.append({
                                "url": base_url + layer_path,
                                "save_path": temp_path,
                                "name": f"{name}_layer{layer_num}",
                                "dest_folder": dest_folder,
                                "type": "multi_layer_part",
                                "layer_num": layer_num,
                                "block_name": name,
                                "final_path": final_path
                            })
                            
                            layer_files.append((temp_path, layer_num))
                        
                        # Затем добавляем задачу на объединение
                        multi_layer_tasks.append({
                            "name": name,
                            "layer_files": layer_files,
                            "final_path": final_path,
                            "dest_folder": dest_folder,
                            "num_layers": num_layers
                        })
            else:
                # Простые элементы (предметы и жидкости)
                for name in name_icons:
                    # Добавляем в соответствующий список
                    if dest_folder == "items":
                        all_expected_items.append(name)
                    elif dest_folder == "liquids":
                        all_expected_liquids.append(name)
                    
                    final_path = os.path.join(dest_dir, f"{name}.png")
                    
                    # Пропускаем если файл уже существует
                    if os.path.exists(final_path):
                        # ПРОВЕРКА НА ВСЕ ИМЕНА: проверяем что файл не пустой
                        if os.path.getsize(final_path) > 0:
                            continue
                        else:
                            print(f"Файл {name} пустой, перезагружаем...")
                    
                    # Формируем URL в зависимости от типа
                    if dest_folder == "liquids":
                        filename = f"liquid-{name}.png"
                        final_url = base_url + filename
                    elif is_item:
                        filename = f"item-{name}.png"
                        final_url = base_url + filename
                    else:
                        filename = f"{name}.png"
                        final_url = base_url + filename
                    
                    total_icons += 1
                    download_tasks.append({
                        "url": final_url,
                        "save_path": final_path,
                        "name": name,
                        "dest_folder": dest_folder,
                        "type": "simple",
                        "layer_num": 1
                    })

        if total_icons == 0:
            # ПРОВЕРКА НА ВСЕ ИМЕНА: финальная проверка после загрузки
            print("Проверяем наличие всех файлов после загрузки...")
            success = self.verify_all_icons_exist(items_dir, liquids_dir, blocks_dir, 
                                                all_expected_items, all_expected_liquids, all_expected_blocks)
            return success

        # Инициализация окна прогресса
        if parent_window:
            progress_window = ctk.CTkToplevel(parent_window)
            progress_window.title("Загрузка иконок")
            progress_window.geometry("400x150")
            progress_window.transient(parent_window)
            progress_window.grab_set()
            
            progress_label = ctk.CTkLabel(progress_window, text=f"Загрузка иконок...")
            progress_label.pack(pady=10)
            
            progress_bar = ctk.CTkProgressBar(progress_window, width=300)
            progress_bar.pack(pady=10)
            progress_bar.set(0)
            
            status_label = ctk.CTkLabel(progress_window, text="Подготовка...")
            status_label.pack(pady=5)
            
            progress_window.update()

        downloaded = 0
        errors = []
        
        def update_progress(current, total, name, folder, stage="download"):
            if parent_window:
                progress = (current + 1) / total
                progress_bar.set(progress)
                if stage == "download":
                    status_label.configure(text=f"{current + 1}/{total} - {name} ({folder})")
                    progress_label.configure(text=f"Загружается: {name}")
                elif stage == "combine":
                    status_label.configure(text=f"Объединение: {name}")
                    progress_label.configure(text=f"Создание иконки: {name}")
                progress_window.update()
        
        def download_file(task):
            try:
                # Создаем папку, если она не существует
                os.makedirs(os.path.dirname(task["save_path"]), exist_ok=True)
                
                response = requests.get(task["url"], stream=True, timeout=30)
                if response.status_code == 200:
                    with open(task["save_path"], 'wb') as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            f.write(chunk)
                    
                    # ПРОВЕРКА НА ВСЕ ИМЕНА: проверяем что файл загрузился
                    if os.path.exists(task["save_path"]) and os.path.getsize(task["save_path"]) > 0:
                        return True, task
                    else:
                        return False, (task, "Файл не загружен или пустой")
                else:
                    return False, (task, f"HTTP {response.status_code}")
            except Exception as e:
                return False, (task, str(e))
        
        def combine_layers(task):
            """Объединяет слои для многослойных иконок"""
            try:
                from PIL import Image
                
                layer_files = task["layer_files"]
                final_path = task["final_path"]
                num_layers = task["num_layers"]
                
                if num_layers == 2:
                    # Для 2 слоев: слой 2 накладывается поверх слоя 1 и делается на 1 меньше
                    layer1_path, layer1_num = layer_files[0]
                    layer2_path, layer2_num = layer_files[1]
                    
                    # Проверяем что оба файла существуют
                    if not os.path.exists(layer1_path) or not os.path.exists(layer2_path):
                        return False, (task, "Один из слоев отсутствует")
                    
                    # Открываем оба изображения
                    layer1 = Image.open(layer1_path).convert("RGBA")
                    layer2 = Image.open(layer2_path).convert("RGBA")
                    
                    # Получаем размеры
                    width1, height1 = layer1.size
                    width2, height2 = layer2.size
                    
                    # Если второй слой такого же размера, уменьшаем его на 1 пиксель с каждой стороны
                    if width1 == width2 and height1 == height2 and width1 > 2 and height1 > 2:
                        # Создаем уменьшенную версию второго слоя
                        new_size = (width1 - 2, height1 - 2)
                        layer2_resized = layer2.resize(new_size, Image.Resampling.LANCZOS)
                        
                        # Создаем новое изображение с прозрачным фоном
                        result = Image.new("RGBA", (width1, height1), (0, 0, 0, 0))
                        
                        # Накладываем первый слой
                        result.paste(layer1, (0, 0))
                        
                        # Накладываем уменьшенный второй слой по центру
                        paste_x = (width1 - new_size[0]) // 2
                        paste_y = (height1 - new_size[1]) // 2
                        result.paste(layer2_resized, (paste_x, paste_y), layer2_resized)
                    else:
                        # Если размеры разные, просто накладываем как есть
                        result = Image.new("RGBA", (width1, height1), (0, 0, 0, 0))
                        result.paste(layer1, (0, 0))
                        result.paste(layer2, (0, 0), layer2)
                    
                    # Сохраняем результат
                    result.save(final_path, "PNG")
                    
                    # ПРОВЕРКА НА ВСЕ ИМЕНА: проверяем что файл создан
                    if not os.path.exists(final_path) or os.path.getsize(final_path) == 0:
                        return False, (task, "Итоговый файл не создан")
                    
                    # Удаляем временные файлы
                    if os.path.exists(layer1_path):
                        os.remove(layer1_path)
                    if os.path.exists(layer2_path):
                        os.remove(layer2_path)
                    
                else:
                    # Для большего количества слоев - накладываем последовательно
                    result = None
                    for temp_path, layer_num in layer_files:
                        if not os.path.exists(temp_path):
                            return False, (task, f"Слой {layer_num} отсутствует")
                        
                        layer_img = Image.open(temp_path).convert("RGBA")
                        
                        if result is None:
                            result = layer_img
                        else:
                            result.paste(layer_img, (0, 0), layer_img)
                        
                        # Удаляем временный файл
                        if os.path.exists(temp_path):
                            os.remove(temp_path)
                    
                    result.save(final_path, "PNG")
                
                return True, task
            except Exception as e:
                return False, (task, str(e))

        try:
            # Шаг 1: Загружаем все файлы
            if parent_window:
                progress_label.configure(text="Загрузка файлов...")
                status_label.configure(text=f"0/{total_icons}")
            
            with ThreadPoolExecutor(max_workers=4) as executor:
                futures = {}
                for task in download_tasks:
                    future = executor.submit(download_file, task)
                    futures[future] = task
                
                for future in as_completed(futures):
                    task = futures[future]
                    success, result = future.result()
                    
                    if success:
                        downloaded += 1
                        if parent_window:
                            update_progress(downloaded, total_icons, task["name"], task["dest_folder"], "download")
                    else:
                        if isinstance(result, tuple):
                            failed_task, error = result
                            errors.append((failed_task["name"], failed_task["dest_folder"], error))
                        else:
                            errors.append((task["name"], task["dest_folder"], "Unknown error"))
                        downloaded += 1
                        if parent_window:
                            progress_label.configure(text=f"Ошибка: {task['name']}")
            
            # Шаг 2: Объединяем многослойные иконки
            if multi_layer_tasks:
                if parent_window:
                    progress_label.configure(text="Объединение слоев...")
                    status_label.configure(text=f"0/{len(multi_layer_tasks)}")
                    progress_bar.set(0)
                
                combined = 0
                total_combine = len(multi_layer_tasks)
                
                with ThreadPoolExecutor(max_workers=2) as executor:
                    combine_futures = {}
                    for task in multi_layer_tasks:
                        future = executor.submit(combine_layers, task)
                        combine_futures[future] = task
                    
                    for future in as_completed(combine_futures):
                        task = combine_futures[future]
                        success, result = future.result()
                        
                        if success:
                            combined += 1
                            if parent_window:
                                update_progress(combined, total_combine, task["name"], task["dest_folder"], "combine")
                        else:
                            failed_task, error = result
                            errors.append((failed_task["name"], failed_task["dest_folder"], f"Combine error: {error}"))
                            if parent_window:
                                progress_label.configure(text=f"Ошибка объединения: {task['name']}")

            # ПРОВЕРКА НА ВСЕ ИМЕНА: финальная проверка после загрузки
            print("Финальная проверка всех загруженных иконок...")
            success = self.verify_all_icons_exist(items_dir, liquids_dir, blocks_dir, 
                                                all_expected_items, all_expected_liquids, all_expected_blocks)
            
            if not success:
                errors.append(("Финальная проверка", "Все файлы", "Не все файлы загружены"))
            
            # Вывод ошибок, если они есть
            if errors:
                error_msg = "\n".join(f"{name} ({folder}): {error}" for name, folder, error in errors)
                print(f"Ошибки загрузки:\n{error_msg}")
                if parent_window:
                    messagebox.showwarning("Ошибки загрузки", f"Не удалось загрузить некоторые иконки:\n{error_msg}")

            if parent_window:
                progress_label.configure(text="Загрузка завершена!")
                progress_window.after(2000, progress_window.destroy())
            
            print(f"Иконки успешно загружены в папки:")
            print(f"- Items: {items_dir}")
            print(f"- Liquids: {liquids_dir}")
            print(f"- Blocks: {blocks_dir}")
            
            return success
        
        except Exception as e:
            error_msg = f"Критическая ошибка: {str(e)}"
            print(error_msg)
            import traceback
            traceback.print_exc()
            
            if parent_window:
                if 'progress_label' in locals():
                    progress_label.configure(text=error_msg)
                messagebox.showerror("Ошибка", error_msg)
            return False

    def verify_all_icons_exist(self, items_dir, liquids_dir, blocks_dir, expected_items, expected_liquids, expected_blocks):
        """
        Проверяет наличие всех ожидаемых файлов
        """
        missing_items = []
        missing_liquids = []
        missing_blocks = []
        
        # Проверяем предметы
        for item in expected_items:
            item_path = os.path.join(items_dir, f"{item}.png")
            if not os.path.exists(item_path) or os.path.getsize(item_path) == 0:
                missing_items.append(item)
        
        # Проверяем жидкости
        for liquid in expected_liquids:
            liquid_path = os.path.join(liquids_dir, f"{liquid}.png")
            if not os.path.exists(liquid_path) or os.path.getsize(liquid_path) == 0:
                missing_liquids.append(liquid)
        
        # Проверяем блоки
        for block in expected_blocks:
            block_path = os.path.join(blocks_dir, f"{block}.png")
            if not os.path.exists(block_path) or os.path.getsize(block_path) == 0:
                missing_blocks.append(block)
        
        if missing_items or missing_liquids or missing_blocks:
            print("Обнаружены отсутствующие или пустые файлы:")
            if missing_items:
                print(f"  Предметы ({len(missing_items)}): {', '.join(missing_items)}")
            if missing_liquids:
                print(f"  Жидкости ({len(missing_liquids)}): {', '.join(missing_liquids)}")
            if missing_blocks:
                print(f"  Блоки ({len(missing_blocks)}): {', '.join(missing_blocks)}")
            return False
        
        print(f"Все иконки проверены успешно:")
        print(f"  Предметы: {len(expected_items)} файлов")
        print(f"  Жидкости: {len(expected_liquids)} файлов")
        print(f"  Блоки: {len(expected_blocks)} файлов")
        return True

    def check_java_status(self):
        """Проверяет статус Java через JAVA_HOME"""
        try:
            # Проверяем JAVA_HOME в переменных окружения пользователя
            java_home = self.get_user_java_home()
            
            if java_home:
                java_exe = Path(java_home) / "bin" / "java.exe"
                if java_exe.exists():
                    self.java_path = java_home
                    self.java_version = self.get_java_version(java_exe)
                    self.java_installed = True
                    
                    # Проверяем это JDK 17
                    if self.java_version and (self.java_version.startswith("17") or "17." in self.java_version):
                        if "jdk-17" in java_home.lower() or "jdk17" in java_home.lower():
                            self.java_is_jdk17 = True
                    print(f"Java найдена: {java_home}, версия: {self.java_version}")
            else:
                print("JAVA_HOME не установлен")
                
        except Exception as e:
            print(f"Ошибка при проверке Java: {e}")

    def get_user_java_home(self):
        """Получает JAVA_HOME из реестра пользователя"""
        try:
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                "Environment",
                0,
                winreg.KEY_READ
            )
            
            try:
                java_home, _ = winreg.QueryValueEx(key, "JAVA_HOME")
                winreg.CloseKey(key)
                return java_home
            except WindowsError:
                winreg.CloseKey(key)
                return None
                
        except Exception as e:
            print(f"Ошибка при чтении реестра: {e}")
            return None

    def get_java_version(self, java_exe):
        """Получает версию Java"""
        try:
            result = subprocess.run([str(java_exe), "-version"], capture_output=True, text=True, shell=True)
            if result.returncode == 0:
                return self.parse_java_version(result.stderr)
        except:
            pass
        return None

    def parse_java_version(self, version_output):
        """Парсит вывод java -version"""
        try:
            lines = version_output.split('\n')
            for line in lines:
                if 'version' in line.lower():
                    # Ищем номер версии
                    match = re.search(r'"(\d+(?:\.\d+)*)', line)
                    return match.group(1)
                    # Альтернативный формат
                    match = re.search(r'(\d+(?:\.\d+)*)', line)
                    if match:
                        return match.group(1)
        except:
            pass
        return "Unknown"

    def set_jdk17_as_primary(self):
        """Устанавливает JDK 17 как основную Java через JAVA_HOME"""
        # Сначала проверяем есть ли JDK 17 в системе
        jdk17_path = self.find_jdk17_in_system()
        
        if not jdk17_path:
            # Если нет - скачиваем и устанавливаем
            self.download_and_install_jdk17()
            return
        
        try:
            # Устанавливаем JAVA_HOME в реестре пользователя
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                "Environment",
                0,
                winreg.KEY_SET_VALUE | winreg.KEY_READ
            )
            
            # Устанавливаем JAVA_HOME
            winreg.SetValueEx(key, "JAVA_HOME", 0, winreg.REG_SZ, jdk17_path)
            
            # Обновляем переменную в текущем процессе
            os.environ["JAVA_HOME"] = jdk17_path
            
            # Добавляем bin в PATH если нужно
            bin_path = f"{jdk17_path}\\bin"
            try:
                current_path, path_type = winreg.QueryValueEx(key, "Path")
                path_str = current_path
                
                if bin_path not in path_str:
                    new_path = f"{bin_path};{path_str}" if path_str else bin_path
                    winreg.SetValueEx(key, "Path", 0, path_type, new_path)
                    os.environ["PATH"] = f"{bin_path};{os.environ['PATH']}"
            except WindowsError:
                # PATH может не существовать
                winreg.SetValueEx(key, "Path", 0, winreg.REG_SZ, bin_path)
                os.environ["PATH"] = bin_path
            
            winreg.CloseKey(key)
            
            # Обновляем системные переменные
            self.broadcast_environment_change()
            
            # Обновляем информацию о Java
            self.java_path = jdk17_path
            self.java_version = self.get_java_version(Path(jdk17_path) / "bin" / "java.exe")
            self.java_is_jdk17 = True
            
            messagebox.showinfo(
                "Успех",
                f"JDK 17 установлена как основная!\n\n"
                f"Перезапустите программу для применения изменений."
            )
            
            # Обновляем UI
            self.show_main_ui()
            
            return True
            
        except Exception as e:
            print(f"Ошибка при работе с реестром: {e}")
            messagebox.showerror("Ошибка", f"Не удалось изменить реестр: {e}")
            return False

    def find_jdk17_in_system(self):
        """Ищет JDK 17 в системе"""
        # Проверяем стандартные пути
        search_paths = [
            "C:\\Program Files\\Java\\jdk-17",
            "C:\\Program Files (x86)\\Java\\jdk-17",
            os.environ.get('ProgramFiles', 'C:\\Program Files') + "\\Java\\jdk-17",
        ]
        
        for path in search_paths:
            java_exe = Path(path) / "bin" / "java.exe"
            if java_exe.exists():
                version = self.get_java_version(java_exe)
                if version and (version.startswith("17") or "17." in version):
                    return path
        
        return None

    def download_and_install_jdk17(self):
        """Скачивает и устанавливает JDK 17"""
        self.show_java_download_ui()
        
        def download_thread():
            try:
                self.root.after(0, lambda: self.update_progress(0.1, "Подготовка к установке..."))
                
                # Определяем путь для установки
                program_files = os.environ.get('ProgramFiles', 'C:\\Program Files')
                install_path = Path(program_files) / "Java"
                install_path.mkdir(parents=True, exist_ok=True)
                
                # URL для скачивания JDK 17
                jdk_url = "https://github.com/adoptium/temurin17-binaries/releases/download/jdk-17.0.12%2B7/OpenJDK17U-jdk_x64_windows_hotspot_17.0.12_7.zip"
                
                self.root.after(0, lambda: self.update_progress(0.2, "Скачивание JDK 17..."))
                
                # Скачиваем файл
                response = requests.get(jdk_url, stream=True, timeout=60)
                response.raise_for_status()
                
                # Получаем размер файла
                total_size = int(response.headers.get('content-length', 0))
                downloaded = 0
                
                # Временный файл
                temp_zip = install_path / "jdk_temp.zip"
                
                # Сохраняем файл
                with open(temp_zip, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)
                            if total_size > 0:
                                progress = 0.2 + (downloaded / total_size * 0.6)
                                self.root.after(0, lambda: self.update_progress(progress, 
                                    f"Скачивание: {downloaded/1024/1024:.1f}MB / {total_size/1024/1024:.1f}MB"))
                
                self.root.after(0, lambda: self.update_progress(0.8, "Распаковка JDK..."))
                
                # Распаковываем архив
                with zipfile.ZipFile(temp_zip, 'r') as zip_ref:
                    # Находим корневую папку
                    first_file = zip_ref.namelist()[0]
                    root_folder = first_file.split('/')[0]
                    
                    # Путь для установки
                    jdk17_path = install_path / "jdk-17"
                    
                    # Удаляем старую установку если есть
                    if jdk17_path.exists():
                        shutil.rmtree(jdk17_path)
                    
                    # Извлекаем файлы
                    for file_info in zip_ref.infolist():
                        filename = file_info.filename
                        
                        if filename.startswith(root_folder + '/'):
                            rel_path = filename[len(root_folder) + 1:]
                            
                            if not rel_path or rel_path.endswith('/'):
                                continue
                            
                            target_path = jdk17_path / rel_path
                            target_path.parent.mkdir(parents=True, exist_ok=True)
                            
                            with zip_ref.open(file_info) as source_file:
                                content = source_file.read()
                                with open(target_path, 'wb') as target_file:
                                    target_file.write(content)
                
                # Удаляем временный файл
                temp_zip.unlink()
                
                self.root.after(0, lambda: self.update_progress(0.9, "Настройка окружения..."))
                
                # Проверяем установку
                java_exe = jdk17_path / "bin" / "java.exe"
                if java_exe.exists():
                    self.root.after(0, lambda: self.update_progress(1.0, "Установка завершена!"))
                    
                    # Устанавливаем как основную
                    self.root.after(100, lambda: self.set_jdk17_as_primary())
                    
                else:
                    self.root.after(0, lambda: self.show_java_error("JDK не установилась корректно"))
                    self.root.after(3000, self.show_main_ui)
                
            except Exception as e:
                print(f"Ошибка при скачивании Java: {e}")
                import traceback
                traceback.print_exc()
                self.root.after(0, lambda: self.show_java_error(f"Ошибка: {str(e)[:100]}"))
                self.root.after(3000, self.show_main_ui)
        
        thread = threading.Thread(target=download_thread, daemon=True)
        thread.start()

    def broadcast_environment_change(self):
        """Уведомляет систему об изменении переменных окружения"""
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

    def show_java_download_ui(self):
        """Показывает UI для скачивания Java"""
        self.clear_window()
        
        ctk.CTkLabel(self.root, text="Установка Java JDK 17", font=("Arial", 20, "bold")).pack(pady=50)
        ctk.CTkLabel(self.root, text="Java JDK 17 не найдена. Устанавливаю...", 
                    font=("Arial", 16)).pack(pady=20)
        ctk.CTkLabel(self.root, text="Пожалуйста, подождите", 
                    font=("Arial", 14)).pack(pady=10)
        
        self.progress_bar = ctk.CTkProgressBar(self.root, width=400)
        self.progress_bar.pack(pady=20)
        self.progress_bar.set(0)
        
        self.status_label = ctk.CTkLabel(self.root, text="Подготовка...", font=("Arial", 12))
        self.status_label.pack(pady=10)

    def update_progress(self, value, status):
        """Обновляет прогресс скачивания"""
        self.progress_bar.set(value)
        self.status_label.configure(text=status)

    def show_java_error(self, message):
        """Показывает сообщение об ошибке"""
        self.update_progress(0, message)

    def show_main_ui(self):
        self.clear_window()
        
        # Только список модов слева
        left_frame = ctk.CTkFrame(self.root, width=300)
        left_frame.pack(side="left", fill="y", padx=5, pady=5)
        
        # Центральная часть
        center_frame = ctk.CTkFrame(self.root)
        center_frame.pack(side="right", fill="both", expand=True, padx=5, pady=5)
        
        self.setup_mods_list(left_frame)
        
        # Показываем соответствующий интерфейс
        if self.java_is_jdk17:
            # Если JDK 17 установлена - показываем создание мода
            self.setup_create_mod_panel(center_frame)
        else:
            # Если нет JDK 17 - показываем установку
            self.setup_install_java_panel(center_frame)

    def setup_create_mod_panel(self, parent):
        """Панель для создания мода"""
        ctk.CTkLabel(parent, text="Mindustry Java Mod Creator", font=("Arial", 20, "bold")).pack(pady=30)
        
        form_frame = ctk.CTkFrame(parent, fg_color="transparent")
        form_frame.pack(pady=30)
        
        ctk.CTkLabel(form_frame, text="Имя папки мода:", font=("Arial", 14)).pack(pady=3)
        
        self.mod_name_entry = ctk.CTkEntry(form_frame, width=280, height=35, font=("Arial", 13))
        self.mod_name_entry.pack(pady=8)
        
        ctk.CTkButton(
            form_frame,
            text="Создать",
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
        
        ctk.CTkLabel(parent, text="Требуется JDK 17", font=("Arial", 16)).pack(pady=10)
        
        info_frame = ctk.CTkFrame(parent, fg_color="transparent")
        info_frame.pack(pady=20)
        
        ctk.CTkLabel(info_frame, text="Для создания модов требуется установить JDK 17.", 
                    font=("Arial", 12)).pack(pady=5)
        
        ctk.CTkButton(
            parent,
            text="Установить JDK 17",
            width=250,
            height=50,
            font=("Arial", 15, "bold"),
            command=self.set_jdk17_as_primary,
            fg_color="green",
            hover_color="dark green"
        ).pack(pady=30)

    def setup_mods_list(self, parent):
        ctk.CTkLabel(parent, text="Созданные моды", font=("Arial", 16, "bold")).pack(pady=10)
        
        scroll_frame = ctk.CTkScrollableFrame(parent, height=500)
        scroll_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        mods_dir = Path("Creator/mods")
        mods = []
        
        if mods_dir.exists():
            for item in mods_dir.iterdir():
                if item.is_dir():
                    mods.append(item)
        
        if not mods:
            ctk.CTkLabel(scroll_frame, text="Нет модов", font=("Arial", 12)).pack(pady=20)
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
        mod_name = self.mod_name_entry.get().strip()
        
        if not mod_name:
            messagebox.showerror("Ошибка", "Введите имя мода!")
            return
        
        mod_dir = Path("Creator/mods") / mod_name
        
        if mod_dir.exists():
            if not messagebox.askyesno("Подтверждение", f"Мод '{mod_name}' уже существует. Перезаписать?"):
                return
            shutil.rmtree(mod_dir)
        
        mod_dir.mkdir(parents=True, exist_ok=True)
        
        self.open_mod_editor(mod_dir)

    def open_mod_editor(self, mod_dir):
        self.mod_folder = mod_dir
        self.clear_window()
        
        from mod_editor import ModEditor
        editor = ModEditor(self.root, self.mod_folder, self)
        editor.open_mod_editor()

    def open_mod_creator(self, mod_folder):
        self.mod_folder = mod_folder
        self.clear_window()
        
        from creator_editor import CreatorEditor
        creator = CreatorEditor(self.root, self.mod_folder, self)
        creator.open_creator()

    def clear_window(self):
        for widget in self.root.winfo_children():
            widget.destroy()

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = MainWindow()
    app.run()