# Creator/main.py - Полный объединенный файл программы
import eel
import sys
import os
import json
import threading
import time
import shutil
import subprocess
import platform
import re
import base64
import requests
import ctypes
import zipfile
import io
import tempfile
from pathlib import Path
from io import BytesIO
from PIL import Image
from Creator.utils.lang_system import LangT

if platform.system() == "Windows":
    import winreg

# ===================== РЕСУРСНЫЙ ПУТЬ =====================
def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# ===================== ГЛОБАЛЬНЫЕ ПЕРЕМЕННЫЕ =====================
MODS_WORK_DIR = "Creator/mods"
current_editor = None
settings = {}
settings_file = None

# ===================== НАСТРОЙКИ =====================
def load_settings():
    global settings, settings_file
    default_settings = {"language": "ru", "save_folder": MODS_WORK_DIR}
    appdata = os.getenv('APPDATA') or os.path.expanduser("~")
    settings_dir = Path(appdata) / "MindustryModCreator"
    settings_dir.mkdir(parents=True, exist_ok=True)
    settings_file = settings_dir / "settings.json"
    if settings_file.exists():
        try:
            with open(settings_file, 'r', encoding='utf-8') as f:
                settings = json.load(f)
                for key, value in default_settings.items():
                    if key not in settings:
                        settings[key] = value
        except:
            settings = default_settings.copy()
    else:
        settings = default_settings.copy()
        save_settings()

def save_settings():
    global settings, settings_file
    try:
        settings_file.parent.mkdir(parents=True, exist_ok=True)
        with open(settings_file, 'w', encoding='utf-8') as f:
            json.dump(settings, f, ensure_ascii=False, indent=4)
        return True
    except:
        return False
# ===================== JAVA DOWNLOAD =====================
@eel.expose
def install_java_web(callback_id=None):
    """Установка Java 17 из веб-интерфейса"""
    # Проверяем, не выполняется ли уже установка
    if hasattr(install_java_web, '_is_running') and install_java_web._is_running:
        return {"success": False, "message": "Установка уже выполняется"}
    
    # Запускаем установку
    install_java_web._is_running = True
    result = install_java_17(callback_id)
    install_java_web._is_running = False
    return result

@eel.expose
def restart_pc_jdk_100_i():
    os.system("shutdown /r /t 5")

@eel.expose
def get_admin_rights_status():
    """Проверяет наличие прав администратора"""
    return {"has_admin": check_admin_rights()}

def check_admin_rights():
    """Проверяет права администратора на Windows"""
    if platform.system() == "Windows":
        try:
            import ctypes
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        except:
            pass
    return False

def get_java_version_from_exe(java_exe):
    """Получает версию Java из исполняемого файла"""
    try:
        result = subprocess.run([java_exe, "-version"], capture_output=True, text=True, shell=True)
        version_output = result.stderr if result.stderr else result.stdout
        patterns = [r'version "(\d+)', r'(\d+)\.\d+']
        for pattern in patterns:
            match = re.search(pattern, version_output)
            if match:
                return match.group(1)
    except:
        pass
    return None

def find_java_17_in_all_paths():
    """Ищет Java 17 во всех возможных местах"""
    paths_to_check = []
    
    # PATH
    for path in os.environ.get("PATH", "").split(os.pathsep):
        java_exe = os.path.join(path, "java.exe")
        if os.path.exists(java_exe):
            paths_to_check.append(java_exe)
    
    # JAVA_HOME
    java_home = os.environ.get("JAVA_HOME", "")
    if java_home:
        java_exe = os.path.join(java_home, "bin", "java.exe")
        if os.path.exists(java_exe):
            paths_to_check.append(java_exe)
    
    # Стандартные пути
    standard_paths = [
        r"C:\Program Files\Java",
        r"C:\Program Files (x86)\Java",
        r"C:\Program Files\Eclipse Adoptium",
        r"C:\mmc_java",
    ]
    for base_path in standard_paths:
        if os.path.exists(base_path):
            for item in os.listdir(base_path):
                item_path = os.path.join(base_path, item)
                if os.path.isdir(item_path):
                    java_exe = os.path.join(item_path, "bin", "java.exe")
                    if os.path.exists(java_exe):
                        paths_to_check.append(java_exe)
    
    # Проверяем версию
    for java_exe in paths_to_check:
        version = get_java_version_from_exe(java_exe)
        if version == "17":
            return java_exe
    return None

def install_java_17(callback_id=None):
    """Устанавливает Java 17 - вызывается из eel"""
    def install_thread():
        try:
            # Сначала проверяем, установлена ли уже Java 17
            java_check = check_java()
            if java_check.get("has_java"):
                send_java_complete(True, f"Java 17 уже установлена по пути: {java_check.get('path')}", callback_id)
                return
            
            # Проверяем права администратора
            has_admin = check_admin_rights()
            
            if not has_admin:
                send_java_progress(0.05, LangT("no_admin_download"), callback_id)
            
            # Определяем путь установки
            if has_admin:
                install_path = Path(r"C:\Program Files\Java\jdk-17")
            else:
                install_path = Path(r"C:\mmc_java")
            
            # Создаем папку
            try:
                install_path.mkdir(parents=True, exist_ok=True)
            except PermissionError:
                send_java_complete(False, "Нет прав для создания папки. Запустите программу от имени администратора.", callback_id)
                return
            
            # URL для скачивания
            jdk_url = "https://github.com/adoptium/temurin17-binaries/releases/download/jdk-17.0.12%2B7/OpenJDK17U-jdk_x64_windows_hotspot_17.0.12_7.zip"
            
            send_java_progress(0.1, LangT("java_t_1"), callback_id)
            
            # Скачиваем
            temp_dir = Path(tempfile.gettempdir())
            temp_zip = temp_dir / "jdk_temp.zip"
            
            try:
                response = requests.get(jdk_url, stream=True, timeout=60)
                response.raise_for_status()
            except requests.RequestException as e:
                send_java_complete(False, f"Ошибка скачивания: {str(e)}", callback_id)
                return
            
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            
            send_java_progress(0.2, LangT("java_download_m1"), callback_id)
            
            try:
                with open(temp_zip, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)
                            if total_size > 0:
                                progress = 0.2 + (downloaded / total_size * 0.6)
                                percent = int((downloaded / total_size) * 100)
                                send_java_progress(progress, f"{LangT("download")}: {downloaded/1024/1024:.1f}MB / {total_size/1024/1024:.1f}MB ({percent}%)", callback_id)
            except Exception as e:
                send_java_complete(False, f"Ошибка при скачивании: {str(e)}", callback_id)
                return
            
            send_java_progress(0.8, LangT("unpack_jdk"), callback_id)
            
            # Распаковываем
            try:
                with zipfile.ZipFile(temp_zip, 'r') as zip_ref:
                    # Удаляем старую папку если есть
                    if install_path.exists():
                        shutil.rmtree(install_path, ignore_errors=True)
                    
                    # Распаковываем во временную папку
                    extract_temp = temp_dir / "jdk_extract"
                    if extract_temp.exists():
                        shutil.rmtree(extract_temp, ignore_errors=True)
                    extract_temp.mkdir(exist_ok=True)
                    
                    zip_ref.extractall(str(extract_temp))
                    
                    # Находим распакованную папку
                    extracted_items = list(extract_temp.iterdir())
                    if extracted_items:
                        extracted_dir = extracted_items[0]
                        # Перемещаем в нужное место
                        shutil.move(str(extracted_dir), str(install_path))
                        # Удаляем временную папку
                        shutil.rmtree(extract_temp, ignore_errors=True)
            except Exception as e:
                send_java_complete(False, f"Ошибка распаковки: {str(e)}", callback_id)
                return
            
            # Удаляем временный файл
            try:
                temp_zip.unlink()
            except:
                pass
            
            send_java_progress(0.95, "⚙️ Настройка окружения...", callback_id)
            
            # Проверяем установку
            java_exe = install_path / "bin" / "java.exe"
            if java_exe.exists():
                # Устанавливаем JAVA_HOME
                set_java_home(str(install_path))
                
                # Добавляем в PATH для текущей сессии
                os.environ["JAVA_HOME"] = str(install_path)
                os.environ["PATH"] = f"{str(install_path / 'bin')};{os.environ.get('PATH', '')}"
                
                send_java_progress(1.0, "✅ Установка завершена!", callback_id)
                send_java_complete(True, f"✅ JDK 17 успешно установлена!\n📂 Путь: {install_path}\n🔄 Перезапустите программу для применения изменений.", callback_id)
            else:
                send_java_complete(False, "❌ JDK не установилась корректно. Попробуйте установить вручную.", callback_id)
                
        except Exception as e:
            send_java_complete(False, f"❌ Ошибка: {str(e)}", callback_id)
    
    threading.Thread(target=install_thread, daemon=True).start()
    return {"success": True, "message": "Установка начата"}

