# block_creator.py
import customtkinter as ctk
import tkinter as tk
import os
import re
from pathlib import Path
import shutil
from tkinter import messagebox
from PIL import Image, ImageTk
from creator_editor import CreatorEditor

class BlockCreator:
    """Класс с функциями создания блоков в Java-стиле"""
    
    def __init__(self, editor_instance):
        """
        Инициализация класса
        
        Args:
            editor_instance: Экземпляр основного редактора
        """
        self.editor = editor_instance
        self.root = editor_instance.root  # Получаем root из редактора
        
        # Делегируем атрибуты от редактора
        self.mod_name = getattr(editor_instance, 'mod_name', '')
        self.mod_folder = getattr(editor_instance, 'mod_folder', '')
        self.build_items = []  # Список для хранения предметов строительства
        self.current_mode = "wall_creator"  # Текущий режим работы
        
        # Предметы строительства (основные функции остаются в этом классе)
        self.default_items = [
            "copper", "lead", "metaglass", "graphite", "sand", 
            "coal", "titanium", "thorium", "scrap", "silicon",
            "plastanium", "phase-fabric", "surge-alloy", "spore-pod", 
            "blast-compound", "pyratite"
        ]

    def back_to_main(self):
        """Возврат к основному интерфейсу редактора"""
        self.clear_window()
        self.editor.open_creator()

    def create_wall(self):
        """Создает или добавляет новую стену в walls/Walls.java"""
        
        # Очищаем всё окно
        self.clear_window()
        
        # Основной фрейм с прокруткой
        main_frame = ctk.CTkFrame(self.root, fg_color="#2b2b2b")
        main_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Фрейм для прокрутки
        scroll_frame = ctk.CTkScrollableFrame(
            main_frame,
            width=500,
            height=600,
            fg_color="#2b2b2b"
        )
        scroll_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Заголовок
        title_frame = ctk.CTkFrame(scroll_frame, fg_color="transparent")
        title_frame.pack(fill="x", pady=(0, 20))
        
        ctk.CTkLabel(
            title_frame,
            text="Создание стены",
            font=("Arial", 24, "bold"),
            text_color="#4CAF50"
        ).pack(pady=10)
        
        # === Карточка для основной информации ===
        info_card = ctk.CTkFrame(
            scroll_frame,
            corner_radius=15,
            border_width=2,
            border_color="#404040",
            fg_color="#363636"
        )
        info_card.pack(fill="x", pady=(0, 20))
        
        ctk.CTkLabel(
            info_card,
            text="Основная информация",
            font=("Arial", 18, "bold"),
            text_color="#E0E0E0"
        ).pack(pady=(15, 10), padx=20, anchor="w")
        
        # Поле ввода названия
        name_frame = ctk.CTkFrame(info_card, fg_color="transparent")
        name_frame.pack(fill="x", padx=20, pady=(0, 15))
        
        ctk.CTkLabel(
            name_frame,
            text="Название стены (английское, можно пробел, первая буква маленькая):",
            font=("Arial", 16),
            text_color="#BDBDBD"
        ).pack(anchor="w", pady=(0, 5))
        
        entry_name = ctk.CTkEntry(
            name_frame,
            width=400,
            height=40,
            placeholder_text="wall name",
            font=("Arial", 15),
            border_width=2,
            corner_radius=8,
            fg_color="#424242",
            border_color="#555555",
            text_color="#FFFFFF",
            placeholder_text_color="#888888"
        )
        entry_name.pack(fill="x", pady=(0, 5))
        
        # === Функции валидации ===
        def validate_float_input(value):
            if value == "" or value == ".":
                return True
            pattern = r'^\d*\.?\d{0,2}$'
            if not re.match(pattern, value):
                return False
            try:
                return float(value) <= 5000.00
            except ValueError:
                return False

        def validate_int_input(value):
            if value == "":
                return True
            if not value.isdigit():
                return False
            return int(value) <= 999999

        def format_float(value):
            if not value:
                return ""
            try:
                num = float(value)
                num = min(num, 5000.00)
                formatted = f"{num:.2f}"
                if formatted.endswith(".00"):
                    formatted = formatted[:-3]
                elif formatted.endswith(".0"):
                    formatted = formatted[:-2]
                return formatted
            except ValueError:
                return value

        vcmd_float = (self.root.register(validate_float_input), '%P')
        vcmd_int = (self.root.register(validate_int_input), '%P')

        # === Карточка для свойств ===
        properties_card = ctk.CTkFrame(
            scroll_frame,
            corner_radius=15,
            border_width=2,
            border_color="#404040",
            fg_color="#363636"
        )
        properties_card.pack(fill="x", pady=(0, 20))

        ctk.CTkLabel(
            properties_card,
            text="Свойства стены",
            font=("Arial", 18, "bold"),
            text_color="#E0E0E0"
        ).pack(pady=(15, 10), padx=20, anchor="w")

        # Грид для свойств
        properties_grid = ctk.CTkFrame(properties_card, fg_color="transparent")
        properties_grid.pack(fill="x", padx=20, pady=(0, 15))

        # Здоровье
        hp_frame = ctk.CTkFrame(properties_grid, fg_color="transparent")
        hp_frame.grid(row=0, column=0, padx=10, pady=5, sticky="ew")
        
        ctk.CTkLabel(
            hp_frame,
            text="❤️ Здоровье (health):",
            font=("Arial", 15),
            text_color="#BDBDBD"
        ).pack(anchor="w", pady=(0, 5))
        
        entry_hp = ctk.CTkEntry(
            hp_frame,
            width=180,
            height=38,
            placeholder_text="400",
            font=("Arial", 14),
            validate="key",
            validatecommand=vcmd_int,
            fg_color="#424242",
            border_color="#555555",
            text_color="#FFFFFF",
            placeholder_text_color="#888888"
        )
        entry_hp.pack(fill="x")

        # Скорость
        speed_frame = ctk.CTkFrame(properties_grid, fg_color="transparent")
        speed_frame.grid(row=0, column=1, padx=10, pady=5, sticky="ew")
        
        ctk.CTkLabel(
            speed_frame,
            text="⚡ Скорость стройки (buildTime*10 \n в игре 1 сек если 10 \n авто умножения на 10):",
            font=("Arial", 15),
            text_color="#BDBDBD"
        ).pack(anchor="w", pady=(0, 5))
        
        entry_speed = ctk.CTkEntry(
            speed_frame,
            width=180,
            height=38,
            placeholder_text="1.0",
            font=("Arial", 14),
            validate="key",
            validatecommand=vcmd_float,
            fg_color="#424242",
            border_color="#555555",
            text_color="#FFFFFF",
            placeholder_text_color="#888888"
        )
        entry_speed.pack(fill="x")

        # Размер
        size_frame = ctk.CTkFrame(properties_grid, fg_color="transparent")
        size_frame.grid(row=1, column=0, padx=10, pady=5, sticky="ew")
        
        ctk.CTkLabel(
            size_frame,
            text="📏 Размер (size):",
            font=("Arial", 15),
            text_color="#BDBDBD"
        ).pack(anchor="w", pady=(0, 5))
        
        size_var = ctk.StringVar(value="1")
        size_combo = ctk.CTkComboBox(
            size_frame,
            values=[str(i) for i in range(1, 16)],
            variable=size_var,
            width=180,
            height=38,
            font=("Arial", 14)
        )
        size_combo.pack(fill="x")

        # === Карточка для дополнительных опций ===
        options_card = ctk.CTkFrame(
            scroll_frame,
            corner_radius=15,
            border_width=2,
            border_color="#404040",
            fg_color="#363636"
        )
        options_card.pack(fill="x", pady=(0, 20))

        ctk.CTkLabel(
            options_card,
            text="Дополнительные опции",
            font=("Arial", 18, "bold"),
            text_color="#E0E0E0"
        ).pack(pady=(15, 10), padx=20, anchor="w")

        # Предметы строительства
        build_items_frame = ctk.CTkFrame(options_card, fg_color="transparent")
        build_items_frame.pack(fill="x", padx=20, pady=(0, 15))
        
        ctk.CTkLabel(
            build_items_frame,
            text="🔨 Предметы для строительства:",
            font=("Arial", 15),
            text_color="#BDBDBD"
        ).pack(anchor="w", pady=(0, 10))
        
        selected_items_var = tk.StringVar(value="Выбрано: 0 предметов")
        selected_items_label = ctk.CTkLabel(
            build_items_frame,
            textvariable=selected_items_var,
            font=("Arial", 12),
            text_color="#9E9E9E",
            wraplength=400
        )
        selected_items_label.pack(anchor="w", pady=(5, 0))
        
        ctk.CTkButton(
            build_items_frame,
            text="Выбрать предметы",
            command=lambda: self.open_build_items_editor(selected_items_var),
            height=35,
            font=("Arial", 13),
            fg_color="#2E7D32",
            hover_color="#1B5E20",
            corner_radius=6
        ).pack(anchor="w", pady=(0, 5))

        # Always Unlocked
        always_unlocked_var = ctk.BooleanVar(value=False)
        always_unlocked_frame = ctk.CTkFrame(options_card, fg_color="transparent")
        always_unlocked_frame.pack(fill="x", padx=20, pady=(0, 15))
        
        ctk.CTkCheckBox(
            always_unlocked_frame,
            text="🔓 Always Unlocked",
            variable=always_unlocked_var,
            font=("Arial", 15),
            text_color="#BDBDBD",
            border_width=2,
            corner_radius=6,
            fg_color="#4CAF50",
            hover_color="#45a049",
            border_color="#555555"
        ).pack(anchor="w", pady=5)

        # === Статус ===
        status_frame = ctk.CTkFrame(scroll_frame, fg_color="transparent")
        status_frame.pack(fill="x", pady=(0, 20))
        
        status_label = ctk.CTkLabel(
            status_frame,
            text="",
            font=("Arial", 14),
            wraplength=450,
            justify="left",
            text_color="#E0E0E0"
        )
        status_label.pack()

        # === Фрейм для кнопок ===
        button_frame = ctk.CTkFrame(scroll_frame, fg_color="transparent")
        button_frame.pack(fill="x", pady=20)
        
        # === Вспомогательные функции ===
        def format_to_lower_camel(text):
            words = text.strip().split()
            if not words:
                return ""
            result = words[0].lower()
            for word in words[1:]:
                result += word.capitalize()
            return result

        def copy_wall_texture(wall_name, size_multiplier):
            try:
                templates_dir = Path("creator/icons/blocks")
                if not templates_dir.exists():
                    return False
                
                template = templates_dir / "copper-wall.png"
                if not template.exists():
                    image_files = list(templates_dir.glob("*.png"))
                    if not image_files:
                        return False
                    template = image_files[0]
                
                texture_name = format_to_lower_camel(wall_name)
                target_name = texture_name + ".png"
                target_dir = Path(self.mod_folder) / "assets" / "sprites" / "walls"
                target_dir.mkdir(parents=True, exist_ok=True)
                target_path = target_dir / target_name
                
                img = Image.open(template)
                base_size = 32
                new_size = base_size * size_multiplier
                img = img.resize((new_size, new_size), Image.Resampling.LANCZOS)
                img.save(target_path)
                
                return True
            except Exception:
                return False

        def check_name_exists(name):
            formatted_name = format_to_lower_camel(name)
            name_lower = formatted_name
            check_paths = [
                Path(self.mod_folder) / "assets" / "sprites" / "items" / f"{name_lower}.png",
                Path(self.mod_folder) / "assets" / "sprites" / "liquids" / f"{name_lower}.png",
                Path(self.mod_folder) / "assets" / "sprites" / "walls" / f"{name_lower}.png",
            ]
            for path in check_paths:
                if path.exists():
                    return True
            return False

        def get_custom_items():
            custom_items = {}
            mod_name_lower = self.mod_name.lower() if self.mod_name else self.mod_name
            items_file_path = Path(self.mod_folder) / "src" / mod_name_lower / "init" / "items" / "ModItems.java"
            
            if items_file_path.exists():
                try:
                    with open(items_file_path, 'r', encoding='utf-8') as file:
                        content = file.read()
                    pattern = r'public\s+static\s+Item\s+(\w+);'
                    matches = re.findall(pattern, content)
                    for item_name in matches:
                        if item_name:
                            custom_items[item_name] = item_name
                except Exception:
                    return {}
            return custom_items

        def get_item_code_name(item_name, custom_items):
            if item_name in custom_items:
                return f"ModItems.{item_name}"
            
            vanilla_item_map = {
                "phase-fabric": "phaseFabric",
                "surge-alloy": "surgeAlloy",
                "spore-pod": "sporePod",
                "blast-compound": "blastCompound",
            }
            
            if item_name in vanilla_item_map:
                return f"Items.{vanilla_item_map[item_name]}"
            
            return f"Items.{item_name}"

        # === Основная функция создания стены ===
        def process_wall():
            original_name = entry_name.get().strip()
            
            if not original_name:
                status_label.configure(
                    text="❌ Ошибка: Введите название стены!", 
                    text_color="#F44336"
                )
                return
            
            constructor_name = format_to_lower_camel(original_name)
            if not constructor_name:
                status_label.configure(
                    text="❌ Ошибка: Некорректное название!", 
                    text_color="#F44336"
                )
                return

            if check_name_exists(original_name):
                status_label.configure(
                    text=f"❌ Ошибка: Имя '{constructor_name}' уже используется!", 
                    text_color="#F44336"
                )
                return
            
            size_multiplier = int(size_var.get())
            texture_copied = copy_wall_texture(original_name, size_multiplier)
            texture_status = "✅ Текстура создана" if texture_copied else "⚠️ Текстура не создана"
            
            hp_value = entry_hp.get().strip() or "400"
            speed_raw = entry_speed.get().strip() or "1.0"
            size_value = size_var.get()

            # Преобразуем buildTime (с плавающей точкой и умножением на 10)
            try:
                # Получаем исходное значение как число
                speed_float = float(speed_raw)
                # Умножаем на 10 для игры
                speed_val = speed_float * 10
                # Для отображения оставляем исходное значение
                speed_display = speed_raw
                # Для кода используем умноженное значение с суффиксом 'f'
                speed_code = f"{speed_val}f"
            except ValueError:
                speed_display = "1.0"
                speed_code = "10.0f"
            
            hp_value = str(int(hp_value))
            always_unlocked_value = "true" if always_unlocked_var.get() else "false"
            
            custom_items = get_custom_items()
            if constructor_name and len(constructor_name) > 0:
                var_name = constructor_name[0].lower() + constructor_name[1:] if constructor_name else ""
            else:
                var_name = ""
            
            itemstack_code = ""
            if self.build_items:
                item_counts = {}
                for item in self.build_items:
                    item_counts[item] = item_counts.get(item, 0) + 1
                
                item_parts = []
                for item_name, count in item_counts.items():
                    code_name = get_item_code_name(item_name, custom_items)
                    item_parts.append(f"{code_name}, {count}")
                
                itemstack_code = f"\n            requirements(Category.defense,\n                ItemStack.with({', '.join(item_parts)}));"
            
            properties = f"""    health = {hp_value};
                size = {size_value};
                buildTime = {speed_code};
                alwaysUnlocked = {always_unlocked_value};
                buildVisibility = BuildVisibility.shown;
                category = Category.defense;{itemstack_code}

                localizedName = Core.bundle.get("{var_name}.name", "OH NO");
                description = Core.bundle.get("{var_name}.description", "OH NO");"""
            
            mod_name_lower = self.mod_name.lower() if self.mod_name else self.mod_name
            block_registration_path = Path(self.mod_folder) / "src" / mod_name_lower / "init" / "blocks" / "walls" / "Walls.java"
            main_mod_path = Path(self.mod_folder) / "src" / mod_name_lower / f"{self.mod_name}JavaMod.java"
            
            block_registration_path.parent.mkdir(parents=True, exist_ok=True)
            
            try:
                with open(block_registration_path, 'r', encoding='utf-8') as file:
                    content = file.read()
            except FileNotFoundError:
                content = f"""package {mod_name_lower}.init.blocks.walls;

import arc.graphics.Color;
import arc.Core;
import mindustry.type.ItemStack;
import mindustry.type.Category;
import mindustry.world.Block;
import mindustry.world.blocks.defense.Wall;
import mindustry.world.meta.BuildVisibility;
import mindustry.content.Items;
import mindustry.Vars;
import {mod_name_lower}.init.items.ModItems;

public class Walls {{
    public static Wall;
                                    
    public static void Load() {{
        // Регистрация блоков
    }}
}}"""

            wall_exists = var_name in content
            if not wall_exists:
                if "public static Wall;" in content:
                    content = content.replace(
                        "public static Wall;",
                        f"public static Wall {var_name};"
                    )
                elif "public static Wall " in content:
                    lines = content.split('\n')
                    for i, line in enumerate(lines):
                        if "public static Wall " in line and var_name not in line:
                            lines[i] = line.rstrip(';') + f", {var_name};"
                            content = '\n'.join(lines)
                            break
                
                load_start = content.find("public static void Load() {")
                if load_start != -1:
                    open_brace = content.find('{', load_start)
                    if open_brace != -1:
                        insert_pos = open_brace + 1
                        indent = "        "
                        wall_code = f'\n{indent}{var_name} = new Wall("{constructor_name}"){{{{\n{indent}{properties}\n{indent}}}}};'
                        content = content[:insert_pos] + wall_code + content[insert_pos:]
                
                with open(block_registration_path, 'w', encoding='utf-8') as file:
                    file.write(content)
                
                try:
                    with open(main_mod_path, 'r', encoding='utf-8') as file:
                        main_content = file.read()
                    
                    import_statement = f"import {mod_name_lower}.init.blocks.walls.Walls;"
                    if import_statement not in main_content:
                        import_add_pos = main_content.find("//import_add")
                        if import_add_pos != -1:
                            insert_pos = import_add_pos + len("//import_add")
                            if insert_pos < len(main_content) and main_content[insert_pos] == '\n':
                                main_content = main_content[:insert_pos] + f"\n{import_statement}" + main_content[insert_pos:]
                            else:
                                main_content = main_content[:insert_pos] + f"\n{import_statement}" + main_content[insert_pos:]
                    
                    load_statement = "Walls.Load();"
                    if load_statement not in main_content:
                        registration_add_pos = main_content.find("//Registration_add")
                        if registration_add_pos != -1:
                            insert_pos = registration_add_pos + len("//Registration_add")
                            if insert_pos < len(main_content) and main_content[insert_pos] == '\n':
                                main_content = main_content[:insert_pos] + f"\n        {load_statement}" + main_content[insert_pos:]
                            else:
                                main_content = main_content[:insert_pos] + f"\n        {load_statement}" + main_content[insert_pos:]
                    
                    with open(main_mod_path, 'w', encoding='utf-8') as file:
                        file.write(main_content)
                    
                    status_messages = [
                        f"✅ Стена '{var_name}' успешно создана!",
                        f'📋 Имя в игре: "{constructor_name}"',
                        f"🖼️ {texture_status}",
                        f"🔧 Always Unlocked: {always_unlocked_value}",
                        "📊 Свойства стены:",
                        f"  • ❤️ Здоровье: {hp_value}",
                        f"  • ⚡ Скорость стройки: {speed_display}",
                        f"  • 📏 Размер: {size_value}",
                        f"  • 🔨 Предметы для стройки: {len(self.build_items)} шт."
                    ]
                    
                    if self.build_items:
                        item_counts = {}
                        for item in self.build_items:
                            item_counts[item] = item_counts.get(item, 0) + 1
                        
                        items_list = []
                        for item_name, count in item_counts.items():
                            if item_name in custom_items:
                                items_list.append(f"ModItems.{item_name} ×{count}")
                            else:
                                display_name = item_name.capitalize() if '-' not in item_name else ''.join(part.capitalize() for part in item_name.split('-'))
                                items_list.append(f"{display_name} ×{count}")
                        
                        status_messages.append(f"  • 📋 Список: {', '.join(items_list)}")
                    
                    status_text = "\n".join(status_messages)
                    status_label.configure(text=status_text, text_color="#4CAF50")
                    
                except Exception as e:
                    status_label.configure(text=f"❌ Ошибка: {str(e)}", text_color="#F44336")
            else:
                status_label.configure(text="⚠️ Стена уже существует", text_color="#FF9800")
            
            self.root.after(5000, lambda: status_label.configure(text=""))

        # === Кнопки действий ===
        buttons_frame = ctk.CTkFrame(button_frame, fg_color="transparent")
        buttons_frame.pack(pady=10)
        
        ctk.CTkButton(
            buttons_frame,
            text="🚀 Создать стену",
            command=process_wall,
            height=45,
            width=200,
            font=("Arial", 16, "bold"),
            fg_color="#2E7D32",
            hover_color="#1B5E20",
            corner_radius=10
        ).pack(side="left", padx=15)
        
        ctk.CTkButton(
            buttons_frame,
            text="← Назад",
            command=self.back_to_main,
            height=45,
            width=120,
            font=("Arial", 14),
            fg_color="#424242",
            hover_color="#616161",
            corner_radius=10
        ).pack(side="left", padx=15)

    def create_solar_panel(self):
        """Создает или добавляет новую солнечную панель в solar_panel/SolarPanels.java"""

        NAME = "SolarPanels" # Walls
        FOLDER = "solar_panels" # walls
        
        # Очищаем всё окно
        self.clear_window()
        
        # Основной фрейм с прокруткой
        main_frame = ctk.CTkFrame(self.root, fg_color="#2b2b2b")
        main_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Фрейм для прокрутки
        scroll_frame = ctk.CTkScrollableFrame(
            main_frame,
            width=500,
            height=600,
            fg_color="#2b2b2b"
        )
        scroll_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Заголовок
        title_frame = ctk.CTkFrame(scroll_frame, fg_color="transparent")
        title_frame.pack(fill="x", pady=(0, 20))
        
        ctk.CTkLabel(
            title_frame,
            text="Создание солнечной панели",
            font=("Arial", 24, "bold"),
            text_color="#4CAF50"
        ).pack(pady=10)
        
        # === Карточка для основной информации ===
        info_card = ctk.CTkFrame(
            scroll_frame,
            corner_radius=15,
            border_width=2,
            border_color="#404040",
            fg_color="#363636"
        )
        info_card.pack(fill="x", pady=(0, 20))
        
        ctk.CTkLabel(
            info_card,
            text="Основная информация",
            font=("Arial", 18, "bold"),
            text_color="#E0E0E0"
        ).pack(pady=(15, 10), padx=20, anchor="w")
        
        # Поле ввода названия
        name_frame = ctk.CTkFrame(info_card, fg_color="transparent")
        name_frame.pack(fill="x", padx=20, pady=(0, 15))
        
        ctk.CTkLabel(
            name_frame,
            text="Название солнечной панели (английское, можно пробел, первая буква маленькая):",
            font=("Arial", 16),
            text_color="#BDBDBD"
        ).pack(anchor="w", pady=(0, 5))
        
        entry_name = ctk.CTkEntry(
            name_frame,
            width=400,
            height=40,
            placeholder_text="solar panel name",
            font=("Arial", 15),
            border_width=2,
            corner_radius=8,
            fg_color="#424242",
            border_color="#555555",
            text_color="#FFFFFF",
            placeholder_text_color="#888888"
        )
        entry_name.pack(fill="x", pady=(0, 5))
        
        # === Функции валидации ===
        def validate_float_input(value):
            if value == "" or value == ".":
                return True
            pattern = r'^\d*\.?\d{0,2}$'
            if not re.match(pattern, value):
                return False
            try:
                return float(value) <= 5000.00
            except ValueError:
                return False

        def validate_int_input(value):
            if value == "":
                return True
            if not value.isdigit():
                return False
            return int(value) <= 999999

        def format_float(value):
            if not value:
                return ""
            try:
                num = float(value)
                num = min(num, 5000.00)
                formatted = f"{num:.2f}"
                if formatted.endswith(".00"):
                    formatted = formatted[:-3]
                elif formatted.endswith(".0"):
                    formatted = formatted[:-2]
                return formatted
            except ValueError:
                return value

        vcmd_float = (self.root.register(validate_float_input), '%P')
        vcmd_int = (self.root.register(validate_int_input), '%P')

        # === Карточка для свойств ===
        properties_card = ctk.CTkFrame(
            scroll_frame,
            corner_radius=15,
            border_width=2,
            border_color="#404040",
            fg_color="#363636"
        )
        properties_card.pack(fill="x", pady=(0, 20))

        ctk.CTkLabel(
            properties_card,
            text="Свойства солнечной панели",
            font=("Arial", 18, "bold"),
            text_color="#E0E0E0"
        ).pack(pady=(15, 10), padx=20, anchor="w")

        # Грид для свойств
        properties_grid = ctk.CTkFrame(properties_card, fg_color="transparent")
        properties_grid.pack(fill="x", padx=20, pady=(0, 15))

        # Здоровье
        hp_frame = ctk.CTkFrame(properties_grid, fg_color="transparent")
        hp_frame.grid(row=0, column=0, padx=10, pady=5, sticky="ew")
        
        ctk.CTkLabel(
            hp_frame,
            text="❤️ Здоровье (health):",
            font=("Arial", 15),
            text_color="#BDBDBD"
        ).pack(anchor="w", pady=(0, 5))
        
        entry_hp = ctk.CTkEntry(
            hp_frame,
            width=180,
            height=38,
            placeholder_text="400",
            font=("Arial", 14),
            validate="key",
            validatecommand=vcmd_int,
            fg_color="#424242",
            border_color="#555555",
            text_color="#FFFFFF",
            placeholder_text_color="#888888"
        )
        entry_hp.pack(fill="x")

        # Скорость
        speed_frame = ctk.CTkFrame(properties_grid, fg_color="transparent")
        speed_frame.grid(row=0, column=1, padx=10, pady=5, sticky="ew")
        
        ctk.CTkLabel(
            speed_frame,
            text="⚡ Скорость стройки (buildTime*10 \n в игре 1 сек если 10 \n авто умножения на 10):",
            font=("Arial", 15),
            text_color="#BDBDBD"
        ).pack(anchor="w", pady=(0, 5))
        
        entry_speed = ctk.CTkEntry(
            speed_frame,
            width=180,
            height=38,
            placeholder_text="1.0",
            font=("Arial", 14),
            validate="key",
            validatecommand=vcmd_float,
            fg_color="#424242",
            border_color="#555555",
            text_color="#FFFFFF",
            placeholder_text_color="#888888"
        )
        entry_speed.pack(fill="x")

        # Размер
        size_frame = ctk.CTkFrame(properties_grid, fg_color="transparent")
        size_frame.grid(row=1, column=0, padx=10, pady=5, sticky="ew")
        
        ctk.CTkLabel(
            size_frame,
            text="📏 Размер (size):",
            font=("Arial", 15),
            text_color="#BDBDBD"
        ).pack(anchor="w", pady=(0, 5))
        
        size_var = ctk.StringVar(value="1")
        size_combo = ctk.CTkComboBox(
            size_frame,
            values=[str(i) for i in range(1, 16)],
            variable=size_var,
            width=180,
            height=38,
            font=("Arial", 14)
        )
        size_combo.pack(fill="x")

        # Энергия
        power_frame = ctk.CTkFrame(properties_grid, fg_color="transparent")
        power_frame.grid(row=1, column=1, padx=10, pady=5, sticky="ew")
        
        ctk.CTkLabel(
            power_frame,
            text="⚡ Производства энергии (powerProduction % 60 \n если 1 то в игре 60 \n авто деления на 60):",
            font=("Arial", 15),
            text_color="#BDBDBD"
        ).pack(anchor="w", pady=(0, 5))
        
        entry_power = ctk.CTkEntry(
            power_frame,
            width=180,
            height=38,
            placeholder_text="1.0",
            font=("Arial", 14),
            validate="key",
            validatecommand=vcmd_float,
            fg_color="#424242",
            border_color="#555555",
            text_color="#FFFFFF",
            placeholder_text_color="#888888"
        )
        entry_power.pack(fill="x")

        # === Карточка для дополнительных опций ===
        options_card = ctk.CTkFrame(
            scroll_frame,
            corner_radius=15,
            border_width=2,
            border_color="#404040",
            fg_color="#363636"
        )
        options_card.pack(fill="x", pady=(0, 20))

        ctk.CTkLabel(
            options_card,
            text="Дополнительные опции",
            font=("Arial", 18, "bold"),
            text_color="#E0E0E0"
        ).pack(pady=(15, 10), padx=20, anchor="w")

        # Предметы строительства
        build_items_frame = ctk.CTkFrame(options_card, fg_color="transparent")
        build_items_frame.pack(fill="x", padx=20, pady=(0, 15))
        
        ctk.CTkLabel(
            build_items_frame,
            text="🔨 Предметы для строительства:",
            font=("Arial", 15),
            text_color="#BDBDBD"
        ).pack(anchor="w", pady=(0, 10))
        
        selected_items_var = tk.StringVar(value="Выбрано: 0 предметов")
        selected_items_label = ctk.CTkLabel(
            build_items_frame,
            textvariable=selected_items_var,
            font=("Arial", 12),
            text_color="#9E9E9E",
            wraplength=400
        )
        selected_items_label.pack(anchor="w", pady=(5, 0))
        
        ctk.CTkButton(
            build_items_frame,
            text="Выбрать предметы",
            command=lambda: self.open_build_items_editor(selected_items_var),
            height=35,
            font=("Arial", 13),
            fg_color="#2E7D32",
            hover_color="#1B5E20",
            corner_radius=6
        ).pack(anchor="w", pady=(0, 5))

        # Always Unlocked
        always_unlocked_var = ctk.BooleanVar(value=False)
        always_unlocked_frame = ctk.CTkFrame(options_card, fg_color="transparent")
        always_unlocked_frame.pack(fill="x", padx=20, pady=(0, 15))
        
        ctk.CTkCheckBox(
            always_unlocked_frame,
            text="🔓 Always Unlocked",
            variable=always_unlocked_var,
            font=("Arial", 15),
            text_color="#BDBDBD",
            border_width=2,
            corner_radius=6,
            fg_color="#4CAF50",
            hover_color="#45a049",
            border_color="#555555"
        ).pack(anchor="w", pady=5)

        # === Статус ===
        status_frame = ctk.CTkFrame(scroll_frame, fg_color="transparent")
        status_frame.pack(fill="x", pady=(0, 20))
        
        status_label = ctk.CTkLabel(
            status_frame,
            text="",
            font=("Arial", 14),
            wraplength=450,
            justify="left",
            text_color="#E0E0E0"
        )
        status_label.pack()

        # === Фрейм для кнопок ===
        button_frame = ctk.CTkFrame(scroll_frame, fg_color="transparent")
        button_frame.pack(fill="x", pady=20)
        
        # === Вспомогательные функции ===
        def format_to_lower_camel(text):
            words = text.strip().split()
            if not words:
                return ""
            result = words[0].lower()
            for word in words[1:]:
                result += word.capitalize()
            return result

        def copy_wall_texture(wall_name, size_multiplier):
            try:
                templates_dir = Path("creator/icons/blocks")
                if not templates_dir.exists():
                    return False
                
                template = templates_dir / "solar-panel.png"
                if not template.exists():
                    image_files = list(templates_dir.glob("*.png"))
                    if not image_files:
                        return False
                    template = image_files[0]
                
                texture_name = format_to_lower_camel(wall_name)
                target_name = texture_name + ".png"
                target_dir = Path(self.mod_folder) / "assets" / "sprites" / f"{FOLDER}"
                target_dir.mkdir(parents=True, exist_ok=True)
                target_path = target_dir / target_name
                
                img = Image.open(template)
                base_size = 32
                new_size = base_size * size_multiplier
                img = img.resize((new_size, new_size), Image.Resampling.LANCZOS)
                img.save(target_path)
                
                return True
            except Exception:
                return False

        def check_name_exists(name):
            formatted_name = format_to_lower_camel(name)
            name_lower = formatted_name
            check_paths = [
                Path(self.mod_folder) / "assets" / "sprites" / "items" / f"{name_lower}.png",
                Path(self.mod_folder) / "assets" / "sprites" / "liquids" / f"{name_lower}.png",
                Path(self.mod_folder) / "assets" / "sprites" / "walls" / f"{name_lower}.png",
                Path(self.mod_folder) / "assets" / "sprites" / "solar_panels" / f"{name_lower}.png"
            ]
            for path in check_paths:
                if path.exists():
                    return True
            return False

        def get_custom_items():
            custom_items = {}
            mod_name_lower = self.mod_name.lower() if self.mod_name else self.mod_name
            items_file_path = Path(self.mod_folder) / "src" / mod_name_lower / "init" / "items" / "ModItems.java"
            
            if items_file_path.exists():
                try:
                    with open(items_file_path, 'r', encoding='utf-8') as file:
                        content = file.read()
                    pattern = r'public\s+static\s+Item\s+(\w+);'
                    matches = re.findall(pattern, content)
                    for item_name in matches:
                        if item_name:
                            custom_items[item_name] = item_name
                except Exception:
                    return {}
            return custom_items

        def get_item_code_name(item_name, custom_items):
            if item_name in custom_items:
                return f"ModItems.{item_name}"
            
            vanilla_item_map = {
                "phase-fabric": "phaseFabric",
                "surge-alloy": "surgeAlloy",
                "spore-pod": "sporePod",
                "blast-compound": "blastCompound",
            }
            
            if item_name in vanilla_item_map:
                return f"Items.{vanilla_item_map[item_name]}"
            
            return f"Items.{item_name}"

        # === Основная функция создания стены ===
        def process_wall():
            original_name = entry_name.get().strip()
            
            if not original_name:
                status_label.configure(
                    text="❌ Ошибка: Введите название стены!", 
                    text_color="#F44336"
                )
                return
            
            constructor_name = format_to_lower_camel(original_name)
            if not constructor_name:
                status_label.configure(
                    text="❌ Ошибка: Некорректное название!", 
                    text_color="#F44336"
                )
                return

            if check_name_exists(original_name):
                status_label.configure(
                    text=f"❌ Ошибка: Имя '{constructor_name}' уже используется!", 
                    text_color="#F44336"
                )
                return
            
            size_multiplier = int(size_var.get())
            texture_copied = copy_wall_texture(original_name, size_multiplier)
            texture_status = "✅ Текстура создана" if texture_copied else "⚠️ Текстура не создана"
            
            hp_value = entry_hp.get().strip() or "400"
            speed_raw = entry_speed.get().strip() or "1.0"
            size_value = size_var.get()
            power_value = entry_power.get().strip() or "1"

            # Преобразуем buildTime (с плавающей точкой и умножением на 10)
            try:
                # Получаем исходное значение как число
                speed_float = float(speed_raw)
                # Умножаем на 10 для игры
                speed_val = speed_float * 10
                # Для отображения оставляем исходное значение
                speed_display = speed_raw
                # Для кода используем умноженное значение с суффиксом 'f'
                speed_code = f"{speed_val}f"
            except ValueError:
                speed_display = "1.0"
                speed_code = "10.0f"
            
            hp_value = str(int(hp_value))
            power_value = format_float(power_value)
            always_unlocked_value = "true" if always_unlocked_var.get() else "false"
            
            custom_items = get_custom_items()
            if constructor_name and len(constructor_name) > 0:
                var_name = constructor_name[0].lower() + constructor_name[1:] if constructor_name else ""
            else:
                var_name = ""
            
            itemstack_code = ""
            if self.build_items:
                item_counts = {}
                for item in self.build_items:
                    item_counts[item] = item_counts.get(item, 0) + 1
                
                item_parts = []
                for item_name, count in item_counts.items():
                    code_name = get_item_code_name(item_name, custom_items)
                    item_parts.append(f"{code_name}, {count}")
                
                itemstack_code = f"\n            requirements(Category.power,\n                ItemStack.with({', '.join(item_parts)}));"
            
            properties = f"""    health = {hp_value};
                size = {size_value};
                buildTime = {speed_code};
                alwaysUnlocked = {always_unlocked_value};
                buildVisibility = BuildVisibility.shown;
                category = Category.power;{itemstack_code}
                powerProduction = {float(power_value) / 60}f;
                
                localizedName = Core.bundle.get("{var_name}.name", "OH NO");
                description = Core.bundle.get("{var_name}.description", "OH NO");"""
            
            mod_name_lower = self.mod_name.lower() if self.mod_name else self.mod_name
            block_registration_path = Path(self.mod_folder) / "src" / mod_name_lower / "init" / "blocks" / f"{FOLDER}" / f"{NAME}.java"
            main_mod_path = Path(self.mod_folder) / "src" / mod_name_lower / f"{self.mod_name}JavaMod.java"
            
            block_registration_path.parent.mkdir(parents=True, exist_ok=True)
            
            try:
                with open(block_registration_path, 'r', encoding='utf-8') as file:
                    content = file.read()
            except FileNotFoundError:
                content = f"""package {mod_name_lower}.init.blocks.{FOLDER};

import arc.graphics.Color;
import mindustry.type.ItemStack;
import mindustry.type.Category;
import arc.Core;
import mindustry.world.Block;
import mindustry.world.blocks.power.SolarGenerator;
import mindustry.world.meta.BuildVisibility;
import mindustry.content.Items;
import mindustry.Vars;
import {mod_name_lower}.init.items.ModItems;

public class {NAME} {{
    public static SolarGenerator;
                                    
    public static void Load() {{
        // Регистрация блоков
    }}
}}"""

            solargenerator_exists = var_name in content
            if not solargenerator_exists:
                if "public static SolarGenerator;" in content:
                    content = content.replace(
                        "public static SolarGenerator;",
                        f"public static SolarGenerator {var_name};"
                    )
                elif "public static SolarGenerator " in content:
                    lines = content.split('\n')
                    for i, line in enumerate(lines):
                        if "public static SolarGenerator " in line and var_name not in line:
                            lines[i] = line.rstrip(';') + f", {var_name};"
                            content = '\n'.join(lines)
                            break
                
                load_start = content.find("public static void Load() {")
                if load_start != -1:
                    open_brace = content.find('{', load_start)
                    if open_brace != -1:
                        insert_pos = open_brace + 1
                        indent = "        "
                        solargenerator_code = f'\n{indent}{var_name} = new SolarGenerator("{constructor_name}"){{{{\n{indent}{properties}\n{indent}}}}};'
                        content = content[:insert_pos] + solargenerator_code + content[insert_pos:]
                
                with open(block_registration_path, 'w', encoding='utf-8') as file:
                    file.write(content)
                
                try:
                    with open(main_mod_path, 'r', encoding='utf-8') as file:
                        main_content = file.read()
                    
                    import_statement = f"import {mod_name_lower}.init.blocks.{FOLDER}.{NAME};"
                    if import_statement not in main_content:
                        import_add_pos = main_content.find("//import_add")
                        if import_add_pos != -1:
                            insert_pos = import_add_pos + len("//import_add")
                            if insert_pos < len(main_content) and main_content[insert_pos] == '\n':
                                main_content = main_content[:insert_pos] + f"\n{import_statement}" + main_content[insert_pos:]
                            else:
                                main_content = main_content[:insert_pos] + f"\n{import_statement}" + main_content[insert_pos:]
                    
                    load_statement = f"{NAME}.Load();"
                    if load_statement not in main_content:
                        registration_add_pos = main_content.find("//Registration_add")
                        if registration_add_pos != -1:
                            insert_pos = registration_add_pos + len("//Registration_add")
                            if insert_pos < len(main_content) and main_content[insert_pos] == '\n':
                                main_content = main_content[:insert_pos] + f"\n        {load_statement}" + main_content[insert_pos:]
                            else:
                                main_content = main_content[:insert_pos] + f"\n        {load_statement}" + main_content[insert_pos:]
                    
                    with open(main_mod_path, 'w', encoding='utf-8') as file:
                        file.write(main_content)
                    
                    status_messages = [
                        f"✅ Стена '{var_name}' успешно создана!",
                        f'📋 Имя в игре: "{constructor_name}"',
                        f"🖼️ {texture_status}",
                        f"🔧 Always Unlocked: {always_unlocked_value}",
                        "📊 Свойства стены:",
                        f"  • ❤️ Здоровье: {hp_value}",
                        f"  • ⚡ Скорость стройки: {speed_display}",
                        f"  • ⚡ powerProduction = {float(power_value) / 60}"
                        f"  • 📏 Размер: {size_value}",
                        f"  • 🔨 Предметы для стройки: {len(self.build_items)} шт."
                    ]
                    
                    if self.build_items:
                        item_counts = {}
                        for item in self.build_items:
                            item_counts[item] = item_counts.get(item, 0) + 1
                        
                        items_list = []
                        for item_name, count in item_counts.items():
                            if item_name in custom_items:
                                items_list.append(f"ModItems.{item_name} ×{count}")
                            else:
                                display_name = item_name.capitalize() if '-' not in item_name else ''.join(part.capitalize() for part in item_name.split('-'))
                                items_list.append(f"{display_name} ×{count}")
                        
                        status_messages.append(f"  • 📋 Список: {', '.join(items_list)}")
                    
                    status_text = "\n".join(status_messages)
                    status_label.configure(text=status_text, text_color="#4CAF50")
                    
                except Exception as e:
                    status_label.configure(text=f"❌ Ошибка: {str(e)}", text_color="#F44336")
            else:
                status_label.configure(text="⚠️ Стена уже существует", text_color="#FF9800")
            
            self.root.after(5000, lambda: status_label.configure(text=""))

        # === Кнопки действий ===
        buttons_frame = ctk.CTkFrame(button_frame, fg_color="transparent")
        buttons_frame.pack(pady=10)
        
        ctk.CTkButton(
            buttons_frame,
            text="🚀 Создать солнечную панель",
            command=process_wall,
            height=45,
            width=200,
            font=("Arial", 16, "bold"),
            fg_color="#2E7D32",
            hover_color="#1B5E20",
            corner_radius=10
        ).pack(side="left", padx=15)
        
        ctk.CTkButton(
            buttons_frame,
            text="← Назад",
            command=self.back_to_main,
            height=45,
            width=120,
            font=("Arial", 14),
            fg_color="#424242",
            hover_color="#616161",
            corner_radius=10
        ).pack(side="left", padx=15)

    def open_build_items_editor(self, selected_items_var):
        """Открывает редактор предметов для строительства"""
        editor_window = ctk.CTkToplevel(self.root)
        editor_window.title("Выбор предметов для строительства")
        editor_window.geometry("600x500")
        editor_window.configure(fg_color="#2b2b2b")
        editor_window.transient(self.root)
        editor_window.grab_set()
        
        main_frame = ctk.CTkFrame(editor_window, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        ctk.CTkLabel(
            main_frame,
            text="Выберите предметы и их количество",
            font=("Arial", 16, "bold")
        ).pack(pady=(0, 15))
        
        # Canvas для прокрутки
        canvas_frame = ctk.CTkFrame(main_frame, fg_color="#3a3a3a", corner_radius=8)
        canvas_frame.pack(fill="both", expand=True)
        
        canvas = tk.Canvas(canvas_frame, bg="#3a3a3a", highlightthickness=0)
        scrollbar = ctk.CTkScrollbar(canvas_frame, orientation="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)
        
        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True, padx=10, pady=10)
        
        items_frame = ctk.CTkFrame(canvas, fg_color="#3a3a3a")
        canvas.create_window((0, 0), window=items_frame, anchor="nw")
        
        # Получаем кастомные предметы
        def get_custom_items():
            custom_items = {}
            mod_name_lower = self.mod_name.lower() if self.mod_name else self.mod_name
            items_file_path = Path(self.mod_folder) / "src" / mod_name_lower / "init" / "items" / "ModItems.java"
            
            if items_file_path.exists():
                try:
                    with open(items_file_path, 'r', encoding='utf-8') as file:
                        content = file.read()
                    pattern = r'public\s+static\s+Item\s+(\w+);'
                    matches = re.findall(pattern, content)
                    for item_name in matches:
                        if item_name:
                            custom_items[item_name] = item_name
                except Exception:
                    pass
            return custom_items
        
        custom_items = get_custom_items()
        checkbox_vars = {}
        amount_vars = {}
        selected_count = tk.IntVar(value=0)
        
        def create_item_row(item_name, is_custom_item=False):
            row_frame = ctk.CTkFrame(items_frame, fg_color="transparent")
            row_frame.pack(fill="x", pady=2)
            
            checkbox_var = tk.BooleanVar(value=False)
            checkbox_vars[item_name] = checkbox_var
            
            def on_checkbox_change():
                if checkbox_var.get():
                    selected_count.set(selected_count.get() + 1)
                else:
                    selected_count.set(selected_count.get() - 1)
            
            ctk.CTkCheckBox(
                row_frame,
                text="",
                variable=checkbox_var,
                width=20,
                command=on_checkbox_change
            ).grid(row=0, column=0, padx=(5, 10))
            
            # Иконка
            icon_frame = ctk.CTkFrame(row_frame, fg_color="transparent", width=32, height=32)
            icon_frame.grid(row=0, column=1, padx=5)
            icon_frame.pack_propagate(False)
            
            try:
                if is_custom_item:
                    item_name_lower = item_name.lower()
                    icon_paths = [
                        Path(self.mod_folder) / "assets" / "sprites" / "items" / f"{item_name_lower}.png",
                        Path(self.mod_folder) / "sprites" / "items" / f"{item_name_lower}.png",
                    ]
                    icon_found = False
                    for icon_path in icon_paths:
                        if icon_path.exists():
                            img = Image.open(icon_path)
                            img = img.resize((32, 32), Image.Resampling.LANCZOS)
                            ctk_img = ctk.CTkImage(img, size=(32, 32))
                            ctk.CTkLabel(icon_frame, image=ctk_img, text="").pack()
                            icon_found = True
                            break
                    if not icon_found:
                        ctk.CTkLabel(icon_frame, text="📦", font=("Arial", 14)).pack()
                else:
                    icon_path = Path("creator/icons/items") / f"{item_name.lower()}.png"
                    if icon_path.exists():
                        img = Image.open(icon_path)
                        img = img.resize((32, 32), Image.Resampling.LANCZOS)
                        ctk_img = ctk.CTkImage(img, size=(32, 32))
                        ctk.CTkLabel(icon_frame, image=ctk_img, text="").pack()
                    else:
                        emoji = "📦"
                        if item_name == "copper": emoji = "🟫"
                        elif item_name == "lead": emoji = "🔩"
                        elif item_name == "metaglass": emoji = "🔮"
                        elif item_name == "graphite": emoji = "⬛"
                        elif item_name == "sand": emoji = "🟨"
                        elif item_name == "coal": emoji = "🪨"
                        elif item_name == "titanium": emoji = "🔷"
                        elif item_name == "thorium": emoji = "🟣"
                        elif item_name == "scrap": emoji = "⚙️"
                        elif item_name == "silicon": emoji = "💎"
                        elif item_name == "plastanium": emoji = "🟢"
                        elif item_name == "phase-fabric": emoji = "🌌"
                        elif item_name == "surge-alloy": emoji = "⚡"
                        elif item_name == "spore-pod": emoji = "🍄"
                        elif item_name == "blast-compound": emoji = "💥"
                        elif item_name == "pyratite": emoji = "🔥"
                        ctk.CTkLabel(icon_frame, text=emoji, font=("Arial", 14)).pack()
            except Exception:
                ctk.CTkLabel(icon_frame, text="📦", font=("Arial", 14)).pack()
            
            # Имя
            display_name = f"ModItems.{item_name}" if is_custom_item else item_name.replace("-", " ").title()
            ctk.CTkLabel(
                row_frame,
                text=display_name,
                font=("Arial", 12),
                width=150,
                anchor="w"
            ).grid(row=0, column=2, padx=5)
            
            if is_custom_item:
                ctk.CTkLabel(
                    row_frame,
                    text="(Мод)",
                    font=("Arial", 10),
                    text_color="#4CAF50",
                    width=40
                ).grid(row=0, column=3, padx=5)
            
            # Количество
            amount_var = tk.StringVar(value="1")
            amount_vars[item_name] = amount_var
            
            def validate_amount(value):
                if value == "":
                    return True
                if not value.isdigit():
                    return False
                return 1 <= int(value) <= 999
            
            vcmd_amount = (editor_window.register(validate_amount), '%P')
            
            amount_frame = ctk.CTkFrame(row_frame, fg_color="transparent")
            amount_frame.grid(row=0, column=4, padx=5)
            
            ctk.CTkLabel(amount_frame, text="Кол-во:", font=("Arial", 10)).pack(side="left", padx=(0, 5))
            
            ctk.CTkEntry(
                amount_frame,
                textvariable=amount_var,
                width=50,
                font=("Arial", 10),
                justify="center",
                validate="key",
                validatecommand=vcmd_amount
            ).pack(side="left")
            
            ctk.CTkLabel(amount_frame, text="шт", font=("Arial", 10)).pack(side="left", padx=(5, 0))
        
        # Создаем предметы
        for item in self.default_items:
            create_item_row(item, False)
        
        for item in custom_items:
            create_item_row(item, True)
        
        items_frame.update_idletasks()
        canvas.configure(scrollregion=canvas.bbox("all"))
        
        # Счетчик
        counter_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        counter_frame.pack(fill="x", pady=(10, 5))
        
        count_label = ctk.CTkLabel(
            counter_frame,
            textvariable=tk.StringVar(value="Выбрано: 0 предметов"),
            font=("Arial", 12, "bold"),
            text_color="#4CAF50"
        )
        count_label.pack()
        
        def update_counter(*args):
            count_label.configure(text=f"Выбрано: {selected_count.get()} предметов")
        
        selected_count.trace_add("write", update_counter)
        update_counter()
        
        # Кнопки
        button_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        button_frame.pack(fill="x", pady=(10, 0))
        
        def save_selection():
            self.build_items = []
            for item_name, checkbox_var in checkbox_vars.items():
                if checkbox_var.get():
                    try:
                        amount = int(amount_vars[item_name].get())
                        if amount > 0:
                            for _ in range(amount):
                                self.build_items.append(item_name)
                    except ValueError:
                        self.build_items.append(item_name)
            
            item_counts = {}
            for item in self.build_items:
                item_counts[item] = item_counts.get(item, 0) + 1
            
            items_list = []
            for item_name, count in item_counts.items():
                if item_name in custom_items:
                    items_list.append(f"ModItems.{item_name} ×{count}")
                else:
                    display_name = item_name.replace("-", " ").title()
                    items_list.append(f"{display_name} ×{count}")
            
            if items_list:
                display_text = f"Выбрано: {len(self.build_items)} предметов ({', '.join(items_list[:3])})"
                if len(items_list) > 3:
                    display_text += "..."
            else:
                display_text = "Выбрано: 0 предметов"
            
            selected_items_var.set(display_text)
            editor_window.destroy()
        
        def cancel_selection():
            editor_window.destroy()
        
        ctk.CTkButton(
            button_frame,
            text="💾 Сохранить", 
            width=140,
            height=35,
            font=("Arial", 13),
            command=save_selection
        ).pack(side="left", padx=20)
        
        ctk.CTkButton(
            button_frame,
            text="❌ Отмена", 
            width=140,
            height=35,
            font=("Arial", 13),
            fg_color="#e62525", 
            hover_color="#701c1c",
            command=cancel_selection
        ).pack(side="left", padx=20)
        
        def on_closing():
            cancel_selection()
        
        editor_window.protocol("WM_DELETE_WINDOW", on_closing)

    def clear_window(self):
        """Очистка окна"""
        for widget in self.root.winfo_children():
            widget.destroy()

def create_block_creator(editor_instance):
    """
    Создает экземпляр BlockCreator
    
    Args:
        editor_instance: Экземпляр основного редактора
    
    Returns:
        BlockCreator: Экземпляр класса с функциями создания блоков
    """
    return BlockCreator(editor_instance)