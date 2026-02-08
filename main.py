import sys
from pathlib import Path
import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox

from Creator.ui.main_window import MainWindow

ctk.set_appearance_mode("Dark")

def main():
    app = MainWindow()
    app.run()

if __name__ == "__main__":
    main()