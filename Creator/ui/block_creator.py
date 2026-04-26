#p/Creator/ui/block_creator.py
import customtkinter as ctk
import tkinter as tk
import os
import re
from pathlib import Path
import shutil
from tkinter import messagebox
from PIL import Image, ImageTk
from tkinter import colorchooser

import sys
import os

def resource_path(relative_path):
    """Получить абсолютный путь к ресурсу (работает и в .py, и в .exe)"""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

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

        self.fuel_items = []  # Предметное топливо
        self.fuel_liquids = []  # Жидкое топливо
        self.default_liquids = ["water", "slag", "oil", "cryofluid"]
        self.current_fuel_type = None
        self.current_fuel_var = None

#----------ФУНКЦИИ----------
    def get_absolute_path(self, relative_path):
        """Возвращает абсолютный путь относительно папки мода"""
        if not self.mod_folder:
            return None
        return Path(self.mod_folder).absolute() / relative_path

    def format_to_lower_camel(self, text: str) -> str:
        """
        Преобразует текст в lowerCamelCase
        Пример: "copper wall" -> "copperWall", "phase-fabric" -> "phaseFabric"
        """
        if not text or not isinstance(text, str):
            return ""
        
        # Заменяем дефисы и подчеркивания на пробелы
        text = text.replace('-', ' ').replace('_', ' ')
        words = text.strip().split()
        
        if not words:
            return ""
        
        # Первое слово с маленькой буквы, остальные с большой
        result = words[0].lower()
        for word in words[1:]:
            if word:  # Проверяем, что слово не пустое
                result += word.capitalize()
        
        return result

    def setup_research_system(self, always_unlocked_var, research_card, 
                             always_unlocked_status, build_card,
                             selected_block_var, selected_block_internal_var,
                             selected_block_type_var, block_icon_label, 
                             block_path_label, research_items_var,
                             on_block_selected_callback=None):
        """
        Настраивает систему исследования для блока
        
        Args:
            always_unlocked_var: BooleanVar для Always Unlocked
            research_card: CTkFrame для карточки исследования
            always_unlocked_status: CTkLabel для отображения статуса
            build_card: CTkFrame карточки строительства (для позиционирования)
            selected_block_var: StringVar для отображения выбранного блока
            selected_block_internal_var: StringVar для внутреннего имени блока
            selected_block_type_var: StringVar для типа блока (mod/vanilla)
            block_icon_label: CTkLabel для иконки блока
            block_path_label: CTkLabel для пути к блоку
            research_items_var: StringVar для отображения выбранных предметов
            on_block_selected_callback: опциональный callback при выборе блока
        
        Returns:
            tuple: (always_unlocked_check, select_block_button, select_items_button)
        """
        
        # === Always Unlocked с индикатором ===
        always_unlocked_frame = ctk.CTkFrame(research_card.master, fg_color="transparent")
        always_unlocked_frame.pack(fill="x", padx=20, pady=(0, 15))
        
        def on_always_unlocked_change():
            """Показывает/скрывает карточку исследования и обновляет индикатор"""
            if always_unlocked_var.get():
                research_card.pack_forget()
                always_unlocked_status.configure(
                    text="✅ Always Unlocked (доступен с самого начала)",
                    text_color="#4CAF50"
                )
            else:
                research_card.pack(fill="x", pady=(0, 20), after=build_card)
                always_unlocked_status.configure(
                    text="🔒 Требуется исследование",
                    text_color="#FFA500"
                )
        
        always_unlocked_check = ctk.CTkCheckBox(
            always_unlocked_frame,
            text="🔓 Always Unlocked (блок сразу доступен)",
            variable=always_unlocked_var,
            command=on_always_unlocked_change,
            font=("Arial", 15),
            text_color="#BDBDBD",
            border_width=2,
            corner_radius=6,
            fg_color="#4CAF50",
            hover_color="#45a049",
            border_color="#555555"
        )
        always_unlocked_check.pack(anchor="w", pady=5)

        # Заголовок карточки исследования
        ctk.CTkLabel(
            research_card,
            text="🔬 Исследование (требуется для открытия)",
            font=("Arial", 18, "bold"),
            text_color="#FF9800"
        ).pack(pady=(15, 10), padx=20, anchor="w")

        # === БЛОК ДЛЯ ИССЛЕДОВАНИЯ ===
        block_res_frame = ctk.CTkFrame(research_card, fg_color="transparent")
        block_res_frame.pack(fill="x", padx=20, pady=(0, 15))
        
        ctk.CTkLabel(
            block_res_frame,
            text="🎯 Блок для исследования:",
            font=("Arial", 15, "bold"),
            text_color="#FF9800"
        ).pack(anchor="w", pady=(0, 10))
        
        # Фрейм для отображения выбранного блока
        selected_block_display = ctk.CTkFrame(block_res_frame, fg_color="#424242", corner_radius=8, height=80)
        selected_block_display.pack(fill="x", pady=(0, 10))
        selected_block_display.pack_propagate(False)
        
        # Иконка блока
        block_icon_frame = ctk.CTkFrame(selected_block_display, fg_color="transparent", width=60, height=60)
        block_icon_frame.pack(side="left", padx=10, pady=10)
        block_icon_frame.pack_propagate(False)
        
        # Сохраняем ссылку на иконку для обновления
        icon_display_label = ctk.CTkLabel(block_icon_frame, text="🧱", font=("Arial", 30))
        icon_display_label.pack(expand=True)
        
        # Информация о блоке
        block_info_frame = ctk.CTkFrame(selected_block_display, fg_color="transparent")
        block_info_frame.pack(side="left", fill="both", expand=True, padx=10, pady=10)
        
        block_name_display = ctk.CTkLabel(
            block_info_frame,
            textvariable=selected_block_var,
            font=("Arial", 14, "bold"),
            text_color="#FFFFFF",
            anchor="w"
        )
        block_name_display.pack(anchor="w")
        
        block_path_display = ctk.CTkLabel(
            block_info_frame,
            textvariable=block_path_label,
            font=("Arial", 10),
            text_color="#AAAAAA",
            anchor="w"
        )
        block_path_display.pack(anchor="w")
        
        # Кнопка выбора блока
        def wrapped_block_selector():
            def after_selection(display_name, internal_name, block_type, icon_name, block_emoji):
                selected_block_var.set(display_name)
                selected_block_internal_var.set(internal_name)
                selected_block_type_var.set(block_type)
                block_path_label.configure(text="Модовый блок" if block_type == "mod" else "Ванильный блок")
                icon_display_label.configure(text=block_emoji)
                
                if on_block_selected_callback:
                    on_block_selected_callback(internal_name, block_type)
            
            self.open_block_selector_universal(
                display_var=selected_block_var,
                internal_var=selected_block_internal_var,
                type_var=selected_block_type_var,
                icon_label=icon_display_label,
                path_label=block_path_label,
                callback=after_selection
            )
        
        select_block_button = ctk.CTkButton(
            block_res_frame,
            text="🔍 Выбрать блок",
            command=wrapped_block_selector,
            height=35,
            font=("Arial", 13),
            fg_color="#FF9800",
            hover_color="#F57C00",
            corner_radius=6
        )
        select_block_button.pack(anchor="w", pady=(0, 5))

        # === ПРЕДМЕТЫ ДЛЯ ИССЛЕДОВАНИЯ ===
        item_res_frame = ctk.CTkFrame(research_card, fg_color="transparent")
        item_res_frame.pack(fill="x", padx=20, pady=(0, 15))
        
        ctk.CTkLabel(
            item_res_frame,
            text="💰 Предметы для исследования:",
            font=("Arial", 15, "bold"),
            text_color="#FF9800"
        ).pack(anchor="w", pady=(0, 10))
        
        research_items_label = ctk.CTkLabel(
            item_res_frame,
            textvariable=research_items_var,
            font=("Arial", 12),
            text_color="#9E9E9E",
            wraplength=400
        )
        research_items_label.pack(anchor="w", pady=(5, 0))
        
        select_items_button = ctk.CTkButton(
            item_res_frame,
            text="📋 Выбрать предметы для исследования",
            command=lambda: self.open_items_editor(research_items_var, "research"),
            height=35,
            font=("Arial", 13),
            fg_color="#FF9800",
            hover_color="#F57C00",
            corner_radius=6
        )
        select_items_button.pack(anchor="w", pady=(0, 5))
        
        # Устанавливаем начальное состояние
        on_always_unlocked_change()
        
        return always_unlocked_check, select_block_button, select_items_button

    def validate_research(self, always_unlocked_var, research_items, selected_block_internal_var) -> tuple:
        """
        Проверяет корректность заполнения данных исследования
        
        Args:
            always_unlocked_var: BooleanVar для Always Unlocked
            research_items: список предметов для исследования
            selected_block_internal_var: StringVar с внутренним именем блока
        
        Returns:
            tuple: (is_valid, error_message)
        """
        if always_unlocked_var.get():
            return True, ""
        
        if not research_items:
            return False, "❌ Ошибка: Выберите предметы для исследования!"
        
        if not selected_block_internal_var.get():
            return False, "❌ Ошибка: Выберите блок для исследования!"
        
        return True, ""

    def create_tech_tree_file_universal(self, block_var_name: str, block_constructor_name: str,
                                    research_block: str, research_items: list,
                                    block_type: str, folder_name: str, 
                                    class_name: str = None) -> bool:
        """
        Универсальная функция создания файла дерева технологий
        
        Args:
            block_var_name: имя переменной блока
            block_constructor_name: имя конструктора блока
            research_block: блок для исследования
            research_items: список предметов [(item_name, count), ...]
            block_type: тип блока (wall, battery, solar, shield, power_node, beam_node, generator, crafter)
            folder_name: имя папки (walls, batterys, solar_panels, etc.)
            class_name: имя класса для дерева технологий (если None, генерируется из block_type)
        
        Returns:
            bool: успешно ли создан файл
        """
        try:
            mod_name_lower = self.mod_name.lower() if self.mod_name else self.mod_name
            
            # Определяем имя класса для дерева технологий
            if not class_name:
                # Преобразуем block_type в имя класса
                type_to_class = {
                    "wall": "WallsTree",
                    "battery": "BatteryTree",
                    "solar": "SolarTree",
                    "shield": "ShieldWallTree",
                    "power_node": "PowerNodeTree",
                    "beam_node": "BeamNodeTree",
                    "generator": "ConsumeGeneratorTree",
                    "crafter": "GenericCrafterTree"
                }
                class_name = type_to_class.get(block_type, f"{block_type.capitalize()}Tree")
            
            tree_file_path = Path(self.mod_folder) / "src" / mod_name_lower / "content" / f"{class_name}.java"
            tree_file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Формируем строку с предметами для исследования
            research_item_parts = []
            custom_items = self.get_custom_items()
            
            for item_name, count in research_items:
                code_name = self.get_item_code_name(item_name, custom_items)
                research_item_parts.append(f"{code_name}, {count}")
            
            research_items_stack = ", ".join(research_item_parts)
            
            # Определяем родительский блок
            if research_block.startswith("Blocks."):
                parent_block = research_block
                research_block_name = research_block
                parent_var_name = research_block.replace("Blocks.", "").replace(".", "_")
            elif "." in research_block:
                parent_block = research_block
                research_block_name = research_block
                parent_var_name = research_block.split(".")[-1]
            else:
                parent_block = f"Blocks.{research_block}"
                research_block_name = f"Blocks.{research_block}"
                parent_var_name = research_block
            
            parent_node_var = f"{parent_var_name}_{block_var_name}Node"
            block_node_var = f"{block_var_name}Node"
            
            # Определяем импорт для класса блока
            folder_to_import = {
                "walls": "walls.Walls",
                "batterys": "batterys.Batterys",
                "solar_panels": "solar_panels.SolarPanels",
                "shield_walls": "shield_walls.ShieldWalls",
                "power_nodes": "power_nodes.PowerNodes",
                "beam_nodes": "beam_nodes.BeamNodes",
                "consume_generators": "consume_generators.ConsumeGenerators",
                "generic_crafter": "generic_crafter.GenericCrafters"
            }
            
            import_path = folder_to_import.get(folder_name, folder_name)
            
            # Формируем код для нового узла (с правильными отступами)
            new_node_code = f"""
                    TechNode {parent_node_var} = {parent_block}.techNode;
                    
                    if ({parent_node_var} != null) {{
                        // Создаем узел для вашего блока
                        TechNode {block_node_var} = new TechNode(
                            {parent_node_var},
                            {block_var_name},
                            ItemStack.with({research_items_stack})
                        );
                        
                        // Добавляем условие - должен быть исследован указанный блок
                        {block_node_var}.objectives.add(new Research({research_block_name}));
                    }}"""
            
            # Проверяем, существует ли уже файл
            if tree_file_path.exists():
                # Читаем существующий файл
                with open(tree_file_path, 'r', encoding='utf-8') as file:
                    existing_content = file.read()
                
                # Проверяем, не добавлен ли уже этот блок
                if f"{block_node_var}" in existing_content:
                    print(f"Блок {block_var_name} уже есть в {class_name}.java")
                    return True
                
                # Находим место для вставки нового кода ВНУТРИ метода Load()
                lines = existing_content.split('\n')
                modified_lines = []
                inserted = False
                load_method_start = -1
                load_method_end = -1
                brace_count = 0
                in_load_method = False
                
                # Находим начало и конец метода Load()
                for i, line in enumerate(lines):
                    if 'public static void Load()' in line:
                        load_method_start = i
                        in_load_method = True
                        brace_count = 0
                    
                    if in_load_method:
                        brace_count += line.count('{') - line.count('}')
                        
                        # Когда закрыли все скобки метода Load()
                        if brace_count == 0 and in_load_method and i > load_method_start:
                            load_method_end = i
                            in_load_method = False
                
                if load_method_start != -1 and load_method_end != -1:
                    # Вставляем новый код ПЕРЕД закрывающей скобкой метода Load()
                    for i, line in enumerate(lines):
                        modified_lines.append(line)
                        
                        # Если это строка с закрывающей скобкой метода Load()
                        if i == load_method_end - 1:  # Вставляем перед последней строкой метода
                            modified_lines.append(new_node_code)
                            inserted = True
                            print(f"Вставлен код для {block_var_name} в метод Load() в {class_name}.java")
                    
                    if inserted:
                        # Записываем обновленное содержимое
                        new_content = '\n'.join(modified_lines)
                        with open(tree_file_path, 'w', encoding='utf-8') as file:
                            file.write(new_content)
                        print(f"✅ Файл {class_name}.java успешно обновлен")
                        return True
                else:
                    # Если не нашли метод Load(), создаем новый файл
                    print(f"Не найден метод Load() в {class_name}.java, создаем новый файл")
                    tree_content = f"""package {mod_name_lower}.content;

    import arc.struct.*;
    import mindustry.game.Objectives.*;
    import mindustry.type.*;
    import mindustry.content.*;
    import mindustry.content.TechTree.TechNode;
    import static mindustry.content.Blocks.*;
    import static {mod_name_lower}.init.blocks.{import_path}.*;

    public class {class_name} {{
        
        public static void Load() {{{new_node_code}
        }}
    }}"""
                    
                    with open(tree_file_path, 'w', encoding='utf-8') as file:
                        file.write(tree_content)
                    
                    print(f"✅ Файл {class_name}.java успешно пересоздан")
                    return True
            else:
                # Создаем новый файл с базовой структурой
                tree_content = f"""package {mod_name_lower}.content;

    import arc.struct.*;
    import mindustry.game.Objectives.*;
    import mindustry.type.*;
    import mindustry.content.*;
    import mindustry.content.TechTree.TechNode;
    import static mindustry.content.Blocks.*;
    import static {mod_name_lower}.init.blocks.{import_path}.*;

    public class {class_name} {{
        
        public static void Load() {{{new_node_code}
        }}
    }}"""
                
                with open(tree_file_path, 'w', encoding='utf-8') as file:
                    file.write(tree_content)
                
                print(f"✅ Файл {class_name}.java успешно создан")
                return True
                
        except Exception as e:
            print(f"❌ Ошибка создания файла дерева технологий: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _generate_tree_node_code(self, parent_node_var: str, block_node_var: str,
                                parent_block: str, block_var_name: str,
                                research_items_stack: str, research_block_name: str) -> str:
        """Генерирует код для узла дерева технологий (БЕЗ объявления переменной)"""
        return f"""
                    // Находим родительский узел для {block_var_name}
                    TechNode {parent_node_var} = {parent_block}.techNode;
                    
                    if ({parent_node_var} != null) {{
                        // Создаем узел для вашего блока
                        TechNode {block_node_var} = new TechNode(
                            {parent_node_var},
                            {block_var_name},
                            ItemStack.with({research_items_stack})
                        );
                        
                        // Добавляем условие - должен быть исследован указанный блок
                        {block_node_var}.objectives.add(new Research({research_block_name}));
                    }}"""

    def update_main_mod_file_universal(self, import_path: str, load_statement: str) -> bool:
        """
        Универсальная функция обновления главного файла мода
        
        Args:
            import_path: путь для импорта (например, "mymod.content.WallsTree")
            load_statement: вызов метода Load() (например, "WallsTree.Load();")
        
        Returns:
            bool: успешно ли обновлен файл
        """
        try:
            mod_name_lower = self.mod_name.lower() if self.mod_name else self.mod_name
            main_mod_path = Path(self.mod_folder) / "src" / mod_name_lower / f"{self.mod_name}JavaMod.java"
            
            if not main_mod_path.exists():
                print(f"⚠️ Главный файл мода не найден: {main_mod_path}")
                return False
            
            with open(main_mod_path, 'r', encoding='utf-8') as file:
                main_content = file.read()
            
            # Добавляем импорт если его нет
            if import_path not in main_content:
                # Ищем место для импорта
                package_end = main_content.find(";", main_content.find("package"))
                if package_end != -1:
                    main_content = main_content[:package_end+1] + "\n\n" + f"import {import_path};" + main_content[package_end+1:]
            
            # Добавляем вызов Load если его нет
            if load_statement not in main_content:
                # Ищем метод init или loadContent или маркер Registration_add
                patterns = ["public void init() {", "public void loadContent() {", "//Registration_add"]
                
                for pattern in patterns:
                    if pattern in main_content:
                        pos = main_content.find(pattern)
                        if pattern == "//Registration_add":
                            insert_pos = pos + len("//Registration_add")
                            if insert_pos < len(main_content) and main_content[insert_pos] == '\n':
                                main_content = main_content[:insert_pos] + f"\n        {load_statement}" + main_content[insert_pos:]
                            else:
                                main_content = main_content[:insert_pos] + f"\n        {load_statement}" + main_content[insert_pos:]
                            break
                        else:
                            open_brace = main_content.find('{', pos)
                            if open_brace != -1:
                                insert_pos = open_brace + 1
                                main_content = main_content[:insert_pos] + f"\n        {load_statement}" + main_content[insert_pos:]
                                break
            
            with open(main_mod_path, 'w', encoding='utf-8') as file:
                file.write(main_content)
            
            print(f"✅ Главный файл мода успешно обновлен")
            return True
            
        except Exception as e:
            print(f"❌ Ошибка обновления главного файла: {e}")
            return False

    def open_block_selector_universal(self, display_var, internal_var, type_var, 
                                    icon_label, path_label, callback=None):
        """
        Универсальная функция выбора блока с поддержкой callback
        
        Args:
            display_var: StringVar для отображения имени
            internal_var: StringVar для внутреннего имени
            type_var: StringVar для типа блока
            icon_label: CTkLabel для отображения иконки
            path_label: CTkLabel для отображения пути
            callback: функция, вызываемая после выбора (принимает display_name, internal_name, block_type, icon_name, block_emoji)
        """
        selector_window = ctk.CTkToplevel(self.root)
        selector_window.title("Выбор блока для исследования")
        selector_window.geometry("900x700")
        selector_window.configure(fg_color="#2b2b2b")
        selector_window.transient(self.root)
        selector_window.grab_set()
        
        main_frame = ctk.CTkFrame(selector_window, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        ctk.CTkLabel(
            main_frame,
            text="Выберите блок, который нужно исследовать для открытия",
            font=("Arial", 16, "bold")
        ).pack(pady=(0, 15))
        
        # Поисковая строка
        search_frame = ctk.CTkFrame(main_frame, fg_color="#363636", corner_radius=8)
        search_frame.pack(fill="x", pady=(0, 10))
        
        ctk.CTkLabel(search_frame, text="🔍", font=("Arial", 14)).pack(side="left", padx=10)
        
        search_var = tk.StringVar()
        search_entry = ctk.CTkEntry(
            search_frame,
            textvariable=search_var,
            placeholder_text="Поиск блока...",
            height=35,
            fg_color="#424242",
            border_width=0
        )
        search_entry.pack(side="left", fill="x", expand=True, padx=(0, 10), pady=5)
        
        # Создаем Notebook для вкладок
        notebook = ctk.CTkTabview(
            main_frame,
            width=860,
            height=520,
            fg_color="#363636",
            segmented_button_fg_color="#404040",
            segmented_button_selected_color="#4CAF50"
        )
        notebook.pack(fill="both", expand=True)
        
        # Вкладки
        mod_tab = notebook.add("📦 Блоки мода")
        vanilla_tab = notebook.add("🎮 Ванильные блоки")
        
        # Получаем блоки мода
        mod_blocks = self.get_mod_blocks_for_research_universal()
        
        # Получаем ванильные блоки
        vanilla_blocks = self._get_vanilla_blocks()
        
        def select_block(display_name, internal_name, block_type, icon_name="", block_emoji="🧱"):
            display_var.set(display_name)
            internal_var.set(internal_name)
            type_var.set(block_type)
            
            # Обновляем иконку и информацию - ИСПРАВЛЕНО
            if icon_label:
                icon_label.configure(text=block_emoji)
            path_label.configure(text="Модовый блок" if block_type == "mod" else "Ванильный блок")
            
            # Вызываем callback если есть
            if callback:
                callback(display_name, internal_name, block_type, icon_name, block_emoji)
            
            selector_window.destroy()
        
        def display_blocks():
            search_text = search_var.get().lower()
            
            # Очищаем вкладки
            for widget in mod_tab.winfo_children():
                widget.destroy()
            for widget in vanilla_tab.winfo_children():
                widget.destroy()
            
            # Отображаем модовые блоки
            self._display_mod_blocks(mod_tab, mod_blocks, search_text, select_block)
            
            # Отображаем ванильные блоки
            self._display_vanilla_blocks(vanilla_tab, vanilla_blocks, search_text, select_block)
        
        # Привязываем поиск
        search_var.trace_add("write", lambda *args: display_blocks())
        
        # Первоначальное отображение
        display_blocks()
        
        # Кнопка отмены
        button_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        button_frame.pack(pady=10)
        
        cancel_btn = ctk.CTkButton(
            button_frame,
            text="❌ Отмена",
            width=120,
            height=35,
            font=("Arial", 12),
            fg_color="#e62525",
            hover_color="#701c1c",
            command=selector_window.destroy
        )
        cancel_btn.pack()

    def get_mod_blocks_for_research_universal(self):
        """Получает список блоков из мода для исследования с указанием типа папки"""
        mod_blocks = {}
        mod_name_lower = self.mod_name.lower() if self.mod_name else self.mod_name
        
        # Пути к файлам с блоками
        block_files = [
            ("walls", f"src/{mod_name_lower}/init/blocks/walls/Walls.java", "🧱 Стены"),
            ("solar_panels", f"src/{mod_name_lower}/init/blocks/solar_panels/SolarPanels.java", "☀️ Солнечные панели"),
            ("batterys", f"src/{mod_name_lower}/init/blocks/batterys/Batterys.java", "🔋 Батареи"),
            ("consume_generators", f"src/{mod_name_lower}/init/blocks/consume_generators/ConsumeGenerators.java", "⚡ Генераторы"),
            ("beam_nodes", f"src/{mod_name_lower}/init/blocks/beam_nodes/BeamNodes.java", "📡 Энерг. башни"),
            ("power_nodes", f"src/{mod_name_lower}/init/blocks/power_nodes/PowerNodes.java", "🔌 Энерг. узлы"),
            ("shield_walls", f"src/{mod_name_lower}/init/blocks/shield_walls/ShieldWalls.java", "🛡️ Щитовые стены"),
            ("generic_crafter", f"src/{mod_name_lower}/init/blocks/generic_crafter/GenericCrafters.java", "🏭 Заводы"),
            ("bridges", f"src/{mod_name_lower}/init/blocks/bridges/Bridges.java", "Мосты")
        ]
        
        for folder, file_path, display_prefix in block_files:
            full_path = Path(self.mod_folder) / file_path
            if full_path.exists():
                try:
                    with open(full_path, 'r', encoding='utf-8') as file:
                        content = file.read()
                    
                    # Ищем объявления блоков
                    patterns = [
                        r'public\s+static\s+\w+\s+(\w+)\s*=\s*new\s+\w+\("([^"]+)"\)',
                        r'public\s+static\s+final\s+\w+\s+(\w+)\s*=\s*new\s+\w+\("([^"]+)"\)',
                        r'(\w+)\s*=\s*new\s+\w+\("([^"]+)"\)',
                    ]
                    
                    for pattern in patterns:
                        matches = re.findall(pattern, content)
                        for match in matches:
                            if isinstance(match, tuple) and len(match) >= 2:
                                var_name = match[0]
                                internal_name = match[1]
                                if var_name and var_name not in mod_blocks:
                                    mod_blocks[var_name] = (f"{display_prefix} - {internal_name}", folder)
                            elif isinstance(match, str):
                                var_name = match
                                if var_name and var_name not in mod_blocks:
                                    mod_blocks[var_name] = (f"{display_prefix} - {var_name}", folder)
                    
                    # Ищем просто объявления переменных
                    var_pattern = r'public\s+static\s+\w+\s+(\w+);'
                    var_matches = re.findall(var_pattern, content)
                    for var_name in var_matches:
                        if var_name and var_name not in mod_blocks and var_name not in ["CATENAME", "NAME", "CATEDOR"]:
                            mod_blocks[var_name] = (f"{display_prefix} - {var_name}", folder)
                            
                except Exception as e:
                    print(f"Ошибка чтения {full_path}: {e}")
        
        return mod_blocks
    
    def _get_vanilla_blocks(self):
        """Получает список ванильных блоков"""
        vanilla_blocks = []
        blocks_dir = Path(resource_path("Creator/icons/blocks"))
        
        # Черный список для фильтрации
        blacklist_blocks = ["beam-node", "shielded-wall", "bridge-conveyor-arrow", "bridge-conveyor-bridge", "bridge-conveyor-end"]
        blacklist_suffixes = [
            "-top", "-bottom", "-left", "-right", "-back", "-front",
            "-glow", "-overlay", "-mask", "-shadow", "-effect",
            "-top-1", "-top-2", "-top-3", "-cap", "-liquid",
            "-bottom-1", "-bottom-2", "-turbine",
            "-edge", "-corner", "-middle",
            "-1", "-2", "-3", "-4", "-5",
            "-a", "-b", "-c", "-d",
            "_top", "_bottom", "_left", "_right",
            "_glow", "_overlay", "_mask",
            "_1", "_2", "_3", "_4", "_5"
        ]
        blacklist_exact = [
            "item-", "liquid-", "ui-", "icon-",
            "background", "white", "black", "transparent",
            "error", "missing", "unknown", "empty",
            "block-icon", "block-background"
        ]
        
        def kebab_to_camel(name):
            """Преобразует kebab-case в camelCase"""
            if not name:
                return name
            parts = name.split('-')
            result = parts[0]
            for part in parts[1:]:
                if part:
                    result += part.capitalize()
            return result
        
        if blocks_dir.exists():
            all_textures = list(blocks_dir.glob("*.png"))
            
            for texture_path in all_textures:
                filename = texture_path.stem
                
                # Фильтрация
                if filename in blacklist_blocks:
                    continue
                
                if any(filename.endswith(suffix) for suffix in blacklist_suffixes):
                    continue
                
                if any(filename.startswith(exact) or filename == exact for exact in blacklist_exact):
                    continue
                
                if len(filename) < 3:
                    continue
                
                # Создаем отображаемое имя
                display_name = filename.replace("-", " ").replace("_", " ").title()
                
                # Определяем тип блока для эмодзи
                if "wall" in filename.lower():
                    block_emoji = "🧱"
                elif "generator" in filename.lower() or "reactor" in filename.lower():
                    block_emoji = "⚡"
                elif "battery" in filename.lower():
                    block_emoji = "🔋"
                elif "solar" in filename.lower():
                    block_emoji = "☀️"
                elif "node" in filename.lower() or "beam" in filename.lower():
                    block_emoji = "📡"
                elif "conveyor" in filename.lower() or "conduit" in filename.lower():
                    block_emoji = "🔄"
                elif "drill" in filename.lower():
                    block_emoji = "⛏️"
                elif "factory" in filename.lower() or "press" in filename.lower():
                    block_emoji = "🏭"
                else:
                    block_emoji = "🧱"
                
                # Внутреннее имя в camelCase
                internal_name = kebab_to_camel(filename)
                
                vanilla_blocks.append((
                    internal_name,
                    display_name,
                    filename,
                    block_emoji
                ))
            
            vanilla_blocks.sort(key=lambda x: x[1])
        
        return vanilla_blocks

    def _display_mod_blocks(self, parent_tab, mod_blocks, search_text, select_callback):
        """Отображает модовые блоки в указанной вкладке"""
        scroll = ctk.CTkScrollableFrame(parent_tab, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Фильтруем
        filtered = {}
        for block_name, (display_name, folder_type) in mod_blocks.items():
            if search_text in display_name.lower() or search_text in block_name.lower():
                filtered[block_name] = (display_name, folder_type)
        
        if filtered:
            row_frame = None
            col_count = 0
            
            for block_name, (display_name, folder_type) in filtered.items():
                if col_count % 3 == 0:
                    row_frame = ctk.CTkFrame(scroll, fg_color="transparent")
                    row_frame.pack(fill="x", pady=2)
                
                # Определяем эмодзи для модового блока
                if "wall" in folder_type.lower():
                    block_emoji = "🧱"
                elif "generator" in folder_type.lower():
                    block_emoji = "⚡"
                elif "battery" in folder_type.lower():
                    block_emoji = "🔋"
                elif "solar" in folder_type.lower():
                    block_emoji = "☀️"
                elif "node" in folder_type.lower():
                    block_emoji = "📡"
                else:
                    block_emoji = "🧱"
                
                # Для модовых блоков icon_info оставляем пустым
                self._create_block_card(
                    row_frame, display_name, block_name, 
                    block_emoji, "mod", "", select_callback  # icon_info = ""
                )
                
                col_count += 1
        else:
            ctk.CTkLabel(
                scroll,
                text="📭 Нет блоков по вашему запросу",
                font=("Arial", 14),
                text_color="#888888"
            ).pack(pady=50)

    def _display_vanilla_blocks(self, parent_tab, vanilla_blocks, search_text, select_callback):
        """Отображает ванильные блоки в указанной вкладке"""
        scroll = ctk.CTkScrollableFrame(parent_tab, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Фильтруем
        filtered = []
        for internal_name, display_name, icon_name, block_emoji in vanilla_blocks:
            if (search_text in display_name.lower() or 
                search_text in internal_name.lower() or 
                search_text in icon_name.lower()):
                filtered.append((internal_name, display_name, icon_name, block_emoji))
        
        if filtered:
            row_frame = None
            col_count = 0
            
            for internal_name, display_name, icon_name, block_emoji in filtered:
                if col_count % 3 == 0:
                    row_frame = ctk.CTkFrame(scroll, fg_color="transparent")
                    row_frame.pack(fill="x", pady=2)
                
                # Для ванильных блоков передаем icon_name как icon_info
                self._create_block_card(
                    row_frame, display_name, f"Blocks.{internal_name}", 
                    block_emoji, "vanilla", icon_name, select_callback
                )
                
                col_count += 1
        else:
            ctk.CTkLabel(
                scroll,
                text="🎮 Нет блоков по вашему запросу",
                font=("Arial", 14),
                text_color="#888888"
            ).pack(pady=50)

    def _create_block_card(self, parent, display_name, internal_name, 
                        block_emoji, block_type, icon_info, select_callback):
        """Создает карточку блока для выбора"""
        card = ctk.CTkFrame(
            parent,
            fg_color="#404040",
            corner_radius=8,
            width=250,
            height=180
        )
        card.pack(side="left", padx=5, pady=5, fill="both", expand=True)
        card.pack_propagate(False)
        
        # Иконка - создаем фрейм для иконки
        icon_frame = ctk.CTkFrame(card, fg_color="transparent", height=60)
        icon_frame.pack(fill="x", padx=10, pady=(10, 5))
        icon_frame.pack_propagate(False)
        
        # Загружаем иконку в зависимости от типа блока
        icon_label = ctk.CTkLabel(icon_frame, text="", font=("Arial", 30))
        icon_label.pack(expand=True)
        
        # Загружаем иконку
        self._load_block_icon(icon_label, internal_name, block_type, icon_info, block_emoji)
        
        # Название
        ctk.CTkLabel(
            card,
            text=display_name,
            font=("Arial", 12, "bold"),
            text_color="#FFFFFF",
            wraplength=230
        ).pack(pady=(0, 2))
        
        # Внутреннее имя
        ctk.CTkLabel(
            card,
            text=internal_name,
            font=("Arial", 9),
            text_color="#AAAAAA"
        ).pack()
        
        # Кнопка выбора
        ctk.CTkButton(
            card,
            text="Выбрать",
            width=100,
            height=30,
            font=("Arial", 11),
            fg_color="#4CAF50",
            hover_color="#45a049",
            command=lambda: select_callback(
                display_name, internal_name, block_type, 
                icon_info if block_type == "vanilla" else "", 
                block_emoji
            )
        ).pack(pady=(5, 10))

    def _load_block_icon(self, icon_label, block_name, block_type, icon_info="", block_emoji="🧱"):
        """Загружает иконку для блока"""
        try:
            icon_path = None

            if block_type == "mod":
                # Список папок для модовых блоков
                BLOCKS_PATHS = ["walls", "batterys", "solar_panels", "consume_generators",
                            "beam_nodes", "power_nodes", "shield_walls", "generic_crafter",
                            "bridges"]

                # Перебираем все возможные папки
                for folder in BLOCKS_PATHS:
                    # Формируем возможные пути для текущей папки
                    possible_paths = [
                        # В assets/sprites/blocks/[folder]/[block_name].png
                        Path(self.mod_folder) / "assets" / "sprites" / "blocks" / folder / f"{block_name}.png",
                        # В sprites/blocks/[folder]/[block_name].png (без assets)
                        Path(self.mod_folder) / "sprites" / "blocks" / folder / f"{block_name}.png",
                        #В подпапке с именем блока
                        Path(self.mod_folder) / "assets" / "sprites" / "blocks" / folder / block_name / f"{block_name}.png"
                    ]

                    # Проверяем каждый путь
                    for path in possible_paths:
                        if path.exists():
                            icon_path = path
                            #print(f"Найдена иконка для модового блока {block_name}: {path}")
                            break

                    # Если иконка найдена, прерываем поиск по остальным папкам
                    if icon_path:
                        break

            else:  # vanilla
                # Для ванильных блоков — ищем в creator/icons/blocks
                icon_filename = icon_info if icon_info else block_name

                # Убираем "Blocks." если есть
                if icon_filename.startswith("Blocks."):
                    icon_filename = icon_filename.replace("Blocks.", "")

                # Пробуем разные варианты имён
                possible_names = [
                    icon_filename,
                    icon_filename.lower(),
                    icon_filename.replace(" ", "-").lower(),
                    icon_filename.replace(" ", "_").lower(),
                    icon_filename.replace("-", ""),
                    icon_filename.lower().replace("wall", ""),
                ]

                # Добавляем варианты с суффиксами
                extended_names = []
                for name in possible_names:
                    extended_names.append(name)
                    extended_names.append(f"{name}-icon")
                    extended_names.append(f"{name}-block")

                for name in extended_names:
                    test_path = Path("creator/icons/blocks") / f"{name}.png"
                    if test_path.exists():
                        icon_path = test_path
                        #print(f"Найдена иконка для ванильного блока {block_name}: {test_path}")
                        break

            # Загрузка и обработка изображения
            if icon_path and icon_path.exists():
                img = Image.open(icon_path)
                img = img.resize((48, 48), Image.Resampling.LANCZOS)
                ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=(48, 48))
                icon_label.configure(image=ctk_img, text="")
            else:
                # Если иконка не найдена, показываем эмодзи
                print(f"Иконка не найдена для {block_name}, используем эмодзи {block_emoji}")
                icon_label.configure(text=block_emoji, image=None)

        except Exception as e:
            print(f"Ошибка загрузки иконки для {block_name}: {e}")
            icon_label.configure(text=block_emoji, image=None)

    def copy_block_texture(self, block_name: str, size_multiplier: int, 
                       target_folder: str, template_names: list = None) -> bool:
        """
        Универсальный метод копирования текстур блоков
        
        Args:
            block_name: имя блока
            size_multiplier: множитель размера (1, 2, 3...)
            target_folder: папка назначения (walls, batterys, etc.)
            template_names: список возможных имен шаблонов (если None, ищет любой PNG)
        
        Returns:
            bool: успешно ли скопирована текстура
        """
        try:
            templates_dir = Path(resource_path("Creator/icons/blocks"))
            if not templates_dir.exists():
                print(f"Папка с шаблонами не найдена: {templates_dir}")
                return False
            
            # Определяем шаблон для копирования
            template = None
            if template_names:
                for template_name in template_names:
                    test_path = templates_dir / template_name
                    if test_path.exists():
                        template = test_path
                        print(f"Найден шаблон: {template_name}")
                        break
            
            # Если шаблон не найден, берем первый доступный PNG
            if not template:
                image_files = list(templates_dir.glob("*.png"))
                if not image_files:
                    print("В папке нет PNG файлов")
                    return False
                template = image_files[0]
                print(f"Используется первый доступный шаблон: {template.name}")
            
            # Формируем имя текстуры
            texture_name = self.format_to_lower_camel(block_name)
            
            # Создаем целевую папку
            target_dir = Path(self.mod_folder) / "assets" / "sprites" / "blocks" / target_folder
            target_dir.mkdir(parents=True, exist_ok=True)
            
            # Загружаем и изменяем размер
            img = Image.open(template)
            base_size = 32
            new_size = base_size * size_multiplier
            img = img.resize((new_size, new_size), Image.Resampling.LANCZOS)
            
            # Сохраняем
            target_path = target_dir / f"{texture_name}.png"
            img.save(target_path)
            
            print(f"Текстура сохранена: {target_path}")
            return True
            
        except Exception as e:
            print(f"Ошибка копирования текстуры для {block_name}: {e}")
            return False
    
    def copy_block_textures_multi(self, block_name: str, size_multiplier: int,
                              target_folder: str, texture_configs: list) -> bool:
        """
        Копирует несколько текстур для одного блока
        
        Args:
            block_name: имя блока
            size_multiplier: множитель размера
            target_folder: папка назначения
            texture_configs: список конфигураций текстур [
                {"template": "battery.png", "suffix": ""},
                {"template": "battery-top.png", "suffix": "-top"},
            ]
        
        Returns:
            bool: успешно ли скопированы все текстуры
        """
        try:
            templates_dir = Path(resource_path("Creator/icons/blocks"))
            if not templates_dir.exists():
                return False
            
            texture_name = self.format_to_lower_camel(block_name)
            target_dir = Path(self.mod_folder) / "assets" / "sprites" / "blocks" / target_folder / texture_name
            target_dir.mkdir(parents=True, exist_ok=True)
            
            base_size = 32
            new_size = base_size * size_multiplier
            success = True
            
            for config in texture_configs:
                template_path = templates_dir / config["template"]
                
                # Если шаблон не найден, пробуем другие варианты
                if not template_path.exists():
                    # Ищем похожие файлы
                    similar_files = list(templates_dir.glob(f"*{config['template']}*"))
                    if similar_files:
                        template_path = similar_files[0]
                    else:
                        print(f"Шаблон {config['template']} не найден, пропускаем")
                        success = False
                        continue
                
                try:
                    img = Image.open(template_path)
                    img = img.resize((new_size, new_size), Image.Resampling.LANCZOS)
                    
                    # Формируем имя файла
                    if config.get("suffix"):
                        target_filename = f"{texture_name}{config['suffix']}.png"
                    else:
                        target_filename = f"{texture_name}.png"
                    
                    target_path = target_dir / target_filename
                    img.save(target_path)
                    #print(f"Сохранена текстура: {target_path}")
                    
                except Exception as e:
                    print(f"Ошибка при обработке {config['template']}: {e}")
                    success = False
            
            return success
            
        except Exception as e:
            print(f"Ошибка копирования текстур: {e}")
            return False
    
    def check_block_name_exists(self, name: str, additional_folders: list = None) -> bool:
        """
        Проверяет, существует ли уже блок с таким именем
        
        Args:
            name: имя для проверки
            additional_folders: дополнительные папки для проверки (если None, используются все)
        
        Returns:
            bool: True если имя уже используется
        """
        formatted_name = self.format_to_lower_camel(name)
        
        # Стандартные папки для проверки
        standard_folders = [
            "consume_generators", "walls", "solar_panels",
            "batterys", "beam_nodes", "power_nodes", "shield_walls",
            "generic_crafter"
        ]
        
        # Используем переданные папки или стандартные
        folders_to_check = additional_folders if additional_folders else standard_folders
        
        # Формируем пути для проверки
        check_paths = [
            # Предметы и жидкости
            Path(self.mod_folder) / "assets" / "sprites" / "items" / f"{formatted_name}.png",
            Path(self.mod_folder) / "assets" / "sprites" / "liquids" / f"{formatted_name}.png",
        ]
        
        # Блоки в разных папках
        for folder in folders_to_check:
            check_paths.append(
                Path(self.mod_folder) / "assets" / "sprites" / "blocks" / folder / f"{formatted_name}.png"
            )
            # Также проверяем в подпапках с именем блока
            check_paths.append(
                Path(self.mod_folder) / "assets" / "sprites" / "blocks" / folder / formatted_name / f"{formatted_name}.png"
            )
        
        # Проверяем существование
        for path in check_paths:
            if path.exists():
                print(f"Найден существующий файл: {path}")
                return True
        
        return False

    def get_custom_items(self, force_refresh: bool = False) -> dict:
        """
        Получает кастомные предметы из мода с кэшированием
        
        Args:
            force_refresh: принудительно обновить кэш
        
        Returns:
            dict: словарь кастомных предметов
        """
        # Используем кэш, если не нужно обновление
        if hasattr(self, '_custom_items_cache') and not force_refresh:
            return self._custom_items_cache
        
        custom_items = {}
        mod_name_lower = self.mod_name.lower() if self.mod_name else self.mod_name
        items_file_path = Path(self.mod_folder) / "src" / mod_name_lower / "init" / "items" / "ModItems.java"
        
        if items_file_path.exists():
            try:
                with open(items_file_path, 'r', encoding='utf-8') as file:
                    content = file.read()
                
                # Ищем объявления предметов
                patterns = [
                    r'public\s+static\s+Item\s+(\w+);',
                    r'public\s+static\s+final\s+Item\s+(\w+);',
                    r'public\s+static\s+Item\s+(\w+)\s*=',
                ]
                
                for pattern in patterns:
                    matches = re.findall(pattern, content)
                    for item_name in matches:
                        if item_name and item_name not in custom_items:
                            custom_items[item_name] = item_name
                            
            except Exception as e:
                print(f"Ошибка чтения ModItems: {e}")
        
        # Сохраняем в кэш
        self._custom_items_cache = custom_items
        return custom_items

    def get_custom_liquids(self, force_refresh: bool = False) -> dict:
        """
        Получает кастомные жидкости из мода с кэшированием
        """
        if hasattr(self, '_custom_liquids_cache') and not force_refresh:
            return self._custom_liquids_cache
        
        custom_liquids = {}
        mod_name_lower = self.mod_name.lower() if self.mod_name else self.mod_name
        liquids_file_path = Path(self.mod_folder) / "src" / mod_name_lower / "init" / "liquids" / "ModLiquids.java"
        
        if liquids_file_path.exists():
            try:
                with open(liquids_file_path, 'r', encoding='utf-8') as file:
                    content = file.read()
                
                patterns = [
                    r'public\s+static\s+Liquid\s+(\w+);',
                    r'public\s+static\s+final\s+Liquid\s+(\w+);',
                ]
                
                for pattern in patterns:
                    matches = re.findall(pattern, content)
                    for liquid_name in matches:
                        if liquid_name:
                            custom_liquids[liquid_name] = liquid_name
                            
            except Exception as e:
                print(f"Ошибка чтения ModLiquids: {e}")
        
        self._custom_liquids_cache = custom_liquids
        return custom_liquids

    def get_item_code_name(self, item_name: str, custom_items: dict = None) -> str:
        """
        Возвращает Java-код для предмета
        
        Args:
            item_name: имя предмета
            custom_items: словарь кастомных предметов (если None, будет получен автоматически)
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

    def get_liquid_code_name(self, liquid_name: str, custom_liquids: dict = None) -> str:
        """
        Возвращает Java-код для жидкости
        """
        if custom_liquids is None:
            custom_liquids = self.get_custom_liquids()
        
        if liquid_name in custom_liquids:
            return f"ModLiquids.{liquid_name}"
        
        vanilla_liquid_map = {
            "water": "water",
            "slag": "slag",
            "oil": "oil",
            "cryofluid": "cryofluid"
        }
        
        if liquid_name in vanilla_liquid_map:
            return f"Liquids.{vanilla_liquid_map[liquid_name]}"
        
        if '-' in liquid_name:
            parts = liquid_name.split('-')
            camel_name = parts[0] + ''.join(p.capitalize() for p in parts[1:])
            return f"Liquids.{camel_name}"
        
        return f"Liquids.{liquid_name}"

    def back_to_main(self):
        """Возврат к основному интерфейсу редактора"""
        self.clear_window()
        self.editor.open_creator()

    #CircularBridge
    def circularBridge(self):
        """Создает файл CircularBridge.java для кастомного типа блока"""
        
        # Формируем имя пакета (нижний регистр)
        package_name = self.mod_name.lower() if self.mod_name else self.mod_name
        
        # Содержимое файла с правильными плейсхолдерами
        content = f"""package {package_name}.custom_types.blocks.bridge;

import arc.Core;
import arc.graphics.g2d.Draw;
import arc.graphics.g2d.Lines;
import arc.graphics.g2d.TextureRegion;
import arc.math.Angles;
import arc.math.Mathf;
import arc.math.geom.Geometry;
import arc.math.geom.Point2;
import arc.struct.Seq;
import arc.util.Time;
import arc.util.Tmp;
import static mindustry.Vars.tilesize;
import static mindustry.Vars.world;
import mindustry.core.Renderer;
import mindustry.gen.Building;
import mindustry.graphics.Drawf;
import mindustry.graphics.Layer;
import mindustry.graphics.Pal;
import mindustry.input.Placement;
import mindustry.type.Item;
import mindustry.ui.Bar;
import mindustry.world.Tile;
import mindustry.world.blocks.distribution.ItemBridge;
import mindustry.world.meta.Stat;
import mindustry.world.meta.StatUnit;

public class CircularBridge extends ItemBridge {{
    
    public TextureRegion topRegion;
    public float itemsPerSecond = 10f;
    public float powerUsage = 0f;
    public int blockHealth = 100;
    public float blockbuildTime = 60f;
    public boolean circu = true;

    public CircularBridge(String name) {{
        super(name);
        
        allowDiagonal = circu; // Разрешаем диагонали только если circu = true
        range = 8;
        bridgeWidth = 8;
        itemCapacity = 20;
        
        // Устанавливаем здоровье через родительское поле
        health = blockHealth;
        buildTime = blockbuildTime;
    }}

    @Override
    public void load() {{
        super.load();
        topRegion = Core.atlas.find(name + "-top");
    }}
    
    @Override
    public void init() {{
        transportTime = 60f / itemsPerSecond;
        
        // Настройка энергопотребления
        if (powerUsage > 0) {{
            hasPower = true;
            consumesPower = true;
            outputsPower = false;
            consumePower(powerUsage / 60f);
        }} else {{
            hasPower = false;
            consumesPower = false;
            outputsPower = false;
        }}
        
        super.init();
    }}

    @Override
    public boolean positionsValid(int x1, int y1, int x2, int y2) {{
        if (circu) {{
            // Круговой режим - проверяем расстояние по прямой
            return Mathf.dst(x1, y1, x2, y2) <= range;
        }} else {{
            // Крестовой режим - только кардинальные направления
            if (x1 == x2) {{
                return Math.abs(y1 - y2) <= range;
            }} else if (y1 == y2) {{
                return Math.abs(x1 - x2) <= range;
            }} else {{
                return false;
            }}
        }}
    }}

    @Override
    public void drawPlace(int x, int y, int rotation, boolean valid) {{
        if (circu) {{
            // Круговой режим - рисуем круг
            Drawf.dashCircle(x * tilesize, y * tilesize, range * tilesize, Pal.placing);
        }} else {{
            // Крестовой режим - рисуем линии по 4 направлениям
            for(int i = 0; i < 4; i++){{
                Drawf.dashLine(Pal.placing,
                x * tilesize + Geometry.d4[i].x * (tilesize / 2f + 2),
                y * tilesize + Geometry.d4[i].y * (tilesize / 2f + 2),
                x * tilesize + Geometry.d4[i].x * (range) * tilesize,
                y * tilesize + Geometry.d4[i].y * (range) * tilesize);
            }}
        }}

        Tile link = findLink(x, y);

        if (link != null && positionsValid(x, y, link.x, link.y)) {{
            Draw.color(Pal.placing);
            Lines.stroke(2f);
            
            float x1 = x * tilesize;
            float y1 = y * tilesize;
            float x2 = link.x * tilesize;
            float y2 = link.y * tilesize;
            
            Lines.line(x1, y1, x2, y2);
            
            Draw.rect("bridge-arrow", (x1 + x2) / 2f, (y1 + y2) / 2f, Angles.angle(x2, y2, x1, y1));
        }}
        Draw.reset();
    }}

    @Override
    public void changePlacementPath(Seq<Point2> points, int rotation) {{
        if (circu) {{
            // Круговой режим - используем евклидово расстояние
            Placement.calculateNodes(points, this, rotation, 
                (point, other) -> Mathf.dst(point.x, point.y, other.x, other.y) <= range);
        }} else {{
            // Крестовой режим - используем манхэттенское расстояние по кардиналям
            Placement.calculateNodes(points, this, rotation, 
                (point, other) -> Math.max(Math.abs(point.x - other.x), Math.abs(point.y - other.y)) <= range);
        }}
    }}

    @Override
    public void setStats() {{
        super.setStats();
        stats.add(Stat.range, range, StatUnit.blocks);
    }}

    @Override
    public void setBars() {{
        super.setBars();
        
        // Добавляем бар энергии только если нужно
        if (powerUsage > 0) {{
            addBar("power", (CircularBridgeBuild entity) -> 
                new Bar(
                    () -> Core.bundle.format("bar.power", (int)(entity.getPowerStatus() * 100f)),
                    () -> Pal.powerBar,
                    () -> entity.getPowerStatus()
                )
            );
        }}
    }}

    public class CircularBridgeBuild extends ItemBridgeBuild {{
        
        public float getPowerStatus() {{
            if (powerUsage == 0) return 1f;
            if (power == null) return 0f;
            return power.status;
        }}
        
        @Override
        public void drawConfigure() {{
            if (circu) {{
                Drawf.dashCircle(x, y, range * tilesize, Pal.placing);
            }} else {{
                for(int i = 1; i <= range; i++){{
                    for(int j = 0; j < 4; j++){{
                        Tile other = tile.nearby(Geometry.d4[j].x * i, Geometry.d4[j].y * i);
                        // Check if other tile exists and link is valid
                        if(other != null && linkValid(tile, other)){{
                            // Check if other.build exists before accessing pos()
                            boolean linked = other.build != null && other.pos() == link;
                            Drawf.select(other.drawx(), other.drawy(),
                                other.block().size * tilesize / 2f + 2f + (linked ? 0f : Mathf.absin(Time.time, 4f, 1f)), 
                                linked ? Pal.place : Pal.breakInvalid);
                        }}
                    }}
                }}
            }}
            super.drawConfigure();
            
            // Показываем статус энергии если нужно
            if (powerUsage > 0) {{
                drawPowerStatus();
            }}
        }}
                
        private void drawPowerStatus() {{
            float size = 2f;
            float percent = getPowerStatus();
            
            // Рисуем фон
            Draw.color(Pal.gray);
            Draw.rect("status-bar-middle", x, y + tilesize * 2f, size, 1f);
            
            // Рисуем заполнение
            Draw.color(percent > 0 ? Pal.powerBar : Pal.remove);
            Draw.rect("status-bar-middle", 
                x - (1f - percent) * size / 2f, 
                y + tilesize * 2f, 
                size * percent, 1f);
            
            Draw.reset();
        }}

        @Override
        public void draw() {{
            // Основной блок всегда рисуется полностью видимым
            Draw.rect(region, x, y);
            
            if (topRegion != null && topRegion.found()) {{
                Draw.z(Layer.blockOver);
                Draw.rect(topRegion, x, y);
            }}

            Draw.z(Layer.power);

            Building other = world.build(link);
            if (other == null || !linkValid(tile, other.tile)) {{
                Draw.reset();
                return;
            }}
            
            if (Mathf.zero(Renderer.bridgeOpacity)) return;

            float angle = Angles.angle(x, y, other.x, other.y);
            
            // Определяем коэффициент прозрачности для элементов моста
            float bridgeAlpha = Renderer.bridgeOpacity;
            if (powerUsage > 0 && getPowerStatus() <= 0.01f) {{
                bridgeAlpha = Renderer.bridgeOpacity * 0.3f; // 30% от обычной прозрачности моста
            }}
            
            // Применяем прозрачность только к элементам моста
            Draw.alpha(bridgeAlpha);
            
            Draw.rect(endRegion, x, y, angle + 90);
            Draw.rect(endRegion, other.x, other.y, angle - 90);

            Lines.stroke(bridgeWidth);
            
            Tmp.v1.set(x, y).sub(other.x, other.y).setLength(tilesize/2f).scl(-1f);
            
            Lines.line(bridgeRegion,
                x + Tmp.v1.x,
                y + Tmp.v1.y,
                other.x - Tmp.v1.x,
                other.y - Tmp.v1.y, false);

            drawArrows(other.tile, angle, bridgeAlpha);
            
            Draw.color();
            Draw.reset();
        }}
        
        private void drawArrows(Tile other, float angle, float bridgeAlpha) {{
            float dst = Mathf.dst(x, y, other.worldx(), other.worldy());
            int arrows = Math.max(1, (int)(dst / tilesize * 1.5f));
            
            float startX = x + Tmp.v1.x;
            float startY = y + Tmp.v1.y;
            float endX = other.worldx() - Tmp.v1.x;
            float endY = other.worldy() - Tmp.v1.y;
            
            // Стрелки тускнеют если мало энергии
            float powerFactor = getPowerStatus();
            
            for (int a = 0; a < arrows; a++) {{
                float progress = (float)(a + 0.5f) / arrows;
                float cx = Mathf.lerp(startX, endX, progress);
                float cy = Mathf.lerp(startY, endY, progress);
                
                Draw.alpha(Mathf.absin(a - time / arrowTimeScl, arrowPeriod, 1f) * warmup * bridgeAlpha * powerFactor);
                Draw.rect(arrowRegion, cx, cy, angle);
            }}
        }}

        @Override
        public void updateTransport(Building other) {{
            // Если нет потребления энергии, работаем всегда
            if (powerUsage == 0) {{
                super.updateTransport(other);
                return;
            }}
            
            // Проверяем наличие энергии
            if (getPowerStatus() <= 0.01f) {{
                return; // Недостаточно энергии
            }}
            
            transportCounter += delta();
            while(transportCounter >= transportTime) {{
                Item item = items.take();
                if (item != null && other.acceptItem(this, item)) {{
                    other.handleItem(this, item);
                    moved = true;
                }} else if (item != null) {{
                    items.add(item, 1);
                }}
                transportCounter -= transportTime;
            }}
        }}

        @Override
        public boolean onConfigureBuildTapped(Building other) {{
            if (other == null) return true;
            
            if (other instanceof CircularBridgeBuild) {{
                CircularBridgeBuild b = (CircularBridgeBuild) other;
                if (b.link == pos()) {{
                    configure(other.pos());
                    other.configure(-1);
                    return false;
                }}
            }}

            if (other.tile != null && linkValid(tile, other.tile)) {{
                if (link == other.pos()) {{
                    configure(-1);
                    other.configure(-1);
                }} else {{
                    configure(other.pos());
                }}
                return false;
            }}
            return true;
        }}
        
        @Override
        public boolean acceptItem(Building source, Item item) {{
            // Если нет потребления энергии, всегда принимаем
            if (powerUsage == 0) {{
                return super.acceptItem(source, item);
            }}
            
            // Проверяем наличие энергии
            if (getPowerStatus() <= 0.01f) {{
                return false; // Недостаточно энергии
            }}
            return super.acceptItem(source, item);
        }}
    }}
}}"""
        
        # Создаем файл
        created_files = self.create_files(
            content=content,
            name="CircularBridge",
            file_type="java",
            path=str(self.get_absolute_path(f"src/{self.mod_name.lower()}/custom_types/blocks/bridge"))
        )
        
        print(f"✅ CircularBridge.java успешно создан: {created_files[0]}")
        
        return created_files

        #CircularBridge

#----------ФУНКЦИИ СОЗДАНИЯ----------
    PATEH_FOLDER = [
        "consume_generators", "walls", "solar_panels",
        "batterys", "beam_nodes", "power_nodes", "shield_walls",
        "generic_crafter", "bridges", "conveyors"
    ]

    #CUSTOM TYPE LOAD
    def create_files(self, content, name, file_type, path):
        """
        Создает один или несколько файлов
        
        Параметры:
        content - содержимое файла (строка или список строк для нескольких файлов)
        name - имя файла (строка или список имен для нескольких файлов)
        file_type - тип файла (строка, например 'txt', 'json', 'csv' или список типов)
        path - путь для сохранения (строка или список путей для нескольких файлов)
        
        Возвращает:
        list: список путей к созданным файлам
        """

        # Преобразуем пути в абсолютные, если это необходимо
        if path and not isinstance(path, list):
            if not os.path.isabs(path) and self.mod_folder:
                # Если путь относительный и есть mod_folder, делаем абсолютным
                path = str(Path(self.mod_folder).parent.parent / path)
        elif path and isinstance(path, list):
            for i, p in enumerate(path):
                if p and not os.path.isabs(p) and self.mod_folder:
                    path[i] = str(Path(self.mod_folder).parent.parent / p)
        
        # Преобразуем одиночные значения в списки для единообразия
        if not isinstance(content, list):
            content = [content]
        if not isinstance(name, list):
            name = [name]
        if not isinstance(file_type, list):
            file_type = [file_type]
        if not isinstance(path, list):
            path = [path]
        
        # Определяем максимальную длину для итерации
        max_len = max(len(content), len(name), len(file_type), len(path))
        
        # Создаем файлы
        created_files = []
        
        for i in range(max_len):
            # Получаем текущие значения (если список короче - используем последний элемент)
            current_content = content[i] if i < len(content) else content[-1]
            current_name = name[i] if i < len(name) else name[-1]
            current_type = file_type[i] if i < len(file_type) else file_type[-1]
            current_path = path[i] if i < len(path) else path[-1]
            
            # Обработка строки содержимого
            if isinstance(current_content, str):
                import re
                
                # Функция для обработки {self.что-то}
                def replace_self(match):
                    expr = match.group(1)
                    try:
                        if expr.startswith('self.'):
                            attr_name = expr[5:]
                            if hasattr(self, attr_name):
                                value = getattr(self, attr_name)
                                return str(value)
                            else:
                                print(f"⚠️ Атрибут {attr_name} не найден, оставляем как есть")
                                return f"{{{expr}}}"
                        else:
                            return f"{{{expr}}}"
                    except Exception as e:
                        print(f"⚠️ Ошибка при обработке {expr}: {e}")
                        return f"{{{expr}}}"
                
                # Обрабатываем все {self.что-то} (включая .ADD-TO)
                # Сначала обрабатываем специальный синтаксис {self.что-то.ADD-TO}
                # Затем обрабатываем обычные {self.что-то}
                
                # 1. Обрабатываем {self.что-то.ADD-TO}
                # Ищем паттерн {self.что-то.ADD-TO}
                pattern_addto = r'\{self\.[^}]+\}'
                current_content = re.sub(pattern_addto, replace_self, current_content)
                
                # 2. Обрабатываем все остальные {self.что-то}
                # Ищем все {self.что-то} которые не были обработаны
                pattern_self = r'\{self\.[^}]+\}'
                current_content = re.sub(pattern_self, replace_self, current_content)
                
                # 3. Для Java файлов также обрабатываем одиночные фигурные скобки (экранирование)
                if current_type in ['java', 'py']:
                    # Для Java файлов нужно экранировать одиночные фигурные скобки
                    # Но оставляем {self.что-то} уже обработанными
                    # Этот шаг не нужен, так как мы уже обработали все плейсхолдеры
                    pass
            
            # Формируем полное имя файла
            if current_type:
                filename = f"{current_name}.{current_type}"
            else:
                filename = current_name
            
            # Создаем директорию, если её нет
            try:
                os.makedirs(current_path, exist_ok=True)
                print(f"📁 Директория создана/существует: {current_path}")
            except Exception as e:
                print(f"❌ Ошибка создания директории {current_path}: {e}")
                continue
            
            # Полный путь к файлу
            full_path = os.path.join(current_path, filename)
            
            # Проверяем, существует ли файл
            if os.path.exists(full_path):
                #print(f"⚠️ Файл уже существует: {full_path}")
                # Пропускаем создание, если файл существует
                # Но можно добавить опцию перезаписи
                continue
            
            try:
                # Создаем файл и записываем содержимое
                with open(full_path, 'w', encoding='utf-8') as file:
                    file.write(str(current_content))
                created_files.append(full_path)
                print(f"✅ Файл создан: {full_path}")
            except Exception as e:
                print(f"❌ Ошибка при создании файла {full_path}: {e}")
        
        return created_files

    #BLOCKS
    def create_wall(self):
        """Создает или добавляет новую стену в walls/Walls.java"""

        PATEH_FOLDER = self.PATEH_FOLDER

        CATENAME = "Wall"
        CATEDOR = "defense"
        TEMPO_ICON = "copper-wall.png"
        BL_NAME_2 = "Стена"
        BL_CR_NAME = "Стену"
        BL_NAME = "стены"
        ENTRY_NAME1 = "wall"
        NAME = "Walls"
        FOLDER = "walls"

        # Пути к файлам
        mod_name_lower = self.mod_name.lower() if self.mod_name else self.mod_name
        block_registration_path = Path(self.mod_folder) / "src" / mod_name_lower / "init" / "blocks" / f"{FOLDER}" / f"{NAME}.java"
        
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
            text=f"Название {BL_NAME} (английское, можно пробел, первая буква маленькая):",
            font=("Arial", 16),
            text_color="#BDBDBD"
        ).pack(anchor="w", pady=(0, 5))
        
        entry_name = ctk.CTkEntry(
            name_frame,
            width=400,
            height=40,
            placeholder_text=f"{ENTRY_NAME1} name",
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
            text=f"Свойства {BL_NAME}",
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
            text="Прочность (health):",
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
            text="Скорость стройки (buildTime):",
            font=("Arial", 15),
            text_color="#BDBDBD"
        ).pack(anchor="w", pady=(0, 5))
        
        entry_speed = ctk.CTkEntry(
            speed_frame,
            width=180,
            height=38,
            placeholder_text="1",
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
            text="Размер (size):",
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

        # === Always Unlocked с индикатором ===
        
        always_unlocked_var = ctk.BooleanVar(value=False)
        always_unlocked_status = ctk.CTkLabel(properties_card, text="", font=("Arial", 12))

        # === КАРТОЧКА ДЛЯ ПРЕДМЕТОВ СТРОИТЕЛЬСТВА ===
        build_card = ctk.CTkFrame(
            scroll_frame,
            corner_radius=15,
            border_width=2,
            border_color="#404040",
            fg_color="#363636"
        )
        build_card.pack(fill="x", pady=(0, 20))
        
        ctk.CTkLabel(
            build_card,
            text="🔨 Предметы для строительства",
            font=("Arial", 18, "bold"),
            text_color="#4CAF50"
        ).pack(pady=(15, 10), padx=20, anchor="w")
        
        build_items_frame = ctk.CTkFrame(build_card, fg_color="transparent")
        build_items_frame.pack(fill="x", padx=20, pady=(0, 15))
        
        build_items_var = tk.StringVar(value="Выбрано: 0 предметов")
        build_items_label = ctk.CTkLabel(
            build_items_frame,
            textvariable=build_items_var,
            font=("Arial", 12),
            text_color="#9E9E9E",
            wraplength=400
        )
        build_items_label.pack(anchor="w", pady=(5, 0))
        
        ctk.CTkButton(
            build_items_frame,
            text="📋 Выбрать предметы для строительства",
            command=lambda: self.open_items_editor(build_items_var, "build"),
            height=35,
            font=("Arial", 13),
            fg_color="#2E7D32",
            hover_color="#1B5E20",
            corner_radius=6
        ).pack(anchor="w", pady=(0, 5))

        # === КАРТОЧКА ДЛЯ ИССЛЕДОВАНИЯ ===
        research_card = ctk.CTkFrame(
            scroll_frame,
            corner_radius=15,
            border_width=2,
            border_color="#404040",
            fg_color="#363636"
        )
        
        # Переменные для исследования
        selected_block_var = tk.StringVar(value="Не выбран")
        selected_block_internal_var = tk.StringVar(value="")
        selected_block_type_var = tk.StringVar(value="")
        block_icon_label = ctk.CTkLabel(properties_card, text="🧱", font=("Arial", 30))  # Временный label, будет заменен
        block_path_label = ctk.CTkLabel(properties_card, text="", font=("Arial", 10))  # Временный label, будет заменен
        research_items_var = tk.StringVar(value="Выбрано: 0 предметов")

        # ИСПОЛЬЗУЕМ НОВУЮ УНИВЕРСАЛЬНУЮ ФУНКЦИЮ
        always_unlocked_check, select_block_button, select_items_button = self.setup_research_system(
            always_unlocked_var=always_unlocked_var,
            research_card=research_card,
            always_unlocked_status=always_unlocked_status,
            build_card=build_card,
            selected_block_var=selected_block_var,
            selected_block_internal_var=selected_block_internal_var,
            selected_block_type_var=selected_block_type_var,
            block_icon_label=block_icon_label,
            block_path_label=block_path_label,
            research_items_var=research_items_var,
            on_block_selected_callback=None
        )

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

        # === Основная функция создания стены ===
        def process_wall():
            original_name = entry_name.get().strip()
            
            if not original_name:
                status_label.configure(
                    text="❌ Ошибка: Введите название стены!", 
                    text_color="#F44336"
                )
                return
            
            # Проверка для always_unlocked = false
            is_valid, error_msg = self.validate_research(
                always_unlocked_var=always_unlocked_var,
                research_items=self.research_items if hasattr(self, 'research_items') else [],
                selected_block_internal_var=selected_block_internal_var
            )
            
            if not is_valid:
                status_label.configure(text=error_msg, text_color="#F44336")
                return
            
            if not hasattr(self, 'build_items') or not self.build_items:
                status_label.configure(
                    text="❌ Ошибка: Выберите предметы для строительства!", 
                    text_color="#F44336"
                )
                return
            
            # Форматируем имя
            constructor_name = self.format_to_lower_camel(original_name)
            if not constructor_name:
                status_label.configure(
                    text="❌ Ошибка: Некорректное название!", 
                    text_color="#F44336"
                )
                return

            # Проверяем, существует ли уже такое имя
            if self.check_block_name_exists(original_name, PATEH_FOLDER):
                status_label.configure(
                    text=f"❌ Ошибка: Имя '{constructor_name}' уже используется!", 
                    text_color="#F44336"
                )
                return
            
            # Копируем текстуру
            size_multiplier = int(size_var.get())
            texture_copied = self.copy_block_texture(
                block_name=original_name,
                size_multiplier=size_multiplier,
                target_folder=FOLDER,
                template_names=[TEMPO_ICON]
            )
            texture_status = "✅ Текстура создана" if texture_copied else "⚠️ Текстура не создана"
            
            # Получаем значения свойств
            hp_value = entry_hp.get().strip() or "400"
            speed_raw = entry_speed.get().strip() or "1"
            size_value = size_var.get()
            
            hp_value = str(int(float(hp_value)))
            always_unlocked_value = "true" if always_unlocked_var.get() else "false"
            
            # Получаем кастомные предметы
            custom_items = self.get_custom_items()
            var_name = constructor_name
            
            # Формируем код для предметов строительства
            build_itemstack_code = ""
            build_items_list = []
            if hasattr(self, 'build_items') and self.build_items:
                item_counts = {}
                for item in self.build_items:
                    item_counts[item] = item_counts.get(item, 0) + 1
                
                item_parts = []
                for item_name, count in item_counts.items():
                    code_name = self.get_item_code_name(item_name, custom_items)
                    item_parts.append(f"{code_name}, {count}")
                    build_items_list.append((item_name, count))
                
                build_itemstack_code = f"\n            requirements(Category.{CATEDOR},\n                ItemStack.with({', '.join(item_parts)}));"
            
            # Формируем свойства блока
            properties = f"""    health = {hp_value};
                size = {size_value};
                buildTime = {speed_raw};
                alwaysUnlocked = {always_unlocked_value};
                buildVisibility = BuildVisibility.shown;
                category = Category.{CATEDOR};{build_itemstack_code}

                localizedName = Core.bundle.get("{var_name}.name", "OH NO");
                description = Core.bundle.get("{var_name}.description", "OH NO");"""
            
            # Пути к файлам
            mod_name_lower = self.mod_name.lower() if self.mod_name else self.mod_name
            block_registration_path = self.get_absolute_path(f"src/{mod_name_lower}/init/blocks/{FOLDER}/{NAME}.java")
            main_mod_path = Path(self.mod_folder) / "src" / mod_name_lower / f"{self.mod_name}JavaMod.java"
            
            block_registration_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Читаем или создаем файл регистрации блоков
            try:
                with open(block_registration_path, 'r', encoding='utf-8') as file:
                    content = file.read()
            except FileNotFoundError:
                content = f"""package {mod_name_lower}.init.blocks.{FOLDER};

import arc.graphics.Color;
import arc.Core;
import mindustry.type.ItemStack;
import mindustry.type.Category;
import mindustry.world.Block;
import mindustry.world.blocks.{CATEDOR}.{CATENAME};
import mindustry.world.meta.BuildVisibility;
import mindustry.content.Items;
import mindustry.Vars;
import {mod_name_lower}.init.items.ModItems;

public class {NAME} {{
    public static {CATENAME};
                                            
    public static void Load() {{
        // Регистрация блоков
    }}
}}"""
            
            wall_exists = var_name in content
            tree_file_created = False
            main_file_updated = False
            
            if not wall_exists:
                # Добавляем переменную блока
                if f"public static {CATENAME};" in content:
                    content = content.replace(
                        f"public static {CATENAME};",
                        f"public static {CATENAME} {var_name};"
                    )
                elif f"public static {CATENAME} " in content:
                    lines = content.split('\n')
                    for i, line in enumerate(lines):
                        if f"public static {CATENAME} " in line and var_name not in line:
                            lines[i] = line.rstrip(';') + f", {var_name};"
                            content = '\n'.join(lines)
                            break
                
                # Добавляем инициализацию блока
                load_start = content.find("public static void Load() {")
                if load_start != -1:
                    open_brace = content.find('{', load_start)
                    if open_brace != -1:
                        insert_pos = open_brace + 1
                        indent = "        "
                        wall_code = f'\n{indent}{var_name} = new {CATENAME}("{constructor_name}"){{{{\n{indent}{properties}\n{indent}}}}};'
                        content = content[:insert_pos] + wall_code + content[insert_pos:]
                
                # Сохраняем файл
                with open(block_registration_path, 'w', encoding='utf-8') as file:
                    file.write(content)
                
                # Обновляем главный файл мода
                try:
                    with open(main_mod_path, 'r', encoding='utf-8') as file:
                        main_content = file.read()
                    
                    # Добавляем импорт
                    import_statement = f"import {mod_name_lower}.init.blocks.{FOLDER}.{NAME};"
                    if import_statement not in main_content:
                        import_add_pos = main_content.find("//import_add")
                        if import_add_pos != -1:
                            insert_pos = import_add_pos + len("//import_add")
                            if insert_pos < len(main_content) and main_content[insert_pos] == '\n':
                                main_content = main_content[:insert_pos] + f"\n{import_statement}" + main_content[insert_pos:]
                            else:
                                main_content = main_content[:insert_pos] + f"\n{import_statement}" + main_content[insert_pos:]
                    
                    # Добавляем вызов Load
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
                    
                    main_file_updated = True
                    
                    # Создаем файл дерева технологий, если Always Unlocked = false
                    if not always_unlocked_var.get():
                        research_items_list = []
                        if hasattr(self, 'research_items') and self.research_items:
                            item_counts = {}
                            for item in self.research_items:
                                item_counts[item] = item_counts.get(item, 0) + 1
                            
                            for item_name, count in item_counts.items():
                                research_items_list.append((item_name, count))
                        
                        research_block = selected_block_internal_var.get()
                        
                        # Используем универсальную функцию
                        tree_file_created = self.create_tech_tree_file_universal(
                            block_var_name=var_name,
                            block_constructor_name=constructor_name,
                            research_block=research_block,
                            research_items=research_items_list,
                            block_type="wall",
                            folder_name=FOLDER,
                            class_name="WallsTree"  # Можно указать явно
                        )
                        
                        # ИСПОЛЬЗУЕМ НОВУЮ УНИВЕРСАЛЬНУЮ ФУНКЦИЮ для обновления главного файла
                        if tree_file_created:
                            self.update_main_mod_file_universal(
                                import_path=f"{mod_name_lower}.content.WallsTree",
                                load_statement="WallsTree.Load();"
                            )
                    
                    # Формируем сообщение о результате
                    status_messages = [
                        f"✅ {BL_NAME_2} '{var_name}' успешно создана!",
                        f'📝 Имя в игре: "{constructor_name}"',
                        f"{texture_status}",
                    ]
                    
                    # Добавляем информацию о Always Unlocked
                    if always_unlocked_var.get():
                        status_messages.append("🔓 Always Unlocked: ДА (доступен с самого начала)")
                    else:
                        status_messages.append("🔒 Always Unlocked: НЕТ (требуется исследование)")
                    
                    status_messages.extend([
                        f"📊 Свойства {BL_NAME}:",
                        f"  • ❤️ Здоровье: {hp_value}",
                        f"  • ⚡ Скорость стройки: {speed_raw}",
                        f"  • 📏 Размер: {size_value}",
                    ])
                    
                    if build_items_list:
                        items_list = []
                        for item_name, count in build_items_list:
                            if item_name in custom_items:
                                items_list.append(f"ModItems.{item_name} ×{count}")
                            else:
                                display_name = item_name.replace('-', ' ').title()
                                items_list.append(f"{display_name} ×{count}")
                        
                        status_messages.append(f"  • 🔨 Стройка: {', '.join(items_list)}")
                    
                    if not always_unlocked_var.get():
                        if hasattr(self, 'research_items') and self.research_items:
                            research_list = []
                            item_counts = {}
                            for item in self.research_items:
                                item_counts[item] = item_counts.get(item, 0) + 1
                            
                            for item_name, count in item_counts.items():
                                if item_name in custom_items:
                                    research_list.append(f"ModItems.{item_name} ×{count}")
                                else:
                                    display_name = item_name.replace('-', ' ').title()
                                    research_list.append(f"{display_name} ×{count}")
                            
                            status_messages.append(f"  • 💰 Исследование: {', '.join(research_list)}")
                        
                        status_messages.append(f"  • 🎯 Блок исследования: {selected_block_var.get()}")
                        
                        if tree_file_created:
                            status_messages.append(f"  • 🌳 WallsTree.java создан и добавлен в main (WallsTree.Load())")
                        else:
                            status_messages.append(f"  • ⚠️ WallsTree.java не создан")
                    
                    if main_file_updated:
                        status_messages.append(f"  • 📄 Главный файл мода обновлен")
                    
                    status_text = "\n".join(status_messages)
                    status_label.configure(text=status_text, text_color="#4CAF50")
                    
                except Exception as e:
                    status_label.configure(text=f"❌ Ошибка: {str(e)}", text_color="#F44336")
            else:
                status_label.configure(text=f"⚠️ {BL_NAME_2} '{var_name}' уже существует", text_color="#FF9800")
            
            self.root.after(5000, lambda: status_label.configure(text=""))

        # === Кнопки действий ===
        buttons_frame = ctk.CTkFrame(button_frame, fg_color="transparent")
        buttons_frame.pack(pady=10)
        
        ctk.CTkButton(
            buttons_frame,
            text=f"Создать {BL_CR_NAME}",
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
        
        # Инициализация переменных
        self.build_items = []
        self.research_items = []

    def create_battery(self):
        """Создает или добавляет новую батарею в battery/Batterys.java"""

        PATEH_FOLDER = self.PATEH_FOLDER

        CATENAME = "Battery"
        CATEDOR = "power"
        TEMPO_ICON = "battery.png"
        TEMPO_ICON_TOP = "battery-top.png"
        BL_NAME_2 = "Батарея"
        BL_CR_NAME = "Батарею"
        BL_NAME = "батареи"
        ENTRY_NAME1 = "battery"
        NAME = "Batterys"
        FOLDER = "batterys"
        
        # Очищаем окно
        self.clear_window()
        
        # Основной фрейм с прокруткой
        main_frame = ctk.CTkFrame(self.root, fg_color="#2b2b2b")
        main_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
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
            text="Создание батареи",
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
            text=f"Название {BL_NAME} (английское, можно пробел, первая буква маленькая):",
            font=("Arial", 16),
            text_color="#BDBDBD"
        ).pack(anchor="w", pady=(0, 5))
        
        entry_name = ctk.CTkEntry(
            name_frame,
            width=400,
            height=40,
            placeholder_text=f"{ENTRY_NAME1} name",
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
            text=f"Свойства {BL_NAME}",
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
            text="Прочность (health):",
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
            text="Скорость стройки (buildTime):",
            font=("Arial", 15),
            text_color="#BDBDBD"
        ).pack(anchor="w", pady=(0, 5))
        
        entry_speed = ctk.CTkEntry(
            speed_frame,
            width=180,
            height=38,
            placeholder_text="1",
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
            text="Размер (size):",
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

        # Энергия (специфично для батареи)
        buff_frame = ctk.CTkFrame(properties_grid, fg_color="transparent")
        buff_frame.grid(row=1, column=1, padx=10, pady=5, sticky="ew")
        
        ctk.CTkLabel(
            buff_frame,
            text="Ёмкость (powerBuffered):",
            font=("Arial", 15),
            text_color="#BDBDBD"
        ).pack(anchor="w", pady=(0, 5))
        
        entry_buff = ctk.CTkEntry(
            buff_frame,
            width=180,
            height=38,
            placeholder_text="1000",
            font=("Arial", 14),
            validate="key",
            validatecommand=vcmd_int,
            fg_color="#424242",
            border_color="#555555",
            text_color="#FFFFFF",
            placeholder_text_color="#888888"
        )
        entry_buff.pack(fill="x")

        # === Always Unlocked с индикатором ===
        
        always_unlocked_var = ctk.BooleanVar(value=False)
        always_unlocked_status = ctk.CTkLabel(properties_card, text="", font=("Arial", 12))

        # === КАРТОЧКА ДЛЯ ПРЕДМЕТОВ СТРОИТЕЛЬСТВА ===
        build_card = ctk.CTkFrame(
            scroll_frame,
            corner_radius=15,
            border_width=2,
            border_color="#404040",
            fg_color="#363636"
        )
        build_card.pack(fill="x", pady=(0, 20))
        
        ctk.CTkLabel(
            build_card,
            text="🔨 Предметы для строительства",
            font=("Arial", 18, "bold"),
            text_color="#4CAF50"
        ).pack(pady=(15, 10), padx=20, anchor="w")
        
        build_items_frame = ctk.CTkFrame(build_card, fg_color="transparent")
        build_items_frame.pack(fill="x", padx=20, pady=(0, 15))
        
        build_items_var = tk.StringVar(value="Выбрано: 0 предметов")
        build_items_label = ctk.CTkLabel(
            build_items_frame,
            textvariable=build_items_var,
            font=("Arial", 12),
            text_color="#9E9E9E",
            wraplength=400
        )
        build_items_label.pack(anchor="w", pady=(5, 0))
        
        ctk.CTkButton(
            build_items_frame,
            text="📋 Выбрать предметы для строительства",
            command=lambda: self.open_items_editor(build_items_var, "build"),
            height=35,
            font=("Arial", 13),
            fg_color="#2E7D32",
            hover_color="#1B5E20",
            corner_radius=6
        ).pack(anchor="w", pady=(0, 5))

        # === КАРТОЧКА ДЛЯ ИССЛЕДОВАНИЯ ===
        research_card = ctk.CTkFrame(
            scroll_frame,
            corner_radius=15,
            border_width=2,
            border_color="#404040",
            fg_color="#363636"
        )
        
        # Переменные для исследования
        selected_block_var = tk.StringVar(value="Не выбран")
        selected_block_internal_var = tk.StringVar(value="")
        selected_block_type_var = tk.StringVar(value="")
        block_icon_label = ctk.CTkLabel(properties_card, text="🔋", font=("Arial", 30))
        block_path_label = ctk.CTkLabel(properties_card, text="", font=("Arial", 10))
        research_items_var = tk.StringVar(value="Выбрано: 0 предметов")

        # ИСПОЛЬЗУЕМ НОВУЮ УНИВЕРСАЛЬНУЮ ФУНКЦИЮ
        always_unlocked_check, select_block_button, select_items_button = self.setup_research_system(
            always_unlocked_var=always_unlocked_var,
            research_card=research_card,
            always_unlocked_status=always_unlocked_status,
            build_card=build_card,
            selected_block_var=selected_block_var,
            selected_block_internal_var=selected_block_internal_var,
            selected_block_type_var=selected_block_type_var,
            block_icon_label=block_icon_label,
            block_path_label=block_path_label,
            research_items_var=research_items_var,
            on_block_selected_callback=None
        )

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

        # === Основная функция создания батареи ===
        def process_battery():
            original_name = entry_name.get().strip()
            
            if not original_name:
                status_label.configure(
                    text="❌ Ошибка: Введите название батареи!", 
                    text_color="#F44336"
                )
                return
            
            # Проверка для always_unlocked = false
            is_valid, error_msg = self.validate_research(
                always_unlocked_var=always_unlocked_var,
                research_items=self.research_items if hasattr(self, 'research_items') else [],
                selected_block_internal_var=selected_block_internal_var
            )
            
            if not is_valid:
                status_label.configure(text=error_msg, text_color="#F44336")
                return
            
            if not hasattr(self, 'build_items') or not self.build_items:
                status_label.configure(
                    text="❌ Ошибка: Выберите предметы для строительства!", 
                    text_color="#F44336"
                )
                return
            
            # Форматируем имя
            constructor_name = self.format_to_lower_camel(original_name)
            if not constructor_name:
                status_label.configure(
                    text="❌ Ошибка: Некорректное название!", 
                    text_color="#F44336"
                )
                return

            # Проверяем, существует ли уже такое имя
            if self.check_block_name_exists(original_name, PATEH_FOLDER):
                status_label.configure(
                    text=f"❌ Ошибка: Имя '{constructor_name}' уже используется!", 
                    text_color="#F44336"
                )
                return
            
            # Копируем текстуры (для батареи их две)
            size_multiplier = int(size_var.get())
            texture_configs = [
                {"template": TEMPO_ICON, "suffix": ""},
                {"template": TEMPO_ICON_TOP, "suffix": "-top"},
            ]
            
            texture_copied = self.copy_block_textures_multi(
                block_name=original_name,
                size_multiplier=size_multiplier,
                target_folder=FOLDER,
                texture_configs=texture_configs
            )
            texture_status = "✅ Текстуры созданы" if texture_copied else "⚠️ Текстуры не созданы"
            
            # Получаем значения свойств
            hp_value = entry_hp.get().strip() or "400"
            speed_raw = entry_speed.get().strip() or "1"
            buff_raw = entry_buff.get().strip() or "1000"
            size_value = size_var.get()
            
            hp_value = str(int(float(hp_value)))
            always_unlocked_value = "true" if always_unlocked_var.get() else "false"
            
            # Получаем кастомные предметы
            custom_items = self.get_custom_items()
            var_name = constructor_name
            
            # Формируем код для предметов строительства
            build_itemstack_code = ""
            build_items_list = []
            if hasattr(self, 'build_items') and self.build_items:
                item_counts = {}
                for item in self.build_items:
                    item_counts[item] = item_counts.get(item, 0) + 1
                
                item_parts = []
                for item_name, count in item_counts.items():
                    code_name = self.get_item_code_name(item_name, custom_items)
                    item_parts.append(f"{code_name}, {count}")
                    build_items_list.append((item_name, count))
                
                build_itemstack_code = f"\n            requirements(Category.{CATEDOR},\n                ItemStack.with({', '.join(item_parts)}));"
            
            # Формируем свойства батареи
            properties = f"""    health = {hp_value};
                size = {size_value};
                buildTime = {speed_raw};
                alwaysUnlocked = {always_unlocked_value};
                buildVisibility = BuildVisibility.shown;
                category = Category.{CATEDOR};{build_itemstack_code}
                consumePowerBuffered({buff_raw}f);

                localizedName = Core.bundle.get("{var_name}.name", "OH NO");
                description = Core.bundle.get("{var_name}.description", "OH NO");"""
            
            # Пути к файлам
            mod_name_lower = self.mod_name.lower() if self.mod_name else self.mod_name
            block_registration_path = self.get_absolute_path(f"src/{mod_name_lower}/init/blocks/{FOLDER}/{NAME}.java")
            main_mod_path = Path(self.mod_folder) / "src" / mod_name_lower / f"{self.mod_name}JavaMod.java"
            
            block_registration_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Читаем или создаем файл регистрации блоков
            try:
                with open(block_registration_path, 'r', encoding='utf-8') as file:
                    content = file.read()
            except FileNotFoundError:
                content = f"""package {mod_name_lower}.init.blocks.{FOLDER};

import arc.graphics.Color;
import arc.Core;
import mindustry.type.ItemStack;
import mindustry.type.Category;
import mindustry.world.Block;
import mindustry.world.blocks.power.{CATENAME};
import mindustry.world.meta.BuildVisibility;
import mindustry.content.Items;
import mindustry.Vars;
import {mod_name_lower}.init.items.ModItems;

public class {NAME} {{
    public static {CATENAME};
                                            
    public static void Load() {{
        // Регистрация блоков
    }}
}}"""
            
            battery_exists = var_name in content
            tree_file_created = False
            main_file_updated = False
            
            if not battery_exists:
                # Добавляем переменную блока
                if f"public static {CATENAME};" in content:
                    content = content.replace(
                        f"public static {CATENAME};",
                        f"public static {CATENAME} {var_name};"
                    )
                elif f"public static {CATENAME} " in content:
                    lines = content.split('\n')
                    for i, line in enumerate(lines):
                        if f"public static {CATENAME} " in line and var_name not in line:
                            lines[i] = line.rstrip(';') + f", {var_name};"
                            content = '\n'.join(lines)
                            break
                
                # Добавляем инициализацию блока
                load_start = content.find("public static void Load() {")
                if load_start != -1:
                    open_brace = content.find('{', load_start)
                    if open_brace != -1:
                        insert_pos = open_brace + 1
                        indent = "        "
                        battery_code = f'\n{indent}{var_name} = new {CATENAME}("{constructor_name}"){{{{\n{indent}{properties}\n{indent}}}}};'
                        content = content[:insert_pos] + battery_code + content[insert_pos:]
                
                # Сохраняем файл
                with open(block_registration_path, 'w', encoding='utf-8') as file:
                    file.write(content)
                
                # Обновляем главный файл мода
                try:
                    with open(main_mod_path, 'r', encoding='utf-8') as file:
                        main_content = file.read()
                    
                    # Добавляем импорт
                    import_statement = f"import {mod_name_lower}.init.blocks.{FOLDER}.{NAME};"
                    if import_statement not in main_content:
                        import_add_pos = main_content.find("//import_add")
                        if import_add_pos != -1:
                            insert_pos = import_add_pos + len("//import_add")
                            if insert_pos < len(main_content) and main_content[insert_pos] == '\n':
                                main_content = main_content[:insert_pos] + f"\n{import_statement}" + main_content[insert_pos:]
                            else:
                                main_content = main_content[:insert_pos] + f"\n{import_statement}" + main_content[insert_pos:]
                    
                    # Добавляем вызов Load
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
                    
                    main_file_updated = True
                    
                    # Создаем файл дерева технологий, если Always Unlocked = false
                    if not always_unlocked_var.get():
                        research_items_list = []
                        if hasattr(self, 'research_items') and self.research_items:
                            item_counts = {}
                            for item in self.research_items:
                                item_counts[item] = item_counts.get(item, 0) + 1
                            
                            for item_name, count in item_counts.items():
                                research_items_list.append((item_name, count))
                        
                        research_block = selected_block_internal_var.get()
                        
                        # Используем универсальную функцию
                        tree_file_created = self.create_tech_tree_file_universal(
                            block_var_name=var_name,
                            block_constructor_name=constructor_name,
                            research_block=research_block,
                            research_items=research_items_list,
                            block_type="battery",
                            folder_name=FOLDER,
                            class_name="BatteryTree"
                        )
                        
                        # ИСПОЛЬЗУЕМ НОВУЮ УНИВЕРСАЛЬНУЮ ФУНКЦИЮ для обновления главного файла
                        if tree_file_created:
                            self.update_main_mod_file_universal(
                                import_path=f"{mod_name_lower}.content.BatteryTree",
                                load_statement="BatteryTree.Load();"
                            )
                    
                    # Формируем сообщение о результате
                    status_messages = [
                        f"✅ {BL_NAME_2} '{var_name}' успешно создана!",
                        f'📝 Имя в игре: "{constructor_name}"',
                        f"{texture_status}",
                    ]
                    
                    # Добавляем информацию о Always Unlocked
                    if always_unlocked_var.get():
                        status_messages.append("🔓 Always Unlocked: ДА (доступен с самого начала)")
                    else:
                        status_messages.append("🔒 Always Unlocked: НЕТ (требуется исследование)")
                    
                    status_messages.extend([
                        f"📊 Свойства {BL_NAME}:",
                        f"  • ❤️ Здоровье: {hp_value}",
                        f"  • ⚡ Скорость стройки: {speed_raw}",
                        f"  • 📏 Размер: {size_value}",
                        f"  • 🔋 Ёмкость: {buff_raw}",
                    ])
                    
                    if build_items_list:
                        items_list = []
                        for item_name, count in build_items_list:
                            if item_name in custom_items:
                                items_list.append(f"ModItems.{item_name} ×{count}")
                            else:
                                display_name = item_name.replace('-', ' ').title()
                                items_list.append(f"{display_name} ×{count}")
                        
                        status_messages.append(f"  • 🔨 Стройка: {', '.join(items_list)}")
                    
                    if not always_unlocked_var.get():
                        if hasattr(self, 'research_items') and self.research_items:
                            research_list = []
                            item_counts = {}
                            for item in self.research_items:
                                item_counts[item] = item_counts.get(item, 0) + 1
                            
                            for item_name, count in item_counts.items():
                                if item_name in custom_items:
                                    research_list.append(f"ModItems.{item_name} ×{count}")
                                else:
                                    display_name = item_name.replace('-', ' ').title()
                                    research_list.append(f"{display_name} ×{count}")
                            
                            status_messages.append(f"  • 💰 Исследование: {', '.join(research_list)}")
                        
                        status_messages.append(f"  • 🎯 Блок исследования: {selected_block_var.get()}")
                        
                        if tree_file_created:
                            status_messages.append(f"  • 🌳 BatteryTree.java создан и добавлен в main (BatteryTree.Load())")
                        else:
                            status_messages.append(f"  • ⚠️ BatteryTree.java не создан")
                    
                    if main_file_updated:
                        status_messages.append(f"  • 📄 Главный файл мода обновлен")
                    
                    status_text = "\n".join(status_messages)
                    status_label.configure(text=status_text, text_color="#4CAF50")
                    
                except Exception as e:
                    status_label.configure(text=f"❌ Ошибка: {str(e)}", text_color="#F44336")
            else:
                status_label.configure(text=f"⚠️ {BL_NAME_2} '{var_name}' уже существует", text_color="#FF9800")
            
            self.root.after(5000, lambda: status_label.configure(text=""))

        # === Кнопки действий ===
        buttons_frame = ctk.CTkFrame(button_frame, fg_color="transparent")
        buttons_frame.pack(pady=10)
        
        ctk.CTkButton(
            buttons_frame,
            text=f"Создать {BL_CR_NAME}",
            command=process_battery,
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
        
        # Инициализация переменных
        self.build_items = []
        self.research_items = []

    def create_solar_panel(self):
        """Создает или добавляет новую солнечную панель в solar_panels/SolarPanels.java"""
        
        # Константы для солнечной панели
        PATEH_FOLDER = self.PATEH_FOLDER

        CATENAME = "SolarGenerator"
        CATEDOR = "power"
        TEMPO_ICON = "solar-panel.png"
        BL_NAME_2 = "Солнечная панель"
        BL_CR_NAME = "Солнечную панель"
        BL_NAME = "солнечной панели"
        ENTRY_NAME1 = "solarPanel"
        NAME = "SolarPanels"
        FOLDER = "solar_panels"
        
        # Очищаем окно
        self.clear_window()
        
        # Основной фрейм с прокруткой
        main_frame = ctk.CTkFrame(self.root, fg_color="#2b2b2b")
        main_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
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
            text=f"Название {BL_NAME} (английское, можно пробел, первая буква маленькая):",
            font=("Arial", 16),
            text_color="#BDBDBD"
        ).pack(anchor="w", pady=(0, 5))
        
        entry_name = ctk.CTkEntry(
            name_frame,
            width=400,
            height=40,
            placeholder_text=f"{ENTRY_NAME1} name",
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
            text=f"Свойства {BL_NAME}",
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
            text="Прочность (health):",
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
            text="Скорость стройки (buildTime):",
            font=("Arial", 15),
            text_color="#BDBDBD"
        ).pack(anchor="w", pady=(0, 5))
        
        entry_speed = ctk.CTkEntry(
            speed_frame,
            width=180,
            height=38,
            placeholder_text="1",
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
            text="Размер (size):",
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

        # Производство энергии (специфично для солнечной панели)
        power_frame = ctk.CTkFrame(properties_grid, fg_color="transparent")
        power_frame.grid(row=1, column=1, padx=10, pady=5, sticky="ew")
        
        ctk.CTkLabel(
            power_frame,
            text="Производство энергии (powerProduction):\n(вводите значение в секунду, будет /60)",
            font=("Arial", 15),
            text_color="#BDBDBD"
        ).pack(anchor="w", pady=(0, 5))
        
        entry_power = ctk.CTkEntry(
            power_frame,
            width=180,
            height=38,
            placeholder_text="60",
            font=("Arial", 14),
            validate="key",
            validatecommand=vcmd_float,
            fg_color="#424242",
            border_color="#555555",
            text_color="#FFFFFF",
            placeholder_text_color="#888888"
        )
        entry_power.pack(fill="x")

        # === Always Unlocked с индикатором ===
        
        always_unlocked_var = ctk.BooleanVar(value=False)
        always_unlocked_status = ctk.CTkLabel(properties_card, text="", font=("Arial", 12))

        # === КАРТОЧКА ДЛЯ ПРЕДМЕТОВ СТРОИТЕЛЬСТВА ===
        build_card = ctk.CTkFrame(
            scroll_frame,
            corner_radius=15,
            border_width=2,
            border_color="#404040",
            fg_color="#363636"
        )
        build_card.pack(fill="x", pady=(0, 20))
        
        ctk.CTkLabel(
            build_card,
            text="🔨 Предметы для строительства",
            font=("Arial", 18, "bold"),
            text_color="#4CAF50"
        ).pack(pady=(15, 10), padx=20, anchor="w")
        
        build_items_frame = ctk.CTkFrame(build_card, fg_color="transparent")
        build_items_frame.pack(fill="x", padx=20, pady=(0, 15))
        
        build_items_var = tk.StringVar(value="Выбрано: 0 предметов")
        build_items_label = ctk.CTkLabel(
            build_items_frame,
            textvariable=build_items_var,
            font=("Arial", 12),
            text_color="#9E9E9E",
            wraplength=400
        )
        build_items_label.pack(anchor="w", pady=(5, 0))
        
        ctk.CTkButton(
            build_items_frame,
            text="📋 Выбрать предметы для строительства",
            command=lambda: self.open_items_editor(build_items_var, "build"),
            height=35,
            font=("Arial", 13),
            fg_color="#2E7D32",
            hover_color="#1B5E20",
            corner_radius=6
        ).pack(anchor="w", pady=(0, 5))

        # === КАРТОЧКА ДЛЯ ИССЛЕДОВАНИЯ ===
        research_card = ctk.CTkFrame(
            scroll_frame,
            corner_radius=15,
            border_width=2,
            border_color="#404040",
            fg_color="#363636"
        )
        
        # Переменные для исследования
        selected_block_var = tk.StringVar(value="Не выбран")
        selected_block_internal_var = tk.StringVar(value="")
        selected_block_type_var = tk.StringVar(value="")
        block_icon_label = ctk.CTkLabel(properties_card, text="☀️", font=("Arial", 30))
        block_path_label = ctk.CTkLabel(properties_card, text="", font=("Arial", 10))
        research_items_var = tk.StringVar(value="Выбрано: 0 предметов")

        # ИСПОЛЬЗУЕМ НОВУЮ УНИВЕРСАЛЬНУЮ ФУНКЦИЮ
        always_unlocked_check, select_block_button, select_items_button = self.setup_research_system(
            always_unlocked_var=always_unlocked_var,
            research_card=research_card,
            always_unlocked_status=always_unlocked_status,
            build_card=build_card,
            selected_block_var=selected_block_var,
            selected_block_internal_var=selected_block_internal_var,
            selected_block_type_var=selected_block_type_var,
            block_icon_label=block_icon_label,
            block_path_label=block_path_label,
            research_items_var=research_items_var,
            on_block_selected_callback=None
        )

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

        # === Основная функция создания солнечной панели ===
        def process_solar():
            original_name = entry_name.get().strip()
            
            if not original_name:
                status_label.configure(
                    text="❌ Ошибка: Введите название солнечной панели!", 
                    text_color="#F44336"
                )
                return
            
            # Проверка для always_unlocked = false
            is_valid, error_msg = self.validate_research(
                always_unlocked_var=always_unlocked_var,
                research_items=self.research_items if hasattr(self, 'research_items') else [],
                selected_block_internal_var=selected_block_internal_var
            )
            
            if not is_valid:
                status_label.configure(text=error_msg, text_color="#F44336")
                return
            
            if not hasattr(self, 'build_items') or not self.build_items:
                status_label.configure(
                    text="❌ Ошибка: Выберите предметы для строительства!", 
                    text_color="#F44336"
                )
                return
            
            # Форматируем имя
            constructor_name = self.format_to_lower_camel(original_name)
            if not constructor_name:
                status_label.configure(
                    text="❌ Ошибка: Некорректное название!", 
                    text_color="#F44336"
                )
                return

            # Проверяем, существует ли уже такое имя
            if self.check_block_name_exists(original_name, PATEH_FOLDER):
                status_label.configure(
                    text=f"❌ Ошибка: Имя '{constructor_name}' уже используется!", 
                    text_color="#F44336"
                )
                return
            
            # Копируем текстуру (для солнечной панели одна)
            size_multiplier = int(size_var.get())
            texture_copied = self.copy_block_texture(
                block_name=original_name,
                size_multiplier=size_multiplier,
                target_folder=FOLDER,
                template_names=[TEMPO_ICON]
            )
            texture_status = "✅ Текстура создана" if texture_copied else "⚠️ Текстура не создана"
            
            # Получаем значения свойств
            hp_value = entry_hp.get().strip() or "400"
            speed_raw = entry_speed.get().strip() or "1"
            power_raw = entry_power.get().strip() or "60"
            size_value = size_var.get()
            
            hp_value = str(int(float(hp_value)))
            always_unlocked_value = "true" if always_unlocked_var.get() else "false"
            
            # Делим мощность на 60 (игровой тик)
            try:
                power_in_game = float(power_raw) / 60.0
                power_in_game_str = f"{power_in_game:.4f}f"
            except:
                power_in_game_str = "1.0f"
            
            # Получаем кастомные предметы
            custom_items = self.get_custom_items()
            var_name = constructor_name
            
            # Формируем код для предметов строительства
            build_itemstack_code = ""
            build_items_list = []
            if hasattr(self, 'build_items') and self.build_items:
                item_counts = {}
                for item in self.build_items:
                    item_counts[item] = item_counts.get(item, 0) + 1
                
                item_parts = []
                for item_name, count in item_counts.items():
                    code_name = self.get_item_code_name(item_name, custom_items)
                    item_parts.append(f"{code_name}, {count}")
                    build_items_list.append((item_name, count))
                
                build_itemstack_code = f"\n            requirements(Category.{CATEDOR},\n                ItemStack.with({', '.join(item_parts)}));"
            
            # Формируем свойства солнечной панели
            properties = f"""    health = {hp_value};
                size = {size_value};
                buildTime = {speed_raw};
                alwaysUnlocked = {always_unlocked_value};
                buildVisibility = BuildVisibility.shown;
                category = Category.{CATEDOR};{build_itemstack_code}
                powerProduction = {power_in_game_str}; // {power_raw}/сек деленное на 60

                localizedName = Core.bundle.get("{var_name}.name", "OH NO");
                description = Core.bundle.get("{var_name}.description", "OH NO");"""
            
            # Пути к файлам
            mod_name_lower = self.mod_name.lower() if self.mod_name else self.mod_name
            block_registration_path = self.get_absolute_path(f"src/{mod_name_lower}/init/blocks/{FOLDER}/{NAME}.java")
            main_mod_path = Path(self.mod_folder) / "src" / mod_name_lower / f"{self.mod_name}JavaMod.java"
            
            block_registration_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Читаем или создаем файл регистрации блоков
            try:
                with open(block_registration_path, 'r', encoding='utf-8') as file:
                    content = file.read()
            except FileNotFoundError:
                content = f"""package {mod_name_lower}.init.blocks.{FOLDER};

import arc.graphics.Color;
import arc.Core;
import mindustry.type.ItemStack;
import mindustry.type.Category;
import mindustry.world.Block;
import mindustry.world.blocks.power.{CATENAME};
import mindustry.world.meta.BuildVisibility;
import mindustry.content.Items;
import mindustry.Vars;
import {mod_name_lower}.init.items.ModItems;

public class {NAME} {{
    public static {CATENAME};
                                            
    public static void Load() {{
        // Регистрация блоков
    }}
}}"""
            
            solar_exists = var_name in content
            tree_file_created = False
            main_file_updated = False
            
            if not solar_exists:
                # Добавляем переменную блока
                if f"public static {CATENAME};" in content:
                    content = content.replace(
                        f"public static {CATENAME};",
                        f"public static {CATENAME} {var_name};"
                    )
                elif f"public static {CATENAME} " in content:
                    lines = content.split('\n')
                    for i, line in enumerate(lines):
                        if f"public static {CATENAME} " in line and var_name not in line:
                            lines[i] = line.rstrip(';') + f", {var_name};"
                            content = '\n'.join(lines)
                            break
                
                # Добавляем инициализацию блока
                load_start = content.find("public static void Load() {")
                if load_start != -1:
                    open_brace = content.find('{', load_start)
                    if open_brace != -1:
                        insert_pos = open_brace + 1
                        indent = "        "
                        solar_code = f'\n{indent}{var_name} = new {CATENAME}("{constructor_name}"){{{{\n{indent}{properties}\n{indent}}}}};'
                        content = content[:insert_pos] + solar_code + content[insert_pos:]
                
                # Сохраняем файл
                with open(block_registration_path, 'w', encoding='utf-8') as file:
                    file.write(content)
                
                # Обновляем главный файл мода
                try:
                    with open(main_mod_path, 'r', encoding='utf-8') as file:
                        main_content = file.read()
                    
                    # Добавляем импорт
                    import_statement = f"import {mod_name_lower}.init.blocks.{FOLDER}.{NAME};"
                    if import_statement not in main_content:
                        import_add_pos = main_content.find("//import_add")
                        if import_add_pos != -1:
                            insert_pos = import_add_pos + len("//import_add")
                            if insert_pos < len(main_content) and main_content[insert_pos] == '\n':
                                main_content = main_content[:insert_pos] + f"\n{import_statement}" + main_content[insert_pos:]
                            else:
                                main_content = main_content[:insert_pos] + f"\n{import_statement}" + main_content[insert_pos:]
                    
                    # Добавляем вызов Load
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
                    
                    main_file_updated = True
                    
                    # Создаем файл дерева технологий, если Always Unlocked = false
                    if not always_unlocked_var.get():
                        research_items_list = []
                        if hasattr(self, 'research_items') and self.research_items:
                            item_counts = {}
                            for item in self.research_items:
                                item_counts[item] = item_counts.get(item, 0) + 1
                            
                            for item_name, count in item_counts.items():
                                research_items_list.append((item_name, count))
                        
                        research_block = selected_block_internal_var.get()
                        
                        # Используем универсальную функцию
                        tree_file_created = self.create_tech_tree_file_universal(
                            block_var_name=var_name,
                            block_constructor_name=constructor_name,
                            research_block=research_block,
                            research_items=research_items_list,
                            block_type="solar",
                            folder_name=FOLDER,
                            class_name="SolarTree"
                        )
                        
                        # ИСПОЛЬЗУЕМ НОВУЮ УНИВЕРСАЛЬНУЮ ФУНКЦИЮ для обновления главного файла
                        if tree_file_created:
                            self.update_main_mod_file_universal(
                                import_path=f"{mod_name_lower}.content.SolarTree",
                                load_statement="SolarTree.Load();"
                            )
                    
                    # Формируем сообщение о результате
                    status_messages = [
                        f"✅ {BL_NAME_2} '{var_name}' успешно создана!",
                        f'📝 Имя в игре: "{constructor_name}"',
                        f"{texture_status}",
                    ]
                    
                    # Добавляем информацию о Always Unlocked
                    if always_unlocked_var.get():
                        status_messages.append("🔓 Always Unlocked: ДА (доступен с самого начала)")
                    else:
                        status_messages.append("🔒 Always Unlocked: НЕТ (требуется исследование)")
                    
                    status_messages.extend([
                        f"📊 Свойства {BL_NAME}:",
                        f"  • ❤️ Здоровье: {hp_value}",
                        f"  • ⚡ Скорость стройки: {speed_raw}",
                        f"  • 📏 Размер: {size_value}",
                        f"  • ⚡ Производство энергии: {power_raw}/сек ({power_in_game_str} в коде)",
                    ])
                    
                    if build_items_list:
                        items_list = []
                        for item_name, count in build_items_list:
                            if item_name in custom_items:
                                items_list.append(f"ModItems.{item_name} ×{count}")
                            else:
                                display_name = item_name.replace('-', ' ').title()
                                items_list.append(f"{display_name} ×{count}")
                        
                        status_messages.append(f"  • 🔨 Стройка: {', '.join(items_list)}")
                    
                    if not always_unlocked_var.get():
                        if hasattr(self, 'research_items') and self.research_items:
                            research_list = []
                            item_counts = {}
                            for item in self.research_items:
                                item_counts[item] = item_counts.get(item, 0) + 1
                            
                            for item_name, count in item_counts.items():
                                if item_name in custom_items:
                                    research_list.append(f"ModItems.{item_name} ×{count}")
                                else:
                                    display_name = item_name.replace('-', ' ').title()
                                    research_list.append(f"{display_name} ×{count}")
                            
                            status_messages.append(f"  • 💰 Исследование: {', '.join(research_list)}")
                        
                        status_messages.append(f"  • 🎯 Блок исследования: {selected_block_var.get()}")
                        
                        if tree_file_created:
                            status_messages.append(f"  • 🌳 SolarTree.java создан и добавлен в main (SolarTree.Load())")
                        else:
                            status_messages.append(f"  • ⚠️ SolarTree.java не создан")
                    
                    if main_file_updated:
                        status_messages.append(f"  • 📄 Главный файл мода обновлен")
                    
                    status_text = "\n".join(status_messages)
                    status_label.configure(text=status_text, text_color="#4CAF50")
                    
                except Exception as e:
                    status_label.configure(text=f"❌ Ошибка: {str(e)}", text_color="#F44336")
            else:
                status_label.configure(text=f"⚠️ {BL_NAME_2} уже существует", text_color="#FF9800")
            
            self.root.after(5000, lambda: status_label.configure(text=""))

        # === Кнопки действий ===
        buttons_frame = ctk.CTkFrame(button_frame, fg_color="transparent")
        buttons_frame.pack(pady=10)
        
        ctk.CTkButton(
            buttons_frame,
            text=f"Создать {BL_CR_NAME}",
            command=process_solar,
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
        
        # Инициализация переменных
        self.build_items = []
        self.research_items = []

    def create_shield_wall(self):
        """Создает или добавляет новую экранированную стену в shield_walls/ShieldWalls.java"""
        
        # Константы для экранированной стены
        PATEH_FOLDER = self.PATEH_FOLDER

        CATENAME = "ShieldWall"
        CATEDOR = "defense"
        TEMPO_ICON = "shielded-wall.png"
        TEMPO_ICON_TOP = "shielded-wall-glow.png"
        BL_NAME_2 = "Экранированная стена"
        BL_CR_NAME = "Экранированную стену"
        BL_NAME = "экранированной стены"
        ENTRY_NAME1 = "shieldWall"
        NAME = "ShieldWalls"
        FOLDER = "shield_walls"
        
        # Очищаем окно
        self.clear_window()
        
        # Основной фрейм с прокруткой
        main_frame = ctk.CTkFrame(self.root, fg_color="#2b2b2b")
        main_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        scroll_frame = ctk.CTkScrollableFrame(
            main_frame,
            width=500,
            height=700,
            fg_color="#2b2b2b"
        )
        scroll_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Заголовок
        title_frame = ctk.CTkFrame(scroll_frame, fg_color="transparent")
        title_frame.pack(fill="x", pady=(0, 20))
        
        ctk.CTkLabel(
            title_frame,
            text="Создание экранированной стены",
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
            text=f"Название {BL_NAME} (английское, можно пробел, первая буква маленькая):",
            font=("Arial", 16),
            text_color="#BDBDBD"
        ).pack(anchor="w", pady=(0, 5))
        
        entry_name = ctk.CTkEntry(
            name_frame,
            width=400,
            height=40,
            placeholder_text=f"{ENTRY_NAME1} name",
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
            text=f"Свойства {BL_NAME}",
            font=("Arial", 18, "bold"),
            text_color="#E0E0E0"
        ).pack(pady=(15, 10), padx=20, anchor="w")

        # Грид для свойств
        properties_grid = ctk.CTkFrame(properties_card, fg_color="transparent")
        properties_grid.pack(fill="x", padx=20, pady=(0, 15))

        # Здоровье стены
        hp_frame = ctk.CTkFrame(properties_grid, fg_color="transparent")
        hp_frame.grid(row=0, column=0, padx=10, pady=5, sticky="ew")
        
        ctk.CTkLabel(
            hp_frame,
            text="Прочность стены (health):",
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
            text="Скорость стройки (buildTime):",
            font=("Arial", 15),
            text_color="#BDBDBD"
        ).pack(anchor="w", pady=(0, 5))
        
        entry_speed = ctk.CTkEntry(
            speed_frame,
            width=180,
            height=38,
            placeholder_text="1",
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
            text="Размер (size):",
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

        # Потребление энергии
        power_frame = ctk.CTkFrame(properties_grid, fg_color="transparent")
        power_frame.grid(row=1, column=1, padx=10, pady=5, sticky="ew")
        
        ctk.CTkLabel(
            power_frame,
            text="Потребление энергии (consumePower) в сек:\n(введите значение, будет /60)",
            font=("Arial", 15),
            text_color="#BDBDBD"
        ).pack(anchor="w", pady=(0, 5))
        
        entry_power = ctk.CTkEntry(
            power_frame,
            width=180,
            height=38,
            placeholder_text="60",
            font=("Arial", 14),
            validate="key",
            validatecommand=vcmd_int,
            fg_color="#424242",
            border_color="#555555",
            text_color="#FFFFFF",
            placeholder_text_color="#888888"
        )
        entry_power.pack(fill="x")

        # Здоровье щита
        shield_hp_frame = ctk.CTkFrame(properties_grid, fg_color="transparent")
        shield_hp_frame.grid(row=2, column=0, padx=10, pady=5, sticky="ew")
        
        ctk.CTkLabel(
            shield_hp_frame,
            text="Прочность щита (shieldHealth):",
            font=("Arial", 15),
            text_color="#BDBDBD"
        ).pack(anchor="w", pady=(0, 5))
        
        entry_shield_hp = ctk.CTkEntry(
            shield_hp_frame,
            width=180,
            height=38,
            placeholder_text="1000",
            font=("Arial", 14),
            validate="key",
            validatecommand=vcmd_int,
            fg_color="#424242",
            border_color="#555555",
            text_color="#FFFFFF",
            placeholder_text_color="#888888"
        )
        entry_shield_hp.pack(fill="x")

        # Перезарядка щита
        cooldown_frame = ctk.CTkFrame(properties_grid, fg_color="transparent")
        cooldown_frame.grid(row=2, column=1, padx=10, pady=5, sticky="ew")
        
        ctk.CTkLabel(
            cooldown_frame,
            text="Перезарядка (breakCooldown):",
            font=("Arial", 15),
            text_color="#BDBDBD"
        ).pack(anchor="w", pady=(0, 5))
        
        entry_cooldown = ctk.CTkEntry(
            cooldown_frame,
            width=180,
            height=38,
            placeholder_text="60",
            font=("Arial", 14),
            validate="key",
            validatecommand=vcmd_int,
            fg_color="#424242",
            border_color="#555555",
            text_color="#FFFFFF",
            placeholder_text_color="#888888"
        )
        entry_cooldown.pack(fill="x")

        # Скорость регенерации
        regen_frame = ctk.CTkFrame(properties_grid, fg_color="transparent")
        regen_frame.grid(row=3, column=0, padx=10, pady=5, sticky="ew")
        
        ctk.CTkLabel(
            regen_frame,
            text="Скорость регенерации (regenSpeed):",
            font=("Arial", 15),
            text_color="#BDBDBD"
        ).pack(anchor="w", pady=(0, 5))
        
        entry_regen = ctk.CTkEntry(
            regen_frame,
            width=180,
            height=38,
            placeholder_text="30",
            font=("Arial", 14),
            validate="key",
            validatecommand=vcmd_int,
            fg_color="#424242",
            border_color="#555555",
            text_color="#FFFFFF",
            placeholder_text_color="#888888"
        )
        entry_regen.pack(fill="x")

        # === Always Unlocked с индикатором ===
        
        always_unlocked_var = ctk.BooleanVar(value=False)
        always_unlocked_status = ctk.CTkLabel(properties_card, text="", font=("Arial", 12))

        # === КАРТОЧКА ДЛЯ ПРЕДМЕТОВ СТРОИТЕЛЬСТВА ===
        build_card = ctk.CTkFrame(
            scroll_frame,
            corner_radius=15,
            border_width=2,
            border_color="#404040",
            fg_color="#363636"
        )
        build_card.pack(fill="x", pady=(0, 20))
        
        ctk.CTkLabel(
            build_card,
            text="🔨 Предметы для строительства",
            font=("Arial", 18, "bold"),
            text_color="#4CAF50"
        ).pack(pady=(15, 10), padx=20, anchor="w")
        
        build_items_frame = ctk.CTkFrame(build_card, fg_color="transparent")
        build_items_frame.pack(fill="x", padx=20, pady=(0, 15))
        
        build_items_var = tk.StringVar(value="Выбрано: 0 предметов")
        build_items_label = ctk.CTkLabel(
            build_items_frame,
            textvariable=build_items_var,
            font=("Arial", 12),
            text_color="#9E9E9E",
            wraplength=400
        )
        build_items_label.pack(anchor="w", pady=(5, 0))
        
        ctk.CTkButton(
            build_items_frame,
            text="📋 Выбрать предметы для строительства",
            command=lambda: self.open_items_editor(build_items_var, "build"),
            height=35,
            font=("Arial", 13),
            fg_color="#2E7D32",
            hover_color="#1B5E20",
            corner_radius=6
        ).pack(anchor="w", pady=(0, 5))

        # === КАРТОЧКА ДЛЯ ИССЛЕДОВАНИЯ ===
        research_card = ctk.CTkFrame(
            scroll_frame,
            corner_radius=15,
            border_width=2,
            border_color="#404040",
            fg_color="#363636"
        )
        
        # Переменные для исследования
        selected_block_var = tk.StringVar(value="Не выбран")
        selected_block_internal_var = tk.StringVar(value="")
        selected_block_type_var = tk.StringVar(value="")
        block_icon_label = ctk.CTkLabel(properties_card, text="🛡️", font=("Arial", 30))
        block_path_label = ctk.CTkLabel(properties_card, text="", font=("Arial", 10))
        research_items_var = tk.StringVar(value="Выбрано: 0 предметов")

        # ИСПОЛЬЗУЕМ НОВУЮ УНИВЕРСАЛЬНУЮ ФУНКЦИЮ
        always_unlocked_check, select_block_button, select_items_button = self.setup_research_system(
            always_unlocked_var=always_unlocked_var,
            research_card=research_card,
            always_unlocked_status=always_unlocked_status,
            build_card=build_card,
            selected_block_var=selected_block_var,
            selected_block_internal_var=selected_block_internal_var,
            selected_block_type_var=selected_block_type_var,
            block_icon_label=block_icon_label,
            block_path_label=block_path_label,
            research_items_var=research_items_var,
            on_block_selected_callback=None
        )

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

        # === Основная функция создания экранированной стены ===
        def process_shield():
            original_name = entry_name.get().strip()
            
            if not original_name:
                status_label.configure(
                    text="❌ Ошибка: Введите название экранированной стены!", 
                    text_color="#F44336"
                )
                return
            
            # Проверка для always_unlocked = false
            is_valid, error_msg = self.validate_research(
                always_unlocked_var=always_unlocked_var,
                research_items=self.research_items if hasattr(self, 'research_items') else [],
                selected_block_internal_var=selected_block_internal_var
            )
            
            if not is_valid:
                status_label.configure(text=error_msg, text_color="#F44336")
                return
            
            if not hasattr(self, 'build_items') or not self.build_items:
                status_label.configure(
                    text="❌ Ошибка: Выберите предметы для строительства!", 
                    text_color="#F44336"
                )
                return
            
            # Форматируем имя
            constructor_name = self.format_to_lower_camel(original_name)
            if not constructor_name:
                status_label.configure(
                    text="❌ Ошибка: Некорректное название!", 
                    text_color="#F44336"
                )
                return

            # Проверяем, существует ли уже такое имя
            if self.check_block_name_exists(original_name, PATEH_FOLDER):
                status_label.configure(
                    text=f"❌ Ошибка: Имя '{constructor_name}' уже используется!", 
                    text_color="#F44336"
                )
                return
            
            # Копируем текстуры (основная и с эффектом свечения)
            size_multiplier = int(size_var.get())
            texture_configs = [
                {"template": TEMPO_ICON, "suffix": ""},
                {"template": TEMPO_ICON_TOP, "suffix": "-glow"},
            ]
            
            texture_copied = self.copy_block_textures_multi(
                block_name=original_name,
                size_multiplier=size_multiplier,
                target_folder=FOLDER,
                texture_configs=texture_configs
            )
            texture_status = "✅ Текстуры созданы" if texture_copied else "⚠️ Текстуры не созданы"
            
            # Получаем значения свойств
            hp_value = entry_hp.get().strip() or "400"
            speed_raw = entry_speed.get().strip() or "1"
            power_raw = entry_power.get().strip() or "60"
            shield_hp_raw = entry_shield_hp.get().strip() or "1000"
            cooldown_raw = entry_cooldown.get().strip() or "60"
            regen_raw = entry_regen.get().strip() or "30"
            size_value = size_var.get()
            
            hp_value = str(int(float(hp_value)))
            always_unlocked_value = "true" if always_unlocked_var.get() else "false"
            
            # Делим потребление энергии на 60
            try:
                power_in_game = float(power_raw) / 60.0
                power_in_game_str = f"{power_in_game:.4f}f"
            except:
                power_in_game_str = "1.0f"
            
            # Получаем кастомные предметы
            custom_items = self.get_custom_items()
            var_name = constructor_name
            
            # Формируем код для предметов строительства
            build_itemstack_code = ""
            build_items_list = []
            if hasattr(self, 'build_items') and self.build_items:
                item_counts = {}
                for item in self.build_items:
                    item_counts[item] = item_counts.get(item, 0) + 1
                
                item_parts = []
                for item_name, count in item_counts.items():
                    code_name = self.get_item_code_name(item_name, custom_items)
                    item_parts.append(f"{code_name}, {count}")
                    build_items_list.append((item_name, count))
                
                build_itemstack_code = f"\n            requirements(Category.{CATEDOR},\n                ItemStack.with({', '.join(item_parts)}));"
            
            # Формируем свойства экранированной стены
            properties = f"""    health = {hp_value};
                size = {size_value};
                buildTime = {speed_raw};
                alwaysUnlocked = {always_unlocked_value};
                buildVisibility = BuildVisibility.shown;
                category = Category.{CATEDOR};{build_itemstack_code}
                consumePower({power_in_game_str});
                outputsPower = true;
                shieldHealth = {shield_hp_raw};
                breakCooldown = {cooldown_raw};
                regenSpeed = {regen_raw};

                localizedName = Core.bundle.get("{var_name}.name", "OH NO");
                description = Core.bundle.get("{var_name}.description", "OH NO");"""
            
            # Пути к файлам
            mod_name_lower = self.mod_name.lower() if self.mod_name else self.mod_name
            block_registration_path = self.get_absolute_path(f"src/{mod_name_lower}/init/blocks/{FOLDER}/{NAME}.java")
            main_mod_path = Path(self.mod_folder) / "src" / mod_name_lower / f"{self.mod_name}JavaMod.java"
            
            block_registration_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Читаем или создаем файл регистрации блоков
            try:
                with open(block_registration_path, 'r', encoding='utf-8') as file:
                    content = file.read()
            except FileNotFoundError:
                content = f"""package {mod_name_lower}.init.blocks.{FOLDER};

import arc.graphics.Color;
import arc.Core;
import mindustry.type.ItemStack;
import mindustry.type.Category;
import mindustry.world.Block;
import mindustry.world.blocks.{CATEDOR}.{CATENAME};
import mindustry.world.meta.BuildVisibility;
import mindustry.content.Items;
import mindustry.Vars;
import {mod_name_lower}.init.items.ModItems;

public class {NAME} {{
    public static {CATENAME};
                                            
    public static void Load() {{
        // Регистрация блоков
    }}
}}"""
            
            shield_exists = var_name in content
            tree_file_created = False
            main_file_updated = False
            
            if not shield_exists:
                # Добавляем переменную блока
                if f"public static {CATENAME};" in content:
                    content = content.replace(
                        f"public static {CATENAME};",
                        f"public static {CATENAME} {var_name};"
                    )
                elif f"public static {CATENAME} " in content:
                    lines = content.split('\n')
                    for i, line in enumerate(lines):
                        if f"public static {CATENAME} " in line and var_name not in line:
                            lines[i] = line.rstrip(';') + f", {var_name};"
                            content = '\n'.join(lines)
                            break
                
                # Добавляем инициализацию блока
                load_start = content.find("public static void Load() {")
                if load_start != -1:
                    open_brace = content.find('{', load_start)
                    if open_brace != -1:
                        insert_pos = open_brace + 1
                        indent = "        "
                        shield_code = f'\n{indent}{var_name} = new {CATENAME}("{constructor_name}"){{{{\n{indent}{properties}\n{indent}}}}};'
                        content = content[:insert_pos] + shield_code + content[insert_pos:]
                
                # Сохраняем файл
                with open(block_registration_path, 'w', encoding='utf-8') as file:
                    file.write(content)
                
                # Обновляем главный файл мода
                try:
                    with open(main_mod_path, 'r', encoding='utf-8') as file:
                        main_content = file.read()
                    
                    # Добавляем импорт
                    import_statement = f"import {mod_name_lower}.init.blocks.{FOLDER}.{NAME};"
                    if import_statement not in main_content:
                        import_add_pos = main_content.find("//import_add")
                        if import_add_pos != -1:
                            insert_pos = import_add_pos + len("//import_add")
                            if insert_pos < len(main_content) and main_content[insert_pos] == '\n':
                                main_content = main_content[:insert_pos] + f"\n{import_statement}" + main_content[insert_pos:]
                            else:
                                main_content = main_content[:insert_pos] + f"\n{import_statement}" + main_content[insert_pos:]
                    
                    # Добавляем вызов Load
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
                    
                    main_file_updated = True
                    
                    # Создаем файл дерева технологий, если Always Unlocked = false
                    if not always_unlocked_var.get():
                        research_items_list = []
                        if hasattr(self, 'research_items') and self.research_items:
                            item_counts = {}
                            for item in self.research_items:
                                item_counts[item] = item_counts.get(item, 0) + 1
                            
                            for item_name, count in item_counts.items():
                                research_items_list.append((item_name, count))
                        
                        research_block = selected_block_internal_var.get()
                        
                        # Используем универсальную функцию
                        tree_file_created = self.create_tech_tree_file_universal(
                            block_var_name=var_name,
                            block_constructor_name=constructor_name,
                            research_block=research_block,
                            research_items=research_items_list,
                            block_type="shield",
                            folder_name=FOLDER,
                            class_name="ShieldWallTree"
                        )
                        
                        # ИСПОЛЬЗУЕМ НОВУЮ УНИВЕРСАЛЬНУЮ ФУНКЦИЮ для обновления главного файла
                        if tree_file_created:
                            self.update_main_mod_file_universal(
                                import_path=f"{mod_name_lower}.content.ShieldWallTree",
                                load_statement="ShieldWallTree.Load();"
                            )
                    
                    # Формируем сообщение о результате
                    status_messages = [
                        f"✅ {BL_NAME_2} '{var_name}' успешно создана!",
                        f'📝 Имя в игре: "{constructor_name}"',
                        f"{texture_status}",
                    ]
                    
                    # Добавляем информацию о Always Unlocked
                    if always_unlocked_var.get():
                        status_messages.append("🔓 Always Unlocked: ДА (доступен с самого начала)")
                    else:
                        status_messages.append("🔒 Always Unlocked: НЕТ (требуется исследование)")
                    
                    status_messages.extend([
                        f"📊 Свойства {BL_NAME}:",
                        f"  • ❤️ Здоровье стены: {hp_value}",
                        f"  • ⚡ Скорость стройки: {speed_raw}",
                        f"  • 📏 Размер: {size_value}",
                        f"  • ⚡ Потребление энергии: {power_raw}/сек ({power_in_game_str} в коде)",
                        f"  • 🛡️ Здоровье щита: {shield_hp_raw}",
                        f"  • ⏱️ Перезарядка: {cooldown_raw}",
                        f"  • 🔄 Регенерация: {regen_raw}",
                    ])
                    
                    if build_items_list:
                        items_list = []
                        for item_name, count in build_items_list:
                            if item_name in custom_items:
                                items_list.append(f"ModItems.{item_name} ×{count}")
                            else:
                                display_name = item_name.replace('-', ' ').title()
                                items_list.append(f"{display_name} ×{count}")
                        
                        status_messages.append(f"  • 🔨 Стройка: {', '.join(items_list)}")
                    
                    if not always_unlocked_var.get():
                        if hasattr(self, 'research_items') and self.research_items:
                            research_list = []
                            item_counts = {}
                            for item in self.research_items:
                                item_counts[item] = item_counts.get(item, 0) + 1
                            
                            for item_name, count in item_counts.items():
                                if item_name in custom_items:
                                    research_list.append(f"ModItems.{item_name} ×{count}")
                                else:
                                    display_name = item_name.replace('-', ' ').title()
                                    research_list.append(f"{display_name} ×{count}")
                            
                            status_messages.append(f"  • 💰 Исследование: {', '.join(research_list)}")
                        
                        status_messages.append(f"  • 🎯 Блок исследования: {selected_block_var.get()}")
                        
                        if tree_file_created:
                            status_messages.append(f"  • 🌳 ShieldWallTree.java создан и добавлен в main (ShieldWallTree.Load())")
                        else:
                            status_messages.append(f"  • ⚠️ ShieldWallTree.java не создан")
                    
                    if main_file_updated:
                        status_messages.append(f"  • 📄 Главный файл мода обновлен")
                    
                    status_text = "\n".join(status_messages)
                    status_label.configure(text=status_text, text_color="#4CAF50")
                    
                except Exception as e:
                    status_label.configure(text=f"❌ Ошибка: {str(e)}", text_color="#F44336")
            else:
                status_label.configure(text=f"⚠️ {BL_NAME_2} уже существует", text_color="#FF9800")
            
            self.root.after(5000, lambda: status_label.configure(text=""))

        # === Кнопки действий ===
        buttons_frame = ctk.CTkFrame(button_frame, fg_color="transparent")
        buttons_frame.pack(pady=10)
        
        ctk.CTkButton(
            buttons_frame,
            text=f"Создать {BL_CR_NAME}",
            command=process_shield,
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
        
        # Инициализация переменных
        self.build_items = []
        self.research_items = []

    def create_power_node(self):
        """Создает или добавляет новый узел питания в power_nodes/PowerNodes.java"""
        
        # Константы для узла питания
        PATEH_FOLDER = self.PATEH_FOLDER

        CATENAME = "PowerNode"
        CATEDOR = "power"
        TEMPO_ICON = "power-node.png"
        BL_NAME_2 = "Узел питания"
        BL_CR_NAME = "Узел питания"
        BL_NAME = "узла питания"
        ENTRY_NAME1 = "powerNode"
        NAME = "PowerNodes"
        FOLDER = "power_nodes"
        
        # Очищаем окно
        self.clear_window()
        
        # Основной фрейм с прокруткой
        main_frame = ctk.CTkFrame(self.root, fg_color="#2b2b2b")
        main_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        scroll_frame = ctk.CTkScrollableFrame(
            main_frame,
            width=500,
            height=700,
            fg_color="#2b2b2b"
        )
        scroll_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Заголовок
        title_frame = ctk.CTkFrame(scroll_frame, fg_color="transparent")
        title_frame.pack(fill="x", pady=(0, 20))
        
        ctk.CTkLabel(
            title_frame,
            text="Создание узла питания",
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
            text=f"Название {BL_NAME} (английское, можно пробел, первая буква маленькая):",
            font=("Arial", 16),
            text_color="#BDBDBD"
        ).pack(anchor="w", pady=(0, 5))
        
        entry_name = ctk.CTkEntry(
            name_frame,
            width=400,
            height=40,
            placeholder_text=f"{ENTRY_NAME1} name",
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

        vcmd_float = (self.root.register(validate_float_input), '%P')
        vcmd_int = (self.root.register(validate_int_input), '%P')

        # === Переменные для хранения цветов ===
        map_color_var = tk.StringVar(value="#ffaa00")
        outline_color_var = tk.StringVar(value="#4d4d4d")
        laser_color1_var = tk.StringVar(value="#ffff00")
        laser_color2_var = tk.StringVar(value="#ffaa00")
        light_color_var = tk.StringVar(value="#ffdd55")

        # === Функции выбора цвета ===
        def choose_color(color_var, button):
            color = colorchooser.askcolor(title="Выберите цвет", initialcolor=color_var.get())
            if color[1]:
                color_var.set(color[1])
                button.configure(fg_color=color[1])

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
            text=f"Свойства {BL_NAME}",
            font=("Arial", 18, "bold"),
            text_color="#E0E0E0"
        ).pack(pady=(15, 10), padx=20, anchor="w")

        # Создаем холст с прокруткой для свойств
        properties_scroll = ctk.CTkScrollableFrame(properties_card, fg_color="transparent", height=300)
        properties_scroll.pack(fill="both", expand=True, padx=20, pady=(0, 15))
        
        # Грид для свойств
        properties_grid = ctk.CTkFrame(properties_scroll, fg_color="transparent")
        properties_grid.pack(fill="x")

        # Здоровье
        hp_frame = ctk.CTkFrame(properties_grid, fg_color="transparent")
        hp_frame.grid(row=0, column=0, padx=10, pady=5, sticky="ew")
        
        ctk.CTkLabel(
            hp_frame,
            text="Прочность (health):",
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
            text="Скорость стройки (buildTime):",
            font=("Arial", 15),
            text_color="#BDBDBD"
        ).pack(anchor="w", pady=(0, 5))
        
        entry_speed = ctk.CTkEntry(
            speed_frame,
            width=180,
            height=38,
            placeholder_text="1",
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
            text="Размер (size):",
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

        # Дальность
        range_frame = ctk.CTkFrame(properties_grid, fg_color="transparent")
        range_frame.grid(row=1, column=1, padx=10, pady=5, sticky="ew")
        
        ctk.CTkLabel(
            range_frame,
            text="Дальность подключения (laserRange):",
            font=("Arial", 15),
            text_color="#BDBDBD"
        ).pack(anchor="w", pady=(0, 5))
        
        entry_range = ctk.CTkEntry(
            range_frame,
            width=180,
            height=38,
            placeholder_text="6",
            font=("Arial", 14),
            validate="key",
            validatecommand=vcmd_int,
            fg_color="#424242",
            border_color="#555555",
            text_color="#FFFFFF",
            placeholder_text_color="#888888"
        )
        entry_range.pack(fill="x")

        # Максимальное количество подключений
        max_nodes_frame = ctk.CTkFrame(properties_grid, fg_color="transparent")
        max_nodes_frame.grid(row=2, column=0, padx=10, pady=5, sticky="ew")
        
        ctk.CTkLabel(
            max_nodes_frame,
            text="Макс. подключений (maxNodes):",
            font=("Arial", 15),
            text_color="#BDBDBD"
        ).pack(anchor="w", pady=(0, 5))
        
        entry_max_nodes = ctk.CTkEntry(
            max_nodes_frame,
            width=180,
            height=38,
            placeholder_text="10",
            font=("Arial", 14),
            validate="key",
            validatecommand=vcmd_int,
            fg_color="#424242",
            border_color="#555555",
            text_color="#FFFFFF",
            placeholder_text_color="#888888"
        )
        entry_max_nodes.pack(fill="x")

        # mapColor
        map_color_frame = ctk.CTkFrame(properties_grid, fg_color="transparent")
        map_color_frame.grid(row=3, column=0, padx=10, pady=5, sticky="ew")
        
        ctk.CTkLabel(
            map_color_frame,
            text="mapColor (цвет на карте):",
            font=("Arial", 15),
            text_color="#BDBDBD"
        ).pack(anchor="w", pady=(0, 5))
        
        entry_map_color = ctk.CTkButton(
            map_color_frame,
            text="#ffaa00",
            width=180,
            height=38,
            font=("Arial", 14),
            command=lambda: choose_color(map_color_var, entry_map_color),
            fg_color="#ffaa00",
            hover_color="#cc8800",
            text_color="#FFFFFF"
        )
        entry_map_color.pack(fill="x")

        # outlineColor
        outline_color_frame = ctk.CTkFrame(properties_grid, fg_color="transparent")
        outline_color_frame.grid(row=3, column=1, padx=10, pady=5, sticky="ew")
        
        ctk.CTkLabel(
            outline_color_frame,
            text="outlineColor (контур):",
            font=("Arial", 15),
            text_color="#BDBDBD"
        ).pack(anchor="w", pady=(0, 5))
        
        entry_outline_color = ctk.CTkButton(
            outline_color_frame,
            text="#4d4d4d",
            width=180,
            height=38,
            font=("Arial", 14),
            command=lambda: choose_color(outline_color_var, entry_outline_color),
            fg_color="#4d4d4d",
            hover_color="#666666",
            text_color="#FFFFFF"
        )
        entry_outline_color.pack(fill="x")

        # laserColor1
        laser_color1_frame = ctk.CTkFrame(properties_grid, fg_color="transparent")
        laser_color1_frame.grid(row=4, column=0, padx=10, pady=5, sticky="ew")
        
        ctk.CTkLabel(
            laser_color1_frame,
            text="Энергия есть (laserColor1):",
            font=("Arial", 15),
            text_color="#BDBDBD"
        ).pack(anchor="w", pady=(0, 5))
        
        entry_laser_color1 = ctk.CTkButton(
            laser_color1_frame,
            text="#ffff00",
            width=180,
            height=38,
            font=("Arial", 14),
            command=lambda: choose_color(laser_color1_var, entry_laser_color1),
            fg_color="#ffff00",
            hover_color="#cccc00",
            text_color="#000000"
        )
        entry_laser_color1.pack(fill="x")

        # laserColor2
        laser_color2_frame = ctk.CTkFrame(properties_grid, fg_color="transparent")
        laser_color2_frame.grid(row=4, column=1, padx=10, pady=5, sticky="ew")
        
        ctk.CTkLabel(
            laser_color2_frame,
            text="Энергии нет (laserColor2):",
            font=("Arial", 15),
            text_color="#BDBDBD"
        ).pack(anchor="w", pady=(0, 5))
        
        entry_laser_color2 = ctk.CTkButton(
            laser_color2_frame,
            text="#ffaa00",
            width=180,
            height=38,
            font=("Arial", 14),
            command=lambda: choose_color(laser_color2_var, entry_laser_color2),
            fg_color="#ffaa00",
            hover_color="#cc8800",
            text_color="#000000"
        )
        entry_laser_color2.pack(fill="x")

        # lightColor
        light_color_frame = ctk.CTkFrame(properties_grid, fg_color="transparent")
        light_color_frame.grid(row=5, column=0, padx=10, pady=5, sticky="ew")
        
        ctk.CTkLabel(
            light_color_frame,
            text="lightColor (цвет света):",
            font=("Arial", 15),
            text_color="#BDBDBD"
        ).pack(anchor="w", pady=(0, 5))
        
        entry_light_color = ctk.CTkButton(
            light_color_frame,
            text="#ffdd55",
            width=180,
            height=38,
            font=("Arial", 14),
            command=lambda: choose_color(light_color_var, entry_light_color),
            fg_color="#ffdd55",
            hover_color="#ddbb33",
            text_color="#000000"
        )
        entry_light_color.pack(fill="x")

        # === Always Unlocked с индикатором ===
        
        always_unlocked_var = ctk.BooleanVar(value=False)
        always_unlocked_status = ctk.CTkLabel(properties_card, text="", font=("Arial", 12))

        # === КАРТОЧКА ДЛЯ ПРЕДМЕТОВ СТРОИТЕЛЬСТВА ===
        build_card = ctk.CTkFrame(
            scroll_frame,
            corner_radius=15,
            border_width=2,
            border_color="#404040",
            fg_color="#363636"
        )
        build_card.pack(fill="x", pady=(0, 20))
        
        ctk.CTkLabel(
            build_card,
            text="🔨 Предметы для строительства",
            font=("Arial", 18, "bold"),
            text_color="#4CAF50"
        ).pack(pady=(15, 10), padx=20, anchor="w")
        
        build_items_frame = ctk.CTkFrame(build_card, fg_color="transparent")
        build_items_frame.pack(fill="x", padx=20, pady=(0, 15))
        
        build_items_var = tk.StringVar(value="Выбрано: 0 предметов")
        build_items_label = ctk.CTkLabel(
            build_items_frame,
            textvariable=build_items_var,
            font=("Arial", 12),
            text_color="#9E9E9E",
            wraplength=400
        )
        build_items_label.pack(anchor="w", pady=(5, 0))
        
        ctk.CTkButton(
            build_items_frame,
            text="📋 Выбрать предметы для строительства",
            command=lambda: self.open_items_editor(build_items_var, "build"),
            height=35,
            font=("Arial", 13),
            fg_color="#2E7D32",
            hover_color="#1B5E20",
            corner_radius=6
        ).pack(anchor="w", pady=(0, 5))

        # === КАРТОЧКА ДЛЯ ИССЛЕДОВАНИЯ ===
        research_card = ctk.CTkFrame(
            scroll_frame,
            corner_radius=15,
            border_width=2,
            border_color="#404040",
            fg_color="#363636"
        )
        
        # Переменные для исследования
        selected_block_var = tk.StringVar(value="Не выбран")
        selected_block_internal_var = tk.StringVar(value="")
        selected_block_type_var = tk.StringVar(value="")
        block_icon_label = ctk.CTkLabel(properties_card, text="⚡", font=("Arial", 30))
        block_path_label = ctk.CTkLabel(properties_card, text="", font=("Arial", 10))
        research_items_var = tk.StringVar(value="Выбрано: 0 предметов")

        # ИСПОЛЬЗУЕМ НОВУЮ УНИВЕРСАЛЬНУЮ ФУНКЦИЮ
        always_unlocked_check, select_block_button, select_items_button = self.setup_research_system(
            always_unlocked_var=always_unlocked_var,
            research_card=research_card,
            always_unlocked_status=always_unlocked_status,
            build_card=build_card,
            selected_block_var=selected_block_var,
            selected_block_internal_var=selected_block_internal_var,
            selected_block_type_var=selected_block_type_var,
            block_icon_label=block_icon_label,
            block_path_label=block_path_label,
            research_items_var=research_items_var,
            on_block_selected_callback=None
        )

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

        # === Основная функция создания узла питания ===
        def process_power_node():
            original_name = entry_name.get().strip()
            
            if not original_name:
                status_label.configure(
                    text="❌ Ошибка: Введите название узла питания!", 
                    text_color="#F44336"
                )
                return
            
            # Проверка для always_unlocked = false
            is_valid, error_msg = self.validate_research(
                always_unlocked_var=always_unlocked_var,
                research_items=self.research_items if hasattr(self, 'research_items') else [],
                selected_block_internal_var=selected_block_internal_var
            )
            
            if not is_valid:
                status_label.configure(text=error_msg, text_color="#F44336")
                return
            
            if not hasattr(self, 'build_items') or not self.build_items:
                status_label.configure(
                    text="❌ Ошибка: Выберите предметы для строительства!", 
                    text_color="#F44336"
                )
                return
            
            # Форматируем имя
            constructor_name = self.format_to_lower_camel(original_name)
            if not constructor_name:
                status_label.configure(
                    text="❌ Ошибка: Некорректное название!", 
                    text_color="#F44336"
                )
                return

            # Проверяем, существует ли уже такое имя
            if self.check_block_name_exists(original_name, PATEH_FOLDER):
                status_label.configure(
                    text=f"❌ Ошибка: Имя '{constructor_name}' уже используется!", 
                    text_color="#F44336"
                )
                return
            
            # Копируем текстуру
            size_multiplier = int(size_var.get())
            texture_copied = self.copy_block_texture(
                block_name=original_name,
                size_multiplier=size_multiplier,
                target_folder=FOLDER,
                template_names=[TEMPO_ICON]
            )
            texture_status = "✅ Текстура создана" if texture_copied else "⚠️ Текстура не создана"
            
            # Получаем значения свойств
            hp_value = entry_hp.get().strip() or "400"
            speed_raw = entry_speed.get().strip() or "1"
            range_raw = entry_range.get().strip() or "6"
            max_nodes_raw = entry_max_nodes.get().strip() or "10"
            size_value = size_var.get()
            
            hp_value = str(int(float(hp_value)))
            always_unlocked_value = "true" if always_unlocked_var.get() else "false"
            
            map_color_raw = map_color_var.get()
            outline_color_raw = outline_color_var.get()
            laser_color1_raw = laser_color1_var.get()
            laser_color2_raw = laser_color2_var.get()
            light_color_raw = light_color_var.get()
            
            # Получаем кастомные предметы
            custom_items = self.get_custom_items()
            var_name = constructor_name
            
            # Формируем код для предметов строительства
            build_itemstack_code = ""
            build_items_list = []
            if hasattr(self, 'build_items') and self.build_items:
                item_counts = {}
                for item in self.build_items:
                    item_counts[item] = item_counts.get(item, 0) + 1
                
                item_parts = []
                for item_name, count in item_counts.items():
                    code_name = self.get_item_code_name(item_name, custom_items)
                    item_parts.append(f"{code_name}, {count}")
                    build_items_list.append((item_name, count))
                
                build_itemstack_code = f"\n            requirements(Category.{CATEDOR},\n                ItemStack.with({', '.join(item_parts)}));"
            
            # Формируем свойства узла питания
            properties = f"""    health = {hp_value};
                size = {size_value};
                buildTime = {speed_raw};
                alwaysUnlocked = {always_unlocked_value};
                buildVisibility = BuildVisibility.shown;
                laserRange = {range_raw};
                maxNodes = {max_nodes_raw};
                category = Category.{CATEDOR};{build_itemstack_code}
                mapColor = Color.valueOf("{map_color_raw}");
                outlineColor = Color.valueOf("{outline_color_raw}");
                laserColor1 = Color.valueOf("{laser_color1_raw}");
                laserColor2 = Color.valueOf("{laser_color2_raw}");
                lightColor = Color.valueOf("{light_color_raw}");

                localizedName = Core.bundle.get("{var_name}.name", "OH NO");
                description = Core.bundle.get("{var_name}.description", "OH NO");"""
            
            # Пути к файлам
            mod_name_lower = self.mod_name.lower() if self.mod_name else self.mod_name
            block_registration_path = self.get_absolute_path(f"src/{mod_name_lower}/init/blocks/{FOLDER}/{NAME}.java")
            main_mod_path = Path(self.mod_folder) / "src" / mod_name_lower / f"{self.mod_name}JavaMod.java"
            
            block_registration_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Читаем или создаем файл регистрации блоков
            try:
                with open(block_registration_path, 'r', encoding='utf-8') as file:
                    content = file.read()
            except FileNotFoundError:
                content = f"""package {mod_name_lower}.init.blocks.{FOLDER};

import arc.graphics.Color;
import arc.Core;
import mindustry.type.ItemStack;
import mindustry.type.Category;
import mindustry.world.Block;
import mindustry.world.blocks.{CATEDOR}.{CATENAME};
import mindustry.world.meta.BuildVisibility;
import mindustry.content.Items;
import mindustry.Vars;
import {mod_name_lower}.init.items.ModItems;

public class {NAME} {{
    public static {CATENAME};
                                            
    public static void Load() {{
        // Регистрация блоков
    }}
}}"""
            
            node_exists = var_name in content
            tree_file_created = False
            main_file_updated = False
            
            if not node_exists:
                # Добавляем переменную блока
                if f"public static {CATENAME};" in content:
                    content = content.replace(
                        f"public static {CATENAME};",
                        f"public static {CATENAME} {var_name};"
                    )
                elif f"public static {CATENAME} " in content:
                    lines = content.split('\n')
                    for i, line in enumerate(lines):
                        if f"public static {CATENAME} " in line and var_name not in line:
                            lines[i] = line.rstrip(';') + f", {var_name};"
                            content = '\n'.join(lines)
                            break
                
                # Добавляем инициализацию блока
                load_start = content.find("public static void Load() {")
                if load_start != -1:
                    open_brace = content.find('{', load_start)
                    if open_brace != -1:
                        insert_pos = open_brace + 1
                        indent = "        "
                        node_code = f'\n{indent}{var_name} = new {CATENAME}("{constructor_name}"){{{{\n{indent}{properties}\n{indent}}}}};'
                        content = content[:insert_pos] + node_code + content[insert_pos:]
                
                # Сохраняем файл
                with open(block_registration_path, 'w', encoding='utf-8') as file:
                    file.write(content)
                
                # Обновляем главный файл мода
                try:
                    with open(main_mod_path, 'r', encoding='utf-8') as file:
                        main_content = file.read()
                    
                    # Добавляем импорт
                    import_statement = f"import {mod_name_lower}.init.blocks.{FOLDER}.{NAME};"
                    if import_statement not in main_content:
                        import_add_pos = main_content.find("//import_add")
                        if import_add_pos != -1:
                            insert_pos = import_add_pos + len("//import_add")
                            if insert_pos < len(main_content) and main_content[insert_pos] == '\n':
                                main_content = main_content[:insert_pos] + f"\n{import_statement}" + main_content[insert_pos:]
                            else:
                                main_content = main_content[:insert_pos] + f"\n{import_statement}" + main_content[insert_pos:]
                    
                    # Добавляем вызов Load
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
                    
                    main_file_updated = True
                    
                    # Создаем файл дерева технологий, если Always Unlocked = false
                    if not always_unlocked_var.get():
                        research_items_list = []
                        if hasattr(self, 'research_items') and self.research_items:
                            item_counts = {}
                            for item in self.research_items:
                                item_counts[item] = item_counts.get(item, 0) + 1
                            
                            for item_name, count in item_counts.items():
                                research_items_list.append((item_name, count))
                        
                        research_block = selected_block_internal_var.get()
                        
                        # Используем универсальную функцию
                        tree_file_created = self.create_tech_tree_file_universal(
                            block_var_name=var_name,
                            block_constructor_name=constructor_name,
                            research_block=research_block,
                            research_items=research_items_list,
                            block_type="power_node",
                            folder_name=FOLDER,
                            class_name="PowerNodeTree"
                        )
                        
                        # ИСПОЛЬЗУЕМ НОВУЮ УНИВЕРСАЛЬНУЮ ФУНКЦИЮ для обновления главного файла
                        if tree_file_created:
                            self.update_main_mod_file_universal(
                                import_path=f"{mod_name_lower}.content.PowerNodeTree",
                                load_statement="PowerNodeTree.Load();"
                            )
                    
                    # Формируем сообщение о результате
                    status_messages = [
                        f"✅ {BL_NAME_2} '{var_name}' успешно создан!",
                        f'📝 Имя в игре: "{constructor_name}"',
                        f"{texture_status}",
                    ]
                    
                    # Добавляем информацию о Always Unlocked
                    if always_unlocked_var.get():
                        status_messages.append("🔓 Always Unlocked: ДА (доступен с самого начала)")
                    else:
                        status_messages.append("🔒 Always Unlocked: НЕТ (требуется исследование)")
                    
                    status_messages.extend([
                        f"📊 Свойства {BL_NAME}:",
                        f"  • ❤️ Здоровье: {hp_value}",
                        f"  • ⚡ Скорость стройки: {speed_raw}",
                        f"  • 📏 Размер: {size_value}",
                        f"  • 📡 Дальность: {range_raw}",
                        f"  • 🔌 Макс. подключений: {max_nodes_raw}",
                    ])
                    
                    if build_items_list:
                        items_list = []
                        for item_name, count in build_items_list:
                            if item_name in custom_items:
                                items_list.append(f"ModItems.{item_name} ×{count}")
                            else:
                                display_name = item_name.replace('-', ' ').title()
                                items_list.append(f"{display_name} ×{count}")
                        
                        status_messages.append(f"  • 🔨 Стройка: {', '.join(items_list)}")
                    
                    if not always_unlocked_var.get():
                        if hasattr(self, 'research_items') and self.research_items:
                            research_list = []
                            item_counts = {}
                            for item in self.research_items:
                                item_counts[item] = item_counts.get(item, 0) + 1
                            
                            for item_name, count in item_counts.items():
                                if item_name in custom_items:
                                    research_list.append(f"ModItems.{item_name} ×{count}")
                                else:
                                    display_name = item_name.replace('-', ' ').title()
                                    research_list.append(f"{display_name} ×{count}")
                            
                            status_messages.append(f"  • 💰 Исследование: {', '.join(research_list)}")
                        
                        status_messages.append(f"  • 🎯 Блок исследования: {selected_block_var.get()}")
                        
                        if tree_file_created:
                            status_messages.append(f"  • 🌳 PowerNodeTree.java создан и добавлен в main (PowerNodeTree.Load())")
                        else:
                            status_messages.append(f"  • ⚠️ PowerNodeTree.java не создан")
                    
                    if main_file_updated:
                        status_messages.append(f"  • 📄 Главный файл мода обновлен")
                    
                    status_text = "\n".join(status_messages)
                    status_label.configure(text=status_text, text_color="#4CAF50")
                    
                except Exception as e:
                    status_label.configure(text=f"❌ Ошибка: {str(e)}", text_color="#F44336")
            else:
                status_label.configure(text=f"⚠️ {BL_NAME_2} уже существует", text_color="#FF9800")
            
            self.root.after(5000, lambda: status_label.configure(text=""))

        # === Кнопки действий ===
        buttons_frame = ctk.CTkFrame(button_frame, fg_color="transparent")
        buttons_frame.pack(pady=10)
        
        ctk.CTkButton(
            buttons_frame,
            text=f"Создать {BL_CR_NAME}",
            command=process_power_node,
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
        
        # Инициализация переменных
        self.build_items = []
        self.research_items = []

    def create_beam_node(self):
        """Создает или добавляет новый лучевой узел в beam_nodes/BeamNodes.java"""
        
        # Константы для лучевого узла
        PATEH_FOLDER = self.PATEH_FOLDER

        CATENAME = "BeamNode"
        CATEDOR = "power"
        TEMPO_ICON = "beam-node.png"
        BL_NAME_2 = "Лучевой узел"
        BL_CR_NAME = "Лучевой узел"
        BL_NAME = "лучевого узла"
        ENTRY_NAME1 = "beamNode"
        NAME = "BeamNodes"
        FOLDER = "beam_nodes"
        
        # Очищаем окно
        self.clear_window()
        
        # Основной фрейм с прокруткой
        main_frame = ctk.CTkFrame(self.root, fg_color="#2b2b2b")
        main_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        scroll_frame = ctk.CTkScrollableFrame(
            main_frame,
            width=500,
            height=700,
            fg_color="#2b2b2b"
        )
        scroll_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Заголовок
        title_frame = ctk.CTkFrame(scroll_frame, fg_color="transparent")
        title_frame.pack(fill="x", pady=(0, 20))
        
        ctk.CTkLabel(
            title_frame,
            text="Создание лучевого узла",
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
            text=f"Название {BL_NAME} (английское, можно пробел, первая буква маленькая):",
            font=("Arial", 16),
            text_color="#BDBDBD"
        ).pack(anchor="w", pady=(0, 5))
        
        entry_name = ctk.CTkEntry(
            name_frame,
            width=400,
            height=40,
            placeholder_text=f"{ENTRY_NAME1} name",
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

        vcmd_float = (self.root.register(validate_float_input), '%P')
        vcmd_int = (self.root.register(validate_int_input), '%P')

        # === Переменные для хранения цветов ===
        map_color_var = tk.StringVar(value="#ff0000")
        outline_color_var = tk.StringVar(value="#ffffff")
        laser_color1_var = tk.StringVar(value="#ff0000")
        laser_color2_var = tk.StringVar(value="#00ff00")
        light_color_var = tk.StringVar(value="#ffffff")

        # === Функции выбора цвета ===
        def choose_color(color_var, button):
            color = colorchooser.askcolor(title="Выберите цвет", initialcolor=color_var.get())
            if color[1]:
                color_var.set(color[1])
                button.configure(fg_color=color[1])

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
            text=f"Свойства {BL_NAME}",
            font=("Arial", 18, "bold"),
            text_color="#E0E0E0"
        ).pack(pady=(15, 10), padx=20, anchor="w")

        # Создаем холст с прокруткой для свойств
        properties_scroll = ctk.CTkScrollableFrame(properties_card, fg_color="transparent", height=300)
        properties_scroll.pack(fill="both", expand=True, padx=20, pady=(0, 15))
        
        # Грид для свойств
        properties_grid = ctk.CTkFrame(properties_scroll, fg_color="transparent")
        properties_grid.pack(fill="x")

        # Здоровье
        hp_frame = ctk.CTkFrame(properties_grid, fg_color="transparent")
        hp_frame.grid(row=0, column=0, padx=10, pady=5, sticky="ew")
        
        ctk.CTkLabel(
            hp_frame,
            text="Прочность (health):",
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
            text="Скорость стройки (buildTime):",
            font=("Arial", 15),
            text_color="#BDBDBD"
        ).pack(anchor="w", pady=(0, 5))
        
        entry_speed = ctk.CTkEntry(
            speed_frame,
            width=180,
            height=38,
            placeholder_text="1",
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
            text="Размер (size):",
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

        # Дальность луча
        range_frame = ctk.CTkFrame(properties_grid, fg_color="transparent")
        range_frame.grid(row=1, column=1, padx=10, pady=5, sticky="ew")
        
        ctk.CTkLabel(
            range_frame,
            text="Дальность луча (range):",
            font=("Arial", 15),
            text_color="#BDBDBD"
        ).pack(anchor="w", pady=(0, 5))
        
        entry_range = ctk.CTkEntry(
            range_frame,
            width=180,
            height=38,
            placeholder_text="6",
            font=("Arial", 14),
            validate="key",
            validatecommand=vcmd_int,
            fg_color="#424242",
            border_color="#555555",
            text_color="#FFFFFF",
            placeholder_text_color="#888888"
        )
        entry_range.pack(fill="x")

        # mapColor
        map_color_frame = ctk.CTkFrame(properties_grid, fg_color="transparent")
        map_color_frame.grid(row=2, column=0, padx=10, pady=5, sticky="ew")
        
        ctk.CTkLabel(
            map_color_frame,
            text="mapColor (цвет на карте):",
            font=("Arial", 15),
            text_color="#BDBDBD"
        ).pack(anchor="w", pady=(0, 5))
        
        entry_map_color = ctk.CTkButton(
            map_color_frame,
            text="#ff0000",
            width=180,
            height=38,
            font=("Arial", 14),
            command=lambda: choose_color(map_color_var, entry_map_color),
            fg_color="#ff0000",
            hover_color="#cc0000",
            text_color="#FFFFFF"
        )
        entry_map_color.pack(fill="x")

        # outlineColor
        outline_color_frame = ctk.CTkFrame(properties_grid, fg_color="transparent")
        outline_color_frame.grid(row=2, column=1, padx=10, pady=5, sticky="ew")
        
        ctk.CTkLabel(
            outline_color_frame,
            text="outlineColor (контур):",
            font=("Arial", 15),
            text_color="#BDBDBD"
        ).pack(anchor="w", pady=(0, 5))
        
        entry_outline_color = ctk.CTkButton(
            outline_color_frame,
            text="#ffffff",
            width=180,
            height=38,
            font=("Arial", 14),
            command=lambda: choose_color(outline_color_var, entry_outline_color),
            fg_color="#ffffff",
            hover_color="#cccccc",
            text_color="#000000"
        )
        entry_outline_color.pack(fill="x")

        # laserColor1
        laser_color1_frame = ctk.CTkFrame(properties_grid, fg_color="transparent")
        laser_color1_frame.grid(row=3, column=0, padx=10, pady=5, sticky="ew")
        
        ctk.CTkLabel(
            laser_color1_frame,
            text="Энергия есть (laserColor1):",
            font=("Arial", 15),
            text_color="#BDBDBD"
        ).pack(anchor="w", pady=(0, 5))
        
        entry_laser_color1 = ctk.CTkButton(
            laser_color1_frame,
            text="#ff0000",
            width=180,
            height=38,
            font=("Arial", 14),
            command=lambda: choose_color(laser_color1_var, entry_laser_color1),
            fg_color="#ff0000",
            hover_color="#cc0000",
            text_color="#FFFFFF"
        )
        entry_laser_color1.pack(fill="x")

        # laserColor2
        laser_color2_frame = ctk.CTkFrame(properties_grid, fg_color="transparent")
        laser_color2_frame.grid(row=3, column=1, padx=10, pady=5, sticky="ew")
        
        ctk.CTkLabel(
            laser_color2_frame,
            text="Энергии нет (laserColor2):",
            font=("Arial", 15),
            text_color="#BDBDBD"
        ).pack(anchor="w", pady=(0, 5))
        
        entry_laser_color2 = ctk.CTkButton(
            laser_color2_frame,
            text="#00ff00",
            width=180,
            height=38,
            font=("Arial", 14),
            command=lambda: choose_color(laser_color2_var, entry_laser_color2),
            fg_color="#00ff00",
            hover_color="#00cc00",
            text_color="#000000"
        )
        entry_laser_color2.pack(fill="x")

        # lightColor
        light_color_frame = ctk.CTkFrame(properties_grid, fg_color="transparent")
        light_color_frame.grid(row=4, column=0, padx=10, pady=5, sticky="ew")
        
        ctk.CTkLabel(
            light_color_frame,
            text="lightColor (цвет света):",
            font=("Arial", 15),
            text_color="#BDBDBD"
        ).pack(anchor="w", pady=(0, 5))
        
        entry_light_color = ctk.CTkButton(
            light_color_frame,
            text="#ffffff",
            width=180,
            height=38,
            font=("Arial", 14),
            command=lambda: choose_color(light_color_var, entry_light_color),
            fg_color="#ffffff",
            hover_color="#cccccc",
            text_color="#000000"
        )
        entry_light_color.pack(fill="x")

        # === Always Unlocked с индикатором ===
        
        always_unlocked_var = ctk.BooleanVar(value=False)
        always_unlocked_status = ctk.CTkLabel(properties_card, text="", font=("Arial", 12))

        # === КАРТОЧКА ДЛЯ ПРЕДМЕТОВ СТРОИТЕЛЬСТВА ===
        build_card = ctk.CTkFrame(
            scroll_frame,
            corner_radius=15,
            border_width=2,
            border_color="#404040",
            fg_color="#363636"
        )
        build_card.pack(fill="x", pady=(0, 20))
        
        ctk.CTkLabel(
            build_card,
            text="🔨 Предметы для строительства",
            font=("Arial", 18, "bold"),
            text_color="#4CAF50"
        ).pack(pady=(15, 10), padx=20, anchor="w")
        
        build_items_frame = ctk.CTkFrame(build_card, fg_color="transparent")
        build_items_frame.pack(fill="x", padx=20, pady=(0, 15))
        
        build_items_var = tk.StringVar(value="Выбрано: 0 предметов")
        build_items_label = ctk.CTkLabel(
            build_items_frame,
            textvariable=build_items_var,
            font=("Arial", 12),
            text_color="#9E9E9E",
            wraplength=400
        )
        build_items_label.pack(anchor="w", pady=(5, 0))
        
        ctk.CTkButton(
            build_items_frame,
            text="📋 Выбрать предметы для строительства",
            command=lambda: self.open_items_editor(build_items_var, "build"),
            height=35,
            font=("Arial", 13),
            fg_color="#2E7D32",
            hover_color="#1B5E20",
            corner_radius=6
        ).pack(anchor="w", pady=(0, 5))

        # === КАРТОЧКА ДЛЯ ИССЛЕДОВАНИЯ ===
        research_card = ctk.CTkFrame(
            scroll_frame,
            corner_radius=15,
            border_width=2,
            border_color="#404040",
            fg_color="#363636"
        )
        
        # Переменные для исследования
        selected_block_var = tk.StringVar(value="Не выбран")
        selected_block_internal_var = tk.StringVar(value="")
        selected_block_type_var = tk.StringVar(value="")
        block_icon_label = ctk.CTkLabel(properties_card, text="⚡", font=("Arial", 30))
        block_path_label = ctk.CTkLabel(properties_card, text="", font=("Arial", 10))
        research_items_var = tk.StringVar(value="Выбрано: 0 предметов")

        # ИСПОЛЬЗУЕМ НОВУЮ УНИВЕРСАЛЬНУЮ ФУНКЦИЮ
        always_unlocked_check, select_block_button, select_items_button = self.setup_research_system(
            always_unlocked_var=always_unlocked_var,
            research_card=research_card,
            always_unlocked_status=always_unlocked_status,
            build_card=build_card,
            selected_block_var=selected_block_var,
            selected_block_internal_var=selected_block_internal_var,
            selected_block_type_var=selected_block_type_var,
            block_icon_label=block_icon_label,
            block_path_label=block_path_label,
            research_items_var=research_items_var,
            on_block_selected_callback=None
        )

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

        # === Основная функция создания лучевого узла ===
        def process_beam_node():
            original_name = entry_name.get().strip()
            
            if not original_name:
                status_label.configure(
                    text="❌ Ошибка: Введите название лучевого узла!", 
                    text_color="#F44336"
                )
                return
            
            # Проверка для always_unlocked = false
            is_valid, error_msg = self.validate_research(
                always_unlocked_var=always_unlocked_var,
                research_items=self.research_items if hasattr(self, 'research_items') else [],
                selected_block_internal_var=selected_block_internal_var
            )
            
            if not is_valid:
                status_label.configure(text=error_msg, text_color="#F44336")
                return
            
            if not hasattr(self, 'build_items') or not self.build_items:
                status_label.configure(
                    text="❌ Ошибка: Выберите предметы для строительства!", 
                    text_color="#F44336"
                )
                return
            
            # Форматируем имя
            constructor_name = self.format_to_lower_camel(original_name)
            if not constructor_name:
                status_label.configure(
                    text="❌ Ошибка: Некорректное название!", 
                    text_color="#F44336"
                )
                return

            # Проверяем, существует ли уже такое имя
            if self.check_block_name_exists(original_name, PATEH_FOLDER):
                status_label.configure(
                    text=f"❌ Ошибка: Имя '{constructor_name}' уже используется!", 
                    text_color="#F44336"
                )
                return
            
            # Копируем текстуру
            size_multiplier = int(size_var.get())
            texture_copied = self.copy_block_texture(
                block_name=original_name,
                size_multiplier=size_multiplier,
                target_folder=FOLDER,
                template_names=[TEMPO_ICON]
            )
            texture_status = "✅ Текстура создана" if texture_copied else "⚠️ Текстура не создана"
            
            # Получаем значения свойств
            hp_value = entry_hp.get().strip() or "400"
            speed_raw = entry_speed.get().strip() or "1"
            range_raw = entry_range.get().strip() or "6"
            size_value = size_var.get()
            
            hp_value = str(int(float(hp_value)))
            always_unlocked_value = "true" if always_unlocked_var.get() else "false"
            
            map_color_raw = map_color_var.get()
            outline_color_raw = outline_color_var.get()
            laser_color1_raw = laser_color1_var.get()
            laser_color2_raw = laser_color2_var.get()
            light_color_raw = light_color_var.get()
            
            # Получаем кастомные предметы
            custom_items = self.get_custom_items()
            var_name = constructor_name
            
            # Формируем код для предметов строительства
            build_itemstack_code = ""
            build_items_list = []
            if hasattr(self, 'build_items') and self.build_items:
                item_counts = {}
                for item in self.build_items:
                    item_counts[item] = item_counts.get(item, 0) + 1
                
                item_parts = []
                for item_name, count in item_counts.items():
                    code_name = self.get_item_code_name(item_name, custom_items)
                    item_parts.append(f"{code_name}, {count}")
                    build_items_list.append((item_name, count))
                
                build_itemstack_code = f"\n            requirements(Category.{CATEDOR},\n                ItemStack.with({', '.join(item_parts)}));"
            
            # Формируем свойства лучевого узла
            properties = f"""    health = {hp_value};
                size = {size_value};
                buildTime = {speed_raw};
                alwaysUnlocked = {always_unlocked_value};
                buildVisibility = BuildVisibility.shown;
                range = {range_raw};
                category = Category.{CATEDOR};{build_itemstack_code}
                mapColor = Color.valueOf("{map_color_raw}");
                outlineColor = Color.valueOf("{outline_color_raw}");
                laserColor1 = Color.valueOf("{laser_color1_raw}");
                laserColor2 = Color.valueOf("{laser_color2_raw}");
                lightColor = Color.valueOf("{light_color_raw}");

                localizedName = Core.bundle.get("{var_name}.name", "OH NO");
                description = Core.bundle.get("{var_name}.description", "OH NO");"""
            
            # Пути к файлам
            mod_name_lower = self.mod_name.lower() if self.mod_name else self.mod_name
            block_registration_path = self.get_absolute_path(f"src/{mod_name_lower}/init/blocks/{FOLDER}/{NAME}.java")
            main_mod_path = Path(self.mod_folder) / "src" / mod_name_lower / f"{self.mod_name}JavaMod.java"
            
            block_registration_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Читаем или создаем файл регистрации блоков
            try:
                with open(block_registration_path, 'r', encoding='utf-8') as file:
                    content = file.read()
            except FileNotFoundError:
                content = f"""package {mod_name_lower}.init.blocks.{FOLDER};

import arc.graphics.Color;
import arc.Core;
import mindustry.type.ItemStack;
import mindustry.type.Category;
import mindustry.world.Block;
import mindustry.world.blocks.{CATEDOR}.{CATENAME};
import mindustry.world.meta.BuildVisibility;
import mindustry.content.Items;
import mindustry.Vars;
import {mod_name_lower}.init.items.ModItems;

public class {NAME} {{
    public static {CATENAME};
                                            
    public static void Load() {{
        // Регистрация блоков
    }}
}}"""
            
            node_exists = var_name in content
            tree_file_created = False
            main_file_updated = False
            
            if not node_exists:
                # Добавляем переменную блока
                if f"public static {CATENAME};" in content:
                    content = content.replace(
                        f"public static {CATENAME};",
                        f"public static {CATENAME} {var_name};"
                    )
                elif f"public static {CATENAME} " in content:
                    lines = content.split('\n')
                    for i, line in enumerate(lines):
                        if f"public static {CATENAME} " in line and var_name not in line:
                            lines[i] = line.rstrip(';') + f", {var_name};"
                            content = '\n'.join(lines)
                            break
                
                # Добавляем инициализацию блока
                load_start = content.find("public static void Load() {")
                if load_start != -1:
                    open_brace = content.find('{', load_start)
                    if open_brace != -1:
                        insert_pos = open_brace + 1
                        indent = "        "
                        node_code = f'\n{indent}{var_name} = new {CATENAME}("{constructor_name}"){{{{\n{indent}{properties}\n{indent}}}}};'
                        content = content[:insert_pos] + node_code + content[insert_pos:]
                
                # Сохраняем файл
                with open(block_registration_path, 'w', encoding='utf-8') as file:
                    file.write(content)
                
                # Обновляем главный файл мода
                try:
                    with open(main_mod_path, 'r', encoding='utf-8') as file:
                        main_content = file.read()
                    
                    # Добавляем импорт
                    import_statement = f"import {mod_name_lower}.init.blocks.{FOLDER}.{NAME};"
                    if import_statement not in main_content:
                        import_add_pos = main_content.find("//import_add")
                        if import_add_pos != -1:
                            insert_pos = import_add_pos + len("//import_add")
                            if insert_pos < len(main_content) and main_content[insert_pos] == '\n':
                                main_content = main_content[:insert_pos] + f"\n{import_statement}" + main_content[insert_pos:]
                            else:
                                main_content = main_content[:insert_pos] + f"\n{import_statement}" + main_content[insert_pos:]
                    
                    # Добавляем вызов Load
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
                    
                    main_file_updated = True
                    
                    # Создаем файл дерева технологий, если Always Unlocked = false
                    if not always_unlocked_var.get():
                        research_items_list = []
                        if hasattr(self, 'research_items') and self.research_items:
                            item_counts = {}
                            for item in self.research_items:
                                item_counts[item] = item_counts.get(item, 0) + 1
                            
                            for item_name, count in item_counts.items():
                                research_items_list.append((item_name, count))
                        
                        research_block = selected_block_internal_var.get()
                        
                        # Используем универсальную функцию
                        tree_file_created = self.create_tech_tree_file_universal(
                            block_var_name=var_name,
                            block_constructor_name=constructor_name,
                            research_block=research_block,
                            research_items=research_items_list,
                            block_type="beam_node",
                            folder_name=FOLDER,
                            class_name="BeamNodeTree"
                        )
                        
                        # ИСПОЛЬЗУЕМ НОВУЮ УНИВЕРСАЛЬНУЮ ФУНКЦИЮ для обновления главного файла
                        if tree_file_created:
                            self.update_main_mod_file_universal(
                                import_path=f"{mod_name_lower}.content.BeamNodeTree",
                                load_statement="BeamNodeTree.Load();"
                            )
                    
                    # Формируем сообщение о результате
                    status_messages = [
                        f"✅ {BL_NAME_2} '{var_name}' успешно создан!",
                        f'📝 Имя в игре: "{constructor_name}"',
                        f"{texture_status}",
                    ]
                    
                    # Добавляем информацию о Always Unlocked
                    if always_unlocked_var.get():
                        status_messages.append("🔓 Always Unlocked: ДА (доступен с самого начала)")
                    else:
                        status_messages.append("🔒 Always Unlocked: НЕТ (требуется исследование)")
                    
                    status_messages.extend([
                        f"📊 Свойства {BL_NAME}:",
                        f"  • ❤️ Здоровье: {hp_value}",
                        f"  • ⚡ Скорость стройки: {speed_raw}",
                        f"  • 📏 Размер: {size_value}",
                        f"  • 📡 Дальность луча: {range_raw}",
                    ])
                    
                    if build_items_list:
                        items_list = []
                        for item_name, count in build_items_list:
                            if item_name in custom_items:
                                items_list.append(f"ModItems.{item_name} ×{count}")
                            else:
                                display_name = item_name.replace('-', ' ').title()
                                items_list.append(f"{display_name} ×{count}")
                        
                        status_messages.append(f"  • 🔨 Стройка: {', '.join(items_list)}")
                    
                    if not always_unlocked_var.get():
                        if hasattr(self, 'research_items') and self.research_items:
                            research_list = []
                            item_counts = {}
                            for item in self.research_items:
                                item_counts[item] = item_counts.get(item, 0) + 1
                            
                            for item_name, count in item_counts.items():
                                if item_name in custom_items:
                                    research_list.append(f"ModItems.{item_name} ×{count}")
                                else:
                                    display_name = item_name.replace('-', ' ').title()
                                    research_list.append(f"{display_name} ×{count}")
                            
                            status_messages.append(f"  • 💰 Исследование: {', '.join(research_list)}")
                        
                        status_messages.append(f"  • 🎯 Блок исследования: {selected_block_var.get()}")
                        
                        if tree_file_created:
                            status_messages.append(f"  • 🌳 BeamNodeTree.java создан и добавлен в main (BeamNodeTree.Load())")
                        else:
                            status_messages.append(f"  • ⚠️ BeamNodeTree.java не создан")
                    
                    if main_file_updated:
                        status_messages.append(f"  • 📄 Главный файл мода обновлен")
                    
                    status_text = "\n".join(status_messages)
                    status_label.configure(text=status_text, text_color="#4CAF50")
                    
                except Exception as e:
                    status_label.configure(text=f"❌ Ошибка: {str(e)}", text_color="#F44336")
            else:
                status_label.configure(text=f"⚠️ {BL_NAME_2} уже существует", text_color="#FF9800")
            
            self.root.after(5000, lambda: status_label.configure(text=""))

        # === Кнопки действий ===
        buttons_frame = ctk.CTkFrame(button_frame, fg_color="transparent")
        buttons_frame.pack(pady=10)
        
        ctk.CTkButton(
            buttons_frame,
            text=f"Создать {BL_CR_NAME}",
            command=process_beam_node,
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
        
        # Инициализация переменных
        self.build_items = []
        self.research_items = []

    def create_consume_generator(self):
        """Создает или добавляет новый генератор в consume_generators/ConsumeGenerators.java"""
        
        # Константы для генератора
        PATEH_FOLDER = self.PATEH_FOLDER

        CATENAME = "ConsumeGenerator"
        CATEDOR = "power"
        TEMPO_ICON_BASE = "rtg-generator.png"
        TEMPO_ICON_TOP = "rtg-generator-top.png"
        BL_NAME_2 = "Генератор"
        BL_CR_NAME = "Генератор"
        BL_NAME = "генератора"
        ENTRY_NAME1 = "generator"
        NAME = "ConsumeGenerators"
        FOLDER = "consume_generators"
        
        # Очищаем окно
        self.clear_window()
        
        # Основной фрейм с прокруткой
        main_frame = ctk.CTkFrame(self.root, fg_color="#2b2b2b")
        main_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        scroll_frame = ctk.CTkScrollableFrame(
            main_frame,
            width=500,
            height=800,
            fg_color="#2b2b2b"
        )
        scroll_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Заголовок
        title_frame = ctk.CTkFrame(scroll_frame, fg_color="transparent")
        title_frame.pack(fill="x", pady=(0, 20))
        
        ctk.CTkLabel(
            title_frame,
            text="Создание генератора",
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
            text=f"Название {BL_NAME} (английское, можно пробел, первая буква маленькая):",
            font=("Arial", 16),
            text_color="#BDBDBD"
        ).pack(anchor="w", pady=(0, 5))
        
        entry_name = ctk.CTkEntry(
            name_frame,
            width=400,
            height=40,
            placeholder_text=f"{ENTRY_NAME1} name",
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

        def validate_energy_input(value):
            if value == "":
                return True
            if not value.isdigit():
                return False
            return int(value) <= 99999999

        vcmd_float = (self.root.register(validate_float_input), '%P')
        vcmd_int = (self.root.register(validate_int_input), '%P')
        vcmd_energy = (self.root.register(validate_energy_input), '%P')
        
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
            text=f"Свойства {BL_NAME}",
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
            text="Прочность (health):",
            font=("Arial", 15),
            text_color="#BDBDBD"
        ).pack(anchor="w", pady=(0, 5))
        
        entry_hp = ctk.CTkEntry(
            hp_frame,
            width=180,
            height=38,
            placeholder_text="500",
            font=("Arial", 14),
            validate="key",
            validatecommand=vcmd_int,
            fg_color="#424242",
            border_color="#555555",
            text_color="#FFFFFF",
            placeholder_text_color="#888888"
        )
        entry_hp.pack(fill="x")
        
        # Мощность
        power_frame = ctk.CTkFrame(properties_grid, fg_color="transparent")
        power_frame.grid(row=0, column=1, padx=10, pady=5, sticky="ew")
        
        ctk.CTkLabel(
            power_frame,
            text="Мощность (powerProduction) в секунду:",
            font=("Arial", 15),
            text_color="#BDBDBD"
        ).pack(anchor="w", pady=(0, 5))
        
        entry_power = ctk.CTkEntry(
            power_frame,
            width=180,
            height=38,
            placeholder_text="500",
            font=("Arial", 14),
            validate="key",
            validatecommand=vcmd_energy,
            fg_color="#424242",
            border_color="#555555",
            text_color="#FFFFFF",
            placeholder_text_color="#888888"
        )
        entry_power.pack(fill="x")
        
        # Размер
        size_frame = ctk.CTkFrame(properties_grid, fg_color="transparent")
        size_frame.grid(row=1, column=0, padx=10, pady=5, sticky="ew")
        
        ctk.CTkLabel(
            size_frame,
            text="Размер (size):",
            font=("Arial", 15),
            text_color="#BDBDBD"
        ).pack(anchor="w", pady=(0, 5))
        
        size_var = ctk.StringVar(value="2")
        size_combo = ctk.CTkComboBox(
            size_frame,
            values=[str(i) for i in range(1, 16)],
            variable=size_var,
            width=180,
            height=38,
            font=("Arial", 14)
        )
        size_combo.pack(fill="x")
        
        # Скорость стройки
        speed_frame = ctk.CTkFrame(properties_grid, fg_color="transparent")
        speed_frame.grid(row=1, column=1, padx=10, pady=5, sticky="ew")
        
        ctk.CTkLabel(
            speed_frame,
            text="Скорость стройки (buildTime):",
            font=("Arial", 15),
            text_color="#BDBDBD"
        ).pack(anchor="w", pady=(0, 5))
        
        entry_speed = ctk.CTkEntry(
            speed_frame,
            width=180,
            height=38,
            placeholder_text="2",
            font=("Arial", 14),
            validate="key",
            validatecommand=vcmd_float,
            fg_color="#424242",
            border_color="#555555",
            text_color="#FFFFFF",
            placeholder_text_color="#888888"
        )
        entry_speed.pack(fill="x")

        # Количество предметов
        capacity_item_frame = ctk.CTkFrame(properties_grid, fg_color="transparent")
        capacity_item_frame.grid(row=2, column=0, padx=10, pady=5, sticky="ew")
        
        ctk.CTkLabel(
            capacity_item_frame,
            text="Вместимость предметов (itemCapacity):",
            font=("Arial", 15),
            text_color="#BDBDBD"
        ).pack(anchor="w", pady=(0, 5))
        
        entry_capacity_item = ctk.CTkEntry(
            capacity_item_frame,
            width=180,
            height=38,
            placeholder_text="10",
            font=("Arial", 14),
            validate="key",
            validatecommand=vcmd_int,
            fg_color="#424242",
            border_color="#555555",
            text_color="#FFFFFF",
            placeholder_text_color="#888888"
        )
        entry_capacity_item.pack(fill="x")

        # Количество жидкости
        capacity_liquid_frame = ctk.CTkFrame(properties_grid, fg_color="transparent")
        capacity_liquid_frame.grid(row=2, column=1, padx=10, pady=5, sticky="ew")
        
        ctk.CTkLabel(
            capacity_liquid_frame,
            text="Вместимость жидкости (liquidCapacity):",
            font=("Arial", 15),
            text_color="#BDBDBD"
        ).pack(anchor="w", pady=(0, 5))
        
        entry_capacity_liquid = ctk.CTkEntry(
            capacity_liquid_frame,
            width=180,
            height=38,
            placeholder_text="10",
            font=("Arial", 14),
            validate="key",
            validatecommand=vcmd_float,
            fg_color="#424242",
            border_color="#555555",
            text_color="#FFFFFF",
            placeholder_text_color="#888888"
        )
        entry_capacity_liquid.pack(fill="x")
        
        # === Карточка для топлива ===
        fuel_card = ctk.CTkFrame(
            scroll_frame,
            corner_radius=15,
            border_width=2,
            border_color="#404040",
            fg_color="#363636"
        )
        fuel_card.pack(fill="x", pady=(0, 20))
        
        ctk.CTkLabel(
            fuel_card,
            text="🔥 Топливо для генератора",
            font=("Arial", 18, "bold"),
            text_color="#FF9800"
        ).pack(pady=(15, 10), padx=20, anchor="w")
        
        # Переменные для хранения топлива
        self.fuel_items_with_amount = []  # [(item_name, amount), ...]
        self.fuel_liquids_with_amount = []  # [(liquid_name, amount), ...]
        
        # Выбор предметов для топлива
        fuel_items_frame = ctk.CTkFrame(fuel_card, fg_color="transparent")
        fuel_items_frame.pack(fill="x", padx=20, pady=(0, 15))
        
        ctk.CTkLabel(
            fuel_items_frame,
            text="📦 Предметы для топлива (количество в секунду):",
            font=("Arial", 15, "bold"),
            text_color="#4CAF50"
        ).pack(anchor="w", pady=(0, 10))
        
        selected_fuel_items_var = tk.StringVar(value="Не выбрано")
        selected_fuel_items_label = ctk.CTkLabel(
            fuel_items_frame,
            textvariable=selected_fuel_items_var,
            font=("Arial", 12),
            text_color="#9E9E9E",
            wraplength=400
        )
        selected_fuel_items_label.pack(anchor="w", pady=(5, 0))
        
        ctk.CTkButton(
            fuel_items_frame,
            text="➕ Добавить предметное топливо",
            command=lambda: self.open_fuel_items_editor_with_amount(selected_fuel_items_var, "item"),
            height=35,
            font=("Arial", 13),
            fg_color="#2E7D32",
            hover_color="#1B5E20",
            corner_radius=6
        ).pack(anchor="w", pady=(0, 5))
        
        # Выбор жидкостей для топлива
        fuel_liquids_frame = ctk.CTkFrame(fuel_card, fg_color="transparent")
        fuel_liquids_frame.pack(fill="x", padx=20, pady=(0, 15))
        
        ctk.CTkLabel(
            fuel_liquids_frame,
            text="💧 Жидкости для топлива (количество в секунду):",
            font=("Arial", 15, "bold"),
            text_color="#2196F3"
        ).pack(anchor="w", pady=(0, 10))
        
        selected_fuel_liquids_var = tk.StringVar(value="Не выбрано")
        selected_fuel_liquids_label = ctk.CTkLabel(
            fuel_liquids_frame,
            textvariable=selected_fuel_liquids_var,
            font=("Arial", 12),
            text_color="#9E9E9E",
            wraplength=400
        )
        selected_fuel_liquids_label.pack(anchor="w", pady=(5, 0))
        
        ctk.CTkButton(
            fuel_liquids_frame,
            text="➕ Добавить жидкое топливо",
            command=lambda: self.open_fuel_items_editor_with_amount(selected_fuel_liquids_var, "liquid"),
            height=35,
            font=("Arial", 13),
            fg_color="#2196F3",
            hover_color="#1976D2",
            corner_radius=6
        ).pack(anchor="w", pady=(0, 5))

        # === Always Unlocked с индикатором ===
        
        always_unlocked_var = ctk.BooleanVar(value=False)
        always_unlocked_status = ctk.CTkLabel(properties_card, text="", font=("Arial", 12))

        # === КАРТОЧКА ДЛЯ ПРЕДМЕТОВ СТРОИТЕЛЬСТВА ===
        build_card = ctk.CTkFrame(
            scroll_frame,
            corner_radius=15,
            border_width=2,
            border_color="#404040",
            fg_color="#363636"
        )
        build_card.pack(fill="x", pady=(0, 20))
        
        ctk.CTkLabel(
            build_card,
            text="🔨 Предметы для строительства",
            font=("Arial", 18, "bold"),
            text_color="#4CAF50"
        ).pack(pady=(15, 10), padx=20, anchor="w")
        
        build_items_frame = ctk.CTkFrame(build_card, fg_color="transparent")
        build_items_frame.pack(fill="x", padx=20, pady=(0, 15))
        
        build_items_var = tk.StringVar(value="Выбрано: 0 предметов")
        build_items_label = ctk.CTkLabel(
            build_items_frame,
            textvariable=build_items_var,
            font=("Arial", 12),
            text_color="#9E9E9E",
            wraplength=400
        )
        build_items_label.pack(anchor="w", pady=(5, 0))
        
        ctk.CTkButton(
            build_items_frame,
            text="📋 Выбрать предметы для строительства",
            command=lambda: self.open_items_editor(build_items_var, "build"),
            height=35,
            font=("Arial", 13),
            fg_color="#2E7D32",
            hover_color="#1B5E20",
            corner_radius=6
        ).pack(anchor="w", pady=(0, 5))

        # === КАРТОЧКА ДЛЯ ИССЛЕДОВАНИЯ ===
        research_card = ctk.CTkFrame(
            scroll_frame,
            corner_radius=15,
            border_width=2,
            border_color="#404040",
            fg_color="#363636"
        )
        
        # Переменные для исследования
        selected_block_var = tk.StringVar(value="Не выбран")
        selected_block_internal_var = tk.StringVar(value="")
        selected_block_type_var = tk.StringVar(value="")
        block_icon_label = ctk.CTkLabel(properties_card, text="🔥", font=("Arial", 30))
        block_path_label = ctk.CTkLabel(properties_card, text="", font=("Arial", 10))
        research_items_var = tk.StringVar(value="Выбрано: 0 предметов")

        # ИСПОЛЬЗУЕМ НОВУЮ УНИВЕРСАЛЬНУЮ ФУНКЦИЮ
        always_unlocked_check, select_block_button, select_items_button = self.setup_research_system(
            always_unlocked_var=always_unlocked_var,
            research_card=research_card,
            always_unlocked_status=always_unlocked_status,
            build_card=build_card,
            selected_block_var=selected_block_var,
            selected_block_internal_var=selected_block_internal_var,
            selected_block_type_var=selected_block_type_var,
            block_icon_label=block_icon_label,
            block_path_label=block_path_label,
            research_items_var=research_items_var,
            on_block_selected_callback=None
        )

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

        # === Основная функция создания генератора ===
        def process_generator():
            original_name = entry_name.get().strip()
            
            if not original_name:
                status_label.configure(
                    text="❌ Ошибка: Введите название генератора!",
                    text_color="#F44336"
                )
                return
            
            # Проверка для always_unlocked = false
            is_valid, error_msg = self.validate_research(
                always_unlocked_var=always_unlocked_var,
                research_items=self.research_items if hasattr(self, 'research_items') else [],
                selected_block_internal_var=selected_block_internal_var
            )
            
            if not is_valid:
                status_label.configure(text=error_msg, text_color="#F44336")
                return
            
            if not hasattr(self, 'build_items') or not self.build_items:
                status_label.configure(
                    text="❌ Ошибка: Выберите предметы для строительства!", 
                    text_color="#F44336"
                )
                return
            
            # Проверяем, что выбрано хотя бы одно топливо
            if (not hasattr(self, 'fuel_items_with_amount') or not self.fuel_items_with_amount) and \
            (not hasattr(self, 'fuel_liquids_with_amount') or not self.fuel_liquids_with_amount):
                status_label.configure(
                    text="❌ Ошибка: Выберите хотя бы один вид топлива (предметы или жидкости)!", 
                    text_color="#F44336"
                )
                return
            
            # Форматируем имя
            constructor_name = self.format_to_lower_camel(original_name)
            if not constructor_name:
                status_label.configure(
                    text="❌ Ошибка: Некорректное название!",
                    text_color="#F44336"
                )
                return

            # Проверяем, существует ли уже такое имя
            if self.check_block_name_exists(original_name, PATEH_FOLDER):
                status_label.configure(
                    text=f"❌ Ошибка: Имя '{constructor_name}' уже используется!", 
                    text_color="#F44336"
                )
                return
            
            # Копируем текстуры (основная и верхняя)
            size_multiplier = int(size_var.get())
            texture_configs = [
                {"template": TEMPO_ICON_BASE, "suffix": ""},
                {"template": TEMPO_ICON_TOP, "suffix": "-top"},
            ]
            
            texture_copied = self.copy_block_textures_multi(
                block_name=original_name,
                size_multiplier=size_multiplier,
                target_folder=FOLDER,
                texture_configs=texture_configs
            )
            texture_status = "✅ Текстуры созданы" if texture_copied else "⚠️ Текстуры не созданы"
            
            # Получаем значения свойств
            hp_value = entry_hp.get().strip() or "500"
            power_raw = entry_power.get().strip() or "500"
            speed_raw = entry_speed.get().strip() or "2"
            capacity_item_raw = entry_capacity_item.get().strip() or "10"
            capacity_liquid_raw = entry_capacity_liquid.get().strip() or "10"
            size_value = size_var.get()
            
            # Делим мощность на 60
            try:
                power_in_game = float(power_raw) / 60.0
                power_in_game_str = f"{power_in_game:.4f}f"
            except:
                power_in_game_str = "8.3333f"
            
            hp_value = str(int(float(hp_value)))
            always_unlocked_value = "true" if always_unlocked_var.get() else "false"
            
            # Получаем кастомные предметы и жидкости
            custom_items = self.get_custom_items()
            custom_liquids = self.get_custom_liquids()
            var_name = constructor_name
            
            # Формируем код для предметов строительства
            build_itemstack_code = ""
            build_items_list = []
            if hasattr(self, 'build_items') and self.build_items:
                item_counts = {}
                for item in self.build_items:
                    item_counts[item] = item_counts.get(item, 0) + 1
                
                item_parts = []
                for item_name, count in item_counts.items():
                    code_name = self.get_item_code_name(item_name, custom_items)
                    item_parts.append(f"{code_name}, {count}")
                    build_items_list.append((item_name, count))
                
                build_itemstack_code = f"\n            requirements(Category.{CATEDOR},\n                ItemStack.with({', '.join(item_parts)}));"
            
            # Формируем код для потребления топлива
            consume_code = ""
            
            # Предметное топливо
            if hasattr(self, 'fuel_items_with_amount') and self.fuel_items_with_amount:
                item_consume_parts = []
                for item_name, amount in self.fuel_items_with_amount:
                    code_name = self.get_item_code_name(item_name, custom_items)
                    consumption_rate = float(amount) / 60.0
                    item_consume_parts.append(f"\n            consumeItem({code_name}, {consumption_rate:.4f}f)")
                
                if item_consume_parts:
                    consume_code += ''.join(item_consume_parts)
            
            # Жидкое топливо
            if hasattr(self, 'fuel_liquids_with_amount') and self.fuel_liquids_with_amount:
                liquid_consume_parts = []
                for liquid_name, amount in self.fuel_liquids_with_amount:
                    code_name = self.get_liquid_code_name(liquid_name, custom_liquids)
                    consumption_rate = float(amount) / 60.0
                    liquid_consume_parts.append(f"{code_name}, {consumption_rate:.4f}f")
                
                if liquid_consume_parts:
                    consume_code += f"\n            consumeLiquids(LiquidStack.with({', '.join(liquid_consume_parts)}));"
            
            # Формируем свойства генератора
            properties = f"""    health = {hp_value};
                size = {size_value};
                buildTime = {speed_raw};
                alwaysUnlocked = {always_unlocked_value};
                buildVisibility = BuildVisibility.shown;
                category = Category.{CATEDOR};
                powerProduction = {power_in_game_str}; // {power_raw}/сек деленное на 60
                liquidCapacity = {capacity_liquid_raw}f;
                itemCapacity = {capacity_item_raw};{build_itemstack_code}{consume_code}

                localizedName = Core.bundle.get("{var_name}.name", "OH NO");
                description = Core.bundle.get("{var_name}.description", "OH NO");"""
            
            # Пути к файлам
            mod_name_lower = self.mod_name.lower() if self.mod_name else self.mod_name
            block_registration_path = self.get_absolute_path(f"src/{mod_name_lower}/init/blocks/{FOLDER}/{NAME}.java")
            main_mod_path = Path(self.mod_folder) / "src" / mod_name_lower / f"{self.mod_name}JavaMod.java"
            
            block_registration_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Читаем или создаем файл регистрации блоков
            try:
                with open(block_registration_path, 'r', encoding='utf-8') as file:
                    content = file.read()
            except FileNotFoundError:
                content = f"""package {mod_name_lower}.init.blocks.{FOLDER};

import arc.graphics.Color;
import arc.Core;
import mindustry.type.ItemStack;
import mindustry.type.Category;
import mindustry.type.LiquidStack;
import mindustry.content.Liquids;
import mindustry.world.Block;
import mindustry.world.blocks.power.{CATENAME};
import mindustry.world.meta.BuildVisibility;
import mindustry.content.Items;
import mindustry.Vars;
import {mod_name_lower}.init.items.ModItems;

public class {NAME} {{
    public static {CATENAME};
                                            
    public static void Load() {{
        // Регистрация блоков
    }}
}}"""
            
            generator_exists = var_name in content
            tree_file_created = False
            main_file_updated = False
            
            if not generator_exists:
                # Добавляем переменную блока
                if f"public static {CATENAME};" in content:
                    content = content.replace(
                        f"public static {CATENAME};",
                        f"public static {CATENAME} {var_name};"
                    )
                elif f"public static {CATENAME} " in content:
                    lines = content.split('\n')
                    for i, line in enumerate(lines):
                        if f"public static {CATENAME} " in line and var_name not in line:
                            lines[i] = line.rstrip(';') + f", {var_name};"
                            content = '\n'.join(lines)
                            break
                
                # Добавляем инициализацию блока
                load_start = content.find("public static void Load() {")
                if load_start != -1:
                    open_brace = content.find('{', load_start)
                    if open_brace != -1:
                        insert_pos = open_brace + 1
                        indent = "        "
                        generator_code = f'\n{indent}{var_name} = new {CATENAME}("{constructor_name}"){{{{\n{indent}{properties}\n{indent}}}}};'
                        content = content[:insert_pos] + generator_code + content[insert_pos:]
                
                # Сохраняем файл
                with open(block_registration_path, 'w', encoding='utf-8') as file:
                    file.write(content)
                
                # Обновляем главный файл мода
                try:
                    with open(main_mod_path, 'r', encoding='utf-8') as file:
                        main_content = file.read()
                    
                    # Добавляем импорт
                    import_statement = f"import {mod_name_lower}.init.blocks.{FOLDER}.{NAME};"
                    if import_statement not in main_content:
                        import_add_pos = main_content.find("//import_add")
                        if import_add_pos != -1:
                            insert_pos = import_add_pos + len("//import_add")
                            if insert_pos < len(main_content) and main_content[insert_pos] == '\n':
                                main_content = main_content[:insert_pos] + f"\n{import_statement}" + main_content[insert_pos:]
                            else:
                                main_content = main_content[:insert_pos] + f"\n{import_statement}" + main_content[insert_pos:]
                    
                    # Добавляем вызов Load
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
                    
                    main_file_updated = True
                    
                    # Создаем файл дерева технологий, если Always Unlocked = false
                    if not always_unlocked_var.get():
                        research_items_list = []
                        if hasattr(self, 'research_items') and self.research_items:
                            item_counts = {}
                            for item in self.research_items:
                                item_counts[item] = item_counts.get(item, 0) + 1
                            
                            for item_name, count in item_counts.items():
                                research_items_list.append((item_name, count))
                        
                        research_block = selected_block_internal_var.get()
                        
                        # Используем универсальную функцию
                        tree_file_created = self.create_tech_tree_file_universal(
                            block_var_name=var_name,
                            block_constructor_name=constructor_name,
                            research_block=research_block,
                            research_items=research_items_list,
                            block_type="generator",
                            folder_name=FOLDER,
                            class_name="ConsumeGeneratorTree"
                        )
                        
                        # ИСПОЛЬЗУЕМ НОВУЮ УНИВЕРСАЛЬНУЮ ФУНКЦИЮ для обновления главного файла
                        if tree_file_created:
                            self.update_main_mod_file_universal(
                                import_path=f"{mod_name_lower}.content.ConsumeGeneratorTree",
                                load_statement="ConsumeGeneratorTree.Load();"
                            )
                    
                    # Формируем сообщение о результате
                    status_messages = [
                        f"✅ {BL_NAME_2} '{var_name}' успешно создан!",
                        f'📝 Имя в игре: "{constructor_name}"',
                        f"{texture_status}",
                    ]
                    
                    # Добавляем информацию о Always Unlocked
                    if always_unlocked_var.get():
                        status_messages.append("🔓 Always Unlocked: ДА (доступен с самого начала)")
                    else:
                        status_messages.append("🔒 Always Unlocked: НЕТ (требуется исследование)")
                    
                    status_messages.extend([
                        f"📊 Свойства {BL_NAME}:",
                        f"  • ❤️ Здоровье: {hp_value}",
                        f"  • ⚡ Мощность: {power_raw}/сек ({power_in_game_str} в коде)",
                        f"  • ⚡ Скорость стройки: {speed_raw}",
                        f"  • 📏 Размер: {size_value}",
                        f"  • 📦 Вместимость предметов: {capacity_item_raw}",
                        f"  • 💧 Вместимость жидкости: {capacity_liquid_raw}",
                    ])
                    
                    if build_items_list:
                        items_list = []
                        for item_name, count in build_items_list:
                            if item_name in custom_items:
                                items_list.append(f"ModItems.{item_name} ×{count}")
                            else:
                                display_name = item_name.replace('-', ' ').title()
                                items_list.append(f"{display_name} ×{count}")
                        
                        status_messages.append(f"  • 🔨 Стройка: {', '.join(items_list)}")
                    
                    if hasattr(self, 'fuel_items_with_amount') and self.fuel_items_with_amount:
                        fuel_list = []
                        for item_name, amount in self.fuel_items_with_amount:
                            if item_name in custom_items:
                                fuel_list.append(f"ModItems.{item_name} ×{amount}/сек")
                            else:
                                display_name = item_name.replace('-', ' ').title()
                                fuel_list.append(f"{display_name} ×{amount}/сек")
                        
                        if fuel_list:
                            status_messages.append(f"  • 🔥 Предметное топливо: {', '.join(fuel_list)}")
                    
                    if hasattr(self, 'fuel_liquids_with_amount') and self.fuel_liquids_with_amount:
                        liquid_list = []
                        for liquid_name, amount in self.fuel_liquids_with_amount:
                            if liquid_name in custom_liquids:
                                liquid_list.append(f"ModLiquids.{liquid_name} ×{amount}/сек")
                            else:
                                display_name = liquid_name.replace('-', ' ').title()
                                liquid_list.append(f"{display_name} ×{amount}/сек")
                        
                        if liquid_list:
                            status_messages.append(f"  • 💧 Жидкое топливо: {', '.join(liquid_list)}")
                    
                    if not always_unlocked_var.get():
                        if hasattr(self, 'research_items') and self.research_items:
                            research_list = []
                            item_counts = {}
                            for item in self.research_items:
                                item_counts[item] = item_counts.get(item, 0) + 1
                            
                            for item_name, count in item_counts.items():
                                if item_name in custom_items:
                                    research_list.append(f"ModItems.{item_name} ×{count}")
                                else:
                                    display_name = item_name.replace('-', ' ').title()
                                    research_list.append(f"{display_name} ×{count}")
                            
                            status_messages.append(f"  • 💰 Исследование: {', '.join(research_list)}")
                        
                        status_messages.append(f"  • 🎯 Блок исследования: {selected_block_var.get()}")
                        
                        if tree_file_created:
                            status_messages.append(f"  • 🌳 ConsumeGeneratorTree.java создан и добавлен в main (ConsumeGeneratorTree.Load())")
                        else:
                            status_messages.append(f"  • ⚠️ ConsumeGeneratorTree.java не создан")
                    
                    if main_file_updated:
                        status_messages.append(f"  • 📄 Главный файл мода обновлен")
                    
                    status_text = "\n".join(status_messages)
                    status_label.configure(text=status_text, text_color="#4CAF50")
                    
                except Exception as e:
                    status_label.configure(text=f"❌ Ошибка: {str(e)}", text_color="#F44336")
            else:
                status_label.configure(text=f"⚠️ {BL_NAME_2} уже существует", text_color="#FF9800")
            
            self.root.after(5000, lambda: status_label.configure(text=""))

        # === Кнопки действий ===
        buttons_frame = ctk.CTkFrame(button_frame, fg_color="transparent")
        buttons_frame.pack(pady=10)
        
        ctk.CTkButton(
            buttons_frame,
            text=f"Создать {BL_CR_NAME}",
            command=process_generator,
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
        
        # Инициализация переменных
        self.build_items = []
        self.research_items = []
        self.fuel_items_with_amount = []
        self.fuel_liquids_with_amount = []

    def create_generic_crafter(self):
        """Создает или добавляет новый завод в generic_crafter/GenericCrafters.java"""
        
        # Константы для завода
        PATEH_FOLDER = self.PATEH_FOLDER

        CATENAME = "GenericCrafter"
        CATEDOR = "crafting"
        TEMPO_ICON_BASE = "kiln.png"
        TEMPO_ICON_TOP = "kiln-top.png"
        BL_NAME_2 = "Завод"
        BL_CR_NAME = "Завод"
        BL_NAME = "завода"
        ENTRY_NAME1 = "crafter"
        NAME = "GenericCrafters"
        FOLDER = "generic_crafter"
        
        # Очищаем окно
        self.clear_window()
        
        # Основной фрейм с прокруткой
        main_frame = ctk.CTkFrame(self.root, fg_color="#2b2b2b")
        main_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        scroll_frame = ctk.CTkScrollableFrame(
            main_frame,
            width=500,
            height=850,
            fg_color="#2b2b2b"
        )
        scroll_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Заголовок
        title_frame = ctk.CTkFrame(scroll_frame, fg_color="transparent")
        title_frame.pack(fill="x", pady=(0, 20))
        
        ctk.CTkLabel(
            title_frame,
            text="Создание завода",
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
            text=f"Название {BL_NAME} (английское, можно пробел, первая буква маленькая):",
            font=("Arial", 16),
            text_color="#BDBDBD"
        ).pack(anchor="w", pady=(0, 5))
        
        entry_name = ctk.CTkEntry(
            name_frame,
            width=400,
            height=40,
            placeholder_text=f"{ENTRY_NAME1} name",
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
            text=f"Свойства {BL_NAME}",
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
            text="Прочность (health):",
            font=("Arial", 15),
            text_color="#BDBDBD"
        ).pack(anchor="w", pady=(0, 5))
        
        entry_hp = ctk.CTkEntry(
            hp_frame,
            width=180,
            height=38,
            placeholder_text="500",
            font=("Arial", 14),
            validate="key",
            validatecommand=vcmd_int,
            fg_color="#424242",
            border_color="#555555",
            text_color="#FFFFFF",
            placeholder_text_color="#888888"
        )
        entry_hp.pack(fill="x")
        
        # Время крафта
        craft_time_frame = ctk.CTkFrame(properties_grid, fg_color="transparent")
        craft_time_frame.grid(row=0, column=1, padx=10, pady=5, sticky="ew")
        
        ctk.CTkLabel(
            craft_time_frame,
            text="Время крафта (craftTime):",
            font=("Arial", 15),
            text_color="#BDBDBD"
        ).pack(anchor="w", pady=(0, 5))
        
        entry_craft_time = ctk.CTkEntry(
            craft_time_frame,
            width=180,
            height=38,
            placeholder_text="60",
            font=("Arial", 14),
            validate="key",
            validatecommand=vcmd_float,
            fg_color="#424242",
            border_color="#555555",
            text_color="#FFFFFF",
            placeholder_text_color="#888888"
        )
        entry_craft_time.pack(fill="x")
        
        # Размер
        size_frame = ctk.CTkFrame(properties_grid, fg_color="transparent")
        size_frame.grid(row=1, column=0, padx=10, pady=5, sticky="ew")
        
        ctk.CTkLabel(
            size_frame,
            text="Размер (size):",
            font=("Arial", 15),
            text_color="#BDBDBD"
        ).pack(anchor="w", pady=(0, 5))
        
        size_var = ctk.StringVar(value="2")
        size_combo = ctk.CTkComboBox(
            size_frame,
            values=[str(i) for i in range(1, 16)],
            variable=size_var,
            width=180,
            height=38,
            font=("Arial", 14)
        )
        size_combo.pack(fill="x")
        
        # Скорость стройки
        speed_frame = ctk.CTkFrame(properties_grid, fg_color="transparent")
        speed_frame.grid(row=1, column=1, padx=10, pady=5, sticky="ew")
        
        ctk.CTkLabel(
            speed_frame,
            text="Скорость стройки (buildTime):",
            font=("Arial", 15),
            text_color="#BDBDBD"
        ).pack(anchor="w", pady=(0, 5))
        
        entry_speed = ctk.CTkEntry(
            speed_frame,
            width=180,
            height=38,
            placeholder_text="2",
            font=("Arial", 14),
            validate="key",
            validatecommand=vcmd_float,
            fg_color="#424242",
            border_color="#555555",
            text_color="#FFFFFF",
            placeholder_text_color="#888888"
        )
        entry_speed.pack(fill="x")

        # Количество предметов
        capacity_item_frame = ctk.CTkFrame(properties_grid, fg_color="transparent")
        capacity_item_frame.grid(row=2, column=0, padx=10, pady=5, sticky="ew")
        
        ctk.CTkLabel(
            capacity_item_frame,
            text="Вместимость предметов (itemCapacity):",
            font=("Arial", 15),
            text_color="#BDBDBD"
        ).pack(anchor="w", pady=(0, 5))
        
        entry_capacity_item = ctk.CTkEntry(
            capacity_item_frame,
            width=180,
            height=38,
            placeholder_text="10",
            font=("Arial", 14),
            validate="key",
            validatecommand=vcmd_int,
            fg_color="#424242",
            border_color="#555555",
            text_color="#FFFFFF",
            placeholder_text_color="#888888"
        )
        entry_capacity_item.pack(fill="x")

        # Количество жидкости
        capacity_liquid_frame = ctk.CTkFrame(properties_grid, fg_color="transparent")
        capacity_liquid_frame.grid(row=2, column=1, padx=10, pady=5, sticky="ew")
        
        ctk.CTkLabel(
            capacity_liquid_frame,
            text="Вместимость жидкости (liquidCapacity):",
            font=("Arial", 15),
            text_color="#BDBDBD"
        ).pack(anchor="w", pady=(0, 5))
        
        entry_capacity_liquid = ctk.CTkEntry(
            capacity_liquid_frame,
            width=180,
            height=38,
            placeholder_text="10",
            font=("Arial", 14),
            validate="key",
            validatecommand=vcmd_float,
            fg_color="#424242",
            border_color="#555555",
            text_color="#FFFFFF",
            placeholder_text_color="#888888"
        )
        entry_capacity_liquid.pack(fill="x")
        
        # === КАРТОЧКА ДЛЯ ПОТРЕБЛЕНИЯ ===
        consume_card = ctk.CTkFrame(
            scroll_frame,
            corner_radius=15,
            border_width=2,
            border_color="#404040",
            fg_color="#363636"
        )
        consume_card.pack(fill="x", pady=(0, 20))
        
        ctk.CTkLabel(
            consume_card,
            text="⬇️ Потребление для завода (за крафт)",
            font=("Arial", 18, "bold"),
            text_color="#FF9800"
        ).pack(pady=(15, 10), padx=20, anchor="w")
        
        # Переменные для хранения потребляемых предметов
        self.consume_items_with_amount = []  # [(item_name, amount), ...]
        self.consume_liquids_with_amount = []  # [(liquid_name, amount), ...]
        self.consume_power_needed = ctk.BooleanVar(value=False)
        self.consume_power_amount = ctk.StringVar(value="1.0")
        
        # Потребление предметов
        consume_items_frame = ctk.CTkFrame(consume_card, fg_color="transparent")
        consume_items_frame.pack(fill="x", padx=20, pady=(0, 15))
        
        ctk.CTkLabel(
            consume_items_frame,
            text="📦 Предметы для потребления (количество за крафт):",
            font=("Arial", 15, "bold"),
            text_color="#4CAF50"
        ).pack(anchor="w", pady=(0, 10))
        
        selected_consume_items_var = tk.StringVar(value="Не выбрано")
        selected_consume_items_label = ctk.CTkLabel(
            consume_items_frame,
            textvariable=selected_consume_items_var,
            font=("Arial", 12),
            text_color="#9E9E9E",
            wraplength=400
        )
        selected_consume_items_label.pack(anchor="w", pady=(5, 0))
        
        ctk.CTkButton(
            consume_items_frame,
            text="➕ Добавить предметы на вход",
            command=lambda: self.open_editor_with_target(selected_consume_items_var, "item", "consume_items"),
            height=35,
            font=("Arial", 13),
            fg_color="#2E7D32",
            hover_color="#1B5E20",
            corner_radius=6
        ).pack(anchor="w", pady=(0, 5))
        
        # Потребление жидкостей
        consume_liquids_frame = ctk.CTkFrame(consume_card, fg_color="transparent")
        consume_liquids_frame.pack(fill="x", padx=20, pady=(0, 15))
        
        ctk.CTkLabel(
            consume_liquids_frame,
            text="💧 Жидкости для потребления (количество за крафт):",
            font=("Arial", 15, "bold"),
            text_color="#2196F3"
        ).pack(anchor="w", pady=(0, 10))
        
        selected_consume_liquids_var = tk.StringVar(value="Не выбрано")
        selected_consume_liquids_label = ctk.CTkLabel(
            consume_liquids_frame,
            textvariable=selected_consume_liquids_var,
            font=("Arial", 12),
            text_color="#9E9E9E",
            wraplength=400
        )
        selected_consume_liquids_label.pack(anchor="w", pady=(5, 0))
        
        ctk.CTkButton(
            consume_liquids_frame,
            text="➕ Добавить жидкости на вход",
            command=lambda: self.open_editor_with_target(selected_consume_liquids_var, "liquid", "consume_liquids"),
            height=35,
            font=("Arial", 13),
            fg_color="#2196F3",
            hover_color="#1976D2",
            corner_radius=6
        ).pack(anchor="w", pady=(0, 5))
        
        # Потребление энергии
        consume_power_frame = ctk.CTkFrame(consume_card, fg_color="transparent")
        consume_power_frame.pack(fill="x", padx=20, pady=(0, 15))
        
        power_check = ctk.CTkCheckBox(
            consume_power_frame,
            text="⚡ Потребляет энергию",
            variable=self.consume_power_needed,
            font=("Arial", 15, "bold"),
            text_color="#FFD700",
            fg_color="#FFD700",
            hover_color="#DAA520"
        )
        power_check.pack(anchor="w", pady=(0, 10))
        
        power_amount_frame = ctk.CTkFrame(consume_power_frame, fg_color="transparent")
        power_amount_frame.pack(fill="x", pady=(0, 5))
        
        ctk.CTkLabel(
            power_amount_frame,
            text="Количество энергии в секунду:",
            font=("Arial", 14),
            text_color="#BDBDBD"
        ).pack(anchor="w", pady=(0, 5))
        
        entry_power_amount = ctk.CTkEntry(
            power_amount_frame,
            width=180,
            height=35,
            textvariable=self.consume_power_amount,
            font=("Arial", 14),
            fg_color="#424242",
            border_color="#555555"
        )
        entry_power_amount.pack(anchor="w")
        
        # === КАРТОЧКА ДЛЯ РЕЗУЛЬТАТА ===
        output_card = ctk.CTkFrame(
            scroll_frame,
            corner_radius=15,
            border_width=2,
            border_color="#404040",
            fg_color="#363636"
        )
        output_card.pack(fill="x", pady=(0, 20))
        
        ctk.CTkLabel(
            output_card,
            text="⬆️ Результат крафта (за крафт)",
            font=("Arial", 18, "bold"),
            text_color="#4CAF50"
        ).pack(pady=(15, 10), padx=20, anchor="w")
        
        # Переменные для хранения результатов
        self.output_items_with_amount = []  # [(item_name, amount), ...]
        self.output_liquids_with_amount = []  # [(liquid_name, amount), ...]
        
        # Результат предметы
        output_items_frame = ctk.CTkFrame(output_card, fg_color="transparent")
        output_items_frame.pack(fill="x", padx=20, pady=(0, 15))
        
        ctk.CTkLabel(
            output_items_frame,
            text="📦 Предметы на выходе (количество за крафт):",
            font=("Arial", 15, "bold"),
            text_color="#4CAF50"
        ).pack(anchor="w", pady=(0, 10))
        
        selected_output_items_var = tk.StringVar(value="Не выбрано")
        selected_output_items_label = ctk.CTkLabel(
            output_items_frame,
            textvariable=selected_output_items_var,
            font=("Arial", 12),
            text_color="#9E9E9E",
            wraplength=400
        )
        selected_output_items_label.pack(anchor="w", pady=(5, 0))
        
        ctk.CTkButton(
            output_items_frame,
            text="➕ Добавить предметы на выход",
            command=lambda: self.open_editor_with_target(selected_output_items_var, "item", "output_items"),
            height=35,
            font=("Arial", 13),
            fg_color="#2E7D32",
            hover_color="#1B5E20",
            corner_radius=6
        ).pack(anchor="w", pady=(0, 5))
        
        # Результат жидкости
        output_liquids_frame = ctk.CTkFrame(output_card, fg_color="transparent")
        output_liquids_frame.pack(fill="x", padx=20, pady=(0, 15))
        
        ctk.CTkLabel(
            output_liquids_frame,
            text="💧 Жидкости на выходе (количество за крафт):",
            font=("Arial", 15, "bold"),
            text_color="#2196F3"
        ).pack(anchor="w", pady=(0, 10))
        
        selected_output_liquids_var = tk.StringVar(value="Не выбрано")
        selected_output_liquids_label = ctk.CTkLabel(
            output_liquids_frame,
            textvariable=selected_output_liquids_var,
            font=("Arial", 12),
            text_color="#9E9E9E",
            wraplength=400
        )
        selected_output_liquids_label.pack(anchor="w", pady=(5, 0))
        
        ctk.CTkButton(
            output_liquids_frame,
            text="➕ Добавить жидкости на выход",
            command=lambda: self.open_editor_with_target(selected_output_liquids_var, "liquid", "output_liquids"),
            height=35,
            font=("Arial", 13),
            fg_color="#2196F3",
            hover_color="#1976D2",
            corner_radius=6
        ).pack(anchor="w", pady=(0, 5))
        
        # === Always Unlocked с индикатором ===
        
        always_unlocked_var = ctk.BooleanVar(value=False)
        always_unlocked_status = ctk.CTkLabel(properties_card, text="", font=("Arial", 12))

        # === КАРТОЧКА ДЛЯ ПРЕДМЕТОВ СТРОИТЕЛЬСТВА ===
        build_card = ctk.CTkFrame(
            scroll_frame,
            corner_radius=15,
            border_width=2,
            border_color="#404040",
            fg_color="#363636"
        )
        build_card.pack(fill="x", pady=(0, 20))
        
        ctk.CTkLabel(
            build_card,
            text="🔨 Предметы для строительства",
            font=("Arial", 18, "bold"),
            text_color="#4CAF50"
        ).pack(pady=(15, 10), padx=20, anchor="w")
        
        build_items_frame = ctk.CTkFrame(build_card, fg_color="transparent")
        build_items_frame.pack(fill="x", padx=20, pady=(0, 15))
        
        build_items_var = tk.StringVar(value="Выбрано: 0 предметов")
        build_items_label = ctk.CTkLabel(
            build_items_frame,
            textvariable=build_items_var,
            font=("Arial", 12),
            text_color="#9E9E9E",
            wraplength=400
        )
        build_items_label.pack(anchor="w", pady=(5, 0))
        
        ctk.CTkButton(
            build_items_frame,
            text="📋 Выбрать предметы для строительства",
            command=lambda: self.open_items_editor(build_items_var, "build"),
            height=35,
            font=("Arial", 13),
            fg_color="#2E7D32",
            hover_color="#1B5E20",
            corner_radius=6
        ).pack(anchor="w", pady=(0, 5))

        # === КАРТОЧКА ДЛЯ ИССЛЕДОВАНИЯ ===
        research_card = ctk.CTkFrame(
            scroll_frame,
            corner_radius=15,
            border_width=2,
            border_color="#404040",
            fg_color="#363636"
        )
        
        # Переменные для исследования
        selected_block_var = tk.StringVar(value="Не выбран")
        selected_block_internal_var = tk.StringVar(value="")
        selected_block_type_var = tk.StringVar(value="")
        block_icon_label = ctk.CTkLabel(properties_card, text="🏭", font=("Arial", 30))
        block_path_label = ctk.CTkLabel(properties_card, text="", font=("Arial", 10))
        research_items_var = tk.StringVar(value="Выбрано: 0 предметов")

        # ИСПОЛЬЗУЕМ НОВУЮ УНИВЕРСАЛЬНУЮ ФУНКЦИЮ
        always_unlocked_check, select_block_button, select_items_button = self.setup_research_system(
            always_unlocked_var=always_unlocked_var,
            research_card=research_card,
            always_unlocked_status=always_unlocked_status,
            build_card=build_card,
            selected_block_var=selected_block_var,
            selected_block_internal_var=selected_block_internal_var,
            selected_block_type_var=selected_block_type_var,
            block_icon_label=block_icon_label,
            block_path_label=block_path_label,
            research_items_var=research_items_var,
            on_block_selected_callback=None
        )

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

        # === Основная функция создания завода ===
        def process_crafter():
            original_name = entry_name.get().strip()
            
            if not original_name:
                status_label.configure(
                    text="❌ Ошибка: Введите название завода!",
                    text_color="#F44336"
                )
                return
            
            # Проверка для always_unlocked = false
            is_valid, error_msg = self.validate_research(
                always_unlocked_var=always_unlocked_var,
                research_items=self.research_items if hasattr(self, 'research_items') else [],
                selected_block_internal_var=selected_block_internal_var
            )
            
            if not is_valid:
                status_label.configure(text=error_msg, text_color="#F44336")
                return
            
            if not hasattr(self, 'build_items') or not self.build_items:
                status_label.configure(
                    text="❌ Ошибка: Выберите предметы для строительства!", 
                    text_color="#F44336"
                )
                return
            
            # Проверка на наличие потребления
            if (not hasattr(self, 'consume_items_with_amount') or not self.consume_items_with_amount) and \
            (not hasattr(self, 'consume_liquids_with_amount') or not self.consume_liquids_with_amount) and \
            (not self.consume_power_needed.get()):
                status_label.configure(
                    text="❌ Ошибка: Добавьте хотя бы один элемент потребления!", 
                    text_color="#F44336"
                )
                return
            
            # Проверка на наличие выхода
            if (not hasattr(self, 'output_items_with_amount') or not self.output_items_with_amount) and \
            (not hasattr(self, 'output_liquids_with_amount') or not self.output_liquids_with_amount):
                status_label.configure(
                    text="❌ Ошибка: Добавьте хотя бы один элемент на выходе!", 
                    text_color="#F44336"
                )
                return
            
            # Форматируем имя
            constructor_name = self.format_to_lower_camel(original_name)
            if not constructor_name:
                status_label.configure(
                    text="❌ Ошибка: Некорректное название!",
                    text_color="#F44336"
                )
                return

            # Проверяем, существует ли уже такое имя
            if self.check_block_name_exists(original_name, PATEH_FOLDER):
                status_label.configure(
                    text=f"❌ Ошибка: Имя '{constructor_name}' уже используется!", 
                    text_color="#F44336"
                )
                return
            
            # Копируем текстуры
            size_multiplier = int(size_var.get())
            texture_configs = [
                {"template": TEMPO_ICON_BASE, "suffix": ""},
                {"template": TEMPO_ICON_TOP, "suffix": "-top"},
            ]
            
            texture_copied = self.copy_block_textures_multi(
                block_name=original_name,
                size_multiplier=size_multiplier,
                target_folder=FOLDER,
                texture_configs=texture_configs
            )
            texture_status = "✅ Текстуры созданы" if texture_copied else "⚠️ Текстуры не созданы"
            
            # Получаем значения свойств
            hp_value = entry_hp.get().strip() or "500"
            craft_time_raw = entry_craft_time.get().strip() or "60"
            speed_raw = entry_speed.get().strip() or "2"
            capacity_item_raw = entry_capacity_item.get().strip() or "10"
            capacity_liquid_raw = entry_capacity_liquid.get().strip() or "10"
            size_value = size_var.get()
            
            hp_value = str(int(float(hp_value)))
            always_unlocked_value = "true" if always_unlocked_var.get() else "false"
            
            # Получаем кастомные предметы и жидкости
            custom_items = self.get_custom_items()
            custom_liquids = self.get_custom_liquids()
            var_name = constructor_name
            
            # Формируем код для предметов строительства
            build_itemstack_code = ""
            build_items_list = []
            if hasattr(self, 'build_items') and self.build_items:
                item_counts = {}
                for item in self.build_items:
                    item_counts[item] = item_counts.get(item, 0) + 1
                
                item_parts = []
                for item_name, count in item_counts.items():
                    code_name = self.get_item_code_name(item_name, custom_items)
                    item_parts.append(f"{code_name}, {count}")
                    build_items_list.append((item_name, count))
                
                build_itemstack_code = f"\n            requirements(Category.{CATEDOR},\n                ItemStack.with({', '.join(item_parts)}));"
            
            # Формируем код для потребления
            consume_code = ""
            
            # Потребление предметов
            if hasattr(self, 'consume_items_with_amount') and self.consume_items_with_amount:
                item_consume_parts = []
                for item_name, amount in self.consume_items_with_amount:
                    code_name = self.get_item_code_name(item_name, custom_items)
                    item_consume_parts.append(f"{code_name}, {int(amount)}")
                
                if item_consume_parts:
                    consume_code += f"\n            consumeItems(ItemStack.with({', '.join(item_consume_parts)}));"
            
            # Потребление жидкостей
            if hasattr(self, 'consume_liquids_with_amount') and self.consume_liquids_with_amount:
                liquid_consume_parts = []
                for liquid_name, amount in self.consume_liquids_with_amount:
                    code_name = self.get_liquid_code_name(liquid_name, custom_liquids)
                    liquid_consume_parts.append(f"{code_name}, {float(amount)}f")
                
                if liquid_consume_parts:
                    consume_code += f"\n            consumeLiquids(LiquidStack.with({', '.join(liquid_consume_parts)}));"
            
            # Потребление энергии
            if self.consume_power_needed.get():
                power_amount = float(self.consume_power_amount.get())
                power_in_game = power_amount / 60.0
                consume_code += f"\n            consumePower({power_in_game:.4f}f);"
            
            # Формируем код для выхода
            output_code = ""
            
            # Выход предметов
            if hasattr(self, 'output_items_with_amount') and self.output_items_with_amount:
                item_output_parts = []
                for item_name, amount in self.output_items_with_amount:
                    code_name = self.get_item_code_name(item_name, custom_items)
                    item_output_parts.append(f"{code_name}, {int(amount)}")
                
                if item_output_parts:
                    output_code = f"\n            outputItems = ItemStack.with({', '.join(item_output_parts)});"
            
            # Выход жидкостей
            if hasattr(self, 'output_liquids_with_amount') and self.output_liquids_with_amount:
                liquid_output_parts = []
                for liquid_name, amount in self.output_liquids_with_amount:
                    code_name = self.get_liquid_code_name(liquid_name, custom_liquids)
                    liquid_output_parts.append(f"{code_name}, {float(amount)}f")
                
                if liquid_output_parts:
                    if output_code:
                        output_code += f"\n            outputLiquids = LiquidStack.with({', '.join(liquid_output_parts)});"
                    else:
                        output_code = f"\n            outputLiquids = LiquidStack.with({', '.join(liquid_output_parts)});"
            
            # Формируем свойства завода
            properties = f"""    health = {hp_value};
                size = {size_value};
                buildTime = {speed_raw};
                alwaysUnlocked = {always_unlocked_value};
                buildVisibility = BuildVisibility.shown;
                category = Category.{CATEDOR};
                craftTime = {craft_time_raw};
                liquidCapacity = {capacity_liquid_raw}f;
                itemCapacity = {capacity_item_raw};{build_itemstack_code}{consume_code}{output_code}

                localizedName = Core.bundle.get("{var_name}.name", "OH NO");
                description = Core.bundle.get("{var_name}.description", "OH NO");"""
            
            # Пути к файлам
            mod_name_lower = self.mod_name.lower() if self.mod_name else self.mod_name
            block_registration_path = self.get_absolute_path(f"src/{mod_name_lower}/init/blocks/{FOLDER}/{NAME}.java")
            main_mod_path = Path(self.mod_folder) / "src" / mod_name_lower / f"{self.mod_name}JavaMod.java"
            
            block_registration_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Читаем или создаем файл регистрации блоков
            try:
                with open(block_registration_path, 'r', encoding='utf-8') as file:
                    content = file.read()
            except FileNotFoundError:
                content = f"""package {mod_name_lower}.init.blocks.{FOLDER};

import arc.graphics.Color;
import arc.Core;
import mindustry.type.ItemStack;
import mindustry.type.Category;
import mindustry.type.LiquidStack;
import mindustry.content.Liquids;
import mindustry.world.Block;
import mindustry.world.blocks.production.{CATENAME};
import mindustry.world.meta.BuildVisibility;
import mindustry.content.Items;
import mindustry.Vars;
import {mod_name_lower}.init.items.ModItems;

public class {NAME} {{
    public static {CATENAME};
                                            
    public static void Load() {{
        // Регистрация блоков
    }}
}}"""
            
            crafter_exists = var_name in content
            tree_file_created = False
            main_file_updated = False
            
            if not crafter_exists:
                # Добавляем переменную блока
                if f"public static {CATENAME};" in content:
                    content = content.replace(
                        f"public static {CATENAME};",
                        f"public static {CATENAME} {var_name};"
                    )
                elif f"public static {CATENAME} " in content:
                    lines = content.split('\n')
                    for i, line in enumerate(lines):
                        if f"public static {CATENAME} " in line and var_name not in line:
                            lines[i] = line.rstrip(';') + f", {var_name};"
                            content = '\n'.join(lines)
                            break
                
                # Добавляем инициализацию блока
                load_start = content.find("public static void Load() {")
                if load_start != -1:
                    open_brace = content.find('{', load_start)
                    if open_brace != -1:
                        insert_pos = open_brace + 1
                        indent = "        "
                        crafter_code = f'\n{indent}{var_name} = new {CATENAME}("{constructor_name}"){{{{\n{indent}{properties}\n{indent}}}}};'
                        content = content[:insert_pos] + crafter_code + content[insert_pos:]
                
                # Сохраняем файл
                with open(block_registration_path, 'w', encoding='utf-8') as file:
                    file.write(content)
                
                # Обновляем главный файл мода
                try:
                    with open(main_mod_path, 'r', encoding='utf-8') as file:
                        main_content = file.read()
                    
                    # Добавляем импорт
                    import_statement = f"import {mod_name_lower}.init.blocks.{FOLDER}.{NAME};"
                    if import_statement not in main_content:
                        import_add_pos = main_content.find("//import_add")
                        if import_add_pos != -1:
                            insert_pos = import_add_pos + len("//import_add")
                            if insert_pos < len(main_content) and main_content[insert_pos] == '\n':
                                main_content = main_content[:insert_pos] + f"\n{import_statement}" + main_content[insert_pos:]
                            else:
                                main_content = main_content[:insert_pos] + f"\n{import_statement}" + main_content[insert_pos:]
                    
                    # Добавляем вызов Load
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
                    
                    main_file_updated = True
                    
                    # Создаем файл дерева технологий, если Always Unlocked = false
                    if not always_unlocked_var.get():
                        research_items_list = []
                        if hasattr(self, 'research_items') and self.research_items:
                            item_counts = {}
                            for item in self.research_items:
                                item_counts[item] = item_counts.get(item, 0) + 1
                            
                            for item_name, count in item_counts.items():
                                research_items_list.append((item_name, count))
                        
                        research_block = selected_block_internal_var.get()
                        
                        # Используем универсальную функцию
                        tree_file_created = self.create_tech_tree_file_universal(
                            block_var_name=var_name,
                            block_constructor_name=constructor_name,
                            research_block=research_block,
                            research_items=research_items_list,
                            block_type="crafter",
                            folder_name=FOLDER,
                            class_name="GenericCrafterTree"
                        )
                        
                        # ИСПОЛЬЗУЕМ НОВУЮ УНИВЕРСАЛЬНУЮ ФУНКЦИЮ для обновления главного файла
                        if tree_file_created:
                            self.update_main_mod_file_universal(
                                import_path=f"{mod_name_lower}.content.GenericCrafterTree",
                                load_statement="GenericCrafterTree.Load();"
                            )
                    
                    # Формируем сообщение о результате
                    status_messages = [
                        f"✅ {BL_NAME_2} '{var_name}' успешно создан!",
                        f'📝 Имя в игре: "{constructor_name}"',
                        f"{texture_status}",
                    ]
                    
                    # Добавляем информацию о Always Unlocked
                    if always_unlocked_var.get():
                        status_messages.append("🔓 Always Unlocked: ДА (доступен с самого начала)")
                    else:
                        status_messages.append("🔒 Always Unlocked: НЕТ (требуется исследование)")
                    
                    status_messages.extend([
                        f"📊 Свойства {BL_NAME}:",
                        f"  • ❤️ Здоровье: {hp_value}",
                        f"  • ⏱️ Время крафта: {craft_time_raw}",
                        f"  • ⚡ Скорость стройки: {speed_raw}",
                        f"  • 📏 Размер: {size_value}",
                        f"  • 📦 Вместимость предметов: {capacity_item_raw}",
                        f"  • 💧 Вместимость жидкости: {capacity_liquid_raw}",
                    ])
                    
                    if build_items_list:
                        items_list = []
                        for item_name, count in build_items_list:
                            if item_name in custom_items:
                                items_list.append(f"ModItems.{item_name} ×{count}")
                            else:
                                display_name = item_name.replace('-', ' ').title()
                                items_list.append(f"{display_name} ×{count}")
                        
                        status_messages.append(f"  • 🔨 Стройка: {', '.join(items_list)}")
                    
                    # Потребление
                    consume_list = []
                    if hasattr(self, 'consume_items_with_amount') and self.consume_items_with_amount:
                        for item_name, amount in self.consume_items_with_amount:
                            if item_name in custom_items:
                                consume_list.append(f"ModItems.{item_name} ×{int(amount)}")
                            else:
                                display_name = item_name.replace('-', ' ').title()
                                consume_list.append(f"{display_name} ×{int(amount)}")
                    
                    if hasattr(self, 'consume_liquids_with_amount') and self.consume_liquids_with_amount:
                        for liquid_name, amount in self.consume_liquids_with_amount:
                            if liquid_name in custom_liquids:
                                consume_list.append(f"ModLiquids.{liquid_name} ×{float(amount)}")
                            else:
                                display_name = liquid_name.replace('-', ' ').title()
                                consume_list.append(f"{display_name} ×{float(amount)}")
                    
                    if self.consume_power_needed.get():
                        power_amount = float(self.consume_power_amount.get())
                        power_in_game = power_amount / 60.0
                        consume_list.append(f"⚡ {power_amount} энергии/сек ({power_in_game:.4f}f)")
                    
                    if consume_list:
                        status_messages.append(f"  • ⬇️ Потребление: {', '.join(consume_list)}")
                    
                    # Выход
                    output_list = []
                    if hasattr(self, 'output_items_with_amount') and self.output_items_with_amount:
                        for item_name, amount in self.output_items_with_amount:
                            if item_name in custom_items:
                                output_list.append(f"ModItems.{item_name} ×{int(amount)}")
                            else:
                                display_name = item_name.replace('-', ' ').title()
                                output_list.append(f"{display_name} ×{int(amount)}")
                    
                    if hasattr(self, 'output_liquids_with_amount') and self.output_liquids_with_amount:
                        for liquid_name, amount in self.output_liquids_with_amount:
                            if liquid_name in custom_liquids:
                                output_list.append(f"ModLiquids.{liquid_name} ×{float(amount)}")
                            else:
                                display_name = liquid_name.replace('-', ' ').title()
                                output_list.append(f"{display_name} ×{float(amount)}")
                    
                    if output_list:
                        status_messages.append(f"  • ⬆️ Выход: {', '.join(output_list)}")
                    
                    if not always_unlocked_var.get():
                        if hasattr(self, 'research_items') and self.research_items:
                            research_list = []
                            item_counts = {}
                            for item in self.research_items:
                                item_counts[item] = item_counts.get(item, 0) + 1
                            
                            for item_name, count in item_counts.items():
                                if item_name in custom_items:
                                    research_list.append(f"ModItems.{item_name} ×{count}")
                                else:
                                    display_name = item_name.replace('-', ' ').title()
                                    research_list.append(f"{display_name} ×{count}")
                            
                            status_messages.append(f"  • 💰 Исследование: {', '.join(research_list)}")
                        
                        status_messages.append(f"  • 🎯 Блок исследования: {selected_block_var.get()}")
                        
                        if tree_file_created:
                            status_messages.append(f"  • 🌳 GenericCrafterTree.java создан и добавлен в main (GenericCrafterTree.Load())")
                        else:
                            status_messages.append(f"  • ⚠️ GenericCrafterTree.java не создан")
                    
                    if main_file_updated:
                        status_messages.append(f"  • 📄 Главный файл мода обновлен")
                    
                    status_text = "\n".join(status_messages)
                    status_label.configure(text=status_text, text_color="#4CAF50")
                    
                except Exception as e:
                    status_label.configure(text=f"❌ Ошибка: {str(e)}", text_color="#F44336")
            else:
                status_label.configure(text=f"⚠️ {BL_NAME_2} уже существует", text_color="#FF9800")
            
            self.root.after(5000, lambda: status_label.configure(text=""))

        # === Кнопки действий ===
        buttons_frame = ctk.CTkFrame(button_frame, fg_color="transparent")
        buttons_frame.pack(pady=10)
        
        ctk.CTkButton(
            buttons_frame,
            text=f"Создать {BL_CR_NAME}",
            command=process_crafter,
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
        
        # Инициализация переменных
        self.build_items = []
        self.research_items = []
        self.consume_items_with_amount = []
        self.consume_liquids_with_amount = []
        self.output_items_with_amount = []
        self.output_liquids_with_amount = []
        self.consume_power_needed.set(False)
        self.consume_power_amount.set("1.0")

    def create_bridge(self):
        """Создает или добавляет новый мост в bridges/Bridges.java"""
        
        # Константы для моста
        PATEH_FOLDER = self.PATEH_FOLDER

        CATENAME = "CircularBridge"
        CATEDOR = "distribution"
        TEMPO_ICON = "bridge-conveyor.png"
        TEMPO_ICON_END = "bridge-conveyor-end.png"
        TEMPO_ICON_ARROW = "bridge-conveyor-arrow.png"
        TEMPO_ICON_BRIDGE = "bridge-conveyor-bridge.png"
        BL_NAME_2 = "Мост"
        BL_CR_NAME = "Мост"
        BL_NAME = "моста"
        ENTRY_NAME1 = "bridge"
        NAME = "Bridges"
        FOLDER = "bridges"
        
        # Очищаем окно
        self.clear_window()
        
        # Основной фрейм с прокруткой
        main_frame = ctk.CTkFrame(self.root, fg_color="#2b2b2b")
        main_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        scroll_frame = ctk.CTkScrollableFrame(
            main_frame,
            width=500,
            height=700,
            fg_color="#2b2b2b"
        )
        scroll_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Заголовок
        title_frame = ctk.CTkFrame(scroll_frame, fg_color="transparent")
        title_frame.pack(fill="x", pady=(0, 20))
        
        ctk.CTkLabel(
            title_frame,
            text="Создание моста",
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
            text=f"Название {BL_NAME} (английское, можно пробел, первая буква маленькая):",
            font=("Arial", 16),
            text_color="#BDBDBD"
        ).pack(anchor="w", pady=(0, 5))
        
        entry_name = ctk.CTkEntry(
            name_frame,
            width=400,
            height=40,
            placeholder_text=f"{ENTRY_NAME1} name",
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
            text=f"Свойства {BL_NAME}",
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
            text="Прочность (health):",
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

        # Скорость стройки
        speed_frame = ctk.CTkFrame(properties_grid, fg_color="transparent")
        speed_frame.grid(row=0, column=1, padx=10, pady=5, sticky="ew")
        
        ctk.CTkLabel(
            speed_frame,
            text="Скорость стройки (buildTime):",
            font=("Arial", 15),
            text_color="#BDBDBD"
        ).pack(anchor="w", pady=(0, 5))
        
        entry_speed = ctk.CTkEntry(
            speed_frame,
            width=180,
            height=38,
            placeholder_text="1",
            font=("Arial", 14),
            validate="key",
            validatecommand=vcmd_float,
            fg_color="#424242",
            border_color="#555555",
            text_color="#FFFFFF",
            placeholder_text_color="#888888"
        )
        entry_speed.pack(fill="x")

        # Размер (фиксирован для моста)
        size_info_frame = ctk.CTkFrame(properties_grid, fg_color="transparent")
        size_info_frame.grid(row=1, column=0, padx=10, pady=5, sticky="ew")
        
        ctk.CTkLabel(
            size_info_frame,
            text="Размер (size): 1 (фиксировано для моста)",
            font=("Arial", 15),
            text_color="#FFA500"
        ).pack(anchor="w", pady=(0, 5))

        # Потребление энергии
        power_frame = ctk.CTkFrame(properties_grid, fg_color="transparent")
        power_frame.grid(row=1, column=1, padx=10, pady=5, sticky="ew")
        
        ctk.CTkLabel(
            power_frame,
            text="Потребление энергии (powerUsage) в сек:\n(0 - не требует энергии)",
            font=("Arial", 15),
            text_color="#BDBDBD"
        ).pack(anchor="w", pady=(0, 5))
        
        entry_power = ctk.CTkEntry(
            power_frame,
            width=180,
            height=38,
            placeholder_text="0",
            font=("Arial", 14),
            validate="key",
            validatecommand=vcmd_int,
            fg_color="#424242",
            border_color="#555555",
            text_color="#FFFFFF",
            placeholder_text_color="#888888"
        )
        entry_power.pack(fill="x")

        # Радиус
        range_frame = ctk.CTkFrame(properties_grid, fg_color="transparent")
        range_frame.grid(row=2, column=0, padx=10, pady=5, sticky="ew")
        
        ctk.CTkLabel(
            range_frame,
            text="Радиус (range):",
            font=("Arial", 15),
            text_color="#BDBDBD"
        ).pack(anchor="w", pady=(0, 5))
        
        entry_range = ctk.CTkEntry(
            range_frame,
            width=180,
            height=38,
            placeholder_text="8",
            font=("Arial", 14),
            validate="key",
            validatecommand=vcmd_int,
            fg_color="#424242",
            border_color="#555555",
            text_color="#FFFFFF",
            placeholder_text_color="#888888"
        )
        entry_range.pack(fill="x")

        # Предметы в секунду
        items_per_second_frame = ctk.CTkFrame(properties_grid, fg_color="transparent")
        items_per_second_frame.grid(row=2, column=1, padx=10, pady=5, sticky="ew")
        
        ctk.CTkLabel(
            items_per_second_frame,
            text="Предметы в секунду (itemsPerSecond):",
            font=("Arial", 15),
            text_color="#BDBDBD"
        ).pack(anchor="w", pady=(0, 5))
        
        entry_items_per_second = ctk.CTkEntry(
            items_per_second_frame,
            width=180,
            height=38,
            placeholder_text="10",
            font=("Arial", 14),
            validate="key",
            validatecommand=vcmd_int,
            fg_color="#424242",
            border_color="#555555",
            text_color="#FFFFFF",
            placeholder_text_color="#888888"
        )
        entry_items_per_second.pack(fill="x")

        # Вместимость
        capacity_frame = ctk.CTkFrame(properties_grid, fg_color="transparent")
        capacity_frame.grid(row=3, column=0, padx=10, pady=5, sticky="ew")
        
        ctk.CTkLabel(
            capacity_frame,
            text="Вместимость (itemCapacity):",
            font=("Arial", 15),
            text_color="#BDBDBD"
        ).pack(anchor="w", pady=(0, 5))
        
        entry_capacity = ctk.CTkEntry(
            capacity_frame,
            width=180,
            height=38,
            placeholder_text="20",
            font=("Arial", 14),
            validate="key",
            validatecommand=vcmd_int,
            fg_color="#424242",
            border_color="#555555",
            text_color="#FFFFFF",
            placeholder_text_color="#888888"
        )
        entry_capacity.pack(fill="x")

        # Круглый режим
        circular_frame = ctk.CTkFrame(properties_grid, fg_color="transparent")
        circular_frame.grid(row=3, column=1, padx=10, pady=5, sticky="ew")
        
        circular_var = ctk.BooleanVar(value=True)
        
        ctk.CTkLabel(
            circular_frame,
            text="Круглый режим (Circular Bridge):",
            font=("Arial", 15),
            text_color="#BDBDBD"
        ).pack(anchor="w", pady=(0, 5))
        
        circular_checkbox = ctk.CTkCheckBox(
            circular_frame,
            text="Включить круговое соединение (позволяет подключаться по диагонали)",
            variable=circular_var,
            font=("Arial", 12),
            text_color="#FFFFFF",
            checkbox_height=20,
            checkbox_width=20,
            fg_color="#2E7D32",
            hover_color="#1B5E20"
        )
        circular_checkbox.pack(anchor="w", pady=5)

        # === Always Unlocked с индикатором ===
        always_unlocked_var = ctk.BooleanVar(value=False)
        always_unlocked_status = ctk.CTkLabel(properties_card, text="", font=("Arial", 12))

        # === КАРТОЧКА ДЛЯ ПРЕДМЕТОВ СТРОИТЕЛЬСТВА ===
        build_card = ctk.CTkFrame(
            scroll_frame,
            corner_radius=15,
            border_width=2,
            border_color="#404040",
            fg_color="#363636"
        )
        build_card.pack(fill="x", pady=(0, 20))
        
        ctk.CTkLabel(
            build_card,
            text="🔨 Предметы для строительства",
            font=("Arial", 18, "bold"),
            text_color="#4CAF50"
        ).pack(pady=(15, 10), padx=20, anchor="w")
        
        build_items_frame = ctk.CTkFrame(build_card, fg_color="transparent")
        build_items_frame.pack(fill="x", padx=20, pady=(0, 15))
        
        build_items_var = tk.StringVar(value="Выбрано: 0 предметов")
        build_items_label = ctk.CTkLabel(
            build_items_frame,
            textvariable=build_items_var,
            font=("Arial", 12),
            text_color="#9E9E9E",
            wraplength=400
        )
        build_items_label.pack(anchor="w", pady=(5, 0))
        
        ctk.CTkButton(
            build_items_frame,
            text="📋 Выбрать предметы для строительства",
            command=lambda: self.open_items_editor(build_items_var, "build"),
            height=35,
            font=("Arial", 13),
            fg_color="#2E7D32",
            hover_color="#1B5E20",
            corner_radius=6
        ).pack(anchor="w", pady=(0, 5))

        # === КАРТОЧКА ДЛЯ ИССЛЕДОВАНИЯ ===
        research_card = ctk.CTkFrame(
            scroll_frame,
            corner_radius=15,
            border_width=2,
            border_color="#404040",
            fg_color="#363636"
        )
        
        # Переменные для исследования
        selected_block_var = tk.StringVar(value="Не выбран")
        selected_block_internal_var = tk.StringVar(value="")
        selected_block_type_var = tk.StringVar(value="")
        block_icon_label = ctk.CTkLabel(properties_card, text="🌉", font=("Arial", 30))
        block_path_label = ctk.CTkLabel(properties_card, text="", font=("Arial", 10))
        research_items_var = tk.StringVar(value="Выбрано: 0 предметов")

        # Используем универсальную функцию
        always_unlocked_check, select_block_button, select_items_button = self.setup_research_system(
            always_unlocked_var=always_unlocked_var,
            research_card=research_card,
            always_unlocked_status=always_unlocked_status,
            build_card=build_card,
            selected_block_var=selected_block_var,
            selected_block_internal_var=selected_block_internal_var,
            selected_block_type_var=selected_block_type_var,
            block_icon_label=block_icon_label,
            block_path_label=block_path_label,
            research_items_var=research_items_var,
            on_block_selected_callback=None
        )

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

        # === Основная функция создания моста ===
        def process_bridge():
            self.circularBridge()
            original_name = entry_name.get().strip()
            
            if not original_name:
                status_label.configure(
                    text="❌ Ошибка: Введите название моста!", 
                    text_color="#F44336"
                )
                return
            
            # Проверка для always_unlocked = false
            is_valid, error_msg = self.validate_research(
                always_unlocked_var=always_unlocked_var,
                research_items=self.research_items if hasattr(self, 'research_items') else [],
                selected_block_internal_var=selected_block_internal_var
            )
            
            if not is_valid:
                status_label.configure(text=error_msg, text_color="#F44336")
                return
            
            if not hasattr(self, 'build_items') or not self.build_items:
                status_label.configure(
                    text="❌ Ошибка: Выберите предметы для строительства!", 
                    text_color="#F44336"
                )
                return
            
            # Форматируем имя
            constructor_name = self.format_to_lower_camel(original_name)
            if not constructor_name:
                status_label.configure(
                    text="❌ Ошибка: Некорректное название!", 
                    text_color="#F44336"
                )
                return

            # Проверяем, существует ли уже такое имя
            if self.check_block_name_exists(original_name, PATEH_FOLDER):
                status_label.configure(
                    text=f"❌ Ошибка: Имя '{constructor_name}' уже используется!", 
                    text_color="#F44336"
                )
                return
            
            # Копируем текстуры (для моста их 4)
            texture_configs = [
                {"template": TEMPO_ICON, "suffix": ""},
                {"template": TEMPO_ICON_END, "suffix": "-end"},
                {"template": TEMPO_ICON_BRIDGE, "suffix": "-bridge"},
                {"template": TEMPO_ICON_ARROW, "suffix": "-arrow"},
            ]
            
            texture_copied = self.copy_block_textures_multi(
                block_name=original_name,
                size_multiplier=1,
                target_folder=FOLDER,
                texture_configs=texture_configs
            )
            texture_status = "✅ Текстуры созданы" if texture_copied else "⚠️ Текстуры не созданы"
            
            # Получаем значения свойств
            hp_value = entry_hp.get().strip() or "400"
            speed_raw = entry_speed.get().strip() or "1"
            power_raw = entry_power.get().strip() or "0"
            range_raw = entry_range.get().strip() or "8"
            items_per_second_raw = entry_items_per_second.get().strip() or "10"
            capacity_raw = entry_capacity.get().strip() or "20"
            
            hp_value = str(int(float(hp_value)))
            always_unlocked_value = "true" if always_unlocked_var.get() else "false"
            circular_value = "true" if circular_var.get() else "false"
            
            # Получаем кастомные предметы
            custom_items = self.get_custom_items()
            var_name = constructor_name
            
            # Формируем код для предметов строительства
            build_itemstack_code = ""
            build_items_list = []
            if hasattr(self, 'build_items') and self.build_items:
                item_counts = {}
                for item in self.build_items:
                    item_counts[item] = item_counts.get(item, 0) + 1
                
                item_parts = []
                for item_name, count in item_counts.items():
                    code_name = self.get_item_code_name(item_name, custom_items)
                    item_parts.append(f"{code_name}, {count}")
                    build_items_list.append((item_name, count))
                
                build_itemstack_code = f"\n            requirements(Category.{CATEDOR},\n                ItemStack.with({', '.join(item_parts)}));"
            
            # Формируем свойства моста
            properties = f"""    health = {hp_value};
                size = 1;
                buildTime = {speed_raw};
                alwaysUnlocked = {always_unlocked_value};
                buildVisibility = BuildVisibility.shown;
                category = Category.{CATEDOR};{build_itemstack_code}
                powerUsage = {power_raw};
                range = {range_raw};
                itemsPerSecond = {items_per_second_raw};
                itemCapacity = {capacity_raw};
                circu = {circular_value};

                localizedName = Core.bundle.get("{var_name}.name", "OH NO");
                description = Core.bundle.get("{var_name}.description", "OH NO");"""
            
            # Пути к файлам
            mod_name_lower = self.mod_name.lower() if self.mod_name else self.mod_name
            block_registration_path = self.get_absolute_path(f"src/{mod_name_lower}/init/blocks/{FOLDER}/{NAME}.java")
            main_mod_path = Path(self.mod_folder) / "src" / mod_name_lower / f"{self.mod_name}JavaMod.java"
            
            # Создаем родительскую папку
            block_registration_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Читаем или создаем файл регистрации блоков
            try:
                with open(block_registration_path, 'r', encoding='utf-8') as file:
                    content = file.read()
            except FileNotFoundError:
                content = f"""package {mod_name_lower}.init.blocks.{FOLDER};

import arc.graphics.Color;
import arc.Core;
import mindustry.type.ItemStack;
import mindustry.type.Category;
import mindustry.world.Block;
import mindustry.world.blocks.distribution.ItemBridge;
import mindustry.world.meta.BuildVisibility;
import mindustry.content.Items;
import mindustry.Vars;
import {mod_name_lower}.init.items.ModItems;
import {mod_name_lower}.custom_types.blocks.bridge.CircularBridge;

public class {NAME} {{
    public static CircularBridge;
                                                
    public static void Load() {{
        // Регистрация блоков
    }}
}}"""
            
            bridge_exists = var_name in content
            tree_file_created = False
            main_file_updated = False
            
            if not bridge_exists:
                # Добавляем переменную блока
                if f"public static CircularBridge;" in content:
                    content = content.replace(
                        f"public static CircularBridge;",
                        f"public static CircularBridge {var_name};"
                    )
                elif f"public static CircularBridge " in content:
                    lines = content.split('\n')
                    for i, line in enumerate(lines):
                        if f"public static CircularBridge " in line and var_name not in line:
                            lines[i] = line.rstrip(';') + f", {var_name};"
                            content = '\n'.join(lines)
                            break
                
                # Добавляем инициализацию блока
                load_start = content.find("public static void Load() {")
                if load_start != -1:
                    open_brace = content.find('{', load_start)
                    if open_brace != -1:
                        insert_pos = open_brace + 1
                        indent = "        "
                        bridge_code = f'\n{indent}{var_name} = new CircularBridge("{constructor_name}"){{{{\n{indent}{properties}\n{indent}}}}};'
                        content = content[:insert_pos] + bridge_code + content[insert_pos:]
                
                # Сохраняем файл
                with open(block_registration_path, 'w', encoding='utf-8') as file:
                    file.write(content)
                
                # Обновляем главный файл мода
                try:
                    with open(main_mod_path, 'r', encoding='utf-8') as file:
                        main_content = file.read()
                    
                    # Добавляем импорт
                    import_statement = f"import {mod_name_lower}.init.blocks.{FOLDER}.{NAME};"
                    if import_statement not in main_content:
                        import_add_pos = main_content.find("//import_add")
                        if import_add_pos != -1:
                            insert_pos = import_add_pos + len("//import_add")
                            if insert_pos < len(main_content) and main_content[insert_pos] == '\n':
                                main_content = main_content[:insert_pos] + f"\n{import_statement}" + main_content[insert_pos:]
                            else:
                                main_content = main_content[:insert_pos] + f"\n{import_statement}" + main_content[insert_pos:]
                    
                    # Добавляем вызов Load
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
                    
                    main_file_updated = True
                    
                    # Создаем файл дерева технологий, если Always Unlocked = false
                    if not always_unlocked_var.get():
                        research_items_list = []
                        if hasattr(self, 'research_items') and self.research_items:
                            item_counts = {}
                            for item in self.research_items:
                                item_counts[item] = item_counts.get(item, 0) + 1
                            
                            for item_name, count in item_counts.items():
                                research_items_list.append((item_name, count))
                        
                        research_block = selected_block_internal_var.get()
                        
                        # Используем универсальную функцию
                        tree_file_created = self.create_tech_tree_file_universal(
                            block_var_name=var_name,
                            block_constructor_name=constructor_name,
                            research_block=research_block,
                            research_items=research_items_list,
                            block_type="bridge",
                            folder_name=FOLDER,
                            class_name="BridgesTree"
                        )
                        
                        if tree_file_created:
                            self.update_main_mod_file_universal(
                                import_path=f"{mod_name_lower}.content.BridgesTree",
                                load_statement="BridgesTree.Load();"
                            )
                    
                    # Формируем сообщение о результате
                    status_messages = [
                        f"✅ {BL_NAME_2} '{var_name}' успешно создан!",
                        f'📝 Имя в игре: "{constructor_name}"',
                        f"{texture_status}",
                    ]
                    
                    # Добавляем информацию о Always Unlocked
                    if always_unlocked_var.get():
                        status_messages.append("🔓 Always Unlocked: ДА (доступен с самого начала)")
                    else:
                        status_messages.append("🔒 Always Unlocked: НЕТ (требуется исследование)")
                    
                    status_messages.extend([
                        f"📊 Свойства {BL_NAME}:",
                        f"  • ❤️ Здоровье: {hp_value}",
                        f"  • ⚡ Скорость стройки: {speed_raw}",
                        f"  • ⚡ Потребление энергии: {power_raw}/сек",
                        f"  • 📡 Радиус: {range_raw}",
                        f"  • 📦 Предметов/сек: {items_per_second_raw}",
                        f"  • 💾 Вместимость: {capacity_raw}",
                        f"  • 🔄 Круговой режим: {'Да' if circular_var.get() else 'Нет'}",
                    ])
                    
                    if build_items_list:
                        items_list = []
                        for item_name, count in build_items_list:
                            if item_name in custom_items:
                                items_list.append(f"ModItems.{item_name} ×{count}")
                            else:
                                display_name = item_name.replace('-', ' ').title()
                                items_list.append(f"{display_name} ×{count}")
                        
                        status_messages.append(f"  • 🔨 Стройка: {', '.join(items_list)}")
                    
                    if not always_unlocked_var.get():
                        if hasattr(self, 'research_items') and self.research_items:
                            research_list = []
                            item_counts = {}
                            for item in self.research_items:
                                item_counts[item] = item_counts.get(item, 0) + 1
                            
                            for item_name, count in item_counts.items():
                                if item_name in custom_items:
                                    research_list.append(f"ModItems.{item_name} ×{count}")
                                else:
                                    display_name = item_name.replace('-', ' ').title()
                                    research_list.append(f"{display_name} ×{count}")
                            
                            status_messages.append(f"  • 💰 Исследование: {', '.join(research_list)}")
                        
                        status_messages.append(f"  • 🎯 Блок исследования: {selected_block_var.get()}")
                        
                        if tree_file_created:
                            status_messages.append(f"  • 🌳 BridgesTree.java создан и добавлен в main (BridgesTree.Load())")
                        else:
                            status_messages.append(f"  • ⚠️ BridgesTree.java не создан")
                    
                    if main_file_updated:
                        status_messages.append(f"  • 📄 Главный файл мода обновлен")
                    
                    status_text = "\n".join(status_messages)
                    status_label.configure(text=status_text, text_color="#4CAF50")
                    
                except Exception as e:
                    status_label.configure(text=f"❌ Ошибка: {str(e)}", text_color="#F44336")
                    import traceback
                    traceback.print_exc()
            else:
                status_label.configure(text=f"⚠️ {BL_NAME_2} '{var_name}' уже существует", text_color="#FF9800")
            
            self.root.after(5000, lambda: status_label.configure(text=""))

        # === Кнопки действий ===
        buttons_frame = ctk.CTkFrame(button_frame, fg_color="transparent")
        buttons_frame.pack(pady=10)
        
        ctk.CTkButton(
            buttons_frame,
            text=f"Создать {BL_CR_NAME}",
            command=process_bridge,
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
        
        # Инициализация переменных
        self.build_items = []
        self.research_items = []

    def create_conveyor(self):
        """Создает или добавляет новый мост в bridges/Bridges.java"""
        
        # Константы для моста
        PATEH_FOLDER = self.PATEH_FOLDER

        CATENAME = "Conveyor"
        CATEDOR = "distribution"
        CONVEYOR00 = "conveyor-0-0.png"
        CONVEYOR01 = "conveyor-0-1.png"
        CONVEYOR02 = "conveyor-0-2.png"
        CONVEYOR03 = "conveyor-0-3.png"
        CONVEYOR10 = "conveyor-1-0.png"
        CONVEYOR11 = "conveyor-1-1.png"
        CONVEYOR12 = "conveyor-1-2.png"
        CONVEYOR13 = "conveyor-1-3.png"
        CONVEYOR20 = "conveyor-2-0.png"
        CONVEYOR21 = "conveyor-2-1.png"
        CONVEYOR22 = "conveyor-2-2.png"
        CONVEYOR23 = "conveyor-2-3.png"
        CONVEYOR30 = "conveyor-3-0.png"
        CONVEYOR31 = "conveyor-3-1.png"
        CONVEYOR32 = "conveyor-3-2.png"
        CONVEYOR33 = "conveyor-3-3.png"
        CONVEYOR40 = "conveyor-4-0.png"
        CONVEYOR41 = "conveyor-4-1.png"
        CONVEYOR42 = "conveyor-4-2.png"
        CONVEYOR43 = "conveyor-4-3.png"
        BL_NAME_2 = "Конвеер"
        BL_CR_NAME = "Конвеер"
        BL_NAME = "Конвеера"
        ENTRY_NAME1 = "conveyor"
        NAME = "Conveyors"
        FOLDER = "conveyors"
        
        # Очищаем окно
        self.clear_window()
        
        # Основной фрейм с прокруткой
        main_frame = ctk.CTkFrame(self.root, fg_color="#2b2b2b")
        main_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        scroll_frame = ctk.CTkScrollableFrame(
            main_frame,
            width=500,
            height=700,
            fg_color="#2b2b2b"
        )
        scroll_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Заголовок
        title_frame = ctk.CTkFrame(scroll_frame, fg_color="transparent")
        title_frame.pack(fill="x", pady=(0, 20))
        
        ctk.CTkLabel(
            title_frame,
            text="Создание моста",
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
            text=f"Название {BL_NAME} (английское, можно пробел, первая буква маленькая):",
            font=("Arial", 16),
            text_color="#BDBDBD"
        ).pack(anchor="w", pady=(0, 5))
        
        entry_name = ctk.CTkEntry(
            name_frame,
            width=400,
            height=40,
            placeholder_text=f"{ENTRY_NAME1} name",
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
            text=f"Свойства {BL_NAME}",
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
            text="Прочность (health):",
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

        # Скорость стройки
        speed_frame = ctk.CTkFrame(properties_grid, fg_color="transparent")
        speed_frame.grid(row=0, column=1, padx=10, pady=5, sticky="ew")
        
        ctk.CTkLabel(
            speed_frame,
            text="Скорость стройки (buildTime):",
            font=("Arial", 15),
            text_color="#BDBDBD"
        ).pack(anchor="w", pady=(0, 5))
        
        entry_speed = ctk.CTkEntry(
            speed_frame,
            width=180,
            height=38,
            placeholder_text="1",
            font=("Arial", 14),
            validate="key",
            validatecommand=vcmd_float,
            fg_color="#424242",
            border_color="#555555",
            text_color="#FFFFFF",
            placeholder_text_color="#888888"
        )
        entry_speed.pack(fill="x")

        # Размер (фиксирован для моста)
        size_info_frame = ctk.CTkFrame(properties_grid, fg_color="transparent")
        size_info_frame.grid(row=1, column=0, padx=10, pady=5, sticky="ew")
        
        ctk.CTkLabel(
            size_info_frame,
            text="Размер (size): 1 (фиксировано для конвеера)",
            font=("Arial", 15),
            text_color="#FFA500"
        ).pack(anchor="w", pady=(0, 5))

        # Предметы в секунду
        items_per_second_frame = ctk.CTkFrame(properties_grid, fg_color="transparent")
        items_per_second_frame.grid(row=2, column=1, padx=10, pady=5, sticky="ew")
        
        ctk.CTkLabel(
            items_per_second_frame,
            text="Предметы в секунду (itemsPerSecond):",
            font=("Arial", 15),
            text_color="#BDBDBD"
        ).pack(anchor="w", pady=(0, 5))
        
        entry_items_per_second = ctk.CTkEntry(
            items_per_second_frame,
            width=180,
            height=38,
            placeholder_text="5",
            font=("Arial", 14),
            validate="key",
            validatecommand=vcmd_int,
            fg_color="#424242",
            border_color="#555555",
            text_color="#FFFFFF",
            placeholder_text_color="#888888"
        )
        entry_items_per_second.pack(fill="x")

        # Вместимость
        capacity_frame = ctk.CTkFrame(properties_grid, fg_color="transparent")
        capacity_frame.grid(row=2, column=0, padx=10, pady=5, sticky="ew")
        
        ctk.CTkLabel(
            capacity_frame,
            text="Вместимость (itemCapacity):",
            font=("Arial", 15),
            text_color="#BDBDBD"
        ).pack(anchor="w", pady=(0, 5))
        
        entry_capacity = ctk.CTkEntry(
            capacity_frame,
            width=180,
            height=38,
            placeholder_text="3",
            font=("Arial", 14),
            validate="key",
            validatecommand=vcmd_int,
            fg_color="#424242",
            border_color="#555555",
            text_color="#FFFFFF",
            placeholder_text_color="#888888"
        )
        entry_capacity.pack(fill="x")

        # === Always Unlocked с индикатором ===
        always_unlocked_var = ctk.BooleanVar(value=False)
        always_unlocked_status = ctk.CTkLabel(properties_card, text="", font=("Arial", 12))

        # === КАРТОЧКА ДЛЯ ПРЕДМЕТОВ СТРОИТЕЛЬСТВА ===
        build_card = ctk.CTkFrame(
            scroll_frame,
            corner_radius=15,
            border_width=2,
            border_color="#404040",
            fg_color="#363636"
        )
        build_card.pack(fill="x", pady=(0, 20))
        
        ctk.CTkLabel(
            build_card,
            text="🔨 Предметы для строительства",
            font=("Arial", 18, "bold"),
            text_color="#4CAF50"
        ).pack(pady=(15, 10), padx=20, anchor="w")
        
        build_items_frame = ctk.CTkFrame(build_card, fg_color="transparent")
        build_items_frame.pack(fill="x", padx=20, pady=(0, 15))
        
        build_items_var = tk.StringVar(value="Выбрано: 0 предметов")
        build_items_label = ctk.CTkLabel(
            build_items_frame,
            textvariable=build_items_var,
            font=("Arial", 12),
            text_color="#9E9E9E",
            wraplength=400
        )
        build_items_label.pack(anchor="w", pady=(5, 0))
        
        ctk.CTkButton(
            build_items_frame,
            text="📋 Выбрать предметы для строительства",
            command=lambda: self.open_items_editor(build_items_var, "build"),
            height=35,
            font=("Arial", 13),
            fg_color="#2E7D32",
            hover_color="#1B5E20",
            corner_radius=6
        ).pack(anchor="w", pady=(0, 5))

        # === КАРТОЧКА ДЛЯ ИССЛЕДОВАНИЯ ===
        research_card = ctk.CTkFrame(
            scroll_frame,
            corner_radius=15,
            border_width=2,
            border_color="#404040",
            fg_color="#363636"
        )
        
        # Переменные для исследования
        selected_block_var = tk.StringVar(value="Не выбран")
        selected_block_internal_var = tk.StringVar(value="")
        selected_block_type_var = tk.StringVar(value="")
        block_icon_label = ctk.CTkLabel(properties_card, text="🌉", font=("Arial", 30))
        block_path_label = ctk.CTkLabel(properties_card, text="", font=("Arial", 10))
        research_items_var = tk.StringVar(value="Выбрано: 0 предметов")

        # Используем универсальную функцию
        always_unlocked_check, select_block_button, select_items_button = self.setup_research_system(
            always_unlocked_var=always_unlocked_var,
            research_card=research_card,
            always_unlocked_status=always_unlocked_status,
            build_card=build_card,
            selected_block_var=selected_block_var,
            selected_block_internal_var=selected_block_internal_var,
            selected_block_type_var=selected_block_type_var,
            block_icon_label=block_icon_label,
            block_path_label=block_path_label,
            research_items_var=research_items_var,
            on_block_selected_callback=None
        )

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

        # === Основная функция создания моста ===
        def process_bridge():
            original_name = entry_name.get().strip()
            
            if not original_name:
                status_label.configure(
                    text="❌ Ошибка: Введите название конвеера!", 
                    text_color="#F44336"
                )
                return
            
            # Проверка для always_unlocked = false
            is_valid, error_msg = self.validate_research(
                always_unlocked_var=always_unlocked_var,
                research_items=self.research_items if hasattr(self, 'research_items') else [],
                selected_block_internal_var=selected_block_internal_var
            )
            
            if not is_valid:
                status_label.configure(text=error_msg, text_color="#F44336")
                return
            
            if not hasattr(self, 'build_items') or not self.build_items:
                status_label.configure(
                    text="❌ Ошибка: Выберите предметы для строительства!", 
                    text_color="#F44336"
                )
                return
            
            # Форматируем имя
            constructor_name = self.format_to_lower_camel(original_name)
            if not constructor_name:
                status_label.configure(
                    text="❌ Ошибка: Некорректное название!", 
                    text_color="#F44336"
                )
                return

            # Проверяем, существует ли уже такое имя
            if self.check_block_name_exists(original_name, PATEH_FOLDER):
                status_label.configure(
                    text=f"❌ Ошибка: Имя '{constructor_name}' уже используется!", 
                    text_color="#F44336"
                )
                return
            
            # Копируем текстуры (для моста их 4)
            texture_configs = [
                # Группа 0
                {"template": CONVEYOR00, "suffix": "-0-0"},
                {"template": CONVEYOR01, "suffix": "-0-1"},
                {"template": CONVEYOR02, "suffix": "-0-2"},
                {"template": CONVEYOR03, "suffix": "-0-3"},
                
                # Группа 1
                {"template": CONVEYOR10, "suffix": "-1-0"},
                {"template": CONVEYOR11, "suffix": "-1-1"},
                {"template": CONVEYOR12, "suffix": "-1-2"},
                {"template": CONVEYOR13, "suffix": "-1-3"},
                
                # Группа 2
                {"template": CONVEYOR20, "suffix": "-2-0"},
                {"template": CONVEYOR21, "suffix": "-2-1"},
                {"template": CONVEYOR22, "suffix": "-2-2"},
                {"template": CONVEYOR23, "suffix": "-2-3"},
                
                # Группа 3
                {"template": CONVEYOR30, "suffix": "-3-0"},
                {"template": CONVEYOR31, "suffix": "-3-1"},
                {"template": CONVEYOR32, "suffix": "-3-2"},
                {"template": CONVEYOR33, "suffix": "-3-3"},
                
                # Группа 4
                {"template": CONVEYOR40, "suffix": "-4-0"},
                {"template": CONVEYOR41, "suffix": "-4-1"},
                {"template": CONVEYOR42, "suffix": "-4-2"},
                {"template": CONVEYOR43, "suffix": "-4-3"},
            ]
            
            texture_copied = self.copy_block_textures_multi(
                block_name=original_name,
                size_multiplier=1,
                target_folder=FOLDER,
                texture_configs=texture_configs
            )
            texture_status = "✅ Текстуры созданы" if texture_copied else "⚠️ Текстуры не созданы"
            
            # Получаем значения свойств
            hp_value = entry_hp.get().strip() or "400"
            speed_raw = entry_speed.get().strip() or "1"
            items_per_second_raw_no = entry_items_per_second.get().strip() or "5"
            capacity_raw = entry_capacity.get().strip() or "3"

            items_per_second_raw = float(items_per_second_raw_no) / 60
            
            hp_value = str(int(float(hp_value)))
            always_unlocked_value = "true" if always_unlocked_var.get() else "false"
            
            # Получаем кастомные предметы
            custom_items = self.get_custom_items()
            var_name = constructor_name
            
            # Формируем код для предметов строительства
            build_itemstack_code = ""
            build_items_list = []
            if hasattr(self, 'build_items') and self.build_items:
                item_counts = {}
                for item in self.build_items:
                    item_counts[item] = item_counts.get(item, 0) + 1
                
                item_parts = []
                for item_name, count in item_counts.items():
                    code_name = self.get_item_code_name(item_name, custom_items)
                    item_parts.append(f"{code_name}, {count}")
                    build_items_list.append((item_name, count))
                
                build_itemstack_code = f"\n            requirements(Category.{CATEDOR},\n                ItemStack.with({', '.join(item_parts)}));"
            
            # Формируем свойства моста
            properties = f"""    health = {hp_value};
                size = 1;
                buildTime = {speed_raw};
                alwaysUnlocked = {always_unlocked_value};
                buildVisibility = BuildVisibility.shown;
                category = Category.{CATEDOR};{build_itemstack_code}
                speed = {items_per_second_raw}f;
                displayedSpeed = {items_per_second_raw_no};
                itemCapacity = {capacity_raw};

                localizedName = Core.bundle.get("{var_name}.name", "OH NO");
                description = Core.bundle.get("{var_name}.description", "OH NO");"""
            
            # Пути к файлам
            mod_name_lower = self.mod_name.lower() if self.mod_name else self.mod_name
            block_registration_path = self.get_absolute_path(f"src/{mod_name_lower}/init/blocks/{FOLDER}/{NAME}.java")
            main_mod_path = Path(self.mod_folder) / "src" / mod_name_lower / f"{self.mod_name}JavaMod.java"
            
            # Создаем родительскую папку
            block_registration_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Читаем или создаем файл регистрации блоков
            try:
                with open(block_registration_path, 'r', encoding='utf-8') as file:
                    content = file.read()
            except FileNotFoundError:
                content = f"""package {mod_name_lower}.init.blocks.{FOLDER};

import arc.graphics.Color;
import arc.Core;
import mindustry.type.ItemStack;
import mindustry.type.Category;
import mindustry.world.Block;
import mindustry.world.blocks.{CATEDOR}.{CATENAME};
import mindustry.world.meta.BuildVisibility;
import mindustry.content.Items;
import mindustry.Vars;
import {mod_name_lower}.init.items.ModItems;

public class {NAME} {{
    public static {CATENAME};
                                                
    public static void Load() {{
        // Регистрация блоков
    }}
}}"""
            
            bridge_exists = var_name in content
            tree_file_created = False
            main_file_updated = False
            
            if not bridge_exists:
                # Добавляем переменную блока
                if f"public static {CATENAME};" in content:
                    content = content.replace(
                        f"public static {CATENAME};",
                        f"public static {CATENAME} {var_name};"
                    )
                elif f"public static {CATENAME} " in content:
                    lines = content.split('\n')
                    for i, line in enumerate(lines):
                        if f"public static {CATENAME} " in line and var_name not in line:
                            lines[i] = line.rstrip(';') + f", {var_name};"
                            content = '\n'.join(lines)
                            break
                
                # Добавляем инициализацию блока
                load_start = content.find("public static void Load() {")
                if load_start != -1:
                    open_brace = content.find('{', load_start)
                    if open_brace != -1:
                        insert_pos = open_brace + 1
                        indent = "        "
                        bridge_code = f'\n{indent}{var_name} = new {CATENAME}("{constructor_name}"){{{{\n{indent}{properties}\n{indent}}}}};'
                        content = content[:insert_pos] + bridge_code + content[insert_pos:]
                
                # Сохраняем файл
                with open(block_registration_path, 'w', encoding='utf-8') as file:
                    file.write(content)
                
                # Обновляем главный файл мода
                try:
                    with open(main_mod_path, 'r', encoding='utf-8') as file:
                        main_content = file.read()
                    
                    # Добавляем импорт
                    import_statement = f"import {mod_name_lower}.init.blocks.{FOLDER}.{NAME};"
                    if import_statement not in main_content:
                        import_add_pos = main_content.find("//import_add")
                        if import_add_pos != -1:
                            insert_pos = import_add_pos + len("//import_add")
                            if insert_pos < len(main_content) and main_content[insert_pos] == '\n':
                                main_content = main_content[:insert_pos] + f"\n{import_statement}" + main_content[insert_pos:]
                            else:
                                main_content = main_content[:insert_pos] + f"\n{import_statement}" + main_content[insert_pos:]
                    
                    # Добавляем вызов Load
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
                    
                    main_file_updated = True
                    
                    # Создаем файл дерева технологий, если Always Unlocked = false
                    if not always_unlocked_var.get():
                        research_items_list = []
                        if hasattr(self, 'research_items') and self.research_items:
                            item_counts = {}
                            for item in self.research_items:
                                item_counts[item] = item_counts.get(item, 0) + 1
                            
                            for item_name, count in item_counts.items():
                                research_items_list.append((item_name, count))
                        
                        research_block = selected_block_internal_var.get()
                        
                        # Используем универсальную функцию
                        tree_file_created = self.create_tech_tree_file_universal(
                            block_var_name=var_name,
                            block_constructor_name=constructor_name,
                            research_block=research_block,
                            research_items=research_items_list,
                            block_type="conveyor",
                            folder_name=FOLDER,
                            class_name="ConveyorTree"
                        )
                        
                        if tree_file_created:
                            self.update_main_mod_file_universal(
                                import_path=f"{mod_name_lower}.content.ConveyorTree",
                                load_statement="ConveyorTree.Load();"
                            )
                    
                    # Формируем сообщение о результате
                    status_messages = [
                        f"✅ {BL_NAME_2} '{var_name}' успешно создан!",
                        f'📝 Имя в игре: "{constructor_name}"',
                        f"{texture_status}",
                    ]
                    
                    # Добавляем информацию о Always Unlocked
                    if always_unlocked_var.get():
                        status_messages.append("🔓 Always Unlocked: ДА (доступен с самого начала)")
                    else:
                        status_messages.append("🔒 Always Unlocked: НЕТ (требуется исследование)")
                    
                    status_messages.extend([
                        f"📊 Свойства {BL_NAME}:",
                        f"  • ❤️ Здоровье: {hp_value}",
                        f"  • ⚡ Скорость стройки: {speed_raw}",
                        f"  • 📦 Предметов/сек: {items_per_second_raw}",
                        f"  • 💾 Вместимость: {capacity_raw}"
                    ])
                    
                    if build_items_list:
                        items_list = []
                        for item_name, count in build_items_list:
                            if item_name in custom_items:
                                items_list.append(f"ModItems.{item_name} ×{count}")
                            else:
                                display_name = item_name.replace('-', ' ').title()
                                items_list.append(f"{display_name} ×{count}")
                        
                        status_messages.append(f"  • 🔨 Стройка: {', '.join(items_list)}")
                    
                    if not always_unlocked_var.get():
                        if hasattr(self, 'research_items') and self.research_items:
                            research_list = []
                            item_counts = {}
                            for item in self.research_items:
                                item_counts[item] = item_counts.get(item, 0) + 1
                            
                            for item_name, count in item_counts.items():
                                if item_name in custom_items:
                                    research_list.append(f"ModItems.{item_name} ×{count}")
                                else:
                                    display_name = item_name.replace('-', ' ').title()
                                    research_list.append(f"{display_name} ×{count}")
                            
                            status_messages.append(f"  • 💰 Исследование: {', '.join(research_list)}")
                        
                        status_messages.append(f"  • 🎯 Блок исследования: {selected_block_var.get()}")
                        
                        if tree_file_created:
                            status_messages.append(f"  • 🌳 ConveyorTree.java создан и добавлен в main (ConveyorTree.Load())")
                        else:
                            status_messages.append(f"  • ⚠️ ConveyorTree.java не создан")
                    
                    if main_file_updated:
                        status_messages.append(f"  • 📄 Главный файл мода обновлен")
                    
                    status_text = "\n".join(status_messages)
                    status_label.configure(text=status_text, text_color="#4CAF50")
                    
                except Exception as e:
                    status_label.configure(text=f"❌ Ошибка: {str(e)}", text_color="#F44336")
                    import traceback
                    traceback.print_exc()
            else:
                status_label.configure(text=f"⚠️ {BL_NAME_2} '{var_name}' уже существует", text_color="#FF9800")
            
            self.root.after(5000, lambda: status_label.configure(text=""))

        # === Кнопки действий ===
        buttons_frame = ctk.CTkFrame(button_frame, fg_color="transparent")
        buttons_frame.pack(pady=10)
        
        ctk.CTkButton(
            buttons_frame,
            text=f"Создать {BL_CR_NAME}",
            command=process_bridge,
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
        
        # Инициализация переменных
        self.build_items = []
        self.research_items = []

#----------ФУНКЦИИ 2----------
    def open_editor_with_target(self, selected_var, item_type, target):
        """
        Открывает редактор выбора предметов/жидкостей с указанием количества
        target: "consume_items", "consume_liquids", "output_items", "output_liquids"
        """
        # Сохраняем информацию о том, куда сохранять результат
        self.current_editor_target = target
        self.current_editor_var = selected_var
        self.current_editor_type = item_type
        
        # Создаем окно редактора
        editor_window = ctk.CTkToplevel(self.root)
        
        if item_type == "item":
            if "consume" in target:
                editor_window.title("Выбор предметов для потребления")
            else:
                editor_window.title("Выбор предметов на выходе")
            title = "Выберите предметы и количество"
        else:  # "liquid"
            if "consume" in target:
                editor_window.title("Выбор жидкостей для потребления")
            else:
                editor_window.title("Выбор жидкостей на выходе")
            title = "Выберите жидкости и количество"
        
        editor_window.geometry("650x500")
        editor_window.configure(fg_color="#2b2b2b")
        editor_window.transient(self.root)
        editor_window.grab_set()
        
        main_frame = ctk.CTkFrame(editor_window, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        ctk.CTkLabel(
            main_frame,
            text=title,
            font=("Arial", 16, "bold"),
            text_color="#FFFFFF"
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
        
        # Определяем какие элементы показывать
        items_to_show = []
        custom_elements = {}
        
        if item_type == "item":
            # Получаем предметы (ванильные + кастомные)
            items_to_show = self.default_items.copy()
            custom_items = {}
            
            # Добавляем кастомные предметы
            mod_name_lower = self.mod_name.lower() if self.mod_name else self.mod_name
            items_file_path = Path(self.mod_folder) / "src" / mod_name_lower / "init" / "items" / "ModItems.java"
            
            if items_file_path.exists():
                try:
                    with open(items_file_path, 'r', encoding='utf-8') as file:
                        content = file.read()
                    pattern = r'public\s+static\s+Item\s+(\w+);'
                    matches = re.findall(pattern, content)
                    for item_name in matches:
                        if item_name and item_name not in items_to_show:
                            items_to_show.append(item_name)
                            custom_items[item_name] = True
                except Exception:
                    pass
            
            custom_elements = custom_items
            icon_dir = "items"
            
        else:  # "liquid"
            # Получаем жидкости (ванильные + кастомные)
            items_to_show = self.default_liquids.copy()
            custom_liquids = {}
            
            # Добавляем кастомные жидкости
            mod_name_lower = self.mod_name.lower() if self.mod_name else self.mod_name
            liquids_file_path = Path(self.mod_folder) / "src" / mod_name_lower / "init" / "liquids" / "ModLiquids.java"
            
            if liquids_file_path.exists():
                try:
                    with open(liquids_file_path, 'r', encoding='utf-8') as file:
                        content = file.read()
                    pattern = r'public\s+static\s+Liquid\s+(\w+);'
                    matches = re.findall(pattern, content)
                    for liquid_name in matches:
                        if liquid_name and liquid_name not in items_to_show:
                            items_to_show.append(liquid_name)
                            custom_liquids[liquid_name] = True
                except Exception:
                    pass
            
            custom_elements = custom_liquids
            icon_dir = "liquids"
        
        checkbox_vars = {}
        amount_vars = {}
        selected_count = tk.IntVar(value=0)
        
        def create_item_row(item_name):
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
                command=on_checkbox_change,
                fg_color="#4CAF50",
                hover_color="#45a049"
            ).grid(row=0, column=0, padx=(5, 10))
            
            # Иконка
            icon_frame = ctk.CTkFrame(row_frame, fg_color="transparent", width=32, height=32)
            icon_frame.grid(row=0, column=1, padx=5)
            icon_frame.pack_propagate(False)
            
            try:
                is_custom = item_name in custom_elements
                
                if is_custom:
                    item_name_lower = item_name.lower()
                    if item_type == "item":
                        icon_paths = [
                            Path(self.mod_folder) / "assets" / "sprites" / "items" / f"{item_name_lower}.png",
                            Path(self.mod_folder) / "sprites" / "items" / f"{item_name_lower}.png",
                        ]
                    else:  # liquid
                        icon_paths = [
                            Path(self.mod_folder) / "assets" / "sprites" / "liquids" / f"{item_name_lower}.png",
                            Path(self.mod_folder) / "sprites" / "liquids" / f"{item_name_lower}.png",
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
                        if item_type == "item":
                            ctk.CTkLabel(icon_frame, text="📦", font=("Arial", 14)).pack()
                        else:
                            ctk.CTkLabel(icon_frame, text="💧", font=("Arial", 14)).pack()
                else:
                    icon_path = Path("creator/icons") / icon_dir / f"{item_name.lower()}.png"
                    if icon_path.exists():
                        img = Image.open(icon_path)
                        img = img.resize((32, 32), Image.Resampling.LANCZOS)
                        ctk_img = ctk.CTkImage(img, size=(32, 32))
                        ctk.CTkLabel(icon_frame, image=ctk_img, text="").pack()
                    else:
                        # Эмодзи для стандартных элементов
                        if item_type == "item":
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
                        else:  # liquid
                            emoji = "💧"
                            if item_name == "water": emoji = "💧"
                            elif item_name == "slag": emoji = "🌋"
                            elif item_name == "oil": emoji = "🛢️"
                            elif item_name == "cryofluid": emoji = "❄️"
                        
                        ctk.CTkLabel(icon_frame, text=emoji, font=("Arial", 14)).pack()
            except Exception:
                ctk.CTkLabel(icon_frame, text="📦" if item_type == "item" else "💧", font=("Arial", 14)).pack()
            
            # Имя
            if item_type == "item":
                display_name = f"ModItems.{item_name}" if item_name in custom_elements else item_name.replace("-", " ").title()
            else:
                display_name = f"ModLiquids.{item_name}" if item_name in custom_elements else item_name.capitalize()
            
            ctk.CTkLabel(
                row_frame,
                text=display_name,
                font=("Arial", 12),
                width=150,
                anchor="w",
                text_color="#FFFFFF"
            ).grid(row=0, column=2, padx=5)
            
            if item_name in custom_elements:
                ctk.CTkLabel(
                    row_frame,
                    text="(Мод)",
                    font=("Arial", 10),
                    text_color="#4CAF50",
                    width=40
                ).grid(row=0, column=3, padx=5)
            
            # Поле для ввода количества
            amount_frame = ctk.CTkFrame(row_frame, fg_color="transparent")
            amount_frame.grid(row=0, column=4, padx=5)
            
            ctk.CTkLabel(
                amount_frame,
                text="Кол-во:",
                font=("Arial", 10),
                text_color="#FF9800" if item_type == "item" else "#2196F3"
            ).pack(side="left", padx=(0, 5))
            
            amount_var = tk.StringVar(value="1")
            amount_vars[item_name] = amount_var
            
            def validate_amount(value):
                if value == "":
                    return True
                if not value.isdigit():
                    return False
                return int(value) <= 99999
            
            vcmd_amount = (editor_window.register(validate_amount), '%P')
            
            amount_entry = ctk.CTkEntry(
                amount_frame,
                textvariable=amount_var,
                width=60,
                font=("Arial", 10),
                justify="center",
                validate="key",
                validatecommand=vcmd_amount,
                fg_color="#424242",
                border_color="#555555",
                text_color="#FFFFFF"
            )
            amount_entry.pack(side="left")
            
            ctk.CTkLabel(
                amount_frame,
                text="ед",
                font=("Arial", 10),
                text_color="#888888"
            ).pack(side="left", padx=(5, 0))
        
        # Создаем элементы
        for item in items_to_show:
            create_item_row(item)
        
        items_frame.update_idletasks()
        canvas.configure(scrollregion=canvas.bbox("all"))
        
        # Счетчик
        counter_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        counter_frame.pack(fill="x", pady=(10, 5))
        
        count_label = ctk.CTkLabel(
            counter_frame,
            textvariable=tk.StringVar(value=f"Выбрано: 0 {'предметов' if item_type == 'item' else 'жидкостей'}"),
            font=("Arial", 12, "bold"),
            text_color="#4CAF50"
        )
        count_label.pack()
        
        def update_counter(*args):
            count_label.configure(text=f"Выбрано: {selected_count.get()} {'предметов' if item_type == 'item' else 'жидкостей'}")
        
        selected_count.trace_add("write", update_counter)
        update_counter()
        
        # Кнопки
        button_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        button_frame.pack(fill="x", pady=(10, 0))
        
        def save_selection():
            selected_items = []
            
            # Собираем выбранные элементы с количеством
            for item_name, checkbox_var in checkbox_vars.items():
                if checkbox_var.get():
                    try:
                        amount = float(amount_vars[item_name].get() or "1")
                        if amount > 0:
                            selected_items.append((item_name, amount))
                    except ValueError:
                        selected_items.append((item_name, 1.0))
            
            # Сохраняем в соответствующую переменную
            if target == "consume_items":
                self.consume_items_with_amount = selected_items
            elif target == "consume_liquids":
                self.consume_liquids_with_amount = selected_items
            elif target == "output_items":
                self.output_items_with_amount = selected_items
            elif target == "output_liquids":
                self.output_liquids_with_amount = selected_items
            
            # Формируем текст для отображения
            if selected_items:
                items_list = []
                for item_name, amount in selected_items:
                    if item_name in custom_elements:
                        if item_type == "item":
                            items_list.append(f"ModItems.{item_name} ×{int(amount)}")
                        else:
                            items_list.append(f"ModLiquids.{item_name} ×{int(amount)}")
                    else:
                        if item_type == "item":
                            display_name = item_name.replace("-", " ").title()
                        else:
                            display_name = item_name.capitalize()
                        items_list.append(f"{display_name} ×{int(amount)}")
                
                display_text = f"Выбрано: {len(selected_items)} {'предметов' if item_type == 'item' else 'жидкостей'} ({', '.join(items_list[:2])})"
                if len(items_list) > 2:
                    display_text += "..."
            else:
                display_text = f"Выбрано: 0 {'предметов' if item_type == 'item' else 'жидкостей'}"
            
            # Обновляем текст на кнопке
            selected_var.set(display_text)
            
            # Очищаем информацию о редакторе
            self.current_editor_target = None
            self.current_editor_var = None
            self.current_editor_type = None
            
            editor_window.destroy()
        
        def cancel_selection():
            # Очищаем информацию о редакторе
            self.current_editor_target = None
            self.current_editor_var = None
            self.current_editor_type = None
            editor_window.destroy()
        
        ctk.CTkButton(
            button_frame,
            text="💾 Сохранить", 
            width=140,
            height=35,
            font=("Arial", 13),
            fg_color="#2E7D32",
            hover_color="#1B5E20",
            command=save_selection
        ).pack(side="left", padx=20)
        
        ctk.CTkButton(
            button_frame,
            text="❌ Отмена", 
            width=140,
            height=35,
            font=("Arial", 13),
            fg_color="#f44336", 
            hover_color="#d32f2f",
            command=cancel_selection
        ).pack(side="left", padx=20)
        
        def on_closing():
            cancel_selection()
        
        editor_window.protocol("WM_DELETE_WINDOW", on_closing)

    def open_block_selector(self, display_var, internal_var, type_var, icon_label, path_label, icon_path_var=None):
        """Открывает окно выбора блока для исследования
        icon_path_var: опциональная переменная для хранения пути к текстуре блока"""
        selector_window = ctk.CTkToplevel(self.root)
        selector_window.title("Выбор блока для исследования")
        selector_window.geometry("900x700")
        selector_window.configure(fg_color="#2b2b2b")
        selector_window.transient(self.root)
        selector_window.grab_set()
        
        main_frame = ctk.CTkFrame(selector_window, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        ctk.CTkLabel(
            main_frame,
            text="Выберите блок, который нужно исследовать для открытия",
            font=("Arial", 16, "bold")
        ).pack(pady=(0, 15))
        
        # Поисковая строка
        search_frame = ctk.CTkFrame(main_frame, fg_color="#363636", corner_radius=8)
        search_frame.pack(fill="x", pady=(0, 10))
        
        ctk.CTkLabel(search_frame, text="🔍", font=("Arial", 14)).pack(side="left", padx=10)
        
        search_var = tk.StringVar()
        search_entry = ctk.CTkEntry(
            search_frame,
            textvariable=search_var,
            placeholder_text="Поиск блока...",
            height=35,
            fg_color="#424242",
            border_width=0
        )
        search_entry.pack(side="left", fill="x", expand=True, padx=(0, 10), pady=5)
        
        # Создаем Notebook для вкладок
        notebook = ctk.CTkTabview(
            main_frame,
            width=860,
            height=520,
            fg_color="#363636",
            segmented_button_fg_color="#404040",
            segmented_button_selected_color="#4CAF50"
        )
        notebook.pack(fill="both", expand=True)
        
        # Вкладки
        mod_tab = notebook.add("📦 Блоки мода")
        vanilla_tab = notebook.add("🎮 Ванильные блоки")
        
        # Получаем блоки мода один раз
        mod_blocks = self.get_mod_blocks_for_research_universal()
        
        # ЧЕРНЫЙ СПИСОК БЛОКОВ - блоки, которые нужно исключить из отображения
        blacklist_blocks = [
            "beam-node", "shielded-wall",
            "conveyor-0-0", "conveyor-0-1", "conveyor-0-2", "conveyor-0-3",
            "conveyor-1-0", "conveyor-1-1", "conveyor-1-2", "conveyor-1-3",
            "conveyor-2-0", "conveyor-2-1", "conveyor-2-2", "conveyor-2-3",
            "conveyor-3-0", "conveyor-3-1", "conveyor-3-2", "conveyor-3-3",
            "conveyor-4-0", "conveyor-4-1", "conveyor-4-2", "conveyor-4-3",
        ]
        
        # Черный список для текстур, которые нужно исключить
        blacklist_suffixes = [
            "-top", "-bottom", "-left", "-right", "-back", "-front",
            "-glow", "-overlay", "-mask", "-shadow", "-effect",
            "-top-1", "-top-2", "-top-3", "-cap", "-liquid",
            "-bottom-1", "-bottom-2", "-turbine",
            "-edge", "-corner", "-middle",
            "-1", "-2", "-3", "-4", "-5",
            "-a", "-b", "-c", "-d",
            "_top", "_bottom", "_left", "_right",
            "_glow", "_overlay", "_mask",
            "_1", "_2", "_3", "_4", "_5",
        ]
        
        # Список исключений - файлы, которые не являются блоками
        blacklist_exact = [
            "item-", "liquid-", "ui-", "icon-",
            "background", "white", "black", "transparent",
            "error", "missing", "unknown", "empty",
            "block-icon", "block-background",
        ]
        
        def kebab_to_camel(name):
            """
            Преобразует kebab-case в camelCase
            Пример: copper-wall -> copperWall
                    phase-wall-large -> phaseWallLarge
                    surge-wall-huge -> surgeWallHuge
            """
            if not name:
                return name
            
            # Разделяем по дефисам
            parts = name.split('-')
            
            # Первая часть остается как есть, остальные с заглавной буквы
            result = parts[0]
            for part in parts[1:]:
                if part:  # Проверяем, что часть не пустая
                    result += part.capitalize()
            
            return result
        
        # Сканируем папку blocks для ванильных текстур
        vanilla_blocks = []
        blocks_dir = Path(resource_path("creator/icons/blocks"))
        
        if blocks_dir.exists():
            print(f"Сканируем папку: {blocks_dir}")
            
            # Получаем все PNG файлы в папке blocks
            all_textures = list(blocks_dir.glob("*.png"))
            
            # Фильтруем и создаем список блоков
            for texture_path in all_textures:
                filename = texture_path.stem  # Имя без расширения
                
                # Проверка на черный список блоков
                if filename in blacklist_blocks:
                    #print(f"Блок {filename} в черном списке - пропускаем")
                    continue
                
                # Проверяем на частичное совпадение с черным списком
                if any(block in filename for block in blacklist_blocks if block in filename):
                    skip = False
                    for block in blacklist_blocks:
                        if block in filename and len(block) > 3:  # Игнорируем слишком короткие
                            skip = True
                            #print(f"Блок {filename} содержит {block} из черного списка - пропускаем")
                            break
                    if skip:
                        continue
                
                # Проверяем на черный список по суффиксам
                if any(filename.endswith(suffix) for suffix in blacklist_suffixes):
                    #print(f"Блок {filename} имеет исключаемый суффикс - пропускаем")
                    continue
                
                # Проверяем на точное совпадение с исключениями
                if any(filename.startswith(exact) or filename == exact for exact in blacklist_exact):
                    #print(f"Блок {filename} в списке исключений - пропускаем")
                    continue
                
                # Игнорируем файлы, которые явно не являются блоками
                if len(filename) < 3:  # Слишком короткие имена
                    continue
                
                # Создаем красивое отображаемое имя
                display_name = filename.replace("-", " ").replace("_", " ").title()
                
                # Определяем тип блока для иконки (для эмодзи)
                if "wall" in filename.lower():
                    block_emoji = "🧱"
                    block_type = "wall"
                elif "generator" in filename.lower() or "reactor" in filename.lower():
                    block_emoji = "⚡"
                    block_type = "power"
                elif "battery" in filename.lower():
                    block_emoji = "🔋"
                    block_type = "battery"
                elif "solar" in filename.lower():
                    block_emoji = "☀️"
                    block_type = "solar"
                elif "node" in filename.lower() or "beam" in filename.lower():
                    block_emoji = "📡"
                    block_type = "node"
                elif "conveyor" in filename.lower() or "conduit" in filename.lower():
                    block_emoji = "🔄"
                    block_type = "transport"
                elif "drill" in filename.lower():
                    block_emoji = "⛏️"
                    block_type = "drill"
                elif "factory" in filename.lower() or "press" in filename.lower():
                    block_emoji = "🏭"
                    block_type = "factory"
                else:
                    block_emoji = "🧱"
                    block_type = "other"
                
                # Преобразуем kebab-case в camelCase для внутреннего имени
                internal_name = kebab_to_camel(filename)
                
                vanilla_blocks.append((
                    internal_name,          # Внутреннее имя в camelCase
                    display_name,           # Отображаемое имя
                    block_type,              # Тип блока
                    filename,                # Имя файла иконки (оригинальное)
                    block_emoji               # Эмодзи для отображения
                ))
            
            # Сортируем по имени
            vanilla_blocks.sort(key=lambda x: x[1])
            #print(f"Найдено {len(vanilla_blocks)} ванильных блоков")
            #print("Примеры преобразования имен:")
            #for i, (internal, display, _, original, _) in enumerate(vanilla_blocks[:5]):
                #print(f"  {original} -> {internal} (для Blocks.{internal})")
        else:
            print(f"Папка {blocks_dir} не найдена")
        
        def select_block(display_name, internal_name, block_type, icon_name="", block_emoji="🧱"):
            display_var.set(display_name)
            internal_var.set(internal_name)
            type_var.set(block_type)
            
            # Сохраняем путь к иконке, если передан параметр
            if icon_path_var and icon_name:
                icon_path_var.set(icon_name)
            
            # Обновляем иконку и информацию
            if block_type == "mod":
                icon_label.configure(text="📦")
                path_label.configure(text="Модовый блок")
            else:
                icon_label.configure(text=block_emoji)
                path_label.configure(text="Ванильный блок")
            
            selector_window.destroy()
        
        def load_block_icon(icon_frame, block_name, block_type, icon_name="", block_emoji="🧱", folder_type=None):
            """Загружает иконку блока"""
            try:
                icon_path = None
                
                if block_type == "mod":
                    # Для модовых блоков
                    if folder_type:
                        # Ищем в указанной папке
                        search_folders = [folder_type]
                    else:
                        # Ищем во всех папках
                        search_folders = [
                            "walls", "batterys", "solar_panels", 
                            "consume_generators", "beam_nodes", 
                            "power_nodes", "shield_walls", "bridges",
                            "generic_crafters"
                        ]
                    
                    # Ищем в двух вариантах путей
                    for folder in search_folders:
                        # Первый вариант: напрямую в папке
                        test_path1 = Path(self.mod_folder) / "assets" / "sprites" / "blocks" / folder / f"{block_name}.png"
                        # Второй вариант: в подпапке с именем блока
                        test_path2 = Path(self.mod_folder) / "assets" / "sprites" / "blocks" / folder / block_name / f"{block_name}.png"
                        
                        if test_path1.exists():
                            icon_path = test_path1
                            break
                        elif test_path2.exists():
                            icon_path = test_path2
                            break
                else:
                    # Для ванильных блоков используем имя иконки (оригинальное имя файла)
                    icon_filename = icon_name if icon_name else block_name
                    
                    # Проверяем в creator/icons/blocks
                    test_path = Path(resource_path("Creator/icons/blocks")) / f"{icon_filename}.png"
                    if test_path.exists():
                        icon_path = test_path
                    else:
                        # Пробуем разные варианты
                        variants = [
                            icon_filename,
                            icon_filename.replace("-", ""),
                            icon_filename.replace("-large", "Large"),
                            icon_filename.replace("-huge", "Huge"),
                            icon_filename.lower()
                        ]
                        for variant in variants:
                            test_path = Path(resource_path("Creator/icons/blocks")) / f"{variant}.png"
                            if test_path.exists():
                                icon_path = test_path
                                break
                
                if icon_path and icon_path.exists():
                    img = Image.open(icon_path)
                    img = img.resize((48, 48), Image.Resampling.LANCZOS)
                    ctk_img = ctk.CTkImage(img, size=(48, 48))
                    ctk.CTkLabel(icon_frame, image=ctk_img, text="").pack(expand=True)
                else:
                    # Эмодзи по умолчанию
                    ctk.CTkLabel(icon_frame, text=block_emoji, font=("Arial", 30)).pack(expand=True)
            except Exception as e:
                print(f"Ошибка загрузки иконки для {block_name}: {e}")
                ctk.CTkLabel(icon_frame, text=block_emoji, font=("Arial", 30)).pack(expand=True)
        
        def display_blocks():
            search_text = search_var.get().lower()
            
            # Очищаем вкладки
            for widget in mod_tab.winfo_children():
                widget.destroy()
            for widget in vanilla_tab.winfo_children():
                widget.destroy()
            
            # Фильтруем блоки мода с проверкой черного списка
            filtered_mod = {}
            for block_name, (display_name, folder_type) in mod_blocks.items():
                # Проверяем, не в черном ли списке
                if block_name in blacklist_blocks:
                    continue
                
                if any(block in block_name for block in blacklist_blocks if block in block_name):
                    skip = False
                    for block in blacklist_blocks:
                        if block in block_name and len(block) > 3:
                            skip = True
                            break
                    if skip:
                        continue
                
                if search_text in display_name.lower() or search_text in block_name.lower():
                    filtered_mod[block_name] = (display_name, folder_type)
            
            # Создаем scrollable фрейм для модовых блоков
            mod_scroll = ctk.CTkScrollableFrame(mod_tab, fg_color="transparent")
            mod_scroll.pack(fill="both", expand=True, padx=5, pady=5)
            
            # Отображаем блоки мода
            if filtered_mod:
                # Создаем сетку 3 колонки
                row_frame = None
                col_count = 0
                
                for block_name, (display_name, folder_type) in filtered_mod.items():
                    if col_count % 3 == 0:
                        row_frame = ctk.CTkFrame(mod_scroll, fg_color="transparent")
                        row_frame.pack(fill="x", pady=2)
                    
                    # Карточка блока
                    block_card = ctk.CTkFrame(
                        row_frame,
                        fg_color="#404040",
                        corner_radius=8,
                        width=250,
                        height=180
                    )
                    block_card.pack(side="left", padx=5, pady=5, fill="both", expand=True)
                    block_card.pack_propagate(False)
                    
                    # Верхняя часть с иконкой
                    icon_frame = ctk.CTkFrame(block_card, fg_color="transparent", height=60)
                    icon_frame.pack(fill="x", padx=10, pady=(10, 5))
                    icon_frame.pack_propagate(False)
                    
                    # Определяем эмодзи для модового блока
                    if "wall" in folder_type.lower():
                        block_emoji = "🧱"
                    elif "generator" in folder_type.lower():
                        block_emoji = "⚡"
                    elif "battery" in folder_type.lower():
                        block_emoji = "🔋"
                    elif "solar" in folder_type.lower():
                        block_emoji = "☀️"
                    elif "node" in folder_type.lower():
                        block_emoji = "📡"
                    else:
                        block_emoji = "🧱"
                    
                    load_block_icon(icon_frame, block_name, "mod", folder_type=folder_type, block_emoji=block_emoji)
                    
                    # Название
                    ctk.CTkLabel(
                        block_card,
                        text=display_name,
                        font=("Arial", 12, "bold"),
                        text_color="#FFFFFF",
                        wraplength=230
                    ).pack(pady=(0, 2))
                    
                    # Внутреннее имя - для модовых блоков оставляем как есть
                    ctk.CTkLabel(
                        block_card,
                        text=block_name,
                        font=("Arial", 9),
                        text_color="#AAAAAA"
                    ).pack()
                    
                    # Кнопка выбора
                    ctk.CTkButton(
                        block_card,
                        text="Выбрать",
                        width=100,
                        height=30,
                        font=("Arial", 11),
                        fg_color="#4CAF50",
                        hover_color="#45a049",
                        command=lambda bn=block_name, dn=display_name: select_block(dn, bn, "mod", bn)
                    ).pack(pady=(5, 10))
                    
                    col_count += 1
            else:
                ctk.CTkLabel(
                    mod_scroll,
                    text="📭 Нет блоков по вашему запросу",
                    font=("Arial", 14),
                    text_color="#888888"
                ).pack(pady=50)
            
            # Фильтруем ванильные блоки
            filtered_vanilla = []
            for internal_name, display_name, block_type, icon_name, block_emoji in vanilla_blocks:
                if search_text in display_name.lower() or search_text in internal_name.lower() or search_text in icon_name.lower():
                    filtered_vanilla.append((internal_name, display_name, block_type, icon_name, block_emoji))
            
            # Создаем scrollable фрейм для ванильных блоков
            vanilla_scroll = ctk.CTkScrollableFrame(vanilla_tab, fg_color="transparent")
            vanilla_scroll.pack(fill="both", expand=True, padx=5, pady=5)
            
            if filtered_vanilla:
                # Создаем сетку 3 колонки
                row_frame = None
                col_count = 0
                
                for internal_name, display_name, block_type, icon_name, block_emoji in filtered_vanilla:
                    if col_count % 3 == 0:
                        row_frame = ctk.CTkFrame(vanilla_scroll, fg_color="transparent")
                        row_frame.pack(fill="x", pady=2)
                    
                    # Карточка блока
                    block_card = ctk.CTkFrame(
                        row_frame,
                        fg_color="#404040",
                        corner_radius=8,
                        width=250,
                        height=180
                    )
                    block_card.pack(side="left", padx=5, pady=5, fill="both", expand=True)
                    block_card.pack_propagate(False)
                    
                    # Верхняя часть с иконкой
                    icon_frame = ctk.CTkFrame(block_card, fg_color="transparent", height=60)
                    icon_frame.pack(fill="x", padx=10, pady=(10, 5))
                    icon_frame.pack_propagate(False)
                    
                    load_block_icon(icon_frame, internal_name, "vanilla", icon_name, block_emoji)
                    
                    # Название
                    ctk.CTkLabel(
                        block_card,
                        text=display_name,
                        font=("Arial", 12, "bold"),
                        text_color="#FFFFFF",
                        wraplength=230
                    ).pack(pady=(0, 2))
                    
                    # Внутреннее имя - теперь правильно в camelCase
                    ctk.CTkLabel(
                        block_card,
                        text=f"Blocks.{internal_name}",
                        font=("Arial", 9),
                        text_color="#AAAAAA"
                    ).pack()
                    
                    # Кнопка выбора
                    ctk.CTkButton(
                        block_card,
                        text="Выбрать",
                        width=100,
                        height=30,
                        font=("Arial", 11),
                        fg_color="#4CAF50",
                        hover_color="#45a049",
                        command=lambda iname=internal_name, dn=display_name, icn=icon_name, em=block_emoji: 
                            select_block(dn, f"Blocks.{iname}", "vanilla", icn, em)
                    ).pack(pady=(5, 10))
                    
                    col_count += 1
            else:
                ctk.CTkLabel(
                    vanilla_scroll,
                    text="🎮 Нет блоков по вашему запросу",
                    font=("Arial", 14),
                    text_color="#888888"
                ).pack(pady=50)
        
        # Привязываем поиск
        def on_search_change(*args):
            display_blocks()
        
        search_var.trace_add("write", on_search_change)
        
        # Первоначальное отображение
        display_blocks()
        
        # Кнопка отмены
        button_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        button_frame.pack(pady=10)
        
        cancel_btn = ctk.CTkButton(
            button_frame,
            text="❌ Отмена",
            width=120,
            height=35,
            font=("Arial", 12),
            fg_color="#e62525",
            hover_color="#701c1c",
            command=selector_window.destroy
        )
        cancel_btn.pack()

    def get_mod_blocks_for_research_universal(self):
        """Получает список блоков из мода для исследования с указанием типа папки"""
        mod_blocks = {}
        mod_name_lower = self.mod_name.lower() if self.mod_name else self.mod_name
        
        # Пути к файлам с блоками
        block_files = [
            ("walls", f"src/{mod_name_lower}/init/blocks/walls/Walls.java", "🧱 Стены"),
            ("solar_panels", f"src/{mod_name_lower}/init/blocks/solar_panels/SolarPanels.java", "☀️ Солнечные панели"),
            ("batterys", f"src/{mod_name_lower}/init/blocks/batterys/Batterys.java", "🔋 Батареи"),
            ("consume_generators", f"src/{mod_name_lower}/init/blocks/consume_generators/ConsumeGenerators.java", "⚡ Генераторы"),
            ("beam_nodes", f"src/{mod_name_lower}/init/blocks/beam_nodes/BeamNodes.java", "📡 Энерг. башни"),
            ("power_nodes", f"src/{mod_name_lower}/init/blocks/power_nodes/PowerNodes.java", "🔌 Энерг. узлы"),
            ("shield_walls", f"src/{mod_name_lower}/init/blocks/shield_walls/ShieldWalls.java", "🛡️ Щитовые стены"),
            ("generic_crafter", f"src/{mod_name_lower}/init/blocks/generic_crafter/GenericCrafters.java", "Заводы"),
            ("bridges", f"src/{mod_name_lower}/init/blocks/bridges/Bridges.java", "Мосты")
        ]
        
        for folder, file_path, display_prefix in block_files:
            full_path = Path(self.mod_folder) / file_path
            if full_path.exists():
                try:
                    with open(full_path, 'r', encoding='utf-8') as file:
                        content = file.read()
                    
                    # Ищем объявления блоков
                    patterns = [
                        r'public\s+static\s+\w+\s+(\w+)\s*=\s*new\s+\w+\("([^"]+)"\)',
                        r'public\s+static\s+final\s+\w+\s+(\w+)\s*=\s*new\s+\w+\("([^"]+)"\)',
                        r'(\w+)\s*=\s*new\s+\w+\("([^"]+)"\)',
                    ]
                    
                    for pattern in patterns:
                        matches = re.findall(pattern, content)
                        for match in matches:
                            if isinstance(match, tuple) and len(match) >= 2:
                                var_name = match[0]
                                internal_name = match[1]
                                if var_name and var_name not in mod_blocks:
                                    mod_blocks[var_name] = (f"{display_prefix} - {internal_name}", folder)
                            elif isinstance(match, str):
                                var_name = match
                                if var_name and var_name not in mod_blocks:
                                    mod_blocks[var_name] = (f"{display_prefix} - {var_name}", folder)
                    
                    # Ищем просто объявления переменных
                    var_pattern = r'public\s+static\s+\w+\s+(\w+);'
                    var_matches = re.findall(var_pattern, content)
                    for var_name in var_matches:
                        if var_name and var_name not in mod_blocks and var_name not in ["CATENAME", "NAME", "CATEDOR"]:
                            mod_blocks[var_name] = (f"{display_prefix} - {var_name}", folder)
                            
                except Exception as e:
                    print(f"Ошибка чтения {full_path}: {e}")
        
        return mod_blocks

    def open_items_editor(self, target_var, target_type):
        """Открывает редактор предметов для строительства или исследования"""
        editor_window = ctk.CTkToplevel(self.root)
        title = "Выбор предметов для исследования" if target_type == "research" else "Выбор предметов для строительства"
        editor_window.title(title)
        editor_window.geometry("700x600")
        editor_window.configure(fg_color="#2b2b2b")
        editor_window.transient(self.root)
        editor_window.grab_set()
        
        main_frame = ctk.CTkFrame(editor_window, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        ctk.CTkLabel(
            main_frame,
            text=title,
            font=("Arial", 16, "bold")
        ).pack(pady=(0, 15))
        
        # Поиск
        search_frame = ctk.CTkFrame(main_frame, fg_color="#363636", corner_radius=8)
        search_frame.pack(fill="x", pady=(0, 10))
        
        ctk.CTkLabel(search_frame, text="🔍", font=("Arial", 14)).pack(side="left", padx=10)
        
        search_var = tk.StringVar()
        search_entry = ctk.CTkEntry(
            search_frame,
            textvariable=search_var,
            placeholder_text="Поиск предмета...",
            height=35,
            fg_color="#424242",
            border_width=0
        )
        search_entry.pack(side="left", fill="x", expand=True, padx=(0, 10), pady=5)
        
        # Canvas для прокрутки
        canvas_frame = ctk.CTkFrame(main_frame, fg_color="#3a3a3a", corner_radius=8)
        canvas_frame.pack(fill="both", expand=True, pady=(0, 10))
        
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
                except Exception as e:
                    print(f"Ошибка чтения ModItems: {e}")
            return custom_items
        
        custom_items = get_custom_items()
        
        # Стандартные предметы
        default_items = [
            "copper", "lead", "metaglass", "graphite", "sand", "coal",
            "titanium", "thorium", "scrap", "silicon", "plastanium",
            "phase-fabric", "surge-alloy", "spore-pod", "blast-compound", "pyratite"
        ]
        
        checkbox_vars = {}
        amount_vars = {}
        selected_count = tk.IntVar(value=0)
        
        def validate_amount(value):
            if value == "":
                return True
            if not value.isdigit():
                return False
            return 1 <= int(value) <= 999
        
        vcmd_amount = (editor_window.register(validate_amount), '%P')
        
        def create_item_row(item_name, is_custom_item=False):
            row_frame = ctk.CTkFrame(items_frame, fg_color="#404040", corner_radius=6)
            row_frame.pack(fill="x", pady=2, padx=2)
            
            # Чекбокс
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
            ).grid(row=0, column=0, padx=(10, 5), pady=10)
            
            # Иконка
            icon_frame = ctk.CTkFrame(row_frame, fg_color="transparent", width=32, height=32)
            icon_frame.grid(row=0, column=1, padx=5)
            icon_frame.pack_propagate(False)
            
            try:
                if is_custom_item:
                    # Ищем иконку модового предмета
                    item_name_lower = item_name.lower()
                    icon_found = False
                    icon_paths = [
                        Path(self.mod_folder) / "assets" / "sprites" / "items" / f"{item_name_lower}.png",
                        Path(self.mod_folder) / "sprites" / "items" / f"{item_name_lower}.png",
                    ]
                    for icon_path in icon_paths:
                        if icon_path.exists():
                            img = Image.open(icon_path)
                            img = img.resize((32, 32), Image.Resampling.LANCZOS)
                            ctk_img = ctk.CTkImage(img, size=(32, 32))
                            ctk.CTkLabel(icon_frame, image=ctk_img, text="").pack()
                            icon_found = True
                            break
                    if not icon_found:
                        ctk.CTkLabel(icon_frame, text="📦", font=("Arial", 16)).pack()
                else:
                    # Иконка ванильного предмета
                    icon_path = Path(resource_path("Creator/icons/items")) / f"{item_name.lower()}.png"
                    if icon_path.exists():
                        img = Image.open(icon_path)
                        img = img.resize((32, 32), Image.Resampling.LANCZOS)
                        ctk_img = ctk.CTkImage(img, size=(32, 32))
                        ctk.CTkLabel(icon_frame, image=ctk_img, text="").pack()
                    else:
                        # Эмодзи по умолчанию
                        emoji_map = {
                            "copper": "🟫", "lead": "🔩", "metaglass": "🔮", "graphite": "⬛",
                            "sand": "🟨", "coal": "🪨", "titanium": "🔷", "thorium": "🟣",
                            "scrap": "⚙️", "silicon": "💎", "plastanium": "🟢", "phase-fabric": "🌌",
                            "surge-alloy": "⚡", "spore-pod": "🍄", "blast-compound": "💥", "pyratite": "🔥"
                        }
                        emoji = emoji_map.get(item_name, "📦")
                        ctk.CTkLabel(icon_frame, text=emoji, font=("Arial", 16)).pack()
            except Exception:
                ctk.CTkLabel(icon_frame, text="📦", font=("Arial", 16)).pack()
            
            # Название
            display_name = f"ModItems.{item_name}" if is_custom_item else item_name.replace("-", " ").title()
            ctk.CTkLabel(
                row_frame,
                text=display_name,
                font=("Arial", 13),
                width=200,
                anchor="w"
            ).grid(row=0, column=2, padx=10)
            
            if is_custom_item:
                ctk.CTkLabel(
                    row_frame,
                    text="(Мод)",
                    font=("Arial", 10),
                    text_color="#4CAF50",
                    width=40
                ).grid(row=0, column=3, padx=5)
            else:
                ctk.CTkLabel(
                    row_frame,
                    text="(Ванилла)",
                    font=("Arial", 10),
                    text_color="#FFA500",
                    width=40
                ).grid(row=0, column=3, padx=5)
            
            # Количество
            amount_var = tk.StringVar(value="1")
            amount_vars[item_name] = amount_var
            
            amount_frame = ctk.CTkFrame(row_frame, fg_color="transparent")
            amount_frame.grid(row=0, column=4, padx=10)
            
            ctk.CTkLabel(amount_frame, text="x", font=("Arial", 14)).pack(side="left")
            
            ctk.CTkEntry(
                amount_frame,
                textvariable=amount_var,
                width=50,
                height=30,
                font=("Arial", 12),
                justify="center",
                validate="key",
                validatecommand=vcmd_amount,
                fg_color="#424242",
                border_color="#555555"
            ).pack(side="left", padx=(5, 0))
        
        # Функция для фильтрации и отображения предметов
        def filter_items():
            search_text = search_var.get().lower()
            
            # Очищаем items_frame
            for widget in items_frame.winfo_children():
                widget.destroy()
            
            # Показываем стандартные предметы
            for item in default_items:
                if search_text in item.lower() or search_text in item.replace("-", " ").lower():
                    create_item_row(item, False)
            
            # Показываем кастомные предметы
            for item in custom_items:
                if search_text in item.lower():
                    create_item_row(item, True)
            
            items_frame.update_idletasks()
            canvas.configure(scrollregion=canvas.bbox("all"))
        
        # Привязываем поиск
        search_var.trace_add("write", lambda *args: filter_items())
        
        # Первоначальное отображение
        filter_items()
        
        # Счетчик выбранных предметов
        counter_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        counter_frame.pack(fill="x", pady=(5, 10))
        
        count_label = ctk.CTkLabel(
            counter_frame,
            text="Выбрано: 0 предметов",
            font=("Arial", 12, "bold"),
            text_color="#4CAF50"
        )
        count_label.pack()
        
        def update_counter(*args):
            count_label.configure(text=f"Выбрано: {selected_count.get()} предметов")
        
        selected_count.trace_add("write", update_counter)
        
        # Кнопки
        button_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        button_frame.pack(fill="x", pady=(0, 5))
        
        def save_selection():
            selected_items = []
            for item_name, checkbox_var in checkbox_vars.items():
                if checkbox_var.get():
                    try:
                        amount = int(amount_vars[item_name].get())
                        if amount < 1:
                            amount = 1
                        for _ in range(amount):
                            selected_items.append(item_name)
                    except ValueError:
                        selected_items.append(item_name)
            
            if target_type == "research":
                self.research_items = selected_items
            else:
                self.build_items = selected_items
            
            # Формируем текст для отображения
            item_counts = {}
            for item in selected_items:
                item_counts[item] = item_counts.get(item, 0) + 1
            
            items_list = []
            for item_name, count in item_counts.items():
                if item_name in custom_items:
                    items_list.append(f"ModItems.{item_name} ×{count}")
                else:
                    display_name = item_name.replace("-", " ").title()
                    items_list.append(f"{display_name} ×{count}")
            
            if items_list:
                display_text = f"Выбрано: {len(selected_items)} предметов ({', '.join(items_list[:3])})"
                if len(items_list) > 3:
                    display_text += "..."
            else:
                display_text = "Выбрано: 0 предметов"
            
            target_var.set(display_text)
            editor_window.destroy()
        
        ctk.CTkButton(
            button_frame,
            text="💾 Сохранить",
            width=140,
            height=35,
            font=("Arial", 13),
            fg_color="#2E7D32",
            hover_color="#1B5E20",
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
            command=editor_window.destroy
        ).pack(side="left", padx=20)

    def open_fuel_items_editor_with_amount(self, selected_var, fuel_type):
        """Открывает редактор выбора топлива с указанием количества потребления"""
        # Сохраняем информацию о том, какой тип топлива редактируем
        self.current_fuel_type = fuel_type
        self.current_fuel_var = selected_var
        
        # Создаем окно редактора
        editor_window = ctk.CTkToplevel(self.root)
        
        if fuel_type == "item":
            editor_window.title("Выбор предметов для топлива")
            title = "Выберите предметы и количество"
        else:  # "liquid"
            editor_window.title("Выбор жидкостей для топлива")
            title = "Выберите жидкости и количество"
        
        editor_window.geometry("650x500")
        editor_window.configure(fg_color="#2b2b2b")
        editor_window.transient(self.root)
        editor_window.grab_set()
        
        main_frame = ctk.CTkFrame(editor_window, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        ctk.CTkLabel(
            main_frame,
            text=title,
            font=("Arial", 16, "bold"),
            text_color="#FFFFFF"
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
        
        # Определяем какие элементы показывать
        items_to_show = []
        custom_elements = {}
        
        if fuel_type == "item":
            # Получаем предметы (ванильные + кастомные)
            items_to_show = self.default_items.copy()
            custom_items = {}
            
            # Добавляем кастомные предметы
            mod_name_lower = self.mod_name.lower() if self.mod_name else self.mod_name
            items_file_path = Path(self.mod_folder) / "src" / mod_name_lower / "init" / "items" / "ModItems.java"
            
            if items_file_path.exists():
                try:
                    with open(items_file_path, 'r', encoding='utf-8') as file:
                        content = file.read()
                    pattern = r'public\s+static\s+Item\s+(\w+);'
                    matches = re.findall(pattern, content)
                    for item_name in matches:
                        if item_name and item_name not in items_to_show:
                            items_to_show.append(item_name)
                            custom_items[item_name] = True
                except Exception:
                    pass
            
            custom_elements = custom_items
            icon_dir = "items"
            
        else:  # "liquid"
            # Получаем жидкости (ванильные + кастомные)
            items_to_show = self.default_liquids.copy()
            custom_liquids = {}
            
            # Добавляем кастомные жидкости
            mod_name_lower = self.mod_name.lower() if self.mod_name else self.mod_name
            liquids_file_path = Path(self.mod_folder) / "src" / mod_name_lower / "init" / "liquids" / "ModLiquids.java"
            
            if liquids_file_path.exists():
                try:
                    with open(liquids_file_path, 'r', encoding='utf-8') as file:
                        content = file.read()
                    pattern = r'public\s+static\s+Liquid\s+(\w+);'
                    matches = re.findall(pattern, content)
                    for liquid_name in matches:
                        if liquid_name and liquid_name not in items_to_show:
                            items_to_show.append(liquid_name)
                            custom_liquids[liquid_name] = True
                except Exception:
                    pass
            
            custom_elements = custom_liquids
            icon_dir = "liquids"
        
        checkbox_vars = {}
        amount_vars = {}
        selected_count = tk.IntVar(value=0)
        
        def create_item_row(item_name):
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
                command=on_checkbox_change,
                fg_color="#4CAF50",
                hover_color="#45a049"
            ).grid(row=0, column=0, padx=(5, 10))
            
            # Иконка
            icon_frame = ctk.CTkFrame(row_frame, fg_color="transparent", width=32, height=32)
            icon_frame.grid(row=0, column=1, padx=5)
            icon_frame.pack_propagate(False)
            
            try:
                is_custom = item_name in custom_elements
                
                if is_custom:
                    item_name_lower = item_name.lower()
                    if fuel_type == "item":
                        icon_paths = [
                            Path(self.mod_folder) / "assets" / "sprites" / "items" / f"{item_name_lower}.png",
                            Path(self.mod_folder) / "sprites" / "items" / f"{item_name_lower}.png",
                        ]
                    else:  # liquid
                        icon_paths = [
                            Path(self.mod_folder) / "assets" / "sprites" / "liquids" / f"{item_name_lower}.png",
                            Path(self.mod_folder) / "sprites" / "liquids" / f"{item_name_lower}.png",
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
                        if fuel_type == "item":
                            ctk.CTkLabel(icon_frame, text="📦", font=("Arial", 14)).pack()
                        else:
                            ctk.CTkLabel(icon_frame, text="💧", font=("Arial", 14)).pack()
                else:
                    icon_path = Path(resource_path("Creator/icons")) / icon_dir / f"{item_name.lower()}.png"
                    if icon_path.exists():
                        img = Image.open(icon_path)
                        img = img.resize((32, 32), Image.Resampling.LANCZOS)
                        ctk_img = ctk.CTkImage(img, size=(32, 32))
                        ctk.CTkLabel(icon_frame, image=ctk_img, text="").pack()
                    else:
                        # Эмодзи для стандартных элементов
                        if fuel_type == "item":
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
                        else:  # liquid
                            emoji = "💧"
                            if item_name == "water": emoji = "💧"
                            elif item_name == "slag": emoji = "🌋"
                            elif item_name == "oil": emoji = "🛢️"
                            elif item_name == "cryofluid": emoji = "❄️"
                        
                        ctk.CTkLabel(icon_frame, text=emoji, font=("Arial", 14)).pack()
            except Exception:
                ctk.CTkLabel(icon_frame, text="📦" if fuel_type == "item" else "💧", font=("Arial", 14)).pack()
            
            # Имя
            if fuel_type == "item":
                display_name = f"ModItems.{item_name}" if item_name in custom_elements else item_name.replace("-", " ").title()
            else:
                display_name = f"ModLiquids.{item_name}" if item_name in custom_elements else item_name.capitalize()
            
            ctk.CTkLabel(
                row_frame,
                text=display_name,
                font=("Arial", 12),
                width=150,
                anchor="w",
                text_color="#FFFFFF"
            ).grid(row=0, column=2, padx=5)
            
            if item_name in custom_elements:
                ctk.CTkLabel(
                    row_frame,
                    text="(Мод)",
                    font=("Arial", 10),
                    text_color="#4CAF50",
                    width=40
                ).grid(row=0, column=3, padx=5)
            
            # Поле для ввода количества
            amount_frame = ctk.CTkFrame(row_frame, fg_color="transparent")
            amount_frame.grid(row=0, column=4, padx=5)
            
            ctk.CTkLabel(
                amount_frame,
                text="Кол-во:",
                font=("Arial", 10),
                text_color="#FF9800" if fuel_type == "item" else "#2196F3"
            ).pack(side="left", padx=(0, 5))
            
            amount_var = tk.StringVar(value="1")
            amount_vars[item_name] = amount_var
            
            def validate_amount(value):
                if value == "":
                    return True
                if not value.isdigit():
                    return False
                return int(value) <= 99999
            
            vcmd_amount = (editor_window.register(validate_amount), '%P')
            
            amount_entry = ctk.CTkEntry(
                amount_frame,
                textvariable=amount_var,
                width=60,
                font=("Arial", 10),
                justify="center",
                validate="key",
                validatecommand=vcmd_amount,
                fg_color="#424242",
                border_color="#555555",
                text_color="#FFFFFF"
            )
            amount_entry.pack(side="left")
            
            ctk.CTkLabel(
                amount_frame,
                text="ед",
                font=("Arial", 10),
                text_color="#888888"
            ).pack(side="left", padx=(5, 0))
        
        # Создаем элементы
        for item in items_to_show:
            create_item_row(item)
        
        items_frame.update_idletasks()
        canvas.configure(scrollregion=canvas.bbox("all"))
        
        # Счетчик
        counter_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        counter_frame.pack(fill="x", pady=(10, 5))
        
        count_label = ctk.CTkLabel(
            counter_frame,
            textvariable=tk.StringVar(value=f"Выбрано: 0 {'предметов' if fuel_type == 'item' else 'жидкостей'}"),
            font=("Arial", 12, "bold"),
            text_color="#4CAF50"
        )
        count_label.pack()
        
        def update_counter(*args):
            count_label.configure(text=f"Выбрано: {selected_count.get()} {'предметов' if fuel_type == 'item' else 'жидкостей'}")
        
        selected_count.trace_add("write", update_counter)
        update_counter()
        
        # Кнопки
        button_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        button_frame.pack(fill="x", pady=(10, 0))
        
        def save_selection():
            if fuel_type == "item":
                # Сохраняем предметы для топлива с количеством
                self.fuel_items_with_amount = []
                for item_name, checkbox_var in checkbox_vars.items():
                    if checkbox_var.get():
                        try:
                            amount = float(amount_vars[item_name].get() or "1")
                            if amount > 0:
                                self.fuel_items_with_amount.append((item_name, amount))
                        except ValueError:
                            self.fuel_items_with_amount.append((item_name, 1.0))
                
                # Формируем текст для отображения
                if self.fuel_items_with_amount:
                    items_list = []
                    for item_name, amount in self.fuel_items_with_amount:
                        if item_name in custom_elements:
                            items_list.append(f"ModItems.{item_name} ×{int(amount)}")
                        else:
                            display_name = item_name.replace("-", " ").title()
                            items_list.append(f"{display_name} ×{int(amount)}")
                    
                    display_text = f"Выбрано: {len(self.fuel_items_with_amount)} предметов ({', '.join(items_list[:2])})"
                    if len(items_list) > 2:
                        display_text += "..."
                else:
                    display_text = "Выбрано: 0 предметов"
                
            else:  # "liquid"
                # Сохраняем жидкости для топлива с количеством
                self.fuel_liquids_with_amount = []
                for liquid_name, checkbox_var in checkbox_vars.items():
                    if checkbox_var.get():
                        try:
                            amount = float(amount_vars[liquid_name].get() or "1")
                            if amount > 0:
                                self.fuel_liquids_with_amount.append((liquid_name, amount))
                        except ValueError:
                            self.fuel_liquids_with_amount.append((liquid_name, 1.0))
                
                # Формируем текст для отображения
                if self.fuel_liquids_with_amount:
                    liquids_list = []
                    for liquid_name, amount in self.fuel_liquids_with_amount:
                        if liquid_name in custom_elements:
                            liquids_list.append(f"ModLiquids.{liquid_name} ×{int(amount)}")
                        else:
                            display_name = liquid_name.capitalize()
                            liquids_list.append(f"{display_name} ×{int(amount)}")
                    
                    display_text = f"Выбрано: {len(self.fuel_liquids_with_amount)} жидкостей ({', '.join(liquids_list[:2])})"
                    if len(liquids_list) > 2:
                        display_text += "..."
                else:
                    display_text = "Выбрано: 0 жидкостей"
            
            # Обновляем текст на кнопке
            selected_var.set(display_text)
            
            # Очищаем информацию о типе топлива
            self.current_fuel_type = None
            self.current_fuel_var = None
            
            editor_window.destroy()
        
        def cancel_selection():
            # Очищаем информацию о типе топлива
            self.current_fuel_type = None
            self.current_fuel_var = None
            editor_window.destroy()
        
        ctk.CTkButton(
            button_frame,
            text="💾 Сохранить", 
            width=140,
            height=35,
            font=("Arial", 13),
            fg_color="#2E7D32",
            hover_color="#1B5E20",
            command=save_selection
        ).pack(side="left", padx=20)
        
        ctk.CTkButton(
            button_frame,
            text="❌ Отмена", 
            width=140,
            height=35,
            font=("Arial", 13),
            fg_color="#f44336", 
            hover_color="#d32f2f",
            command=cancel_selection
        ).pack(side="left", padx=20)
        
        def on_closing():
            cancel_selection()
        
        editor_window.protocol("WM_DELETE_WINDOW", on_closing)

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
                    icon_path = Path(resource_path("Creator/icons/items")) / f"{item_name.lower()}.png"
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