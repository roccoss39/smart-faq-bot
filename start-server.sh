#!/bin/bash
# ================================
# URUCHOM SMART FAQ BOT LOKALNIE
# ================================

echo "🚀 Uruchamianie Smart FAQ Bot..."
echo "📁 Folder: $(pwd)"
echo ""

# Sprawdź czy pliki istnieją
if [ ! -f "index.html" ]; then
    echo "❌ Błąd: Nie znaleziono pliku index.html"
    echo "💡 Upewnij się, że jesteś w folderze smart-faq-bot"
    exit 1
fi

echo "✅ Pliki znalezione:"
echo "   - index.html"
echo "   - config.js"  
echo "   - script.js"
echo "   - style.css"
echo ""

# Sprawdź dostępne opcje serwera
if command -v python3 &> /dev/null; then
    echo "🐍 Uruchamianie serwera Python..."
    echo "🌐 Bot będzie dostępny na: http://localhost:8000"
    echo "🌐 Test page: http://localhost:8000/test.html"
    echo ""
    echo "📱 Aby zatrzymać serwer, naciśnij Ctrl+C"
    echo ""
    python3 -m http.server 8000
elif command -v python &> /dev/null; then
    echo "🐍 Uruchamianie serwera Python..."
    echo "🌐 Bot będzie dostępny na: http://localhost:8000"
    echo "🌐 Test page: http://localhost:8000/test.html"
    echo ""
    echo "📱 Aby zatrzymać serwer, naciśnij Ctrl+C"
    echo ""
    python -m http.server 8000
elif command -v npx &> /dev/null; then
    echo "📦 Uruchamianie serwera Node.js..."
    echo "🌐 Bot będzie dostępny na: http://localhost:3000"
    echo ""
    npx serve . -p 3000
else
    echo "❌ Nie znaleziono Python ani Node.js"
    echo ""
    echo "💡 Zainstaluj jedną z opcji:"
    echo "   - Python: https://python.org"
    echo "   - Node.js: https://nodejs.org"
    echo ""
    echo "🔧 Lub użyj VS Code z rozszerzeniem 'Live Server'"
    exit 1
fi
