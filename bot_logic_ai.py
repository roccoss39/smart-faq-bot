"""
Bot Logic AI - Wersja z PEŁNĄ AI klasyfikacją intencji
Wszystkie decyzje podejmuje AI, zero regex
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

# PROMPT SYSTEMOWY - IDENTYCZNY
SYSTEM_PROMPT = """
WAŻNE: Odpowiadaj BEZPOŚREDNIO bez pokazywania swojego procesu myślowego!
NIE używaj tagów <thinking> ani nie pokazuj swoich rozumowań!
Odpowiadaj tylko końcową odpowiedzią!

Jesteś AI asystentem salonu fryzjerskiego "Kleopatra" w Warszawie przy ul. Pięknej 15.

ZASADY ODPOWIEDZI:
- NIE pokazuj swojego procesu myślowego
- NIE pisz "Okay, the user is asking..." 
- NIE używaj tagów <thinking></thinking>
- Odpowiadaj TYLKO po polsku
- Bądź bezpośredni i pomocny
- Używaj max 2-3 emoji na wiadomość
- Odpowiedzi max 300 znaków (dla Facebook Messenger)

INFORMACJE O SALONIE:
- Nazwa: Salon Fryzjerski "Kleopatra"
- Adres: ul. Piękna 15, 00-001 Warszawa
- Telefon: 123-456-789
- Email: kontakt@salon-kleopatra.pl
- Website: www.salon-kleopatra.pl

GODZINY OTWARCIA:
- Poniedziałek-Piątek: 9:00-19:00
- Sobota: 9:00-16:00  
- Niedziela: zamknięte

CENNIK USŁUG:
STRZYŻENIE:
- Damskie: 80-120 zł
- Męskie: 50-70 zł
- Dziecięce: 40 zł

KOLORYZACJA:
- Całościowe farbowanie: 120-180 zł
- Retusz odrostów: 80 zł
- Pasemka/refleksy: 150-250 zł

Odpowiadaj TYLKO po polsku. Bądź pomocny i empatyczny.
WAŻNE ZASADY ODPOWIEDZI:
1. Bądź przyjazny, profesjonalny i pomocny
2. Używaj emoji do ożywienia rozmowy
3. 🔥 ZAWSZE na końcu zachęć do umówienia wizyty jednym z tych sposobów:
   - "Chcesz się umówić? Napisz: 'chcę się umówić' 📅"
   - "Mogę pomóc ci zarezerwować termin! Wystarczy napisać 'umów mnie' ✨"
   - "Gotowy na wizytę? Napisz 'wolne terminy' aby sprawdzić dostępność! 💫"
   - "Zainteresowany? Napisz 'chcę się umówić' a pokażę dostępne terminy! 🎯"
4. Jeśli pytanie dotyczy cen/usług - ZAWSZE dodaj zachętę do rezerwacji
5. Odpowiadaj krótko (max 100 słów) + zachęta do umówienia

Odpowiedz naturalnie i profesjonalnie na pytanie klienta.
"""

# ==============================================
# SYSTEM SESJI - IDENTYCZNY
# ==============================================

user_sessions = {}

class UserSession:
    def __init__(self, user_id):
        self.user_id = user_id
        self.state = "start"
        self.appointment_data = {}
        self.last_activity = datetime.now()
        
    def set_booking_details(self, day, time, service):
        self.appointment_data = {
            'day': day,
            'time': time, 
            'service': service
        }
        self.state = "waiting_for_details"
        self.last_activity = datetime.now()
        
    def set_client_details(self, name, phone):
        self.appointment_data['name'] = name
        self.appointment_data['phone'] = phone
        self.state = "ready_to_book"
        self.last_activity = datetime.now()
        
    def reset(self):
        self.state = "start"
        self.appointment_data = {}
        self.last_activity = datetime.now()
        
    def is_expired(self, minutes=30):
        return (datetime.now() - self.last_activity).total_seconds() > (minutes * 60)

def get_user_session(user_id):
    if user_id not in user_sessions:
        user_sessions[user_id] = UserSession(user_id)
    
    session = user_sessions[user_id]
    
    if session.is_expired():
        logger.info(f"🕐 Sesja {user_id} wygasła - resetowanie")
        session.reset()
    
    return session

# ==============================================
# AI KLASYFIKACJA INTENCJI - GŁÓWNA RÓŻNICA
# ==============================================

def analyze_user_intent_ai(user_message, session=None):
    """UPROSZCZONA AI KLASYFIKACJA Z CZYSZCZENIEM"""
    return analyze_user_intent_ai_robust(user_message, session)
    intent_prompt = f"""Wiadomość: "{user_message}"

Klasyfikuj do jednej kategorii:

CONTACT_DATA - Imię+nazwisko+telefon (np. "Jan Kowalski 123456789")
BOOKING - Dzień+godzina (np. "wtorek 10:00") 
ASK_AVAILABILITY - Pytanie o terminy (np. "wolne terminy")
WANT_APPOINTMENT - Chęć umówienia (np. "chcę się umówić")
CANCEL_VISIT - Anulowanie (np. "anuluj wizytę")
OTHER_QUESTION - Pozostałe (np. "cześć", "ile kosztuje")

