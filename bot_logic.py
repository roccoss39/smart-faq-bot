"""
Bot Logic - Logika konwersacji i zarządzania sesjami użytkowników
Obsługuje rezerwacje, AI responses i stan konwersacji
"""

import logging
import re
from datetime import datetime, timedelta
import pytz
from together import Together
import os
from calendar_service import get_available_slots, create_appointment

logger = logging.getLogger(__name__)

# ==============================================
# KONFIGURACJA AI
# ==============================================

# Sprawdź czy klucz API jest dostępny
api_key = os.getenv('TOGETHER_API_KEY')
if not api_key:
    logger.error("BŁĄD: Brak zmiennej środowiskowej TOGETHER_API_KEY")
    raise Exception("Brak Together API key")

client = Together(api_key=api_key)

# PROMPT SYSTEMOWY
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
Pamiętaj: NIE pokazuj procesu myślowego!
"""

# ==============================================
# SYSTEM SESJI UŻYTKOWNIKÓW
# ==============================================

user_sessions = {}

class UserSession:
    def __init__(self, user_id):
        self.user_id = user_id
        self.state = "start"  # start, booking, waiting_for_details, ready_to_book
        self.appointment_data = {}
        self.last_activity = datetime.now()
        
    def set_booking_details(self, day, time, service):
        """Ustaw szczegóły rezerwacji"""
        self.appointment_data = {
            'day': day,
            'time': time, 
            'service': service
        }
        self.state = "waiting_for_details"
        self.last_activity = datetime.now()
        
    def set_client_details(self, name, phone):
        """Ustaw dane klienta"""
        self.appointment_data['name'] = name
        self.appointment_data['phone'] = phone
        self.state = "ready_to_book"
        self.last_activity = datetime.now()
        
    def reset(self):
        """Resetuj sesję"""
        self.state = "start"
        self.appointment_data = {}
        self.last_activity = datetime.now()
        
    def is_expired(self, minutes=30):
        """Sprawdź czy sesja wygasła"""
        return (datetime.now() - self.last_activity).total_seconds() > (minutes * 60)

def get_user_session(user_id):
    """Pobierz lub utwórz sesję użytkownika"""
    if user_id not in user_sessions:
        user_sessions[user_id] = UserSession(user_id)
    
    session = user_sessions[user_id]
    
    # Sprawdź czy sesja nie wygasła
    if session.is_expired():
        logger.info(f"🕐 Sesja {user_id} wygasła - resetowanie")
        session.reset()
    
    return session

def cleanup_expired_sessions():
    """Usuń wygasłe sesje (wywołuj okresowo)"""
    expired_users = [
        user_id for user_id, session in user_sessions.items() 
        if session.is_expired()
    ]
    
    for user_id in expired_users:
        del user_sessions[user_id]
        logger.info(f"🗑️ Usunięto wygasłą sesję: {user_id}")

# ==============================================
# PARSOWANIE WIADOMOŚCI
# ==============================================

def parse_booking_message(message):
    """Wyciągnij szczegóły rezerwacji z wiadomości"""
    try:
        message_lower = message.lower().strip()
        logger.info(f"🔍 PARSING: '{message}' → '{message_lower}'")  # DEBUG
        
        # Znajdź dzień
        days_map = {
            'poniedziałek': 'Poniedziałek', 'poniedzialek': 'Poniedziałek', 'pon': 'Poniedziałek',
            'wtorek': 'Wtorek', 'wt': 'Wtorek',
            'środa': 'Środa', 'sroda': 'Środa', 'śr': 'Środa', 'sr': 'Środa',
            'czwartek': 'Czwartek', 'czw': 'Czwartek',
            'piątek': 'Piątek', 'piatek': 'Piątek', 'pt': 'Piątek',
            'sobota': 'Sobota', 'sobote': 'Sobota', 'sb': 'Sobota'
        }
        
        day = None
        for day_key, day_value in days_map.items():
            if day_key in message_lower:
                day = day_value
                break
                
        # Znajdź godzinę (różne formaty)
        time_patterns = [
            r'(\d{1,2}):(\d{2})',                    # 10:00
            r'(\d{1,2})\.(\d{2})',                   # 10.00
            r'(\d{1,2}):(\d{0,2})',                  # 10: lub 10:0
            r'(\d{1,2})\s*h',                        # 10h
            r'godz\.?\s*(\d{1,2})',                  # godz 10
            r'o\s+(\d{1,2}):?(\d{0,2})',             # "o 10:00" lub "o 10"
            r'na\s+(\d{1,2}):?(\d{0,2})',            # "na 10:00"  ← DODAJ
            r'(\d{1,2}):?(\d{0,2})\s+na',            # "10:00 na"  ← DODAJ
        ]
        
        time = None
        for pattern in time_patterns:
            time_match = re.search(pattern, message_lower)
            if time_match:
                hour = int(time_match.group(1))
                minute = int(time_match.group(2)) if len(time_match.groups()) > 1 and time_match.group(2) else 0
                
                # Walidacja godziny
                if 9 <= hour <= 19:  # Godziny pracy
                    time = f"{hour:02d}:{minute:02d}"
                    break
                    
        # Znajdź usługę
        services_map = {
            'strzyżenie męskie': 'Strzyżenie męskie',
            'strzyżenie damskie': 'Strzyżenie damskie',
            'strzyżenie': 'Strzyżenie',
            'strzyenie': 'Strzyżenie',  # literówka
            'farbowanie': 'Farbowanie',
            'farba': 'Farbowanie',
            'pasemka': 'Pasemka',
            'refleksy': 'Refleksy',
            'koloryzacja': 'Koloryzacja',
            'ombre': 'Ombre',
            'baleyage': 'Baleyage'
        }
        
        service = 'Strzyżenie'  # domyślnie
        for service_key, service_value in services_map.items():
            if service_key in message_lower:
                service = service_value
                break
                
        if day and time:
            return {
                'day': day,
                'time': time,
                'service': service
            }
            
        return None
        
    except Exception as e:
        logger.error(f"❌ Błąd parsowania rezerwacji: {e}")
        return None

def parse_contact_data(message):
    """Wyciągnij dane kontaktowe z wiadomości"""
    try:
        message = message.strip()
        
        # Różne wzorce dla danych kontaktowych
        patterns = [
            # "Jan Kowalski, 123456789"
            r'([A-ZĄĆĘŁŃÓŚŹŻ][a-ząćęłńóśźż]+)\s+([A-ZĄĆĘŁŃÓŚŹŻ][a-ząćęłńóśźż]+)[,\s]+(\d{9}|\d{3}[-\s]\d{3}[-\s]\d{3})',
            # "Jan Kowalski 123456789"  
            r'([A-ZĄĆĘŁŃÓŚŹŻ][a-ząćęłńóśźż]+)\s+([A-ZĄĆĘŁŃÓŚŹŻ][a-ząćęłńóśźż]+)\s+(\d{9}|\d{3}[-\s]\d{3}[-\s]\d{3})',
            # "Jan Kowalski tel: 123456789"
            r'([A-ZĄĆĘŁŃÓŚŹŻ][a-ząćęłńóśźż]+)\s+([A-ZĄĆĘŁŃÓŚŹŻ][a-ząćęłńóśźż]+)\s*tel\.?\s*:?\s*(\d{9}|\d{3}[-\s]\d{3}[-\s]\d{3})',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, message)
            if match:
                name = f"{match.group(1)} {match.group(2)}"
                phone = re.sub(r'[-\s]', '', match.group(3))
                
                # Walidacja telefonu (9 cyfr)
                if len(phone) == 9 and phone.isdigit():
                    return {
                        'name': name,
                        'phone': phone
                    }
            
        return None
        
    except Exception as e:
        logger.error(f"❌ Błąd parsowania kontaktu: {e}")
        return None

# ==============================================
# TWORZENIE WIZYT
# ==============================================

def create_booking(appointment_data):
    """Utwórz wizytę w kalendarzu Google"""
    try:
        # Konwertuj dane na datetime
        day_map = {
            'Poniedziałek': 0, 'Wtorek': 1, 'Środa': 2, 
            'Czwartek': 3, 'Piątek': 4, 'Sobota': 5
        }
        
        target_day = day_map.get(appointment_data['day'])
        if target_day is None:
            logger.error(f"❌ Nieprawidłowy dzień: {appointment_data['day']}")
            return False
            
        # Znajdź najbliższy dzień
        tz = pytz.timezone('Europe/Warsaw')
        now = datetime.now(tz)
        days_ahead = (target_day - now.weekday()) % 7
        if days_ahead == 0:  # Dzisiaj
            days_ahead = 7  # Następny tydzień
            
        appointment_date = now + timedelta(days=days_ahead)
        
        # Ustaw godzinę
        time_parts = appointment_data['time'].split(':')
        appointment_datetime = appointment_date.replace(
            hour=int(time_parts[0]), 
            minute=int(time_parts[1]), 
            second=0, 
            microsecond=0
        )
        
        # Sprawdź czy termin nie jest w przeszłości
        if appointment_datetime <= now:
            logger.error(f"❌ Termin w przeszłości: {appointment_datetime}")
            return False
        
        logger.info(f"📅 Tworzenie wizyty: {appointment_datetime} dla {appointment_data['name']}")
        
        # Utwórz wizytę w kalendarzu
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

# ==============================================
# CZYSZCZENIE ODPOWIEDZI AI
# ==============================================

# ZASTĄP funkcję clean_thinking_response:

def clean_thinking_response(response_text):
    """Usuwa sekcje 'thinking' z odpowiedzi modelu DeepSeek-R1"""
    if not response_text:
        return ""
        
    original = response_text
    cleaned = response_text
    
    # SZCZEGÓLNE TRAKTOWANIE NIEDOMKNIĘTEGO <think>
    # Znajdź wszystko po ostatnim </think> lub <think> 
    
    # Jeśli jest <think> ale nie ma </think>, weź tylko tekst po <think>
    if '<think>' in cleaned.lower() and '</think>' not in cleaned.lower():
        # Znajdź indeks ostatniego <think>
        think_pattern = re.compile(r'<think[^>]*>', re.IGNORECASE)
        matches = list(think_pattern.finditer(cleaned))
        if matches:
            # Weź tekst po ostatnim <think>
            last_match = matches[-1]
            after_think = cleaned[last_match.end():]
            
            # Sprawdź czy po <think> jest sensowna odpowiedź
            lines = after_think.strip().split('\n')
            for line in lines:
                line = line.strip()
                # Szukaj linii z jedną z poprawnych intencji
                if any(intent in line.upper() for intent in ["BOOKING", "SHOW_AVAILABLE", "GENERAL_BOOKING", "CONTACT_INFO", "CANCEL", "GENERAL"]):
                    cleaned = line
                    break
            else:
                # Jeśli nie znaleziono intencji, weź pierwszą sensowną linię
                for line in lines:
                    if len(line.strip()) > 0 and not line.strip().startswith('<'):
                        cleaned = line.strip()
                        break
    
    # Usuń wszystko między zamkniętymi tagami
    cleaned = re.sub(r'<thinking>.*?</thinking>', '', cleaned, flags=re.DOTALL | re.IGNORECASE)
    cleaned = re.sub(r'<THINK>.*?</THINK>', '', cleaned, flags=re.DOTALL | re.IGNORECASE)
    cleaned = re.sub(r'<think>.*?</think>', '', cleaned, flags=re.DOTALL | re.IGNORECASE)
    
    # Usuń ewentualne pozostałe tagi
    cleaned = re.sub(r'<[^>]*>', '', cleaned)
    
    # Usuń ewentualne puste linie
    cleaned = cleaned.strip()
    
    # Debug log
    if original != cleaned and len(original) > 50:
        logger.debug(f"🧹 Oczyszczono: '{original[:50]}...' → '{cleaned}'")
    
    return cleaned

# ==============================================
# GŁÓWNA LOGIKA BOTA
# ==============================================

def process_user_message(user_message, user_id=None):
    """
    GŁÓWNA FUNKCJA - Przetwórz wiadomość użytkownika z AI Intent Router
    """
    try:
        # Pobierz sesję użytkownika
        session = get_user_session(user_id) if user_id else None
        user_message = user_message.strip()
        
        logger.info(f"🤖 Przetwarzam: '{user_message}' | Sesja: {session.state if session else 'brak'}")
        
        # ===========================================
        # AI ANALYSIS INTENCJI
        # ===========================================
        
        intent = analyze_user_intent(user_message, session)
        
        # ===========================================
        # OBSŁUGA NA PODSTAWIE INTENCJI
        # ===========================================
        
        # 1. CONTACT_DATA - gdy klient podaje dane kontaktowe
        if intent == "CONTACT_DATA" and session and session.state == "waiting_for_details":
            contact_data = parse_contact_data(user_message)
            if contact_data:
                session.set_client_details(contact_data['name'], contact_data['phone'])
                
                # UTWÓRZ WIZYTĘ W KALENDARZU
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
        
        # 1.5. CANCELLING - weryfikacja danych do anulowania
        if session and session.state == "cancelling":
            cancellation_data = parse_cancellation_data(user_message)
            if cancellation_data:
                # TODO: Sprawdź w kalendarzu czy wizyta istnieje
                session.reset()
                return f"✅ **Wizyta anulowana**\n\n👤 Klient: {cancellation_data['name']}\n📞 Telefon: {cancellation_data['phone']}\n📅 Termin: {cancellation_data['day']} {cancellation_data['time']}\n\n🤖 Czy mogę w czymś jeszcze pomóc?"
            else:
                return f"📝 **Błędny format!**\n\nPodaj w formacie:\n**\"Imię Nazwisko, telefon, dzień godzina\"**\n\nNp: *\"Jan Kowalski, 123456789, środa 11:00\"*"
        
        # 2. BOOKING - konkretna rezerwacja "umawiam się na wtorek 10:00"
        elif intent == "BOOKING":
            parsed = parse_booking_message(user_message)
            logger.info(f"🔍 PARSED BOOKING: {parsed}")
            
            if parsed and session:
                session.set_booking_details(parsed['day'], parsed['time'], parsed['service'])
                return f"📝 **Prawie gotowe!**\n\n📅 **Termin:** {parsed['day']} {parsed['time']}\n✂️ **Usługa:** {parsed['service']}\n\n🔔 Potrzebuję jeszcze:\n• 👤 **Imię i nazwisko**\n• 📞 **Numer telefonu**\n\nNapisz: **\"Jan Kowalski, 123456789\"**"
            else:
                return f"📝 **Nie mogę rozpoznać terminu!**\n\nSprawdź format:\n**\"Umawiam się na [dzień] [godzina] na strzyżenie\"**\n\nNp: *\"Umawiam się na wtorek 10:00 na strzyżenie\"*"
        
        # 3. ASK_AVAILABILITY - pytanie o dostępne terminy
        elif intent == "ASK_AVAILABILITY":
            day_mentioned = extract_day_from_message(user_message)
            
            try:
                slots = get_available_slots(days_ahead=10)
                
                if day_mentioned:
                    day_slots = [slot for slot in slots if slot['day_name'] == day_mentioned]
                    if day_slots:
                        slots_text = '\n'.join([
                            f"• {slot['display'].split()[-1]}"
                            for slot in day_slots[:10]
                        ])
                        day_display = get_day_in_locative(day_mentioned)  # ← NOWA FUNKCJA
                        return f"📅 **Wolne terminy {day_display}:**\n{slots_text}\n\n💬 Aby się umówić napisz:\n**\"Umawiam się na {day_mentioned.lower()} [godzina] na strzyżenie\"** ✂️"
                    else:
                        other_days = [slot for slot in slots if slot['day_name'] != day_mentioned][:5]
                        if other_days:
                            slots_text = '\n'.join([
                                f"• {slot['day_name']} {slot['display'].split()[-1]}" 
                                for slot in other_days
                            ])
                            return f"😔 Brak wolnych terminów w {day_mentioned.lower()}.\n\n📅 **Dostępne w inne dni:**\n{slots_text}\n\n📞 Lub zadzwoń: **123-456-789**"
                        else:
                            return f"😔 Brak wolnych terminów w {day_mentioned.lower()}.\n📞 Zadzwoń: **123-456-789**"
                else:
                    if slots:
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
        
        # 4. WANT_APPOINTMENT - ogólne "chcę się umówić"
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
        
        # 5. CANCEL_VISIT - anulowanie z weryfikacją
        elif intent == "CANCEL_VISIT":
            if session and session.state == "waiting_for_details" and session.appointment_data:
                # User ma aktywną rezerwację - anuluj ją
                appointment_info = session.appointment_data
                session.reset()
                return f"❌ **Anulowano rezerwację**\n\n📅 Termin: {appointment_info['day']} {appointment_info['time']}\n✂️ Usługa: {appointment_info['service']}\n\n🤖 Mogę Ci w czymś jeszcze pomóc?"
            else:
                # Pytaj o szczegóły wizyty do anulowania
                if session:
                    session.state = "cancelling"
                return f"❌ **Anulowanie wizyty**\n\n🔍 Aby anulować wizytę, podaj:\n• 👤 **Imię i nazwisko**\n• 📞 **Numer telefonu**\n• 📅 **Dzień i godzinę wizyty**\n\nNp: *\"Jan Kowalski, 123456789, środa 11:00\"*"
        
        # 6. OTHER_QUESTION - standardowa rozmowa AI
        else:  # OTHER_QUESTION
            return get_ai_response(user_message)
            
    except Exception as e:
        logger.error(f"❌ Błąd przetwarzania wiadomości: {e}")
        return "😔 Wystąpił problem. Spróbuj ponownie lub zadzwoń: **123-456-789** 📞"

# ===========================================
# DODAJ POMOCNICZE FUNKCJE
# ===========================================

def extract_day_from_message(message):
    """Wyciągnij dzień z wiadomości"""
    days_map = {
        'poniedziałek': 'Poniedziałek', 'poniedzialek': 'Poniedziałek', 'pon': 'Poniedziałek',
        'wtorek': 'Wtorek', 'wt': 'Wtorek',
        'środa': 'Środa', 'sroda': 'Środa', 'śr': 'Środa',
        'czwartek': 'Czwartek', 'czw': 'Czwartek',
        'piątek': 'Piątek', 'piatek': 'Piątek', 'pt': 'Piątek',
        'sobota': 'Sobota', 'sobote': 'Sobota', 'sb': 'Sobota'
    }
    
    message_lower = message.lower()
    for day_key, day_value in days_map.items():
        if day_key in message_lower:
            return day_value
    return None

def get_ai_response(user_message):
    """Standardowa odpowiedź AI"""
    try:
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message}
        ]
        
        response = client.chat.completions.create(
            model="deepseek-ai/DeepSeek-R1-Distill-Llama-70B-free",  # ← POWRÓT DO R1
            messages=messages,
            max_tokens=600,
            temperature=0.3
        )
        
        raw_response = response.choices[0].message.content
        cleaned_response = clean_thinking_response(raw_response)
        
        # Sprawdź czy jest czysta odpowiedź
        if len(cleaned_response.strip()) > 10:
            return cleaned_response.strip()
        else:
            return "😊 Dzień dobry! Jak mogę pomóc? Zapraszamy do salonu Kleopatra na ul. Pięknej 15! 💇‍♀️"
        
    except Exception as e:
        logger.error(f"❌ Błąd AI response: {e}")
        return "😔 Przepraszam, chwilowo mam problemy z odpowiadaniem. Zadzwoń: **123-456-789** 📞"

# ZASTĄP funkcję analyze_user_intent:

def analyze_user_intent(user_message):
    """Analizuj intencję użytkownika za pomocą AI"""
    intent_prompt = f"""Classify this Polish message into ONE category.

