@echo off
echo ===================================
echo   Memory Card Game - Build Script
echo ===================================
echo.

echo Installing dependencies...
pip install pygame pyinstaller --quiet
if %errorlevel% neq 0 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)

echo Building executable...
pyinstaller --onedir --add-data "assets;assets" --name "MemoryCardGame" --windowed --noconfirm main.py
if %errorlevel% neq 0 (
    echo ERROR: Build failed
    pause
    exit /b 1
)

echo Copying source files...
copy main.py dist\MemoryCardGame\ >nul
copy game.py dist\MemoryCardGame\ >nul
copy ui_controls.py dist\MemoryCardGame\ >nul
copy asset_state.py dist\MemoryCardGame\ >nul
copy ai_logic.py dist\MemoryCardGame\ >nul
copy physics_collision.py dist\MemoryCardGame\ >nul

echo.
echo ===================================
echo   Build complete!
echo   EXE location: dist\MemoryCardGame\MemoryCardGame.exe
echo ===================================
pause