Odpowiedz tylko nazwą kategorii:"""

    try:
        response = client.chat.completions.create(
            model="deepseek-ai/DeepSeek-R1-Distill-Llama-70B-free",
            messages=[{"role": "user", "content": intent_prompt}],
            max_tokens=1000,
            temperature=0.0
        )
        
        raw_intent = response.choices[0].message.content.strip()
        
        # 🔧 DODAJ CZYSZCZENIE!
        cleaned_intent = clean_thinking_response_enhanced(raw_intent).upper()
        
        valid_intents = ["CONTACT_DATA", "BOOKING", "ASK_AVAILABILITY", "WANT_APPOINTMENT", "CANCEL_VISIT", "OTHER_QUESTION"]
        
        for intent in valid_intents:
            if intent in cleaned_intent:
                logger.info(f"🎯 AI Intent: '{user_message}' → {intent}")
                return intent
        
        logger.warning(f"🤔 AI raw: '{raw_intent}' → cleaned: '{cleaned_intent}' → OTHER_QUESTION")
        return "OTHER_QUESTION"
        
    except Exception as e:
        logger.error(f"❌ Błąd AI klasyfikacji: {e}")
        return "OTHER_QUESTION"

# ==============================================
# AI PARSOWANIE DANYCH - TAKŻE AI!
# ==============================================


def parse_contact_data_ai(message):
    """ULTRA PRECYZYJNE AI parsowanie danych kontaktowych - Z CZYSZCZENIEM JSON"""
    parse_prompt = f"""WYCIĄGNIJ DANE KONTAKTOWE Z WIADOMOŚCI:

"{message}"

SZUKAJ WZORCÓW:
1. IMIĘ + NAZWISKO (każde słowo zaczyna się wielką literą)
2. TELEFON (ciąg 9 cyfr, może mieć spacje/myślniki)

AKCEPTOWANE FORMATY:
✅ "Jan Kowalski 123456789"
✅ "Anna Nowak, 987654321"  
✅ "Piotr Wiśniewski tel. 555 666 777"
✅ "Maria Kowalczyk telefon: 111-222-333"
✅ "nazywam się Adam Nowak, numer 444555666"

ODRZUCANE:
❌ "chcę się umówić" (brak danych)
❌ "Jan 123456789" (brak nazwiska)  
❌ "Jan Kowalski" (brak telefonu)
❌ "123456789" (brak imienia)

INSTRUKCJE:
- Znajdź pierwsze imię + nazwisko w tekście
- Znajdź 9-cyfrowy numer telefonu (usuń spacje/myślniki)
- Jeśli brak któregoś elementu → zwróć null

FORMAT ODPOWIEDZI (tylko JSON, bez bloków kodu):
{{"name": "Imię Nazwisko", "phone": "123456789"}}

lub

null"""

    try:
        response = client.chat.completions.create(
            model="deepseek-ai/DeepSeek-R1-Distill-Llama-70B-free",
            messages=[{"role": "user", "content": parse_prompt}],
            max_tokens=1000,
            temperature=0.0
        )
        
        raw_response = response.choices[0].message.content.strip()
        cleaned_response = clean_thinking_response(raw_response)
        
        # 🔧 USUŃ BLOKI KODU MARKDOWN
        cleaned_response = re.sub(r'```json\s*', '', cleaned_response)
        cleaned_response = re.sub(r'```\s*', '', cleaned_response)
        cleaned_response = cleaned_response.strip()
        
        import json
        try:
            # Sprawdź czy odpowiedź to null
            if "null" in cleaned_response.lower():
                logger.info(f"🔍 AI CONTACT: '{message}' → null (brak danych)")
                return None
                
            # Spróbuj sparsować JSON
            result = json.loads(cleaned_response)
            if result and result.get('name') and result.get('phone'):
                # Walidacja telefonu - tylko cyfry, dokładnie 9
                phone = re.sub(r'[-\s().]', '', str(result['phone']))
                if len(phone) == 9 and phone.isdigit():
                    logger.info(f"🔍 AI CONTACT: '{message}' → {result}")
                    return {'name': result['name'], 'phone': phone}
        except json.JSONDecodeError as e:
            logger.warning(f"🔍 AI CONTACT JSON error: {e}, cleaned: '{cleaned_response}'")
            
        logger.warning(f"🔍 AI CONTACT: '{message}' → nieprawidłowy format: '{cleaned_response}'")
        return None
        
    except Exception as e:
        logger.error(f"❌ Błąd AI parsowania kontaktu: {e}")
        return None

def parse_booking_message_ai(message):
    """ULTRA PRECYZYJNE AI parsowanie szczegółów rezerwacji - Z CZYSZCZENIEM JSON"""
    parse_prompt = f"""WYCIĄGNIJ SZCZEGÓŁY REZERWACJI Z WIADOMOŚCI:

"{message}"

SZUKAJ WZORCÓW:
1. DZIEŃ TYGODNIA (pełna nazwa: poniedziałek, wtorek, środa, czwartek, piątek, sobota)
2. GODZINA (format HH:MM, np. 10:00, 15:30)
3. USŁUGA (opcjonalne, domyślnie "Strzyżenie")

AKCEPTOWANE FORMATY:
✅ "umawiam się na wtorek 10:00" → {{"day": "Wtorek", "time": "10:00", "service": "Strzyżenie"}}
✅ "środa 15:30" → {{"day": "Środa", "time": "15:30", "service": "Strzyżenie"}}
✅ "piątek o 14:00" → {{"day": "Piątek", "time": "14:00", "service": "Strzyżenie"}}
✅ "środa 15:30 na farbowanie" → {{"day": "Środa", "time": "15:30", "service": "Farbowanie"}}
✅ "chcę na poniedziałek o 11:00" → {{"day": "Poniedziałek", "time": "11:00", "service": "Strzyżenie"}}

ODRZUCANE:
❌ "chcę się umówić" → null (brak terminu)
❌ "wtorek" → null (brak godziny)
❌ "10:00" → null (brak dnia)

MAPOWANIE DNI:
- poniedziałek/pon → "Poniedziałek"
- wtorek/wt → "Wtorek"  
- środa/sr → "Środa"
- czwartek/czw → "Czwartek"
- piątek/pt → "Piątek"
- sobota/sob → "Sobota"

MAPOWANIE USŁUG:
- strzyżenie/obcięcie → "Strzyżenie"
- farbowanie/koloryzacja → "Farbowanie"
- inne/brak → "Strzyżenie"

