@echo off
REM ================================
REM URUCHOM SMART FAQ BOT LOKALNIE  
REM ================================

echo 🚀 Uruchamianie Smart FAQ Bot...
echo 📁 Folder: %cd%
echo.

REM Sprawdź czy pliki istnieją
if not exist "index.html" (
    echo ❌ Błąd: Nie znaleziono pliku index.html
    echo 💡 Upewnij się, że jesteś w folderze smart-faq-bot
    pause
    exit /b 1
)

echo ✅ Pliki znalezione:
echo    - index.html
echo    - config.js
echo    - script.js  
echo    - style.css
echo.

REM Sprawdź dostępne opcje serwera
where python >nul 2>nul
if %errorlevel% == 0 (
    echo 🐍 Uruchamianie serwera Python...
    echo 🌐 Bot będzie dostępny na: http://localhost:8000
    echo 🌐 Test page: http://localhost:8000/test.html
    echo.
    echo 📱 Aby zatrzymać serwer, naciśnij Ctrl+C
    echo.
    python -m http.server 8000
    goto :end
)

where node >nul 2>nul
if %errorlevel% == 0 (
    echo 📦 Uruchamianie serwera Node.js...
    echo 🌐 Bot będzie dostępny na: http://localhost:3000
    echo.
    npx serve . -p 3000
    goto :end
)

echo ❌ Nie znaleziono Python ani Node.js
echo.
echo 💡 Zainstaluj jedną z opcji:
echo    - Python: https://python.org
echo    - Node.js: https://nodejs.org  
echo.
echo 🔧 Lub użyj VS Code z rozszerzeniem 'Live Server'
pause

:end
