@echo off
setlocal

:: === Настройки ===
set PROJECT_NAME=CognitiveMotorTests
set MAIN_SCRIPT=main.py
set ICON_FILE=app_icon.ico
set FONT_FILE=resources/DejaVuSans.ttf
set OUTPUT_DIR=dist

:: === Проверка наличия основных файлов ===
if not exist "%MAIN_SCRIPT%" (
    echo Ошибка: не найден основной файл %MAIN_SCRIPT%
    pause
    exit /b 1
)

if not exist "%ICON_FILE%" (
    echo Предупреждение: иконка %ICON_FILE% не найдена. Сборка без иконки.
    set ICON_ARG=
) else (
    set ICON_ARG=--icon="%ICON_FILE%"
)

if not exist "%FONT_FILE%" (
    echo Ошибка: шрифт %FONT_FILE% не найден!
    pause
    exit /b 1
)

:: === Установка зависимостей (опционально) ===
echo Установка/обновление PyInstaller...
pip install pyinstaller PyQt6 reportlab --upgrade --quiet

:: === Очистка предыдущих сборок ===
echo Очистка старых сборок...
if exist "%OUTPUT_DIR%" rmdir /s /q "%OUTPUT_DIR%"
if exist "build" rmdir /s /q "build"
if exist "%PROJECT_NAME%.spec" del "%PROJECT_NAME%.spec"

:: === Сборка в один файл ===
echo Сборка приложения в один исполняемый файл...
pyinstaller ^
  --onefile ^
  --windowed ^
  --add-data "resources/DejaVuSans.ttf;resources" ^
  --add-data "report.py;." ^
  --add-data "cognitive_metrics.py;." ^
  --add-data "progress_tracker.py;." ^
  --hidden-import=reportlab.lib.fonts ^
  --hidden-import=reportlab.pdfbase.ttfonts ^
  --hidden-import=json ^
  %ICON_ARG% ^
  --name="%PROJECT_NAME%" ^
  --clean ^
  "%MAIN_SCRIPT%"

:: === Проверка результата ===
if exist "%OUTPUT_DIR%\%PROJECT_NAME%.exe" (
    echo.
    echo ✅ Сборка успешно завершена!
    echo Исполняемый файл: %cd%\%OUTPUT_DIR%\%PROJECT_NAME%.exe
    echo Его можно копировать на другие компьютеры без установки Python.
) else (
    echo ❌ Ошибка: исполняемый файл не создан.
    pause
    exit /b 1
)

pause