FORMAT ODPOWIEDZI (tylko JSON, bez bloków kodu):
{{"day": "Dzień", "time": "HH:MM", "service": "Usługa"}}

lub

null"""

    try:
        response = client.chat.completions.create(
            model="deepseek-ai/DeepSeek-R1-Distill-Llama-70B-free",
            messages=[{"role": "user", "content": parse_prompt}],
            max_tokens=1000,
            temperature=0.0
        )
        
        raw_response = response.choices[0].message.content.strip()
        cleaned_response = clean_thinking_response(raw_response)
        
        # 🔧 USUŃ BLOKI KODU MARKDOWN
        cleaned_response = re.sub(r'```json\s*', '', cleaned_response)
        cleaned_response = re.sub(r'```\s*', '', cleaned_response)
        cleaned_response = cleaned_response.strip()
        
        import json
        try:
            if "null" in cleaned_response.lower():
                logger.info(f"🔍 AI BOOKING: '{message}' → null (brak terminu)")
                return None
                
            result = json.loads(cleaned_response)
            if result and result.get('day') and result.get('time'):
                # Walidacja godziny
                time_str = str(result['time'])
                if re.match(r'^\d{1,2}:\d{2}$', time_str):
                    hour = int(time_str.split(':')[0])
                    if 9 <= hour <= 19:  # Godziny pracy
                        # Domyślna usługa jeśli brak
                        service = result.get('service', 'Strzyżenie')
                        parsed_result = {
                            'day': result['day'],
                            'time': time_str,
                            'service': service
                        }
                        logger.info(f"🔍 AI BOOKING: '{message}' → {parsed_result}")
                        return parsed_result
        except json.JSONDecodeError as e:
            logger.warning(f"🔍 AI BOOKING JSON error: {e}, cleaned: '{cleaned_response}'")
            
        logger.warning(f"🔍 AI BOOKING: '{message}' → nieprawidłowy format: '{cleaned_response}'")
        return None
        
    except Exception as e:
        logger.error(f"❌ Błąd AI parsowania rezerwacji: {e}")
        return None

# def parse_contact_data_ai(message):
#     """ULTRA PRECYZYJNE AI parsowanie danych kontaktowych"""
#     parse_prompt = f"""WYCIĄGNIJ DANE KONTAKTOWE Z WIADOMOŚCI:

# "{message}"

# SZUKAJ WZORCÓW:
# 1. IMIĘ + NAZWISKO (każde słowo zaczyna się wielką literą)
# 2. TELEFON (ciąg 9 cyfr, może mieć spacje/myślniki)

# AKCEPTOWANE FORMATY:
# ✅ "Jan Kowalski 123456789"
# ✅ "Anna Nowak, 987654321"  
# ✅ "Piotr Wiśniewski tel. 555 666 777"
# ✅ "Maria Kowalczyk telefon: 111-222-333"
# ✅ "nazywam się Adam Nowak, numer 444555666"

# ODRZUCANE:
# ❌ "chcę się umówić" (brak danych)
# ❌ "Jan 123456789" (brak nazwiska)  
# ❌ "Jan Kowalski" (brak telefonu)
# ❌ "123456789" (brak imienia)

# INSTRUKCJE:
# - Znajdź pierwsze imię + nazwisko w tekście
# - Znajdź 9-cyfrowy numer telefonu (usuń spacje/myślniki)
# - Jeśli brak któregoś elementu → zwróć null

# FORMAT ODPOWIEDZI (tylko JSON):
# {{"name": "Imię Nazwisko", "phone": "123456789"}}

# lub

# null"""

#     try:
#         response = client.chat.completions.create(
#             model="deepseek-ai/DeepSeek-R1-Distill-Llama-70B-free",
#             messages=[{"role": "user", "content": parse_prompt}],
#             max_tokens=1000,
#             temperature=0.0
#         )
        
#         raw_response = response.choices[0].message.content.strip()
#         cleaned_response = clean_thinking_response(raw_response)
        
#         import json
#         try:
#             # Sprawdź czy odpowiedź to null
#             if "null" in cleaned_response.lower():
#                 logger.info(f"🔍 AI CONTACT: '{message}' → null (brak danych)")
#                 return None
                
#             # Spróbuj sparsować JSON
#             result = json.loads(cleaned_response)
#             if result and result.get('name') and result.get('phone'):
#                 # Walidacja telefonu - tylko cyfry, dokładnie 9
#                 phone = re.sub(r'[-\s().]', '', str(result['phone']))
#                 if len(phone) == 9 and phone.isdigit():
#                     logger.info(f"🔍 AI CONTACT: '{message}' → {result}")
#                     return {'name': result['name'], 'phone': phone}
#         except json.JSONDecodeError:
#             pass
            
#         logger.warning(f"🔍 AI CONTACT: '{message}' → nieprawidłowy format: '{cleaned_response}'")
#         return None
        
#     except Exception as e:
#         logger.error(f"❌ Błąd AI parsowania kontaktu: {e}")
#         return None

def parse_cancellation_data_ai(message):
    """AI parsowanie danych do anulowania"""
    parse_prompt = f"""Wyciągnij dane do anulowania wizyty.

WIADOMOŚĆ: "{message}"

Znajdź:
1. IMIĘ I NAZWISKO
2. NUMER TELEFONU (9 cyfr)
3. DZIEŃ TYGODNIA wizyty
4. GODZINĘ wizyty (HH:MM)

ODPOWIEDZ W FORMACIE JSON:
{{"name": "Imię Nazwisko", "phone": "123456789", "day": "Dzień", "time": "HH:MM"}}

Jeśli nie można wyciągnąć wszystkich danych, odpowiedz: null"""

    try:
        response = client.chat.completions.create(
            model="deepseek-ai/DeepSeek-R1-Distill-Llama-70B-free",
            messages=[{"role": "user", "content": parse_prompt}],
            max_tokens=1000,
            temperature=0.1
        )
        
        raw_response = response.choices[0].message.content.strip()
        cleaned_response = clean_thinking_response(raw_response)
        
        import json
        try:
            result = json.loads(cleaned_response)
            if (result and result.get('name') and result.get('phone') 
                and result.get('day') and result.get('time')):
                
                # Walidacja telefonu
                phone = re.sub(r'[-\s]', '', result['phone'])
                if len(phone) == 9 and phone.isdigit():
                    return {
                        'name': result['name'], 
                        'phone': phone,
                        'day': result['day'],
                        'time': result['time']
                    }
        except:
            pass
            
        return None
        
    except Exception as e:
        logger.error(f"❌ Błąd AI parsowania anulowania: {e}")
        return None

