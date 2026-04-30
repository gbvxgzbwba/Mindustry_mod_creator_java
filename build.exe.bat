@echo off
chcp 65001 >nul
title Сборка Mindustry Mod Creator

echo ========================================
echo   Сборка Mindustry Mod Creator
echo ========================================
echo.

echo 1. Очистка старых сборок...
rmdir /s /q build 2>nul
rmdir /s /q dist 2>nul
del *.spec 2>nul

echo 2. Установка PyInstaller (если не установлен)...
pip install pyinstaller --quiet

echo 3. Сборка приложения...
pyinstaller --onefile ^
    --name "MindustryModCreator" ^
    --noconsole ^
    --add-data "Creator;Creator" ^
    --add-data "Creator;icons" ^
    --add-data "Creator;utils" ^
    --add-data "Creator;langs" ^
    --hidden-import "PIL" ^
    --hidden-import "PIL._imaging" ^
    --hidden-import "customtkinter" ^
    --hidden-import "requests" ^
    --hidden-import "PIL.Image" ^
    --hidden-import "PIL.ImageDraw" ^
    --hidden-import "PIL.ImageTk" ^
    --hidden-import "PIL.ImageFilter" ^
    --hidden-import "PIL.ImageOps" ^
    --hidden-import "PIL._tkinter_finder" ^
    --collect-all "customtkinter" ^
    --collect-all "PIL" ^
    main.py
pyinstaller --onefile ^
    --name "MindustryModCreatorConsole" ^
    --add-data "Creator;Creator" ^
    --add-data "Creator;icons" ^
    --add-data "Creator;utils" ^
    --add-data "Creator;langs" ^
    --hidden-import "PIL" ^
    --hidden-import "PIL._imaging" ^
    --hidden-import "customtkinter" ^
    --hidden-import "requests" ^
    --hidden-import "PIL.Image" ^
    --hidden-import "PIL.ImageDraw" ^
    --hidden-import "PIL.ImageTk" ^
    --hidden-import "PIL.ImageFilter" ^
    --hidden-import "PIL.ImageOps" ^
    --hidden-import "PIL._tkinter_finder" ^
    --collect-all "customtkinter" ^
    --collect-all "PIL" ^
    main.py

echo.
echo ========================================
echo   ГОТОВО!
echo ========================================
echo.
echo Файл создан: dist\MindustryModCreator.exe
echo.
pause