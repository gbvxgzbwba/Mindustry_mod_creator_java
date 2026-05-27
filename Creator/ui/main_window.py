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
        if not folder.exists():
            return []
        items = []
        for item in sorted(folder.iterdir()):
            if item.is_dir():
                try:
                    item_count = len(list(item.iterdir()))
                except:
                    item_count = 0
                items.append({
                    "type": "folder",
                    "name": item.name,
                    "path": str(item),
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
                    "path": str(item),
                    "width": width,
                    "height": height
                })
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

# ===================== ЗАПУСК =====================
def start_eel():
    Path(MODS_WORK_DIR).mkdir(parents=True, exist_ok=True)
    load_settings()
    webpath = resource_path("Creator/ui/web")
    eel.init(webpath, allowed_extensions=['.js', '.html'])
    eel.start("manager.html", port=8000, mode='default')

if __name__ == "__main__":
    print("="*50)
    print("ЗАПУСК Mindustry Mod Creator")
    print("="*50)
    start_eel()