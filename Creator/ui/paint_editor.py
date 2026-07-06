#p/Creator/ui/paint_editor.py
import customtkinter as ctk
import tkinter as tk
from tkinter import colorchooser, messagebox, filedialog
from PIL import Image
import os
import gc
from datetime import datetime
import copy

class PixelPaint:
    def __init__(self):
        # Настройки редактора
        self.current_color = "#000000"
        self.grid_size = 32
        self.cell_size = 20
        self.base_cell_size = 20
        self.min_cell_size = 8
        self.max_cell_size = 60
        self.canvas_width = 600
        self.canvas_height = 500
        
        # Параметры прокрутки
        self.offset_x = 0
        self.offset_y = 0
        self.max_offset_x = 300
        self.max_offset_y = 300
        
        # Перемещение зажатым колесиком
        self.is_panning = False
        self.pan_start_x = 0
        self.pan_start_y = 0
        self.pan_start_offset_x = 0
        self.pan_start_offset_y = 0
        
        self.current_tool = "pencil"
        self.history = []
        self.history_index = -1
        self.is_drawing = False
        
        # Цвета
        self.bg_color = "#FFFFFF"
        self.edge_color = "#666666"
        
        # Последний путь сохранения
        self.last_save_path = None
        
        # Хранилище пикселей
        self.pixel_data = {}  # Словарь для хранения всех пикселей {(x, y): color}
        
        self.setup_editor()
    
    def setup_editor(self):
        """Настройка редактора пиксельной графики"""
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        self.paint_window = ctk.CTk()
        self.paint_window.title("Pixel Paint - 32x32 Editor")
        self.paint_window.geometry("1000x700")
        self.paint_window.resizable(False, False)
        self.paint_window.configure(fg_color="#333333")
        self.paint_window.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Главный контейнер - горизонтальный
        main_frame = ctk.CTkFrame(self.paint_window, fg_color="#333333")
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # ============ ЛЕВАЯ ПАНЕЛЬ ============
        left_panel = ctk.CTkFrame(main_frame, fg_color="#404040", width=220)
        left_panel.pack(side="left", fill="y", padx=(0, 10))
        left_panel.pack_propagate(False)
        
        # Заголовок
        title = ctk.CTkLabel(left_panel, text="🎨 PIXEL PAINT", 
                           font=("Arial", 16, "bold"),
                           text_color="#FFFFFF")
        title.pack(pady=(10, 0))
        
        subtitle = ctk.CTkLabel(left_panel, text="32x32 Editor | v1.0",
                              font=("Arial", 9),
                              text_color="#AAAAAA")
        subtitle.pack(pady=(0, 10))
        
        # ======== ИНСТРУМЕНТЫ ========
        tools_frame = ctk.CTkFrame(left_panel, fg_color="#404040")
        tools_frame.pack(pady=5, padx=10, fill="x")
        
        tools_label = ctk.CTkLabel(tools_frame, text="🛠️ ИНСТРУМЕНТЫ",
                                  font=("Arial", 11, "bold"),
                                  text_color="#CCCCCC")
        tools_label.pack(anchor="w", pady=(0, 5))
        
        # Сетка для инструментов
        tools_grid = ctk.CTkFrame(tools_frame, fg_color="#404040")
        tools_grid.pack(fill="x")
        
        # Первый ряд инструментов
        tools_row1 = ctk.CTkFrame(tools_grid, fg_color="#404040")
        tools_row1.pack(fill="x", pady=2)
        
        self.pencil_button = ctk.CTkButton(
            tools_row1, 
            text="✏️",
            width=45,
            command=lambda: self.set_tool("pencil"),
            fg_color="#1f6aa5",
            hover_color="#1a5a8c",
            font=("Arial", 14)
        )
        self.pencil_button.pack(side="left", padx=2)
        
        self.eraser_button = ctk.CTkButton(
            tools_row1,
            text="🧽",
            width=45,
            command=lambda: self.set_tool("eraser"),
            fg_color="#555555",
            hover_color="#444444",
            font=("Arial", 14)
        )
        self.eraser_button.pack(side="left", padx=2)
        
        self.fill_button = ctk.CTkButton(
            tools_row1,
            text="🪣",
            width=45,
            command=lambda: self.set_tool("fill"),
            fg_color="#555555",
            hover_color="#444444",
            font=("Arial", 14)
        )
        self.fill_button.pack(side="left", padx=2)
        
        # Второй ряд инструментов
        tools_row2 = ctk.CTkFrame(tools_grid, fg_color="#404040")
        tools_row2.pack(fill="x", pady=2)
        
        # Цвет и палитра
        self.color_preview = ctk.CTkFrame(tools_row2, 
                                         fg_color=self.current_color,
                                         width=45, 
                                         height=35,
                                         corner_radius=5)
        self.color_preview.pack(side="left", padx=2)
        
        self.color_button = ctk.CTkButton(
            tools_row2, 
            text="🎨",
            width=45,
            command=self.change_color,
            fg_color="#555555",
            hover_color="#444444",
            font=("Arial", 14)
        )
        self.color_button.pack(side="left", padx=2)
        
        clear_btn = ctk.CTkButton(
            tools_row2,
            text="🗑️",
            width=45,
            command=self.clear_canvas,
            fg_color="#d32f2f",
            hover_color="#b71c1c",
            font=("Arial", 14)
        )
        clear_btn.pack(side="left", padx=2)
        
        # ======== ИСТОРИЯ ========
        history_frame = ctk.CTkFrame(left_panel, fg_color="#404040")
        history_frame.pack(pady=10, padx=10, fill="x")
        
        history_label = ctk.CTkLabel(history_frame, text="📋 ИСТОРИЯ",
                                    font=("Arial", 11, "bold"),
                                    text_color="#CCCCCC")
        history_label.pack(anchor="w", pady=(0, 5))
        
        history_buttons = ctk.CTkFrame(history_frame, fg_color="#404040")
        history_buttons.pack(fill="x")
        
        undo_btn = ctk.CTkButton(
            history_buttons,
            text="↩ Отмена",
            command=self.undo,
            fg_color="#555555",
            hover_color="#444444",
            height=32,
            font=("Arial", 11)
        )
        undo_btn.pack(side="left", padx=2, fill="x", expand=True)
        
        redo_btn = ctk.CTkButton(
            history_buttons,
            text="↪ Повтор",
            command=self.redo,
            fg_color="#555555",
            hover_color="#444444",
            height=32,
            font=("Arial", 11)
        )
        redo_btn.pack(side="right", padx=2, fill="x", expand=True)
        
        # ======== МАСШТАБ ========
        zoom_frame = ctk.CTkFrame(left_panel, fg_color="#404040")
        zoom_frame.pack(pady=10, padx=10, fill="x")
        
        zoom_label = ctk.CTkLabel(zoom_frame, text="🔍 МАСШТАБ",
                                 font=("Arial", 11, "bold"),
                                 text_color="#CCCCCC")
        zoom_label.pack(anchor="w", pady=(0, 5))
        
        # Слайдер и значение
        zoom_control = ctk.CTkFrame(zoom_frame, fg_color="#404040")
        zoom_control.pack(fill="x")
        
        self.zoom_slider = ctk.CTkSlider(
            zoom_control,
            from_=40, to=300,
            command=self.zoom_changed,
            width=120,
            fg_color="#555555",
            progress_color="#1f6aa5"
        )
        self.zoom_slider.set(100)
        self.zoom_slider.pack(side="left", padx=(0, 5))
        
        self.zoom_value = ctk.CTkLabel(zoom_control, text="100%",
                                      font=("Arial", 12, "bold"),
                                      text_color="#FFFFFF",
                                      width=50)
        self.zoom_value.pack(side="left")
        
        # Кнопки масштаба
        zoom_buttons = ctk.CTkFrame(zoom_frame, fg_color="#404040")
        zoom_buttons.pack(fill="x", pady=(5, 0))
        
        zoom_in_btn = ctk.CTkButton(
            zoom_buttons,
            text="➕",
            width=40,
            command=self.zoom_in,
            fg_color="#555555",
            hover_color="#444444",
            font=("Arial", 14)
        )
        zoom_in_btn.pack(side="left", padx=2)
        
        zoom_out_btn = ctk.CTkButton(
            zoom_buttons,
            text="➖",
            width=40,
            command=self.zoom_out,
            fg_color="#555555",
            hover_color="#444444",
            font=("Arial", 14)
        )
        zoom_out_btn.pack(side="left", padx=2)
        
        reset_btn = ctk.CTkButton(
            zoom_buttons,
            text="↺ Сброс",
            width=70,
            command=self.reset_position,
            fg_color="#555555",
            hover_color="#444444",
            height=32,
            font=("Arial", 11)
        )
        reset_btn.pack(side="right", padx=2)
        
        # ======== НАВИГАЦИЯ ========
        nav_frame = ctk.CTkFrame(left_panel, fg_color="#404040")
        nav_frame.pack(pady=10, padx=10, fill="x")
        
        nav_label = ctk.CTkLabel(nav_frame, text="🧭 НАВИГАЦИЯ",
                                font=("Arial", 11, "bold"),
                                text_color="#CCCCCC")
        nav_label.pack(anchor="w", pady=(0, 5))
        
        nav_info = ctk.CTkLabel(nav_frame, 
                               text="• Колесико: ↑↓\n"
                                    "• Shift+Колесико: ←→\n"
                                    "• Зажать колесико: Свободно\n"
                                    "• Ctrl+Колесико: Масштаб",
                               font=("Arial", 10),
                               text_color="#AAAAAA",
                               justify="left")
        nav_info.pack(pady=5, anchor="w")
        
        # ======== ФАЙЛ ========
        file_frame = ctk.CTkFrame(left_panel, fg_color="#404040")
        file_frame.pack(pady=10, padx=10, fill="x")
        
        file_label = ctk.CTkLabel(file_frame, text="💾 ФАЙЛ",
                                 font=("Arial", 11, "bold"),
                                 text_color="#CCCCCC")
        file_label.pack(anchor="w", pady=(0, 5))
        
        # Кнопки файлов
        save_btn = ctk.CTkButton(
            file_frame,
            text="💾 Сохранить",
            command=self.save_image,
            fg_color="#2e7d32",
            hover_color="#1e5622",
            height=35,
            font=("Arial", 11, "bold")
        )
        save_btn.pack(pady=2, fill="x")
        
        save_as_btn = ctk.CTkButton(
            file_frame,
            text="💾 Сохранить как...",
            command=self.save_image_as,
            fg_color="#555555",
            hover_color="#444444",
            height=32,
            font=("Arial", 11)
        )
        save_as_btn.pack(pady=2, fill="x")
        
        load_btn = ctk.CTkButton(
            file_frame,
            text="📂 Загрузить",
            command=self.load_image,
            fg_color="#555555",
            hover_color="#444444",
            height=32,
            font=("Arial", 11)
        )
        load_btn.pack(pady=2, fill="x")
        
        # ======== БЫСТРЫЕ ЦВЕТА ========
        colors_frame = ctk.CTkFrame(left_panel, fg_color="#404040")
        colors_frame.pack(pady=10, padx=10, fill="x")
        
        colors_label = ctk.CTkLabel(colors_frame, text="🎨 БЫСТРЫЕ ЦВЕТА",
                                   font=("Arial", 11, "bold"),
                                   text_color="#CCCCCC")
        colors_label.pack(anchor="w", pady=(0, 5))
        
        # Палитра цветов
        palette = ctk.CTkFrame(colors_frame, fg_color="#404040")
        palette.pack(fill="x")
        
        quick_colors = [
            "#000000", "#FFFFFF", "#FF0000", "#00FF00", "#0000FF",
            "#FFFF00", "#FF00FF", "#00FFFF", "#FF8800", "#8800FF"
        ]
        
        # Создаем сетку 2x5
        for i in range(0, len(quick_colors), 5):
            row = ctk.CTkFrame(palette, fg_color="#404040")
            row.pack(fill="x", pady=2)
            for j in range(5):
                if i + j < len(quick_colors):
                    color = quick_colors[i + j]
                    color_btn = ctk.CTkButton(
                        row,
                        text="",
                        width=30,
                        height=25,
                        fg_color=color,
                        hover_color=color,
                        command=lambda c=color: self.set_quick_color(c)
                    )
                    color_btn.pack(side="left", padx=2)
        
        # ======== СТАТУС ========
        status_frame = ctk.CTkFrame(left_panel, fg_color="#404040")
        status_frame.pack(pady=10, padx=10, fill="x", side="bottom")
        
        self.status_label = ctk.CTkLabel(
            status_frame,
            text="✅ Готов к работе",
            font=("Arial", 10),
            text_color="#AAAAAA"
        )
        self.status_label.pack(pady=5)
        
        # ============ ПРАВАЯ ПАНЕЛЬ (ХОЛСТ) ============
        canvas_frame = ctk.CTkFrame(main_frame, fg_color="#333333")
        canvas_frame.pack(side="right", fill="both", expand=True)
        
        # Холст
        self.canvas = tk.Canvas(
            canvas_frame,
            width=self.canvas_width,
            height=self.canvas_height,
            bg=self.edge_color,
            highlightthickness=2,
            highlightbackground="#555555",
            cursor="crosshair",
            confine=True
        )
        self.canvas.pack(padx=10, pady=10)
        
        # Информационная строка под холстом
        info_bar = ctk.CTkFrame(canvas_frame, fg_color="#404040", height=30)
        info_bar.pack(fill="x", padx=10, pady=(0, 10))
        
        self.info_label = ctk.CTkLabel(
            info_bar,
            text="✏️ Карандаш | 🎨 #000000 | 📐 32x32 | 🔍 100%",
            font=("Arial", 11),
            text_color="#CCCCCC"
        )
        self.info_label.pack(side="left", padx=10)
        
        # Привязка событий
        self.canvas.bind("<B1-Motion>", self.draw_pixel)
        self.canvas.bind("<Button-1>", self.handle_click)
        self.canvas.bind("<ButtonRelease-1>", self.stop_drawing)
        
        # Перемещение зажатым колесиком
        self.canvas.bind("<Button-2>", self.start_pan)
        self.canvas.bind("<B2-Motion>", self.pan)
        self.canvas.bind("<ButtonRelease-2>", self.stop_pan)
        self.canvas.bind("<Button-3>", self.start_pan)
        self.canvas.bind("<B3-Motion>", self.pan)
        self.canvas.bind("<ButtonRelease-3>", self.stop_pan)
        
        self.canvas.bind("<MouseWheel>", self.on_mousewheel)
        self.canvas.bind("<Shift-MouseWheel>", self.on_shift_mousewheel)
        self.canvas.bind("<Control-MouseWheel>", self.on_zoom)

        self.draw_full_canvas()
        self.save_state()
        self.update_info()
    
    # ============ ИСПРАВЛЕННЫЕ ФУНКЦИИ ============
    
    def draw_grid(self):
        """Отрисовка сетки - ИСПРАВЛЕНО И ДОБАВЛЕНО"""
        if self.cell_size >= 8:
            # Вычисляем видимую область сетки
            start_col = max(0, -self.offset_x // self.cell_size)
            start_row = max(0, -self.offset_y // self.cell_size)
            end_col = min(self.grid_size, 
                        (self.canvas_width - self.offset_x) // self.cell_size + 1)
            end_row = min(self.grid_size, 
                        (self.canvas_height - self.offset_y) // self.cell_size + 1)
            
            # Вертикальные линии
            for i in range(start_col, end_col + 1):
                x = self.offset_x + i * self.cell_size
                if 0 <= x <= self.canvas_width:
                    y_start = max(0, self.offset_y + start_row * self.cell_size)
                    y_end = min(self.canvas_height, 
                              self.offset_y + end_row * self.cell_size)
                    self.canvas.create_line(
                        x, y_start, x, y_end,
                        fill="#CCCCCC", width=1, tags="grid"
                    )
            
            # Горизонтальные линии
            for i in range(start_row, end_row + 1):
                y = self.offset_y + i * self.cell_size
                if 0 <= y <= self.canvas_height:
                    x_start = max(0, self.offset_x + start_col * self.cell_size)
                    x_end = min(self.canvas_width, 
                              self.offset_x + end_col * self.cell_size)
                    self.canvas.create_line(
                        x_start, y, x_end, y,
                        fill="#CCCCCC", width=1, tags="grid"
                    )
    
    def draw_full_canvas(self):
        """Полная перерисовка холста с сохранением пикселей"""
        self.canvas.delete("all")
        
        # Рисуем серую область вокруг
        self.canvas.create_rectangle(
            0, 0, 
            self.canvas_width, self.canvas_height,
            fill=self.edge_color,
            outline=self.edge_color,
            tags="edge"
        )
        
        # Рисуем белое поле для рисования
        white_x1 = self.offset_x
        white_y1 = self.offset_y
        white_x2 = min(self.offset_x + self.grid_size * self.cell_size, self.canvas_width)
        white_y2 = min(self.offset_y + self.grid_size * self.cell_size, self.canvas_height)
        
        if white_x2 > 0 and white_y2 > 0 and white_x1 < self.canvas_width and white_y1 < self.canvas_height:
            white_x1 = max(0, white_x1)
            white_y1 = max(0, white_y1)
            white_x2 = max(white_x1, min(white_x2, self.canvas_width))
            white_y2 = max(white_y1, min(white_y2, self.canvas_height))
            
            if white_x2 > white_x1 and white_y2 > white_y1:
                self.canvas.create_rectangle(
                    white_x1, white_y1, white_x2, white_y2,
                    fill=self.bg_color,
                    outline=self.bg_color,
                    tags="white_area"
                )
        
        self.draw_grid()  # Теперь эта функция существует
        self.draw_all_pixels_from_data()
    
    def draw_all_pixels_from_data(self):
        """Отрисовка всех пикселей из хранилища данных"""
        for (x, y), color in self.pixel_data.items():
            self.draw_pixel_at_position(x, y, color)
    
    def draw_pixel_at_position(self, x, y, color):
        """Рисование пикселя в определенной позиции с проверкой видимости"""
        x1 = self.offset_x + x * self.cell_size
        y1 = self.offset_y + y * self.cell_size
        x2 = x1 + self.cell_size
        y2 = y1 + self.cell_size
        
        # Проверяем видимость и обрезаем
        if x1 < self.canvas_width and y1 < self.canvas_height and x2 > 0 and y2 > 0:
            x1 = max(0, x1)
            y1 = max(0, y1)
            x2 = min(self.canvas_width, x2)
            y2 = min(self.canvas_height, y2)
            
            if x2 > x1 and y2 > y1:
                self.canvas.create_rectangle(
                    x1, y1, x2, y2,
                    fill=color,
                    outline="#CCCCCC" if self.cell_size >= 10 else color,
                    width=1 if self.cell_size >= 10 else 0,
                    tags=f"pixel_{x}_{y}"
                )
    
    # --- ФУНКЦИИ РИСОВАНИЯ ---
    
    def start_drawing(self, event):
        """Начало рисования"""
        self.is_drawing = True
        self.draw_pixel(event)
    
    def draw_pixel(self, event):
        """Рисование пикселя с сохранением в хранилище"""
        if not self.is_drawing:
            return
        
        canvas_x = self.canvas.canvasx(event.x)
        canvas_y = self.canvas.canvasy(event.y)
        
        # Проверяем, находимся ли внутри белого поля
        if canvas_x < self.offset_x or canvas_x >= self.offset_x + self.grid_size * self.cell_size or \
           canvas_y < self.offset_y or canvas_y >= self.offset_y + self.grid_size * self.cell_size:
            return
        
        x = int((canvas_x - self.offset_x) // self.cell_size)
        y = int((canvas_y - self.offset_y) // self.cell_size)
        
        if 0 <= x < self.grid_size and 0 <= y < self.grid_size:
            if self.current_tool == "eraser":
                # Удаляем пиксель из хранилища
                if (x, y) in self.pixel_data:
                    del self.pixel_data[(x, y)]
                self.canvas.delete(f"pixel_{x}_{y}")
            elif self.current_tool in ["pencil", "fill"]:
                # Добавляем пиксель в хранилище
                self.pixel_data[(x, y)] = self.current_color
                self.canvas.delete(f"pixel_{x}_{y}")
                self.draw_pixel_at_position(x, y, self.current_color)
    
    def stop_drawing(self, event):
        """Остановка рисования"""
        if self.is_drawing:
            self.is_drawing = False
            self.save_state()
    
    def flood_fill(self, x, y, target_color, replacement_color):
        """Заливка области с сохранением в хранилище"""
        if target_color == replacement_color:
            return
        
        stack = [(x, y)]
        visited = set()
        
        while stack:
            cx, cy = stack.pop()
            if (cx, cy) in visited:
                continue
            visited.add((cx, cy))
            
            if cx < 0 or cx >= self.grid_size or cy < 0 or cy >= self.grid_size:
                continue
            
            # Получаем текущий цвет пикселя
            current_pixel_color = self.pixel_data.get((cx, cy), self.bg_color)
            
            if current_pixel_color != target_color:
                continue
            
            # Обновляем хранилище
            if replacement_color == self.bg_color:
                if (cx, cy) in self.pixel_data:
                    del self.pixel_data[(cx, cy)]
            else:
                self.pixel_data[(cx, cy)] = replacement_color
            
            # Обновляем отображение
            self.canvas.delete(f"pixel_{cx}_{cy}")
            if replacement_color != self.bg_color:
                self.draw_pixel_at_position(cx, cy, replacement_color)
            
            stack.append((cx+1, cy))
            stack.append((cx-1, cy))
            stack.append((cx, cy+1))
            stack.append((cx, cy-1))
    
    def handle_click(self, event):
        """Обработчик клика"""
        canvas_x = self.canvas.canvasx(event.x)
        canvas_y = self.canvas.canvasy(event.y)
        
        # Проверяем, находимся ли внутри белого поля
        if canvas_x < self.offset_x or canvas_x >= self.offset_x + self.grid_size * self.cell_size or \
           canvas_y < self.offset_y or canvas_y >= self.offset_y + self.grid_size * self.cell_size:
            return
        
        x = int((canvas_x - self.offset_x) // self.cell_size)
        y = int((canvas_y - self.offset_y) // self.cell_size)
        
        if 0 <= x < self.grid_size and 0 <= y < self.grid_size:
            if self.current_tool == "fill":
                self.save_state()
                target_color = self.pixel_data.get((x, y), self.bg_color)
                self.flood_fill(x, y, target_color, self.current_color)
                self.save_state()
            else:
                self.start_drawing(event)
    
    # --- ФУНКЦИИ ИСТОРИИ ---
    
    def save_state(self):
        """Сохранение состояния в историю (копия pixel_data)"""
        if self.history_index < len(self.history) - 1:
            self.history = self.history[:self.history_index + 1]
        
        # Создаем глубокую копию словаря пикселей
        state = copy.deepcopy(self.pixel_data)
        self.history.append(state)
        
        # Ограничиваем историю 50 состояниями
        if len(self.history) > 50:
            self.history = self.history[-50:]
            self.history_index = len(self.history) - 1
        else:
            self.history_index = len(self.history) - 1
    
    def undo(self):
        """Отмена действия"""
        if self.history_index > 0:
            self.history_index -= 1
            self.restore_state()
            self.status_label.configure(text="↩ Отмена действия")
    
    def redo(self):
        """Повтор действия"""
        if self.history_index < len(self.history) - 1:
            self.history_index += 1
            self.restore_state()
            self.status_label.configure(text="↪ Повтор действия")
    
    def restore_state(self):
        """Восстановление состояния из истории"""
        self.pixel_data = copy.deepcopy(self.history[self.history_index])
        self.draw_full_canvas()
    
    # --- ФУНКЦИИ ОЧИСТКИ ---
    
    def clear_pixels_only(self):
        """Очистка всех пикселей"""
        self.pixel_data.clear()
        self.draw_full_canvas()
    
    def clear_canvas(self):
        """Очистка холста"""
        if messagebox.askyesno("Очистка", "Очистить весь холст?", icon="warning"):
            self.clear_pixels_only()
            self.save_state()
            self.status_label.configure(text="🗑️ Холст очищен")
            messagebox.showinfo("Очистка", "Холст очищен!")
    
    # --- ФУНКЦИИ ПЕРЕМЕЩЕНИЯ ---
    
    def on_mousewheel(self, event):
        """Вертикальное перемещение колесиком"""
        delta = -1 if event.delta > 0 else 1
        new_offset_y = self.offset_y + delta * self.cell_size // 2
        
        max_y = self.max_offset_y
        min_y = -self.max_offset_y
        new_offset_y = max(min_y, min(new_offset_y, max_y))
        
        if new_offset_y != self.offset_y:
            self.offset_y = new_offset_y
            self.draw_full_canvas()
    
    def on_shift_mousewheel(self, event):
        """Горизонтальное перемещение Shift+колесико"""
        delta = -1 if event.delta > 0 else 1
        new_offset_x = self.offset_x + delta * self.cell_size // 2
        
        max_x = self.max_offset_x
        min_x = -self.max_offset_x
        new_offset_x = max(min_x, min(new_offset_x, max_x))
        
        if new_offset_x != self.offset_x:
            self.offset_x = new_offset_x
            self.draw_full_canvas()
    
    def start_pan(self, event):
        """Начало перемещения зажатым колесиком"""
        self.is_panning = True
        self.pan_start_x = event.x
        self.pan_start_y = event.y
        self.pan_start_offset_x = self.offset_x
        self.pan_start_offset_y = self.offset_y
        self.canvas.config(cursor="fleur")
        self.status_label.configure(text="🖐️ Перемещение...")
    
    def pan(self, event):
        """Перемещение зажатым колесиком"""
        if self.is_panning:
            dx = event.x - self.pan_start_x
            dy = event.y - self.pan_start_y
            
            new_offset_x = self.pan_start_offset_x + dx
            new_offset_y = self.pan_start_offset_y + dy
            
            new_offset_x = max(-self.max_offset_x, min(new_offset_x, self.max_offset_x))
            new_offset_y = max(-self.max_offset_y, min(new_offset_y, self.max_offset_y))
            
            self.offset_x = new_offset_x
            self.offset_y = new_offset_y
            self.draw_full_canvas()
    
    def stop_pan(self, event):
        """Остановка перемещения зажатым колесиком"""
        self.is_panning = False
        self.canvas.config(cursor="crosshair")
        self.status_label.configure(text="✅ Готов к работе")
    
    def reset_position(self):
        """Сброс позиции в центр"""
        self.offset_x = 0
        self.offset_y = 0
        self.draw_full_canvas()
        self.status_label.configure(text="📍 Позиция сброшена")
    
    # --- ФУНКЦИИ МАСШТАБИРОВАНИЯ ---
    
    def zoom_in(self):
        """Приблизить"""
        new_size = min(self.cell_size + 2, self.max_cell_size)
        if new_size != self.cell_size:
            self.cell_size = new_size
            zoom_percent = int((self.cell_size / self.base_cell_size) * 100)
            self.zoom_slider.set(zoom_percent)
            self.zoom_value.configure(text=f"{zoom_percent}%")
            self.draw_full_canvas()
            self.update_info()
    
    def zoom_out(self):
        """Отдалить"""
        new_size = max(self.cell_size - 2, self.min_cell_size)
        if new_size != self.cell_size:
            self.cell_size = new_size
            zoom_percent = int((self.cell_size / self.base_cell_size) * 100)
            self.zoom_slider.set(zoom_percent)
            self.zoom_value.configure(text=f"{zoom_percent}%")
            self.draw_full_canvas()
            self.update_info()
    
    def on_zoom(self, event):
        """Масштабирование Ctrl+колесико"""
        if event.delta > 0:
            new_size = min(self.cell_size + 2, self.max_cell_size)
        else:
            new_size = max(self.cell_size - 2, self.min_cell_size)
        
        if new_size != self.cell_size:
            # Сохраняем позицию центра
            center_x = self.canvas_width // 2
            center_y = self.canvas_height // 2
            
            # Вычисляем какой пиксель в центре
            center_pixel_x = (center_x - self.offset_x) / self.cell_size
            center_pixel_y = (center_y - self.offset_y) / self.cell_size
            
            self.cell_size = new_size
            
            # Корректируем смещение, чтобы центр оставался на месте
            self.offset_x = center_x - int(center_pixel_x * self.cell_size)
            self.offset_y = center_y - int(center_pixel_y * self.cell_size)
            
            # Ограничиваем смещение
            self.offset_x = max(-self.max_offset_x, min(self.offset_x, self.max_offset_x))
            self.offset_y = max(-self.max_offset_y, min(self.offset_y, self.max_offset_y))
            
            zoom_percent = int((self.cell_size / self.base_cell_size) * 100)
            self.zoom_slider.set(zoom_percent)
            self.zoom_value.configure(text=f"{zoom_percent}%")
            self.draw_full_canvas()
            self.update_info()
    
    def zoom_changed(self, value):
        """Изменение масштаба через слайдер"""
        zoom_percent = int(float(value))
        new_size = int((zoom_percent / 100) * self.base_cell_size)
        new_size = max(self.min_cell_size, min(new_size, self.max_cell_size))
        
        if new_size != self.cell_size:
            self.cell_size = new_size
            self.zoom_value.configure(text=f"{zoom_percent}%")
            self.draw_full_canvas()
            self.update_info()
    
    # --- ФУНКЦИИ ЦВЕТА И ИНСТРУМЕНТОВ ---
    
    def set_quick_color(self, color):
        """Быстрый выбор цвета"""
        self.current_color = color
        self.color_preview.configure(fg_color=color)
        self.set_tool("pencil")
        self.update_info()
    
    def change_color(self):
        """Смена цвета"""
        color = colorchooser.askcolor(title="Выберите цвет", initialcolor=self.current_color)
        if color[1]:
            self.current_color = color[1]
            self.color_preview.configure(fg_color=self.current_color)
            self.set_tool("pencil")
            self.update_info()
    
    def set_tool(self, tool):
        """Установка инструмента"""
        self.current_tool = tool
        
        self.pencil_button.configure(fg_color="#555555")
        self.eraser_button.configure(fg_color="#555555")
        self.fill_button.configure(fg_color="#555555")
        
        if tool == "pencil":
            self.pencil_button.configure(fg_color="#1f6aa5")
            self.status_label.configure(text="✏️ Выбран карандаш")
        elif tool == "eraser":
            self.eraser_button.configure(fg_color="#1f6aa5")
            self.status_label.configure(text="🧽 Выбран ластик")
        elif tool == "fill":
            self.fill_button.configure(fg_color="#1f6aa5")
            self.status_label.configure(text="🪣 Выбрана заливка")
        
        self.update_info()
    
    def update_info(self):
        """Обновление информационной строки"""
        tool_names = {
            "pencil": "✏️ Карандаш",
            "eraser": "🧽 Ластик", 
            "fill": "🪣 Заливка"
        }
        tool_name = tool_names.get(self.current_tool, "✏️ Карандаш")
        zoom_percent = int((self.cell_size / self.base_cell_size) * 100)
        
        self.info_label.configure(
            text=f"{tool_name} | 🎨 {self.current_color} | 📐 32x32 | 🔍 {zoom_percent}% | 🖼️ {len(self.pixel_data)} пикселей"
        )
    
    # --- ФУНКЦИИ СОХРАНЕНИЯ И ЗАГРУЗКИ ---
    
    def save_image(self):
        """Быстрое сохранение изображения"""
        if self.last_save_path and os.path.exists(os.path.dirname(self.last_save_path)):
            self.save_to_path(self.last_save_path)
        else:
            self.save_image_as()
    
    def save_image_as(self):
        """Сохранить изображение как..."""
        save_dir = "pixel_paint_saves"
        os.makedirs(save_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_filename = f"pixel_art_{timestamp}.png"
        default_path = os.path.join(save_dir, default_filename)
        
        file_path = filedialog.asksaveasfilename(
            title="Сохранить изображение",
            initialdir=save_dir,
            initialfile=default_filename,
            defaultextension=".png",
            filetypes=[("PNG files", "*.png"), ("All files", "*.*")]
        )
        
        if file_path:
            self.save_to_path(file_path)
    
    def save_to_path(self, file_path):
        """Сохранение изображения по указанному пути"""
        try:
            img = Image.new("RGBA", (self.grid_size, self.grid_size), (255, 255, 255, 0))
            pixels = img.load()
            
            # Сохраняем из хранилища данных
            for (x, y), color in self.pixel_data.items():
                try:
                    r, g, b = tuple(int(color.lstrip('#')[i:i+2], 16) for i in (0, 2, 4))
                    pixels[x, y] = (r, g, b, 255)
                except:
                    pixels[x, y] = (0, 0, 0, 255)
            
            img.save(file_path)
            self.last_save_path = file_path
            self.status_label.configure(text=f"💾 Сохранено: {os.path.basename(file_path)}")
            
            messagebox.showinfo(
                "Сохранено", 
                f"✅ Изображение сохранено!\n📁 {os.path.basename(file_path)}\n🎨 Пикселей: {len(self.pixel_data)}"
            )
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"❌ Не удалось сохранить изображение:\n{e}")
    
    def load_image(self):
        """Загрузка изображения"""
        file_path = filedialog.askopenfilename(
            title="Загрузить изображение",
            initialdir="pixel_paint_saves",
            filetypes=[("PNG files", "*.png"), ("All files", "*.*")]
        )
        
        if file_path:
            try:
                img = Image.open(file_path)
                
                if img.size != (self.grid_size, self.grid_size):
                    img = img.resize((self.grid_size, self.grid_size), Image.NEAREST)
                
                if img.mode != "RGBA":
                    img = img.convert("RGBA")
                
                # Очищаем текущие данные
                self.pixel_data.clear()
                
                # Загружаем пиксели
                pixels = img.load()
                
                for x in range(self.grid_size):
                    for y in range(self.grid_size):
                        r, g, b, a = pixels[x, y]
                        if a > 0:
                            color = f"#{r:02x}{g:02x}{b:02x}"
                            self.pixel_data[(x, y)] = color
                
                self.draw_full_canvas()
                self.save_state()
                self.status_label.configure(text=f"📂 Загружено: {os.path.basename(file_path)}")
                self.update_info()
                
                messagebox.showinfo(
                    "Загружено", 
                    f"✅ Изображение загружено!\n📁 {os.path.basename(file_path)}\n🎨 Пикселей: {len(self.pixel_data)}"
                )
                
            except Exception as e:
                messagebox.showerror("Ошибка", f"❌ Не удалось загрузить изображение:\n{e}")
    
    def on_closing(self):
        """Очистка ресурсов при закрытии окна"""
        if messagebox.askokcancel("Выход", "Сохранить изменения перед выходом?"):
            self.save_image()
        self.paint_window.quit()
        self.paint_window.destroy()
        gc.collect()
    
    def run(self):
        """Запуск приложения"""
        self.paint_window.mainloop()

if __name__ == "__main__":
    app = PixelPaint()
    app.run()