MESSAGE: "{user_message}"

CATEGORIES:

**BOOKING** - Specific booking with BOTH day AND time mentioned
Examples: "umawiam się na wtorek 10:00", "środa 15:30", "poniedziałek o 11:00"

**ASK_AVAILABILITY** - Asking about available appointment times
Examples: "kiedy mają państwo wolne terminy?", "dostępne godziny na wtorek?", "jakie są wolne terminy?"

**WANT_APPOINTMENT** - General booking request WITHOUT specific time
Examples: "chce sie ostrzyc", "chcę się umówić", "potrzebuję wizyty"

**CONTACT_DATA** - Personal contact details
Examples: "Jan Kowalski, 123456789", "Anna Nowak 987-654-321"

**CANCEL_VISIT** - Cancel appointment request
Examples: "anuluj", "rezygnuję", "odwołuję wizytę"

**OTHER_QUESTION** - Other questions about salon, greetings
Examples: "cześć", "ile kosztuje strzyżenie?", "gdzie jesteście?"

IMPORTANT RULES:
- If message has day AND time → BOOKING
- If only general appointment request → WANT_APPOINTMENT  
- If asking about availability → ASK_AVAILABILITY

ANSWER: Write ONLY the category name (e.g. BOOKING, WANT_APPOINTMENT, etc.)"""

    try:
        response = client.chat.completions.create(
            model="deepseek-ai/DeepSeek-R1-Distill-Llama-70B-free",
            messages=[{"role": "user", "content": intent_prompt}],
            max_tokens=1000,
            temperature=0.0
        )
        
        raw_intent = response.choices[0].message.content
        
        # DEBUG: Pokaż pełną odpowiedź
        print(f"🔍 FULL RAW RESPONSE:")
        print(f"'{raw_intent}'")
        print(f"🔍 LENGTH: {len(raw_intent)}")
        
        # NOWE NAZWY KATEGORII
        valid_intents = ["BOOKING", "ASK_AVAILABILITY", "WANT_APPOINTMENT", "CONTACT_DATA", "CANCEL_VISIT", "OTHER_QUESTION"]
        
        # SZUKAJ OSTATNIEJ LINII Z INTENCJĄ
        lines = raw_intent.split('\n')
        found_intent = None
        
        for line in reversed(lines):
            line_clean = line.strip().upper()
            if line_clean in valid_intents:
                found_intent = line_clean
                print(f"🎯 FOUND INTENT IN LINE: '{line_clean}'")
                break
        
        # Jeśli nie znaleziono w osobnej linii, szukaj jako ostatnie słowo
        if not found_intent:
            for intent in valid_intents:
                if raw_intent.upper().strip().endswith(intent):
                    found_intent = intent
                    print(f"🎯 FOUND INTENT AT END: '{intent}'")
                    break
        
        # Jeśli nadal nie znaleziono, szukaj w całym tekście
        if not found_intent:
            for intent in valid_intents:
                if intent in raw_intent.upper():
                    found_intent = intent
                    print(f"🎯 FOUND INTENT ANYWHERE: '{intent}'")
                    break
        
        if found_intent:
            logger.info(f"🎯 Intent rozpoznany: '{user_message}' → {found_intent}")
            return found_intent
        
        # Fallback
        logger.warning(f"🤔 Nierozpoznana intencja dla '{user_message}' → OTHER_QUESTION")
        print(f"❌ NO INTENT FOUND, DEFAULTING TO OTHER_QUESTION")
        return "OTHER_QUESTION"
        
    except Exception as e:
        logger.error(f"❌ Błąd analizy intencji: {e}")
        return "OTHER_QUESTION"

# ==============================================
# FUNKCJE POMOCNICZE
# ==============================================

def get_session_info(user_id):
    """Pobierz informacje o sesji użytkownika (dla debugowania)"""
    if user_id in user_sessions:
        session = user_sessions[user_id]
        return {
            'state': session.state,
            'appointment_data': session.appointment_data,
            'last_activity': session.last_activity.isoformat()
        }
    return None

def reset_user_session(user_id):
    """Resetuj sesję użytkownika"""
    if user_id in user_sessions:
        user_sessions[user_id].reset()
        return True
    return False

def get_active_sessions_count():
    """Zwróć liczbę aktywnych sesji"""
    return len(user_sessions)

# ==============================================
# INICJALIZACJA
# ==============================================

logger.info("🤖 Bot Logic zainicjalizowany")
logger.info(f"🔑 Together API: {'✅' if api_key else '❌'}")

def get_day_in_locative(day_name):
    """Zwróć dzień w miejscowniku (w + dzień)"""
    locative_map = {
        'Poniedziałek': 'w poniedziałek',
        'Wtorek': 'we wtorek', 
        'Środa': 'w środę',
        'Czwartek': 'w czwartek',
        'Piątek': 'w piątek',
        'Sobota': 'w sobotę'
    }
    return locative_map.get(day_name, f'w {day_name.lower()}')

def get_day_in_accusative(day_name):
    """Zwróć dzień w bierniku (na + dzień)"""
    accusative_map = {
        'Poniedziałek': 'poniedziałek',
        'Wtorek': 'wtorek',
        'Środa': 'środę', 
        'Czwartek': 'czwartek',
        'Piątek': 'piątek',
        'Sobota': 'sobotę'
    }
    return accusative_map.get(day_name, day_name.lower())

# DODAJ NOWĄ FUNKCJĘ parse_cancellation_data:

def parse_cancellation_data(message):
    """Wyciągnij dane do anulowania wizyty"""
    try:
        # Wzorce dla: "Jan Kowalski, 123456789, środa 11:00"
        patterns = [
            r'([A-ZĄĆĘŁŃÓŚŹŻ][a-ząćęłńóśźż]+)\s+([A-ZĄĆĘŁŃÓŚŹŻ][a-ząćęłńóśźż]+)[,\s]+(\d{9}|\d{3}[-\s]\d{3}[-\s]\d{3})[,\s]+([a-ząćęłńóśźż]+)\s+(\d{1,2}):?(\d{0,2})',
            r'([A-ZĄĆĘŁŃÓŚŹŻ][a-ząćęłńóśźż]+)\s+([A-ZĄĆĘŁŃÓŚŹŻ][a-ząćęłńóśźż]+)[,\s]+(\d{9})[,\s]+([a-ząćęłńóśźż]+)\s+(\d{1,2}):?(\d{0,2})'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, message)
            if match:
                name = f"{match.group(1)} {match.group(2)}"
                phone = re.sub(r'[-\s]', '', match.group(3))
                day_raw = match.group(4).lower()
                hour = int(match.group(5))
                minute = int(match.group(6)) if match.group(6) else 0
                
                # Mapuj dzień
                days_map = {
                    'poniedziałek': 'Poniedziałek', 'pon': 'Poniedziałek',
                    'wtorek': 'Wtorek', 'wt': 'Wtorek',
                    'środa': 'Środa', 'środę': 'Środa', 'sr': 'Środa',
                    'czwartek': 'Czwartek', 'czw': 'Czwartek',
                    'piątek': 'Piątek', 'pt': 'Piątek',
                    'sobota': 'Sobota', 'sobotę': 'Sobota', 'sb': 'Sobota'
                }
                
                day = days_map.get(day_raw)
                time = f"{hour:02d}:{minute:02d}"
                
                if day and len(phone) == 9:
                    return {
                        'name': name,
                        'phone': phone,
                        'day': day,
                        'time': time
                    }
        
        return None
        
    except Exception as e:
        logger.error(f"❌ Błąd parsowania anulowania: {e}")
        return None