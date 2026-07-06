#!/usr/bin/env python3
"""
Mindustry Java Mod Creator - Запуск приложения
"""

import sys
import os
import traceback
from pathlib import Path
import customtkinter as ctk

def main():
    # Устанавливаем путь к проекту
    project_root = Path(__file__).parent.absolute()
    
    # Добавляем в PYTHONPATH если нужно
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    
    # Настройка темы ДО создания окна
    ctk.set_appearance_mode("Dark")
    ctk.set_default_color_theme("blue")
    
    try:
        # Ленивый импорт (после настройки путей)
        from Creator.ui.main_window import MainWindow
        
        app = MainWindow()
        app.run()
        
    except KeyboardInterrupt:
        print("\nПрограмма прервана пользователем")
        sys.exit(0)
    except Exception as e:
        print(f"КРИТИЧЕСКАЯ ОШИБКА: {e}")
        traceback.print_exc()
        input("Нажмите Enter для выхода...")
        sys.exit(1)

if __name__ == "__main__":
    main()