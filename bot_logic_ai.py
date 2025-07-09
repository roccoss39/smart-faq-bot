"""
Bot Logic AI - Uproszczona wersja z TYLKO używanymi funkcjami
"""

import logging
import re
from datetime import datetime, timedelta
import pytz
from together import Together
import os
from calendar_service import get_available_slots, create_appointment, cancel_appointment

logger = logging.getLogger(__name__)

# ==============================================
# KONFIGURACJA AI
# ==============================================

api_key = os.getenv('TOGETHER_API_KEY')
if not api_key:
    logger.error("BŁĄD: Brak zmiennej środowiskowej TOGETHER_API_KEY")
    raise Exception("Brak Together API key")

client = Together(api_key=api_key)

# ==============================================
# HISTORIA UŻYTKOWNIKÓW
# ==============================================

user_conversations = {}

def get_user_history(user_id):
    """Pobierz historię rozmowy użytkownika"""
    if user_id not in user_conversations:
        user_conversations[user_id] = []
    return user_conversations[user_id]

def add_to_history(user_id, role, message):
    """Dodaj wiadomość do historii"""
    history = get_user_history(user_id)
    history.append({"role": role, "content": message})
    
    # Ogranicz historię do ostatnich 20 wiadomości
    if len(history) > 20:
        user_conversations[user_id] = history[-20:]

# ==============================================
# FUNKCJA DATY
# ==============================================

def get_current_date_info():
    """Zwraca aktualną datę i czas dla AI"""
    tz = pytz.timezone('Europe/Warsaw')
    now = datetime.now(tz)
    
    # Mapowanie angielskich na polskie nazwy
    day_names = {
        'Monday': 'poniedziałek',
        'Tuesday': 'wtorek', 
        'Wednesday': 'środa',
        'Thursday': 'czwartek',
        'Friday': 'piątek',
        'Saturday': 'sobota',
        'Sunday': 'niedziela'
    }
    
    month_names = {
        'January': 'styczeń', 'February': 'luty', 'March': 'marzec',
        'April': 'kwiecień', 'May': 'maj', 'June': 'czerwiec',
        'July': 'lipiec', 'August': 'sierpień', 'September': 'wrzesień',
        'October': 'październik', 'November': 'listopad', 'December': 'grudzień'
    }
    
    today_eng = now.strftime('%A')
    today_pl = day_names.get(today_eng, today_eng.lower())
    
    tomorrow = now + timedelta(days=1)
    tomorrow_eng = tomorrow.strftime('%A')
    tomorrow_pl = day_names.get(tomorrow_eng, tomorrow_eng.lower())
    
    month_pl = month_names.get(now.strftime('%B'), now.strftime('%B'))
    
    # Zwróć sformatowany string dla AI
    return f"""📅 AKTUALNA DATA I CZAS:
- Dzisiaj: {today_pl}, {now.day} {month_pl} {now.year}
- Jutro: {tomorrow_pl}
- Godzina: {now.strftime('%H:%M')}
- Dzień tygodnia: {today_pl}

POLSKIE NAZWY DNI:
- Monday = poniedziałek
- Tuesday = wtorek  
- Wednesday = środa
- Thursday = czwartek
- Friday = piątek
- Saturday = sobota
- Sunday = niedziela

MAPOWANIE WZGLĘDNYCH DAT:
- Gdy klient pyta o "jutro" = {tomorrow_pl}
- Gdy klient pyta o "dzisiaj" = {today_pl}
- Gdy klient pyta o "pojutrze" = {day_names.get((now + timedelta(days=2)).strftime('%A'), 'pojutrze')}"""

# ==============================================
# CZYSZCZENIE ODPOWIEDZI AI
# ==============================================

