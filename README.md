# Smart FAQ Bot - Salon Fryzjerski "Kleopatra"

Nowoczesny, inteligentny chatbot FAQ zbudowany z użyciem OpenAI API, HTML, CSS i JavaScript. Bot może odpowiadać na często zadawane pytania dotyczące salonu fryzjerskiego używając AI lub lokalnej bazy wiedzy.

## 🚀 Funkcje

- 🤖 **Integracja z OpenAI**: Inteligentne odpowiedzi powered by GPT-3.5-turbo
- 💬 **Nowoczesny interfejs**: Piękny, responsywny interfejs chatu
- 📱 **Mobile-first**: Idealnie działający na wszystkich urządzeniach  
- ⚙️ **Tryb Demo**: Fallback do lokalnej bazy wiedzy gdy brak API
- 🎨 **Polski design**: Dostosowany do polskiego salonu fryzjerskiego
- 🔄 **Real-time**: Natychmiastowe odpowiedzi z realistycznymi opóźnieniami

## 📁 Struktura plików

```
smart-faq-bot/
├── index.html      # Główny plik HTML z interfejsem
├── style.css       # Style i responsywny design  
├── script.js       # Główna logika bota
├── config.js       # Konfiguracja AI i baza wiedzy
└── README.md       # Ten plik
```

## ⚡ Szybki start

### 1. Przygotowanie
```bash
# Sklonuj lub pobierz pliki projektu
# Otwórz folder w VS Code
```

### 2. Konfiguracja OpenAI API (opcjonalnie)
1. Idź na [platform.openai.com](https://platform.openai.com/api-keys)
2. Stwórz nowy API key
3. W pliku `config.js` zmień:
```javascript
const OPENAI_API_KEY = 'sk-proj-TWÓJ_KLUCZ_TUTAJ'; // Wklej tutaj swój klucz
```

### 3. Uruchomienie
- Otwórz `index.html` w przeglądarce
- Bot działa od razu w trybie DEMO (bez API)
- Po dodaniu klucza API - pełna funkcjonalność AI

## 🔧 Konfiguracja

### Edycja informacji o salonie
W pliku `config.js` zmień sekcję `SYSTEM_PROMPT`:

```javascript
INFORMACJE O SALONIE:
- Nazwa: Twój Salon
- Adres: Twój adres
- Telefon: Twój numer
// ... inne dane
```

### Dodawanie usług i cen
```javascript
CENNIK USŁUG:
STRZYŻENIE:
- Damskie: 80-120 zł
- Męskie: 50-70 zł
// ... dodaj swoje ceny
```

### Lokalna baza wiedzy (fallback)
```javascript
const KNOWLEDGE_BASE = {
    services: {
        keywords: ['usługi', 'strzyżenie', 'farbowanie'],
        response: 'Twoja odpowiedź tutaj...'
    }
    // ... dodaj więcej kategorii
};
```

## 💡 Jak to działa

### Z OpenAI API:
1. **Użytkownik pyta** → 2. **Analiza przez GPT-3.5** → 3. **Inteligentna odpowiedź**

### W trybie Demo:
1. **Użytkownik pyta** → 2. **Wyszukiwanie słów kluczowych** → 3. **Dopasowana odpowiedź**

### Funkcje specjalne:
- **Pilne sprawy** → Automatyczne przekierowanie do recepcji
- **Reklamacje** → Przekierowanie do kierownika  
- **Historia rozmowy** → Kontekst dla lepszych odpowiedzi

## 🎨 Customizacja

### Zmiana kolorów i stylów
```css
/* W style.css zmień gradient główny */
background: linear-gradient(135deg, #TwójKolor1, #TwójKolor2);
```

### Dodanie nowych intencji
```javascript
// W config.js dodaj nowe kategorie
const INTENTS = {
    NOWA_KATEGORIA: ['słowo1', 'słowo2', 'fraza'],
    // ... existing
};
```

### Rozszerzenie funkcjonalności
```javascript
// W script.js dodaj nowe funkcje
function handleSpecialCases(message, intent) {
    if (intent === 'NOWA_KATEGORIA') {
        return {
            response: "Specjalna odpowiedź",
            action: "CUSTOM_ACTION"
        };
    }
}
```

## 🔍 Debug i testowanie

Otwórz Developer Tools (F12) i użyj:

```javascript
// Sprawdź historię rozmowy
debugBot.getHistory()

// Testuj rozpoznawanie intencji  
debugBot.testIntent("jakie są ceny strzyżenia?")

// Sprawdź konfigurację
debugBot.getConfig()
```

## 📊 Możliwości rozbudowy

### 1. Integracja z kalendarzem
```javascript
// Dodaj funkcję sprawdzania wolnych terminów
async function checkAvailability(date) {
    // Połączenie z API kalendarza
}
```

### 2. System płatności
```javascript
// Dodaj możliwość płatności online
function initiatePayment(service, price) {
    // Integracja z PayU/Przelewy24
}
```

### 3. Analytics
```javascript
// Śledzenie interakcji
function trackEvent(event, data) {
    // Google Analytics lub własne API
}
```

## 💰 Koszty

- **Tryb Demo**: Darmowy ✅
- **OpenAI API**: ~0.002$ za 1000 tokenów (~50 wiadomości = $0.10)
- **Miesięczny koszt**: 20-50 zł dla małego salonu

## 🆘 Troubleshooting

### Problem: Bot nie odpowiada
```javascript
// Sprawdź w konsoli:
console.log('API configured:', IS_API_CONFIGURED);
// Jeśli false - dodaj klucz API
```

### Problem: Błędne odpowiedzi
```javascript
// Sprawdź i edytuj SYSTEM_PROMPT w config.js
// Dodaj więcej informacji o salonie
```

### Problem: Nie działa na telefonie
```css
/* Sprawdź CSS - responsywne style są już dodane */
@media (max-width: 480px) { /* ... */ }
```

## 📞 Wsparcie

- **Email**: kontakt@salon-kleopatra.pl
- **Telefon**: 123-456-789
- **GitHub Issues**: Do zgłaszania błędów

## 📄 Licencja

MIT License - możesz swobodnie używać i modyfikować.

---

**🎯 Cel**: Zaautomatyzować 80% pytań klientów i zwiększyć konwersję o 30%  
**💡 Tip**: Regularnie aktualizuj bazę wiedzy na podstawie pytań klientów