def set_java_home(java_path):
    """Устанавливает JAVA_HOME в системе и в текущем процессе"""
    if platform.system() != "Windows":
        return
    
    try:
        # Устанавливаем в реестре для постоянного хранения
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            "Environment",
            0,
            winreg.KEY_SET_VALUE | winreg.KEY_READ | winreg.KEY_WRITE
        )
        
        # Устанавливаем JAVA_HOME
        winreg.SetValueEx(key, "JAVA_HOME", 0, winreg.REG_EXPAND_SZ, java_path)
        
        # Добавляем bin в PATH
        bin_path = os.path.join(java_path, "bin")
        try:
            current_path, path_type = winreg.QueryValueEx(key, "PATH")
            path_str = current_path if current_path else ""
            if bin_path not in path_str:
                new_path = f"{bin_path};{path_str}" if path_str else bin_path
                winreg.SetValueEx(key, "PATH", 0, winreg.REG_EXPAND_SZ, new_path)
        except WindowsError:
            winreg.SetValueEx(key, "PATH", 0, winreg.REG_EXPAND_SZ, bin_path)
        
        winreg.CloseKey(key)
        
        # Обновляем переменные в текущем процессе
        os.environ["JAVA_HOME"] = java_path
        
        # Обновляем PATH в текущем процессе
        current_path = os.environ.get("PATH", "")
        if bin_path not in current_path:
            os.environ["PATH"] = f"{bin_path};{current_path}"
        
        # Уведомляем систему об изменении
        broadcast_environment_change()
        
        print(f"✅ JAVA_HOME установлен: {java_path}")
        print(f"✅ PATH обновлен: {bin_path}")
        
    except Exception as e:
        print(f"Ошибка установки JAVA_HOME: {e}")

def broadcast_environment_change():
    """Уведомляет систему об изменении переменных окружения"""
    if platform.system() == "Windows":
        try:
            import ctypes
            HWND_BROADCAST = 0xFFFF
            WM_SETTINGCHANGE = 0x001A
            SMTO_ABORTIFHUNG = 0x0002
            
            # Отправляем сообщение всем окнам
            ctypes.windll.user32.SendMessageTimeoutW(
                HWND_BROADCAST, WM_SETTINGCHANGE, 0, "Environment",
                SMTO_ABORTIFHUNG, 5000, None
            )
            
            # Дополнительно обновляем для текущего процесса
            ctypes.windll.user32.SendMessageTimeoutW(
                HWND_BROADCAST, WM_SETTINGCHANGE, 0, None,
                SMTO_ABORTIFHUNG, 5000, None
            )
        except Exception as e:
            print(f"Ошибка уведомления системы: {e}")

def send_java_progress(percent, message, callback_id):
    """Отправляет прогресс установки Java в веб-интерфейс"""
    if callback_id:
        try:
            eel.java_install_progress(callback_id, percent, message)()
        except:
            pass

def send_java_complete(success, message, callback_id):
    """Отправляет завершение установки Java"""
    if callback_id:
        try:
            eel.java_install_complete(callback_id, success, message)()
        except:
            pass
# ===================== РАБОТА С МОДАМИ =====================
def get_mods_list():
    mods_dir = Path(MODS_WORK_DIR)
    mods = []
    if mods_dir.exists():
        for item in mods_dir.iterdir():
            if item.is_dir():
                mods.append(item.name)
    return sorted(mods)

def create_mod_folder(mod_name):
    mod_dir = Path(MODS_WORK_DIR) / mod_name
    if mod_dir.exists():
        return {"success": False, "error": f"Мод '{mod_name}' уже существует"}
    mod_dir.mkdir(parents=True, exist_ok=True)
    return {"success": True, "mod_path": str(mod_dir)}

def delete_mod(mod_name):
    mod_dir = Path(MODS_WORK_DIR) / mod_name
    if mod_dir.exists():
        shutil.rmtree(mod_dir)
        return {"success": True}
    return {"success": False, "error": "Мод не найден"}

# ===================== JAVA =====================
def check_java():
    java_paths = []
    for p in os.environ.get("PATH", "").split(os.pathsep):
        java_exe = os.path.join(p, "java.exe")
        if os.path.exists(java_exe):
            java_paths.append(java_exe)
    java_home = os.environ.get("JAVA_HOME", "")
    if java_home:
        java_exe = os.path.join(java_home, "bin", "java.exe")
        if os.path.exists(java_exe):
            java_paths.append(java_exe)
    for java_exe in java_paths:
        try:
            result = subprocess.run([java_exe, "-version"], capture_output=True, text=True, shell=True)
            version_text = result.stderr if result.stderr else result.stdout
            match = re.search(r'version "(\d+)', version_text)
            if match and match.group(1) == "17":
                return {"has_java": True, "version": "17", "path": java_exe}
        except:
            pass
    return {"has_java": False, "version": None, "path": None}

# ===================== ШАБЛОН =====================
def replace_example_in_java(content_bytes, mod_name):
    try:
        content = content_bytes.decode('utf-8')
        mod_name_clean = re.sub(r'[^a-zA-Z0-9]', '', mod_name)
        mod_name_lower = mod_name_clean.lower()
        mod_name_camel = mod_name_clean[0].upper() + mod_name_clean[1:] if mod_name_clean else "Mod"
        content = content.replace('package example;', f'package {mod_name_lower};')
        content = re.sub(r'import\s+example\.', f'import {mod_name_lower}.', content)
        content = content.replace('ExampleJavaMod', f'{mod_name_camel}JavaMod')
        content = content.replace('example-java-mod', mod_name_lower)
        content = re.sub(r'\bexample\.', f'{mod_name_lower}.', content)
        return content.encode('utf-8')
    except:
        return content_bytes

def update_java_main_class(mod_folder, mod_name):
    mod_name_clean = re.sub(r'[^a-zA-Z0-9]', '', mod_name)
    mod_name_lower = mod_name_clean.lower()
    mod_name_camel = mod_name_clean[0].upper() + mod_name_clean[1:] if mod_name_clean else "Mod"
    example_dir = mod_folder / "src" / "example"
    if example_dir.exists():
        shutil.rmtree(example_dir)
    src_dir = mod_folder / "src" / mod_name_lower
    src_dir.mkdir(parents=True, exist_ok=True)
    java_file = src_dir / f"{mod_name_camel}JavaMod.java"
    if not java_file.exists():
        java_content = f"""package {mod_name_lower};

import arc.*;
import arc.util.*;
import mindustry.*;
import mindustry.game.EventType.*;
import mindustry.mod.*;

public class {mod_name_camel}JavaMod extends Mod{{
    public {mod_name_camel}JavaMod(){{
        Log.info("Loaded {mod_name_camel}JavaMod");
    }}
    @Override
    public void loadContent(){{
        Log.info("Loading content");
    }}
}}
"""
        java_file.write_text(java_content, encoding='utf-8')
    return f"{mod_name_lower}.{mod_name_camel}JavaMod"

def create_mod_hjson(mod_folder, mod_name, main_class):
    hjson_content = f'''displayName: "{mod_name}"
name: "{mod_name.lower().replace(' ', '-')}"
author: "Your Name"
main: "{main_class}"
description: "Empty mod template"
version: "1.0"
minGameVersion: "156"
java: true
'''
    (mod_folder / "mod.hjson").write_text(hjson_content, encoding='utf-8')

def download_template(mod_name):
    mod_folder = Path(MODS_WORK_DIR) / mod_name
    
    def download_thread():
        try:
            url = "https://github.com/Anuken/MindustryModTemplate/archive/refs/heads/master.zip"
            response = requests.get(url, timeout=60)
            response.raise_for_status()
            zip_data = io.BytesIO(response.content)
            with zipfile.ZipFile(zip_data, 'r') as zip_ref:
                first_file = zip_ref.namelist()[0]
                root_folder = first_file.split('/')[0]
                for file_info in zip_ref.infolist():
                    filename = file_info.filename
                    if filename.startswith(root_folder + '/'):
                        rel_path = filename[len(root_folder) + 1:]
                        if not rel_path or rel_path.endswith('/'):
                            continue
                        target_path = mod_folder / rel_path
                        target_path.parent.mkdir(parents=True, exist_ok=True)
                        content = zip_ref.read(file_info)
                        if rel_path.endswith('.java'):
                            content = replace_example_in_java(content, mod_name)
                        with open(target_path, 'wb') as f:
                            f.write(content)
            example_folder = mod_folder / "src" / "example"
            if example_folder.exists():
                shutil.rmtree(example_folder)
            main_class = update_java_main_class(mod_folder, mod_name)
            create_mod_hjson(mod_folder, mod_name, main_class)
            eel.download_complete(True, mod_name)
        except Exception as e:
            eel.download_complete(False, str(e))
    
    threading.Thread(target=download_thread, daemon=True).start()