# ==============================================
# FUNKCJE POMOCNICZE - IDENTYCZNE
# ==============================================

def clean_thinking_response(response_text):
    """Usuwa sekcje 'thinking' z odpowiedzi modelu"""
    if not response_text:
        return ""
        
    original = response_text
    cleaned = response_text
    
    if '<think>' in cleaned.lower() and '</think>' not in cleaned.lower():
        think_pattern = re.compile(r'<think[^>]*>', re.IGNORECASE)
        matches = list(think_pattern.finditer(cleaned))
        if matches:
            last_match = matches[-1]
            after_think = cleaned[last_match.end():]
            
            lines = after_think.strip().split('\n')
            for line in lines:
                line = line.strip()
                if any(intent in line.upper() for intent in ["BOOKING", "ASK_AVAILABILITY", "WANT_APPOINTMENT", "CONTACT_DATA", "CANCEL_VISIT", "OTHER_QUESTION"]):
                    cleaned = line
                    break
            else:
                for line in lines:
                    if len(line.strip()) > 0 and not line.strip().startswith('<'):
                        cleaned = line.strip()
                        break
    
    cleaned = re.sub(r'<thinking>.*?</thinking>', '', cleaned, flags=re.DOTALL | re.IGNORECASE)
    cleaned = re.sub(r'<THINK>.*?</THINK>', '', cleaned, flags=re.DOTALL | re.IGNORECASE)
    cleaned = re.sub(r'<think>.*?</think>', '', cleaned, flags=re.DOTALL | re.IGNORECASE)
    cleaned = re.sub(r'<[^>]*>', '', cleaned)
    cleaned = cleaned.strip()
    
    return cleaned

# DODAJ na końcu pliku bot_logic_ai.py (przed ostatnią linią):

def clean_thinking_response_enhanced(response_text):
    """ULEPSZONE czyszczenie thinking tags - specjalnie dla klasyfikacji"""
    if not response_text:
        return ""
        
    original = response_text
    cleaned = response_text
    
    # 1. USUŃ WSZYSTKIE THINKING BLOKI
    cleaned = re.sub(r'<think>.*?</think>', '', cleaned, flags=re.DOTALL | re.IGNORECASE)
    cleaned = re.sub(r'<thinking>.*?</thinking>', '', cleaned, flags=re.DOTALL | re.IGNORECASE)
    
    # 2. USUŃ NIEDOMKNIĘTE THINKING TAGI
    cleaned = re.sub(r'<think[^>]*>.*$', '', cleaned, flags=re.DOTALL | re.IGNORECASE)
    cleaned = re.sub(r'<thinking[^>]*>.*$', '', cleaned, flags=re.DOTALL | re.IGNORECASE)
    
    # 3. USUŃ WSZYSTKIE TAGI HTML
    cleaned = re.sub(r'<[^>]*>', '', cleaned)
    
    # 4. USUŃ TYPOWE AI INTRO PHRASES
    intro_phrases = [
        r'okay,?\s+so\s+i\s+need\s+to\s+classify.*?[.!]',
        r'let\s+me\s+go\s+through.*?[.!]',
        r'i\s+need\s+to\s+analyze.*?[.!]',
        r'looking\s+at\s+this\s+message.*?[.!]'
    ]
    
    for phrase in intro_phrases:
        cleaned = re.sub(phrase, '', cleaned, flags=re.IGNORECASE)
    
    # 5. WYCIĄGNIJ TYLKO NAZWĘ KATEGORII
    valid_intents = ["CONTACT_DATA", "BOOKING", "ASK_AVAILABILITY", "WANT_APPOINTMENT", "CANCEL_VISIT", "OTHER_QUESTION"]
    
    # Sprawdź czy w oczyszczonej odpowiedzi jest kategoria
    cleaned_upper = cleaned.upper()
    for intent in valid_intents:
        if intent in cleaned_upper:
            return intent
    
    # 6. JEŚLI NIE ZNALEZIONO, SPRÓBUJ WYCIĄGNĄĆ Z ORYGINALNEJ
    original_upper = original.upper()
    for intent in valid_intents:
        if intent in original_upper:
            return intent
    
    # 7. OSTATNIA SZANSA - WYCIĄGNIJ OSTATNIĄ LINIĘ
    lines = cleaned.strip().split('\n')
    if lines:
        last_line = lines[-1].strip().upper()
        for intent in valid_intents:
            if intent in last_line:
                return intent
    
    return cleaned.strip()

