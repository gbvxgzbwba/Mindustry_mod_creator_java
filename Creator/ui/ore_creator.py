#Creator/ui/ore_creator.py
import customtkinter as ctk
import tkinter as tk
import os
import re
from pathlib import Path
import shutil
from tkinter import messagebox
from PIL import Image
import sys
from Creator.utils.lang_system import LangT

def resource_path(relative_path):
    """Получить абсолютный путь к ресурсу"""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

class OreBlockCreator:
    """Класс с функциями создания руд"""
    
    def __init__(self, editor_instance):    
        self.editor = editor_instance
        self.root = editor_instance.root
        self.mod_name = getattr(editor_instance, 'mod_name', '')
        self.mod_folder = getattr(editor_instance, 'mod_folder', '')
        self.selected_item = None
        
        # Кэш для предметов (как в block_creator)
        self._custom_items_cache = {}

    def get_absolute_path(self, relative_path):
        if not self.mod_folder:
            return None
        return Path(self.mod_folder).absolute() / relative_path

    def format_to_lower_camel(self, text: str) -> str:
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

    def get_custom_items(self, force_refresh: bool = False) -> dict:
        """
        Получает кастомные предметы из мода с кэшированием
        """
        # Используем кэш, если не нужно обновление
        if hasattr(self, '_custom_items_cache') and not force_refresh and self._custom_items_cache:
            return self._custom_items_cache
        
        custom_items = {}
        mod_name_lower = self.mod_name.lower() if self.mod_name else self.mod_name
        items_file_path = Path(self.mod_folder) / "src" / mod_name_lower / "init" / "items" / "ModItems.java"
        
        if items_file_path.exists():
            try:
                with open(items_file_path, 'r', encoding='utf-8') as file:
                    content = file.read()
                
                # Паттерны для поиска предметов
                patterns = [
                    r'new\s+Item\s*\(\s*"([^"]+)"\s*\)',
                ]
                
                for pattern in patterns:
                    matches = re.findall(pattern, content)
                    for match in matches:
                        if isinstance(match, tuple):
                            item_name = match[0]
                        else:
                            item_name = match
                        
                        if item_name and item_name not in custom_items:
                            if item_name not in ['Item', 'Liquid', 'Block', 'Items', 'Liquids', 'Blocks']:
                                custom_items[item_name] = item_name
                            
            except Exception as e:
                print(f"DEBUG: Error reading ModItems: {e}")
        
        # Сохраняем в кэш
        self._custom_items_cache = custom_items
        return custom_items

    def get_item_code_name(self, item_name: str, custom_items: dict = None) -> str:
        """
        Возвращает Java-код для предмета
        ТОЧНАЯ КОПИЯ из block_creator.py
        """
        if custom_items is None:
            custom_items = self.get_custom_items()
        
        # Кастомный предмет
        if item_name in custom_items:
            return f"ModItems.{item_name}"
        
        # Специальные случаи для ванильных предметов
        vanilla_item_map = {
            "phase-fabric": "phaseFabric",
            "surge-alloy": "surgeAlloy",
            "spore-pod": "sporePod",
            "blast-compound": "blastCompound",
            "pyratite": "pyratite"
        }
        
        if item_name in vanilla_item_map:
            return f"Items.{vanilla_item_map[item_name]}"
        
        # Преобразуем kebab-case в camelCase
        if '-' in item_name:
            parts = item_name.split('-')
            camel_name = parts[0] + ''.join(p.capitalize() for p in parts[1:])
            return f"Items.{camel_name}"
        
        return f"Items.{item_name}"

    def copy_ore_texture(self, ore_name: str) -> bool:
        """Копирует текстуры руды name1, name2, name3 в sprites/blocks/environment/"""
        try:
            formatted_name = self.format_to_lower_camel(ore_name)
            
            # Целевая папка (КУДА копируем)
            target_dir = Path(self.mod_folder) / "assets" / "sprites" / "blocks" / "environment" / "ores" / f"{formatted_name}"
            target_dir.mkdir(parents=True, exist_ok=True)
            
            # Путь к шаблонам (ОТКУДА копируем)
            template_dir = Path(resource_path("Creator/icons/blocks"))
            
            # Три текстуры с именами name1, name2, name3
            texture_variants = [
                (f"{formatted_name}1.png", "ore-copper1.png"),    # name1
                (f"{formatted_name}2.png", "ore-copper2.png"),    # name2
                (f"{formatted_name}3.png", "ore-copper3.png")     # name3
            ]
            
            copied_count = 0
            for target_name, source_name in texture_variants:
                source_path = template_dir / source_name
                target_path = target_dir / target_name
                
                if source_path.exists():
                    shutil.copy2(source_path, target_path)
                    copied_count += 1
                    print(LangT(f"Текстура создана: {target_path}"))
                else:
                    print(LangT(f"Шаблон не найден: {source_path}"))
            
            if copied_count == 3:
                print(LangT(f"✅ Все 3 текстуры руды созданы для {formatted_name}"))
                return True
            else:
                print(LangT(f"⚠️ Создано только {copied_count} из 3 текстур"))
                return copied_count > 0
                
        except Exception as e:
            print(LangT(f"Ошибка копирования текстур: {e}"))
            return False

    def open_item_selector(self, selected_var, callback=None):
        """
        Открывает выбор предмета (только 1 предмет, без количества)
        """
        editor_window = ctk.CTkToplevel(self.root)
        editor_window.title(LangT("Выбор предмета для выпадения"))
        editor_window.geometry("750x550")
        editor_window.configure(fg_color="#2b2b2b")
        editor_window.transient(self.root)
        editor_window.grab_set()
        
        main_frame = ctk.CTkFrame(editor_window, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=8, pady=8)
        
        # Заголовок
        ctk.CTkLabel(
            main_frame,
            text=LangT("Выберите предмет, который будет выпадать из руды"),
            font=("Arial", 16, "bold")
        ).pack(pady=(0, 10))
        
        # Получаем кастомные предметы
        custom_items = self.get_custom_items()
        
        # Функция для выбора и закрытия
        def select_and_close(item_name):
            display_text = f"ModItems.{item_name}"
            selected_var.set(display_text)
            if callback:
                callback(item_name, True)
            editor_window.destroy()
        
        def create_item_card(parent, item_name):
            """Создает карточку для выбора предмета"""
            CARD_WIDTH = 140
            CARD_HEIGHT = 160
            
            card = ctk.CTkFrame(
                parent, 
                width=CARD_WIDTH, 
                height=CARD_HEIGHT,
                fg_color="#363636", 
                corner_radius=10,
                border_width=2,
                border_color="#404040"
            )
            card.pack_propagate(False)
            card.pack(side="left", padx=5, pady=5)
            
            # Иконка
            icon_frame = ctk.CTkFrame(card, fg_color="transparent", width=60, height=60)
            icon_frame.pack(pady=(15, 5))
            icon_frame.pack_propagate(False)
            
            # Загрузка иконки
            try:
                from PIL import Image
                
                item_name_lower = item_name.lower()
                icon_paths = [
                    Path(self.mod_folder) / "assets" / "sprites" / "items" / f"{item_name_lower}.png",
                    Path(self.mod_folder) / "sprites" / "items" / f"{item_name_lower}.png",
                ]
                
                icon_found = False
                for icon_path in icon_paths:
                    if icon_path.exists():
                        img = Image.open(icon_path)
                        img = img.resize((50, 50), Image.Resampling.LANCZOS)
                        ctk_img = ctk.CTkImage(img, size=(50, 50))
                        ctk.CTkLabel(icon_frame, image=ctk_img, text="").pack(expand=True)
                        icon_found = True
                        break
                if not icon_found:
                    ctk.CTkLabel(icon_frame, text="📦", font=("Arial", 40)).pack(expand=True)
                    
            except Exception as e:
                print(f"Error loading icon for {item_name}: {e}")
                ctk.CTkLabel(icon_frame, text="📦", font=("Arial", 40)).pack(expand=True)
            
            # Название
            display_name = item_name[:15] + ("..." if len(item_name) > 15 else "")
            name_color = "#4CAF50"
            
            name_label = ctk.CTkLabel(
                card, 
                text=display_name, 
                font=("Arial", 11, "bold"),
                wraplength=CARD_WIDTH-15,
                text_color=name_color
            )
            name_label.pack(pady=5)
            
            # Разделитель
            ctk.CTkFrame(card, height=1, fg_color="#404040").pack(fill="x", pady=6, padx=8)
            
            # Кнопка выбора
            select_btn = ctk.CTkButton(
                card,
                text=LangT("Выбрать"),
                width=80,
                height=30,
                font=("Arial", 11, "bold"),
                fg_color="#4CAF50",
                hover_color="#388E3C",
                corner_radius=6
            )
            select_btn.pack(pady=8)
            
            # При нажатии на кнопку - выбираем и закрываем
            select_btn.configure(command=lambda: select_and_close(item_name))
            
            # При клике на карточку - выбираем и закрываем
            card.bind("<Button-1>", lambda e: select_and_close(item_name))
            name_label.bind("<Button-1>", lambda e: select_and_close(item_name))
            icon_frame.bind("<Button-1>", lambda e: select_and_close(item_name))
            
            # Меняем курсор при наведении
            card.bind("<Enter>", lambda e: card.configure(cursor="hand2"))
            card.bind("<Leave>", lambda e: card.configure(cursor=""))
            
            # Подсветка при наведении
            def on_enter(e):
                card.configure(fg_color="#404040")
            
            def on_leave(e):
                card.configure(fg_color="#363636")
            
            card.bind("<Enter>", on_enter)
            card.bind("<Leave>", on_leave)
            
            return card
        
        def populate_items(elements):
            """Заполняет окно предметами в grid"""
            # Очищаем всё кроме заголовка
            for widget in main_frame.winfo_children():
                if widget != main_frame.winfo_children()[0]:
                    widget.destroy()
            
            # Создаем scrollable фрейм
            scroll_frame = ctk.CTkScrollableFrame(main_frame, fg_color="#2b2b2b")
            scroll_frame.pack(fill="both", expand=True, pady=(10, 0))
            
            if not elements:
                empty_label = ctk.CTkLabel(
                    scroll_frame,
                    text=LangT("📭 Нет предметов в моде"),
                    font=("Arial", 14),
                    text_color="#888888"
                )
                empty_label.pack(pady=50)
                return
            
            cards_container = ctk.CTkFrame(scroll_frame, fg_color="transparent")
            cards_container.pack(fill="both", expand=True)
            
            sorted_elements = sorted(elements.keys())
            
            def calculate_grid():
                container_width = cards_container.winfo_width()
                if container_width < 10:
                    return 1
                CARD_WIDTH = 140
                HORIZONTAL_PADDING = 10
                cards_per_row = max(1, (container_width - HORIZONTAL_PADDING) // (CARD_WIDTH + HORIZONTAL_PADDING))
                return cards_per_row
            
            def update_grid():
                for widget in cards_container.winfo_children():
                    widget.destroy()
                
                cards_per_row = calculate_grid()
                current_row_frame = None
                
                for i, item_name in enumerate(sorted_elements):
                    if i % cards_per_row == 0:
                        current_row_frame = ctk.CTkFrame(cards_container, fg_color="transparent")
                        current_row_frame.pack(fill="x", pady=2)
                    
                    create_item_card(current_row_frame, item_name)
            
            def on_resize(event):
                update_grid()
            
            cards_container.bind("<Configure>", on_resize)
            update_grid()
        
        # Заполняем предметами
        populate_items(custom_items)
        
        # Кнопка закрытия
        button_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        button_frame.pack(fill="x", pady=(15, 5))
        
        ctk.CTkButton(
            button_frame,
            text=LangT("❌ Закрыть"), 
            width=130,
            height=35,
            font=("Arial", 12, "bold"),
            fg_color="#f44336", 
            hover_color="#d32f2f",
            command=editor_window.destroy
        ).pack(pady=5)
        
        def on_closing():
            editor_window.destroy()
        
        editor_window.protocol("WM_DELETE_WINDOW", on_closing)

    def check_ore_exists(self, name: str) -> bool:
        """Проверяет, существует ли уже руда с таким именем"""
        mod_name_lower = self.mod_name.lower() if self.mod_name else self.mod_name
        ore_file_path = Path(self.mod_folder) / "src" / mod_name_lower / "init" / "blocks" / "ores" / "Ores.java"
        
        if ore_file_path.exists():
            try:
                with open(ore_file_path, 'r', encoding='utf-8') as file:
                    content = file.read()
                    if f"public static OreBlock {name};" in content or f"public static OreBlock {name} " in content:
                        return True
                    if f'OreBlock("{name}")' in content:
                        return True
            except:
                pass
        
        # Проверяем текстуры name1, name2, name3
        texture_paths = [
            Path(self.mod_folder) / "assets" / "sprites" / "blocks" / "environment" / f"{name}1.png",
            Path(self.mod_folder) / "assets" / "sprites" / "blocks" / "environment" / f"{name}2.png",
            Path(self.mod_folder) / "assets" / "sprites" / "blocks" / "environment" / f"{name}3.png"
        ]
        
        for texture_path in texture_paths:
            if texture_path.exists():
                return True
        
        return False

    def create_ore(self):
        """Создает или добавляет новую руду"""
        
        self.clear_window()
        
        main_frame = ctk.CTkFrame(self.root, fg_color="#2b2b2b")
        main_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        scroll_frame = ctk.CTkScrollableFrame(main_frame, width=500, height=600, fg_color="#2b2b2b")
        scroll_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        title_frame = ctk.CTkFrame(scroll_frame, fg_color="transparent")
        title_frame.pack(fill="x", pady=(0, 20))
        
        ctk.CTkLabel(title_frame, text=LangT("Создание руды"), 
                    font=("Arial", 24, "bold"), text_color="#4CAF50").pack(pady=10)
        
        # Информационная карточка
        info_card = ctk.CTkFrame(scroll_frame, corner_radius=15, border_width=2,
                                 border_color="#404040", fg_color="#363636")
        info_card.pack(fill="x", pady=(0, 20))
        
        ctk.CTkLabel(info_card, text=LangT("Основная информация"), 
                    font=("Arial", 18, "bold"), text_color="#E0E0E0").pack(pady=(15, 10), padx=20, anchor="w")
        
        # Поле ввода названия
        name_frame = ctk.CTkFrame(info_card, fg_color="transparent")
        name_frame.pack(fill="x", padx=20, pady=(0, 15))
        
        ctk.CTkLabel(name_frame, text=LangT("Название руды (английское, можно пробел): \n (это названия не влияет на отображения \n в игре это названия в коде для текстур и загрузки)"),
                    font=("Arial", 16), text_color="#BDBDBD").pack(anchor="w", pady=(0, 5))
        
        entry_name = ctk.CTkEntry(name_frame, width=400, height=40,
                                  placeholder_text="ore name", font=("Arial", 15),
                                  border_width=2, corner_radius=8, fg_color="#424242",
                                  border_color="#555555", text_color="#FFFFFF",
                                  placeholder_text_color="#888888")
        entry_name.pack(fill="x", pady=(0, 5))
        
        # Карточка свойств
        properties_card = ctk.CTkFrame(scroll_frame, corner_radius=15, border_width=2,
                                       border_color="#404040", fg_color="#363636")
        properties_card.pack(fill="x", pady=(0, 20))
        
        ctk.CTkLabel(properties_card, text=LangT("Свойства руды"),
                    font=("Arial", 18, "bold"), text_color="#E0E0E0").pack(pady=(15, 10), padx=20, anchor="w")
        
        # Грид для свойств
        properties_grid = ctk.CTkFrame(properties_card, fg_color="transparent")
        properties_grid.pack(fill="x", padx=20, pady=(0, 15))
        
        # Твердость (hardness) - не больше 5
        hardness_frame = ctk.CTkFrame(properties_grid, fg_color="transparent")
        hardness_frame.grid(row=0, column=0, padx=10, pady=5, sticky="ew")
        
        ctk.CTkLabel(hardness_frame, text=LangT("Твердость (hardness, 1-5):"),
                    font=("Arial", 15), text_color="#BDBDBD").pack(anchor="w", pady=(0, 5))
        
        def validate_hardness(value):
            if value == "":
                return True
            if not value.isdigit():
                return False
            return 1 <= int(value) <= 5
        
        vcmd_hardness = (self.root.register(validate_hardness), '%P')
        
        entry_hardness = ctk.CTkEntry(hardness_frame, width=180, height=38,
                                      placeholder_text="3", font=("Arial", 14),
                                      validate="key", validatecommand=vcmd_hardness,
                                      fg_color="#424242", border_color="#555555",
                                      text_color="#FFFFFF", placeholder_text_color="#888888")
        entry_hardness.pack(fill="x")
        
        # Выбор предмета для дропа
        drop_frame = ctk.CTkFrame(properties_grid, fg_color="transparent")
        drop_frame.grid(row=0, column=1, padx=10, pady=5, sticky="ew")
        
        ctk.CTkLabel(drop_frame, text=LangT("Предмет для выпадения (itemDrop):"),
                    font=("Arial", 15), text_color="#BDBDBD").pack(anchor="w", pady=(0, 5))
        
        selected_item_var = tk.StringVar(value=LangT("Не выбран"))
        
        item_display = ctk.CTkEntry(drop_frame, width=180, height=38,
                                    textvariable=selected_item_var,
                                    font=("Arial", 14), fg_color="#424242",
                                    border_color="#555555", text_color="#FFFFFF",
                                    state="readonly")
        item_display.pack(fill="x", pady=(0, 5))
        
        def on_item_selected(item_name, is_custom):
            self.selected_item = (item_name, is_custom)
            if is_custom:
                selected_item_var.set(f"ModItems.{item_name}")
            else:
                selected_item_var.set(f"Items.{item_name}")
        
        ctk.CTkButton(drop_frame, text=LangT("🔍 Выбрать предмет"),
                     command=lambda: self.open_item_selector(selected_item_var, on_item_selected),
                     height=35, font=("Arial", 13), fg_color="#FF9800",
                     hover_color="#F57C00", corner_radius=6).pack(anchor="w")
        
        # Статус
        status_frame = ctk.CTkFrame(scroll_frame, fg_color="transparent")
        status_frame.pack(fill="x", pady=(0, 20))
        
        status_label = ctk.CTkLabel(status_frame, text="", font=("Arial", 14),
                                    wraplength=450, justify="left", text_color="#E0E0E0")
        status_label.pack()
        
        status_label.pack()
        # ДОБАВЛЕНО: Картинка-подсказка
        help_frame = ctk.CTkFrame(scroll_frame, fg_color="transparent")
        help_frame.pack(fill="x", pady=(10, 10))

        try:
            help_image = ctk.CTkImage(
                light_image=Image.open(resource_path("Creator/icons/helphardness.png")),
                dark_image=Image.open(resource_path("Creator/icons/helphardness.png")),
                size=(880, 600)  # Уменьшите размер, так как 1050x650 слишком большой
            )
            ctk.CTkLabel(help_frame, image=help_image, text="").pack()
        except Exception as e:
            print(f"Error loading help image: {e}")
        
        # Кнопки
        button_frame = ctk.CTkFrame(scroll_frame, fg_color="transparent")
        button_frame.pack(fill="x", pady=20)
        
        def process_ore():
            original_name = entry_name.get().strip()
            
            if not original_name:
                status_label.configure(text=LangT("❌ Ошибка: Введите название руды!"), text_color="#F44336")
                return
            
            if not self.selected_item:
                status_label.configure(text=LangT("❌ Ошибка: Выберите предмет для выпадения!"), text_color="#F44336")
                return
            
            hardness = entry_hardness.get().strip() or "3"
            try:
                hardness_int = int(hardness)
                if not 1 <= hardness_int <= 5:
                    status_label.configure(text=LangT("❌ Ошибка: Твердость должна быть от 1 до 5!"), text_color="#F44336")
                    return
            except:
                status_label.configure(text=LangT("❌ Ошибка: Введите число от 1 до 5!"), text_color="#F44336")
                return
            
            constructor_name = self.format_to_lower_camel(original_name)
            if not constructor_name:
                status_label.configure(text=LangT("❌ Ошибка: Некорректное название!"), text_color="#F44336")
                return
            
            # Проверка существования
            if self.check_ore_exists(constructor_name):
                status_label.configure(text=LangT("❌ Ошибка: Руда '{constructor_name}' уже существует!").format(constructor_name=constructor_name), text_color="#F44336")
                return
            
            # Копирование текстур (name1, name2, name3)
            texture_copied = self.copy_ore_texture(original_name)
            texture_status = LangT("✅ Текстуры созданы") if texture_copied else LangT("⚠️ Текстуры не созданы")
            
            item_name, is_custom = self.selected_item
            item_code = self.get_item_code_name(item_name)
            
            # Создание файла
            mod_name_lower = self.mod_name.lower() if self.mod_name else self.mod_name
            ore_file_path = Path(self.mod_folder) / "src" / mod_name_lower / "init" / "blocks" / "environment" / "ores" / "Ores.java"
            ore_file_path.parent.mkdir(parents=True, exist_ok=True)
            
            main_mod_path = Path(self.mod_folder) / "src" / mod_name_lower / f"{self.mod_name}JavaMod.java"
            
            # Читаем или создаем файл
            try:
                with open(ore_file_path, 'r', encoding='utf-8') as file:
                    content = file.read()
            except FileNotFoundError:
                content = f"""package {mod_name_lower}.init.blocks.environment.ores;

import mindustry.world.blocks.environment.OreBlock;
import mindustry.content.Items;
import {mod_name_lower}.init.items.ModItems;

public class Ores {{
    public static OreBlock;
    
    public static void Load() {{
        // Регистрация руд
    }}
}}"""
            
            # Добавляем импорт Items если его нет
            if "import mindustry.content.Items;" not in content:
                lines = content.split('\n')
                insert_pos = -1
                for i, line in enumerate(lines):
                    if line.startswith('import ') and i > insert_pos:
                        insert_pos = i
                if insert_pos != -1:
                    lines.insert(insert_pos + 1, "import mindustry.content.Items;")
                    content = '\n'.join(lines)
            
            ore_exists = constructor_name in content
            
            if not ore_exists:
                # Добавляем переменную
                if "public static OreBlock;" in content:
                    content = content.replace("public static OreBlock;", f"public static OreBlock {constructor_name};")
                elif "public static OreBlock " in content:
                    lines = content.split('\n')
                    for i, line in enumerate(lines):
                        if "public static OreBlock " in line and constructor_name not in line:
                            lines[i] = line.rstrip(';') + f", {constructor_name};"
                            content = '\n'.join(lines)
                            break
                
                # Добавляем инициализацию
                load_start = content.find("public static void Load() {")
                if load_start != -1:
                    open_brace = content.find('{', load_start)
                    if open_brace != -1:
                        insert_pos = open_brace + 1
                        indent = "        "
                        ore_code = f'''
{indent}{constructor_name} = new OreBlock("{constructor_name}"){{{{
{indent}    itemDrop = {item_code};
{indent}    {item_code}.hardness = {hardness_int};
{indent}}}}};'''
                        content = content[:insert_pos] + ore_code + content[insert_pos:]
                
                # Сохраняем файл
                with open(ore_file_path, 'w', encoding='utf-8') as file:
                    file.write(content)
                
                # Обновляем главный файл
                try:
                    with open(main_mod_path, 'r', encoding='utf-8') as file:
                        main_content = file.read()
                    
                    modified = False
                    
                    # Добавляем импорт
                    import_statement = f"import {mod_name_lower}.init.blocks.environment.ores.Ores;"
                    if import_statement not in main_content:
                        import_add_pos = main_content.find("//import_add")
                        if import_add_pos != -1:
                            insert_pos = import_add_pos + len("//import_add")
                            if insert_pos < len(main_content) and main_content[insert_pos] == '\n':
                                main_content = main_content[:insert_pos] + f"\n{import_statement}" + main_content[insert_pos:]
                            else:
                                main_content = main_content[:insert_pos] + f"\n{import_statement}" + main_content[insert_pos:]
                            modified = True
                    
                    # Добавляем вызов Load
                    load_statement = "Ores.Load();"
                    if load_statement not in main_content:
                        registration_add_pos = main_content.find("//Registration_add")
                        if registration_add_pos != -1:
                            insert_pos = registration_add_pos + len("//Registration_add")
                            if insert_pos < len(main_content) and main_content[insert_pos] == '\n':
                                main_content = main_content[:insert_pos] + f"\n        {load_statement}" + main_content[insert_pos:]
                            else:
                                main_content = main_content[:insert_pos] + f"\n        {load_statement}" + main_content[insert_pos:]
                            modified = True
                    
                    if modified:
                        with open(main_mod_path, 'w', encoding='utf-8') as file:
                            file.write(main_content)
                    
                    status_messages = [
                        LangT("✅ Руда '{constructor_name}' успешно создана!").format(constructor_name=constructor_name),
                        LangT(f"{texture_status}")
                    ]
                    
                    status_text = "\n".join(status_messages)
                    status_label.configure(text=status_text, text_color="#4CAF50")
                    
                except Exception as e:
                    status_label.configure(text=LangT(f"❌ Ошибка: {str(e)}"), text_color="#F44336")
            else:
                status_label.configure(text=LangT(f"⚠️ Руда '{constructor_name}' уже существует"), text_color="#FF9800")
            
            self.root.after(5000, lambda: status_label.configure(text=""))
        
        def back_to_main():
            self.editor.open_creator()
        
        buttons_frame = ctk.CTkFrame(button_frame, fg_color="transparent")
        buttons_frame.pack(pady=10)
        
        ctk.CTkButton(buttons_frame, text=LangT("🚀 Создать руду"), command=process_ore,
                     height=45, width=200, font=("Arial", 16, "bold"),
                     fg_color="#2E7D32", hover_color="#1B5E20", corner_radius=10).pack(side="left", padx=15)
        
        ctk.CTkButton(buttons_frame, text=LangT("← Назад"), command=back_to_main,
                     height=45, width=120, font=("Arial", 14),
                     fg_color="#424242", hover_color="#616161", corner_radius=10).pack(side="left", padx=15)
        
        self.selected_item = None

    def clear_window(self):
        """Очистка окна"""
        for widget in self.root.winfo_children():
            widget.destroy()