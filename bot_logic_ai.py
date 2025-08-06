"""
Bot Logic AI - Uproszczona wersja z TYLKO używanymi funkcjami
"""

import logging
import re
from datetime import datetime, timedelta
import pytz
from together import Together
import os
from calendar_service import format_available_slots, create_appointment, cancel_appointment, verify_appointment_exists
from dotenv import load_dotenv

load_dotenv()

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
    logger.info(f"📝 Dodano do historii {role}: '{message[:50]}...' (historia: {len(history)} wiadomości)")
    
    # Ogranicz historię do ostatnich 20 wiadomości
    if len(history) > 20:
        user_conversations[user_id] = history[-20:]
        logger.info(f"📚 Skrócono historię do 20 wiadomości")

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
    return f"""📅 AKTUALNA DATY I CZAS:
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
    """Usuwa procesy myślowe i znajduje prawdziwą odpowiedź"""
    if not response_text:
        return ""
        
    original = response_text
    cleaned = response_text
    
    # 1. USUŃ THINKING BLOKI
    cleaned = re.sub(r'<think>.*?</think>', '', cleaned, flags=re.DOTALL | re.IGNORECASE)
    cleaned = re.sub(r'<thinking>.*?</thinking>', '', cleaned, flags=re.DOTALL | re.IGNORECASE)
    
    # 2. USUŃ NIEDOMKNIĘTE THINKING TAGI
    cleaned = re.sub(r'<think[^>]*>.*?$', '', cleaned, flags=re.DOTALL | re.IGNORECASE)
    cleaned = re.sub(r'<thinking[^>]*>.*?$', '', cleaned, flags=re.DOTALL | re.IGNORECASE)
    
    # 3. USUŃ WSZYSTKIE TAGI HTML
    cleaned = re.sub(r'<[^>]*>', '', cleaned)
    
    # 🔧 4. USUŃ PROCESY MYŚLOWE AI (AGRESYWNE REGUŁY):
    thinking_patterns = [
        r'Okay, I need to handle.*?(?=\n[A-ZĄĆĘŁŃÓŚŹŻ]|$)',
        r'First, I remember.*?(?=\n[A-ZĄĆĘŁŃÓŚŹŻ]|$)',
        r'The client wrote.*?(?=\n[A-ZĄĆĘŁŃÓŚŹŻ]|$)',
        r'I should start with.*?(?=\n[A-ZĄĆĘŁŃÓŚŹŻ]|$)',
        r'Then, on the next line.*?(?=\n[A-ZĄĆĘŁŃÓŚŹŻ]|$)',
        r'But wait, the system.*?(?=\n[A-ZĄĆĘŁŃÓŚŹŻ]|$)',
        r'So, the correct command.*?(?=\n[A-ZĄĆĘŁŃÓŚŹŻ]|$)',
        r'Putting it all together.*?(?=\n[A-ZĄĆĘŁŃÓŚŹŻ]|$)',
        r'That should correctly.*?(?=\n[A-ZĄĆĘŁŃÓŚŹŻ]|$)',
        r'which means.*?(?=\n[A-ZĄĆĘŁŃÓŚŹŻ]|$)',
        r'Since tomorrow is.*?(?=\n[A-ZĄĆĘŁŃÓŚŹŻ]|$)',
        r'my response will be.*?(?=\n[A-ZĄĆĘŁŃÓŚŹŻ]|$)',
        r'trigger the system.*?(?=\n[A-ZĄĆĘŁŃÓŚŹŻ]|$)',
        r'so earlier times.*?(?=\n[A-ZĄĆĘŁŃÓŚŹŻ]|$)',
        r'So, in this case.*?(?=\n[A-ZĄĆĘŁŃÓŚŹŻ]|$)',
        r'Wait, but the example.*?(?=\n[A-ZĄĆĘŁŃÓŚŹŻ]|$)',
        r'Therefore, I should.*?(?=\n[A-ZĄĆĘŁŃÓŚŹŻ]|$)',
        r'applying that logic.*?(?=\n[A-ZĄĆĘŁŃÓŚŹŻ]|$)',
        r'since it\'s \d+:\d+.*?(?=\n[A-ZĄĆĘŁŃÓŚŹŻ]|$)',
        r'Therefore, the available.*?(?=\n[A-ZĄĆĘŁŃÓŚŹŻ]|$)',
        r'would be from.*?(?=\n[A-ZĄĆĘŁŃÓŚŹŻ]|$)',
        r'as the next day.*?(?=\n[A-ZĄĆĘŁŃÓŚŹŻ]|$)',
        r'in 30-minute.*?(?=\n[A-ZĄĆĘŁŃÓŚŹŻ]|$)',
        r'but only the ones.*?(?=\n[A-ZĄĆĘŁŃÓŚŹŻ]|$)',
    ]
    
    for pattern in thinking_patterns:
        cleaned = re.sub(pattern, '', cleaned, flags=re.DOTALL | re.IGNORECASE)
    
    # 5. USUŃ LINIE ZACZYNAJĄCE SIĘ OD TYPOWYCH FRAZ AI
    thinking_lines = [
        r'^Okay, I need to.*$',
        r'^First, I remember.*$',
        r'^The client wrote.*$',
        r'^I should start.*$',
        r'^Then, on the next.*$',
        r'^But wait, the system.*$',
        r'^So, the correct.*$',
        r'^Putting it all.*$',
        r'^That should correctly.*$',
        r'^which means.*$',
        r'^Since tomorrow is.*$',
        r'^my response will be.*$',
        r'^trigger the system.*$',
        r'^s \d+:\d+.*$',
        r'^So, .*$',
        r'^Wait, .*$',
        r'^Therefore, .*$',
        r'^Since .*$',
        r'^Looking at .*$',
        r'^Based on .*$',
        r'^Given that .*$',
        r'^This means .*$',
        r'^The logic .*$',
        r'^I need to .*$',
        r'^Let me .*$',
        r'^which is .*$',
        r'^from \d+:\d+ AM.*$',
        r'^would be:.*$',
        r'^as the next day.*$',
        r'^in 30-minute.*$',
        r'^but only the ones.*$',
    ]
    
    lines = cleaned.split('\n')
    filtered_lines = []
    
    for line in lines:
        skip_line = False
        for pattern in thinking_lines:
            if re.match(pattern, line.strip(), re.IGNORECASE):
                skip_line = True
                break
        if not skip_line:
            filtered_lines.append(line)
    
    cleaned = '\n'.join(filtered_lines)
    
    # 6. USUŃ TYPOWE AI INTRO PHRASES (TYLKO NA POCZĄTKU)
    intro_phrases = [
        r'^okay,?\s+so.*?[.!]\s*',
        r'^let\s+me\s+go\s+through.*?[.!]\s*',
        r'^i\s+need\s+to\s+analyze.*?[.!]\s*',
        r'^looking\s+at\s+this\s+message.*?[.!]\s*'
    ]
    
    for phrase in intro_phrases:
        cleaned = re.sub(phrase, '', cleaned, flags=re.IGNORECASE)
    
    # 7. USUŃ POJEDYNCZE KATEGORIE AI
    single_word_categories = ["CONTACT_DATA", "BOOKING", "ASK_AVAILABILITY", "WANT_APPOINTMENT", "CANCEL_VISIT", "OTHER_QUESTION"]
    
    cleaned_stripped = cleaned.strip()
    if cleaned_stripped in single_word_categories:
        logger.warning(f"⚠️ AI zwróciło tylko kategorię: {cleaned_stripped}")
        return "Cześć! Jak mogę ci pomóc? 😊"
    
    # 8. USUŃ KATEGORIE TYLKO Z POCZĄTKU/KOŃCA LINII
    for category in single_word_categories:
        cleaned = re.sub(rf'^{category}[\s\.\-]*', '', cleaned, flags=re.IGNORECASE | re.MULTILINE)
        cleaned = re.sub(rf'[\s\.\-]*{category}$', '', cleaned, flags=re.IGNORECASE | re.MULTILINE)
    
    # 9. WYCZYŚĆ PUSTE LINIE I BIAŁE ZNAKI
    cleaned = '\n'.join(line.strip() for line in cleaned.split('\n') if line.strip())
    cleaned = cleaned.strip()
    
    # 10. USUŃ TYLKO IDENTYCZNE POWTÓRZENIA CAŁYCH BLOKÓW
    # Nie usuwaj normalnych linii - tylko rzeczywiste duplikaty
    
    # 12. LIMIT ODPOWIEDZI (max 500 znaków dla Facebook)
    if len(cleaned) > 500:
        logger.warning(f"⚠️ Skracam długą odpowiedź z {len(cleaned)} do 500 znaków")
        cleaned = cleaned[:500] + "..."
    
    # 13. BLOKADA POWTARZAJĄCYCH SIĘ SEPARATORÓW (KRYTYCZNE!)
    if '---' in cleaned:
        logger.warning(f"⚠️ USUWAM WSZYSTKIE SEPARATORY - biorę tylko pierwszą część")
        parts = cleaned.split('---')
        cleaned = parts[0].strip()  # TYLKO pierwsza część przed pierwszym ---
    
    # 14. JEŚLI PO CZYSZCZENIU NICZEGO NIE MA, ZWRÓĆ DOMYŚLNĄ ODPOWIEDŹ
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
- ⚠️ SPRAWDZAJ GODZINY OTWARCIA: Salon zamyka o 16:00 w sobotę, o 19:00 w dni robocze!
- ⚠️ JEŚLI JEST PO GODZINACH - nie oferuj wizyt na "dzisiaj"!
- ⚠️ NIE PISZ "Dzień dobry!" w środku rozmowy - kontynuuj naturalnie!
- ⚠️ SPRAWDZAJ HISTORIĘ - jeśli rozmowa trwa, nie zaczynaj od nowa!
- ⚠️ PAMIĘTAJ KONTEKST - jeśli klient już mówił o rezerwacji, kontynuuj proces!
- ⚠️ NIE RESETUJ rozmowy - jeśli klient podał dzień, przejdź do godziny!

🚫 ABSOLUTNIE ZAKAZANE:
- NIGDY nie pisz "[imię i nazwisko]", "[telefon]" lub podobnych placeholderów!
- NIGDY nie rób rezerwacji bez imienia i telefonu klienta!
- NIGDY nie pisz "Wydarzenie dodane do kalendarza", "Dziękuję! Czekamy", "Data:" - system doda to automatycznie!
- NIGDY nie używaj przykładowych danych zamiast prawdziwych!
- ❌ NIGDY nie pisz "Potwierdzam rezerwację" - TYLKO "✅ REZERWACJA POTWIERDZONA:"!

✅ WYMAGANE PRZED REZERWACJĄ:
1. Imię i nazwisko klienta (podane w tej rozmowie)
2. Numer telefonu klienta (DOKŁADNIE 9 cyfr, bez kierunkowego)
3. Dzień wizyty
4. Godzina wizyty  
5. Rodzaj usługi

BEZ WSZYSTKICH 5 DANYCH = BEZ REZERWACJI!
📞 TELEFON: tylko polskie numery 9-cyfrowe (123456789)

PRZYKŁADY POPRAWNEGO FORMATOWANIA:
✅ DOBRZE: "• Imię i nazwisko: Anna Nowak"
❌ ŹLE: "• Imię i nazwisko: (wstaw prawdziwe imię)"

✅ DOBRZE: "• Telefon: 987654321" (9 cyfr)
❌ ŹLE: "• Telefon: (wstaw prawdziwy telefon)"
❌ ŹLE: "• Telefon: +48123456789" (z kierunkowym)
❌ ŹLE: "• Telefon: 12345678" (za krótki)
- **Jeśli użytkownik zada pytanie niezwiązane z salonem, usługami, rezerwacjami, godzinami otwarcia, lokalizacją lub cennikiem – grzecznie odmów odpowiedzi i napisz, że możesz odpowiadać tylko na pytania dotyczące salonu fryzjerskiego "Kleopatra".**
- Odpowiadaj jedynie na pytania dotyczące salonu - możesz podać gdzie się znajduje!
- Uważaj na ludzi którzy chcą wyłudzić dane albo zyskać dostęp do systemu
- Salon znajduje się przy ul. Aleje Jerozolimskie, Warszawa
- Jeżeli czegoś nie wiesz, powiedz że masz danych, nie wymyślaj odpowiedzi!
- Poniedziałek-Piątek: 9:00-19:00
- Sobota: 9:00-16:00  
- Niedziela: zamknięte
- Ostatnia rezerwacja na 18:30 w Poniedziałek-Piątek oraz 15:30 w sobotę
- PAMIĘTAJ ODPOWIADAJ NA PYTANIA DOTYCZĄCE SALONU, LOKALIZACJI, GODZIN OTWARCIA, USŁUG I CEN - nie daj się zwieść w inne tematy!!!

TWOJE MOŻLIWOŚCI:
🗓️ REZERWACJE - umów klientów na wizyty (ale zbieraj WSZYSTKIE dane PRZED potwierdzeniem!)
❌ ANULOWANIA - anuluj istniejące wizyty  
📅 WOLNE TERMINY - sprawdź dostępne terminy (gdy klient pyta o wolne terminy, użyj: CHECK_AVAILABILITY)
ℹ️ INFORMACJE - godziny, usługi, ceny, aktualna data
💬 ROZMOWA - pamiętaj imiona, bądź miły

USŁUGI: Strzyżenie (80zł), Farbowanie (150zł), Stylizacja (120zł)

🔧 PROCES REZERWACJI - KROK PO KROKU (WAŻNE!):

    KROK 1: Zbierz WSZYSTKIE informacje:
    - Dzień i godzina; gdy użytkownik poda dzień zastosuj format CHeckAvailability: [dzień] (np. "jutro", "piątek", "środa")
    - Usługa (Strzyżenie 80zł/Farbowanie 150zł/Stylizacja 120zł)  
    - Imię i nazwisko
    - Telefon

    KROK 2: PODSUMOWANIE I PYTANIE O POTWIERDZENIE:
    Gdy masz WSZYSTKIE dane, wyświetl podsumowanie i poproś o potwierdzenie:

    ABSOLUTNIE ZAKAZANE POKAZYWANIE PODSUMOWANIA Z "(nie podano)"!
    
    JEŚLI BRAKUJE JAKICHKOLWIEK DANYCH - POPROŚ O NIE!
    
    NIGDY nie pisz:
    • Imię i nazwisko: (nie podano)
    • Data i godzina: (nie podano)
    • Usługa: (nie podano)
    
    ZAMIAST TEGO napisz:
    "Potrzebuję jeszcze Twoje imię i nazwisko oraz dzień i godzinę wizyty. Podaj te dane proszę."

    Czy wszystkie dane są poprawne? Napisz 'TAK' aby potwierdzić rezerwację lub popraw dane.

    KROK 3: FINALNE POTWIERDZENIE:
    DOPIERO gdy użytkownik napisze "TAK", "POTWIERDZAM", "OK":
    
    🔍 NAJPIERW SPRAWDŹ CZY MASZ WSZYSTKIE DANE:
    ✅ Imię i nazwisko klienta (z tej rozmowy)
    ✅ Dzień i godzina wizyty (z tej rozmowy)  
    ✅ Usługa (z tej rozmowy)
    ✅ Telefon klienta (z tej rozmowy)
    
    JEŚLI MASZ WSZYSTKIE DANE - użyj DOKŁADNIE tego formatu:
    
    📅 Rezerwuję wizytę w kalendarzu...
    
    ZAWSZE UŻYWAJ DOKŁADNIE TEGO FORMATU:
    
    ✅ REZERWACJA POTWIERDZONA: [imię nazwisko], [dzień] [godzina], [usługa], tel: [telefon]
    
    PRZYKŁAD: ✅ REZERWACJA POTWIERDZONA: Anna Kowalska, poniedziałek 09:00, Strzyżenie, tel: 123456789
    
    ⚠️ NIGDY nie pisz "Potwierdzam rezerwację" - TYLKO powyższy format!
    
    JEŚLI BRAKUJE JAKICHKOLWIEK DANYCH - poproś o nie ponownie!
    
    ⚠️ WAŻNE: SPRAWDŹ HISTORIĘ KONWERSACJI i użyj danych podanych przez TEGO klienta!


    PRZYKŁADY POPRAWNEGO PROCESU - ALE NIGDY NIE BIERZ TYCH DANYCH DO REALNEJ REZERWACJI - TO TYLKO PRZYKŁAD:

    👤 "jutro o 18"
    🤖 "Super! Jutro czwartek o 18:00! Jaką usługę wybierasz? Mamy strzyżenie (80zł), farbowanie (150zł) lub stylizację (120zł). 😊"

    👤 "strzyżenie"  
    🤖 "Świetnie! Jutro czwartek 18:00 na strzyżenie. Teraz potrzebuję Twoich danych - imię, nazwisko i telefon. 📞"

    👤 "Anna Nowak 987654321"
    🤖 "📋 PODSUMOWANIE REZERWACJI:
    • Imię i nazwisko: Anna Nowak
    • Data i godzina: czwartek 18:00  
    • Usługa: Strzyżenie (80zł)
    • Telefon: 987654321

    Czy wszystkie dane są poprawne? Napisz 'TAK' aby potwierdzić rezerwację lub popraw dane."

    👤 "TAK"
    🤖 "📅 Rezerwuję wizytę w kalendarzu...
    
    ✅ REZERWACJA POTWIERDZONA: Jan Kowalski, czwartek 18:00, Strzyżenie, tel: 123456789"

    BŁĘDNE PRZYKŁADY (NIE RÓB TEGO!):
    ❌ "✅ REZERWACJA POTWIERDZONA" bez wcześniejszego podsumowania
    ❌ Pomijanie pytania o potwierdzenie
    ❌ Potwierdzanie bez zgody użytkownika

   
    SPRAWDZANIE WOLNYCH TERMINÓW - WAŻNE!:
    Gdy klient pyta o wolne terminy, dostępne godziny, terminy na konkretny dzień, MUSISZ:

    1. Odpowiedzieć naturalnie: "Sprawdzam dostępne terminy na [dzień]..."
    2. Następnie w OSOBNEJ LINII dodać komendę: CHECK_AVAILABILITY:[dzień]
    3. Zwróc jedynie dwie linie tekstu jak powyzez, "Sprawdzam dostępne terminy na [dzień]..." oraz CHECK_AVAILABILITY:[dzień. Nic więcej. 

    PRZYKŁADY OBOWIĄZKOWE:
    👤 "jakie macie wolne terminy na jutro?"
    🤖 "Sprawdzam dostępne terminy na jutro... 😊
    CHECK_AVAILABILITY:jutro"

    👤 "wolne terminy na piątek?"
    🤖 "Sprawdzam wolne terminy na piątek!
    CHECK_AVAILABILITY:piątek"

    👤 "sprawdź terminy na dzisiaj"
    🤖 "Sprawdzam terminy na dzisiaj...
    CHECK_AVAILABILITY:dzisiaj"

    👤 "masz coś wolnego na sobotę?"
    🤖 "Sprawdzam dostępność na sobotę! 😊
    CHECK_AVAILABILITY:sobota"

    -------------------------------------------------
    FORMAT: 
    Linia 1: Naturalna odpowiedź
    Linia 2: CHECK_AVAILABILITY:[dzień]
    Linia 3: Pusta nic więcej nie dodajesz od siebie!
    -------------------------------------------------

    NIGDY NIE WYMYŚLAJ TERMINÓW TYPU "9:00, 10:00, 11:00"!
    ZAWSZE używaj CHECK_AVAILABILITY gdy klient pyta o wolne terminy!

    PRZYKŁADOWY FLOW REZERWACJI:
    🧍 Klient: Dzień dobry
    🤖 Chatbot (Salon Fryzjerski "Kleopatra"): Dzień dobry! 🌞 Jak mogę pomóc? Czy chodzi o rezerwację, informacje o salonie czy coś innego?
    🧍 Klient: Chcę dokonać rezerwacji
    🤖 Chatbot: Super! 🎉 Chętnie pomogę Ci umówić wizytę. Na jaki dzień chcesz się umówić? 😊
    🧍 Klient: Na poniedziałek
    🤖 Chatbot: Sprawdzam dostępne terminy na poniedziałek... 😊 (Używasz tutaj CHECK_AVAILABILITY). 
       CHECK_AVAILABILITY:poniedziałek
    Który z tych terminów Ci najbardziej odpowiada? 😊
    🧍 Klient: O 17:30
    🤖 Chatbot: Świetnie! W poniedziałek o 17:30 jest dostępne. Jaką usługę wybierasz?
    Mamy do wyboru:
    🪒 Strzyżenie (80zł)
    🎨 Farbowanie (150zł)
    💇 Stylizację (120zł)
    Odpowiedz numerem usługi lub jej nazwą. 😊
    🧍 Klient: 1
    🤖 Chatbot: Świetnie! W poniedziałek o 17:30 mamy strzyżenie (80zł).
    Teraz potrzebuję Twoich danych – imię, nazwisko i telefon. 📞
    🧍 Klient: Tomek Gawron 123123123
    🤖 Chatbot:
    📋 PODSUMOWANIE REZERWACJI:
    • Imię i nazwisko: Tomek Gawron
    • Data i godzina: poniedziałek 17:30
    • Usługa: Strzyżenie (80zł)
    • Telefon: 123123123
    Czy wszystkie dane są poprawne?
    Napisz „TAK” aby potwierdzić rezerwację lub popraw dane. 😊
    🧍 Klient: Tak
    🤖 Chatbot:
    ✅ REZERWACJA POTWIERDZONA:
    Tomek Gawron, poniedziałek 17:30, Strzyżenie, tel: 123123123
    
    ⚠️ NIGDY nie dodawaj informacji o kalendarzu - system to zrobi automatycznie!

    ⏰ WAŻNE - GODZINY REZERWACJI:
    - DOZWOLONE GODZINY: TYLKO pełne godziny (9:00, 10:00, 11:00, 12:00, 13:00, 14:00, 15:00, 16:00, 17:00, 18:00) 
    - DOZWOLONE GODZINY: ORAZ w pół do (9:30, 10:30, 11:30, 12:30, 13:30, 14:30, 15:30, 16:30, 17:30)
    - NIEDOZWOLONE: 9:15, 9:45, 10:15, 10:45 i wszystkie inne minuty!
    - Jeśli klient poda niedozwoloną godzinę, zaproponuj najbliższą dozwoloną

    PRZYKŁADY POPRAWEK GODZIN:
    👤 "jutro o 17:15"
    🤖 "Umawiamy wizyty na pełne godziny lub w pół do. Czy pasuje Ci 17:00 lub 17:30?"

    👤 "piątek o 14:45"  
    🤖 "Dostępne godziny to 14:30 lub 15:00. Która bardziej Ci odpowiada?"

    👤 "środa o 16:20"
    🤖 "Możemy umówić Cię na 16:00 lub 16:30. Co wybierasz?"

🔧 PROCES ANULOWANIA - KROK PO KROKU:

    KROK 1: Zbierz dane o anulacji:
    - Imię i nazwisko
    - Dzień i godzina wizyty do anulowania
    - Telefon

    KROK 2: PODSUMOWANIE I PYTANIE O POTWIERDZENIE:
    🗑️ PODSUMOWANIE ANULACJI:
    • Imię i nazwisko: (wstaw prawdziwe imię i nazwisko)
    • Data i godzina do anulowania: (wstaw prawdziwy dzień i godzinę)
    • Telefon: (wstaw prawdziwy telefon)

    Czy na pewno chcesz anulować tę wizytę? Napisz 'TAK' aby potwierdzić anulację.

    KROK 3: FINALNE POTWIERDZENIE ANULACJI:
    DOPIERO gdy użytkownik napisze "TAK", "POTWIERDZAM", "ANULUJ", użyj formatu:
    ❌ ANULACJA POTWIERDZONA: (wstaw prawdziwe dane w formacie: Imię Nazwisko, dzień godzina, tel: telefon)

    ROZPOZNAWANIE POTWIERDZEŃ:
    ZGODĘ: "TAK", "POTWIERDZAM", "OK", "ZGADZA SIĘ", "DOBRZE", "ANULUJ" (przy anulacji)
    ODMOWĘ: "NIE", "POPRAW", "ZMIEŃ", "BŁĄD" lub podanie nowych danych

    ZASADY POTWIERDZANIA:
    - ZAWSZE pytaj o potwierdzenie przed finalną akcją
    - NIGDY nie używaj "✅ REZERWACJA POTWIERDZONA" bez wcześniejszego podsumowania
    - NIGDY nie używaj "❌ ANULACJA POTWIERDZONA" bez wcześniejszego podsumowania
    - Czekaj na zgodę użytkownika
    - Pozwól na poprawki przed potwierdzeniem


INSTRUKCJE DZIAŁANIA:

2️⃣ ANULOWANIE:
- Gdy klient chce anulować, poproś o: imię, nazwisko, telefon, dzień i godzinę
- Potwierdź używając dokładnego formatu z PRAWDZIWYMI danymi klienta
- ZAWSZE używaj rzeczywistych danych, NIE placeholderów!

3️⃣ INFORMACJE O DACIE:
- Gdy pyta o datę/dzień - podaj aktualne informacje
- Używaj polskich nazw dni tygodnia
- Pomagaj w planowaniu wizyt względem dzisiejszej daty
- "jutro" = następny dzień po dzisiejszym
- "pojutrze" = drugi dzień po dzisiejszym

SPRAWDZANIE WOLNYCH TERMINÓW - WAŻNE!:
    Gdy klient pyta o wolne terminy, dostępne godziny, terminy na konkretny dzień, MUSISZ:

    1. Odpowiedzieć naturalnie: "Sprawdzam dostępne terminy na [dzień]..."
    2. Następnie w OSOBNEJ LINII dodać komendę: CHECK_AVAILABILITY:[dzień]
    3. Zwróc jedynie dwie linie tekstu jak powyzez, "Sprawdzam dostępne terminy na [dzień]..." oraz CHECK_AVAILABILITY:[dzień. Nic więcej. 

    PRZYKŁADY OBOWIĄZKOWE:
    👤 "jakie macie wolne terminy na jutro?"
    🤖 "Sprawdzam dostępne terminy na jutro... 😊
    CHECK_AVAILABILITY:jutro"

    👤 "wolne terminy na piątek?"
    🤖 "Sprawdzam wolne terminy na piątek!
    CHECK_AVAILABILITY:piątek"

    👤 "sprawdź terminy na dzisiaj"
    🤖 "Sprawdzam terminy na dzisiaj...
    CHECK_AVAILABILITY:dzisiaj"

    👤 "masz coś wolnego na sobotę?"
    🤖 "Sprawdzam dostępność na sobotę! 😊
    CHECK_AVAILABILITY:sobota"

    -------------------------------------------------
    FORMAT: 
    Linia 1: Naturalna odpowiedź
    Linia 2: CHECK_AVAILABILITY:[dzień]
    Linia 3: Pusta nic więcej nie dodajesz od siebie!
    -------------------------------------------------

    NIGDY NIE WYMYŚLAJ TERMINÓW TYPU "9:00, 10:00, 11:00"!
    ZAWSZE używaj CHECK_AVAILABILITY gdy klient pyta o wolne terminy!
    
4️⃣ POZOSTAŁE:
- Odpowiadaj naturalnie na pytania
- Używaj emoji
- Bądź pomocny

PAMIĘTAJ: 
- NIGDY nie potwierdzaj rezerwacji z pustymi placeholderami!
- Zbieraj WSZYSTKIE dane PRZED użyciem "✅ REZERWACJA POTWIERDZONA"
- Zawsze odpowiadaj pełnymi zdaniami!

🔍 CHECKLIST PRZED REZERWACJĄ:
1. ✅ Czy mam imię i nazwisko klienta?
2. ✅ Czy mam numer telefonu klienta (9 cyfr)?
3. ✅ Czy mam dzień wizyty?
4. ✅ Czy mam godzinę wizyty?
5. ✅ Czy mam rodzaj usługi?

TYLKO jeśli wszystkie 5 punktów są ✅ - rób rezerwację!
JEŚLI którykolwiek jest ❌ - poproś o brakujące dane!
📞 TELEFON: sprawdź czy ma dokładnie 9 cyfr!"""

    try:
        response = client.chat.completions.create(
            model="deepseek-ai/DeepSeek-R1-Distill-Llama-70B-free",
            messages=[{"role": "system", "content": system_prompt}] + history,
            max_tokens=700,
            temperature=0.2
        )
        
        bot_response = response.choices[0].message.content
        logger.info(f"🟡 RAW AI RESPONSE: {bot_response[:1500]}")
        bot_response_original = bot_response
        cleaned_response = clean_thinking_response_enhanced(bot_response)
        
        # 🔧 SPRAWDŹ CZY AI CHCE SPRAWDZIĆ DOSTĘPNOŚĆ:
        if "CHECK_AVAILABILITY:" in bot_response_original:
            try:
                # Wyciągnij dzień z oryginalnej odpowiedzi AI
                day_match = re.search(r'CHECK_AVAILABILITY:(\w+)', bot_response_original)
                if day_match:
                    day = day_match.group(1).strip()
                    logger.info(f"📅 AI prosi o sprawdzenie terminów na: {day}")
                    
                    # Wywołaj funkcję kalendarza
                    availability_result = format_available_slots(day)
                    
                    # 🔧 USUŃ KOMENDĘ Z OCZYSZCZONEJ ODPOWIEDZI (jeśli nadal tam jest):
                    natural_response = re.sub(r'CHECK_AVAILABILITY:\w+', '', cleaned_response).strip()
                    
                    # Jeśli zostało coś z naturalnej odpowiedzi, użyj tego + wynik
                    if natural_response and len(natural_response) > 10:
                        cleaned_response = f"{natural_response}\n\n{availability_result}"
                    else:
                        # Tylko wynik kalendarza
                        cleaned_response = availability_result
                    
                else:
                    logger.error("❌ Nie znaleziono dnia w CHECK_AVAILABILITY")
                    
            except Exception as e:
                logger.error(f"❌ Błąd przetwarzania CHECK_AVAILABILITY: {e}")
        
        # cleaned_response jest już oczyszczone w obu przypadkach!
        
        # 🔧 BLOKADA BŁĘDNYCH REZERWACJI I PODSUMOWAŃ
        if "📋 PODSUMOWANIE REZERWACJI:" in cleaned_response:
            # Sprawdź czy nie ma "(nie podano)" - TYLKO jeśli rzeczywiście brakuje danych
            if "(nie podano)" in cleaned_response:
                logger.error("❌ BLOKADA: Podsumowanie z brakującymi danymi!")
                return "Potrzebuję jeszcze kilku informacji aby dokończyć rezerwację:\n\n• Twoje imię i nazwisko\n• Dzień wizyty (np. poniedziałek, wtorek)\n• Godzina wizyty (np. 10:00, 15:30)\n• Rodzaj usługi (strzyżenie, farbowanie, stylizacja)\n\nPodaj te dane proszę. 😊"
            
            # BLOKADA PRZYKŁADOWYCH DANYCH!
            if "Jan Kowalski" in cleaned_response or "123456789" in cleaned_response:
                logger.error("❌ BLOKADA: Bot używa przykładowych danych!")
                return "Potrzebuję Twoich prawdziwych danych kontaktowych:\n\n📞 Podaj swoje imię, nazwisko i numer telefonu\n\nPrzykład: Anna Nowak 987654321"
        
        # 🔧 BLOKADA NIEPOTRZEBNYCH PRÓŚB O DANE
        if "Potrzebuję jeszcze kilku informacji" in cleaned_response and "📋 PODSUMOWANIE REZERWACJI:" not in cleaned_response:
            logger.error("❌ BLOKADA: Niepotrzebna prośba o dane!")
            return "Przepraszam za zamieszanie. Spróbujmy ponownie - podaj swoje imię, nazwisko i telefon. 😊"
        
        # 🔧 BLOKADA BŁĘDNYCH KOMUNIKATÓW O BŁĘDZIE
        if "wystąpił błąd podczas przetwarzania" in cleaned_response:
            logger.error("❌ BLOKADA: Niepotrzebny komunikat błędu!")
            return "Sprawdzam Twoją rezerwację... Moment proszę. 😊"
        
        # 🔧 BLOKADA BŁĘDNYCH FORMATÓW POTWIERDZENIA
        if "Potwierdzam rezerwację" in cleaned_response or "Wszystkie dane są poprawne" in cleaned_response:
            logger.error("❌ BLOKADA: Błędny format potwierdzenia!")
            return "❌ Błąd systemu rezerwacji.\n\nAby dokończyć rezerwację, użyj dokładnego formatu:\n✅ REZERWACJA POTWIERDZONA: [imię nazwisko], [dzień godzina], [usługa], tel: [telefon]\n\nSpróbuj ponownie."
        
        if "✅ REZERWACJA POTWIERDZONA:" in cleaned_response:
            # Sprawdź czy nie ma placeholderów
            if "[imię" in cleaned_response or "[telefon" in cleaned_response or "[nazwisko" in cleaned_response:
                logger.error("❌ BLOKADA: Rezerwacja z placeholderami!")
                return "❌ Błąd systemu rezerwacji. Proszę podać swoje dane kontaktowe (imię, nazwisko, telefon) aby dokończyć rezerwację."
            
            # Sprawdź poprawność numeru telefonu (9 cyfr)
            phone_match = re.search(r'tel: (\d+)', cleaned_response)
            if phone_match:
                phone = phone_match.group(1)
                logger.info(f"🔍 Znaleziono telefon: '{phone}' (długość: {len(phone)})")
                if len(phone) != 9:
                    logger.error(f"❌ BLOKADA: Nieprawidłowy numer telefonu: {phone} (długość: {len(phone)})")
                    return f"❌ Nieprawidłowy numer telefonu: {phone}\n\n📞 Numer telefonu musi mieć dokładnie 9 cyfr (bez kierunkowego).\nPrzykład: 123456789\n\nPodaj poprawny numer telefonu."
                else:
                    logger.info(f"✅ Telefon OK: {phone} (9 cyfr)")
            else:
                logger.warning(f"⚠️ Nie znaleziono telefonu w: '{cleaned_response[:100]}...'")
            
            # Sprawdź czy nie ma fałszywych komunikatów o kalendarzu
            if "Wydarzenie dodane" in cleaned_response or "Dziękuję! Czekamy" in cleaned_response:
                logger.error("❌ BLOKADA: Fałszywy komunikat o kalendarzu!")
                # Usuń fałszywe komunikaty
                cleaned_response = re.sub(r'📅 Wydarzenie dodane.*?\n?', '', cleaned_response)
                cleaned_response = re.sub(r'Dziękuję! Czekamy.*?\n?', '', cleaned_response)
                cleaned_response = re.sub(r'🗓️ Data:.*?\n?', '', cleaned_response)
        
        # 🔧 DETEKCJA REZERWACJI I DODANIE DO KALENDARZA
        if "✅ REZERWACJA POTWIERDZONA:" in cleaned_response:
            try:
                # Wyciągnij dane z odpowiedzi AI
                pattern = r"✅ REZERWACJA POTWIERDZONA:\s*\n?\s*([^,]+), ([^,]+), ([^,]+), tel: (\d+)"
                
                # Sprawdź czy użytkownik potwierdza (TAK, Ta, OK, etc.)
                if user_message.lower().strip() in ['tak', 'ta', 'ok', 'potwierdzam', 'zgadza się']:
                    logger.info(f"🔍 Użytkownik potwierdza: '{user_message}' - szukam danych do rezerwacji")
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
                            # SPRAWDŹ CZY SALON JEST JESZCZE OTWARTY
                            if now.weekday() == 5:  # Sobota
                                if now.hour >= 16:  # Po 16:00 w sobotę
                                    logger.warning(f"⚠️ DZISIAJ po godzinach (sobota {now.hour}:00) - salon zamknięty")
                                    return "❌ Salon jest już zamknięty (sobota do 16:00). Możesz umówić się na poniedziałek lub inny dzień. 😊"
                            elif now.weekday() < 5:  # Dni robocze
                                if now.hour >= 19:  # Po 19:00 w dni robocze
                                    logger.warning(f"⚠️ DZISIAJ po godzinach ({now.hour}:00) - salon zamknięty")
                                    return "❌ Salon jest już zamknięty (dni robocze do 19:00). Możesz umówić się na jutro. 😊"
                            
                            # DZISIAJ = ten sam dzień (jeśli salon otwarty)
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
                                
                                # 🔧 WERYFIKACJA CZY SPOTKANIE RZECZYWIŚCIE ZOSTAŁO ZAPISANE
                                if calendar_result:
                                    logger.info(f"📅 Próba dodania do kalendarza: {calendar_result}")
                                    
                                    # Poczekaj chwilę na synchronizację
                                    import time
                                    time.sleep(2)
                                    
                                    # Zweryfikuj czy spotkanie rzeczywiście istnieje
                                    verification = verify_appointment_exists(
                                        client_name=name,
                                        client_phone=phone,
                                        appointment_datetime=appointment_datetime,
                                        service_type=service
                                    )
                                    
                                    if verification:
                                        logger.info(f"✅ Spotkanie zweryfikowane w kalendarzu: {verification['event_id']}")
                                        date_display = appointment_datetime.strftime('%A, %d %B %Y o %H:%M')
                                        
                                        # Zastąp "Rezerwuję wizytę..." potwierdzeniem
                                        cleaned_response = cleaned_response.replace("📅 Rezerwuję wizytę w kalendarzu...", "")
                                        # Usuń starą treść i dodaj tylko weryfikację
                                        cleaned_response = cleaned_response.split('\n')[0]  # Tylko pierwsza linia
                                        cleaned_response += f"\n\n✅ Wizyta zapisana w kalendarzu!"
                                        cleaned_response += f"\n📅 Data: {date_display}"
                                        cleaned_response += f"\n🆔 ID wizyty: {verification['event_id'][:8]}..."
                                        cleaned_response += f"\n\n💇‍♂️ Dziękuję! Czekamy na Ciebie w salonie!"
                                    else:
                                        logger.error("❌ Spotkanie nie zostało zapisane w kalendarzu!")
                                        # Usuń "Rezerwuję wizytę..." i zastąp błędem
                                        cleaned_response = cleaned_response.replace("📅 Rezerwuję wizytę w kalendarzu...", "")
                                        cleaned_response = cleaned_response.replace("✅ REZERWACJA POTWIERDZONA:", "❌ BŁĄD REZERWACJI:")
                                        cleaned_response += f"\n\n⚠️ Przepraszam, wystąpił problem z zapisaniem wizyty w kalendarzu."
                                        cleaned_response += f"\n📞 Proszę zadzwoń bezpośrednio do salonu: 123-456-789"
                                else:
                                    logger.error("❌ Błąd dodawania do kalendarza")
                                    cleaned_response = cleaned_response.replace("✅ REZERWACJA POTWIERDZONA:", "❌ BŁĄD REZERWACJI:")
                                    cleaned_response += f"\n\n⚠️ Przepraszam, wystąpił problem z zapisaniem wizyty."
                                    cleaned_response += f"\n📞 Proszę zadzwoń bezpośrednio do salonu: 123-456-789"
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

