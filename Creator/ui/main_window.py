#p/Creator/ui/main_window.py
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

    def load_all_icons(self, icons_config=None, parent_window=None):
        # Базовая конфигурация по умолчанию
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

                        #создания
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

                        {"name": "bridge-conveyor", "filename": "blocks/distribution/bridge-conveyor.png"},
                        {"name": "bridge-conveyor-end", "filename": "blocks/distribution/bridge-conveyor-end.png"},
                        {"name": "bridge-conveyor-bridge", "filename": "blocks/distribution/bridge-conveyor-bridge.png"},
                        {"name": "bridge-conveyor-arrow", "filename": "blocks/distribution/bridge-conveyor-arrow.png"},
                    ]
                }
            }
        }
        
        # Используем переданную конфигурацию или стандартную
        config = icons_config if icons_config is not None else default_config
        
        # Базовая директория для иконок
        icons_dir = os.path.join("Creator", "icons")
        
        # Создаем директории для каждой категории
        category_dirs = {}
        for category_name, category_config in config["categories"].items():
            category_dir = os.path.join(icons_dir, category_config["dest_dir"])
            os.makedirs(category_dir, exist_ok=True)
            category_dirs[category_name] = category_dir
        
        # Проверяем наличие всех иконок
        print("Проверка наличия иконок...")
        
        missing_icons = {}
        total_expected = 0
        total_existing = 0
        
        # Временная директория для загрузки слоев
        temp_dir = os.path.join(icons_dir, "temp_layers")
        os.makedirs(temp_dir, exist_ok=True)
        
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
            print(f"Все иконки уже загружены ({total_existing}/{total_expected})")
            # Очищаем временную директорию
            try:
                shutil.rmtree(temp_dir)
            except:
                pass
            return True
        
        # Показываем, какие иконки отсутствуют
        if missing_icons:
            print(f"Отсутствуют {total_expected - total_existing} иконок:")
            for category_name, missing in missing_icons.items():
                print(f"  {category_name} ({len(missing)}): {', '.join([m.get('name', 'unknown') for m in missing])}")
        
        # Подготавливаем задачи для загрузки
        download_tasks = []
        layer_groups = {}  # Группируем слои для склейки
        
        for category_name, category_config in config["categories"].items():
            category_dir = category_dirs[category_name]
            
            # Берем только отсутствующие иконки или все, если нет списка отсутствующих
            files_to_download = missing_icons.get(category_name, category_config["files"])
            
            for file_info in files_to_download:
                final_path = os.path.join(category_dir, f"{file_info['name']}.png")
                
                # Проверяем, есть ли слои
                if "layers" in file_info:
                    # Это многослойная иконка
                    layers = file_info["layers"]
                    layer_files = []
                    
                    # Добавляем задачи для каждого слоя
                    for i, layer in enumerate(layers):
                        temp_layer_path = os.path.join(temp_dir, f"{file_info['name']}_layer_{i}_{os.path.basename(layer['filename'])}")
                        
                        full_url = config["base_url"] + layer["filename"]
                        
                        layer_info = {
                            "url": full_url,
                            "save_path": temp_layer_path,
                            "name": f"{file_info['name']}_layer_{i}",
                            "category": category_name,
                            "is_layer": True,
                            "layer_index": i,
                            "layer_config": layer
                        }
                        
                        download_tasks.append(layer_info)
                        layer_files.append((temp_layer_path, layer))
                    
                    # Сохраняем информацию для склейки
                    layer_groups[final_path] = {
                        "layers": layer_files,
                        "name": file_info["name"],
                        "category": category_name,
                        "size": file_info.get("size", None)
                    }
                else:
                    # Одиночная иконка
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
        
        # Инициализация окна прогресса
        if parent_window:
            progress_window = ctk.CTkToplevel(parent_window)
            progress_window.title("Загрузка иконок")
            progress_window.geometry("400x180")
            progress_window.transient(parent_window)
            progress_window.grab_set()
            
            progress_label = ctk.CTkLabel(progress_window, text="Загрузка иконок...")
            progress_label.pack(pady=10)
            
            progress_bar = ctk.CTkProgressBar(progress_window, width=300)
            progress_bar.pack(pady=10)
            progress_bar.set(0)
            
            status_label = ctk.CTkLabel(progress_window, text="Подготовка...")
            status_label.pack(pady=5)
            
            # Добавляем метку для текущей операции
            operation_label = ctk.CTkLabel(progress_window, text="")
            operation_label.pack(pady=2)
            
            progress_window.update()
        
        downloaded = 0
        total_to_download = len(download_tasks)
        errors = []
        downloaded_layers = {}
        
        def update_progress(current, total, name, category, operation="Загрузка"):
            if parent_window:
                progress = current / total if total > 0 else 0
                progress_bar.set(progress)
                status_label.configure(text=f"{current}/{total} - {name}")
                progress_label.configure(text=f"{operation}: {name}")
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
                    
                    # Проверяем, что файл загрузился корректно
                    if os.path.exists(task["save_path"]) and os.path.getsize(task["save_path"]) > 0:
                        return True, task
                    else:
                        return False, (task, "Файл не загружен или пустой")
                else:
                    return False, (task, f"HTTP {response.status_code}")
            except Exception as e:
                return False, (task, str(e))
        
        def merge_layers(final_path, layers_info):
            """Склеивает несколько слоев в одно изображение"""
            try:
                from PIL import Image
                
                # Загружаем первый слой для определения размера
                base_image = None
                base_size = None
                
                # Если задан целевой размер, используем его
                target_size = layers_info.get("size")
                
                # Загружаем все слои
                images = []
                for layer_path, layer_config in layers_info["layers"]:
                    if os.path.exists(layer_path):
                        img = Image.open(layer_path).convert("RGBA")
                        
                        # Применяем настройки слоя
                        if "offset_x" in layer_config or "offset_y" in layer_config:
                            # Создаем новое изображение с учетом смещения
                            offset_x = layer_config.get("offset_x", 0)
                            offset_y = layer_config.get("offset_y", 0)
                            
                            new_img = Image.new("RGBA", img.size, (0, 0, 0, 0))
                            new_img.paste(img, (offset_x, offset_y), img)
                            img = new_img
                        
                        if "alpha" in layer_config:
                            # Изменяем прозрачность
                            alpha = int(layer_config["alpha"] * 255)
                            if img.mode == "RGBA":
                                r, g, b, a = img.split()
                                a = a.point(lambda p: p * alpha // 255)
                                img = Image.merge("RGBA", (r, g, b, a))
                        
                        images.append(img)
                        
                        if base_size is None:
                            base_size = img.size
                
                if not images:
                    return False
                
                # Определяем размер итогового изображения
                if target_size:
                    final_size = target_size
                else:
                    # Находим максимальные размеры среди всех слоев
                    max_width = max(img.size[0] for img in images)
                    max_height = max(img.size[1] for img in images)
                    final_size = (max_width, max_height)
                
                # Создаем пустое изображение для результата
                result = Image.new("RGBA", final_size, (0, 0, 0, 0))
                
                # Накладываем слои в порядке возрастания (первый - нижний)
                for img in images:
                    # Центрируем изображение, если оно меньше итогового
                    if img.size != final_size:
                        new_img = Image.new("RGBA", final_size, (0, 0, 0, 0))
                        x_offset = (final_size[0] - img.size[0]) // 2
                        y_offset = (final_size[1] - img.size[1]) // 2
                        new_img.paste(img, (x_offset, y_offset), img)
                        img = new_img
                    
                    result = Image.alpha_composite(result, img)
                
                # Сохраняем результат
                os.makedirs(os.path.dirname(final_path), exist_ok=True)
                result.save(final_path, "PNG")
                
                return True
                
            except Exception as e:
                print(f"Ошибка при склейке слоев для {final_path}: {e}")
                import traceback
                traceback.print_exc()
                return False
        
        try:
            # Загружаем файлы
            if parent_window:
                progress_label.configure(text="Загрузка файлов...")
                status_label.configure(text=f"0/{total_to_download}")
            
            with ThreadPoolExecutor(max_workers=4) as executor:
                futures = {executor.submit(download_file, task): task for task in download_tasks}
                
                for future in as_completed(futures):
                    task = futures[future]
                    success, result = future.result()
                    
                    if success:
                        downloaded += 1
                        if task.get("is_layer", False):
                            # Сохраняем информацию о загруженном слое
                            layer_key = f"{task['category']}_{task['name']}"
                            downloaded_layers[layer_key] = task["save_path"]
                        
                        if parent_window:
                            update_progress(downloaded, total_to_download, 
                                        task["name"], task["category"])
                    else:
                        if isinstance(result, tuple):
                            failed_task, error = result
                            errors.append((failed_task["name"], failed_task["category"], error))
                        else:
                            errors.append((task["name"], task["category"], "Unknown error"))
                        downloaded += 1
            
            # Склеиваем слои
            if layer_groups:
                if parent_window:
                    progress_label.configure(text="Склейка слоев...")
                    status_label.configure(text=f"0/{len(layer_groups)}")
                    progress_bar.set(0)
                    progress_window.update()
                
                merged_count = 0
                for final_path, layers_info in layer_groups.items():
                    if parent_window:
                        update_progress(merged_count, len(layer_groups), 
                                    layers_info["name"], layers_info["category"], 
                                    operation="Склейка")
                    
                    if merge_layers(final_path, layers_info):
                        merged_count += 1
                    else:
                        errors.append((layers_info["name"], layers_info["category"], 
                                    "Ошибка склейки слоев"))
            
            # Финальная проверка
            print("Финальная проверка загруженных иконок...")
            
            final_existing = 0
            final_missing = []
            
            for category_name, category_config in config["categories"].items():
                category_dir = category_dirs[category_name]
                
                for file_info in category_config["files"]:
                    icon_path = os.path.join(category_dir, f"{file_info['name']}.png")
                    
                    if os.path.exists(icon_path) and os.path.getsize(icon_path) > 0:
                        final_existing += 1
                    else:
                        final_missing.append(f"{category_name}/{file_info['name']}")
            
            if final_missing:
                errors.append(("Финальная проверка", "Все категории", 
                            f"Отсутствуют {len(final_missing)} иконок: {', '.join(final_missing[:5])}..."))
            
            # Очищаем временную директорию
            try:
                shutil.rmtree(temp_dir)
            except:
                pass
            
            # Вывод ошибок, если они есть
            if errors:
                error_msg = "\n".join(f"{name} ({category}): {error}" for name, category, error in errors)
                print(f"Ошибки загрузки:\n{error_msg}")
                if parent_window:
                    messagebox.showwarning("Ошибки загрузки", 
                                        f"Не удалось загрузить некоторые иконки:\n{error_msg}")
            
            if parent_window:
                progress_label.configure(text="Загрузка завершена!")
                progress_window.after(2000, progress_window.destroy)
            
            print(f"Иконки успешно загружены: {final_existing}/{total_expected}")
            return len(errors) == 0
        
        except Exception as e:
            error_msg = f"Критическая ошибка: {str(e)}"
            print(error_msg)
            import traceback
            traceback.print_exc()
            
            # Очищаем временную директорию
            try:
                shutil.rmtree(temp_dir)
            except:
                pass
            
            if parent_window and 'progress_window' in locals():
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
        
        from .mod_editor import ModEditor
        editor = ModEditor(self.root, self.mod_folder, self)
        editor.open_mod_editor()

    def open_mod_creator(self, mod_folder):
        self.mod_folder = mod_folder
        self.clear_window()
        
        from .creator_editor import CreatorEditor
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