def analyze_user_intent_ai_robust(user_message, session=None):
    """NIEZAWODNA AI KLASYFIKACJA Z MULTIPLE FALLBACKS"""
    
    # STRATEGIA 1: ULEPSONY PROMPT Z PRZYKŁADAMI
    try:
        enhanced_prompt = f"""KLASYFIKUJ WIADOMOŚĆ UŻYTKOWNIKA:

WIADOMOŚĆ: "{user_message}"

KATEGORIE Z PRZYKŁADAMI:

1. CONTACT_DATA - Dane kontaktowe (imię + nazwisko + telefon):
   ✅ "Jan Kowalski, 123456789"
   ✅ "Anna Nowak tel. 987654321"
   ✅ "Piotr Wiśniewski, numer: 555666777"
   ❌ "chcę się umówić"

2. BOOKING - Konkretny termin (dzień + godzina):
   ✅ "umawiam się na wtorek 10:00"
   ✅ "środa 15:30 na strzyżenie"
   ✅ "piątek o 14:00"
   ❌ "chcę się umówić"
   ❌ "wtorek" (brak godziny)

3. ASK_AVAILABILITY - Pytanie o dostępne terminy:
   ✅ "wolne terminy?"
   ✅ "godziny w środę?"
   ✅ "kiedy można się umówić?"
   ✅ "dostępne terminy w piątek?"

4. WANT_APPOINTMENT - Chęć umówienia bez konkretnego terminu:
   ✅ "chcę się umówić"
   ✅ "potrzebuję wizyty"
   ✅ "umów mnie"
   ✅ "rezerwacja"

5. CANCEL_VISIT - Anulowanie wizyty:
   ✅ "anuluj wizytę"
   ✅ "odwołaj termin"
   ✅ "rezygnuję z wizyty"

6. OTHER_QUESTION - Pozostałe (powitania, pytania o ceny, lokalizację):
   ✅ "cześć"
   ✅ "ile kosztuje strzyżenie?"
   ✅ "gdzie jesteście?"
   ✅ "godziny otwarcia?"

ODPOWIEDZ TYLKO NAZWĄ KATEGORII (bez myślenia na głos):"""
        
        response = client.chat.completions.create(
            model="deepseek-ai/DeepSeek-R1-Distill-Llama-70B-free",
            messages=[{"role": "user", "content": enhanced_prompt}],
            max_tokens=1000,
            temperature=0.0
        )
        
        raw = response.choices[0].message.content.strip()
        cleaned = clean_thinking_response_enhanced(raw)
        
        valid_intents = ["CONTACT_DATA", "BOOKING", "ASK_AVAILABILITY", "WANT_APPOINTMENT", "CANCEL_VISIT", "OTHER_QUESTION"]
        
        for intent in valid_intents:
            if intent in cleaned.upper():
                logger.info(f"🎯 AI Strategy 1 Enhanced: '{user_message}' → {intent}")
                return intent
            
    except Exception as e:
        logger.warning(f"AI Strategy 1 Enhanced failed: {e}")
    
    # STRATEGIA 2: STEP-BY-STEP ANALYSIS
    try:
        step_prompt = f"""ANALIZUJ KROK PO KROKU:

WIADOMOŚĆ: "{user_message}"

KROK 1: Czy zawiera imię + nazwisko + telefon (9 cyfr)?
- TAK → CONTACT_DATA
- NIE → idź do KROK 2

KROK 2: Czy zawiera dzień tygodnia + godzinę (HH:MM)?
- TAK → BOOKING  
- NIE → idź do KROK 3

KROK 3: Czy pyta o dostępne terminy/godziny?
- Słowa: "wolne", "dostępne", "terminy", "godziny w"
- TAK → ASK_AVAILABILITY
- NIE → idź do KROK 4

KROK 4: Czy wyraża chęć umówienia się?
- Słowa: "chcę się umówić", "potrzebuję wizyty", "umów mnie"
- TAK → WANT_APPOINTMENT
- NIE → idź do KROK 5

KROK 5: Czy chce anulować wizytę?
- Słowa: "anuluj", "odwołaj", "rezygnuj"
- TAK → CANCEL_VISIT
- NIE → OTHER_QUESTION

ODPOWIEDŹ (tylko nazwa kategorii):"""
        
        response = client.chat.completions.create(
            model="deepseek-ai/DeepSeek-R1-Distill-Llama-70B-free",
            messages=[{"role": "user", "content": step_prompt}],
            max_tokens=500,
            temperature=0.0
        )
        
        raw = response.choices[0].message.content.strip()
        cleaned = clean_thinking_response_enhanced(raw)
        
        for intent in valid_intents:
            if intent in cleaned.upper():
                logger.info(f"🎯 AI Strategy 2 Step-by-step: '{user_message}' → {intent}")
                return intent
                
    except Exception as e:
        logger.warning(f"AI Strategy 2 failed: {e}")
    
    # STRATEGIA 3: SIMPLE KEYWORDS (pure AI approach)
    try:
        keyword_prompt = f"""Przeanalizuj wiadomość i znajdź kluczowe elementy:

WIADOMOŚĆ: "{user_message}"

SZUKAJ:
- Czy jest imię + nazwisko + 9-cyfrowy telefon? → CONTACT_DATA
- Czy jest dzień (poniedziałek/wtorek/środa/czwartek/piątek/sobota) + czas (XX:XX)? → BOOKING
- Czy pyta o "wolne terminy" lub "dostępne godziny"? → ASK_AVAILABILITY  
- Czy mówi "chcę się umówić" lub podobnie? → WANT_APPOINTMENT
- Czy mówi "anuluj" lub "odwołaj"? → CANCEL_VISIT
- W pozostałych przypadkach → OTHER_QUESTION

Odpowiedz kategorią:"""
        
        response = client.chat.completions.create(
            model="deepseek-ai/DeepSeek-R1-Distill-Llama-70B-free",
            messages=[{"role": "user", "content": keyword_prompt}],
            max_tokens=500,
            temperature=0.0
        )
        
        raw = response.choices[0].message.content.strip()
        cleaned = clean_thinking_response_enhanced(raw)
        
        for intent in valid_intents:
            if intent in cleaned.upper():
                logger.info(f"🎯 AI Strategy 3 Keywords: '{user_message}' → {intent}")
                return intent
                
    except Exception as e:
        logger.warning(f"AI Strategy 3 failed: {e}")
    
    # OSTATECZNY FALLBACK - prosty wybór
    logger.warning(f"🚨 Wszystkie AI strategie nie działają dla: '{user_message}' → OTHER_QUESTION")
    return "OTHER_QUESTION"

