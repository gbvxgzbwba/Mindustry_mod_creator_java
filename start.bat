@echo off
chcp 65001 > nul 2>&1
title Mindustry Mod Creator

echo ========================================
echo    Mindustry Mod Creator
echo ========================================
echo.

:: Проверяем Python через py launcher (более надежно)
where py >nul 2>&1
if errorlevel 1 (
    echo [ОШИБКА] Python не найден!
    echo Установите Python 3.10+ с официального сайта
    echo https://www.python.org/downloads/
    echo.
    echo Не забудьте отметить "Add Python to PATH" при установке
    pause
    exit /b 1
)

:: Получаем версию Python
for /f "tokens=2" %%I in ('py -c "import sys; print(sys.version.split()[0])" 2^>nul') do set "PY_VERSION=%%I"
echo Найден Python: %PY_VERSION%

:: Проверяем версию (должна быть 3.10+)
py -c "import sys; exit(0 if sys.version_info >= (3,10) else 1)" >nul 2>&1
if errorlevel 1 (
    echo [ОШИБКА] Требуется Python 3.10 или выше
    echo Установленная версия: %PY_VERSION%
    pause
    exit /b 1
)

:: Создаем виртуальное окружение, если его нет
if not exist "venv" (
    echo Создаем виртуальное окружение...
    py -m venv venv
    echo Готово
)

:: Активируем виртуальное окружение
call venv\Scripts\activate.bat

:: Устанавливаем зависимости (только если requirements.txt новее)
if not exist "venv\lib\site-packages\installed" (
    echo Устанавливаем зависимости...
    py -m pip install --upgrade pip
    py -m pip install customtkinter requests pillow
    echo %date% %time% > venv\lib\site-packages\installed
    echo Готово
)

:: Запускаем приложение
echo.
echo ========================================
echo    Запуск...
echo ========================================
echo.

py main.py

:: Если произошла ошибка, показываем сообщение
if errorlevel 1 (
    echo.
    echo [ОШИБКА] Приложение завершилось с ошибкой
    echo Проверьте установку Java JDK 17
    echo.
)

:: Деактивируем виртуальное окружение
call deactivate

pause