def clean_thinking_response_enhanced(response_text):
    """Usuwa <think> tagi ale zachowuje treść odpowiedzi"""
    if not response_text:
        return ""
        
    original = response_text
    cleaned = response_text
    
    # 1. USUŃ WSZYSTKIE THINKING BLOKI
    cleaned = re.sub(r'<think>.*?</think>', '', cleaned, flags=re.DOTALL | re.IGNORECASE)
    cleaned = re.sub(r'<thinking>.*?</thinking>', '', cleaned, flags=re.DOTALL | re.IGNORECASE)
    
    # 2. USUŃ NIEDOMKNIĘTE THINKING TAGI
    cleaned = re.sub(r'<think[^>]*>.*?(?=\n[A-ZĄĆĘŁŃÓŚŹŻ]|$)', '', cleaned, flags=re.DOTALL | re.IGNORECASE)
    cleaned = re.sub(r'<thinking[^>]*>.*?(?=\n[A-ZĄĆĘŁŃÓŚŹŻ]|$)', '', cleaned, flags=re.DOTALL | re.IGNORECASE)
    
    # 3. USUŃ WSZYSTKIE TAGI HTML
    cleaned = re.sub(r'<[^>]*>', '', cleaned)
    
    # 4. USUŃ TYPOWE AI INTRO PHRASES (TYLKO NA POCZĄTKU)
    intro_phrases = [
        r'^okay,?\s+so.*?[.!]\s*',
        r'^let\s+me\s+go\s+through.*?[.!]\s*',
        r'^i\s+need\s+to\s+analyze.*?[.!]\s*',
        r'^looking\s+at\s+this\s+message.*?[.!]\s*'
    ]
    
    for phrase in intro_phrases:
        cleaned = re.sub(phrase, '', cleaned, flags=re.IGNORECASE)
    
    # 5. USUŃ POJEDYNCZE KATEGORIE AI (jeśli to cała odpowiedź)
    single_word_categories = ["CONTACT_DATA", "BOOKING", "ASK_AVAILABILITY", "WANT_APPOINTMENT", "CANCEL_VISIT", "OTHER_QUESTION"]
    
    cleaned_stripped = cleaned.strip()
    if cleaned_stripped in single_word_categories:
        # To jest błędna odpowiedź - AI zwróciło tylko kategorię
        logger.warning(f"⚠️ AI zwróciło tylko kategorię: {cleaned_stripped}")
        return "Cześć! Jak mogę ci pomóc? 😊"
    
    # 6. USUŃ KATEGORIE TYLKO Z POCZĄTKU/KOŃCA LINII
    for category in single_word_categories:
        # Usuń kategorię z początku linii + opcjonalne znaki
        cleaned = re.sub(rf'^{category}[\s\.\-]*', '', cleaned, flags=re.IGNORECASE | re.MULTILINE)
        # Usuń kategorię z końca linii + opcjonalne znaki  
        cleaned = re.sub(rf'[\s\.\-]*{category}$', '', cleaned, flags=re.IGNORECASE | re.MULTILINE)
    
    # 7. WYCZYŚĆ PUSTE LINIE I BIAŁE ZNAKI
    cleaned = '\n'.join(line.strip() for line in cleaned.split('\n') if line.strip())
    cleaned = cleaned.strip()
    
    # 8. JEŚLI PO CZYSZCZENIU NICZEGO NIE MA, ZWRÓĆ DOMYŚLNĄ ODPOWIEDŹ
    if not cleaned or len(cleaned) < 5:
        logger.warning(f"⚠️ Pusta odpowiedź po czyszczeniu z: '{original[:100]}...'")
        return "Cześć! Jak mogę ci pomóc? 😊"
    
    return cleaned

# ==============================================
# GŁÓWNA FUNKCJA - TYLKO TA JEDNA JEST UŻYWANA
# ==============================================

