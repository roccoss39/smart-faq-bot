# Smart FAQ Bot - Salon Fryzjerski "Kleopatra"

🤖 **Zaawansowany bot wieloplatformowy** z integracją AI (Together API), Facebook Messenger, systemem kalendarza i rezerwacji online. Obsługuje wielodostęp użytkowników z separacją sesji.

## 🚀 Funkcje

- 🤖 **Integracja z Together AI**: Inteligentne odpowiedzi powered by Llama-3.1-70B
- 📘 **Facebook Messenger**: Natywna integracja z webhook
- 📅 **System rezerwacji**: Zarządzanie terminami i kalendarzem
- 👥 **Multi-user**: Równoczesna obsługa wielu użytkowników
- 🔄 **Separacja sesji**: Każdy użytkownik ma własną sesję rozmowy
- 💬 **Interfejs webowy**: Responsywny chat na stronie
- 📱 **Mobile-first**: Działa perfekcyjnie na telefonach
- 🧪 **Kompleksowe testy**: System testów wielodostępu użytkowników

## 📁 Struktura projektu

```
smart-faq-bot/
├── backend.py              # Główny serwer Flask + API endpoints
├── bot_logic_ai.py         # Logika AI i zarządzanie sesjami
├── facebook_webhook.py     # Webhook Facebook Messenger
├── calendar_system.py      # System kalendarza i rezerwacji
├── test_multi_users.py     # Testy wielodostępu użytkowników
├── index.html              # Interfejs webowy chatu
├── style.css               # Style responsywne
├── script.js               # Frontend JavaScript
├── config.js               # Konfiguracja bazy wiedzy
├── .env                    # Zmienne środowiskowe (NIE commituj!)
├── .env.example            # Przykład konfiguracji
└── README.md               # Ten plik
```

## ⚡ Szybki start

### 1. **Przygotowanie środowiska**

```bash
# Sklonuj repozytorium
git clone https://github.com/USERNAME/smart-faq-bot.git
cd smart-faq-bot

# Aktywuj wirtualne środowisko (jeśli używasz)
source .venv/bin/activate

# Zainstaluj zależności
pip install -r requirements.txt
```

### 2. **Konfiguracja zmiennych środowiskowych**

```bash
# Skopiuj przykład konfiguracji
cp .env.example .env

# Edytuj .env i uzupełnij klucze API
nano .env
```

**Zawartość `.env`:**
```bash
# Together AI
TOGETHER_API_KEY=your_together_ai_key_here

# Facebook Messenger
FACEBOOK_ACCESS_TOKEN=your_facebook_page_access_token
FACEBOOK_VERIFY_TOKEN=your_custom_verify_token_12345

# Google Calendar (opcjonalnie)
GOOGLE_CALENDAR_ID=your_calendar_id
```

### 3. **Uruchomienie backendu**

```bash
# Uruchom serwer Flask
python backend.py
```

Serwer wystartuje na `http://localhost:5000`

### 4. **Konfiguracja ngrok dla Facebook Webhook**

```bash
# W nowym terminalu uruchom ngrok
ngrok http 5000
```

**Otrzymasz URL typu:** `https://abc123.ngrok.io`

### 5. **Konfiguracja Facebook Webhook**

1. **Idź do Facebook Developers** → Twoja aplikacja → Messenger → Settings
2. **Webhook URL:** `https://abc123.ngrok.io/` (URL z ngrok)
3. **Verify Token:** Ten sam co w `.env` (np. `your_custom_verify_token_12345`)
4. **Subscription Fields:** Zaznacz `messages`, `messaging_postbacks`
5. **Kliknij "Verify and Save"**

### 6. **Test działania**

```bash
# Uruchom testy wielodostępu
python test_multi_users.py

# Lub otwórz interfejs webowy
# http://localhost:5000/
```

## 🔧 Szczegółowa konfiguracja

### **Together AI API Setup**

