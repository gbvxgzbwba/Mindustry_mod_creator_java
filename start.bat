@echo off
chcp 65001 > nul
title Mindustry Mod Creator

:: Создаем ESC символ (исправленный способ)
for /f %%a in ('echo prompt $E ^| cmd') do set "ESC=%%a"

:: Если ESC не создался, используем альтернативный метод
if "%ESC%"=="" set "ESC="

echo %ESC%[92m========================================%ESC%[0m
echo %ESC%[96m   Mindustry Mod Creator
echo %ESC%[92m========================================%ESC%[0m
echo.

:: Проверяем Python
echo %ESC%[93mПроверяем Python...%ESC%[0m
python --version >nul 2>&1
if errorlevel 1 (
    echo %ESC%[91mPython не найден!%ESC%[0m
    echo %ESC%[93mУстанавливаем Python...%ESC%[0m
    curl -L -o python-installer.exe https://www.python.org/ftp/python/3.13.3/python-3.13.3-amd64.exe
    if exist python-installer.exe (
        start /wait python-installer.exe /quiet InstallAllUsers=1 PrependPath=1 Include_launcher=0
        del python-installer.exe
        echo %ESC%[92mPython успешно установлен!%ESC%[0m
        echo %ESC%[93mОбновляем переменные окружения...%ESC%[0m
        refreshenv >nul 2>&1 || (
            echo %ESC%[91mПерезапустите скрипт для применения изменений%ESC%[0m
            pause
            exit /b 1
        )
    ) else (
        echo %ESC%[91mНе удалось загрузить установщик Python%ESC%[0m
        pause
        exit /b 1
    )
)

:: Проверяем Python снова после возможной установки
python --version >nul 2>&1
if errorlevel 1 (
    echo %ESC%[91mPython все еще не найден. Перезапустите скрипт после установки.%ESC%[0m
    pause
    exit /b 1
)

:: Проверяем pip
echo %ESC%[93mПроверяем pip...%ESC%[0m
python -m pip --version >nul 2>&1
if errorlevel 1 (
    echo %ESC%[91mPip не найден!%ESC%[0m
    echo %ESC%[93mУстанавливаем pip...%ESC%[0m
    curl -L -o get-pip.py https://bootstrap.pypa.io/get-pip.py
    if exist get-pip.py (
        python get-pip.py
        del get-pip.py
        echo %ESC%[92mPip успешно установлен!%ESC%[0m
    ) else (
        echo %ESC%[91mНе удалось загрузить get-pip.py%ESC%[0m
    )
)

:: Проверяем и устанавливаем библиотеки
echo %ESC%[93mПроверяем библиотеки...%ESC%[0m

python -c "import customtkinter" >nul 2>&1
if errorlevel 1 (
    echo %ESC%[93mУстанавливаем customtkinter...%ESC%[0m
    python -m pip install customtkinter
    echo %ESC%[92mcustomtkinter установлен!%ESC%[0m
)

python -c "import requests" >nul 2>&1
if errorlevel 1 (
    echo %ESC%[93mУстанавливаем requests...%ESC%[0m
    python -m pip install requests
    echo %ESC%[92mrequests установлен!%ESC%[0m
)

python -c "import PIL" >nul 2>&1
if errorlevel 1 (
    echo %ESC%[93mУстанавливаем pillow...%ESC%[0m
    python -m pip install pillow
    echo %ESC%[92mPillow установлен!%ESC%[0m
)

:: Очищаем кэш Python
if exist __pycache__ (
    echo %ESC%[93mОчищаем кэш...%ESC%[0m
    rmdir /s /q __pycache__
    echo %ESC%[92mКэш очищен!%ESC%[0m
)

:: Запускаем приложение
echo.
echo %ESC%[92m========================================%ESC%[0m
echo %ESC%[96mЗапуск Mindustry Mod Creator...%ESC%[0m
echo %ESC%[92m========================================%ESC%[0m
echo.

:: Проверяем существование main.py
if not exist main.py (
    echo %ESC%[91mОшибка: файл main.py не найден!%ESC%[0m
    pause
    exit /b 1
)

python main.py

:: Если произошла ошибка, показываем сообщение
if errorlevel 1 (
    echo.
    echo %ESC%[91mПриложение завершилось с ошибкой%ESC%[0m
)

pause