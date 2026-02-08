import customtkinter as ctk
import shutil
import requests
import threading
from pathlib import Path
from tkinter import messagebox
import os
import zipfile
import io
import re

class ModEditor:
    def __init__(self, root, mod_folder, main_app):
        self.root = root
        self.mod_folder = mod_folder
        self.main_app = main_app
        self.mod_name = mod_folder.name
        self.param_index = 0
        self.parameters = [
            ("displayName", "Название мода в игре:", "text"),
            ("name", "Внутреннее имя мода (без пробелов):", "text"),
            ("author", "Автор мода:", "text"),
            ("description", "Описание мода:", "text"),
            ("version", "Версия мода (например: 1.0):", "text"),
            ("minGameVersion", "Минимальная версия игры (например: 154):", "number")
        ]
        self.param_values = {}
        
    def open_mod_editor(self):
        self.clear_window()
        
        # Проверяем существующий mod.hjson
        mod_hjson_path = self.mod_folder / "mod.hjson"
        
        if mod_hjson_path.exists():
            # Файл существует - предлагаем выбор
            ctk.CTkLabel(self.root, text="Редактирование мода", font=("Arial", 20, "bold")).pack(pady=50)
            ctk.CTkLabel(self.root, text=f"Мод: {self.mod_name}", font=("Arial", 16)).pack(pady=10)
            
            # Кнопки выбора
            frame = ctk.CTkFrame(self.root)
            frame.pack(pady=30)
            
            ctk.CTkButton(frame, text="Редактировать существующий mod.hjson", 
                         command=self.edit_existing_hjson, width=200).pack(pady=10, padx=20)
            ctk.CTkButton(frame, text="Скачать новый шаблон", 
                         command=self.download_new_template, width=200).pack(pady=10, padx=20)
            ctk.CTkButton(frame, text="Назад", 
                         command=self.main_app.show_main_ui, width=200, fg_color="gray").pack(pady=20, padx=20)
        else:
            # Файла нет - скачиваем шаблон
            ctk.CTkLabel(self.root, text="Скачивание шаблона", font=("Arial", 20, "bold")).pack(pady=50)
            ctk.CTkLabel(self.root, text=f"Мод: {self.mod_name}", font=("Arial", 16)).pack(pady=10)
            ctk.CTkLabel(self.root, text="Скачиваю и распаковываю...", font=("Arial", 14)).pack(pady=20)
            
            self.root.after(100, self.download_template)
    
    def edit_existing_hjson(self):
        """Редактировать существующий файл mod.hjson"""
        self.clear_window()
        self.start_parameter_input(edit_existing=True)
    
    def download_new_template(self):
        """Скачать новый шаблон"""
        self.clear_window()
        ctk.CTkLabel(self.root, text="Скачивание шаблона", font=("Arial", 20, "bold")).pack(pady=50)
        ctk.CTkLabel(self.root, text=f"Мод: {self.mod_name}", font=("Arial", 16)).pack(pady=10)
        ctk.CTkLabel(self.root, text="Скачиваю и распаковываю...", font=("Arial", 14)).pack(pady=20)
        
        self.root.after(100, self.download_template)
    
    def download_template(self):
        def download_thread():
            try:
                template_url = "https://github.com/Anuken/MindustryModTemplate/archive/refs/heads/master.zip"
                print("Скачиваю и распаковываю шаблон...")
                
                response = requests.get(template_url, timeout=60)
                response.raise_for_status()
                
                zip_data = io.BytesIO(response.content)
                
                with zipfile.ZipFile(zip_data, 'r') as zip_ref:
                    first_file = zip_ref.namelist()[0]
                    root_folder = first_file.split('/')[0]
                    
                    print(f"Извлекаю файлы из {root_folder}...")
                    
                    for file_info in zip_ref.infolist():
                        filename = file_info.filename
                        
                        if filename.startswith(root_folder + '/'):
                            rel_path = filename[len(root_folder) + 1:]
                            
                            if not rel_path or rel_path.endswith('/'):
                                continue
                            
                            target_path = self.mod_folder / rel_path
                            target_path.parent.mkdir(parents=True, exist_ok=True)
                            
                            with zip_ref.open(file_info) as source_file:
                                content = source_file.read()
                                
                                # Если это Java файл, заменяем example на имя мода
                                if rel_path.endswith('.java'):
                                    content = self.replace_example_in_java(content)
                                
                                with open(target_path, 'wb') as target_file:
                                    target_file.write(content)
                
                print("Шаблон успешно установлен!")
                
                # Удаляем папку example если она существует
                self.remove_example_folder()
                
                # После скачивания запускаем ввод параметров
                self.root.after(0, lambda: self.start_parameter_input(edit_existing=False))
                
            except Exception as e:
                print(f"Ошибка: {e}")
                self.create_empty_structure()
                self.root.after(0, lambda: self.start_parameter_input(edit_existing=False))
        
        thread = threading.Thread(target=download_thread, daemon=True)
        thread.start()
    
    def remove_example_folder(self):
        """Удаляет папку example из src если она существует"""
        try:
            example_folder = self.mod_folder / "src" / "example"
            if example_folder.exists() and example_folder.is_dir():
                print(f"Удаляю папку example: {example_folder}")
                
                # Проверяем, есть ли Java файлы в папке example
                java_files = list(example_folder.glob("*.java"))
                if java_files:
                    print(f"Найдено Java файлов в example: {len(java_files)}")
                    # Если есть файлы, проверяем их содержимое на наличие ExampleJavaMod
                    for java_file in java_files:
                        content = java_file.read_text(encoding='utf-8', errors='ignore')
                        if "ExampleJavaMod" in content:
                            print(f"Файл {java_file.name} содержит ExampleJavaMod")
                
                # Удаляем папку example рекурсивно
                shutil.rmtree(example_folder)
                print("Папка example успешно удалена")
                
                # Также проверяем и удаляем другие возможные папки example
                for item in (self.mod_folder / "src").iterdir():
                    if item.is_dir() and item.name.lower() == "example":
                        print(f"Удаляю дополнительную папку example: {item}")
                        shutil.rmtree(item)
            
            # Также удаляем любые .class файлы или другие следы example
            self.cleanup_example_files()
            
        except Exception as e:
            print(f"Ошибка при удалении папки example: {e}")
    
    def cleanup_example_files(self):
        """Очищает другие файлы связанные с example"""
        try:
            # Ищем и удаляем .class файлы
            for class_file in self.mod_folder.rglob("*.class"):
                if "example" in class_file.name.lower() or "Example" in class_file.name:
                    try:
                        class_file.unlink()
                        print(f"Удален .class файл: {class_file}")
                    except:
                        pass
            
            # Ищем в других файлах references на example
            for file in self.mod_folder.rglob("*"):
                if file.is_file() and file.suffix in ['.gradle', '.properties', '.xml', '.txt', '.md']:
                    try:
                        content = file.read_text(encoding='utf-8', errors='ignore')
                        if 'example' in content.lower():
                            # Заменяем example на имя мода
                            mod_name_lower = re.sub(r'[^a-zA-Z0-9]', '', self.mod_name).lower()
                            new_content = content.replace('example', mod_name_lower)
                            new_content = re.sub(r'example\.', f'{mod_name_lower}.', new_content)
                            file.write_text(new_content, encoding='utf-8')
                            print(f"Обновлен файл: {file}")
                    except:
                        pass
                        
        except Exception as e:
            print(f"Ошибка при очистке файлов example: {e}")
    
    def replace_example_in_java(self, content_bytes):
        """Заменяет 'example' на имя мода в Java файлах"""
        try:
            content = content_bytes.decode('utf-8')
            
            # Получаем имя мода для замены (убираем пробелы, делаем в camelCase)
            mod_name_clean = re.sub(r'[^a-zA-Z0-9]', '', self.mod_name)
            mod_name_lower = mod_name_clean.lower()
            mod_name_camel = mod_name_clean[0].upper() + mod_name_clean[1:] if mod_name_clean else "Mod"
            
            # Заменяем package example; на package имя_мода;
            content = content.replace('package example;', f'package {mod_name_lower};')
            
            # Заменяем imports с example.
            content = re.sub(r'import\s+example\.', f'import {mod_name_lower}.', content)
            
            # Заменяем ExampleJavaMod на ИмяМодаJavaMod
            content = content.replace('ExampleJavaMod', f'{mod_name_camel}JavaMod')
            
            # Заменяем ссылки на спрайты
            content = content.replace('example-java-mod', mod_name_lower)
            
            # Заменяем example. в других местах
            content = re.sub(r'\bexample\.', f'{mod_name_lower}.', content)
            
            return content.encode('utf-8')
        except:
            return content_bytes
    
    def update_java_main_class(self):
        """Создает или обновляет главный Java класс"""
        # Определяем имя мода для package
        mod_name_clean = re.sub(r'[^a-zA-Z0-9]', '', self.mod_name)
        mod_name_lower = mod_name_clean.lower()
        mod_name_camel = mod_name_clean[0].upper() + mod_name_clean[1:] if mod_name_clean else "Mod"
        
        # Удаляем старую папку example если она еще существует
        example_dir = self.mod_folder / "src" / "example"
        if example_dir.exists() and example_dir.is_dir():
            try:
                shutil.rmtree(example_dir)
                print("Удалена старая папка example")
            except Exception as e:
                print(f"Ошибка при удалении папки example: {e}")
        
        # Создаем директорию для нового package
        src_dir = self.mod_folder / "src" / mod_name_lower
        src_dir.mkdir(parents=True, exist_ok=True)
        
        # Путь к файлу
        java_file = src_dir / f"{mod_name_camel}JavaMod.java"
        
        # Если файл существует, проверяем его содержимое
        if java_file.exists():
            try:
                content = java_file.read_text(encoding='utf-8')
                # Проверяем, содержит ли файл правильный package
                if f'package {mod_name_lower};' not in content:
                    # Обновляем package
                    content = re.sub(r'package\s+[a-zA-Z0-9._]+;', f'package {mod_name_lower};', content)
                    java_file.write_text(content, encoding='utf-8')
            except:
                # Если ошибка чтения, пересоздаем файл
                pass
        
        # Если файла нет или он пустой, создаем заново
        if not java_file.exists() or java_file.stat().st_size == 0:
            java_content = f"""package {mod_name_lower};

import arc.*;
import arc.util.*;
import mindustry.*;
import mindustry.content.*;
import mindustry.game.EventType.*;
import mindustry.gen.*;
import mindustry.mod.*;
import mindustry.ui.dialogs.*;
//import_add

public class {mod_name_camel}JavaMod extends Mod{{

    public {mod_name_camel}JavaMod(){{
        Log.info("Loaded {mod_name_camel}JavaMod constructor.");

        //listen for game load event
        Events.on(ClientLoadEvent.class, e -> {{
            //show dialog upon startup
            Time.runTask(10f, () -> {{
                BaseDialog dialog = new BaseDialog("frog");
                dialog.cont.add("behold").row();
                //mod sprites are prefixed with the mod name (this mod is called '{mod_name_lower}' in its config) (name > mod.hjson)
                dialog.cont.image(Core.atlas.find("{mod_name_lower}-frog")).pad(20f).row();
                dialog.cont.button("I see", dialog::hide).size(100f, 50f);
                dialog.show();
            }});
        }});
    }}

    @Override
    public void loadContent(){{
        Log.info("Loading some {mod_name_lower} content.");
        //Registration_add
    }}

}}
"""
            java_file.write_text(java_content, encoding='utf-8')
            print(f"Создан Java файл: {java_file}")
        
        # Возвращаем путь для main в mod.hjson
        return f"{mod_name_lower}.{mod_name_camel}JavaMod"
    
    def start_parameter_input(self, edit_existing=False):
        """Начинаем ввод параметров"""
        self.clear_window()
        self.param_index = 0
        self.param_values = {}
        self.edit_existing = edit_existing
        
        # Сначала обновляем Java файлы и удаляем example
        self.remove_example_folder()
        main_class_path = self.update_java_main_class()
        self.param_values['main'] = main_class_path
        
        # Загружаем существующие значения если редактируем
        if edit_existing:
            self.load_existing_values()
        
        # Показываем первый параметр
        self.show_current_parameter()
    
    def load_existing_values(self):
        """Загружаем существующие значения из mod.hjson"""
        mod_hjson_path = self.mod_folder / "mod.hjson"
        if mod_hjson_path.exists():
            try:
                content = mod_hjson_path.read_text(encoding='utf-8')
                lines = content.split('\n')
                
                for line in lines:
                    line = line.strip()
                    if ':' in line:
                        key, value = line.split(':', 1)
                        key = key.strip()
                        value = value.strip().strip('"')
                        
                        if key in [p[0] for p in self.parameters] + ['main']:
                            self.param_values[key] = value
            except Exception as e:
                print(f"Ошибка при чтении mod.hjson: {e}")
    
    def show_current_parameter(self):
        """Показывает текущий параметр для ввода"""
        if self.param_index >= len(self.parameters):
            self.save_parameters()
            return
            
        param_name, param_label, param_type = self.parameters[self.param_index]
        current_value = self.param_values.get(param_name, "")
        
        self.clear_window()
        
        # Заголовок
        ctk.CTkLabel(self.root, text="Настройка мода", font=("Arial", 20, "bold")).pack(pady=30)
        ctk.CTkLabel(self.root, text=f"Шаг {self.param_index + 1} из {len(self.parameters)}", 
                    font=("Arial", 14)).pack(pady=5)
        
        # Информация о главном классе
        if param_name == "displayName":
            ctk.CTkLabel(self.root, text=f"Главный класс: {self.param_values.get('main', 'Не определен')}", 
                        font=("Arial", 12), text_color="gray").pack(pady=5)
            ctk.CTkLabel(self.root, text=f"Package: {self.param_values.get('main', '').rsplit('.', 1)[0] if '.' in self.param_values.get('main', '') else ''}", 
                        font=("Arial", 12), text_color="gray").pack(pady=2)
        
        # Название параметра
        ctk.CTkLabel(self.root, text=param_label, font=("Arial", 16)).pack(pady=20)
        
        # Поле ввода
        if param_type == "text":
            entry = ctk.CTkEntry(self.root, width=400, font=("Arial", 14))
            if current_value:
                entry.insert(0, current_value)
            entry.pack(pady=10)
            
            # Автоматические значения для некоторых полей
            if param_name == "name" and not current_value:
                default_name = self.mod_name.lower().replace(' ', '-').replace('_', '-')
                entry.delete(0, 'end')
                entry.insert(0, default_name)
            elif param_name == "displayName" and not current_value:
                entry.delete(0, 'end')
                entry.insert(0, self.mod_name)
            elif param_name == "version" and not current_value:
                entry.delete(0, 'end')
                entry.insert(0, "1.0")
            elif param_name == "minGameVersion" and not current_value:
                entry.delete(0, 'end')
                entry.insert(0, "154")
        
        elif param_type == "number":
            entry = ctk.CTkEntry(self.root, width=400, font=("Arial", 14))
            if current_value:
                entry.insert(0, current_value)
            else:
                entry.insert(0, "154")
            entry.pack(pady=10)
        
        # Кнопки
        frame = ctk.CTkFrame(self.root)
        frame.pack(pady=30)
        
        if self.param_index > 0:
            ctk.CTkButton(frame, text="← Назад", command=self.previous_parameter, 
                         width=100).pack(side="left", padx=10)
        
        btn_text = "Сохранить и завершить" if self.param_index == len(self.parameters) - 1 else "Далее →"
        ctk.CTkButton(frame, text=btn_text, command=lambda: self.next_parameter(entry.get()), 
                     width=100).pack(side="left", padx=10)
        
        ctk.CTkButton(self.root, text="Отмена", command=self.main_app.show_main_ui,
                     fg_color="gray", width=100).pack(pady=10)
        
        # Сохраняем ссылку на entry для использования
        self.current_entry = entry
    
    def next_parameter(self, value):
        """Переход к следующему параметру"""
        param_name = self.parameters[self.param_index][0]
        self.param_values[param_name] = value
        
        self.param_index += 1
        self.show_current_parameter()
    
    def previous_parameter(self):
        """Возврат к предыдущему параметру"""
        self.param_index -= 1
        self.show_current_parameter()
    
    def save_parameters(self):
        """Сохраняем все параметры в mod.hjson"""
        try:
            mod_hjson_path = self.mod_folder / "mod.hjson"
            
            # Удаляем папку example перед сохранением
            self.remove_example_folder()
            
            # Обновляем главный Java класс
            main_class_path = self.update_java_main_class()
            self.param_values['main'] = main_class_path
            
            # Если редактируем существующий файл, обновляем его
            if self.edit_existing and mod_hjson_path.exists():
                content = mod_hjson_path.read_text(encoding='utf-8')
                lines = content.split('\n')
                
                new_lines = []
                for line in lines:
                    line_stripped = line.strip()
                    if ':' in line_stripped:
                        key = line_stripped.split(':', 1)[0].strip()
                        if key in self.param_values:
                            # Обновляем значение
                            new_lines.append(f'{key}: "{self.param_values[key]}"')
                        elif key == 'main':
                            # Обновляем main класс
                            new_lines.append(f'main: "{self.param_values["main"]}"')
                        else:
                            new_lines.append(line)
                    else:
                        new_lines.append(line)
                
                # Добавляем отсутствующие параметры
                for param_name in [p[0] for p in self.parameters]:
                    if param_name not in content:
                        new_lines.append(f'{param_name}: "{self.param_values.get(param_name, "")}"')
                
                # Добавляем main если нет
                if "main:" not in content:
                    new_lines.append(f'main: "{self.param_values["main"]}"')
                
                # Добавляем java: true если нет
                if "java:" not in content.lower():
                    new_lines.append("java: true")
                
                mod_hjson_path.write_text('\n'.join(new_lines), encoding='utf-8')
            
            else:
                # Создаем новый файл
                hjson_content = f"""#the mod name as displayed in-game
displayName: "{self.param_values.get('displayName', self.mod_name)}"

#the internal name of your mod
name: "{self.param_values.get('name', self.mod_name.lower().replace(' ', '-'))}"

#your name
author: "{self.param_values.get('author', 'Your Name')}"

#the fully qualified main class of the mod
main: "{self.param_values['main']}"

#the mod description as seen in the mod dialog
description: "{self.param_values.get('description', 'Empty mod template')}"

#the mod version
version: "{self.param_values.get('version', '1.0')}"

#the minimum game build required to run this mod
minGameVersion: "{self.param_values.get('minGameVersion', '154')}"

#this is a java mod
java: true
"""
                mod_hjson_path.write_text(hjson_content, encoding='utf-8')
            
            # Переходим к редактору
            self.go_to_creator()
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось сохранить файл: {e}")
            self.main_app.show_main_ui()
    
    def create_empty_structure(self):
        """Создает пустую структуру если не удалось скачать"""
        (self.mod_folder / "src").mkdir(exist_ok=True)
        (self.mod_folder / "assets").mkdir(exist_ok=True)
        
        # Создаем Java класс
        main_class_path = self.update_java_main_class()
        
        # Создаем пустой mod.hjson с базовыми значениями
        hjson_content = f"""displayName: "{self.mod_name}"
name: "{self.mod_name.lower().replace(' ', '-')}"
author: "Your Name"
main: "{main_class_path}"
description: "Empty mod template"
version: 1.0
minGameVersion: 154
java: true
hidden: false"""
        
        (self.mod_folder / "mod.hjson").write_text(hjson_content, encoding='utf-8')
    
    def go_to_creator(self):
        from creator_editor import CreatorEditor
        creator = CreatorEditor(self.root, self.mod_folder, self.main_app)
        creator.open_creator()
    
    def show_error(self, message):
        messagebox.showerror("Ошибка", message)
        self.main_app.show_main_ui()
    
    def clear_window(self):
        for widget in self.root.winfo_children():
            widget.destroy()