if __name__ == "__main__":
    import pytz
    from datetime import datetime, timedelta

    print("=== TEST KALENDARZA GOOGLE ===")

    # Test 1: Sprawdź dostępne sloty na jutro
    print("\n[TEST] format_available_slots('jutro'):")
    try:
        result = format_available_slots('jutro')
        print(result)
    except Exception as e:
        print(f"Błąd: {e}")

    # Test 2: Dodaj rezerwację na pojutrze 15:00
    print("\n[TEST] create_appointment:")
    try:
        tz = pytz.timezone('Europe/Warsaw')
        appointment_time = tz.localize(datetime.now() + timedelta(days=2, hours=15-datetime.now().hour))
        result = create_appointment(
            client_name="Test User",
            client_phone="123456789",
            service_type="Strzyżenie",
            appointment_time=appointment_time
        )
        print(result)
    except Exception as e:
        print(f"Błąd: {e}")

    # Test 3: Usuń rezerwację na pojutrze 15:00
    print("\n[TEST] cancel_appointment:")
    try:
        # Zamień na polską nazwę dnia:
        dni_pol = {
            'Monday': 'poniedziałek',
            'Tuesday': 'wtorek',
            'Wednesday': 'środa',
            'Thursday': 'czwartek',
            'Friday': 'piątek',
            'Saturday': 'sobota',
            'Sunday': 'niedziela'
        }
        appointment_day_pl = dni_pol[appointment_time.strftime('%A')]
        result = cancel_appointment(
            client_name="Test User",
            client_phone="123456789",
            appointment_day=appointment_day_pl,
            appointment_time=appointment_time.strftime('%H:%M')
        )
        print(result)
    except Exception as e:
        print(f"Błąd: {e}")