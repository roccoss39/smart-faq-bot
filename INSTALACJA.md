# 🚀 INSTRUKCJA INSTALACJI - Smart FAQ Bot

## 📋 Wymagania
- Przeglądarka internetowa (Chrome, Firefox, Safari, Edge)
- Opcjonalnie: klucz API OpenAI (dla pełnej funkcjonalności AI)
- Opcjonalnie: VS Code (do edycji kodu)

## ⚡ SZYBKA INSTALACJA (2 minuty)

### Krok 1: Pobierz pliki
```bash
# Opcja A: Pobierz jako ZIP z GitHub
# Opcja B: Sklonuj repozytorium
git clone [LINK_DO_REPO]
cd smart-faq-bot
```

### Krok 2: Otwórz w przeglądarce
```bash
# Po prostu otwórz plik index.html w przeglądarce
# Lub jeśli masz VS Code:
code .
# I użyj Live Server extension
```

### Krok 3: Test działania
1. Otwórz chatbot
2. Napisz: "Jakie są ceny strzyżenia?"
3. Bot powinien odpowiedzieć ✅

**🎉 Gotowe! Bot działa w trybie DEMO**

## 🤖 PEŁNA FUNKCJONALNOŚĆ AI (opcjonalnie)

### Krok 1: Załóż konto OpenAI
1. Idź na: https://platform.openai.com
2. Zarejestruj się / zaloguj
3. Przejdź do: API Keys
4. Kliknij: "Create new secret key"
5. Skopiuj klucz (zaczyna się od `sk-`)

### Krok 2: Dodaj klucz do bota
1. Otwórz plik: `config.js`
2. Znajdź linię:
```javascript
const OPENAI_API_KEY = 'sk-proj-TWÓJ_KLUCZ_TUTAJ';
```
3. Zamień `sk-proj-TWÓJ_KLUCZ_TUTAJ` na swój prawdziwy klucz
4. Zapisz plik
5. Odśwież stronę w przeglądarce

### Krok 3: Sprawdź status
- Status powinien zmienić się z "DEMO MODE" na "AI CONNECTED" 🟢

## 🛠️ KUSTOMIZACJA POD SWÓJ SALON

### Zmiana danych salonu (config.js):
```javascript
// Znajdź i zmień:
INFORMACJE O SALONIE:
- Nazwa: Salon Fryzjerski "TWOJA_NAZWA"
- Adres: ul. Twoja 15, Miasto
- Telefon: 123-456-789
```

### Zmiana cen (config.js):
```javascript
CENNIK USŁUG:
STRZYŻENIE:
- Damskie: 80-120 zł  // <- Zmień na swoje ceny
- Męskie: 50-70 zł
```

### Zmiana kolorów (style.css):
```css
/* Znajdź i zmień gradient: */
background: linear-gradient(135deg, #TwójKolor1, #TwójKolor2);
```

## 🚨 ROZWIĄZYWANIE PROBLEMÓW

### Problem: Bot nie odpowiada
**Rozwiązanie:**
1. Otwórz Developer Tools (F12)
2. Sprawdź konsolę czy są błędy
3. Sprawdź czy pliki się załadowały

### Problem: "DEMO MODE" mimo dodania klucza API
**Rozwiązanie:**
1. Sprawdź czy klucz zaczyna się od `sk-`
2. Sprawdź czy nie ma spacji przed/po kluczu
3. Odśwież stronę (Ctrl+F5)

### Problem: Bot daje złe odpowiedzi
**Rozwiązanie:**
1. Edytuj sekcję `SYSTEM_PROMPT` w config.js
2. Dodaj więcej szczegółów o swoim salonie
3. Przetestuj ponownie

### Problem: Nie działa na telefonie
**Rozwiązanie:**
- Sprawdź czy używasz nowoczesnej przeglądarki
- Style responsywne są już wbudowane

## 💰 KOSZTY

### Tryb DEMO:
- **Koszt**: 0 zł ✅
- **Funkcje**: Podstawowe odpowiedzi z bazy wiedzy

### Tryb AI (OpenAI):
- **Koszt**: ~20-50 zł/miesiąc dla małego salonu
- **Funkcje**: Inteligentne odpowiedzi AI
- **Szczegóły**: $0.002 za 1000 tokenów (~50 wiadomości = 0.50 zł)

## 📱 HOSTING (udostępnienie online)

### Opcja 1: Netlify (DARMOWE)
1. Idź na: netlify.com
2. Przeciągnij folder z plikami
3. Gotowe! Masz link do bota

### Opcja 2: GitHub Pages (DARMOWE)
1. Stwórz repo na GitHub
2. Wrzuć pliki
3. Włącz GitHub Pages w ustawieniach

### Opcja 3: Własny hosting
- Wrzuć pliki na serwer przez FTP
- Bot działa na każdym hostingu HTML

## 🎯 NASTĘPNE KROKI

### Po instalacji:
1. **Przetestuj** - Zadaj różne pytania
2. **Dostosuj** - Zmień dane na swoje
3. **Wdróż** - Dodaj na stronę salonu
4. **Monitoruj** - Zobacz jakie pytania zadają klienci
5. **Rozbuduj** - Dodaj nowe odpowiedzi

### Rozbudowa:
- ✅ Integracja z kalendarzem rezerwacji
- ✅ System płatności online  
- ✅ Analytics i statystyki
- ✅ Wsparcie dla więcej języków

## 📞 WSPARCIE

**Problemy techniczne:**
- GitHub Issues: [LINK]
- Email: support@example.com

**Pytania biznesowe:**
- Jak zwiększyć konwersję?
- Jakie metryki śledzić?
- Jak zintegrować z istniejącą stroną?

---

**🎉 Powodzenia z nowym AI asystentem!**  
*Automatyzuj odpowiedzi, oszczędzaj czas, zwiększaj sprzedaż* 💰
