import os
import re
from pathlib import Path
import shutil

# Путь к модулю (устанавливается автоматически)
MODULE_PATH = None
EDITOR_INSTANCE = None

def set_module_path(path):
    global MODULE_PATH
    MODULE_PATH = Path(path)

def set_editor(editor):
    global EDITOR_INSTANCE
    EDITOR_INSTANCE = editor

def create_wall(data=None):
    """Создаёт стену в текущем открытом моде"""
    if not data:
        return {"success": False, "error": "Нет данных"}
    
    wall_name = data.get('wall_name', '').strip()
    if not wall_name:
        return {"success": False, "error": "Введите название стены"}
    
    # Проверяем имя
    if not re.match(r'^[a-zA-Z][a-zA-Z0-9_]*$', wall_name):
        return {"success": False, "error": "Имя должно начинаться с буквы и содержать только буквы, цифры и подчеркивание"}
    
    # АВТОМАТИЧЕСКИ ОПРЕДЕЛЯЕМ МОД
    editor = EDITOR_INSTANCE
    if not editor:
        return {"success": False, "error": "Откройте мод сначала!"}
    
    try:
        mod_name_lower = editor.mod_name.lower()
        mod_folder = editor.mod_folder
        
        # Создаём папку для стен
        wall_dir = mod_folder / "src" / mod_name_lower / "init" / "walls"
        wall_dir.mkdir(parents=True, exist_ok=True)
        
        # Путь к файлу walls.java
        walls_file = wall_dir / "walls.java"
        
        # Проверяем, существует ли файл walls.java
        if walls_file.exists():
            content = walls_file.read_text(encoding='utf-8')
            
            # Проверяем, есть ли уже такая стена
            if f"public static Wall " in content and wall_name in content:
                if re.search(r'public static Wall[^;]*\b' + wall_name + r'\b', content):
                    return {"success": False, "error": f"Стена '{wall_name}' уже существует в walls.java"}
            
            # Обновляем поле public static Wall - добавляем новое имя через запятую
            lines = content.split('\n')
            
            # Находим строку с public static Wall
            found = False
            for i, line in enumerate(lines):
                if "public static Wall " in line and ";" in line:
                    # Убираем точку с запятой, добавляем запятую и новое имя
                    current_line = line.rstrip(';')
                    if not current_line.endswith(','):
                        current_line += ','
                    lines[i] = current_line + ' ' + wall_name + ';'
                    found = True
                    break
            
            if not found:
                # Если не нашли, создаём новую строку
                for i, line in enumerate(lines):
                    if "public class walls {" in line:
                        lines.insert(i + 1, f"    public static Wall {wall_name};")
                        break
            
            # Добавляем инициализацию в метод Load() с двойными скобками {{{{
            init_code = f'''        {wall_name} = new Wall("{wall_name}") {{{{
            localizedName = Core.bundle.get("{wall_name}.name", "{wall_name.capitalize()} Wall");
            description = Core.bundle.get("{wall_name}.description", "A strong defensive wall.");
            requirements(Category.defense, ItemStack.with());
            health = {data.get('health', 100)};
            size = {data.get('size', 1)};
            alwaysUnlocked = {'true' if data.get('always_unlocked') else 'false'};
        }}}};'''
            
            # Находим метод Load()
            load_start = -1
            for i, line in enumerate(lines):
                if "public static void Load()" in line:
                    load_start = i
                    break
            
            if load_start != -1:
                # Находим открывающую скобку метода Load
                open_brace = -1
                for i in range(load_start, len(lines)):
                    if '{' in lines[i]:
                        open_brace = i
                        break
                
                if open_brace != -1:
                    # Находим закрывающую скобку
                    close_brace = -1
                    brace_count = 0
                    for i in range(open_brace, len(lines)):
                        brace_count += lines[i].count('{') - lines[i].count('}')
                        if brace_count == 0:
                            close_brace = i
                            break
                    
                    if close_brace != -1:
                        # Проверяем, не добавлен ли уже этот блок
                        if f'{wall_name} = new Wall("{wall_name}")' not in content:
                            # Вставляем перед закрывающей скобкой
                            lines.insert(close_brace, init_code)
            
            # Сохраняем обновлённый файл
            new_content = '\n'.join(lines)
            walls_file.write_text(new_content, encoding='utf-8')
            
        else:
            # Создаём новый файл walls.java с полными импортами
            walls_content = f'''package {mod_name_lower}.init.walls;

import mindustry.world.blocks.defense.Wall;
import mindustry.type.Category;
import mindustry.type.ItemStack;
import mindustry.content.Items;
import arc.Core;

public class walls {{
    public static Wall {wall_name};

    public static void Load() {{
        {wall_name} = new Wall("{wall_name}") {{{{
            localizedName = Core.bundle.get("{wall_name}.name", "{wall_name.capitalize()} Wall");
            description = Core.bundle.get("{wall_name}.description", "A strong defensive wall.");
            requirements(Category.defense, ItemStack.with());
            health = {data.get('health', 100)};
            size = {data.get('size', 1)};
            alwaysUnlocked = {'true' if data.get('always_unlocked') else 'false'};
        }}}};
    }}
}}
'''
            walls_file.write_text(walls_content, encoding='utf-8')
        
        # Находим главный файл мода
        main_file = None
        mod_name_capitalized = editor.mod_name.capitalize()
        main_class_name = f"{mod_name_capitalized}JavaMod"
        
        # Ищем файл с классом JavaMod
        src_dir = mod_folder / "src" / mod_name_lower
        for file in src_dir.glob("*.java"):
            content = file.read_text(encoding='utf-8')
            if f"class {main_class_name}" in content or f"class {mod_name_capitalized}Mod" in content:
                main_file = file
                break
        
        # Если не нашли, ищем любой файл с extends Mod
        if not main_file:
            for file in src_dir.glob("*.java"):
                content = file.read_text(encoding='utf-8')
                if "extends Mod" in content:
                    main_file = file
                    break
        
        if main_file:
            content = main_file.read_text(encoding='utf-8')
            lines = content.split('\n')
            
            # Добавляем импорт - исправлено!
            import_line = f"import {mod_name_lower}.init.walls.walls;"
            if import_line not in content:
                import_index = -1
                for i, line in enumerate(lines):
                    if line.startswith('import ') and not line.startswith('import java'):
                        import_index = i
                
                if import_index != -1:
                    lines.insert(import_index + 1, import_line)
                else:
                    # Если нет импортов, вставляем после package
                    for i, line in enumerate(lines):
                        if line.startswith('package '):
                            lines.insert(i + 1, '\n' + import_line)
                            break
            
            # Добавляем вызов Load() в loadContent
            load_call = "        walls.Load(); // Load walls"
            
            # Проверяем, есть ли уже вызов
            if "walls.Load()" not in content:
                # Ищем метод loadContent
                load_content_start = -1
                for i, line in enumerate(lines):
                    if "public void loadContent()" in line:
                        load_content_start = i
                        break
                
                if load_content_start != -1:
                    # Находим открывающую скобку метода
                    open_brace_idx = -1
                    for i in range(load_content_start, len(lines)):
                        if '{' in lines[i]:
                            open_brace_idx = i
                            break
                    
                    if open_brace_idx != -1:
                        # Находим закрывающую скобку
                        close_brace_idx = -1
                        brace_count = 0
                        for i in range(open_brace_idx, len(lines)):
                            brace_count += lines[i].count('{') - lines[i].count('}')
                            if brace_count == 0:
                                close_brace_idx = i
                                break
                        
                        if close_brace_idx != -1:
                            # Ищем позицию для вставки (после Log.info или в начале)
                            inserted = False
                            for i in range(open_brace_idx + 1, close_brace_idx):
                                if i < len(lines) and "Log.info" in lines[i]:
                                    # Вставляем после строки с Log.info
                                    lines.insert(i + 1, load_call)
                                    inserted = True
                                    break
                            
                            if not inserted:
                                # Вставляем после открывающей скобки
                                lines.insert(open_brace_idx + 1, load_call)
                else:
                    # Если нет метода loadContent, создаём его
                    # Находим конец класса
                    class_end = -1
                    for i in range(len(lines) - 1, -1, -1):
                        if '}' in lines[i] and not lines[i].strip().startswith('//'):
                            class_end = i
                            break
                    
                    if class_end != -1:
                        # Создаём новый метод loadContent
                        load_method = [
                            "",
                            "    @Override",
                            "    public void loadContent(){",
                            "        walls.Load(); // Load walls",
                            "        Log.info(\"Loading some content.\");",
                            "    }"
                        ]
                        # Вставляем перед закрывающей скобкой класса
                        lines[class_end:class_end] = load_method
            
            # Сохраняем обновлённый файл
            main_file.write_text('\n'.join(lines), encoding='utf-8')
        
        # Копируем текстуру-шаблон из папки texture модуля
        # ИМЯ ФАЙЛА: wall_template.png (должен лежать в папке texture рядом с этим скриптом)
        texture_template = MODULE_PATH / "texture" / "wall_template.png"
        if texture_template.exists():
            sprite_dir = mod_folder / "assets" / "sprites" / "walls"
            sprite_dir.mkdir(parents=True, exist_ok=True)
            # Копируем как {wall_name}.png
            shutil.copy2(texture_template, sprite_dir / f"{wall_name}.png")
        else:
            print(f"⚠️ Предупреждение: Файл-шаблон текстуры не найден: {texture_template}")
        
        return {
            "success": True,
            "message": f"✅ Стена '{wall_name}' добавлена в walls.java!",
            "refresh": True
        }
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"success": False, "error": str(e)}