def create_booking(appointment_data):
    """Identyczna funkcja tworzenia wizyty"""
    try:
        day_map = {
            'Poniedziałek': 0, 'Wtorek': 1, 'Środa': 2, 
            'Czwartek': 3, 'Piątek': 4, 'Sobota': 5
        }
        
        target_day = day_map.get(appointment_data['day'])
        if target_day is None:
            logger.error(f"❌ Nieprawidłowy dzień: {appointment_data['day']}")
            return False
            
        tz = pytz.timezone('Europe/Warsaw')
        now = datetime.now(tz)
        days_ahead = (target_day - now.weekday()) % 7
        if days_ahead == 0:
            days_ahead = 7
            
        appointment_date = now + timedelta(days=days_ahead)
        
        time_parts = appointment_data['time'].split(':')
        appointment_datetime = appointment_date.replace(
            hour=int(time_parts[0]), 
            minute=int(time_parts[1]), 
            second=0, 
            microsecond=0
        )
        
        if appointment_datetime <= now:
            logger.error(f"❌ Termin w przeszłości: {appointment_datetime}")
            return False
        
        logger.info(f"📅 Tworzenie wizyty: {appointment_datetime} dla {appointment_data['name']}")
        
        result = create_appointment(
            client_name=appointment_data['name'],
            client_phone=appointment_data['phone'],
            service_type=appointment_data['service'],
            appointment_time=appointment_datetime
        )
        
        if result:
            logger.info(f"✅ Wizyta utworzona! ID: {result}")
            return True
        else:
            logger.error("❌ Błąd tworzenia wizyty w kalendarzu")
            return False
        
    except Exception as e:
        logger.error(f"❌ Błąd tworzenia wizyty: {e}")
        return False

def get_ai_response(user_message):
    """Identyczna funkcja AI response"""
    message_lower = user_message.lower().strip()
    
    quick_responses = {
        'jakie usługi oferujecie': """✂️ **NASZE USŁUGI:**

**STRZYŻENIE:**
• Damskie: 80-120 zł
• Męskie: 50-70 zł  
• Dziecięce: 40 zł

**KOLORYZACJA:**
• Całościowe farbowanie: 120-180 zł
• Retusz odrostów: 80 zł
• Pasemka/refleksy: 150-250 zł

💫 **Chcesz się umówić?** Napisz: *'chcę się umówić'* 📅""",

        'gdzie jesteście': """📍 **LOKALIZACJA:**

🏢 **Salon Fryzjerski "Kleopatra"**
📮 ul. Piękna 15, 00-001 Warszawa

🚇 **Dojazd:**
• Metro: Centrum (5 min pieszo)
• Autobus: 15, 18, 35 (przystanek Piękna)

🅿️ **Parking:** Publiczne miejsca w okolicy

💫 **Chcesz się umówić?** Napisz: *'chcę się umówić'* 📅""",

        'godziny otwarcia': """🕐 **GODZINY OTWARCIA:**

📅 **Poniedziałek-Piątek:** 9:00-19:00
📅 **Sobota:** 9:00-16:00  
📅 **Niedziela:** Zamknięte

📞 **Kontakt:** 123-456-789
📧 **Email:** kontakt@salon-kleopatra.pl

💫 **Chcesz się umówić?** Napisz: *'chcę się umówić'* 📅""",

        'kontakt': """📞 **KONTAKT:**

☎️ **Telefon:** 123-456-789
📧 **Email:** kontakt@salon-kleopatra.pl
🌐 **Strona:** www.salon-kleopatra.pl

📍 **Adres:** ul. Piękna 15, Warszawa

🕐 **Godziny:** Pon-Pt 9:00-19:00, Sob 9:00-16:00

💫 **Chcesz się umówić?** Napisz: *'chcę się umówić'* 📅"""
    }
    
    for phrase, response in quick_responses.items():
        if phrase in message_lower:
            return response

    try:
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message}
        ]
        
        response = client.chat.completions.create(
            model="deepseek-ai/DeepSeek-R1-Distill-Llama-70B-free",
            messages=messages,
            max_tokens=600,
            temperature=0.3
        )
        
        raw_response = response.choices[0].message.content
        cleaned_response = clean_thinking_response(raw_response)
        
        if len(cleaned_response.strip()) > 10:
            return cleaned_response.strip()
        else:
            return "😊 Dzień dobry! Jak mogę pomóc? Zapraszamy do salonu Kleopatra na ul. Pięknej 15! 💇‍♀️"
        
    except Exception as e:
        logger.error(f"❌ Błąd AI response: {e}")
        return "😔 Przepraszam, chwilowo mam problemy z odpowiadaniem. Zadzwoń: **123-456-789** 📞"

def get_welcome_menu():
    """Identyczne menu powitalne"""
    menu = """👋 **Witamy w Salonie Fryzjerskim "Kleopatra"**

Miło Cię poznać! W czym możemy pomóc?

📅 **Chcesz się umówić na wizytę?**
Napisz: *"chcę się umówić"*

🔍 **Chcesz sprawdzić wolne terminy?**
Napisz: *"wolne terminy"*

❌ **Chcesz anulować istniejącą wizytę?**
Napisz: *"anuluj wizytę"*

✂️ **Chcesz poznać nasze usługi i ceny?**
Napisz: *"jakie usługi oferujecie?"*

📍 **Chcesz dowiedzieć się więcej o salonie?**
Napisz: *"gdzie jesteście?"* lub *"godziny otwarcia"*

📞 **Kontakt bezpośredni:**
Telefon: **123-456-789**

💬 **Możesz też po prostu napisać o co Ci chodzi - zrozumiem!** 😊"""

    return menu