1. Idź na [api.together.xyz](https://api.together.xyz)
2. Stwórz konto i wygeneruj API key
3. Dodaj do `.env`: `TOGETHER_API_KEY=your_key_here`

### **Facebook Messenger Setup**

1. **Facebook Developers** → Create App → Business
2. **Add Product** → Messenger
3. **Generate Page Access Token** → Dodaj do `.env`
4. **Webhook setup** (jak powyżej z ngrok)
5. **Subscribe to page** → Wybierz swoją stronę Facebook

### **Google Calendar (opcjonalnie)**

```bash
# Pobierz credentials.json z Google Cloud Console
# Dodaj GOOGLE_CALENDAR_ID do .env
```

## 🧪 Testowanie

### **Test podstawowy**
```bash
python backend.py
# Odwiedź http://localhost:5000
```

### **Test wielodostępu użytkowników**
```bash
python test_multi_users.py
```

### **Test Facebook Messenger**
```bash
# 1. Uruchom backend + ngrok
# 2. Skonfiguruj webhook
# 3. Napisz na FB do swojego bota
```

### **Debug API**
```bash
curl http://localhost:5000/api/health
curl -X POST http://localhost:5000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "test", "user_id": "test123"}'
```

## 🎯 Funkcje specjalne

### **Wielodostęp użytkowników**
- Każdy użytkownik ma **osobną sesję**
- **Separacja rozmów** - bez mieszania kontekstów
- **Automatic cleanup** wygasłych sesji
- **Memory monitoring** i optymalizacja

### **System rezerwacji**
```
User: "Chcę się umówić"
Bot: "Dostępne terminy: jutro 10:00, 14:00..."
User: "Jutro 10:00"
Bot: "Podaj imię i telefon"
User: "Jan Kowalski, 123456789"
Bot: ✅ "Rezerwacja potwierdzona!"
```

### **Inteligentne odpowiedzi**
- **Kontekst rozmowy** - pamięta wcześniejsze wiadomości
- **Intent recognition** - rozpoznaje intencje użytkownika
- **Fallback responses** - gdy AI nie rozumie

## 🔧 Customizacja

### **Edycja informacji o salonie**

```python
# W bot_logic_ai.py zmień SYSTEM_PROMPT
SYSTEM_PROMPT = """
INFORMACJE O SALONIE:
- Nazwa: Twój Salon
- Adres: Twój adres  
- Telefon: Twój numer
...
"""
```

### **Dodanie nowych usług**

```python
CENNIK USŁUG:
STRZYŻENIE:
- Damskie: 80-120 zł
- Męskie: 50-70 zł
TWOJE_NOWE_USŁUGI:
- Manicure: 60 zł
- Pedicure: 80 zł
```

### **Zmiana kolorów interfejsu**

```css
/* W style.css */
:root {
    --primary-color: #TwójKolor;
    --secondary-color: #TwójKolor2;
}
```

## 📊 Monitoring i Analytics

### **Logi systemu**
```bash
# Sprawdź logi backendu
tail -f backend.log

# Sprawdź sesje użytkowników
curl http://localhost:5000/api/sessions
```

### **Metryki wydajności**
```python
# W test_multi_users.py
def check_memory_usage():
    # Monitorowanie zużycia pamięci przez sesje
```

## 🚨 Troubleshooting

### **Problem: Bot nie odpowiada na Facebook**

```bash
# 1. Sprawdź logi backendu
python backend.py

# 2. Sprawdź webhook URL
curl https://your-ngrok-url.ngrok.io/

# 3. Sprawdź czy backend otrzymuje wiadomości
# Powinnaś widzieć: "👤 Nowy użytkownik: 1234567890"
```

### **Problem: "Backend może nie działać"**

```bash
# 1. Sprawdź czy serwer działa
curl http://localhost:5000/api/health

# 2. Sprawdź port
lsof -i :5000

# 3. Uruchom ponownie
python backend.py
```

### **Problem: Błąd Together API**

```bash
# 1. Sprawdź klucz API w .env
echo $TOGETHER_API_KEY

# 2. Test API
curl -H "Authorization: Bearer $TOGETHER_API_KEY" \
     https://api.together.xyz/v1/models
```

### **Problem: Użytkownicy są ignorowani**

1. **Sprawdź tryb rozwoju** - tylko admini mogą pisać
2. **Dodaj testerów** w Facebook Developers → Roles
3. **Przejdź przez App Review** dla pełnej publikacji

## 💰 Koszty eksploatacji

- **Together AI**: ~$0.60/1M tokenów (~10-30zł/miesiąc)
- **ngrok**: Darmowy (podstawowy) | $8/mies (pro)
- **Hosting**: VPS ~20-50zł/miesiąc
- **Facebook**: Darmowy

**Szacowany koszt miesięczny: 30-100zł**

## 🚀 Deployment na produkcję

### **VPS/Serwer**
```bash
# Na serwerze
git clone https://github.com/USERNAME/smart-faq-bot.git
cd smart-faq-bot
pip install -r requirements.txt

# Konfiguracja
cp .env.example .env
nano .env

# Uruchomienie z PM2 (process manager)
npm install -g pm2
pm2 start "python backend.py" --name smart-faq-bot
pm2 startup
pm2 save
```

### **Nginx (reverse proxy)**
```nginx
server {
    listen 80;
    server_name yourdomain.com;
    
    location / {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## 📞 Wsparcie

- **GitHub Issues**: Zgłaszanie błędów
- **Email**: podziewski39@o2.pl
- **Facebook**: Problemy z integracją Messenger

## 📄 Licencja

MIT License - możesz swobodnie używać, modyfikować i dystrybuować.

---

**🎯 Cel**: Automatyzacja 80% pytań klientów i zwiększenie konwersji o 30%  
**⚡ Status**: Gotowy do produkcji z pełnym multi-user supportem  
**🔧 Stack**: Python/Flask + Together AI + Facebook Messenger + JavaScript

**💡 Pro tip**: Regularnie aktualizuj bazę wiedzy na podstawie najczęstszych pytań klientów!
