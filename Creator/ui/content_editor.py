import customtkinter as ctk
import tkinter as tk
from tkinter import colorchooser
import json
import os, gc
import shutil
import urllib.request
import threading
import zipfile
import platform
import subprocess
from tkinter import messagebox, Menu
from PIL import Image
from utils.resource_utils import safe_navigation
from utils.lang_system import LangT
VERSION = "1.2"
class ContentEditor:
    def __init__(self, root, mod_folder, mod_name, main_app):
        self.root = root
        self.mod_folder = mod_folder
        self.mod_name = mod_name
        self.main_app = main_app
        self.is_pressed = False
        self.resize_timers = {}
        self.last_widths = {}
        self.is_resizing = False

    def clear_window(self):
        """Очистка окна"""
        for widget in self.root.winfo_children():
            widget.destroy()
    
    def setup_resize_protection(self, widget_name, callback, delay=300):
        """Настройка защиты от лагов для конкретного виджета"""
        def on_configure(event):
            if widget_name in self.resize_timers:
                self.root.after_cancel(self.resize_timers[widget_name])
                
            # Отменяем предыдущий таймер для этого виджета
            if widget_name in self.resize_timers:
                self.root.after_cancel(self.resize_timers[widget_name])
            
            # Устанавливаем новый таймер
            self.resize_timers[widget_name] = self.root.after(delay, callback)
        
        return on_configure

    def bind_mouse_events(self):
        """Привязка событий мыши для определения ресайза"""
        def on_press(event):
            self.is_resizing = True
        
        def on_release(event):
            self.is_resizing = False
            # Принудительно обновляем после отпускания мыши
            self.force_update_all()
        
        self.root.bind("<ButtonPress-1>", on_press)
        self.root.bind("<ButtonRelease-1>", on_release)

    def force_update_all(self):
        """Принудительное обновление всех отложенных обновлений"""
        for timer_id in self.resize_timers.values():
            try:
                self.root.after_cancel(timer_id)
            except:
                pass
        
        # Вызываем все отложенные callback'и
        for widget_name in list(self.resize_timers.keys()):
            # Здесь нужно вызвать соответствующий метод обновления
            # В зависимости от того, какой виджет активен
            pass

    def show_content_buttons(self):
        """Главное меню с просмотром контента"""
        self.clear_window()
        
        self.root.configure(fg_color="#2b2b2b")

        # Основной контейнер
        main_frame = ctk.CTkFrame(self.root, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Левая панель с кнопками действий
        left_panel = ctk.CTkFrame(main_frame, width=200, fg_color="#3a3a3a", corner_radius=8)
        left_panel.pack(side="left", fill="y", padx=(0, 10))
        left_panel.pack_propagate(False)

        # Кнопки в левой панели
        action_buttons = [
            (LangT("🧱 Создать блок"), lambda: self.main_app.show_block_creator()),
            (LangT("📦 Создать предмет"), lambda: self.create_content_window("item")),
            (LangT("💧 Создать жидкость"), lambda: self.create_content_window("liquid"))
        ]

        action_buttons_2 = [
            (LangT("📁 Создать ZIP"), self.create_zip),
            (LangT("📂 Открыть папку"), self.open_mod_folder)
        ]

        for text, cmd in action_buttons:
            btn = ctk.CTkButton(
                left_panel,
                hover_color="#800000", border_color="#800000",
                text=text,
                width=180,
                height=40,
                font=("Arial", 14),
                anchor="w",
                command=cmd
            )
            btn.pack(pady=5, padx=10, fill="x")

        for text, cmd in action_buttons_2:
            btn = ctk.CTkButton(
                left_panel,
                hover_color="#001380", border_color="#001380",
                text=text,
                width=180,
                height=40,
                font=("Arial", 14),
                anchor="w",
                command=cmd
            )
            btn.pack(pady=5, padx=10, fill="x")

        # Основная область с контентом
        content_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        content_frame.pack(side="right", fill="both", expand=True)

        # Вкладки для разных типов контента
        self.tabs = ctk.CTkTabview(content_frame)
        self.tabs.pack(fill="both", expand=True)
        
        # Создаем вкладки
        self.tabs.add(LangT("Блоки"))
        self.tabs.add(LangT("Предметы")) 
        self.tabs.add(LangT("Жидкости"))

        # Загружаем контент для каждой вкладки
        self.load_content(LangT("Блоки"), "blocks")
        self.load_content(LangT("Предметы"), "items") 
        self.load_content(LangT("Жидкости"), "liquids")

    def delete_item(self, item, content_type):
        """Удаление элемента с очисткой всех связанных данных"""
        # Код без изменений
        sprite_type = item["type"] if content_type == "blocks" else content_type
        item_name = item["name"]
        
        texture_folder = os.path.join(self.mod_folder, "sprites", sprite_type, item_name)
        single_texture = os.path.join(self.mod_folder, "sprites", sprite_type, f"{item_name}.png")
        cache_path = os.path.join("mindustry_mod_creator", "cache", f"{self.mod_name}.json")

        confirm_msg = f"{LangT("Вы уверены, что хотите удалить")} {content_type[:-1]} '{item_name}'?\n\n"
        confirm_msg += f"{LangT("• Файл данных:")} {item['full_path']}\n"
        
        if os.path.exists(texture_folder):
            confirm_msg += f"{LangT("• Будет удалена ВСЯ папка с текстурами:")} {texture_folder}\n"
        elif os.path.exists(single_texture):
            confirm_msg += f"{LangT("• Будет удален файл текстуры:")} {single_texture}\n"
        else:
            confirm_msg += LangT("• Текстуры не найдены")

        if not messagebox.askyesno(LangT("Подтверждение удаления"), confirm_msg):
            return

        try:
            # Удаляем основной файл данных
            try:
                os.remove(item["full_path"])
            except FileNotFoundError:
                pass

            # Удаляем текстуры
            try:
                if os.path.exists(texture_folder):
                    shutil.rmtree(texture_folder)
            except Exception as e:
                print(f"{LangT("Ошибка удаления папки:")} {e}")

            try:
                if os.path.exists(single_texture):
                    os.remove(single_texture)
            except FileNotFoundError:
                pass
            except Exception as e:
                print(f"{LangT("Ошибка удаления текстуры:")} {e}")

            # Чистим кэш
            item_removed = False
            if os.path.exists(cache_path):
                with open(cache_path, "r", encoding="utf-8") as f:
                    cache = json.load(f)
                
                for category in list(cache.keys()):
                    if category == "_comment":
                        continue
                    
                    if isinstance(cache[category], list) and item_name in cache[category]:
                        cache[category].remove(item_name)
                        item_removed = True
                        
                        if not cache[category]:
                            del cache[category]
                        break
                
                if item_removed:
                    with open(cache_path, "w", encoding="utf-8") as f:
                        json.dump(cache, f, indent=4, ensure_ascii=False)

            result_msg = f"{content_type[:-1]} '{item_name}' {LangT("успешно удален")}\n"
            result_msg += f"{LangT("• Все связанные текстуры удалены")}\n" if os.path.exists(texture_folder) or os.path.exists(single_texture) else ""
            
            messagebox.showinfo(LangT("Успех"), result_msg)
            safe_navigation(self.show_content_buttons)
            
        except Exception as e:
            messagebox.showerror(LangT("Ошибка"), f"{LangT("Не удалось удалить:")} {str(e)}")

    def edit_item_json(self, json_path):
        """Редактирование JSON файла"""
        if not os.path.exists(json_path):
            messagebox.showerror(LangT("Ошибка"), f"{LangT("Файл не найден:")} {json_path}")
            return
        
        with open(json_path, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                messagebox.showerror(LangT("Ошибка"), LangT("Некорректный JSON файл"))
                return
        
        # Создаем окно редактора
        editor = ctk.CTkToplevel(self.root)
        editor.title(f"{LangT("Редактор")} {os.path.basename(json_path)}")
        editor.geometry("800x600")

        editor.after(500, lambda: editor.focus_force())
        
        text_frame = ctk.CTkFrame(editor)
        text_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        text = ctk.CTkTextbox(text_frame, font=("Consolas", 12))
        text.pack(fill="both", expand=True)
        text.insert("1.0", json.dumps(data, indent=4, ensure_ascii=False))
        
        button_frame = ctk.CTkFrame(editor)
        button_frame.pack(pady=10)
        
        def save_changes():
            try:
                new_data = json.loads(text.get("1.0", tk.END))
                with open(json_path, "w", encoding="utf-8") as f:
                    json.dump(new_data, f, indent=4, ensure_ascii=False)
                messagebox.showinfo(LangT("Успех"), LangT("Изменения сохранены"))
            except Exception as e:
                messagebox.showerror(LangT("Ошибка"), f"{LangT("Не удалось сохранить:")} {str(e)}")
        
        ctk.CTkButton(button_frame, text=LangT("Сохранить"), command=save_changes).pack(side="left", padx=5)
        ctk.CTkButton(button_frame, text=LangT("Отмена"), command=editor.destroy).pack(side="left", padx=5)

    def open_mod_folder(self):
        """Открытие папки мода"""
        mods_folder = os.path.join("mindustry_mod_creator", "mods", f"{self.mod_name}")
        try:
            if not os.path.exists(mods_folder):
                messagebox.showerror(LangT("Ошибка"), f"{LangT("Папка с модами не существует:")}\n{mods_folder}")
                return
            
            if platform.system() == "Windows":
                os.startfile(mods_folder)
            elif platform.system() == "Darwin":
                subprocess.run(["open", mods_folder])
            else:  # Linux
                subprocess.run(["xdg-open", mods_folder])
                
        except Exception as e:
            messagebox.showerror(LangT("Ошибка"), f"{LangT("Не удалось открыть папку:")}\n{str(e)}")

    def create_zip(self):
        """Создание ZIP архива мода"""
        try:
            folder_path = os.path.join("mindustry_mod_creator", "mods", self.mod_name)
            zip_path = os.path.join(f"C:\\Program Files (x86)\\Steam\\steamapps\\common\\Mindustry\\saves\\mods\\{self.mod_name}.zip")

            if not os.path.exists(folder_path):
                messagebox.showerror(LangT("Ошибка"), f"{LangT("Папка мода не существует:")}\n{folder_path}")
                return None
            
            if not os.listdir(folder_path):
                messagebox.showerror(LangT("Ошибка"), f"{LangT("Папка мода пуста:")}\n{folder_path}")
                return None

            if os.path.exists(zip_path):
                try:
                    os.remove(zip_path)
                except Exception as e:
                    messagebox.showerror(LangT("Ошибка"), f"{LangT("Не удалось удалить старый архив:")}\n{str(e)}")
                    return None

            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, _, files in os.walk(folder_path):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, os.path.dirname(folder_path))
                        zipf.write(file_path, arcname)
            
            messagebox.showinfo(LangT("Успех"), f"{LangT("ZIP-архив мода создан:")}\n{zip_path}")
            return zip_path
            
        except Exception as e:
            messagebox.showerror(LangT("Ошибка"), f"{LangT("Не удалось создать архив:")}\n{str(e)}")
            return None

    def load_content(self, tab_name, content_type):
        """Загрузка и отображение контента"""
        tab = self.tabs.tab(tab_name)
        
        main_frame = ctk.CTkFrame(tab, fg_color="#2b2b2b")
        main_frame.pack(fill="both", expand=True, padx=0, pady=0)

        canvas = tk.Canvas(main_frame, bg="#2b2b2b", highlightthickness=0)
        scrollbar = ctk.CTkScrollbar(main_frame, command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)
        
        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True, padx=0, pady=0)

        content_frame = ctk.CTkFrame(canvas, fg_color="#2b2b2b")
        canvas.create_window((0, 0), window=content_frame, anchor="nw")

        items = self.get_content_items(content_type)
        
        if not items:
            ctk.CTkLabel(content_frame, text=f"{LangT("Нет")} {content_type} {LangT("в моде")}").pack(pady=20)
            return

        CARD_WIDTH = 170
        CARD_HEIGHT = 170
        MARGIN = 15

        widget_id = f"content_{content_type}"
        
        def create_card(parent, item):
            card = ctk.CTkFrame(
                parent,
                width=CARD_WIDTH,
                height=CARD_HEIGHT,
                fg_color="#3a3a3a",
                corner_radius=8,
                border_width=1,
                border_color="#4a4a4a"
            )
            card.pack_propagate(False)
            
            # Загрузка иконки
            try:
                layers = item.get("layers", [
                    ["{name}.png", 1],
                    ["{name}-rotator.png", 2],
                    ["{name}-top.png", 3]
                ])

                img = None

                if layers:
                    sorted_layers = sorted(layers, key=lambda x: x[1])
                    temp_image = None
                    
                    for layer_template, layer_number in sorted_layers:
                        layer_filename = layer_template.replace("{name}", item["name"])
                        
                        sprite_type = item.get("type", content_type)
                        possible_paths = self.generate_layer_paths(sprite_type, item["name"], layer_filename)
                        layer_img_path = self.find_image_path(possible_paths)
                        
                        if not layer_img_path:
                            continue
                            
                        try:
                            from PIL import Image
                            layer_img = Image.open(layer_img_path).convert("RGBA")
                            
                            if temp_image is None:
                                temp_image = Image.new("RGBA", layer_img.size, (0, 0, 0, 0))
                            
                            temp_image = Image.alpha_composite(temp_image, layer_img)
                            
                        except Exception as e:
                            print(f"{LangT("Ошибка обработки слоя")} {layer_filename}: {e}")
                            continue
                    
                    if temp_image is not None:
                        img = ctk.CTkImage(temp_image, size=(80, 80))
                
                if img is None:
                    sprite_type = item.get("type", content_type)
                    base_filename = f"{item['name']}.png"
                    possible_paths = self.generate_layer_paths(sprite_type, item["name"], base_filename)
                    img_path = self.find_image_path(possible_paths)
                    
                    if img_path:
                        img = self.create_ctk_image(img_path)

            except Exception as e:
                print(f"{LangT("Критическая ошибка загрузки изображения для")} {item.get('name', 'unknown')}: {e}")
                img = None
            
            ctk.CTkLabel(card, image=img, text="X" if not img else "", 
                        font=("Arial", 40) if not img else None).pack(pady=(10, 5))
            
            if "type" in item:
                ctk.CTkLabel(card, text=item["type"], font=("Arial", 12, "bold")).pack(pady=(0, 5))
            
            ctk.CTkLabel(card, text=item["name"], font=("Arial", 12, "bold"),
                        wraplength=CARD_WIDTH-20).pack(pady=(0, 15))
            
            # Контекстное меню
            menu = Menu(self.root, tearoff=0)
            menu.add_command(label=LangT("Удалить"), command=lambda: self.delete_item(item, content_type))
            menu.add_command(label=LangT("Редактировать JSON"), command=lambda: self.edit_item_json(item["full_path"]))                   

            if content_type in ["items", "liquids"]:
                menu.add_command(label=LangT("Редактор фото"), command=lambda item=item: self.main_app.show_paint_editor(item))
            elif content_type == "blocks":
                menu.add_command(label=LangT("Редактировать исследования"), 
                                command=lambda: [setattr(self.root, 'current_block_item', item), self.edit_requirements_from_parent()])
            
            def show_menu(e):
                try: menu.tk_popup(e.x_root, e.y_root)
                finally: menu.grab_release()
            
            card.bind("<Button-3>", show_menu)
            card.bind("<Double-Button-1>", lambda e: self.edit_item_json(item["full_path"]))
            
            return card

        def place_cards():
            current_width = canvas.winfo_width()
        
            # ИЗМЕНИТЬ: Проверяем, действительно ли изменилась ширина
            if (widget_id in self.last_widths and 
                current_width == self.last_widths[widget_id] and 
                current_width > 100):
                return
                
            self.last_widths[widget_id] = current_width
            
            canvas.update_idletasks()
            width = current_width
            
            cards_per_row = max(1, width // (CARD_WIDTH + MARGIN))
            remaining_space = width - (cards_per_row * (CARD_WIDTH + MARGIN))
            
            for widget in content_frame.winfo_children():
                widget.destroy()
            
            current_row = None
            for i, item in enumerate(items):
                if i % cards_per_row == 0:
                    current_row = ctk.CTkFrame(content_frame, fg_color="transparent")
                    current_row.pack(fill="x", pady=0)
                
                card = create_card(current_row, item)
                card.pack(side="left", padx=MARGIN//2)
                
                if i % cards_per_row == cards_per_row - 1 and remaining_space > 0:
                    extra = ctk.CTkFrame(current_row, width=remaining_space, fg_color="transparent")
                    extra.pack(side="left")

            content_frame.update_idletasks()
            canvas.configure(scrollregion=canvas.bbox("all"))

        def on_canvas_configure(event):
            """Обработчик изменения размера с задержкой"""
            # Отменяем предыдущий таймер
            if hasattr(self, 'resize_timers') and widget_id in self.resize_timers:
                canvas.after_cancel(self.resize_timers[widget_id])
                
            # Устанавливаем новый таймер с задержкой 250ms
            self.resize_timers[widget_id] = canvas.after(250, place_cards)

        # Первоначальное размещение карточек
        canvas.after(100, place_cards)
            
        # Биндим событие с задержкой
        canvas.bind("<Configure>", on_canvas_configure)

    def get_content_items(self, content_type):
        """Получение списка элементов контента"""
        items = []
        content_path = os.path.join(self.mod_folder, "content", content_type)
        
        if not os.path.exists(content_path):
            return items

        if content_type == "blocks":
            for block_type in os.listdir(content_path):
                type_path = os.path.join(content_path, block_type)
                if os.path.isdir(type_path):
                    for file in os.listdir(type_path):
                        if file.endswith(".json"):
                            items.append({
                                "name": os.path.splitext(file)[0],
                                "type": block_type,
                                "full_path": os.path.join(type_path, file)
                            })
        else:
            for file in os.listdir(content_path):
                if file.endswith(".json"):
                    items.append({
                        "name": os.path.splitext(file)[0],
                        "full_path": os.path.join(content_path, file)
                    })
        
        return items

    def generate_layer_paths(self, sprite_type, item_name, layer_filename):
        """Генерация возможных путей для слоя"""
        base_paths = []
        
        if sprite_type == "conduit":
            base_paths = [
                os.path.join(self.mod_folder, "sprites", "conduit", item_name, layer_filename),
                os.path.join(self.mod_folder, "sprites", "conduit", layer_filename)
            ]
        elif sprite_type == "conveyor":
            base_paths = [
                os.path.join(self.mod_folder, "sprites", "conveyor", item_name, layer_filename),
                os.path.join(self.mod_folder, "sprites", "conveyor", layer_filename)
            ]
        else:
            base_paths = [
                os.path.join(self.mod_folder, "sprites", sprite_type, item_name, layer_filename),
                os.path.join(self.mod_folder, "sprites", sprite_type, layer_filename),
                os.path.join(self.mod_folder, "sprites", "items", item_name, layer_filename),
                os.path.join(self.mod_folder, "sprites", "items", layer_filename),
                os.path.join(self.mod_folder, "sprites", "liquids", item_name, layer_filename),
                os.path.join(self.mod_folder, "sprites", "liquids", layer_filename)
            ]
        
        base_paths.append(os.path.join(self.mod_folder, "sprites", layer_filename))
        return base_paths

    def find_image_path(self, possible_paths):
        """Поиск существующего пути изображения"""
        for path in possible_paths:
            if os.path.exists(path):
                return path
        return None

    def create_ctk_image(self, img_path, size=(80, 80)):
        """Создание CTkImage из пути"""
        if img_path and os.path.exists(img_path):
            try:
                from PIL import Image
                return ctk.CTkImage(Image.open(img_path), size=size)
            except Exception as e:
                print(f"{LangT("Ошибка загрузки изображения")} {img_path}: {e}")
        return None

    def create_content_window(self, content_type="item"):
        """Универсальная форма для создания предмета или жидкости"""
        # Код без изменений
        self.clear_window()

        config = {
            "item": {
                "title": LangT("Создание нового предмета"),
                "fields": [
                    (LangT("Название предмета"), 150),
                    (LangT("Описание"), 150),
                    (LangT("Воспламеняемость (0-1)"), 150),
                    (LangT("Взрывоопасность (0-1)"), 150),
                    (LangT("Радиоактивность (0-1)"), 150),
                    (LangT("Заряд (0-1)"), 150),
                    (LangT("Цвет (#rrggbb)"), 150)
                ],
                "texture_url": "https://raw.githubusercontent.com/gbvxgzbwba/texture123/main/ore/ore.png",
                "sprite_folder": "items",
                "content_folder": "items",
                "success_msg": LangT("предмет")
            },
            "liquid": {
                "title": LangT("Создание новой жидкости"), 
                "fields": [
                    (LangT("Название жидкости"), 150),
                    (LangT("Описание"), 150),
                    (LangT("Густота (0-1)"), 150),
                    (LangT("Температура (0-1)"), 150),
                    (LangT("Воспламеняемость (0-1)"), 150),
                    (LangT("Взрывоопасность (0-1)"), 150),
                    (LangT("Цвет (#rrggbb)"), 150)
                ],
                "texture_url": "https://raw.githubusercontent.com/Anuken/Mindustry/master/core/assets-raw/sprites/items/liquid-water.png",
                "sprite_folder": "liquids",
                "content_folder": "liquids", 
                "success_msg": LangT("жидкость")
            }
        }
        
        cfg = config[content_type]
        
        ctk.CTkLabel(self.root, text=cfg["title"], font=("Arial", 16, "bold")).pack(pady=10)

        form_frame = ctk.CTkFrame(self.root)
        form_frame.pack(pady=10)

        entries = []
        for i, (label_text, width) in enumerate(cfg["fields"]):
            label = ctk.CTkLabel(form_frame, text=label_text)
            entry = ctk.CTkEntry(form_frame, width=width)
            label.grid(row=i, column=0, sticky="w", pady=5, padx=10)
            entry.grid(row=i, column=1, pady=5, padx=10)
            entries.append(entry)

        def save_content():
            name = entries[0].get().strip().replace(" ", "_")
            desc = entries[1].get().strip()
            
            try:
                if content_type == "item":
                    flammability = float(entries[2].get())
                    explosiveness = float(entries[3].get())
                    radioactivity = float(entries[4].get())
                    charge = float(entries[5].get())
                    color = entries[6].get().strip()
                    
                    for val, field_name in [(flammability, LangT("Воспламеняемость")), 
                                        (explosiveness, LangT("Взрывоопасность")), 
                                        (radioactivity, LangT("Радиоактивность")), 
                                        (charge, LangT("Заряд"))]:
                        if not 0 <= val <= 1:
                            raise ValueError(f"{field_name} {LangT("должна быть от 0 до 1")}")
                    
                    content_data = {
                        "name": name,
                        "description": desc,
                        "flammability": flammability,
                        "explosiveness": explosiveness, 
                        "radioactivity": radioactivity,
                        "charge": charge,
                        "color": color
                    }
                else:  # liquid
                    viscosity = float(entries[2].get())
                    temperature = float(entries[3].get())
                    flammability = float(entries[4].get())
                    explosiveness = float(entries[5].get())
                    color = entries[6].get().strip()
                    
                    for val, field_name in [(viscosity, LangT("Густота")), 
                                        (temperature, LangT("Температура")),
                                        (flammability, LangT("Воспламеняемость")), 
                                        (explosiveness, LangT("Взрывоопасность"))]:
                        if not 0 <= val <= 1:
                            raise ValueError(f"{field_name} {LangT("должна быть от 0 до 1")}")
                    
                    content_data = {
                        "name": name,
                        "description": desc,
                        "viscosity": viscosity,
                        "temperature": temperature, 
                        "flammability": flammability,
                        "explosiveness": explosiveness,
                        "color": color
                    }
                    
            except ValueError as e:
                messagebox.showerror(LangT("Ошибка"), str(e))
                return

            required_fields = [name, desc, color] if content_type == "liquid" else [name, desc]
            if not all(required_fields):
                messagebox.showerror(LangT("Ошибка"), LangT("Все поля должны быть заполнены!"))
                return

            content_folder = os.path.join("mindustry_mod_creator", "mods", self.mod_name, "content", cfg["content_folder"])
            os.makedirs(content_folder, exist_ok=True)

            content_file_path = os.path.join(content_folder, f"{name}.json")
            with open(content_file_path, "w", encoding="utf-8") as file:
                json.dump(content_data, file, indent=4, ensure_ascii=False)

            sprite_folder = os.path.join("mindustry_mod_creator", "mods", self.mod_name, "sprites", cfg["sprite_folder"])
            texture_path = os.path.join(sprite_folder, f"{name}.png")
            
            from utils.file_utils import safe_download_texture
            if not safe_download_texture(cfg["texture_url"], texture_path):
                messagebox.showwarning(LangT("Предупреждение"), 
                                    f"{LangT("Текстура для")} {name} {LangT("не была загружена. Вы можете добавить её позже.")}")

            messagebox.showinfo(LangT("Успех"), f"{cfg['success_msg'].capitalize()} '{name}' {LangT("сохранён!")}")
            safe_navigation(self.show_content_buttons)

        ctk.CTkButton(self.root, text=f"{LangT("💾 Сохранить")} {cfg['success_msg']}", font=("Arial", 12),
                    command=save_content).pack(pady=20)
        ctk.CTkButton(self.root, text=LangT("Назад"), font=("Arial", 12),
                    command=lambda: safe_navigation(self.show_content_buttons)).pack(pady=20)

    def edit_requirements_from_context(self):
        """Редактор требований для блока, выбранного в главном меню"""
        #без изменений
        if not hasattr(self.root, 'current_block_item'):
            messagebox.showerror(LangT("Ошибка"), LangT("Блок не выбран"))
            return
        
        item = self.root.current_block_item
        block_name = item["name"]
        folder_path = os.path.dirname(item["full_path"])
        
        block_path = os.path.join(folder_path, f"{block_name}.json")
        if not os.path.exists(block_path):
            messagebox.showerror(LangT("Ошибка"), f"{LangT("Файл блока не найден:")} {block_path}")
            return
        
        with open(block_path, "r", encoding="utf-8") as f:
            try:
                block_data = json.load(f)
            except json.JSONDecodeError:
                messagebox.showerror(LangT("Ошибка"), LangT("Некорректный JSON файл блока."))
                return
        
        self.clear_window()
        self.root.configure(fg_color="#2b2b2b")
        
        main_frame = ctk.CTkFrame(self.root, fg_color="transparent")
        main_frame.pack(padx=10, pady=10, fill="both", expand=True)
        
        header_frame = ctk.CTkFrame(main_frame, height=90, fg_color="#3a3a3a", corner_radius=8)
        header_frame.pack(fill="x", pady=(0, 15))
        
        try:
            block_type = block_data.get("type")
            texture_path = os.path.join(self.mod_folder, "sprites", block_type, block_name, f"{block_name}.png")
            if os.path.exists(texture_path):
                from PIL import Image
                img = Image.open(texture_path)
                img = img.resize((70, 70), Image.LANCZOS)
                ctk_img = ctk.CTkImage(light_image=img, size=(70, 70))
                img_label = ctk.CTkLabel(header_frame, image=ctk_img, text="")
                img_label.pack(side="left", padx=20)
        except Exception as e:
            print(f"{LangT("Ошибка загрузки изображения:")} {e}")
        
        ctk.CTkLabel(header_frame, 
                    text=f"{LangT("Редактор требований:")} {block_name}, {LangT("лимит 25000")}",
                    font=("Arial", 18, "bold")).pack(side="left", padx=10)
        
        content_frame = ctk.CTkFrame(main_frame, fg_color="#3a3a3a", corner_radius=8)
        content_frame.pack(fill="both", expand=True)
        
        def load_item_icon(item_name):
            icon_paths = [
                os.path.join(self.mod_folder, "sprites", "items", f"{item_name}.png"),
                os.path.join("mindustry_mod_creator", "sprites", "items", f"{item_name}.png"),
                os.path.join("mindustry_mod_creator", "icons", f"{item_name}.png")
            ]
            for path in icon_paths:
                if os.path.exists(path):
                    try:
                        from PIL import Image
                        img = Image.open(path)
                        img = img.resize((50, 50), Image.LANCZOS)
                        return ctk.CTkImage(light_image=img, size=(50, 50))
                    except:
                        continue
            return None
        
        default_items = [
            "copper", "lead", "metaglass", "graphite", "sand", 
            "coal", "titanium", "thorium", "scrap", "silicon",
            "plastanium", "phase-fabric", "surge-alloy", "spore-pod", 
            "blast-compound", "pyratite"
        ]
        
        mod_items = []
        mod_items_path = os.path.join(self.mod_folder, "content", "items")
        if os.path.exists(mod_items_path):
            mod_items = [f.replace(".json", "") for f in os.listdir(mod_items_path) if f.endswith(".json")]

        default_item_entries = {}
        mod_item_entries = {}

        def create_item_card(parent, item, is_mod_item=False):
            card_frame = ctk.CTkFrame(parent, 
                                    fg_color="#4a4a4a", 
                                    corner_radius=8,
                                    height=180)
            card_frame.pack_propagate(False)
            
            content_frame = ctk.CTkFrame(card_frame, fg_color="transparent")
            content_frame.pack(fill="both", expand=True, padx=10, pady=10)
            
            top_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
            top_frame.pack(fill="x", pady=(0, 10))
            
            icon = load_item_icon(item)
            if icon:
                ctk.CTkLabel(top_frame, image=icon, text="").pack()
            
            ctk.CTkLabel(top_frame, 
                        text=item.capitalize(), 
                        font=("Arial", 14),
                        anchor="center").pack()
            
            bottom_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
            bottom_frame.pack(fill="x", pady=(10, 0))

            int_value = tk.IntVar(value=0)
            str_value = tk.StringVar(value="0")
            max_value = 25000

            if "research" in block_data and "requirements" in block_data["research"]:
                for req in block_data["research"]["requirements"]:
                    if req["item"] == item:
                        str_value.set(str(req["amount"]))
                        break

            def sync_values(*args):
                try:
                    val = str_value.get()
                    int_value.set(int(val) if val else 0)
                except:
                    int_value.set(0)
            
            str_value.trace_add("write", sync_values)
            
            def validate_input(new_val):
                if new_val == "":
                    return True
                if not new_val.isdigit():
                    return False
                if len(new_val) > 5:
                    return False
                if int(new_val) > max_value:
                    return False
                return True
            
            validation = parent.register(validate_input)
            
            controls_frame = ctk.CTkFrame(bottom_frame, fg_color="transparent")
            controls_frame.pack(fill="x", pady=5)
            
            controls_frame.grid_columnconfigure(0, weight=0, minsize=35)
            controls_frame.grid_columnconfigure(1, weight=1, minsize=70)
            controls_frame.grid_columnconfigure(2, weight=0, minsize=35)

            def start_increment(change):
                global is_pressed
                is_pressed = True
                update_value(change)
                self.root.after(100, lambda: repeat_increment(change))

            def stop_increment():
                global is_pressed
                is_pressed = False

            def repeat_increment(change):
                if is_pressed:
                    update_value(change)
                    self.root.after(100, lambda: repeat_increment(change))
            
            def update_value(change):
                try:
                    current = str_value.get()
                    try:
                        current_num = int(current) if current else 0
                    except ValueError:
                        current_num = 0
                    new_value = max(0, min(max_value, current_num + change))
                    str_value.set(str(new_value))
                except Exception as e:
                    str_value.set("0")

            minus_btn = ctk.CTkButton(
                controls_frame,
                text="-",
                width=35,
                height=35,
                font=("Arial", 16),
                fg_color="#e62525",
                hover_color="#701c1c",
                border_color="#701c1c",
                corner_radius=6,
                anchor="center",
                command=lambda: update_value(-1)
            )
            minus_btn.bind("<ButtonPress-1>", lambda e: start_increment(-1))
            minus_btn.bind("<ButtonRelease-1>", lambda e: stop_increment())
            minus_btn.grid(row=0, column=0, padx=(0, 5), sticky="nsew")

            entry = ctk.CTkEntry(
                controls_frame,
                width=70,
                height=35,
                font=("Arial", 14),
                textvariable=str_value,
                fg_color="#BE6F24",
                border_color="#613e11",
                justify="center",
                validate="key",
                validatecommand=(validation, "%P")
            )
            entry.grid(row=0, column=1, padx=5, sticky="ew")

            plus_btn = ctk.CTkButton(
                controls_frame,
                text="+",
                width=35,
                height=35,
                font=("Arial", 16),
                corner_radius=6,
                anchor="center",
                command=lambda: update_value(1)
            )
            plus_btn.bind("<ButtonPress-1>", lambda e: start_increment(1))
            plus_btn.bind("<ButtonRelease-1>", lambda e: stop_increment())
            plus_btn.grid(row=0, column=2, padx=(5, 0), sticky="nsew")
            
            def handle_focus_out(event):
                if str_value.get() == "":
                    str_value.set("0")
            
            entry.bind("<FocusOut>", handle_focus_out)
            
            if is_mod_item:
                mod_item_entries[item] = int_value
            else:
                default_item_entries[item] = int_value
            
            return card_frame
        
        def calculate_columns(container_width):
            min_card_width = 180
            spacing = 10
            max_columns = max(1, container_width // (min_card_width + spacing))
            if max_columns * (min_card_width + spacing) - spacing <= container_width:
                return max_columns, min_card_width
            return 1, -1
        
        def update_grid(canvas, items_frame, items):
            container_width = canvas.winfo_width()
            if container_width < 1:
                return
            
            columns, card_width = calculate_columns(container_width)
            
            for widget in items_frame.grid_slaves():
                widget.grid_forget()
            
            for i, item in enumerate(items):
                row = i // columns
                col = i % columns
                is_mod_item = item in mod_items
                card = create_item_card(items_frame, item, is_mod_item)
                if card_width == -1:
                    card.configure(width=container_width - 20)
                else:
                    card.configure(width=card_width)
                card.grid(row=row, column=col, padx=5, pady=5, sticky="nsew")
            
            items_frame.update_idletasks()
            canvas.configure(scrollregion=canvas.bbox("all"))
            
            if items_frame.winfo_height() <= canvas.winfo_height():
                canvas.yview_moveto(0)
                scrollbar.pack_forget()
            else:
                scrollbar.pack(side="right", fill="y")
        
        canvas = tk.Canvas(content_frame, bg="#3a3a3a", highlightthickness=0)
        scrollbar = ctk.CTkScrollbar(content_frame, orientation="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)
        
        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True, padx=10, pady=10)
        
        items_frame = ctk.CTkFrame(canvas, fg_color="#3a3a3a")
        canvas.create_window((0, 0), window=items_frame, anchor="nw")

        def on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind("<MouseWheel>", on_mousewheel)
        
        all_items = default_items + mod_items
        update_grid(canvas, items_frame, all_items)
        
        canvas.bind("<Configure>", lambda e: update_grid(canvas, items_frame, all_items))
        items_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        
        footer_frame = ctk.CTkFrame(main_frame, height=70, fg_color="#3a3a3a", corner_radius=8)
        footer_frame.pack(fill="x", pady=(15, 0))
        
        btn_frame = ctk.CTkFrame(footer_frame, fg_color="transparent")
        btn_frame.pack(expand=True, pady=15)

        def save_requirements():
            requirements = []
            
            for item, var in default_item_entries.items():
                amount = var.get()
                if amount > 0:
                    requirements.append({"item": item, "amount": amount})
            
            for item, var in mod_item_entries.items():
                amount = var.get()
                if amount > 0:
                    requirements.append({"item": item, "amount": amount})
            
            if not requirements:
                messagebox.showwarning(LangT("Ошибка"), LangT("Вы не добавили ни одного ресурса!"))
                return
            
            if "research" not in block_data:
                block_data["research"] = {}
            
            block_data["research"]["requirements"] = requirements
            
            try:
                with open(block_path, "w", encoding="utf-8") as f:
                    json.dump(block_data, f, indent=4, ensure_ascii=False)
                
                messagebox.showinfo(LangT("Успех"), f"{LangT("Требования для блока")} '{block_name}' {LangT("успешно сохранены!")}")
                safe_navigation(self.show_content_buttons)
            
            except Exception as e:
                messagebox.showerror(LangT("Ошибка"), f"{LangT("Не удалось сохранить требования:")} {str(e)}")
        
        ctk.CTkButton(btn_frame, 
                    text=LangT("Сохранить"), 
                    width=140, 
                    height=45,
                    font=("Arial", 14),
                    command=save_requirements).pack(side="left", padx=20)
        
        ctk.CTkButton(btn_frame, 
                    text=LangT("Отмена"), 
                    width=140, 
                    height=45,
                    font=("Arial", 14),
                    fg_color="#e62525", 
                    hover_color="#701c1c", 
                    border_color="#701c1c",
                    command=lambda: safe_navigation(self.show_content_buttons)).pack(side="left", padx=20)

    def edit_requirements_from_parent(self):
        """Редактор требований для блока, выбранного в главном меню"""
        #без изменений
        if not hasattr(self.root, 'current_block_item'):
            messagebox.showerror(LangT("Ошибка"), LangT("Блок не выбран"))
            return
        
        item = self.root.current_block_item
        block_name = item["name"]
        folder_path = os.path.dirname(item["full_path"])
        
        block_path = os.path.join(folder_path, f"{block_name}.json")
        if not os.path.exists(block_path):
            messagebox.showerror(LangT("Ошибка"), f"{LangT("Файл блока не найден:")} {block_path}")
            return
        
        with open(block_path, "r", encoding="utf-8") as f:
            try:
                block_data = json.load(f)
            except json.JSONDecodeError:
                messagebox.showerror(LangT("Ошибка"), LangT("Некорректный JSON файл блока."))
                return
        
        self.clear_window()
        self.root.configure(fg_color="#2b2b2b")
        
        main_frame = ctk.CTkFrame(self.root, fg_color="transparent")
        main_frame.pack(padx=10, pady=10, fill="both", expand=True)
        
        header_frame = ctk.CTkFrame(main_frame, height=90, fg_color="#3a3a3a", corner_radius=8)
        header_frame.pack(fill="x", pady=(0, 15))
        
        try:
            block_type = block_data.get("type")
            texture_path = os.path.join(self.mod_folder, "sprites", block_type, block_name, f"{block_name}.png")
            if not os.path.exists(texture_path):
                texture_path = os.path.join(self.mod_folder, "sprites", block_type, f"{block_name}.png")
            if os.path.exists(texture_path):
                from PIL import Image
                img = Image.open(texture_path)
                img = img.resize((70, 70), Image.LANCZOS)
                ctk_img = ctk.CTkImage(light_image=img, size=(70, 70))
                img_label = ctk.CTkLabel(header_frame, image=ctk_img, text="")
                img_label.pack(side="left", padx=20)
        except Exception as e:
            print(f"{LangT("Ошибка загрузки изображения:")} {e}")
        
        ctk.CTkLabel(header_frame, 
                    text=f"{LangT("Выберите родительский блок для:")} {block_name}",
                    font=("Arial", 18, "bold")).pack(side="left", padx=10)
        
        content_frame = ctk.CTkFrame(main_frame, fg_color="#3a3a3a", corner_radius=8)
        content_frame.pack(fill="both", expand=True)
        
        mod_name = os.path.basename(self.mod_folder)
        cache_path = os.path.join("mindustry_mod_creator", "cache", f"{mod_name}.json")
        blocks_list = []
        
        if os.path.exists(cache_path):
            with open(cache_path, "r", encoding="utf-8") as f:
                try:
                    cache_data = json.load(f)
                    for block_type, blocks in cache_data.items():
                        if block_type == "_comment":
                            continue
                        if isinstance(blocks, list):
                            for block_name_in_cache in blocks:
                                if block_name_in_cache:
                                    blocks_list.append({
                                        "type": block_type,
                                        "name": block_name_in_cache
                                    })
                except json.JSONDecodeError as e:
                    messagebox.showerror(LangT("Ошибка"), f"{LangT("Некорректный JSON файл кэша:")} {e}")
                    return
        
        blocks_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        blocks_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        canvas = tk.Canvas(blocks_frame, bg="#3a3a3a", highlightthickness=0)
        scrollbar = ctk.CTkScrollbar(blocks_frame, orientation="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)
        
        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)
        
        inner_frame = ctk.CTkFrame(canvas, fg_color="transparent")
        canvas_window = canvas.create_window((0, 0), window=inner_frame, anchor="nw")
        
        def on_mousewheel(event):
            try:
                if canvas.winfo_exists():
                    canvas.yview_scroll(int(-1*(event.delta/120)), "units")
            except:
                pass
        
        canvas.bind("<MouseWheel>", on_mousewheel)
        inner_frame.bind("<MouseWheel>", lambda e: canvas.event_generate("<MouseWheel>", delta=e.delta))
        
        def on_canvas_configure(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
            canvas.itemconfig(canvas_window, width=canvas.winfo_width())
        
        canvas.bind("<Configure>", on_canvas_configure)
        
        def load_block_icon(block_info):
            if not isinstance(block_info, dict):
                print(LangT("Ошибка: block_info должен быть словарем"))
                return None
                
            block_name = block_info.get("name")
            if not block_name:
                print(LangT("Ошибка: В block_info отсутствует 'name'"))
                return None
            
            block_types = {
                "LiquidRouter",
                "conveyor",
                "wall",
                "GenericCrafter",
                "SolarGenerator",
                "StorageBlock",
                "conduit",
                "ConsumeGenerator",
                "PowerNode",
                "Router",
                "Junction",
                "Unloader",
                "LiquidJunction",
                "Battery",
                "ThermalGenerator"
            }
            block_types = {t for t in block_types if t is not None}

            search_paths = []
            for block_type in block_types:
                search_paths.extend([
                    os.path.join(self.mod_folder, "sprites", block_type, block_name, f"{block_name}.png"),
                    os.path.join(self.mod_folder, "sprites", block_type, f"{block_name}.png")
                ])
            
            search_paths.extend([
                os.path.join("mindustry_mod_creator", "icons", f"{block_name}.png")
            ])
            
            for path in search_paths:
                if os.path.exists(path):
                    try:
                        from PIL import Image
                        img = Image.open(path)
                        img = img.resize((50, 50), Image.LANCZOS)
                        return ctk.CTkImage(light_image=img, size=(50, 50))
                    except Exception as e:
                        print(f"{LangT("Ошибка загрузки изображения")} {path}: {e}")
                        continue
            try:
                print(f"{LangT("Текстура для блока")} {block_name} {LangT("не найдена. Создана заглушка")}")
                from PIL import Image
                empty_img = Image.new('RGBA', (50, 50), (100, 100, 100, 255))
                return ctk.CTkImage(light_image=empty_img, size=(50, 50))
            except Exception as e:
                print(f"{LangT("Ошибка создания заглушки:")} {e}")
                return None
        
        def create_block_card(parent, block_info):
            block_type = block_info["type"]
            block_name_in_cache = block_info["name"]
            
            card_frame = ctk.CTkFrame(parent, 
                                    fg_color="#4a4a4a", 
                                    corner_radius=8,
                                    width=200,
                                    height=220)
            card_frame.pack_propagate(False)
            
            content_frame = ctk.CTkFrame(card_frame, fg_color="transparent")
            content_frame.pack(fill="both", expand=True, padx=10, pady=10)
            
            top_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
            top_frame.pack(fill="both", expand=True)
            
            icon = load_block_icon(block_info)
            if icon:
                ctk.CTkLabel(top_frame, image=icon, text="").pack(pady=5)
            
            ctk.CTkLabel(top_frame, 
                        text=block_name_in_cache,
                        font=("Arial", 14, "bold"),
                        anchor="center").pack()
            
            ctk.CTkLabel(top_frame, 
                        text=f"Тип: {block_type}",
                        font=("Arial", 11),
                        anchor="center").pack()
            
            def on_select():
                if "research" not in block_data:
                    block_data["research"] = {"parent": block_name_in_cache}
                else:
                    block_data["research"]["parent"] = block_name_in_cache
                
                try:
                    with open(block_path, "w", encoding="utf-8") as f:
                        json.dump(block_data, f, indent=4, ensure_ascii=False)
                    messagebox.showinfo(LangT("Успех"), f"{LangT("Родительский блок")} '{block_name_in_cache}' {LangT("установлен")}")
                    self.edit_requirements_from_context()
                except Exception as e:
                    messagebox.showerror(LangT("Ошибка"), f"{LangT("Не удалось сохранить:")} {e}")
            
            ctk.CTkButton(content_frame, 
                        text=LangT("Выбрать"), 
                        command=on_select).pack(pady=5)
            
            return card_frame
        
        columns = 4
        row = 0
        col = 0
        
        for i, block_info in enumerate(blocks_list):
            if i % columns == 0 and i != 0:
                row += 1
                col = 0
            
            card = create_block_card(inner_frame, block_info)
            card.grid(row=row, column=col, padx=5, pady=5, sticky="nsew")
            inner_frame.grid_columnconfigure(col, weight=1)
            col += 1
        
        buttons_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        buttons_frame.pack(fill="x", pady=(10, 0))
        
        ctk.CTkButton(buttons_frame, 
                    text=LangT("Отмена"), 
                    command=lambda: safe_navigation(self.show_content_buttons),
                    fg_color="#e62525",
                    hover_color="#701c1c").pack(side="right", padx=10)
        
        inner_frame.update_idletasks()
        canvas.configure(scrollregion=canvas.bbox("all"))
        
        def update_columns(event=None):
            nonlocal columns
            canvas_width = canvas.winfo_width()
            if canvas_width > 1:
                new_columns = max(1, canvas_width // 210)
                if new_columns != columns:
                    columns = new_columns
                    rearrange_cards()
        
            def rearrange_cards():
                for widget in inner_frame.winfo_children():
                    widget.destroy()
                
                row = 0
                col = 0
                for i, block_info in enumerate(blocks_list):
                    if i % columns == 0 and i != 0:
                        row += 1
                        col = 0
                    
                    card = create_block_card(inner_frame, block_info)
                    card.grid(row=row, column=col, padx=5, pady=5, sticky="nsew")
                    inner_frame.grid_columnconfigure(col, weight=1)
                    col += 1
                
                inner_frame.update_idletasks()
                canvas.configure(scrollregion=canvas.bbox("all"))
            
            canvas.bind("<Configure>", lambda e: (on_canvas_configure(e), update_columns(e)))
            update_columns()

        def paint(self, item=None):
            """Редактор пиксельной графики 32x32 с шаблонами"""
            #без изменений
            ctk.set_default_color_theme("blue")
            global current_color, grid_size, cell_size, canvas_size, current_tool
            global history, history_index, is_drawing, save_path

            def on_closing():
                nonlocal img, canvas, paint_window
                
                try:
                    if img and hasattr(img, 'close'):
                        img.close()
                except:
                    pass
                if canvas:
                    canvas.delete("all")
                    canvas = None
                    
                paint_window.destroy()
                gc.collect()
            
            current_color = "#000000"
            grid_size = 32
            cell_size = 20
            canvas_size = grid_size * cell_size
            current_tool = "pencil"
            history = []
            history_index = -1
            is_drawing = False

            if item is not None:
                if "full_path" in item:
                    if "items" in item["full_path"]:
                        content_type = "items"
                    elif "liquids" in item["full_path"]:
                        content_type = "liquids"
            
            templates_dir = os.path.join("mindustry_mod_creator", "icons", "paint", content_type)
            os.makedirs(templates_dir, exist_ok=True)
            
            if item is None:
                save_dir = os.path.join("mindustry_mod_creator", "icons", "paint")
                os.makedirs(save_dir, exist_ok=True)
                save_path = os.path.join(save_dir, "new_image.png")
                item_name = "new_image"
            else:
                item_name = item.get("name", "unnamed")
                content_type = item.get("type", "items")
                
                possible_paths = [
                    os.path.join(self.mod_folder, "sprites", content_type, item_name, f"{item_name}.png"),
                    os.path.join(self.mod_folder, "sprites", content_type, f"{item_name}.png"),
                    os.path.join(self.mod_folder, "sprites", "items", f"{item_name}.png"),
                    os.path.join(self.mod_folder, "sprites", "liquids", f"{item_name}.png"),
                    os.path.join(os.path.dirname(item.get("full_path", "")), f"{item_name}.png")
                ]
                
                for path in possible_paths:
                    if os.path.exists(path):
                        save_path = path
                        break
                else:
                    save_dir = os.path.dirname(item.get("full_path", self.mod_folder))
                    os.makedirs(save_dir, exist_ok=True)
                    save_path = os.path.join(save_dir, f"{item_name}.png")

            def save_state():
                global history, history_index
                
                if history_index < len(history) - 1:
                    history = history[:history_index + 1]
                
                state = []
                for x in range(grid_size):
                    row = []
                    for y in range(grid_size):
                        items = canvas.find_withtag(f"pixel_{x}_{y}")
                        color = None
                        if items:
                            color = canvas.itemcget(items[0], "fill")
                        row.append(color)
                    state.append(row)
                
                history.append(state)
                history_index = len(history) - 1

            def undo():
                global history_index
                if history_index > 0:
                    history_index -= 1
                    restore_state()

            def redo():
                global history_index
                if history_index < len(history) - 1:
                    history_index += 1
                    restore_state()

            def restore_state():
                state = history[history_index]
                canvas.delete("all")
                draw_grid()
                
                for x in range(grid_size):
                    for y in range(grid_size):
                        if state[x][y] is not None:
                            canvas.create_rectangle(
                                x * cell_size, y * cell_size,
                                (x + 1) * cell_size, (y + 1) * cell_size,
                                fill=state[x][y], outline="", tags=f"pixel_{x}_{y}"
                            )

            def start_drawing(event):
                global is_drawing
                is_drawing = True
                draw_pixel(event)
                save_state()

            def draw_pixel(event):
                if not is_drawing:
                    return
                    
                x = event.x // cell_size
                y = event.y // cell_size
                if 0 <= x < grid_size and 0 <= y < grid_size:
                    canvas.delete(f"pixel_{x}_{y}")
                    if current_tool == "eraser":
                        return
                    elif current_tool in ["pencil", "fill"]:
                        canvas.create_rectangle(
                            x * cell_size, y * cell_size,
                            (x + 1) * cell_size, (y + 1) * cell_size,
                            fill=current_color, outline="", tags=f"pixel_{x}_{y}"
                        )

            def stop_drawing(event):
                global is_drawing
                is_drawing = False
                save_state()

            def flood_fill(x, y, target_color, replacement_color):
                if target_color == replacement_color:
                    return
                if x < 0 or x >= grid_size or y < 0 or y >= grid_size:
                    return
                
                items = canvas.find_withtag(f"pixel_{x}_{y}")
                current_pixel_color = None
                if items:
                    current_pixel_color = canvas.itemcget(items[0], "fill")
                
                if current_pixel_color != target_color:
                    return
                
                canvas.delete(f"pixel_{x}_{y}")
                canvas.create_rectangle(
                    x * cell_size, y * cell_size,
                    (x + 1) * cell_size, (y + 1) * cell_size,
                    fill=replacement_color, outline="", tags=f"pixel_{x}_{y}"
                )
                
                flood_fill(x+1, y, target_color, replacement_color)
                flood_fill(x-1, y, target_color, replacement_color)
                flood_fill(x, y+1, target_color, replacement_color)
                flood_fill(x, y-1, target_color, replacement_color)

            def handle_click(event):
                x = event.x // cell_size
                y = event.y // cell_size
                if 0 <= x < grid_size and 0 <= y < grid_size:
                    if current_tool == "fill":
                        save_state()
                        items = canvas.find_withtag(f"pixel_{x}_{y}")
                        target_color = None
                        if items:
                            target_color = canvas.itemcget(items[0], "fill")
                        flood_fill(x, y, target_color, current_color)
                        save_state()
                    else:
                        start_drawing(event)

            def change_color():
                global current_color
                color = colorchooser.askcolor(title=LangT("Выберите цвет"), initialcolor=current_color)
                if color[1]:
                    current_color = color[1]
                    color_button.configure(fg_color=current_color)
                    set_tool("pencil")

            def clear_canvas():
                canvas.delete("all")
                draw_grid()
                save_state()

            def draw_grid():
                canvas.configure(bg="#e0e0e0")
                for i in range(grid_size + 1):
                    canvas.create_line(
                        i * cell_size, 0, 
                        i * cell_size, canvas_size, 
                        fill="#d0d0d0", width=2
                    )
                    canvas.create_line(
                        0, i * cell_size, 
                        canvas_size, i * cell_size, 
                        fill="#d0d0d0", width=2
                    )

            def save_image():
                nonlocal img
                try:
                    img = Image.new("RGBA", (grid_size, grid_size), (0, 0, 0, 0))
                    img = Image.new("RGBA", (grid_size, grid_size), (0, 0, 0, 0))
                    pixels = img.load()
                    
                    for x in range(grid_size):
                        for y in range(grid_size):
                            items = canvas.find_withtag(f"pixel_{x}_{y}")
                            if items:
                                color = canvas.itemcget(items[0], "fill")
                                if color:
                                    try:
                                        r, g, b = tuple(int(color.lstrip('#')[i:i+2], 16) for i in (0, 2, 4))
                                        pixels[x, y] = (r, g, b, 255)
                                    except:
                                        pixels[x, y] = (0, 0, 0, 255)
                    
                    img.save(save_path)
                    messagebox.showinfo(LangT("Сохранено"), f"{LangT("Изображение сохранено в:")}\n{save_path}")
                finally:
                    if 'img' in locals():
                        img.close()

            def set_tool(tool):
                global current_tool
                current_tool = tool
                
                pencil_button.configure(fg_color="#2b2b2b")
                eraser_button.configure(fg_color="#2b2b2b")
                fill_button.configure(fg_color="#2b2b2b")
                
                if tool == "pencil":
                    pencil_button.configure(fg_color="#1f6aa5")
                elif tool == "eraser":
                    eraser_button.configure(fg_color="#1f6aa5")
                elif tool == "fill":
                    fill_button.configure(fg_color="#1f6aa5")

            def load_template_image(path):
                try:
                    img = Image.open(path)
                    
                    if img.size != (32, 32):
                        img = img.resize((32, 32), Image.NEAREST)
                    
                    if img.mode != "RGBA":
                        img = img.convert("RGBA")
                    
                    pixels = img.load()
                    
                    clear_canvas()
                    
                    for x in range(32):
                        for y in range(32):
                            pixel = pixels[x, y]
                            if len(pixel) == 4:
                                r, g, b, a = pixel
                                if a > 0:
                                    color = f"#{r:02x}{g:02x}{b:02x}"
                                    canvas.create_rectangle(
                                        x * cell_size, y * cell_size,
                                        (x + 1) * cell_size, (y + 1) * cell_size,
                                        fill=color, outline="", tags=f"pixel_{x}_{y}"
                                    )
                    img.close()
                    save_state()
                except Exception as e:
                    messagebox.showerror(LangT("Ошибка"), f"{LangT("Не удалось загрузить шаблон:")} {e}")

            def show_templates():
                templates = []
                if os.path.exists(templates_dir):
                    for file in os.listdir(templates_dir):
                        if file.endswith(".png"):
                            templates.append({
                                "name": file[:-4],
                                "path": os.path.join(templates_dir, file)
                            })
                
                if not templates:
                    messagebox.showinfo(LangT("Шаблоны"), f"{LangT("В папке шаблонов")} ({content_type}) {LangT("нет изображений")}")
                    return
                
                template_window = ctk.CTkToplevel(paint_window)
                template_window.title(LangT("Выберите шаблон"))
                template_window.geometry("600x400")
                
                scroll_frame = ctk.CTkScrollableFrame(template_window)
                scroll_frame.pack(fill="both", expand=True, padx=10, pady=10)
                
                for template in templates:
                    try:
                        img = Image.open(template["path"])
                        img = img.resize((64, 64), Image.NEAREST)
                        ctk_img = ctk.CTkImage(light_image=img, size=(64, 64))
                        
                        frame = ctk.CTkFrame(scroll_frame)
                        frame.pack(fill="x", pady=5)
                        
                        ctk.CTkLabel(frame, image=ctk_img, text="").pack(side="left", padx=10)
                        ctk.CTkLabel(frame, text=template["name"], font=("Arial", 14)).pack(side="left", padx=10)
                        
                        def load_template(path=template["path"]):
                            load_template_image(path)
                            template_window.destroy()
                        
                        ctk.CTkButton(frame, text=LangT("Загрузить"), command=load_template).pack(side="right", padx=10)
                    except Exception as e:
                        print(f"{LangT("Ошибка загрузки шаблона")} {template['name']}: {e}")

            paint_window = ctk.CTkToplevel(self.root)
            paint_window.title(f"32x32 Pixel Editor - {item_name}")
            paint_window.resizable(False, False)
            paint_window.protocol("WM_DELETE_WINDOW", on_closing)

            canvas = ctk.CTkCanvas(paint_window, bg="#e0e0e0", width=canvas_size, height=canvas_size, highlightthickness=0)
            canvas.pack()

            tool_frame = ctk.CTkFrame(paint_window, fg_color="transparent")
            tool_frame.pack(fill="x", pady=(10, 0))

            ctk.CTkButton(
                tool_frame,
                text=LangT("< Отмена"),
                command=undo,
                width=80,
                fg_color="#555555",
                hover_color="#444444"
            ).pack(side="left", padx=2)

            ctk.CTkButton(
                tool_frame,
                text=LangT("Повтор >"),
                command=redo,
                width=80,
                fg_color="#555555",
                hover_color="#444444"
            ).pack(side="left", padx=2)

            pencil_button = ctk.CTkButton(
                tool_frame, 
                text=LangT("Карандаш"),
                command=lambda: set_tool("pencil"),
                width=80,
                fg_color="#1f6aa5"
            )
            pencil_button.pack(side="left", padx=5)

            eraser_button = ctk.CTkButton(
                tool_frame,
                text=LangT("Ластик"),
                command=lambda: set_tool("eraser"),
                width=80
            )
            eraser_button.pack(side="left", padx=5)

            fill_button = ctk.CTkButton(
                tool_frame,
                text=LangT("Заливка"),
                command=lambda: set_tool("fill"),
                width=80
            )
            fill_button.pack(side="left", padx=5)

            color_button = ctk.CTkButton(
                tool_frame, 
                text=LangT("Цвет"), 
                command=change_color,
                fg_color=current_color,
                hover_color=current_color,
                width=80
            )
            color_button.pack(side="left", padx=5)

            ctk.CTkButton(
                tool_frame,
                text=LangT("Очистить"),
                command=clear_canvas,
                width=80
            ).pack(side="left", padx=5)

            ctk.CTkButton(
                tool_frame,
                text=LangT("Шаблоны"),
                command=show_templates,
                width=80,
                fg_color="#4CAF50",
                hover_color="#388E3C"
            ).pack(side="left", padx=5)

            ctk.CTkButton(
                tool_frame,
                text=LangT("Сохранить"),
                command=save_image,
                width=80
            ).pack(side="left", padx=5)

            canvas.bind("<B1-Motion>", draw_pixel)
            canvas.bind("<Button-1>", handle_click)
            canvas.bind("<ButtonRelease-1>", stop_drawing)

            draw_grid()

            if os.path.exists(save_path):
                try:
                    img = Image.open(save_path)
                    if img.size != (grid_size, grid_size):
                        img = img.resize((grid_size, grid_size), Image.NEAREST)
                    
                    if img.mode != "RGBA":
                        img = img.convert("RGBA")
                    
                    pixels = img.load()
                    for x in range(grid_size):
                        for y in range(grid_size):
                            r, g, b, a = pixels[x, y]
                            if a > 0:
                                color = f"#{r:02x}{g:02x}{b:02x}"
                                canvas.create_rectangle(
                                    x * cell_size, y * cell_size,
                                    (x + 1) * cell_size, (y + 1) * cell_size,
                                    fill=color, outline="", tags=f"pixel_{x}_{y}"
                                )
                    save_state()
                except Exception as e:
                    print(f"{LangT("Ошибка загрузки изображения:")} {e}")
                    save_state()
            else:
                save_state()

    def open_requirements_editor(self, block_name, block_data):
                self.clear_window()
                
                self.root.configure(fg_color="#2b2b2b")
                
                main_frame = ctk.CTkFrame(self.root, fg_color="transparent")
                main_frame.pack(padx=10, pady=10, fill="both", expand=True)
                
                header_frame = ctk.CTkFrame(main_frame, height=90, fg_color="#3a3a3a", corner_radius=8)
                header_frame.pack(fill="x", pady=(0, 15))
                
                try:
                    block_type = block_data.get("type")
                    texture_path = os.path.join("mindustry_mod_creator", "mods", self.mod_name, "sprites", block_type, block_name, f"{block_name}.png")
                    if os.path.exists(texture_path):
                        img = Image.open(texture_path)
                        img = img.resize((70, 70), Image.LANCZOS)
                        ctk_img = ctk.CTkImage(light_image=img, size=(70, 70))
                        img_label = ctk.CTkLabel(header_frame, image=ctk_img, text="")
                        img_label.pack(side="left", padx=20)
                except Exception as e:
                    print(f"{LangT("Ошибка загрузки изображения:")} {e}")
                
                ctk.CTkLabel(header_frame, 
                            text=f"{LangT("Редактор ресурсов:")} {block_name}, {block_type}, {LangT("максимум 70.000")}",
                            font=("Arial", 18, "bold")).pack(side="left", padx=10)
                
                content_frame = ctk.CTkFrame(main_frame, fg_color="#3a3a3a", corner_radius=8)
                content_frame.pack(fill="both", expand=True)
                
                def load_item_icon(item_name):
                    icon_paths = [
                        os.path.join(self.mod_folder, "sprites", "items", f"{item_name}.png"),
                        os.path.join("mindustry_mod_creator", "sprites", "items", f"{item_name}.png"),
                        os.path.join("mindustry_mod_creator", "icons", f"{item_name}.png")
                    ]
                    for path in icon_paths:
                        if os.path.exists(path):
                            try:
                                img = Image.open(path)
                                img = img.resize((50, 50), Image.LANCZOS)
                                return ctk.CTkImage(light_image=img, size=(50, 50))
                            except:
                                continue
                    return None
                
                # Списки предметов
                default_items = [
                    "copper", "lead", "metaglass", "graphite", "sand", 
                    "coal", "titanium", "thorium", "scrap", "silicon",
                    "plastanium", "phase-fabric", "surge-alloy", "spore-pod", 
                    "blast-compound", "pyratite"
                ]
                
                mod_items = []
                mod_items_path = os.path.join(self.mod_folder, "content", "items")
                if os.path.exists(mod_items_path):
                    mod_items = [f.replace(".json", "") for f in os.listdir(mod_items_path) if f.endswith(".json")]

                default_item_entries = {}
                mod_item_entries = {}

                def create_item_card(parent, item, is_mod_item=False):
                    card_frame = ctk.CTkFrame(parent, 
                                            fg_color="#4a4a4a", 
                                            corner_radius=8,
                                            height=180)
                    card_frame.pack_propagate(False)
                    
                    content_frame = ctk.CTkFrame(card_frame, fg_color="transparent")
                    content_frame.pack(fill="both", expand=True, padx=10, pady=10)
                    
                    top_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
                    top_frame.pack(fill="x", pady=(0, 10))
                    
                    icon = load_item_icon(item)
                    if icon:
                        ctk.CTkLabel(top_frame, image=icon, text="").pack()
                    
                    ctk.CTkLabel(top_frame, 
                                text=item.capitalize(), 
                                font=("Arial", 14),
                                anchor="center").pack()
                    
                    bottom_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
                    bottom_frame.pack(fill="x", pady=(10, 0))

                    int_value = tk.IntVar(value=0)
                    str_value = tk.StringVar(value="0")
                    max_value = 70000

                    def sync_values(*args):
                        try:
                            val = str_value.get()
                            int_value.set(int(val) if val else 0)
                        except:
                            int_value.set(0)
                    
                    str_value.trace_add("write", sync_values)
                    
                    def validate_input(new_val):
                        if new_val == "":
                            return True
                        if not new_val.isdigit():
                            return False
                        if len(new_val) > 5:
                            return False
                        if int(new_val) > max_value:
                            return False
                        return True
                    
                    validation = parent.register(validate_input)
                    
                    controls_frame = ctk.CTkFrame(bottom_frame, fg_color="transparent")
                    controls_frame.pack(fill="x", pady=5)
                    
                    # Настройка grid layout
                    controls_frame.grid_columnconfigure(0, weight=0, minsize=35)
                    controls_frame.grid_columnconfigure(1, weight=1, minsize=70)
                    controls_frame.grid_columnconfigure(2, weight=0, minsize=35)
                    
                    def update_value(change):
                        try:
                            current = str_value.get()
                            try:
                                current_num = int(current) if current else 0
                            except ValueError:
                                current_num = 0
                            new_value = max(0, min(max_value, current_num + change))
                            str_value.set(str(new_value))
                        except Exception as e:
                            str_value.set("0")

                    def start_increment(change):
                        global is_pressed
                        is_pressed = True
                        update_value(change)
                        self.root.after(100, lambda: repeat_increment(change))

                    def stop_increment():
                        global is_pressed
                        is_pressed = False

                    def repeat_increment(change):
                        if is_pressed:
                            update_value(change)
                            self.root.after(100, lambda: repeat_increment(change))

                    minus_btn = ctk.CTkButton(
                        controls_frame,
                        text="-",
                        width=35,
                        height=35,
                        font=("Arial", 16),
                        fg_color="#e62525",
                        hover_color="#701c1c",
                        border_color="#701c1c",
                        corner_radius=6,
                        anchor="center"
                    )
                    minus_btn.grid(row=0, column=0, padx=(0, 5), sticky="nsew")
                    minus_btn.bind("<ButtonPress-1>", lambda e: start_increment(-1))
                    minus_btn.bind("<ButtonRelease-1>", lambda e: stop_increment())

                    entry = ctk.CTkEntry(
                        controls_frame,
                        width=70,
                        height=35,
                        font=("Arial", 14),
                        textvariable=str_value,
                        fg_color="#BE6F24",
                        border_color="#613e11",
                        justify="center",
                        validate="key",
                        validatecommand=(validation, "%P")
                    )
                    entry.grid(row=0, column=1, padx=5, sticky="ew")

                    plus_btn = ctk.CTkButton(
                        controls_frame,
                        text="+",
                        width=35,
                        height=35,
                        font=("Arial", 16),
                        corner_radius=6,
                        anchor="center"
                    )
                    plus_btn.grid(row=0, column=2, padx=(5, 0), sticky="nsew")
                    plus_btn.bind("<ButtonPress-1>", lambda e: start_increment(1))
                    plus_btn.bind("<ButtonRelease-1>", lambda e: stop_increment())
                    
                    def handle_focus_out(event):
                        if str_value.get() == "":
                            str_value.set("0")
                    
                    entry.bind("<FocusOut>", handle_focus_out)
                    
                    if is_mod_item:
                        mod_item_entries[item] = int_value
                    else:
                        default_item_entries[item] = int_value
                    
                    return card_frame
                
                def calculate_columns(container_width):
                    min_card_width = 180
                    spacing = 10
                    max_columns = max(1, container_width // (min_card_width + spacing))
                    if max_columns * (min_card_width + spacing) - spacing <= container_width:
                        return max_columns, min_card_width
                    return 1, -1
                
                def update_grid(canvas, items_frame, items):
                    """Обновление сетки карточек"""
                    container_width = canvas.winfo_width()
                    
                    # Проверяем, действительно ли изменился размер
                    widget_id = f"requirements_{block_name}"
                    if (widget_id in self.last_widths and 
                        container_width == self.last_widths[widget_id] and 
                        container_width > 100):
                        return
                        
                    self.last_widths[widget_id] = container_width

                    if container_width < 1:
                        return
                    
                    columns, card_width = calculate_columns(container_width)
                    
                    for widget in items_frame.grid_slaves():
                        widget.grid_forget()
                    
                    for i, item in enumerate(items):
                        row = i // columns
                        col = i % columns
                        is_mod_item = item in mod_items
                        card = create_item_card(items_frame, item, is_mod_item)
                        if card_width == -1:
                            card.configure(width=container_width - 20)
                        else:
                            card.configure(width=card_width)
                        card.grid(row=row, column=col, padx=5, pady=5, sticky="nsew")
                    
                    items_frame.update_idletasks()
                    canvas.configure(scrollregion=canvas.bbox("all"))
                    
                    if items_frame.winfo_height() <= canvas.winfo_height():
                        canvas.yview_moveto(0)
                        scrollbar.pack_forget()
                    else:
                        scrollbar.pack(side="right", fill="y")
                
                # Создаем один скроллируемый контейнер для всех предметов
                canvas = tk.Canvas(content_frame, bg="#3a3a3a", highlightthickness=0)
                scrollbar = ctk.CTkScrollbar(content_frame, orientation="vertical", command=canvas.yview)
                canvas.configure(yscrollcommand=scrollbar.set)
                
                scrollbar.pack(side="right", fill="y")
                canvas.pack(side="left", fill="both", expand=True, padx=10, pady=10)
                
                items_frame = ctk.CTkFrame(canvas, fg_color="#3a3a3a")
                canvas.create_window((0, 0), window=items_frame, anchor="nw")

                def on_mousewheel(event):
                    canvas.yview_scroll(int(-1*(event.delta/120)),"units")
                canvas.bind("<MouseWheel>", on_mousewheel)
                canvas.bind("<Button-4>", lambda e: canvas.yview_scroll(-1, "units"))
                canvas.bind("<Button-5>", lambda e: canvas.yview_scroll(1, "units"))
                
                # Объединяем все предметы в один список
                all_items = default_items + mod_items
                update_grid(canvas, items_frame, all_items)
                
                widget_id = f"requirements_{block_name}"
                resize_handler = self.setup_resize_protection(widget_id, 
                    lambda: update_grid(canvas, items_frame, all_items), 
                    delay=300)
                canvas.bind("<Configure>", resize_handler)
                items_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
                
                footer_frame = ctk.CTkFrame(main_frame, height=70, fg_color="#3a3a3a", corner_radius=8)
                footer_frame.pack(fill="x", pady=(15, 0))
                
                btn_frame = ctk.CTkFrame(footer_frame, fg_color="transparent")
                btn_frame.pack(expand=True, pady=15)
                
                def save_requirements():
                    requirements = []
                    
                    for item, var in default_item_entries.items():
                        amount = var.get()
                        if amount > 0:
                            requirements.append({"item": item, "amount": amount})
                    
                    for item, var in mod_item_entries.items():
                        amount = var.get()
                        if amount > 0:
                            requirements.append({"item": item, "amount": amount})
                    
                    if not requirements:
                        messagebox.showwarning(LangT("Ошибка"), LangT("Вы не добавили ни одного ресурса!"))
                        return
                    
                    block_data["requirements"] = requirements
                    
                    try:
                        block_type = block_data.get("type")
                        content_folder = os.path.join("mindustry_mod_creator", "mods", self.mod_name, "content", "blocks", block_type)
                        os.makedirs(content_folder, exist_ok=True)
                        
                        # Создаем окно прогресса и блокируем кнопки
                        progress_window = ctk.CTkToplevel(self.root)
                        progress_window.title(LangT("Загрузка текстур"))
                        progress_window.geometry("400x150")
                        progress_window.transient(self.root)
                        progress_window.grab_set()
                        progress_window.protocol("WM_DELETE_WINDOW", lambda: None)  # Блокируем закрытие
                        
                        progress_label = ctk.CTkLabel(progress_window, text=LangT("Подготовка к загрузке..."))
                        progress_label.pack(pady=10)
                        
                        progress_bar = ctk.CTkProgressBar(progress_window, width=300)
                        progress_bar.pack(pady=10)
                        progress_bar.set(0)
                        
                        status_label = ctk.CTkLabel(progress_window, text="0/0")
                        status_label.pack(pady=5)
                        
                        # Блокируем кнопки в основном окне
                        for child in btn_frame.winfo_children():
                            child.configure(state="disabled")

                        # Список текстур для загрузки
                        texture_names = []
                        base_url = ""

                        if block_type == "wall":
                            texture_names = ["copper-wall.png"]
                            base_url = "https://raw.githubusercontent.com/Anuken/Mindustry/master/core/assets-raw/sprites/blocks/walls/"

                        elif block_type == "Battery":
                            texture_names = ["battery.png", "battery-top.png"]
                            base_url = "https://raw.githubusercontent.com/Anuken/Mindustry/master/core/assets-raw/sprites/blocks/power/"
                        elif block_type == "conveyor":
                            texture_names = [
                                "conveyor-0-0.png", "conveyor-0-1.png", "conveyor-0-2.png", "conveyor-0-3.png",
                                "conveyor-1-0.png", "conveyor-1-1.png", "conveyor-1-2.png", "conveyor-1-3.png",
                                "conveyor-2-0.png", "conveyor-2-1.png", "conveyor-2-2.png", "conveyor-2-3.png",
                                "conveyor-3-0.png", "conveyor-3-1.png", "conveyor-3-2.png", "conveyor-3-3.png",
                                "conveyor-4-0.png", "conveyor-4-1.png", "conveyor-4-2.png", "conveyor-4-3.png"
                            ]
                            base_url = "https://raw.githubusercontent.com/Anuken/Mindustry/master/core/assets-raw/sprites/blocks/distribution/conveyors/"
                        elif block_type == "GenericCrafter":
                            texture_names = ["silicon-smelter.png"]
                            base_url = "https://raw.githubusercontent.com/Anuken/Mindustry/master/core/assets-raw/sprites/blocks/production/"
                        elif block_type == "SolarGenerator":
                            texture_names = ["solar-panel.png"]
                            base_url = "https://raw.githubusercontent.com/Anuken/Mindustry/master/core/assets-raw/sprites/blocks/power/"
                        elif block_type == "StorageBlock":
                            texture_names = ["container.png","container-team.png"]
                            base_url = "https://raw.githubusercontent.com/Anuken/Mindustry/master/core/assets-raw/sprites/blocks/storage/"
                        elif block_type == "conduit":
                            texture_names = ["conduit-top-0.png", "conduit-top-1.png", "conduit-top-2.png", "conduit-top-3.png",
                                "conduit-top-4.png", "conduit-bottom-0.png", "conduit-bottom-1.png", "conduit-bottom-2.png",
                                "conduit-bottom-3.png", "conduit-bottom-4.png", "conduit-bottom.png"
                            ]
                            base_url = "https://raw.githubusercontent.com/Anuken/Mindustry/master/core/assets-raw/sprites/blocks/liquid/conduits/"
                        elif block_type == "ConsumeGenerator":
                            texture_names = [
                                "rtg-generator.png"
                            ]
                            base_url = "https://raw.githubusercontent.com/Anuken/Mindustry/master/core/assets-raw/sprites/blocks/power/"
                        elif block_type == "PowerNode":
                            texture_names = ["power-node.png"]
                            base_url = "https://raw.githubusercontent.com/Anuken/Mindustry/master/core/assets-raw/sprites/blocks/power/"
                        elif block_type == "Router":
                            texture_names = ["router.png"]
                            base_url = "https://raw.githubusercontent.com/Anuken/Mindustry/master/core/assets-raw/sprites/blocks/distribution/"
                        elif block_type == "Junction":
                            texture_names = ["junction.png"]
                            base_url = "https://raw.githubusercontent.com/Anuken/Mindustry/master/core/assets-raw/sprites/blocks/distribution/"
                        elif block_type == "Unloader":
                            texture_names = ["unloader.png", "unloader-center.png"]
                            base_url = "https://raw.githubusercontent.com/Anuken/Mindustry/master/core/assets-raw/sprites/blocks/storage/"
                        elif block_type == "LiquidRouter":
                            texture_names = ["liquid-router.png", "liquid-router-bottom.png"]
                            base_url = "https://raw.githubusercontent.com/Anuken/Mindustry/master/core/assets-raw/sprites/blocks/liquid/"
                        elif block_type == "LiquidJunction":
                            texture_names = ["liquid-junction.png"]
                            base_url = "https://raw.githubusercontent.com/Anuken/Mindustry/master/core/assets-raw/sprites/blocks/liquid/"
                        elif block_type == "ThermalGenerator":
                            texture_names = ["thermal-generator.png"]
                            base_url = "https://raw.githubusercontent.com/Anuken/Mindustry/master/core/assets-raw/sprites/blocks/power/"
                        elif block_type == "BeamNode":
                            texture_names = ["beam-node.png"]
                            base_url = "https://raw.githubusercontent.com/Anuken/Mindustry/master/core/assets-raw/sprites/blocks/power/"
                        elif block_type == "Pump":
                            texture_names = ["rotary-pump.png"]
                            base_url = "https://raw.githubusercontent.com/Anuken/Mindustry/master/core/assets-raw/sprites/blocks/liquid/"
                        elif block_type == "SolidPump":
                            texture_names = ["water-extractor.png","water-extractor-rotator.png","water-extractor-top.png"]
                            base_url = "https://raw.githubusercontent.com/Anuken/Mindustry/master/core/assets-raw/sprites/blocks/drills/"
                        elif block_type == "MendProjector":
                            texture_names = ["mend-projector.png", "mend-projector-top.png"]
                            base_url = "https://raw.githubusercontent.com/Anuken/Mindustry/master/core/assets-raw/sprites/blocks/defense/"
                        elif block_type == "OverdriveProjector":
                            texture_names = ["overdrive-projector.png", "overdrive-projector-top.png"]
                            base_url = "https://raw.githubusercontent.com/Anuken/Mindustry/master/core/assets-raw/sprites/blocks/defense/"
                        else:
                            raise ValueError(f"{LangT("Неизвестный тип блока:")} {block_type}")

                        if len(texture_names) == 1:
                            sprite_folder = os.path.join("mindustry_mod_creator", "mods", self.mod_name, "sprites", block_type)
                        else:
                            sprite_folder = os.path.join("mindustry_mod_creator", "mods", self.mod_name, "sprites", block_type, block_name)
                        os.makedirs(sprite_folder, exist_ok=True)
                        
                        total_files = len(texture_names)
                        downloaded = 0
                        
                        def update_progress():
                            nonlocal downloaded
                            progress = downloaded / total_files
                            progress_bar.set(progress)
                            status_label.configure(text=f"{downloaded}/{total_files}")
                            progress_window.update()
                        
                        def resize_image(image_path, size_multiplier):
                            """Изменяет размер изображения согласно множителю (1=32px, 2=64px, ...)"""
                            from PIL import Image
                            try:
                                original_size = 32  # Базовый размер текстур Mindustry
                                new_size = original_size * size_multiplier
                                
                                img = Image.open(image_path)
                                if img.size != (new_size, new_size):
                                    img = img.resize((new_size, new_size), Image.Resampling.LANCZOS)
                                    img.save(image_path)
                            except Exception as e:
                                print(f"{LangT("Ошибка при изменении размера")} {image_path}: {e}")
                        
                        def download_textures():
                            nonlocal downloaded
                            try:
                                size_multiplier = int(block_data.get("size", 1))
                                size_multiplier = max(1, min(15, size_multiplier))  # Ограничиваем диапазон 1-15
                                
                                for texture in texture_names:
                                    try:
                                        # Формируем новое имя файла
                                        if block_type == "battery":
                                            new_name = texture.replace("battery", block_name)
                                        elif block_type == "wall":
                                            new_name = texture.replace("copper-wall", block_name)
                                        elif block_type == "conveyor":
                                            new_name = texture.replace("conveyor", block_name)
                                        elif block_type == "GenericCrafter":
                                            new_name = texture.replace("silicon-smelter", block_name)
                                        elif block_type == "SolarGenerator":
                                            new_name = texture.replace("solar-panel", block_name)
                                        elif block_type == "StorageBlock":
                                            new_name = texture.replace("container", block_name)
                                        elif block_type == "conduit":
                                            new_name = texture.replace("conduit", block_name)
                                        elif block_type == "ConsumeGenerator":
                                            new_name = texture.replace("rtg-generator", block_name)
                                        elif block_type == "PowerNode":
                                            new_name = texture.replace("power-node", block_name)
                                        elif block_type == "Router":
                                            new_name = texture.replace("router", block_name)
                                        elif block_type == "Junction":
                                            new_name = texture.replace("junction", block_name)
                                        elif block_type == "Unloader":
                                            new_name = texture.replace("unloader", block_name)
                                        elif block_type == "LiquidRouter":
                                            new_name = texture.replace("liquid-router", block_name)
                                        elif block_type == "LiquidJunction":
                                            new_name = texture.replace("liquid-junction", block_name)
                                        elif block_type == "ThermalGenerator":
                                            new_name = texture.replace("thermal-generator", block_name)
                                        elif block_type == "BeamNode":
                                            new_name = texture.replace("beam-node", block_name)
                                        elif block_type == "Pump":
                                            new_name = texture.replace("rotary-pump", block_name)
                                        elif block_type == "SolidPump":
                                            new_name = texture.replace("water-extractor", block_name)
                                        elif block_type == "MendProjector":
                                            new_name = texture.replace("mend-projector", block_name)
                                        elif block_type == "OverdriveProjector":
                                            new_name = texture.replace("overdrive-projector", block_name)
                                        else:
                                            new_name = f"{block_name}{texture[texture.find('-'):]}" if '-' in texture else f"{block_name}.png"
                                        
                                        texture_path = os.path.join(sprite_folder, new_name)
                                        
                                        if not os.path.exists(texture_path):
                                            texture_url = f"{base_url}{texture}"
                                            urllib.request.urlretrieve(texture_url, texture_path)
                                            resize_image(texture_path, size_multiplier)
                                            progress_label.configure(text=f"{LangT("Загружено:")} {new_name}")
                                        
                                        downloaded += 1
                                        progress_window.after(100, update_progress)
                                    
                                    except Exception as e:
                                        progress_label.configure(text=f"{LangT("Ошибка загрузки:")} {texture}")
                                        print(f"{LangT("Ошибка при загрузке")} {texture}: {str(e)}")
                                        downloaded += 1  # Все равно увеличиваем счетчик
                                
                                progress_window.after(100, finish_saving)
                            
                            except Exception as e:
                                progress_window.after(100, lambda: error_occurred(str(e)))
                        
                        def finish_saving():
                            try:
                                block_path = os.path.join(content_folder, f"{block_name}.json")
                                with open(block_path, "w", encoding="utf-8") as f:
                                    json.dump(block_data, f, indent=4, ensure_ascii=False)
                                
                                progress_window.destroy()
                                for child in btn_frame.winfo_children():
                                    child.configure(state="normal")
                                
                                messagebox.showinfo(LangT("Успех"), f"{LangT("Блок")} '{block_name}' {LangT("успешно сохранён!")}")
                                safe_navigation(self.main_app.show_content_buttons())
                            
                            except Exception as e:
                                error_occurred(str(e))
                        
                        def error_occurred(error_msg):
                            progress_window.destroy()
                            for child in btn_frame.winfo_children():
                                child.configure(state="normal")
                            messagebox.showerror(LangT("Ошибка"), f"{LangT("Не удалось сохранить блок:")} {error_msg}")
                        
                        # Запускаем загрузку в отдельном потоке
                        threading.Thread(target=download_textures, daemon=True).start()

                    except Exception as e:
                        messagebox.showerror(LangT("Ошибка"), f"{LangT("Не удалось начать сохранение:")} {str(e)}")
                        # Восстанавливаем состояние кнопок на случай ошибки
                        for child in btn_frame.winfo_children():
                            child.configure(state="normal")
                
                ctk.CTkButton(btn_frame, 
                            text=LangT("Сохранить"), 
                            width=140, 
                            height=45,
                            font=("Arial", 14),
                            command=save_requirements).pack(side="left", padx=20)
                
                ctk.CTkButton(btn_frame, 
                            text=LangT("Отмена"), 
                            width=140, 
                            height=45,
                            font=("Arial", 14),
                            fg_color="#e62525", 
                            hover_color="#701c1c", border_color="#701c1c",
                            command=lambda: safe_navigation(self.main_app.show_content_buttons())).pack(side="left", padx=20)

    def open_GenericCrafter_editor(self, block_name, block_data, editor_type="items_input"):
                """
                Универсальный редактор для GenericCrafter
                editor_type: "items_input", "liquids_input", "items_output", "liquids_output"
                """
                self.clear_window()
                self.root.configure(fg_color="#2b2b2b")
                
                # Определяем параметры в зависимости от типа редактора
                config = {
                    "items_input": {
                        "title": LangT("потребляемых предметов"),
                        "resource_type": "items",
                        "default_resources": [
                            "copper", "lead", "metaglass", "graphite", "sand", 
                            "coal", "titanium", "thorium", "scrap", "silicon",
                            "plastanium", "phase-fabric", "surge-alloy", "spore-pod", 
                            "blast-compound", "pyratite"
                        ],
                        "resource_folder": "items",
                        "icon_loader": "item",
                        "data_key": "consumes",
                        "next_editor": "liquids_input",
                        "entry_type": "int",
                        "entry_color": "#BE6F24",
                        "border_color": "#613e11"
                    },
                    "liquids_input": {
                        "title": LangT("потребляемых жидкостей"), 
                        "resource_type": "liquids",
                        "default_resources": ["water", "slag", "oil", "cryofluid"],
                        "resource_folder": "liquids",
                        "icon_loader": "liquid",
                        "data_key": "consumes",
                        "next_editor": "items_output",
                        "entry_type": "float",
                        "entry_color": "#3a7ebf",
                        "border_color": "#1f4b7a"
                    },
                    "items_output": {
                        "title": LangT("выходных предметов"),
                        "resource_type": "items",
                        "default_resources": [
                            "copper", "lead", "metaglass", "graphite", "sand", 
                            "coal", "titanium", "thorium", "scrap", "silicon",
                            "plastanium", "phase-fabric", "surge-alloy", "spore-pod", 
                            "blast-compound", "pyratite"
                        ],
                        "resource_folder": "items",
                        "icon_loader": "item", 
                        "data_key": "outputItems",
                        "next_editor": "liquids_output",
                        "entry_type": "int",
                        "entry_color": "#2e8b57",
                        "border_color": "#1a5232"
                    },
                    "liquids_output": {
                        "title": LangT("выходных жидкостей"),
                        "resource_type": "liquids", 
                        "default_resources": ["water", "slag", "oil", "cryofluid"],
                        "resource_folder": "liquids",
                        "icon_loader": "liquid",
                        "data_key": "outputLiquids",
                        "next_editor": "requirements",
                        "entry_type": "float",
                        "entry_color": "#3a7ebf",
                        "border_color": "#1f4b7a"
                    }
                }
                
                cfg = config[editor_type]
                
                main_frame = ctk.CTkFrame(self.root, fg_color="transparent")
                main_frame.pack(padx=10, pady=10, fill="both", expand=True)
                
                # Header
                header_frame = ctk.CTkFrame(main_frame, height=90, fg_color="#3a3a3a", corner_radius=8)
                header_frame.pack(fill="x", pady=(0, 15))
                
                try:
                    block_type = block_data.get("type")
                    texture_path = os.path.join("mindustry_mod_creator", "mods", self.mod_name, "sprites", block_type, block_name, f"{block_name}.png")
                    if os.path.exists(texture_path):
                        img = Image.open(texture_path)
                        img = img.resize((70, 70), Image.LANCZOS)
                        ctk_img = ctk.CTkImage(light_image=img, size=(70, 70))
                        img_label = ctk.CTkLabel(header_frame, image=ctk_img, text="")
                        img_label.pack(side="left", padx=20)
                except Exception as e:
                    print(f"{LangT("Ошибка загрузки изображения:")} {e}")
                
                ctk.CTkLabel(header_frame, 
                            text=f"{LangT("Редактор")} {cfg['title']}: {block_name}",
                            font=("Arial", 18, "bold")).pack(side="left", padx=10)
                
                content_frame = ctk.CTkFrame(main_frame, fg_color="#3a3a3a", corner_radius=8)
                content_frame.pack(fill="both", expand=True)
                
                def load_resource_icon(resource_name):
                    icon_paths = [
                        os.path.join(self.mod_folder, "sprites", cfg["resource_folder"], f"{resource_name}.png"),
                        os.path.join("mindustry_mod_creator", "sprites", cfg["resource_folder"], f"{resource_name}.png"),
                        os.path.join("mindustry_mod_creator", "icons", f"{resource_name}.png")
                    ]
                    for path in icon_paths:
                        if os.path.exists(path):
                            try:
                                img = Image.open(path)
                                img = img.resize((50, 50), Image.LANCZOS)
                                return ctk.CTkImage(light_image=img, size=(50, 50))
                            except:
                                continue
                    return None
                
                # Получаем списки ресурсов
                default_resources = cfg["default_resources"]
                
                mod_resources = []
                mod_resources_path = os.path.join(self.mod_folder, "content", cfg["resource_folder"])
                if os.path.exists(mod_resources_path):
                    mod_resources = [f.replace(".json", "") for f in os.listdir(mod_resources_path) if f.endswith(".json")]

                default_resource_entries = {}
                mod_resource_entries = {}

                def create_resource_card(parent, resource, is_mod_resource=False):
                    card_frame = ctk.CTkFrame(parent, 
                                            fg_color="#4a4a4a", 
                                            corner_radius=8,
                                            height=180)
                    card_frame.pack_propagate(False)
                    
                    content_frame = ctk.CTkFrame(card_frame, fg_color="transparent")
                    content_frame.pack(fill="both", expand=True, padx=10, pady=10)
                    
                    top_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
                    top_frame.pack(fill="x", pady=(0, 10))
                    
                    icon = load_resource_icon(resource)
                    if icon:
                        ctk.CTkLabel(top_frame, image=icon, text="").pack()
                    
                    ctk.CTkLabel(top_frame, 
                                text=resource.capitalize(), 
                                font=("Arial", 14),
                                anchor="center").pack()
                    
                    bottom_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
                    bottom_frame.pack(fill="x", pady=(10, 0))

                    # Создаем переменные в зависимости от типа
                    if cfg["entry_type"] == "int":
                        value_var = tk.IntVar(value=0)
                        max_value = 50
                    else:  # float
                        value_var = tk.DoubleVar(value=0.0)
                        max_value = 50.0
                        
                    str_value = tk.StringVar(value="0" if cfg["entry_type"] == "int" else "0.0")

                    def sync_values(*args):
                        try:
                            val = str_value.get()
                            if cfg["entry_type"] == "int":
                                value_var.set(int(val) if val else 0)
                            else:
                                value_var.set(float(val) if val else 0.0)
                        except:
                            if cfg["entry_type"] == "int":
                                value_var.set(0)
                            else:
                                value_var.set(0.0)
                    
                    str_value.trace_add("write", sync_values)
                    
                    def validate_input(new_val):
                        if new_val == "":
                            return True
                        if cfg["entry_type"] == "int":
                            if not new_val.isdigit():
                                return False
                            if len(new_val) > 2:
                                return False
                            if int(new_val) > max_value:
                                return False
                        else:  # float
                            try:
                                val = float(new_val)
                                if val < 0 or val > max_value:
                                    return False
                            except ValueError:
                                return False
                        return True
                    
                    validation = parent.register(validate_input)
                    
                    controls_frame = ctk.CTkFrame(bottom_frame, fg_color="transparent")
                    controls_frame.pack(fill="x", pady=5)
                    
                    controls_frame.grid_columnconfigure(0, weight=0, minsize=35)
                    controls_frame.grid_columnconfigure(1, weight=1, minsize=70)
                    controls_frame.grid_columnconfigure(2, weight=0, minsize=35)
                    
                    def update_value(change):
                        try:
                            current = str_value.get()
                            try:
                                if cfg["entry_type"] == "int":
                                    current_num = int(current) if current else 0
                                else:
                                    current_num = float(current) if current else 0.0
                            except ValueError:
                                current_num = 0 if cfg["entry_type"] == "int" else 0.0
                            new_value = max(0, min(max_value, current_num + change))
                            if cfg["entry_type"] == "int":
                                str_value.set(str(int(new_value)))
                            else:
                                str_value.set(f"{new_value:.1f}")
                        except Exception as e:
                            if cfg["entry_type"] == "int":
                                str_value.set("0")
                            else:
                                str_value.set("0.0")

                    def start_increment(change):
                        global is_pressed
                        is_pressed = True
                        update_value(change)
                        self.root.after(100, lambda: repeat_increment(change))

                    def stop_increment():
                        global is_pressed
                        is_pressed = False

                    def repeat_increment(change):
                        if is_pressed:
                            update_value(change)
                            self.root.after(100, lambda: repeat_increment(change))

                    minus_btn = ctk.CTkButton(
                        controls_frame,
                        text="-",
                        width=35,
                        height=35,
                        font=("Arial", 16),
                        fg_color="#e62525",
                        hover_color="#701c1c",
                        border_color="#701c1c",
                        corner_radius=6,
                        anchor="center"
                    )
                    minus_btn.grid(row=0, column=0, padx=(0, 5), sticky="nsew")
                    minus_btn.bind("<ButtonPress-1>", lambda e: start_increment(-1 if cfg["entry_type"] == "int" else -0.1))
                    minus_btn.bind("<ButtonRelease-1>", lambda e: stop_increment())

                    entry = ctk.CTkEntry(
                        controls_frame,
                        width=70,
                        height=35,
                        font=("Arial", 14),
                        textvariable=str_value,
                        fg_color=cfg["entry_color"],
                        border_color=cfg["border_color"],
                        justify="center",
                        validate="key",
                        validatecommand=(validation, "%P")
                    )
                    entry.grid(row=0, column=1, padx=5, sticky="ew")

                    plus_btn = ctk.CTkButton(
                        controls_frame,
                        text="+",
                        width=35,
                        height=35,
                        font=("Arial", 16),
                        corner_radius=6,
                        anchor="center"
                    )
                    plus_btn.grid(row=0, column=2, padx=(5, 0), sticky="nsew")
                    plus_btn.bind("<ButtonPress-1>", lambda e: start_increment(1 if cfg["entry_type"] == "int" else 0.1))
                    plus_btn.bind("<ButtonRelease-1>", lambda e: stop_increment())
                    
                    def handle_focus_out(event):
                        if str_value.get() == "":
                            str_value.set("0" if cfg["entry_type"] == "int" else "0.0")
                    
                    entry.bind("<FocusOut>", handle_focus_out)
                    
                    if is_mod_resource:
                        mod_resource_entries[resource] = value_var
                    else:
                        default_resource_entries[resource] = value_var
                    
                    return card_frame
                
                def calculate_columns(container_width):
                    min_card_width = 180
                    spacing = 10
                    max_columns = max(1, container_width // (min_card_width + spacing))
                    if max_columns * (min_card_width + spacing) - spacing <= container_width:
                        return max_columns, min_card_width
                    return 1, -1
                
                def update_grid(canvas, items_frame, items):
                    container_width = canvas.winfo_width()
    
                    # Проверяем, действительно ли изменился размер
                    if (widget_id in self.last_widths and 
                        container_width == self.last_widths[widget_id] and 
                        container_width > 100):
                        return
                        
                    self.last_widths[widget_id] = container_width

                    if container_width < 1:
                        return
                    
                    columns, card_width = calculate_columns(container_width)
                    
                    for widget in items_frame.grid_slaves():
                        widget.grid_forget()
                    
                    for i, item in enumerate(items):
                        row = i // columns
                        col = i % columns
                        is_mod_resource = item in mod_resources
                        card = create_resource_card(items_frame, item, is_mod_resource)
                        if card_width == -1:
                            card.configure(width=container_width - 20)
                        else:
                            card.configure(width=card_width)
                        card.grid(row=row, column=col, padx=5, pady=5, sticky="nsew")
                    
                    items_frame.update_idletasks()
                    canvas.configure(scrollregion=canvas.bbox("all"))
                    
                    if items_frame.winfo_height() <= canvas.winfo_height():
                        canvas.yview_moveto(0)
                        scrollbar.pack_forget()
                    else:
                        scrollbar.pack(side="right", fill="y")
                
                # Создаем скроллируемый контейнер
                canvas = tk.Canvas(content_frame, bg="#3a3a3a", highlightthickness=0)
                scrollbar = ctk.CTkScrollbar(content_frame, orientation="vertical", command=canvas.yview)
                canvas.configure(yscrollcommand=scrollbar.set)
                
                scrollbar.pack(side="right", fill="y")
                canvas.pack(side="left", fill="both", expand=True, padx=10, pady=10)
                
                items_frame = ctk.CTkFrame(canvas, fg_color="#3a3a3a")
                canvas.create_window((0, 0), window=items_frame, anchor="nw")

                def on_mousewheel(event):
                    canvas.yview_scroll(int(-1*(event.delta/120)),"units")
                canvas.bind("<MouseWheel>", on_mousewheel)
                canvas.bind("<Button-4>", lambda e: canvas.yview_scroll(-1, "units"))
                canvas.bind("<Button-5>", lambda e: canvas.yview_scroll(1, "units"))
                
                # Объединяем все ресурсы в один список
                all_resources = default_resources + mod_resources
                update_grid(canvas, items_frame, all_resources)
                
                widget_id = f"requirements_{block_name}"
                resize_handler = self.setup_resize_protection(widget_id, 
                    lambda: update_grid(canvas, items_frame, all_resources), 
                    delay=300)
                canvas.bind("<Configure>", resize_handler)
                items_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
                
                footer_frame = ctk.CTkFrame(main_frame, height=70, fg_color="#3a3a3a", corner_radius=8)
                footer_frame.pack(fill="x", pady=(15, 0))
                
                btn_frame = ctk.CTkFrame(footer_frame, fg_color="transparent")
                btn_frame.pack(expand=True, pady=15)

                def save_requirements():
                    resources_list = []
                    
                    # Обрабатываем ресурсы в зависимости от типа редактора
                    entries_dict = {**default_resource_entries, **mod_resource_entries}
                    
                    for resource, var in entries_dict.items():
                        amount = var.get()
                        if amount > 0:
                            if cfg["entry_type"] == "float" and editor_type in ["liquids_input", "liquids_output"]:
                                # Для жидкостей пересчитываем amount
                                calculated_amount = round((1 / 60) * amount, 25)
                                resources_list.append({
                                    cfg["resource_type"][:-1]: resource,  # "items" -> "item", "liquids" -> "liquid"
                                    "amount": calculated_amount
                                })
                            else:
                                # Для предметов используем исходное значение
                                resources_list.append({
                                    cfg["resource_type"][:-1]: resource,
                                    "amount": amount
                                })
                    
                    # Проверки в зависимости от типа редактора
                    if not resources_list:
                        if editor_type == "items_input" and not block_data["consumes"].get("liquids"):
                            messagebox.showwarning(LangT("Ошибка"), LangT("Вы не добавили ни одного предмета!"))
                            return
                        elif editor_type == "liquids_input" and not block_data["consumes"].get("items"):
                            messagebox.showwarning(LangT("Ошибка"), LangT("Вы не добавили ни жидкостей, ни предметов!"))
                            return
                        elif editor_type == "items_output" and not block_data.get("outputLiquids"):
                            messagebox.showwarning(LangT("Ошибка"), LangT("Вы не добавили ни предметов!"))
                            return
                        elif editor_type == "liquids_output" and not block_data.get("outputItems"):
                            messagebox.showwarning(LangT("Ошибка"), LangT("Вы не добавили ни жидкостей, ни предметов!"))
                            return
                    
                    # Сохраняем данные в соответствующую структуру
                    if editor_type in ["items_input", "liquids_input"]:
                        if "consumes" not in block_data:
                            block_data["consumes"] = {}
                        if editor_type == "items_input":
                            block_data["consumes"]["items"] = resources_list
                        else:  # liquids_input
                            block_data["consumes"]["liquids"] = resources_list
                    else:  # output editors
                        if editor_type == "items_output":
                            block_data["outputItems"] = resources_list
                        else:  # liquids_output
                            block_data["outputLiquids"] = resources_list
                            clean_empty_consumes(block_data)
                    
                    try:
                        block_type = block_data.get("type")
                        content_folder = os.path.join("mindustry_mod_creator", "mods", self.mod_name, "content", "blocks", block_type)
                        os.makedirs(content_folder, exist_ok=True)
                        
                        block_path = os.path.join(content_folder, f"{block_name}.json")
                        with open(block_path, "w", encoding="utf-8") as f:
                            json.dump(block_data, f, indent=4, ensure_ascii=False)
                        
                        messagebox.showinfo(LangT("Успех"), f"{cfg['title'].capitalize()} {LangT("для блока")} '{block_name}' {LangT("успешно сохранены!")}")
                        
                        # Переход к следующему редактору
                        if cfg["next_editor"] == "liquids_input":
                            self.open_GenericCrafter_editor(block_name, block_data, "liquids_input")
                        elif cfg["next_editor"] == "items_output":
                            self.open_GenericCrafter_editor(block_name, block_data, "items_output")
                        elif cfg["next_editor"] == "liquids_output":
                            self.open_GenericCrafter_editor(block_name, block_data, "liquids_output")
                        else:  # requirements
                            self.open_requirements_editor(block_name, block_data)
                    
                    except Exception as e:
                        messagebox.showerror(LangT("Ошибка"), f"{LangT("Не удалось сохранить")} {cfg['resource_type']}: {str(e)}")
                
                def skip_resources():
                    # Проверки для пропуска в зависимости от типа редактора
                    if editor_type == "liquids_input" and not block_data["consumes"].get("items"):
                        messagebox.showerror(LangT("Ошибка"), LangT("Вы не добавили предмет, нельзя пропустить жидкость"))
                        return
                    elif editor_type == "items_output" and not block_data.get("outputLiquids"):
                        # Для items_output проверяем, есть ли выходные жидкости
                        pass
                    elif editor_type == "liquids_output" and not block_data.get("outputItems"):
                        messagebox.showerror(LangT("Ошибка"), LangT("Вы не добавили предмет, нельзя пропустить жидкость"))
                        return
                    
                    # Переход к следующему редактору
                    if cfg["next_editor"] == "liquids_input":
                        self.open_GenericCrafter_editor(block_name, block_data, "liquids_input")
                    elif cfg["next_editor"] == "items_output":
                        self.open_GenericCrafter_editor(block_name, block_data, "items_output")
                    elif cfg["next_editor"] == "liquids_output":
                        self.open_GenericCrafter_editor(block_name, block_data, "liquids_output")
                    else:  # requirements
                        if editor_type == "liquids_output":
                            self.clean_empty_consumes(block_data)
                        self.open_requirements_editor(block_name, block_data)
                
                def clean_empty_consumes(block_data):
                    """Проверяет и удаляет пустые массивы в структуре consumes и outputLiquids/outputItems"""
                    if "consumes" in block_data:
                        consumes = block_data["consumes"]
                        
                        if consumes == {}:
                            del block_data["consumes"]
                        else:
                            if "items" in consumes and isinstance(consumes["items"], list) and len(consumes["items"]) == 0:
                                del consumes["items"]
                            
                            if "liquids" in consumes and isinstance(consumes["liquids"], list) and len(consumes["liquids"]) == 0:
                                del consumes["liquids"]
                            
                            if consumes == {}:
                                del block_data["consumes"]
                    
                    if "outputLiquids" in block_data and isinstance(block_data["outputLiquids"], list) and len(block_data["outputLiquids"]) == 0:
                        del block_data["outputLiquids"]
                    
                    if "outputItems" in block_data and isinstance(block_data["outputItems"], list) and len(block_data["outputItems"]) == 0:
                        del block_data["outputItems"]

                    if "liquidCapacity" in block_data and block_data["liquidCapacity"] == 0:
                        del block_data["liquidCapacity"]
                    
                    if "itemCapacity" in block_data and block_data["itemCapacity"] == 0:
                        del block_data["itemCapacity"]
                    
                    return block_data
                
                ctk.CTkButton(btn_frame, 
                            text=LangT("Сохранить"), 
                            width=140, 
                            height=45,
                            font=("Arial", 14),
                            command=save_requirements).pack(side="left", padx=20)
                
                ctk.CTkButton(btn_frame, 
                            text=LangT("Пропустить"), 
                            width=140, 
                            height=45,
                            font=("Arial", 14),
                            fg_color="#e62525", 
                            hover_color="#701c1c", border_color="#701c1c",
                            command=skip_resources).pack(side="left", padx=20)

    def open_consumes_editor(self, block_name, block_data, editor_type="items"):
                """
                Универсальный редактор для потребляемых ресурсов
                editor_type: "items" - предметы, "liquids" - жидкости
                """
                self.clear_window()
                self.root.configure(fg_color="#2b2b2b")
                
                # Определяем параметры в зависимости от типа редактора
                config = {
                    "items": {
                        "title": LangT("потребляемых предметов"),
                        "resource_type": "items",
                        "default_resources": [
                            "copper", "lead", "metaglass", "graphite", "sand", 
                            "coal", "titanium", "thorium", "scrap", "silicon",
                            "plastanium", "phase-fabric", "surge-alloy", "spore-pod", 
                            "blast-compound", "pyratite"
                        ],
                        "resource_folder": "items",
                        "data_key": "consumes",
                        "next_editor": "liquids",
                        "entry_type": "int",
                        "entry_color": "#BE6F24",
                        "border_color": "#613e11",
                        "increment": 1
                    },
                    "liquids": {
                        "title": LangT("потребляемых жидкостей"), 
                        "resource_type": "liquids",
                        "default_resources": ["water", "slag", "oil", "cryofluid"],
                        "resource_folder": "liquids",
                        "data_key": "consumes",
                        "next_editor": "requirements",
                        "entry_type": "float",
                        "entry_color": "#3a7ebf",
                        "border_color": "#1f4b7a",
                        "increment": 0.1
                    }
                }
                
                cfg = config[editor_type]
                
                main_frame = ctk.CTkFrame(self.root, fg_color="transparent")
                main_frame.pack(padx=10, pady=10, fill="both", expand=True)
                
                header_frame = ctk.CTkFrame(main_frame, height=90, fg_color="#3a3a3a", corner_radius=8)
                header_frame.pack(fill="x", pady=(0, 15))
                
                try:
                    block_type = block_data.get("type")
                    texture_path = os.path.join("mindustry_mod_creator", "mods", self.mod_name, "sprites", block_type, block_name, f"{block_name}.png")
                    if os.path.exists(texture_path):
                        img = Image.open(texture_path)
                        img = img.resize((70, 70), Image.LANCZOS)
                        ctk_img = ctk.CTkImage(light_image=img, size=(70, 70))
                        img_label = ctk.CTkLabel(header_frame, image=ctk_img, text="")
                        img_label.pack(side="left", padx=20)
                except Exception as e:
                    print(f"{LangT("Ошибка загрузки изображения:")} {e}")
                
                ctk.CTkLabel(header_frame, 
                            text=f"{LangT("Редактор")} {cfg['title']}: {block_name}",
                            font=("Arial", 18, "bold")).pack(side="left", padx=10)
                
                content_frame = ctk.CTkFrame(main_frame, fg_color="#3a3a3a", corner_radius=8)
                content_frame.pack(fill="both", expand=True)
                
                def load_resource_icon(resource_name):
                    icon_paths = [
                        os.path.join(self.mod_folder, "sprites", cfg["resource_folder"], f"{resource_name}.png"),
                        os.path.join("mindustry_mod_creator", "sprites", cfg["resource_folder"], f"{resource_name}.png"),
                        os.path.join("mindustry_mod_creator", "icons", f"{resource_name}.png")
                    ]
                    for path in icon_paths:
                        if os.path.exists(path):
                            try:
                                img = Image.open(path)
                                img = img.resize((50, 50), Image.LANCZOS)
                                return ctk.CTkImage(light_image=img, size=(50, 50))
                            except:
                                continue
                    return None
                
                # Получаем списки ресурсов
                default_resources = cfg["default_resources"]
                
                mod_resources = []
                mod_resources_path = os.path.join(self.mod_folder, "content", cfg["resource_folder"])
                if os.path.exists(mod_resources_path):
                    mod_resources = [f.replace(".json", "") for f in os.listdir(mod_resources_path) if f.endswith(".json")]

                default_resource_entries = {}
                mod_resource_entries = {}

                def create_resource_card(parent, resource, is_mod_resource=False):
                    card_frame = ctk.CTkFrame(parent, 
                                            fg_color="#4a4a4a", 
                                            corner_radius=8,
                                            height=180)
                    card_frame.pack_propagate(False)
                    
                    content_frame = ctk.CTkFrame(card_frame, fg_color="transparent")
                    content_frame.pack(fill="both", expand=True, padx=10, pady=10)
                    
                    top_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
                    top_frame.pack(fill="x", pady=(0, 10))
                    
                    icon = load_resource_icon(resource)
                    if icon:
                        ctk.CTkLabel(top_frame, image=icon, text="").pack()
                    
                    ctk.CTkLabel(top_frame, 
                                text=resource.capitalize(), 
                                font=("Arial", 14),
                                anchor="center").pack()
                    
                    bottom_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
                    bottom_frame.pack(fill="x", pady=(10, 0))

                    # Создаем переменные в зависимости от типа
                    if cfg["entry_type"] == "int":
                        value_var = tk.IntVar(value=0)
                        max_value = 50
                    else:  # float
                        value_var = tk.DoubleVar(value=0.0)
                        max_value = 50.0
                        
                    str_value = tk.StringVar(value="0" if cfg["entry_type"] == "int" else "0.0")

                    def sync_values(*args):
                        try:
                            val = str_value.get()
                            if cfg["entry_type"] == "int":
                                value_var.set(int(val) if val else 0)
                            else:
                                value_var.set(float(val) if val else 0.0)
                        except:
                            if cfg["entry_type"] == "int":
                                value_var.set(0)
                            else:
                                value_var.set(0.0)
                    
                    str_value.trace_add("write", sync_values)
                    
                    def validate_input(new_val):
                        if new_val == "":
                            return True
                        if cfg["entry_type"] == "int":
                            if not new_val.isdigit():
                                return False
                            if len(new_val) > 2:
                                return False
                            if int(new_val) > max_value:
                                return False
                        else:  # float
                            try:
                                val = float(new_val)
                                if val < 0 or val > max_value:
                                    return False
                            except ValueError:
                                return False
                        return True
                    
                    validation = parent.register(validate_input)
                    
                    controls_frame = ctk.CTkFrame(bottom_frame, fg_color="transparent")
                    controls_frame.pack(fill="x", pady=5)
                    
                    controls_frame.grid_columnconfigure(0, weight=0, minsize=35)
                    controls_frame.grid_columnconfigure(1, weight=1, minsize=70)
                    controls_frame.grid_columnconfigure(2, weight=0, minsize=35)
                    
                    def update_value(change):
                        try:
                            current = str_value.get()
                            try:
                                if cfg["entry_type"] == "int":
                                    current_num = int(current) if current else 0
                                else:
                                    current_num = float(current) if current else 0.0
                            except ValueError:
                                current_num = 0 if cfg["entry_type"] == "int" else 0.0
                            new_value = max(0, min(max_value, current_num + change))
                            if cfg["entry_type"] == "int":
                                str_value.set(str(int(new_value)))
                            else:
                                str_value.set(f"{new_value:.1f}")
                        except Exception as e:
                            if cfg["entry_type"] == "int":
                                str_value.set("0")
                            else:
                                str_value.set("0.0")

                    def start_increment(change):
                        global is_pressed
                        is_pressed = True
                        update_value(change)
                        self.root.after(100, lambda: repeat_increment(change))

                    def stop_increment():
                        global is_pressed
                        is_pressed = False

                    def repeat_increment(change):
                        if is_pressed:
                            update_value(change)
                            self.root.after(100, lambda: repeat_increment(change))

                    minus_btn = ctk.CTkButton(
                        controls_frame,
                        text="-",
                        width=35,
                        height=35,
                        font=("Arial", 16),
                        fg_color="#e62525",
                        hover_color="#701c1c",
                        border_color="#701c1c",
                        corner_radius=6,
                        anchor="center"
                    )
                    minus_btn.grid(row=0, column=0, padx=(0, 5), sticky="nsew")
                    minus_btn.bind("<ButtonPress-1>", lambda e: start_increment(-cfg["increment"]))
                    minus_btn.bind("<ButtonRelease-1>", lambda e: stop_increment())

                    entry = ctk.CTkEntry(
                        controls_frame,
                        width=70,
                        height=35,
                        font=("Arial", 14),
                        textvariable=str_value,
                        fg_color=cfg["entry_color"],
                        border_color=cfg["border_color"],
                        justify="center",
                        validate="key",
                        validatecommand=(validation, "%P")
                    )
                    entry.grid(row=0, column=1, padx=5, sticky="ew")

                    plus_btn = ctk.CTkButton(
                        controls_frame,
                        text="+",
                        width=35,
                        height=35,
                        font=("Arial", 16),
                        corner_radius=6,
                        anchor="center"
                    )
                    plus_btn.grid(row=0, column=2, padx=(5, 0), sticky="nsew")
                    plus_btn.bind("<ButtonPress-1>", lambda e: start_increment(cfg["increment"]))
                    plus_btn.bind("<ButtonRelease-1>", lambda e: stop_increment())
                    
                    def handle_focus_out(event):
                        if str_value.get() == "":
                            str_value.set("0" if cfg["entry_type"] == "int" else "0.0")
                    
                    entry.bind("<FocusOut>", handle_focus_out)
                    
                    if is_mod_resource:
                        mod_resource_entries[resource] = value_var
                    else:
                        default_resource_entries[resource] = value_var
                    
                    return card_frame
                
                def calculate_columns(container_width):
                    min_card_width = 180
                    spacing = 10
                    max_columns = max(1, container_width // (min_card_width + spacing))
                    if max_columns * (min_card_width + spacing) - spacing <= container_width:
                        return max_columns, min_card_width
                    return 1, -1
                
                def update_grid(canvas, items_frame, items):
                    container_width = canvas.winfo_width()
    
                    # Проверяем, действительно ли изменился размер
                    if (widget_id in self.last_widths and 
                        container_width == self.last_widths[widget_id] and 
                        container_width > 100):
                        return
                        
                    self.last_widths[widget_id] = container_width

                    if container_width < 1:
                        return
                    
                    columns, card_width = calculate_columns(container_width)
                    
                    for widget in items_frame.grid_slaves():
                        widget.grid_forget()
                    
                    for i, item in enumerate(items):
                        row = i // columns
                        col = i % columns
                        is_mod_resource = item in mod_resources
                        card = create_resource_card(items_frame, item, is_mod_resource)
                        if card_width == -1:
                            card.configure(width=container_width - 20)
                        else:
                            card.configure(width=card_width)
                        card.grid(row=row, column=col, padx=5, pady=5, sticky="nsew")
                    
                    items_frame.update_idletasks()
                    canvas.configure(scrollregion=canvas.bbox("all"))
                    
                    if items_frame.winfo_height() <= canvas.winfo_height():
                        canvas.yview_moveto(0)
                        scrollbar.pack_forget()
                    else:
                        scrollbar.pack(side="right", fill="y")
                
                # Создаем скроллируемый контейнер
                canvas = tk.Canvas(content_frame, bg="#3a3a3a", highlightthickness=0)
                scrollbar = ctk.CTkScrollbar(content_frame, orientation="vertical", command=canvas.yview)
                canvas.configure(yscrollcommand=scrollbar.set)
                
                scrollbar.pack(side="right", fill="y")
                canvas.pack(side="left", fill="both", expand=True, padx=10, pady=10)
                
                items_frame = ctk.CTkFrame(canvas, fg_color="#3a3a3a")
                canvas.create_window((0, 0), window=items_frame, anchor="nw")

                def on_mousewheel(event):
                    canvas.yview_scroll(int(-1*(event.delta/120)),"units")
                canvas.bind("<MouseWheel>", on_mousewheel)
                canvas.bind("<Button-4>", lambda e: canvas.yview_scroll(-1, "units"))
                canvas.bind("<Button-5>", lambda e: canvas.yview_scroll(1, "units"))
                
                # Объединяем все ресурсы в один список
                all_resources = default_resources + mod_resources
                update_grid(canvas, items_frame, all_resources)
                
                widget_id = f"requirements_{block_name}"
                resize_handler = self.setup_resize_protection(widget_id, 
                    lambda: update_grid(canvas, items_frame, all_resources), 
                    delay=300)
                canvas.bind("<Configure>", resize_handler)
                items_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
                
                footer_frame = ctk.CTkFrame(main_frame, height=70, fg_color="#3a3a3a", corner_radius=8)
                footer_frame.pack(fill="x", pady=(15, 0))
                
                btn_frame = ctk.CTkFrame(footer_frame, fg_color="transparent")
                btn_frame.pack(expand=True, pady=15)

                def save_requirements():
                    resources_list = []
                    
                    # Обрабатываем ресурсы в зависимости от типа редактора
                    for resource, var in default_resource_entries.items():
                        amount = var.get()
                        if amount > 0:
                            if editor_type == "liquids":
                                # Для жидкостей пересчитываем amount
                                calculated_amount = round((1 / 60) * amount, 25)
                                resources_list.append({
                                    "liquid": resource,
                                    "amount": calculated_amount
                                })
                            else:
                                # Для предметов используем исходное значение
                                resources_list.append({
                                    "item": resource,
                                    "amount": amount
                                })
                    
                    for resource, var in mod_resource_entries.items():
                        amount = var.get()
                        if amount > 0:
                            if editor_type == "liquids":
                                calculated_amount = round((1 / 60) * amount, 25)
                                resources_list.append({
                                    "liquid": resource,
                                    "amount": calculated_amount
                                })
                            else:
                                resources_list.append({
                                    "item": resource,
                                    "amount": amount
                                })
                    
                    # Проверки в зависимости от типа редактора
                    if not resources_list:
                        if editor_type == "items" and not block_data["consumes"].get("liquids"):
                            messagebox.showerror(LangT("Ошибка"), LangT("Должно быть хотя бы что-то одно: предметы ИЛИ жидкости!"))
                            return
                        elif editor_type == "liquids" and not block_data["consumes"].get("items"):
                            messagebox.showerror(LangT("Ошибка"), LangT("Должно быть хотя бы что-то одно: предметы ИЛИ жидкости!"))
                            return
                    
                    # Сохраняем данные в соответствующую структуру
                    if editor_type == "items":
                        block_data["consumes"]["items"] = resources_list
                    else:  # liquids
                        block_data["consumes"]["liquids"] = resources_list
                    
                    try:
                        block_type = block_data.get("type")
                        content_folder = os.path.join("mindustry_mod_creator", "mods", self.mod_name, "content", "blocks", block_type)
                        os.makedirs(content_folder, exist_ok=True)
                        
                        block_path = os.path.join(content_folder, f"{block_name}.json")
                        with open(block_path, "w", encoding="utf-8") as f:
                            json.dump(block_data, f, indent=4, ensure_ascii=False)
                        
                        messagebox.showinfo(LangT("Успех"), f"{cfg['title'].capitalize()} {LangT("для блока")} '{block_name}' {LangT("успешно сохранены!")}")
                        
                        # Переход к следующему редактору
                        if editor_type == "items":
                            self.open_consumes_editor(block_name, block_data, "liquids")
                        else:  # liquids
                            self.open_requirements_editor(block_name, block_data)
                    
                    except Exception as e:
                        messagebox.showerror(LangT("Ошибка"), f"{LangT("Не удалось сохранить")} {cfg['resource_type']}: {str(e)}")
                
                def skip_resources():
                    # Проверки для пропуска в зависимости от типа редактора
                    if editor_type == "liquids" and not block_data["consumes"].get("items"):
                        messagebox.showerror(LangT("Ошибка"), LangT("Если пропустили предмет добавте жидкость"))
                        return
                    
                    # Переход к следующему редактору
                    if editor_type == "items":
                        self.open_consumes_editor(block_name, block_data, "liquids")
                    else:  # liquids
                        if block_data["consumes"].get("items"):
                            self.clean_empty_consumes(block_data)
                        self.open_requirements_editor(block_name, block_data)
                
                def clean_empty_consumes(block_data):
                    """Проверяет и удаляет пустые массивы в структуре consumes"""
                    if "consumes" in block_data:
                        consumes = block_data["consumes"]
                        
                        if consumes == {}:
                            del block_data["consumes"]
                        else:
                            if "items" in consumes and isinstance(consumes["items"], list) and len(consumes["items"]) == 0:
                                del consumes["items"]
                            
                            if "liquids" in consumes and isinstance(consumes["liquids"], list) and len(consumes["liquids"]) == 0:
                                del consumes["liquids"]
                            
                            if consumes == {}:
                                del block_data["consumes"]

                    if "liquidCapacity" in block_data and block_data["liquidCapacity"] == 0:
                        del block_data["liquidCapacity"]
                    
                    if "itemCapacity" in block_data and block_data["itemCapacity"] == 0:
                        del block_data["itemCapacity"]
                    
                    return block_data
                
                ctk.CTkButton(btn_frame, 
                            text=LangT("Сохранить"), 
                            width=140, 
                            height=45,
                            font=("Arial", 14),
                            command=save_requirements).pack(side="left", padx=20)
                
                ctk.CTkButton(btn_frame, 
                            text=LangT("Пропустить"), 
                            width=140, 
                            height=45,
                            font=("Arial", 14),
                            fg_color="#e62525", 
                            hover_color="#701c1c", border_color="#701c1c",
                            command=skip_resources).pack(side="left", padx=20)

    def open_solidpump_liquid_edit(self, block_name, block_data):
                self.clear_window()
                self.root.configure(fg_color="#2b2b2b")
                
                main_frame = ctk.CTkFrame(self.root, fg_color="transparent")
                main_frame.pack(padx=10, pady=10, fill="both", expand=True)
                
                header_frame = ctk.CTkFrame(main_frame, height=90, fg_color="#3a3a3a", corner_radius=8)
                header_frame.pack(fill="x", pady=(0, 15))
                
                try:
                    block_type = block_data.get("type")
                    texture_path = os.path.join("mindustry_mod_creator", "mods", self.mod_name, "sprites", block_type, block_name, f"{block_name}.png")
                    if os.path.exists(texture_path):
                        img = Image.open(texture_path)
                        img = img.resize((70, 70), Image.LANCZOS)
                        ctk_img = ctk.CTkImage(light_image=img, size=(70, 70))
                        img_label = ctk.CTkLabel(header_frame, image=ctk_img, text="")
                        img_label.pack(side="left", padx=20)
                except Exception as e:
                    print(f"{LangT("Ошибка загрузки изображения:")} {e}")
                
                ctk.CTkLabel(header_frame, 
                            text=f"{LangT("Выбор жидкости для насоса:")} {block_name}",
                            font=("Arial", 18, "bold")).pack(side="left", padx=10)
                
                content_frame = ctk.CTkFrame(main_frame, fg_color="#3a3a3a", corner_radius=8)
                content_frame.pack(fill="both", expand=True)
                
                def load_liquid_icon(liquid_name):
                    icon_paths = [
                        os.path.join(self.mod_folder, "sprites", "liquids", f"{liquid_name}.png"),
                        os.path.join("mindustry_mod_creator", "sprites", "liquids", f"{liquid_name}.png"),
                        os.path.join("mindustry_mod_creator", "icons", f"{liquid_name}.png")
                    ]
                    for path in icon_paths:
                        if os.path.exists(path):
                            try:
                                img = Image.open(path)
                                img = img.resize((50, 50), Image.LANCZOS)
                                return ctk.CTkImage(light_image=img, size=(50, 50))
                            except:
                                continue
                    return None
                
                # Списки жидкостей
                default_liquids = ["water", "slag", "oil", "cryofluid"]
                
                mod_liquids = []
                mod_liquids_path = os.path.join(self.mod_folder, "content", "liquids")
                if os.path.exists(mod_liquids_path):
                    mod_liquids = [f.replace(".json", "") for f in os.listdir(mod_liquids_path) if f.endswith(".json")]

                def create_liquid_card(parent, liquid, is_mod_liquid=False):
                    card_frame = ctk.CTkFrame(parent, 
                                            fg_color="#4a4a4a", 
                                            corner_radius=8,
                                            height=180)
                    card_frame.pack_propagate(False)
                    
                    content_frame = ctk.CTkFrame(card_frame, fg_color="transparent")
                    content_frame.pack(fill="both", expand=True, padx=10, pady=10)
                    
                    top_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
                    top_frame.pack(fill="x", pady=(0, 10))
                    
                    icon = load_liquid_icon(liquid)
                    if icon:
                        ctk.CTkLabel(top_frame, image=icon, text="").pack()
                    
                    ctk.CTkLabel(top_frame, 
                                text=liquid.capitalize(), 
                                font=("Arial", 14),
                                anchor="center").pack()
                    
                    bottom_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
                    bottom_frame.pack(fill="x", pady=(10, 0))

                    select_btn = ctk.CTkButton(
                        bottom_frame,
                        text=LangT("Выбрать"),
                        width=120,
                        height=35,
                        font=("Arial", 14),
                        command=lambda: select_liquid(liquid)
                    )
                    select_btn.pack(pady=10)
                    
                    return card_frame
                
                def select_liquid(liquid):
                    # Добавляем {"result": liquid} в JSON блока
                    block_data["result"] = liquid
                    
                    try:
                        block_type = block_data.get("type")
                        content_folder = os.path.join("mindustry_mod_creator", "mods", self.mod_name, "content", "blocks", block_type)
                        os.makedirs(content_folder, exist_ok=True)
                        
                        block_path = os.path.join(content_folder, f"{block_name}.json")
                        with open(block_path, "w", encoding="utf-8") as f:
                            json.dump(block_data, f, indent=4, ensure_ascii=False)
                        
                        messagebox.showinfo(LangT("Успех"), f"{LangT("Жидкость")} '{liquid}' {LangT("добавлена в блок")} '{block_name}'!")
                        # Сразу открываем редактор требований после выбора
                        self.open_requirements_editor(block_name, block_data)
                    
                    except Exception as e:
                        messagebox.showerror(LangT("Ошибка"), f"{LangT("Не удалось сохранить жидкость:")} {str(e)}")
                
                def calculate_columns(container_width):
                    min_card_width = 180
                    spacing = 10
                    max_columns = max(1, container_width // (min_card_width + spacing))
                    if max_columns * (min_card_width + spacing) - spacing <= container_width:
                        return max_columns, min_card_width
                    return 1, -1
                
                def update_grid(canvas, items_frame, items):
                    container_width = canvas.winfo_width()
                    if container_width < 1:
                        return
                    
                    columns, card_width = calculate_columns(container_width)
                    
                    for widget in items_frame.grid_slaves():
                        widget.grid_forget()
                    
                    for i, item in enumerate(items):
                        row = i // columns
                        col = i % columns
                        is_mod_liquid = item in mod_liquids
                        card = create_liquid_card(items_frame, item, is_mod_liquid)
                        if card_width == -1:
                            card.configure(width=container_width - 20)
                        else:
                            card.configure(width=card_width)
                        card.grid(row=row, column=col, padx=5, pady=5, sticky="nsew")
                    
                    items_frame.update_idletasks()
                    canvas.configure(scrollregion=canvas.bbox("all"))
                    
                    if items_frame.winfo_height() <= canvas.winfo_height():
                        canvas.yview_moveto(0)
                        scrollbar.pack_forget()
                    else:
                        scrollbar.pack(side="right", fill="y")
                
                # Создаем один скроллируемый контейнер для всех жидкостей
                canvas = tk.Canvas(content_frame, bg="#3a3a3a", highlightthickness=0)
                scrollbar = ctk.CTkScrollbar(content_frame, orientation="vertical", command=canvas.yview)
                canvas.configure(yscrollcommand=scrollbar.set)
                
                scrollbar.pack(side="right", fill="y")
                canvas.pack(side="left", fill="both", expand=True, padx=10, pady=10)
                
                items_frame = ctk.CTkFrame(canvas, fg_color="#3a3a3a")
                canvas.create_window((0, 0), window=items_frame, anchor="nw")

                def on_mousewheel(event):
                    canvas.yview_scroll(int(-1*(event.delta/120)), "units")
                
                # Добавляем обработку прокрутки для Linux
                def on_button_4(event):
                    canvas.yview_scroll(-1, "units")
                
                def on_button_5(event):
                    canvas.yview_scroll(1, "units")
                
                # Привязываем события прокрутки
                canvas.bind("<MouseWheel>", on_mousewheel)
                canvas.bind("<Button-4>", on_button_4)
                canvas.bind("<Button-5>", on_button_5)
                
                # Объединяем все жидкости в один список
                all_liquids = default_liquids + mod_liquids
                
                # Сразу вызываем обновление сетки после создания
                canvas.after(100, lambda: update_grid(canvas, items_frame, all_liquids))
                
                canvas.bind("<Configure>", lambda e: update_grid(canvas, items_frame, all_liquids))
                items_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

    def open_mender_resource_editor(self, block_name, block_data):
        """
        Редактор для выбора предметов для блока
        """
        self.clear_window()
        self.root.configure(fg_color="#2b2b2b")
        
        main_frame = ctk.CTkFrame(self.root, fg_color="transparent")
        main_frame.pack(padx=10, pady=10, fill="both", expand=True)
        
        header_frame = ctk.CTkFrame(main_frame, height=90, fg_color="#3a3a3a", corner_radius=8)
        header_frame.pack(fill="x", pady=(0, 15))
        
        try:
            block_type = block_data.get("type")
            texture_path = os.path.join("mindustry_mod_creator", "mods", self.mod_name, "sprites", block_type, block_name, f"{block_name}.png")
            if os.path.exists(texture_path):
                img = Image.open(texture_path)
                img = img.resize((70, 70), Image.LANCZOS)
                ctk_img = ctk.CTkImage(light_image=img, size=(70, 70))
                img_label = ctk.CTkLabel(header_frame, image=ctk_img, text="")
                img_label.pack(side="left", padx=20)
        except Exception as e:
            print(f"Ошибка загрузки изображения: {e}")
        
        ctk.CTkLabel(header_frame, 
                    text=f"Выбор предметов для блока: {block_name}",
                    font=("Arial", 18, "bold")).pack(side="left", padx=10)
        
        content_frame = ctk.CTkFrame(main_frame, fg_color="#3a3a3a", corner_radius=8)
        content_frame.pack(fill="both", expand=True)
        
        def load_resource_icon(resource_name):
            icon_paths = [
                os.path.join(self.mod_folder, "sprites", "items", f"{resource_name}.png"),
                os.path.join("mindustry_mod_creator", "sprites", "items", f"{resource_name}.png"),
                os.path.join("mindustry_mod_creator", "icons", f"{resource_name}.png")
            ]
            for path in icon_paths:
                if os.path.exists(path):
                    try:
                        img = Image.open(path)
                        img = img.resize((50, 50), Image.LANCZOS)
                        return ctk.CTkImage(light_image=img, size=(50, 50))
                    except:
                        continue
            return None
        
        # Получаем списки ресурсов
        default_resources = [
            "copper", "lead", "metaglass", "graphite", "sand", 
            "coal", "titanium", "thorium", "scrap", "silicon",
            "plastanium", "phase-fabric", "surge-alloy", "spore-pod", 
            "blast-compound", "pyratite"
        ]
        
        mod_resources = []
        mod_resources_path = os.path.join(self.mod_folder, "content", "items")
        if os.path.exists(mod_resources_path):
            mod_resources = [f.replace(".json", "") for f in os.listdir(mod_resources_path) if f.endswith(".json")]

        # Переменные для выбора
        selected_resources = []  # Список для хранения выбранных ресурсов
        selected_count = tk.StringVar(value="0/5")  # Счетчик выбранных ресурсов
        resource_amount_vars = {}  # Словарь для хранения количества каждого ресурса
        checkbox_vars = {}  # Словарь для хранения переменных чекбоксов

        def create_resource_card(parent, resource, is_mod_resource=False):
            card_frame = ctk.CTkFrame(parent, 
                                    fg_color="#4a4a4a", 
                                    corner_radius=8,
                                    height=200)
            card_frame.pack_propagate(False)
            
            content_frame = ctk.CTkFrame(card_frame, fg_color="transparent")
            content_frame.pack(fill="both", expand=True, padx=10, pady=10)
            
            top_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
            top_frame.pack(fill="x", pady=(0, 10))
            
            icon = load_resource_icon(resource)
            if icon:
                ctk.CTkLabel(top_frame, image=icon, text="").pack()
            
            ctk.CTkLabel(top_frame, 
                        text=resource.capitalize(), 
                        font=("Arial", 14),
                        anchor="center").pack()
            
            bottom_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
            bottom_frame.pack(fill="x", pady=(10, 0))

            # Поле для ввода количества для предмета
            amount_frame = ctk.CTkFrame(bottom_frame, fg_color="transparent")
            amount_frame.pack(fill="x", pady=(0, 5))
            
            ctk.CTkLabel(amount_frame, text="Количество:", font=("Arial", 10)).pack(side="left")
            amount_var = tk.StringVar(value="1")
            resource_amount_vars[resource] = amount_var
            
            amount_entry = ctk.CTkEntry(amount_frame, 
                                    textvariable=amount_var,
                                    width=60,
                                    font=("Arial", 10))
            amount_entry.pack(side="right", padx=(5, 0))

            # Чекбокс выбора с ограничением
            checkbox_var = tk.BooleanVar(value=False)
            checkbox_vars[resource] = checkbox_var
            
            def on_checkbox_toggle():
                if checkbox_var.get():
                    if len(selected_resources) >= 5:
                        checkbox_var.set(False)
                        messagebox.showwarning("Лимит", "Можно выбрать не более 5 ресурсов!")
                        return
                    selected_resources.append(resource)
                else:
                    if resource in selected_resources:
                        selected_resources.remove(resource)
                
                # Обновляем счетчик
                selected_count.set(f"{len(selected_resources)}/5")
            
            checkbox = ctk.CTkCheckBox(
                bottom_frame,
                text="Выбрать",
                variable=checkbox_var,
                font=("Arial", 12),
                command=on_checkbox_toggle
            )
            checkbox.pack(pady=10)
            
            return card_frame
        
        def calculate_columns(container_width):
            min_card_width = 180
            spacing = 10
            max_columns = max(1, container_width // (min_card_width + spacing))
            if max_columns * (min_card_width + spacing) - spacing <= container_width:
                return max_columns, min_card_width
            return 1, -1
        
        # Словарь для хранения карточек ресурсов
        resource_cards = {}
        
        def update_grid(canvas, items_frame, items):
            container_width = canvas.winfo_width()
            if container_width < 1:
                return
            
            columns, card_width = calculate_columns(container_width)
            
            # Сохраняем состояние чекбоксов перед обновлением
            saved_states = {}
            for resource, checkbox_var in checkbox_vars.items():
                saved_states[resource] = checkbox_var.get()
            
            # Очищаем только grid, но не удаляем карточки
            for widget in items_frame.grid_slaves():
                widget.grid_forget()
            
            # Перераспределяем карточки по новой сетке
            for i, item in enumerate(items):
                row = i // columns
                col = i % columns
                
                # Если карточка еще не создана, создаем ее
                if item not in resource_cards:
                    resource_cards[item] = create_resource_card(items_frame, item, item in mod_resources)
                
                card = resource_cards[item]
                if card_width == -1:
                    card.configure(width=container_width - 20)
                else:
                    card.configure(width=card_width)
                card.grid(row=row, column=col, padx=5, pady=5, sticky="nsew")
                
                # Восстанавливаем состояние чекбокса
                if item in saved_states:
                    checkbox_vars[item].set(saved_states[item])
            
            items_frame.update_idletasks()
            canvas.configure(scrollregion=canvas.bbox("all"))
            
            if items_frame.winfo_height() <= canvas.winfo_height():
                canvas.yview_moveto(0)
                scrollbar.pack_forget()
            else:
                scrollbar.pack(side="right", fill="y")
        
        # Создаем скроллируемый контейнер
        canvas = tk.Canvas(content_frame, bg="#3a3a3a", highlightthickness=0)
        scrollbar = ctk.CTkScrollbar(content_frame, orientation="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)
        
        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True, padx=10, pady=10)
        
        items_frame = ctk.CTkFrame(canvas, fg_color="#3a3a3a")
        canvas.create_window((0, 0), window=items_frame, anchor="nw")

        def on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        def on_button_4(event):
            canvas.yview_scroll(-1, "units")
        
        def on_button_5(event):
            canvas.yview_scroll(1, "units")
        
        canvas.bind("<MouseWheel>", on_mousewheel)
        canvas.bind("<Button-4>", on_button_4)
        canvas.bind("<Button-5>", on_button_5)
        
        # Объединяем все ресурсы в один список
        all_resources = default_resources + mod_resources
        
        # Сразу вызываем обновление сетки после создания
        canvas.after(100, lambda: update_grid(canvas, items_frame, all_resources))
        
        canvas.bind("<Configure>", lambda e: update_grid(canvas, items_frame, all_resources))
        items_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        
        # Фрейм с настройками
        settings_frame = ctk.CTkFrame(main_frame, fg_color="#3a3a3a", corner_radius=8, height=80)
        settings_frame.pack(fill="x", pady=15)
        settings_frame.pack_propagate(False)
        
        settings_inner = ctk.CTkFrame(settings_frame, fg_color="transparent")
        settings_inner.pack(expand=True, padx=20, pady=15)
        
        # Счетчик выбранных ресурсов
        ctk.CTkLabel(settings_inner, 
                    textvariable=selected_count,
                    font=("Arial", 16, "bold"),
                    text_color="#ffffff").pack(side="left", padx=20)
        
        ctk.CTkLabel(settings_inner, 
                    text="Выбрано предметов (максимум 5)",
                    font=("Arial", 14),
                    text_color="#cccccc").pack(side="left", padx=10)
        
        # Фрейм с кнопками
        footer_frame = ctk.CTkFrame(main_frame, height=70, fg_color="#3a3a3a", corner_radius=8)
        footer_frame.pack(fill="x", pady=(0, 0))
        
        btn_frame = ctk.CTkFrame(footer_frame, fg_color="transparent")
        btn_frame.pack(expand=True, pady=15)

        def save_resource():
            if not selected_resources:
                messagebox.showerror("Ошибка", "Выберите хотя бы один предмет!")
                return
            
            # Создаем структуру consumes для нескольких ресурсов
            resources_config = []
            for resource in selected_resources:
                # Берем количество из поля ввода
                try:
                    amount = float(resource_amount_vars[resource].get())
                except ValueError:
                    amount = 1  # Значение по умолчанию при ошибке
                
                resource_config = {
                    "item": resource,
                    "amount": amount
                }
                resources_config.append(resource_config)
            
            # Сохраняем в блок
            if "consumes" not in block_data:
                block_data["consumes"] = {}
            
            # Сохраняем с автоматическими значениями booster=true и optional=true
            block_data["consumes"]["items"] = {
                "items": resources_config,
                "booster": True,
                "optional": True
            }
            
            try:
                block_type = block_data.get("type")
                content_folder = os.path.join("mindustry_mod_creator", "mods", self.mod_name, "content", "blocks", block_type)
                os.makedirs(content_folder, exist_ok=True)
                
                block_path = os.path.join(content_folder, f"{block_name}.json")
                with open(block_path, "w", encoding="utf-8") as f:
                    json.dump(block_data, f, indent=4, ensure_ascii=False)
                
                messagebox.showinfo("Успех", f"{len(selected_resources)} предметов добавлены в блок '{block_name}'!")
                
                # Переход к следующему редактору
                self.open_requirements_editor(block_name, block_data)
            
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось сохранить предметы: {str(e)}")
        
        def skip_resource():
            # Переход к следующему редактору
            self.open_requirements_editor(block_name, block_data)
        
        ctk.CTkButton(btn_frame, 
                    text="Сохранить", 
                    width=140, 
                    height=45,
                    font=("Arial", 14),
                    command=save_resource).pack(side="left", padx=20)
        