def extract_day_from_message(message):
    """ULEPSZONE AI wyciąganie dnia z wiadomości"""
    day_prompt = f"""ZNAJDŹ DZIEŃ TYGODNIA:

WIADOMOŚĆ: "{message}"

SZUKAJ DOKŁADNIE:
- poniedziałek/poniedzialek/pon → Poniedziałek
- wtorek/wtor/wt → Wtorek  
- środa/sroda/śr/sr → Środa
- czwartek/czwartke/czw → Czwartek
- piątek/piatek/pt → Piątek
- sobota/sobotę/sob → Sobota
- niedziela/niedzielę/niedziele/nd → Niedziela

PRZYKŁADY:
"godziny w środę" → Środa
"wolne terminy w piątek" → Piątek
"czy macie coś na wtorek" → Wtorek
"chcę się umówić" → null

ODPOWIEDŹ (tylko nazwa dnia lub null):"""

    try:
        response = client.chat.completions.create(
            model="deepseek-ai/DeepSeek-R1-Distill-Llama-70B-free",
            messages=[{"role": "user", "content": day_prompt}],
            max_tokens=500,
            temperature=0.0
        )
        
        result = clean_thinking_response(response.choices[0].message.content.strip())
        
        # Mapowanie AI odpowiedzi na standardowe nazwy
        day_mapping = {
            'poniedziałek': 'Poniedziałek',
            'wtorek': 'Wtorek', 
            'środa': 'Środa',
            'czwartek': 'Czwartek',
            'piątek': 'Piątek',
            'sobota': 'Sobota',
            'niedziela': 'Niedziela'
        }
        
        result_lower = result.lower()
        for key, value in day_mapping.items():
            if key in result_lower:
                logger.info(f"🔍 AI extracted day: '{message}' → {value}")
                return value
        
        logger.info(f"🔍 AI no day found in: '{message}' → None")
        return None
        
    except Exception as e:
        logger.error(f"❌ Błąd AI wyciągania dnia: {e}")
        return None

# ==============================================
# GŁÓWNA FUNKCJA - IDENTYCZNA LOGIKA, INNE PARSOWANIE
# ==============================================