# ===================== КЛАСС РЕДАКТОРА (ПОЛНАЯ ЛОГИКА) =====================
class CreatorEditor:
    def __init__(self, mod_folder, mod_name):
        self.mod_folder = Path(mod_folder)
        self.mod_name = mod_name
        self.compile_callback = None
        self.current_compile_callback = None
        self.settings = load_settings()
        
        self.TP_source_folder = self.mod_folder / "build" / "libs"
        self.TP_filename = f"{mod_name}Desktop.jar"
        self.TP_new_name = f"{mod_name}.jar"

    def move_and_rename_file(self):
        source_path = self.TP_source_folder / self.TP_filename
        if not source_path.exists():
            return False
        save_folder = self.settings.get("save_folder", "mods")
        target_folder = Path(save_folder)
        target_folder.mkdir(parents=True, exist_ok=True)
        target_path = target_folder / self.TP_new_name
        try:
            if target_path.exists():
                target_path.unlink()
            shutil.move(str(source_path), str(target_path))
            return True
        except:
            return False

    def _format_to_camel_case(self, text):
        if not text or not isinstance(text, str):
            return ""
        words = text.strip().split()
        if not words:
            return ""
        result = words[0].lower()
        for word in words[1:]:
            if word:
                result += word.capitalize()
        return result

    def _format_float_value(self, value):
        if not value:
            return "0"
        try:
            num = float(value)
            num = min(num, 5000.00)
            formatted = f"{num:.2f}"
            if formatted.endswith(".00"):
                formatted = formatted[:-3]
            elif formatted.endswith(".0"):
                formatted = formatted[:-2]
            return formatted
        except:
            return "0"

    def _find_and_load_sprite(self, block_name, sprite_subdir):
        sprites_root = self.mod_folder / "assets" / "sprites"
        possible_paths = [
            sprites_root / sprite_subdir / f"{block_name}.png",
            sprites_root / block_name / f"{block_name}.png",
            sprites_root / f"{block_name}.png"
        ]
        for sprite_path in possible_paths:
            if sprite_path.exists():
                try:
                    with Image.open(sprite_path) as img:
                        img.thumbnail((64, 64), Image.Resampling.LANCZOS)
                        buffer = BytesIO()
                        img.save(buffer, format='PNG')
                        base64_str = base64.b64encode(buffer.getvalue()).decode('utf-8')
                        return f"data:image/png;base64,{base64_str}"
                except:
                    continue
        return None

    def _get_all_blocks_data(self):
        mod_name_lower = self.mod_name.lower()
        all_blocks = []
        
        # Items
        items_file = self.mod_folder / f"src/{mod_name_lower}/init/items/ModItems.java"
        if items_file.exists():
            with open(items_file, 'r', encoding='utf-8') as f:
                content = f.read()
            patterns = [
                r'public\s+static\s+Item\s+([^;]+);',
                r'Item\s+(\w+)\s*=',
                r'(\w+)\s*=\s*new\s+Item\("[^"]+"\)',
            ]
            for pattern in patterns:
                matches = re.findall(pattern, content)
                for match in matches:
                    block_names = [b.strip() for b in (match.split(',') if isinstance(match, str) else [match])]
                    for block_name in block_names:
                        if block_name and not any(b["name"] == block_name for b in all_blocks):
                            sprite_data = self._find_and_load_sprite(block_name, "items")
                            all_blocks.append({
                                "name": block_name,
                                "type": "item",
                                "display": "Предмет",
                                "icon": "📦",
                                "hasSprite": sprite_data is not None,
                                "spriteData": sprite_data
                            })
        
        # Liquids
        liquids_file = self.mod_folder / f"src/{mod_name_lower}/init/liquids/ModLiquid.java"
        if liquids_file.exists():
            with open(liquids_file, 'r', encoding='utf-8') as f:
                content = f.read()
            patterns = [
                r'public\s+static\s+Liquid\s+([^;]+);',
                r'Liquid\s+(\w+)\s*=',
                r'(\w+)\s*=\s*new\s+Liquid\("[^"]+"\)',
            ]
            for pattern in patterns:
                matches = re.findall(pattern, content)
                for match in matches:
                    block_names = [b.strip() for b in (match.split(',') if isinstance(match, str) else [match])]
                    for block_name in block_names:
                        if block_name and not any(b["name"] == block_name for b in all_blocks):
                            sprite_data = self._find_and_load_sprite(block_name, "liquids")
                            all_blocks.append({
                                "name": block_name,
                                "type": "liquid",
                                "display": "Жидкость",
                                "icon": "💧",
                                "hasSprite": sprite_data is not None,
                                "spriteData": sprite_data
                            })
        
        return all_blocks

    def _delete_block_by_name(self, block_name, block_type):
        mod_name_lower = self.mod_name.lower()
        try:
            formatted_name = self._format_to_camel_case(block_name)
            
            # Удаляем текстуру
            if block_type == "item":
                sprite_path = self.mod_folder / f"assets/sprites/items/{formatted_name}.png"
            else:
                sprite_path = self.mod_folder / f"assets/sprites/liquids/{formatted_name}.png"
            if sprite_path.exists():
                sprite_path.unlink()
            
            # Удаляем из Java файла
            if block_type == "item":
                file_path = self.mod_folder / f"src/{mod_name_lower}/init/items/ModItems.java"
                java_type = "Item"
            else:
                file_path = self.mod_folder / f"src/{mod_name_lower}/init/liquids/ModLiquid.java"
                java_type = "Liquid"
            
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Удаляем строку с объявлением
                lines = content.split('\n')
                new_lines = []
                skip_until = -1
                i = 0
                while i < len(lines):
                    line = lines[i]
                    if re.search(rf'{formatted_name}\s*=\s*new\s+{java_type}\s*\(', line):
                        brace_count = 0
                        j = i
                        while j < len(lines):
                            current = lines[j]
                            if '{' in current:
                                brace_count += current.count('{')
                            if '}' in current:
                                brace_count -= current.count('}')
                            if brace_count == 0 and ';' in current:
                                i = j + 1
                                break
                            j += 1
                        else:
                            i += 1
                        continue
                    
                    if f'public static {java_type} {formatted_name}' in line:
                        match = re.search(rf'public static {java_type}\s+(.+?);', line)
                        if match:
                            vars_str = match.group(1)
                            var_list = [v.strip() for v in vars_str.split(',')]
                            remaining = [v for v in var_list if v != formatted_name]
                            indent = ' ' * (len(line) - len(line.lstrip()))
                            if remaining:
                                new_line = f"{indent}public static {java_type} {', '.join(remaining)};"
                                new_lines.append(new_line)
                            continue
                    
                    new_lines.append(line)
                    i += 1
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write('\n'.join(new_lines))
            
            return {"success": True, "message": f"Элемент '{block_name}' удален"}
        except Exception as e:
            return {"success": False, "message": str(e)}

    def _create_item(self, item_data):
        try:
            action = item_data.get('action', 'create')
            mod_name_lower = self.mod_name.lower()
            
            if action == 'edit':
                item_name = item_data.get('name', '')
                formatted_name = self._format_to_camel_case(item_name)
                file_path = self.mod_folder / f"src/{mod_name_lower}/init/items/ModItems.java"
                
                if not file_path.exists():
                    return {"success": False, "error": "ModItems.java не найден"}
                
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                pattern = rf'{formatted_name}\s*=\s*new\s+Item\("[^"]*"\)\s*{{{{(.*?)}}}};'
                match = re.search(pattern, content, re.DOTALL)
                
                if not match:
                    return {"success": False, "error": f"Предмет '{item_name}' не найден"}
                
                block_content = match.group(1)
                
                def extract_float(prop):
                    m = re.search(rf'{prop}\s*=\s*([\d.]+)f?', block_content)
                    if m:
                        v = m.group(1)
                        if v.endswith('.0'):
                            v = v[:-2]
                        return v
                    return "0"
                
                always_match = re.search(r'alwaysUnlocked\s*=\s*(true|false)', block_content)
                
                return {
                    "success": True,
                    "data": {
                        "name": item_name,
                        "charge": extract_float("charge"),
                        "flammability": extract_float("flammability"),
                        "explosiveness": extract_float("explosiveness"),
                        "radioactivity": extract_float("radioactivity"),
                        "always_unlocked": always_match.group(1) == "true" if always_match else False
                    }
                }
            
            if action == 'update':
                original_name = item_data.get('original_name', '')
                name = item_data.get('name', '').strip()
                charge = item_data.get('charge', '0')
                flammability = item_data.get('flammability', '0')
                explosiveness = item_data.get('explosiveness', '0')
                radioactivity = item_data.get('radioactivity', '0')
                always_unlocked = item_data.get('always_unlocked', False)
                
                if not name:
                    return {"success": False, "error": "Имя предмета обязательно"}
                
                formatted_name = self._format_to_camel_case(name)
                original_formatted = self._format_to_camel_case(original_name) if original_name else formatted_name
                file_path = self.mod_folder / f"src/{mod_name_lower}/init/items/ModItems.java"
                
                if not file_path.exists():
                    return {"success": False, "error": "ModItems.java не найден"}
                
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                pattern = rf'({formatted_name}\s*=\s*new\s+Item\("[^"]*"\)\s*{{{{)(.*?)(}}}};)'
                
                def replace_props(m):
                    prefix = m.group(1)
                    suffix = m.group(3)
                    new_props = f"""    charge = {self._format_float_value(charge)}f;
                    flammability = {self._format_float_value(flammability)}f;
                    explosiveness = {self._format_float_value(explosiveness)}f;
                    radioactivity = {self._format_float_value(radioactivity)}f;
                    alwaysUnlocked = {"true" if always_unlocked else "false"};
                    
                    localizedName = Core.bundle.get("{formatted_name}.name", "{name}");
                    description = Core.bundle.get("{formatted_name}.description", "");"""
                    return f"{prefix}\n{new_props}\n{suffix}"
                
                if original_formatted != formatted_name:
                    content = content.replace(original_formatted, formatted_name)
                
                content = re.sub(pattern, replace_props, content, flags=re.DOTALL)
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                # Переименовываем текстуру
                old_path = self.mod_folder / f"assets/sprites/items/{original_formatted}.png"
                new_path = self.mod_folder / f"assets/sprites/items/{formatted_name}.png"
                if old_path.exists() and not new_path.exists():
                    old_path.rename(new_path)
                
                return {"success": True, "message": f"Предмет '{name}' обновлен"}
            
            # CREATE
            name = item_data.get('name', '').strip()
            if not name:
                return {"success": False, "error": "Имя предмета обязательно"}
            
            formatted_name = self._format_to_camel_case(name)
            file_path = self.mod_folder / f"src/{mod_name_lower}/init/items/ModItems.java"
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            if not file_path.exists():
                file_path.write_text(f"""package {mod_name_lower}.init.items;

import mindustry.type.Item;
import arc.Core;

public class ModItems {{
    public static Item;
    
    public static void Load() {{
    }}
}}
""", encoding='utf-8')
            
            content = file_path.read_text(encoding='utf-8')
            
            if f'new Item("{formatted_name}")' not in content:
                if "public static Item;" in content:
                    content = content.replace("public static Item;", f"public static Item {formatted_name};")
                elif f"public static Item {formatted_name}" not in content:
                    lines = content.split('\n')
                    for i, line in enumerate(lines):
                        if "public static Item " in line and formatted_name not in line:
                            lines[i] = line.rstrip(';') + f", {formatted_name};"
                            content = '\n'.join(lines)
                            break
                
                load_start = content.find("public static void Load() {")
                if load_start != -1:
                    open_brace = content.find('{', load_start)
                    if open_brace != -1:
                        indent = "        "
                        charge = self._format_float_value(item_data.get('charge', '0'))
                        flammability = self._format_float_value(item_data.get('flammability', '0'))
                        explosiveness = self._format_float_value(item_data.get('explosiveness', '0'))
                        radioactivity = self._format_float_value(item_data.get('radioactivity', '0'))
                        always = "true" if item_data.get('always_unlocked', False) else "false"
                        
                        item_code = f'''
        {formatted_name} = new Item("{formatted_name}"){{{{
            charge = {charge}f;
            flammability = {flammability}f;
            explosiveness = {explosiveness}f;
            radioactivity = {radioactivity}f;
            alwaysUnlocked = {always};
            
            localizedName = Core.bundle.get("{formatted_name}.name", "{name}");
            description = Core.bundle.get("{formatted_name}.description", "");
        }}}};'''
                        content = content[:open_brace+1] + item_code + content[open_brace+1:]
                
                file_path.write_text(content, encoding='utf-8')
                
                # Копируем иконку
                template = resource_path("Creator/icons/items/copper.png")
                sprite_dir = self.mod_folder / "assets/sprites/items"
                sprite_dir.mkdir(parents=True, exist_ok=True)
                target = sprite_dir / f"{formatted_name}.png"
                if os.path.exists(template) and not target.exists():
                    shutil.copy2(template, target)
                
                return {"success": True, "message": f"Предмет '{name}' создан"}
            else:
                return {"success": False, "error": f"Предмет '{name}' уже существует"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _create_liquid(self, liquid_data):
        try:
            action = liquid_data.get('action', 'create')
            mod_name_lower = self.mod_name.lower()
            
            if action == 'edit':
                liquid_name = liquid_data.get('name', '')
                formatted_name = self._format_to_camel_case(liquid_name)
                file_path = self.mod_folder / f"src/{mod_name_lower}/init/liquids/ModLiquid.java"
                
                if not file_path.exists():
                    return {"success": False, "error": "ModLiquid.java не найден"}
                
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                pattern = rf'{formatted_name}\s*=\s*new\s+Liquid\("[^"]*"\)\s*{{{{(.*?)}}}};'
                match = re.search(pattern, content, re.DOTALL)
                
                if not match:
                    return {"success": False, "error": f"Жидкость '{liquid_name}' не найдена"}
                
                block_content = match.group(1)
                
                def extract_float(prop):
                    m = re.search(rf'{prop}\s*=\s*([\d.]+)f?', block_content)
                    if m:
                        v = m.group(1)
                        if v.endswith('.0'):
                            v = v[:-2]
                        return v
                    return "0"
                
                always_match = re.search(r'alwaysUnlocked\s*=\s*(true|false)', block_content)
                
                return {
                    "success": True,
                    "data": {
                        "name": liquid_name,
                        "flammability": extract_float("flammability"),
                        "explosiveness": extract_float("explosiveness"),
                        "temperature": extract_float("temperature"),
                        "viscosity": extract_float("viscosity"),
                        "always_unlocked": always_match.group(1) == "true" if always_match else False
                    }
                }
            
            if action == 'update':
                original_name = liquid_data.get('original_name', '')
                name = liquid_data.get('name', '').strip()
                flammability = liquid_data.get('flammability', '0')
                explosiveness = liquid_data.get('explosiveness', '0')
                temperature = liquid_data.get('temperature', '0')
                viscosity = liquid_data.get('viscosity', '0')
                always_unlocked = liquid_data.get('always_unlocked', False)
                
                if not name:
                    return {"success": False, "error": "Имя жидкости обязательно"}
                
                formatted_name = self._format_to_camel_case(name)
                original_formatted = self._format_to_camel_case(original_name) if original_name else formatted_name
                file_path = self.mod_folder / f"src/{mod_name_lower}/init/liquids/ModLiquid.java"
                
                if not file_path.exists():
                    return {"success": False, "error": "ModLiquid.java не найден"}
                
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                pattern = rf'({formatted_name}\s*=\s*new\s+Liquid\("[^"]*"\)\s*{{{{)(.*?)(}}}};)'
                
                def replace_props(m):
                    prefix = m.group(1)
                    suffix = m.group(3)
                    visc_val = float(viscosity) if viscosity else 0
                    visc_val = max(0, min(visc_val, 1))
                    visc_str = f"{visc_val:.2f}".rstrip('0').rstrip('.') if visc_val != 0 else "0"
                    new_props = f"""    flammability = {self._format_float_value(flammability)}f;
                            explosiveness = {self._format_float_value(explosiveness)}f;
                            temperature = {self._format_float_value(temperature)}f;
                            viscosity = {visc_str}f;
                            alwaysUnlocked = {"true" if always_unlocked else "false"};
                            
                            localizedName = Core.bundle.get("{formatted_name}.name", "{name}");
                            description = Core.bundle.get("{formatted_name}.description", "");"""
                    return f"{prefix}\n{new_props}\n{suffix}"
                
                if original_formatted != formatted_name:
                    content = content.replace(original_formatted, formatted_name)
                
                content = re.sub(pattern, replace_props, content, flags=re.DOTALL)
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                # Переименовываем текстуру
                old_path = self.mod_folder / f"assets/sprites/liquids/{original_formatted}.png"
                new_path = self.mod_folder / f"assets/sprites/liquids/{formatted_name}.png"
                if old_path.exists() and not new_path.exists():
                    old_path.rename(new_path)
                
                return {"success": True, "message": f"Жидкость '{name}' обновлена"}
            
            # CREATE
            name = liquid_data.get('name', '').strip()
            if not name:
                return {"success": False, "error": "Имя жидкости обязательно"}
            
            formatted_name = self._format_to_camel_case(name)
            file_path = self.mod_folder / f"src/{mod_name_lower}/init/liquids/ModLiquid.java"
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            if not file_path.exists():
                file_path.write_text(f"""package {mod_name_lower}.init.liquids;

import mindustry.type.Liquid;
import arc.Core;

public class ModLiquid {{
    public static Liquid;
    
    public static void Load() {{
    }}
}}
""", encoding='utf-8')
            
            content = file_path.read_text(encoding='utf-8')
            
            if f'new Liquid("{formatted_name}")' not in content:
                if "public static Liquid;" in content:
                    content = content.replace("public static Liquid;", f"public static Liquid {formatted_name};")
                elif f"public static Liquid {formatted_name}" not in content:
                    lines = content.split('\n')
                    for i, line in enumerate(lines):
                        if "public static Liquid " in line and formatted_name not in line:
                            lines[i] = line.rstrip(';') + f", {formatted_name};"
                            content = '\n'.join(lines)
                            break
                
                load_start = content.find("public static void Load() {")
                if load_start != -1:
                    open_brace = content.find('{', load_start)
                    if open_brace != -1:
                        indent = "        "
                        flammability = self._format_float_value(liquid_data.get('flammability', '0'))
                        explosiveness = self._format_float_value(liquid_data.get('explosiveness', '0'))
                        temperature = self._format_float_value(liquid_data.get('temperature', '0'))
                        visc_val = float(liquid_data.get('viscosity', '0')) if liquid_data.get('viscosity') else 0
                        visc_val = max(0, min(visc_val, 1))
                        visc_str = f"{visc_val:.2f}".rstrip('0').rstrip('.') if visc_val != 0 else "0"
                        always = "true" if liquid_data.get('always_unlocked', False) else "false"
                        
                        liquid_code = f'''
        {formatted_name} = new Liquid("{formatted_name}"){{{{
            flammability = {flammability}f;
            explosiveness = {explosiveness}f;
            temperature = {temperature}f;
            viscosity = {visc_str}f;
            alwaysUnlocked = {always};
            
            localizedName = Core.bundle.get("{formatted_name}.name", "{name}");
            description = Core.bundle.get("{formatted_name}.description", "");
        }}}};'''
                        content = content[:open_brace+1] + liquid_code + content[open_brace+1:]
                
                file_path.write_text(content, encoding='utf-8')
                
                return {"success": True, "message": f"Жидкость '{name}' создана"}
            else:
                return {"success": False, "error": f"Жидкость '{name}' уже существует"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _compile_mod(self, callback_id=None):
        import queue
        log_queue = queue.Queue()
        
        def send_log(message, level="info"):
            if callback_id:
                try:
                    eel.send_compile_log(callback_id, message, level)()
                except:
                    pass
        
        def compile_thread():
            original_cwd = os.getcwd()
            try:
                send_log("="*60, "header")
                send_log(LangT("compile_mod_start_text"), "header")
                send_log(f"📁 Mod: {self.mod_name}", "info")
                
                os.chdir(str(self.mod_folder))
                gradle = "gradlew.bat" if platform.system() == "Windows" else "./gradlew"
                
                if not Path(gradle).exists():
                    send_log(f"❌ {gradle} не найден!", "error")
                    return
                
                send_log(LangT("start_gradle"), "header")
                
                creation_flags = 0
                if platform.system() == "Windows":
                    creation_flags = subprocess.CREATE_NO_WINDOW
                
                process = subprocess.Popen(
                    [gradle, "jar"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    bufsize=1,
                    creationflags=creation_flags,
                    shell=True if platform.system() == "Windows" else False
                )
                
                for line in process.stdout:
                    if line.strip():
                        send_log(line.strip(), "gradle")
                
                return_code = process.wait()
                
                os.chdir(original_cwd)
                
                if return_code == 0:
                    send_log(LangT("compilation_end_yes"), "success")
                    jar_files = list(self.mod_folder.glob("build/libs/*.jar"))
                    if jar_files:
                        send_log(f"📦 JAR: {jar_files[0].name}", "success")
                        self.move_and_rename_file()
                        send_log(LangT("jar_teleporte"), "success")
                else:
                    send_log(LangT("Compilatiom_error").format(e1=return_code), "error")
                
                send_log(LangT("compile_mod_end_text"), "header")
            except Exception as e:
                send_log(LangT("error: {e}").format(e=e), "error")
            finally:
                if callback_id:
                    time.sleep(1)
                    try:
                        eel.compile_completed(callback_id)()
                    except:
                        pass
        
        threading.Thread(target=compile_thread, daemon=True).start()
        return {"status": "started", "callback_id": callback_id}

    def _get_textures_tree_data(self):
        textures_root = self.mod_folder / "assets" / "sprites"
        return {"rootPath": str(textures_root), "exists": textures_root.exists()}

    def _get_texture_folder_content(self, folder_path):
        folder = Path(folder_path)
        print(f"Получение содержимого папки: {folder_path}")
        
        if not folder.exists():
            print(f"Папка не существует: {folder_path}")
            return []
        
        items = []
        for item in sorted(folder.iterdir()):
            try:
                # Возвращаем только имя файла, а не полный путь
                # Полный путь будем формировать в JavaScript
                if item.is_dir():
                    try:
                        item_count = len(list(item.iterdir()))
                    except:
                        item_count = 0
                    items.append({
                        "type": "folder",
                        "name": item.name,
                        "path": item.name,  # Только имя
                        "fullPath": str(item).replace('\\', '/'),  # Полный путь для операций
                        "itemCount": item_count
                    })
                elif item.suffix.lower() in ['.png', '.jpg', '.jpeg', '.gif']:
                    width, height = 0, 0
                    try:
                        with Image.open(item) as img:
                            width, height = img.size
                    except:
                        pass
                    items.append({
                        "type": "texture",
                        "name": item.name,
                        "path": item.name,  # Только имя
                        "fullPath": str(item).replace('\\', '/'),  # Полный путь для операций
                        "width": width,
                        "height": height
                    })
            except Exception as e:
                print(f"Ошибка обработки {item}: {e}")
                continue
        
        print(f"Всего элементов: {len(items)}")
        return items

    def _get_texture_base64(self, texture_path):
        path = Path(texture_path)
        if not path.exists():
            return None
        try:
            with Image.open(path) as img:
                img.thumbnail((50, 50), Image.Resampling.LANCZOS)
                buffer = BytesIO()
                img.save(buffer, format='PNG')
                return f"data:image/png;base64,{base64.b64encode(buffer.getvalue()).decode()}"
        except:
            return None

    def _get_translations_data(self):
        bundles_dir = self.mod_folder / "assets" / "bundles"
        bundles_dir.mkdir(parents=True, exist_ok=True)
        
        en_names, en_descs = {}, {}
        ru_names, ru_descs = {}, {}
        
        en_path = bundles_dir / "bundle.properties"
        if en_path.exists():
            for line in en_path.read_text(encoding='utf-8').split('\n'):
                if '=' in line and not line.startswith('#'):
                    k, v = line.split('=', 1)
                    k, v = k.strip(), v.strip()
                    if k.endswith('.description'):
                        en_descs[k] = v
                    else:
                        en_names[k] = v
        
        ru_path = bundles_dir / "bundle_ru.properties"
        if ru_path.exists():
            for line in ru_path.read_text(encoding='utf-8').split('\n'):
                if '=' in line and not line.startswith('#'):
                    k, v = line.split('=', 1)
                    k, v = k.strip(), v.strip()
                    if k.endswith('.description'):
                        ru_descs[k] = v
                    else:
                        ru_names[k] = v
        
        return {
            "success": True,
            "data": {
                "en": {"names": en_names, "descriptions": en_descs},
                "ru": {"names": ru_names, "descriptions": ru_descs}
            }
        }

    def _auto_search_translations(self):
        mod_name_lower = self.mod_name.lower()
        found_items = {}
        
        search_configs = [
            {"type": "item", "class": "Item", "path": f"src/{mod_name_lower}/init/items/ModItems.java"},
            {"type": "liquid", "class": "Liquid", "path": f"src/{mod_name_lower}/init/liquids/ModLiquid.java"},
        ]
        
        for config in search_configs:
            file_path = self.mod_folder / config["path"]
            if file_path.exists():
                content = file_path.read_text(encoding='utf-8')
                patterns = [
                    rf'public\s+static\s+{config["class"]}\s+(\w+);',
                    rf'(\w+)\s*=\s*new\s+{config["class"]}\("[^"]*"\)',
                ]
                for pattern in patterns:
                    matches = re.findall(pattern, content)
                    for match in matches:
                        if isinstance(match, str):
                            for item in [i.strip() for i in match.split(',')]:
                                if item and item not in found_items:
                                    found_items[item] = {"type": config["type"]}
        
        en_names = {f"{item}.name": item.replace("_", " ").title() for item in found_items}
        
        return {
            "success": True,
            "data": {
                "en": {"names": en_names, "descriptions": {}},
                "ru": {"names": en_names.copy(), "descriptions": {}}
            },
            "foundCount": len(found_items)
        }

    def _save_bundle_files(self, data):
        bundles_dir = self.mod_folder / "assets" / "bundles"
        bundles_dir.mkdir(parents=True, exist_ok=True)
        
        en_lines = []
        for k, v in sorted(data.get('en_names', {}).items()):
            if v:
                en_lines.append(f"{k}={v}")
        for k, v in sorted(data.get('en_descriptions', {}).items()):
            if v:
                en_lines.append(f"{k}={v}")
        (bundles_dir / "bundle.properties").write_text('\n'.join(en_lines), encoding='utf-8')
        
        ru_lines = []
        for k, v in sorted(data.get('ru_names', {}).items()):
            if v:
                ru_lines.append(f"{k}={v}")
        for k, v in sorted(data.get('ru_descriptions', {}).items()):
            if v:
                ru_lines.append(f"{k}={v}")
        (bundles_dir / "bundle_ru.properties").write_text('\n'.join(ru_lines), encoding='utf-8')
        
        return {"success": True}

    def upload_and_save_icon(self, base64_data, original_filename, target_path, target_name):
        try:
            image_data = base64.b64decode(base64_data)
            image = Image.open(BytesIO(image_data))
            if image.format != 'PNG':
                output = BytesIO()
                image.save(output, format='PNG')
                image_data = output.getvalue()
            
            target_folder = Path(target_path)
            target_folder.mkdir(parents=True, exist_ok=True)
            full_path = target_folder / f"{target_name}.png"
            with open(full_path, 'wb') as f:
                f.write(image_data)
            
            return {"success": True, "message": f"Иконка сохранена как {target_name}.png", "path": str(full_path)}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _create_texture_folder(self, parent_path, folder_name):
        """Создаёт новую папку в указанной директории текстур"""
        try:
            parent = Path(parent_path)
            if not parent.exists():
                return {"success": False, "error": "Родительская папка не найдена"}
            
            clean_name = re.sub(r'[<>:"/\\|?*]', '_', folder_name.strip())
            if not clean_name:
                return {"success": False, "error": "Некорректное имя папки"}
            
            new_folder = parent / clean_name
            if new_folder.exists():
                return {"success": False, "error": f"Папка '{clean_name}' уже существует"}
            
            new_folder.mkdir(parents=True, exist_ok=True)
            return {"success": True, "message": f"Папка '{clean_name}' создана", "path": str(new_folder)}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _upload_texture_file(self, target_path, base64_data, filename):
        """Загружает PNG файл в указанную папку текстур"""
        try:
            target = Path(target_path)
            if not target.exists():
                return {"success": False, "error": "Целевая папка не найдена"}
            
            image_data = base64.b64decode(base64_data)
            image = Image.open(BytesIO(image_data))
            if image.format != 'PNG':
                return {"success": False, "error": "Файл должен быть в формате PNG"}
            
            clean_name = re.sub(r'[<>:"/\\|?*]', '_', filename.strip())
            if not clean_name:
                clean_name = "texture.png"
            if not clean_name.lower().endswith('.png'):
                clean_name += '.png'
            
            file_path = target / clean_name
            if file_path.exists():
                base = file_path.stem
                ext = file_path.suffix
                counter = 1
                while file_path.exists():
                    file_path = target / f"{base}_{counter}{ext}"
                    counter += 1
            
            with open(file_path, 'wb') as f:
                f.write(image_data)
            
            return {"success": True, "message": f"Файл '{file_path.name}' загружен", "path": str(file_path)}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _rename_texture_item(self, old_path, new_name):
        """Переименовывает файл или папку в текстурах"""
        try:
            old = Path(old_path)
            if not old.exists():
                return {"success": False, "error": "Элемент не найден"}
            
            clean_name = re.sub(r'[<>:"/\\|?*]', '_', new_name.strip())
            if not clean_name:
                return {"success": False, "error": "Некорректное имя"}
            
            parent = old.parent
            new_path = parent / clean_name
            
            if new_path.exists():
                return {"success": False, "error": f"Элемент с именем '{clean_name}' уже существует"}
            
            old.rename(new_path)
            return {"success": True, "message": f"Переименован в '{clean_name}'", "new_path": str(new_path)}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _delete_texture_item(self, item_path):
        """Удаляет файл или папку из текстур"""
        try:
            # Очищаем путь от невидимых символов и нормализуем
            import re
            # Удаляем невидимые символы (кроме пробелов)
            item_path = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', item_path)
            # Заменяем обратные слеши на прямые
            item_path = item_path.replace('\\', '/')
            # Удаляем лишние пробелы
            item_path = item_path.strip()
            
            print(f"Очищенный путь: {item_path}")
            
            # Пробуем найти файл в папке текстур по имени
            textures_root = self.mod_folder / "assets" / "sprites"
            
            # Если путь содержит только имя файла, ищем его в папке текстур
            if '/' not in item_path and '\\' not in item_path:
                print(f"Ищем файл по имени: {item_path}")
                for root, dirs, files in os.walk(textures_root):
                    for f in files:
                        if f == item_path:
                            full_path = Path(root) / f
                            print(f"Найден файл: {full_path}")
                            item = full_path
                            break
                    if 'item' in locals() and item.exists():
                        break
                else:
                    return {"success": False, "error": f"Файл не найден: {item_path}"}
            else:
                item = Path(item_path)
            
            print(f"Итоговый путь для удаления: {item}")
            print(f"Существует: {item.exists()}")
            
            if not item.exists():
                return {"success": False, "error": f"Элемент не найден: {item_path}"}
            
            # Защита от удаления корневой папки
            if str(item).lower() == str(textures_root).lower():
                return {"success": False, "error": "Нельзя удалить корневую папку текстур"}
            
            # Проверяем, что элемент внутри папки текстур
            if str(textures_root) not in str(item.parent):
                return {"success": False, "error": "Можно удалять только файлы внутри папки текстур"}
            
            if item.is_dir():
                shutil.rmtree(item)
                print(f"Папка удалена: {item}")
            else:
                item.unlink()
                print(f"Файл удалён: {item}")
            
            return {"success": True, "message": f"Элемент '{item.name}' удалён"}
        except PermissionError as e:
            return {"success": False, "error": f"Нет прав доступа: {str(e)}"}
        except Exception as e:
            print(f"Ошибка удаления: {e}")
            import traceback
            traceback.print_exc()
            return {"success": False, "error": str(e)}
    
    def _get_source_files(self, rel_path=""):
        """Получает список файлов - принимает ОТНОСИТЕЛЬНЫЙ путь"""
        mod_name_lower = self.mod_name.lower()
        src_root = self.mod_folder / "src" / mod_name_lower
        
        # Сохраняем текущий относительный путь
        self._current_source_path = rel_path
        
        # Если путь пустой - используем корень
        if not rel_path or rel_path.strip() == "":
            current_path = src_root
            self._current_source_path = ""
        else:
            # Очищаем путь от лишних слешей
            clean_path = rel_path.replace('\\', '/').strip('/')
            current_path = src_root / clean_path
        
        # Если путь не существует - возвращаем корень
        if not current_path.exists():
            current_path = src_root
            self._current_source_path = ""
            if not current_path.exists():
                return {"success": False, "error": "Корневая папка не найдена"}
        
        items = []
        for item in sorted(current_path.iterdir()):
            try:
                if item.is_dir():
                    item_count = len(list(item.iterdir())) if item.exists() else 0
                    # Сохраняем и полный путь, и имя для относительного пути
                    items.append({
                        "type": "folder",
                        "name": item.name,
                        "path": str(item).replace('\\', '/'),  # Полный путь для операций
                        "relPath": str(item.relative_to(src_root)).replace('\\', '/'),  # Относительный путь
                        "itemCount": item_count
                    })
                else:
                    items.append({
                        "type": "file",
                        "name": item.name,
                        "path": str(item).replace('\\', '/'),  # Полный путь
                        "size": item.stat().st_size
                    })
            except Exception as e:
                print(f"Ошибка обработки {item}: {e}")
                continue
        
        # Возвращаем ОТНОСИТЕЛЬНЫЙ путь для отображения
        rel_current = str(current_path.relative_to(src_root)).replace('\\', '/')
        if rel_current == '.':
            rel_current = ''
        
        return {
            "success": True,
            "files": items,
            "currentPath": rel_current,  # Относительный путь
            "rootPath": str(src_root).replace('\\', '/')
        }

    def _get_source_file_content(self, file_path):
        """Читает содержимое файла по полному пути"""
        full_path = Path(file_path)
        
        if not full_path.exists():
            return {"success": False, "error": "Файл не найден"}
        
        try:
            content = full_path.read_text(encoding='utf-8')
            return {"success": True, "content": content, "filename": full_path.name}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _create_java_file(self, class_name):
        """
        Создает новый Java файл в текущей папке
        """
        try:
            import re
            from pathlib import Path
            
            mod_name_lower = self.mod_name.lower()
            
            # Получаем текущий путь
            if not hasattr(self, '_current_source_path'):
                self._current_source_path = ""
            
            rel_path = self._current_source_path or ""
            src_root = self.mod_folder / "src" / mod_name_lower
            
            if rel_path:
                current_path = src_root / rel_path.replace('\\', '/').strip('/')
            else:
                current_path = src_root
            
            if not current_path.exists():
                current_path.mkdir(parents=True, exist_ok=True)
            
            # Очищаем имя класса
            clean_name = re.sub(r'[^a-zA-Z0-9_]', '', class_name.strip())
            if not clean_name:
                return {"success": False, "error": "Некорректное имя класса"}
            
            # Проверяем, существует ли уже файл
            file_path = current_path / f"{clean_name}.java"
            if file_path.exists():
                return {"success": False, "error": f"Файл '{clean_name}.java' уже существует"}
            
            # Создаем содержимое Java файла
            # Определяем пакет
            package_parts = []
            if rel_path:
                package_parts = rel_path.replace('\\', '/').strip('/').split('/')
            
            # Убираем имя мода из пакета, если оно есть
            package_name = mod_name_lower
            if package_parts:
                # Проверяем, не является ли первая часть именем мода
                if package_parts[0] == mod_name_lower:
                    package_parts = package_parts[1:]
                if package_parts:
                    package_name = f"{mod_name_lower}.{'.'.join(package_parts)}"
            
            # Базовый шаблон класса
            java_content = f"""package {package_name};

    import arc.*;
    import arc.util.*;
    import mindustry.*;
    import mindustry.gen.*;
    import mindustry.mod.*;
    import mindustry.world.*;
    import mindustry.type.*;

    public class {clean_name} {{
        
        public {clean_name}() {{
            // Конструктор
        }}
        
        public void init() {{
            // Инициализация
        }}
    }}
    """
            
            # Записываем файл
            file_path.write_text(java_content, encoding='utf-8')
            
            return {"success": True, "message": f"Файл '{clean_name}.java' создан", "filePath": str(file_path).replace('\\', '/')}
            
        except Exception as e:
            print(f"Ошибка создания Java файла: {e}")
            import traceback
            traceback.print_exc()
            return {"success": False, "error": str(e)}
    
    def _rename_source_file(self, old_path, new_name):
        """Переименовывает файл в исходных кодах"""
        try:
            from pathlib import Path
            
            old = Path(old_path)
            if not old.exists():
                return {"success": False, "error": "Файл не найден"}
            
            if old.is_dir():
                return {"success": False, "error": "Указанный путь является папкой, а не файлом"}
            
            # Проверяем расширение
            old_ext = old.suffix
            new_name_clean = new_name.strip()
            
            # Если новое имя не имеет расширения, добавляем старое
            if not Path(new_name_clean).suffix:
                new_name_clean += old_ext
            
            clean_name = re.sub(r'[<>:"/\\|?*]', '_', new_name_clean)
            if not clean_name:
                return {"success": False, "error": "Некорректное имя файла"}
            
            parent = old.parent
            new_path = parent / clean_name
            
            if new_path.exists():
                return {"success": False, "error": f"Файл с именем '{clean_name}' уже существует"}
            
            old.rename(new_path)
            
            return {"success": True, "message": f"Файл переименован в '{clean_name}'", "new_path": str(new_path)}
            
        except Exception as e:
            print(f"Ошибка переименования файла в source: {e}")
            import traceback
            traceback.print_exc()
            return {"success": False, "error": str(e)}

    def _delete_source_file(self, file_path):
        """Удаляет файл из исходных кодов"""
        try:
            from pathlib import Path
            
            file = Path(file_path)
            if not file.exists():
                return {"success": False, "error": "Файл не найден"}
            
            if file.is_dir():
                return {"success": False, "error": "Указанный путь является папкой, а не файлом"}
            
            # Защита от удаления важных файлов
            mod_name_lower = self.mod_name.lower()
            src_root = self.mod_folder / "src" / mod_name_lower
            
            # Проверяем, что файл внутри src
            if str(src_root) not in str(file.parent):
                return {"success": False, "error": "Можно удалять только файлы внутри папки src"}
            
            # Проверяем, не является ли файл главным классом мода
            main_class_name = f"{mod_name_lower.capitalize()}JavaMod.java"
            if file.name == main_class_name:
                return {"success": False, "error": f"Нельзя удалить главный класс мода: {main_class_name}"}
            
            # Удаляем файл
            file.unlink()
            print(f"Файл удалён: {file}")
            
            return {"success": True, "message": f"Файл '{file.name}' удалён"}
            
        except PermissionError as e:
            return {"success": False, "error": f"Нет прав доступа: {str(e)}"}
        except Exception as e:
            print(f"Ошибка удаления файла в source: {e}")
            import traceback
            traceback.print_exc()
            return {"success": False, "error": str(e)}

# ===================== EEL ФУНКЦИИ =====================

@eel.expose
def get_settings():
    return settings

@eel.expose
def save_settings_api(language, save_folder):
    global settings
    settings["language"] = language
    settings["save_folder"] = save_folder
    save_settings()
    return {"success": True}

@eel.expose
def get_free_game_path():
    appdata = os.getenv('APPDATA') or os.path.expanduser("~")
    return os.path.join(appdata, "Mindustry", "mods") if appdata else MODS_WORK_DIR

@eel.expose
def get_mods():
    return get_mods_list()

@eel.expose
def create_mod(mod_name):
    result = create_mod_folder(mod_name)
    if result["success"]:
        download_template(mod_name)
        return {"success": True, "mod_name": mod_name}
    return result

@eel.expose
def delete_mod_api(mod_name):
    return delete_mod(mod_name)

@eel.expose
def get_java_status():
    return check_java()

@eel.expose
def open_in_editor(mod_name):
    global current_editor
    mod_path = Path(MODS_WORK_DIR) / mod_name
    if not mod_path.exists():
        return {"success": False, "error": "Мод не найден"}
    current_editor = CreatorEditor(mod_path, mod_name)
    return {"success": True, "mod_name": mod_name, "mod_path": str(mod_path)}

# Функции редактора
@eel.expose
def editor_get_mod_folder():
    return str(current_editor.mod_folder) if current_editor else ""

@eel.expose
def editor_get_blocks_list():
    return current_editor._get_all_blocks_data() if current_editor else []

@eel.expose
def editor_get_textures_tree():
    return current_editor._get_textures_tree_data() if current_editor else {"rootPath": "", "exists": False}

@eel.expose
def editor_get_texture_folder_content(path):
    return current_editor._get_texture_folder_content(path) if current_editor else []

@eel.expose
def editor_get_texture_image(texture_path):
    return current_editor._get_texture_base64(texture_path) if current_editor else None

@eel.expose
def editor_open_file_externally(file_path):
    try:
        if platform.system() == 'Windows':
            os.startfile(file_path)
        elif platform.system() == 'Darwin':
            subprocess.run(['open', file_path])
        else:
            subprocess.run(['xdg-open', file_path])
        return {"success": True}
    except:
        return {"success": False}

@eel.expose
def editor_delete_block(block_name, block_type):
    return current_editor._delete_block_by_name(block_name, block_type) if current_editor else {"success": False}

@eel.expose
def editor_create_item_from_web(item_data):
    return current_editor._create_item(item_data) if current_editor else {"success": False}

@eel.expose
def editor_create_liquid_from_web(liquid_data):
    return current_editor._create_liquid(liquid_data) if current_editor else {"success": False}

@eel.expose
def editor_compile_mod_web(callback_id=None):
    return current_editor._compile_mod(callback_id) if current_editor else {"status": "error"}

@eel.expose
def editor_open_mod_folder():
    if current_editor:
        try:
            os.startfile(current_editor.mod_folder)
        except:
            pass
    return

@eel.expose
def editor_get_translations_data():
    return current_editor._get_translations_data() if current_editor else {"success": False}

@eel.expose
def editor_auto_search_translations():
    return current_editor._auto_search_translations() if current_editor else {"success": False}

@eel.expose
def editor_save_bundle_files(data):
    return current_editor._save_bundle_files(data) if current_editor else {"success": False}

@eel.expose
def editor_upload_and_save_icon(base64_data, original_filename, target_path, target_name):
    return current_editor.upload_and_save_icon(base64_data, original_filename, target_path, target_name) if current_editor else {"success": False}

# Функции для логов компиляции
@eel.expose
def send_compile_log(callback_id, message, level):
    pass

@eel.expose
def compile_completed(callback_id):
    pass

@eel.expose
def editor_create_texture_folder(parent_path, folder_name):
    return current_editor._create_texture_folder(parent_path, folder_name) if current_editor else {"success": False}

@eel.expose
def editor_upload_texture_file(target_path, base64_data, filename):
    return current_editor._upload_texture_file(target_path, base64_data, filename) if current_editor else {"success": False}

@eel.expose
def editor_rename_texture_item(old_path, new_name):
    return current_editor._rename_texture_item(old_path, new_name) if current_editor else {"success": False}

@eel.expose
def editor_delete_texture_item(item_path):
    print(f"editor_delete_texture_item вызван с параметром: {item_path}")  # Отладка
    if current_editor is None:
        print("current_editor is None!")  # Отладка
        return {"success": False, "error": "Редактор не инициализирован"}
    
    result = current_editor._delete_texture_item(item_path)
    print(f"Результат: {result}")  # Отладка
    return result

@eel.expose
def editor_get_source_files(path=""):
    """Получает список файлов в папке source"""
    if current_editor is None:
        return {"success": False, "error": "Редактор не инициализирован"}
    return current_editor._get_source_files(path)

@eel.expose
def editor_open_source_folder(path):
    """Открывает папку в source - принимает относительный путь"""
    if current_editor is None:
        return {"success": False, "error": "Редактор не инициализирован"}
    return current_editor._get_source_files(path)

@eel.expose
def editor_get_source_file_content(file_path):
    """Читает содержимое файла"""
    if current_editor is None:
        return {"success": False, "error": "Редактор не инициализирован"}
    return current_editor._get_source_file_content(file_path)

@eel.expose
def editor_create_source_folder(folder_name):
    """
    Создает папку в текущей директории исходных кодов
    """
    try:
        from pathlib import Path
        
        if current_editor is None:
            return {"success": False, "error": "Редактор не инициализирован"}
        
        # Получаем текущий относительный путь из редактора
        # Для этого нужно сохранять текущий путь при навигации
        # Используем атрибут объекта редактора
        if not hasattr(current_editor, '_current_source_path'):
            current_editor._current_source_path = ""
        
        rel_path = current_editor._current_source_path or ""
        
        # Формируем полный путь
        mod_name_lower = current_editor.mod_name.lower()
        src_root = current_editor.mod_folder / "src" / mod_name_lower
        
        if rel_path:
            current_path = src_root / rel_path.replace('\\', '/').strip('/')
        else:
            current_path = src_root
        
        # Создаем новую папку
        clean_name = re.sub(r'[<>:"/\\|?*]', '_', folder_name.strip())
        if not clean_name:
            return {"success": False, "error": "Некорректное имя папки"}
        
        new_folder = current_path / clean_name
        
        if new_folder.exists():
            return {"success": False, "error": f"Папка '{clean_name}' уже существует"}
        
        new_folder.mkdir(parents=True, exist_ok=True)
        
        return {"success": True, "message": f"Папка '{clean_name}' создана", "path": str(new_folder)}
        
    except Exception as e:
        print(f"Ошибка создания папки в source: {e}")
        import traceback
        traceback.print_exc()
        return {"success": False, "error": str(e)}

@eel.expose
def editor_rename_source_folder(old_path, new_name):
    """
    Переименовывает папку в исходных кодах
    """
    try:
        from pathlib import Path
        
        if current_editor is None:
            return {"success": False, "error": "Редактор не инициализирован"}
        
        old = Path(old_path)
        if not old.exists():
            return {"success": False, "error": "Папка не найдена"}
        
        if not old.is_dir():
            return {"success": False, "error": "Указанный путь не является папкой"}
        
        clean_name = re.sub(r'[<>:"/\\|?*]', '_', new_name.strip())
        if not clean_name:
            return {"success": False, "error": "Некорректное имя папки"}
        
        parent = old.parent
        new_path = parent / clean_name
        
        if new_path.exists():
            return {"success": False, "error": f"Папка с именем '{clean_name}' уже существует"}
        
        old.rename(new_path)
        
        # Обновляем текущий путь в редакторе, если он был внутри переименованной папки
        if hasattr(current_editor, '_current_source_path') and current_editor._current_source_path:
            current_path = current_editor._current_source_path.replace('\\', '/')
            old_name = old.name
            if old_name in current_path:
                # Обновляем путь в стеке навигации
                current_editor._current_source_path = current_path.replace(old_name, clean_name, 1)
        
        return {"success": True, "message": f"Папка переименована в '{clean_name}'", "new_path": str(new_path)}
        
    except Exception as e:
        print(f"Ошибка переименования папки в source: {e}")
        import traceback
        traceback.print_exc()
        return {"success": False, "error": str(e)}

@eel.expose
def editor_delete_source_folder(folder_path):
    """
    Удаляет папку из исходных кодов
    """
    try:
        from pathlib import Path
        import shutil
        
        if current_editor is None:
            return {"success": False, "error": "Редактор не инициализирован"}
        
        # Нормализуем путь
        folder_path = folder_path.replace('\\', '/').strip()
        print(f"Удаление папки: {folder_path}")
        
        folder = Path(folder_path)
        if not folder.exists():
            return {"success": False, "error": "Папка не найдена"}
        
        if not folder.is_dir():
            return {"success": False, "error": "Указанный путь не является папкой"}
        
        # Защита от удаления корневой папки
        mod_name_lower = current_editor.mod_name.lower()
        src_root = current_editor.mod_folder / "src" / mod_name_lower
        
        if str(folder).lower() == str(src_root).lower():
            return {"success": False, "error": "Нельзя удалить корневую папку src"}
        
        # Проверяем, что папка внутри src
        if str(src_root) not in str(folder.parent):
            return {"success": False, "error": "Можно удалять только папки внутри src"}
        
        # Удаляем папку
        shutil.rmtree(folder)
        print(f"Папка удалена: {folder}")
        
        # Сбрасываем текущий путь, если он был внутри удалённой папки
        if hasattr(current_editor, '_current_source_path'):
            current_path = current_editor._current_source_path.replace('\\', '/')
            if current_path.startswith(folder.name) or f"/{folder.name}" in current_path:
                current_editor._current_source_path = ""
        
        return {"success": True, "message": f"Папка '{folder.name}' удалена"}
        
    except PermissionError as e:
        return {"success": False, "error": f"Нет прав доступа: {str(e)}"}
    except Exception as e:
        print(f"Ошибка удаления папки в source: {e}")
        import traceback
        traceback.print_exc()
        return {"success": False, "error": str(e)}
    
@eel.expose
def editor_save_source_file(file_path, content):
    """
    Сохраняет содержимое файла исходного кода
    """
    try:
        from pathlib import Path
        
        if current_editor is None:
            return {"success": False, "error": "Редактор не инициализирован"}
        
        full_path = Path(file_path)
        if not full_path.exists():
            return {"success": False, "error": "Файл не найден"}
        
        # Проверяем, что файл находится в папке мода
        mod_name_lower = current_editor.mod_name.lower()
        src_root = current_editor.mod_folder / "src" / mod_name_lower
        
        if str(src_root) not in str(full_path.parent):
            return {"success": False, "error": "Можно редактировать только файлы внутри папки src"}
        
        # Сохраняем файл
        full_path.write_text(content, encoding='utf-8')
        
        return {"success": True, "message": f"Файл '{full_path.name}' сохранён"}
        
    except Exception as e:
        print(f"Ошибка сохранения файла: {e}")
        import traceback
        traceback.print_exc()
        return {"success": False, "error": str(e)}

@eel.expose
def editor_create_java_file(class_name):
    """
    Создает новый Java файл в текущей папке исходных кодов
    """
    if current_editor is None:
        return {"success": False, "error": "Редактор не инициализирован"}
    return current_editor._create_java_file(class_name)

@eel.expose
def editor_rename_source_file(old_path, new_name):
    """
    Переименовывает файл в исходных кодах
    """
    if current_editor is None:
        return {"success": False, "error": "Редактор не инициализирован"}
    return current_editor._rename_source_file(old_path, new_name)

@eel.expose
def editor_delete_source_file(file_path):
    """
    Удаляет файл из исходных кодов
    """
    print(f"editor_delete_source_file вызван с параметром: {file_path}")
    if current_editor is None:
        return {"success": False, "error": "Редактор не инициализирован"}
    return current_editor._delete_source_file(file_path)

# ===================== ЗАПУСК =====================
def start_eel():
    Path(MODS_WORK_DIR).mkdir(parents=True, exist_ok=True)
    load_settings()
    webpath = resource_path("Creator/ui/web")
    eel.init(webpath, allowed_extensions=['.js', '.html'])
    eel.start("manager.html", port=8000, size=(1200, 1000))

if __name__ == "__main__":
    print("="*50)
    print("ЗАПУСК Mindustry Mod Creator")
    print("="*50)
    start_eel()