def process_user_message_smart(user_message, user_id):
    """INTELIGENTNY SYSTEM - TYLKO AI Z PAMIĘCIĄ + KALENDARZ + DATA"""
    
    # 🔧 OBSŁUGA PUSTYCH WIADOMOŚCI:
    if not user_message or not user_message.strip():
        return "Cześć! Jak mogę ci pomóc? 😊"
    
    # Pobierz historię
    history = get_user_history(user_id)
    add_to_history(user_id, "user", user_message)
    
    # 🔧 POBIERZ AKTUALNĄ DATĘ Z OSOBNEJ FUNKCJI
    current_date_info = get_current_date_info()
    
    # ZAAWANSOWANY SYSTEM PROMPT Z DATĄ
    system_prompt = f"""Jesteś asystentem salonu fryzjerskiego "Kleopatra".

{current_date_info}

🚨 KRYTYCZNE ZASADY:
- NIE używaj tagów <think>, <thinking> ani nie pokazuj procesu myślowego!
- NIE odpowiadaj BOOKING, CONTACT_DATA, itp. - to są kategorie wewnętrzne!
- Odpowiadaj ZAWSZE pełnymi zdaniami po polsku!
- Bądź naturalny, pomocny i przyjazny!
- ZNASZ AKTUALNĄ DATĘ - używaj jej w odpowiedziach!

🔧 PROCES REZERWACJI - KROK PO KROKU (WAŻNE!):

KROK 1: Zbierz WSZYSTKIE informacje PRZED potwierdzeniem:
- Dzień i godzina
- Usługa (Strzyżenie/Farbowanie/Stylizacja)  
- Imię i nazwisko
- Telefon

KROK 2: DOPIERO gdy masz WSZYSTKIE dane, użyj formatu:
✅ REZERWACJA POTWIERDZONA: [imię] [nazwisko], [dzień] [godzina], [usługa], tel: [telefon]

NIGDY nie używaj tego formatu z pustymi placeholderami!

PRZYKŁADY POPRAWNEGO PROCESU:

👤 "jutro o 18"
🤖 "Super! Jutro czwartek o 18:00! Jaką usługę wybierasz? Mamy strzyżenie (80zł), farbowanie (150zł) lub stylizację (120zł). 😊"

👤 "strzyżenie"  
🤖 "Świetnie! Jutro czwartek 18:00 na strzyżenie. Teraz potrzebuję Twoich danych - imię, nazwisko i telefon. 📞"

👤 "Jan Kowalski 123456789"
🤖 "✅ REZERWACJA POTWIERDZONA: Jan Kowalski, czwartek 18:00, Strzyżenie, tel: 123456789

Dziękuję! Czekamy na Ciebie w salonie! 💇‍♂️"

BŁĘDNE PRZYKŁADY (NIE RÓB TEGO!):
❌ "✅ REZERWACJA POTWIERDZONA: [imię] [nazwisko], czwartek 18:00, [usługa], tel: [telefon]"
❌ Potwierdzanie bez wszystkich danych

FORMATY POTWIERDZENIA:

PRZY REZERWACJI - użyj DOKŁADNIE (tylko z prawdziwymi danymi):
✅ REZERWACJA POTWIERDZONA: [prawdziwe imię] [prawdziwe nazwisko], [dzień] [godzina], [prawdziwa usługa], tel: [prawdziwy telefon]

PRZY ANULOWANIU - użyj DOKŁADNIE:  
❌ ANULACJA POTWIERDZONA: [imię] [nazwisko], [dzień] [godzina], tel: [telefon]

PRZYKŁADY DOBRYCH ODPOWIEDZI Z DATĄ:

👤 "jaki mamy dzisiaj dzień?"
🤖 "Dzisiaj mamy {get_current_date_info().split('Dzisiaj: ')[1].split('\\n')[0].split(',')[0]}! 😊 Chcesz się umówić na wizytę?"

👤 "chcę się umówić na jutro"
🤖 "Jutro to {(datetime.now(pytz.timezone('Europe/Warsaw')) + timedelta(days=1)).strftime('%A').lower()}! Jaka godzina Ci odpowiada? 😊"

👤 "chcę się umówić"
🤖 "Jaki dzień i godzina Ci odpowiadają? 😊"

👤 "wtorek 15:00 strzyżenie"  
🤖 "Super! Wtorek 15:00 na strzyżenie brzmi świetnie! Teraz potrzebuję Twoich danych - imię, nazwisko i telefon. 📞"

👤 "Anna Kowalska 987654321"
🤖 "✅ REZERWACJA POTWIERDZONA: Anna Kowalska, wtorek 15:00, Strzyżenie, tel: 987654321

Dziękuję! Czekamy na Ciebie w salonie! 💇‍♀️"

TWOJE MOŻLIWOŚCI:
🗓️ REZERWACJE - umów klientów na wizyty (ale zbieraj WSZYSTKIE dane PRZED potwierdzeniem!)
❌ ANULOWANIA - anuluj istniejące wizyty  
📅 WOLNE TERMINY - sprawdź dostępne terminy (gdy klient pyta o wolne terminy, użyj: CHECK_AVAILABILITY)
ℹ️ INFORMACJE - godziny, usługi, ceny, aktualna data
💬 ROZMOWA - pamiętaj imiona, bądź miły

GODZINY: 9:00-18:00, poniedziałek-sobota
USŁUGI: Strzyżenie (80zł), Farbowanie (150zł), Stylizacja (120zł)

INSTRUKCJE DZIAŁANIA:

1️⃣ REZERWACJA (POPRAWNA KOLEJNOŚĆ):
a) Gdy klient chce wizytę, poproś o dzień i godzinę
b) Gdy masz dzień/godzinę, poproś o usługę  
c) Gdy masz usługę, poproś o imię, nazwisko, telefon
d) DOPIERO gdy masz WSZYSTKIE dane, potwierdź używając dokładnego formatu

2️⃣ ANULOWANIE:
- Gdy klient chce anulować, poproś o: imię, nazwisko, telefon, dzień i godzinę
- Potwierdź używając dokładnego formatu: 
  ❌ ANULACJA POTWIERDZONA: [imię] [nazwisko], [dzień] [godzina], tel: [telefon]
- ZAWSZE używaj tego formatu przy anulowaniu!

3️⃣ INFORMACJE O DACIE:
- Gdy pyta o datę/dzień - podaj aktualne informacje
- Używaj polskich nazw dni tygodnia
- Pomagaj w planowaniu wizyt względem dzisiejszej daty
- "jutro" = następny dzień po dzisiejszym
- "pojutrze" = drugi dzień po dzisiejszym

SPRAWDZANIE WOLNYCH TERMINÓW - WAŻNE!:
Gdy klient pyta o wolne terminy, dostępne godziny, terminy na konkretny dzień, MUSISZ użyć formatu:
CHECK_AVAILABILITY: [dzień] 

NIE WYMYŚLAJ TERMINÓW! ZAWSZE UŻYJ CHECK_AVAILABILITY!

PRZYKŁADY OBOWIĄZKOWE:
👤 "jakie macie wolne terminy na jutro?"
🤖 "CHECK_AVAILABILITY: jutro"

👤 "sprawdź wolne terminy na jutro"
🤖 "CHECK_AVAILABILITY: jutro"

👤 "czy macie wolne terminy na czwartek?"
🤖 "CHECK_AVAILABILITY: czwartek"

👤 "jakie godziny macie wolne dzisiaj?"
🤖 "CHECK_AVAILABILITY: dzisiaj"

👤 "chcę sprawdzić terminy na piątek"
🤖 "CHECK_AVAILABILITY: piątek"

👤 "kiedy macie wolne?"
🤖 "CHECK_AVAILABILITY: dzisiaj"

NIGDY NIE WYMYŚLAJ TERMINÓW TYPU "9:00, 10:00, 11:00"!
ZAWSZE użyj CHECK_AVAILABILITY i pozwól systemowi sprawdzić prawdziwe terminy!

Po użyciu CHECK_AVAILABILITY system automatycznie pokaże dostępne godziny z kalendarza Google.

4️⃣ POZOSTAŁE:
- Odpowiadaj naturalnie na pytania
- Używaj emoji
- Bądź pomocny

PAMIĘTAJ: 
- NIGDY nie potwierdzaj rezerwacji z pustymi placeholderami!
- Zbieraj WSZYSTKIE dane PRZED użyciem "✅ REZERWACJA POTWIERDZONA"
- Zawsze odpowiadaj pełnymi zdaniami!"""

    try:
        response = client.chat.completions.create(
            model="deepseek-ai/DeepSeek-R1-Distill-Llama-70B-free",
            messages=[{"role": "system", "content": system_prompt}] + history,
            max_tokens=700,
            temperature=0.7
        )
        
        bot_response = response.choices[0].message.content
        
        # 🔧 UŻYJ FUNKCJI clean_thinking_response_enhanced:
        cleaned_response = clean_thinking_response_enhanced(bot_response)
        
        # 🔧 DETEKCJA REZERWACJI I DODANIE DO KALENDARZA
        if "✅ REZERWACJA POTWIERDZONA:" in cleaned_response:
            try:
                # Wyciągnij dane z odpowiedzi AI
                pattern = r"✅ REZERWACJA POTWIERDZONA: ([^,]+), ([^,]+), ([^,]+), tel: (\d+)"
                match = re.search(pattern, cleaned_response)
                
                if match:
                    name = match.group(1).strip()
                    datetime_str = match.group(2).strip()  # np. "środa 17:00"
                    service = match.group(3).strip()
                    phone = match.group(4).strip()
                    
                    logger.info(f"📅 Parsowanie rezerwacji: {name}, {datetime_str}, {service}, {phone}")
                    
                    # 🔧 NOWA LOGIKA DAT - OBSŁUGA "DZISIAJ", "JUTRO", KONKRETNYCH DNI
                    tz = pytz.timezone('Europe/Warsaw')
                    now = datetime.now(tz)
                    
                    # Mapowanie dni na liczby
                    day_mapping = {
                        'poniedziałek': 0, 'wtorek': 1, 'środa': 2,
                        'czwartek': 3, 'piątek': 4, 'sobota': 5
                    }
                    
                    # Parsuj dzień i godzinę
                    parts = datetime_str.lower().split()
                    if len(parts) >= 2:
                        day_pl = parts[0]
                        time_str = parts[1]  # np. "17:00"
                        
                        # 🔧 OBSŁUGA RÓŻNYCH FORMATÓW DNI:
                        appointment_date = None
                        
                        if day_pl in ['dzisiaj', 'dziś']:
                            # DZISIAJ = ten sam dzień
                            appointment_date = now.date()
                            logger.info(f"📅 DZISIAJ: {appointment_date}")
                            
                        elif day_pl == 'jutro':
                            # JUTRO = następny dzień
                            appointment_date = (now + timedelta(days=1)).date()
                            logger.info(f"📅 JUTRO: {appointment_date}")
                            
                        elif day_pl in day_mapping:
                            # KONKRETNY DZIEŃ TYGODNIA
                            target_day = day_mapping[day_pl]
                            current_day = now.weekday()
                            
                            # Oblicz ile dni do przodu
                            if target_day > current_day:
                                # W tym tygodniu
                                days_ahead = target_day - current_day
                            elif target_day == current_day:
                                # Ten sam dzień - sprawdź godzinę
                                time_parts = time_str.split(':')
                                if len(time_parts) == 2:
                                    hour = int(time_parts[0])
                                    minute = int(time_parts[1])
                                    appointment_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
                                    
                                    if appointment_time > now:
                                        # Dzisiaj, ale w przyszłości
                                        days_ahead = 0
                                    else:
                                        # Dzisiaj, ale w przeszłości - następny tydzień
                                        days_ahead = 7
                                else:
                                    days_ahead = 7
                            else:
                                # Następny tydzień
                                days_ahead = 7 - (current_day - target_day)
                            
                            appointment_date = (now + timedelta(days=days_ahead)).date()
                            logger.info(f"📅 {day_pl.upper()}: {appointment_date} (za {days_ahead} dni)")
                        
                        if appointment_date:
                            # Parsuj godzinę
                            time_parts = time_str.split(':')
                            if len(time_parts) == 2:
                                hour = int(time_parts[0])
                                minute = int(time_parts[1])
                                
                                # Utwórz datetime wizyty
                                appointment_datetime = datetime.combine(
                                    appointment_date,
                                    datetime.min.time().replace(hour=hour, minute=minute)
                                )
                                appointment_datetime = tz.localize(appointment_datetime)
                                
                                logger.info(f"📅 FINALNA DATA WIZYTY: {appointment_datetime}")
                                
                                # 🔧 UŻYJ FUNKCJI create_appointment:
                                calendar_result = create_appointment(
                                    client_name=name,
                                    client_phone=phone,
                                    service_type=service,
                                    appointment_time=appointment_datetime
                                )
                                
                                if calendar_result:
                                    logger.info(f"📅 Dodano do kalendarza Google: {calendar_result}")
                                    # 🔧 DODAJ KONKRETNĄ DATĘ DO ODPOWIEDZI:
                                    date_display = appointment_datetime.strftime('%A, %d %B %Y o %H:%M')
                                    cleaned_response += f"\n\n📅 Wydarzenie dodane do kalendarza Google!"
                                    cleaned_response += f"\n🗓️ Data: {date_display}"
                                else:
                                    logger.error("❌ Błąd dodawania do kalendarza")
                                    cleaned_response += f"\n\n⚠️ Rezerwacja zapisana, problem z kalendarzem Google."
                            else:
                                logger.error(f"❌ Nieprawidłowy format czasu: {time_str}")
                        else:
                            logger.error(f"❌ Nie można określić daty dla: {day_pl}")
                    else:
                        logger.error(f"❌ Nieprawidłowy format daty: {datetime_str}")
                        
            except Exception as e:
                logger.error(f"❌ Błąd integracji kalendarza rezerwacji: {e}")
        
        # 🔧 DETEKCJA ANULOWANIA I USUNIĘCIE Z KALENDARZA
        elif "❌ ANULACJA POTWIERDZONA:" in cleaned_response:
            try:
                # Wyciągnij dane z odpowiedzi AI
                pattern = r"❌ ANULACJA POTWIERDZONA: ([^,]+), ([^,]+), tel: (\d+)"
                match = re.search(pattern, cleaned_response)
                
                if match:
                    name = match.group(1).strip()
                    datetime_str = match.group(2).strip()  # np. "środa 18:00"
                    phone = match.group(3).strip()
                    
                    logger.info(f"🗑️ Parsowanie anulacji: {name}, {datetime_str}, {phone}")
                    
                    # Parsuj dzień i godzinę
                    parts = datetime_str.lower().split()
                    if len(parts) >= 2:
                        day_pl = parts[0]
                        time_str = parts[1]  # np. "18:00"
                        
                        # Mapowanie na nazwy wymagane przez funkcję cancel_appointment
                        day_names_mapping = {
                            'poniedziałek': 'Poniedziałek',
                            'wtorek': 'Wtorek',
                            'środa': 'Środa', 
                            'czwartek': 'Czwartek',
                            'piątek': 'Piątek',
                            'sobota': 'Sobota'
                        }
                        
                        day_name = day_names_mapping.get(day_pl)
                        if day_name:
                            # 🔧 UŻYJ FUNKCJI cancel_appointment:
                            cancel_result = cancel_appointment(
                                client_name=name,
                                client_phone=phone,
                                appointment_day=day_name,  # 'Środa'
                                appointment_time=time_str  # '18:00'
                            )
                            
                            if cancel_result:
                                logger.info(f"🗑️ Usunięto z kalendarza Google: {cancel_result}")
                                cleaned_response += f"\n\n🗑️ Wydarzenie usunięte z kalendarza Google!"
                                cleaned_response += f"\n📅 Anulowano: {day_name} o {time_str}"
                            else:
                                logger.error("❌ Nie znaleziono wizyty do anulowania")
                                cleaned_response += f"\n\n⚠️ Nie znaleziono wizyty w kalendarzu Google."
                        else:
                            logger.error(f"❌ Nieznany dzień: {day_pl}")
                    else:
                        logger.error(f"❌ Nieprawidłowy format daty: {datetime_str}")
                        
            except Exception as e:
                logger.error(f"❌ Błąd integracji kalendarza anulacji: {e}")
        
        # 🔧 SPRAWDZANIE WOLNYCH TERMINÓW
        if "CHECK_AVAILABILITY:" in cleaned_response:
            try:
                # Wyciągnij dzień z odpowiedzi AI
                availability_match = re.search(r"CHECK_AVAILABILITY:\s*(.+)", cleaned_response)
                if availability_match:
                    requested_day = availability_match.group(1).strip()
                    logger.info(f"📅 Sprawdzanie terminów dla: {requested_day}")
                    
                    # Konwertuj względne dni na konkretne daty
                    tz = pytz.timezone('Europe/Warsaw')
                    now = datetime.now(tz)
                    
                    target_date = None
                    
                    if requested_day.lower() in ['dzisiaj', 'dziś']:
                        target_date = now.date()
                    elif requested_day.lower() == 'jutro':
                        target_date = (now + timedelta(days=1)).date()
                    elif requested_day.lower() in ['poniedziałek', 'wtorek', 'środa', 'czwartek', 'piątek', 'sobota']:
                        # Mapowanie dni
                        day_mapping = {
                            'poniedziałek': 0, 'wtorek': 1, 'środa': 2,
                            'czwartek': 3, 'piątek': 4, 'sobota': 5
                        }
                        target_day = day_mapping[requested_day.lower()]
                        current_day = now.weekday()
                        
                        if target_day > current_day:
                            days_ahead = target_day - current_day
                        elif target_day == current_day:
                            days_ahead = 0
                        else:
                            days_ahead = 7 - (current_day - target_day)
                        
                        target_date = (now + timedelta(days=days_ahead)).date()
                    
                    if target_date:
                        # 🔧 UŻYJ FUNKCJI get_available_slots:
                        available_slots = get_available_slots(target_date)
                        
                        if available_slots:
                            logger.info(f"📅 Znaleziono wolne terminy: {available_slots}")
                            
                            # Formatuj odpowiedź z wolnymi terminami
                            day_name = target_date.strftime('%A')
                            day_names = {
                                'Monday': 'poniedziałek', 'Tuesday': 'wtorek', 'Wednesday': 'środa',
                                'Thursday': 'czwartek', 'Friday': 'piątek', 'Saturday': 'sobota'
                            }
                            day_pl = day_names.get(day_name, day_name)
                            
                            slots_text = "\n".join([f"⏰ {slot}" for slot in available_slots])
                            
                            cleaned_response = f"📅 Wolne terminy na {day_pl} ({target_date.strftime('%d.%m.%Y')}):\n\n{slots_text}\n\n😊 Który termin Ci odpowiada?"
                        else:
                            logger.info(f"📅 Brak wolnych terminów na: {target_date}")
                            cleaned_response = f"😔 Niestety, nie mamy wolnych terminów na {requested_day}. Sprawdź inny dzień lub skontaktuj się z salonem."
                    else:
                        logger.error(f"❌ Nie można określić daty dla: {requested_day}")
                        cleaned_response = "Nie rozumiem którego dnia dotyczy pytanie. Możesz spytać o 'dzisiaj', 'jutro' lub konkretny dzień tygodnia? 😊"
                
                # Usuń CHECK_AVAILABILITY z odpowiedzi
                cleaned_response = re.sub(r"CHECK_AVAILABILITY:.*?\n?", "", cleaned_response, flags=re.IGNORECASE)
                
            except Exception as e:
                logger.error(f"❌ Błąd sprawdzania terminów: {e}")
                cleaned_response = "Przepraszam, wystąpił problem ze sprawdzaniem terminów. Spróbuj ponownie. 😊"
        
        # 🔧 WALIDACJA - SPRAWDŹ CZY BOT WYMYŚLA TERMINY
        if any(keyword in user_message.lower() for keyword in ['wolne terminy', 'dostępne', 'kiedy macie', 'jakie godziny', 'sprawdź terminy']):
            if "CHECK_AVAILABILITY:" not in cleaned_response:
                logger.warning(f"⚠️ Bot nie użył CHECK_AVAILABILITY dla: {user_message}")
                # Wymusz użycie CHECK_AVAILABILITY
                if 'jutro' in user_message.lower():
                    cleaned_response = "CHECK_AVAILABILITY: jutro"
                elif 'dzisiaj' in user_message.lower() or 'dziś' in user_message.lower():
                    cleaned_response = "CHECK_AVAILABILITY: dzisiaj"
                elif any(day in user_message.lower() for day in ['poniedziałek', 'wtorek', 'środa', 'czwartek', 'piątek', 'sobota']):
                    for day in ['poniedziałek', 'wtorek', 'środa', 'czwartek', 'piątek', 'sobota']:
                        if day in user_message.lower():
                            cleaned_response = f"CHECK_AVAILABILITY: {day}"
                            break
                else:
                    cleaned_response = "CHECK_AVAILABILITY: dzisiaj"
        
        # Potem dodaj do historii już oczyszczoną wersję
        add_to_history(user_id, "assistant", cleaned_response)
        
        logger.info(f"🧠 AI Smart: '{user_message}' → '{cleaned_response[:50]}...'")
        return cleaned_response
        
    except Exception as e:
        logger.error(f"❌ Błąd AI Smart: {e}")
        return "Przepraszam, wystąpił błąd. Spróbuj ponownie."

# ==============================================
# STATYSTYKI UŻYTKOWNIKÓW
# ==============================================

def get_user_stats():
    """Statystyki użytkowników z pamięcią"""
    return {
        "total_conversations": len(user_conversations),
        "active_conversations": len([h for h in user_conversations.values() if len(h) > 0])
    }

logger.info("🤖 Bot Logic AI zainicjalizowany - UPROSZCZONA WERSJA")
logger.info(f"🔑 Together API: {'✅' if api_key else '❌'}")