def process_user_message(user_message, user_id=None):
    """GŁÓWNA FUNKCJA - AI VERSION"""
    try:
        session = get_user_session(user_id) if user_id else None
        user_message = user_message.strip()
        
        logger.info(f"🤖 AI: Przetwarzam: '{user_message}' | Sesja: {session.state if session else 'brak'}")
        
        # ===========================================
        # AI ANALYSIS INTENCJI - GŁÓWNA RÓŻNICA!
        # ===========================================
        
        intent = analyze_user_intent_ai(user_message, session)  # ← AI ZAMIAST REGEX!
        
        # ===========================================
        # OBSŁUGA - IDENTYCZNA LOGIKA
        # ===========================================
        
        # 1. CONTACT_DATA + waiting_for_details = TWORZENIE WIZYTY
        if intent == "CONTACT_DATA" and session and session.state == "waiting_for_details":
            contact_data = parse_contact_data_ai(user_message)  # ← AI PARSING!
            if contact_data:
                session.set_client_details(contact_data['name'], contact_data['phone'])
                
                appointment_result = create_booking(session.appointment_data)
                
                if appointment_result:
                    confirmation = f"✅ **WIZYTA POTWIERDZONA!**\n\n📅 **Termin:** {session.appointment_data['day']} {session.appointment_data['time']}\n👤 **Klient:** {contact_data['name']}\n📞 **Telefon:** {contact_data['phone']}\n✂️ **Usługa:** {session.appointment_data['service']}\n\n📍 **Salon Kleopatra**\nul. Piękna 15, Warszawa\n\n🎉 Do zobaczenia w salonie!"
                    session.reset()
                    return confirmation
                else:
                    session.reset()
                    return f"❌ **Błąd rezerwacji**\n\nTermin mógł zostać zajęty przez kogoś innego.\n📞 Zadzwoń: **123-456-789**"
            else:
                return f"📝 **Błędny format!**\n\nNapisz w formacie:\n**\"Imię Nazwisko, numer telefonu\"**\n\nNp: **\"Jan Kowalski, 123456789\"**"
        
        # 2. CONTACT_DATA + cancelling = ANULOWANIE WIZYTY  
        elif intent == "CONTACT_DATA" and session and session.state == "cancelling":
            cancellation_data = parse_cancellation_data_ai(user_message)  # ← AI PARSING!
            if cancellation_data:
                        
                cancel_result = cancel_appointment(
                    client_name=cancellation_data['name'],
                    client_phone=cancellation_data['phone'], 
                    appointment_day=cancellation_data['day'],
                    appointment_time=cancellation_data['time']
                )
                
                session.reset()
                
                if cancel_result:
                    return f"✅ **Wizyta anulowana!**\n\n👤 Klient: {cancellation_data['name']}\n📞 Telefon: {cancellation_data['phone']}\n📅 Termin: {cancellation_data['day']} {cancellation_data['time']}\n\n🗑️ **Usunięto z kalendarza**\n\n🤖 Czy mogę w czymś jeszcze pomóc?"
                else:
                    return f"❌ **Nie znaleziono wizyty**\n\n👤 Klient: {cancellation_data['name']}\n📞 Telefon: {cancellation_data['phone']}\n📅 Termin: {cancellation_data['day']} {cancellation_data['time']}\n\n🔍 **Sprawdź dane lub zadzwoń:** 123-456-789"
            else:
                return f"📝 **Błędny format!**\n\nPodaj w formacie:\n**\"Imię Nazwisko, telefon, dzień godzina\"**\n\nNp: *\"Jan Kowalski, 123456789, środa 11:00\"*"
        
        # 3. BOOKING - konkretna rezerwacja
        elif intent == "BOOKING":
            parsed = parse_booking_message_ai(user_message)  # ← AI PARSING!
            logger.info(f"🔍 AI PARSED BOOKING: {parsed}")
            
            if parsed and session:
                session.set_booking_details(parsed['day'], parsed['time'], parsed['service'])
                return f"📝 **Prawie gotowe!**\n\n📅 **Termin:** {parsed['day']} {parsed['time']}\n✂️ **Usługa:** {parsed['service']}\n\n🔔 Potrzebuję jeszcze:\n• 👤 **Imię i nazwisko**\n• 📞 **Numer telefonu**\n\nNapisz: **\"Jan Kowalski, 123456789\"**"
            else:
                return f"📝 **Nie mogę rozpoznać terminu!**\n\nSprawdź format:\n**\"Umawiam się na [dzień] [godzina] na strzyżenie\"**\n\nNp: *\"Umawiam się na wtorek 10:00 na strzyżenie\"*"
        
        # 4. ASK_AVAILABILITY - identyczne
        elif intent == "ASK_AVAILABILITY":
            day_mentioned = extract_day_from_message(user_message)  # ← AI EXTRACTION!
            
            try:
                if day_mentioned:
                    from calendar_service import get_available_slots_for_day
                    
                    slots = get_available_slots_for_day(day_mentioned)
                    
                    if slots:
                        day_display = day_mentioned.capitalize()
                        response = f"📅 **Wolne terminy w {day_display}:**\n"
                        
                        hours = []
                        for slot in slots:
                            time_str = slot['datetime'].strftime('%H:%M')
                            if time_str not in hours:
                                hours.append(time_str)
                        
                        for hour in hours:
                            response += f"• {hour}\n"
                            
                        response += f"\n💬 Aby się umówić napisz:\n*\"Umawiam się na {day_mentioned.lower()} [godzina] na [usługa]\"*"
                        
                        return response
                    else:
                        return f"❌ **Brak wolnych terminów w {day_mentioned.capitalize()}**\n\nSprawdź inne dni lub zadzwoń: 123-456-789"
                
                else:
                    slots = get_available_slots(days_ahead=10)
                    
                    if slots:
                        from collections import defaultdict
                        slots_by_day = defaultdict(list)
                        
                        for slot in slots:
                            day_name = slot['day_name']
                            slots_by_day[day_name].append(slot)
                        
                        response = "📅 **Dostępne terminy:**\n"
                        for day_name, day_slots in list(slots_by_day.items())[:5]:
                            response += f"• **{day_name}**: "
                            times = [slot['datetime'].strftime('%H:%M') for slot in day_slots[:4]]
                            response += ", ".join(times)
                            response += "\n"
                        
                        response += "\n💬 Aby sprawdzić konkretny dzień napisz:\n*\"godziny w środę\"* lub *\"wolne terminy w piątek\"*"
                        
                        return response
                    else:
                        return "❌ **Brak dostępnych terminów**\n\nSpróbuj później lub zadzwoń: 123-456-789"
                        
            except Exception as e:
                logger.error(f"❌ Błąd pobierania terminów: {e}")
                return "😔 Problem z kalendarżem. Zadzwoń: **123-456-789** 📞"
        
        # 5. WANT_APPOINTMENT - identyczne
        elif intent == "WANT_APPOINTMENT":
            try:
                slots = get_available_slots(days_ahead=10)
                if slots:
                    if session:
                        session.state = "booking"
                    
                    slots_text = '\n'.join([
                        f"• {slot['day_name']} {slot['display'].split()[-1]}" 
                        for slot in slots[:8]
                    ])
                    
                    return f"📅 **Dostępne terminy:**\n{slots_text}\n\n💬 Napisz:\n**\"Umawiam się na [dzień] [godzina] na strzyżenie\"** ✂️"
                else:
                    return "😔 Brak wolnych terminów w najbliższych dniach.\n📞 Zadzwoń: **123-456-789**"
            except Exception as e:
                logger.error(f"❌ Błąd pobierania terminów: {e}")
                return "😔 Problem z kalendarżem. Zadzwoń: **123-456-789** 📞"
        
        # 6. CANCEL_VISIT - identyczne
        elif intent == "CANCEL_VISIT":
            if session and session.state == "waiting_for_details" and session.appointment_data:
                appointment_info = session.appointment_data
                session.reset()
                return f"❌ **Anulowano rezerwację**\n\n📅 Termin: {appointment_info['day']} {appointment_info['time']}\n✂️ Usługa: {appointment_info['service']}\n\n🤖 Mogę Ci w czymś jeszcze pomóc?"
            else:
                if session:
                    session.state = "cancelling"
                return f"❌ **Anulowanie wizyty**\n\n🔍 Aby anulować wizytę, podaj:\n• 👤 **Imię i nazwisko**\n• 📞 **Numer telefonu**\n• 📅 **Dzień i godzinę wizyty**\n\nNp: *\"Jan Kowalski, 123456789, środa 11:00\"*"
        
        # 7. OTHER_QUESTION - identyczne
        else:
            greeting_patterns = [
                'hej', 'cześć', 'dzień dobry', 'witaj', 'hello', 'hi', 'siema',
                'dobry wieczór', 'miłego dnia', 'pozdrawiam', 'dobry', 'witam'
            ]
            
            message_lower = user_message.lower().strip()
            is_greeting = any(greeting in message_lower for greeting in greeting_patterns)
            
            if is_greeting and len(user_message.strip()) <= 20:
                return get_welcome_menu()
            else:
                return get_ai_response(user_message)
            
    except Exception as e:
        logger.error(f"❌ Błąd przetwarzania wiadomości AI: {e}")
        return "😔 Wystąpił problem. Spróbuj ponownie lub zadzwoń: **123-456-789** 📞"

logger.info("🤖 Bot Logic AI zainicjalizowany - PEŁNA AI WERSJA")
logger.info(f"🔑 Together API: {'✅' if api_key else '❌'}")