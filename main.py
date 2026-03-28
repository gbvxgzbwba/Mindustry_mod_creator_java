# main.py
import sys
import os
from pathlib import Path
import customtkinter as ctk

# Добавляем корень проекта в PYTHONPATH
project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Устанавливаем рабочую директорию
os.chdir(project_root)

# Импорт должен быть абсолютным
from Creator.ui.main_window import MainWindow

ctk.set_appearance_mode("Dark")

def main():
    app = MainWindow()
    app.run()

if __name__ == "__main__":
    main()