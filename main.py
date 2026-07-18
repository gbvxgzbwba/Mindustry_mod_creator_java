#!/usr/bin/env python3
"""
Mindustry Java Mod Creator - Запуск приложения с автообновлением
"""

import sys
import os
import traceback
import threading
from pathlib import Path
import customtkinter as ctk

# Устанавливаем путь к проекту
project_root = Path(__file__).parent.absolute()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

def check_updates_background():
    """Фоновая проверка обновлений"""
    try:
        from Creator.utils.updater import AutoUpdater
        
        # Настройки
        REPO_URL = "gbvxgzbwba/Mindustry_mod_creator_java"
        
        # Конфигурации EXE файлов
        EXE_CONFIGS = [
            {"name": "MindustryModCreator.exe", "version_prefix": "noConsole"},
            {"name": "MindustryModCreatorConsole.exe", "version_prefix": "Console"}
        ]
        
        updater = AutoUpdater(REPO_URL, EXE_CONFIGS)
        
        # Тихая проверка без диалога
        if updater.check_and_update(show_dialog=False):
            print("Обновление запущено в фоне")
        else:
            print("Обновлений не найдено")
            
    except Exception as e:
        print(f"Ошибка фоновой проверки: {e}")

def main():
    """Главная функция запуска"""
    
    # Настройка темы ДО создания окна
    ctk.set_appearance_mode("Dark")
    ctk.set_default_color_theme("blue")
    
    try:
        # Импортируем модули
        from Creator.ui.main_window import MainWindow
        
        # Создаем главное окно
        app = MainWindow()
        
        # Запускаем фоновую проверку обновлений
        update_thread = threading.Thread(target=check_updates_background, daemon=True)
        update_thread.start()
        
        # Запускаем приложение
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