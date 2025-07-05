# backend.py - UZUPEŁNIONY O FACEBOOK INTEGRATION
from flask import Flask, request, jsonify
from flask_cors import CORS
from together import Together
import os
import logging
import re
import requests
import json
from calendar_service import get_calendar_service, get_available_slots, create_appointment

# Konfiguracja logowania 
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)  # Pozwoli na wywołania z przeglądarki

# Sprawdź czy klucz API jest dostępny
api_key = os.getenv('TOGETHER_API_KEY')
if not api_key:
    logger.error("BŁĄD: Brak zmiennej środowiskowej TOGETHER_API_KEY")
    exit(1)

client = Together(api_key=api_key)

# FACEBOOK WEBHOOK CONFIGURATION
FACEBOOK_VERIFY_TOKEN = os.getenv('FACEBOOK_VERIFY_TOKEN', 'kleopatra_bot_verify_2024')
FACEBOOK_PAGE_ACCESS_TOKEN = os.getenv('FACEBOOK_PAGE_ACCESS_TOKEN')

# Na górze pliku, po importach:

# SYSTEM SESJI UŻYTKOWNIKÓW
user_sessions = {}

class UserSession:
    def __init__(self, user_id):
        self.user_id = user_id
        self.state = "start"  # start, booking, waiting_for_details
        self.appointment_data = {}
        self.last_activity = None
        
    def set_booking_details(self, day, time, service):
        self.appointment_data = {
            'day': day,
            'time': time, 
            'service': service
        }
        self.state = "waiting_for_details"
        
    def set_client_details(self, name, phone):
        self.appointment_data['name'] = name
        self.appointment_data['phone'] = phone
        self.state = "ready_to_book"

def get_user_session(user_id):
    """Pobierz lub utwórz sesję użytkownika"""
    if user_id not in user_sessions:
        user_sessions[user_id] = UserSession(user_id)
    return user_sessions[user_id]

def get_page_id():
    """Pobierz ID strony z tokenu"""
    try:
        url = f"https://graph.facebook.com/v18.0/me"
        params = {'access_token': FACEBOOK_PAGE_ACCESS_TOKEN}
        response = requests.get(url, params=params)
        if response.status_code == 200:
            data = response.json()
            return data.get('id')
    except:
        pass
    return "750208294831428"  # fallback

PAGE_ID = get_page_id() if FACEBOOK_PAGE_ACCESS_TOKEN else "750208294831428"

# PROMPT SYSTEMOWY - przeniesiony z frontend
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

def clean_thinking_response(response_text):
    """Usuwa sekcje 'thinking' z odpowiedzi modelu DeepSeek-R1"""
    # Usuń wszystko między <thinking> i </thinking>
    cleaned = re.sub(r'<thinking>.*?</thinking>', '', response_text, flags=re.DOTALL)
    
    # Usuń inne możliwe markery
    cleaned = re.sub(r'<think>.*?</think>', '', cleaned, flags=re.DOTALL)
    
    # Usuń ewentualne puste linie na początku
    cleaned = cleaned.strip()
    
    return cleaned

def send_facebook_message(recipient_id, message_text):
    """Wyślij wiadomość przez Facebook Messenger"""
    if not FACEBOOK_PAGE_ACCESS_TOKEN:
        logger.error("Brak Facebook Page Access Token")
        return False
        
    try:
        # Ogranicz długość wiadomości (Facebook limit: 2000 znaków)
        if len(message_text) > 1900:
            message_text = message_text[:1897] + "..."
        
        # UŻYJ PAGE_ID ZAMIAST 'me'
        url = f"https://graph.facebook.com/v18.0/{PAGE_ID}/messages"
        payload = {
            'recipient': {'id': recipient_id},
            'message': {'text': message_text}
        }
        params = {'access_token': FACEBOOK_PAGE_ACCESS_TOKEN}
        
        response = requests.post(url, json=payload, params=params)
        
        if response.status_code == 200:
            logger.info(f"✅ Wiadomość wysłana do {recipient_id}: '{message_text[:50]}...'")
            return True
        else:
            logger.error(f"❌ Błąd wysyłania: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Błąd Facebook API: {e}")
        return False

def process_ai_message(user_message, user_id=None):
    """Przetwórz wiadomość przez AI z obsługą kalendarza i sesji"""
    try:
        # Pobierz sesję użytkownika
        session = get_user_session(user_id) if user_id else None
        
        # === OBSŁUGA REZERWACJI KROK PO KROKU ===
        
        # KROK 1: Sprawdź czy użytkownik chce się umówić
        booking_keywords = ['umów', 'wizyta', 'termin', 'rezerwacja', 'zapisać', 'appointment', 'wolne terminy', 'spotkanie']
        if any(word in user_message.lower() for word in booking_keywords):
            slots = get_available_slots(days_ahead=5)
            if slots:
                if session:
                    session.state = "booking"
                slots_text = '\n'.join([
                    f"• {slot['day_name']} {slot['display'].split()[-1]}" 
                    for slot in slots[:8]
                ])
                return f"📅 **Dostępne terminy:**\n{slots_text}\n\n💬 Napisz:\n**\"Umawiam się na [dzień] [godzina] na [usługa]\"**\n\nNp: *\"Umawiam się na poniedziałek 12:00 na strzyżenie\"* ✂️"
            else:
                return "😔 Brak wolnych terminów w najbliższych dniach.\n📞 Zadzwoń: **123-456-789**"
        
        # KROK 2: Parsing konkretnej rezerwacji
        booking_patterns = ['umawiam się', 'rezerwuję', 'chcę na', 'zapisz mnie']
        if any(pattern in user_message.lower() for pattern in booking_patterns):
            # Spróbuj wyciągnąć szczegóły z wiadomości
            parsed = parse_booking_message(user_message)
            if parsed and session:
                session.set_booking_details(parsed['day'], parsed['time'], parsed['service'])
                return f"📝 **Prawie gotowe!**\n\n📅 **Termin:** {parsed['day']} {parsed['time']}\n✂️ **Usługa:** {parsed['service']}\n\n🔔 Potrzebuję jeszcze:\n• 👤 **Imię i nazwisko**\n• 📞 **Numer telefonu**\n\nNapisz: **\"Jan Kowalski, 123-456-789\"**"
            else:
                return f"📝 **Prawie gotowe!**\n\nPotrzebuję jeszcze:\n• 👤 **Imię i nazwisko**\n• 📞 **Numer telefonu**\n\nNapisz: **\"Jan Kowalski, 123-456-789\"**"
        
        # KROK 3: Sprawdź czy podaje dane kontaktowe
        if session and session.state == "waiting_for_details":
            contact_data = parse_contact_data(user_message)
            if contact_data:
                session.set_client_details(contact_data['name'], contact_data['phone'])
                
                # UTWÓRZ WIZYTĘ W KALENDARZU
                appointment_result = create_booking(session.appointment_data)
                
                if appointment_result:
                    # Reset sesji
                    session.state = "start"
                    return f"✅ **WIZYTA POTWIERDZONA!**\n\n📅 **Termin:** {session.appointment_data['day']} {session.appointment_data['time']}\n👤 **Klient:** {contact_data['name']}\n📞 **Telefon:** {contact_data['phone']}\n✂️ **Usługa:** {session.appointment_data['service']}\n\n📍 **Salon Kleopatra**\nul. Piękna 15, Warszawa\n\n🎉 Do zobaczenia w salonie!"
                else:
                    return f"❌ **Błąd rezerwacji**\n\nTermin mógł zostać zajęty przez kogoś innego.\n📞 Zadzwoń: **123-456-789**"
            else:
                return f"📝 **Błędny format!**\n\nNapisz w formacie:\n**\"Imię Nazwisko, numer telefonu\"**\n\nNp: **\"Jan Kowalski, 123-456-789\"**"
        
        # === STANDARDOWA OBSŁUGA AI ===
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message}
        ]
        
        response = client.chat.completions.create(
            model="deepseek-ai/DeepSeek-R1-Distill-Llama-70B-free",
            messages=messages,
            max_tokens=300,
            temperature=0.3
        )
        
        raw_response = response.choices[0].message.content
        cleaned_response = clean_thinking_response(raw_response)
        
        return cleaned_response
        
    except Exception as e:
        logger.error(f"❌ Błąd AI: {e}")
        return "😔 Wystąpił problem. Spróbuj ponownie lub zadzwoń: **123-456-789** 📞"

# ================================
# FACEBOOK WEBHOOK ENDPOINTS
# ================================

@app.route('/', methods=['GET', 'POST'])
def webhook():
    """Główny endpoint dla Facebook webhook"""
    
    if request.method == 'GET':
        # WERYFIKACJA WEBHOOK PRZEZ FACEBOOK
        verify_token = request.args.get('hub.verify_token')
        challenge = request.args.get('hub.challenge')
        
        logger.info(f"🔍 Facebook weryfikuje webhook. Token: {verify_token}")
        
        if verify_token == FACEBOOK_VERIFY_TOKEN:
            logger.info("✅ Webhook zweryfikowany przez Facebook!")
            return challenge
        else:
            logger.error(f"❌ Nieprawidłowy token weryfikacji. Oczekiwano: {FACEBOOK_VERIFY_TOKEN}")
            return "Unauthorized", 401
    
    elif request.method == 'POST':
        # OBSŁUGA WIADOMOŚCI Z FACEBOOK MESSENGER
        try:
            data = request.json
            logger.info(f"📨 Webhook data: {json.dumps(data, indent=2)}")
            
            if data.get('object') == 'page':
                for entry in data.get('entry', []):
                    for messaging_event in entry.get('messaging', []):
                        
                        # Sprawdź czy to wiadomość tekstowa (NIE echo)
                        if (messaging_event.get('message') and 
                            messaging_event['message'].get('text') and 
                            not messaging_event['message'].get('is_echo')):
                            
                            sender_id = messaging_event['sender']['id']
                            message_text = messaging_event['message']['text']
                            
                            logger.info(f"💬 Wiadomość od {sender_id}: {message_text}")
                            
                            # Przetwórz przez AI
                            ai_response = process_ai_message(message_text, sender_id)
                            
                            # Wyślij odpowiedź
                            send_facebook_message(sender_id, ai_response)
            
            return "OK", 200
            
        except Exception as e:
            logger.error(f"❌ Błąd webhook: {e}")
            return "Error", 500

# ================================
# EXISTING API ENDPOINTS (dla web chat)
# ================================

@app.route('/api/chat', methods=['POST'])
def chat():
    try:
        if not request.json or 'messages' not in request.json:
            return jsonify({'error': 'Brak wiadomości w zapytaniu'}), 400
        
        data = request.json
        user_messages = data['messages']
        
        if len(user_messages) > 20:
            user_messages = user_messages[-20:]
        
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        
        for msg in user_messages:
            if msg.get('role') != 'system':
                messages.append(msg)
        
        logger.info(f"Wysyłam {len(messages)} wiadomości do API")
        
        response = client.chat.completions.create(
            model="deepseek-ai/DeepSeek-R1-Distill-Llama-70B-free",
            messages=messages,
            max_tokens=500,
            temperature=0.5,
            stream=False
        )
        
        raw_response = response.choices[0].message.content
        cleaned_response = clean_thinking_response(raw_response)
        
        return jsonify({
            'response': cleaned_response,
            'status': 'success'
        })
        
    except Exception as e:
        logger.error(f"Błąd API: {str(e)}")
        return jsonify({
            'error': 'Wystąpił błąd serwera',
            'status': 'error'
        }), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'ok',
        'service': 'Smart FAQ Bot Backend + Facebook Messenger',
        'model': 'deepseek-ai/DeepSeek-R1-Distill-Llama-70B-free',
        'facebook_configured': bool(FACEBOOK_PAGE_ACCESS_TOKEN),
        'verify_token': FACEBOOK_VERIFY_TOKEN
    })

def parse_booking_message(message):
    """Wyciągnij szczegóły rezerwacji z wiadomości"""
    try:
        message_lower = message.lower()
        
        # Znajdź dzień
        days_map = {
            'poniedziałek': 'Poniedziałek', 'poniedzialek': 'Poniedziałek',
            'wtorek': 'Wtorek', 
            'środa': 'Środa', 'sroda': 'Środa',
            'czwartek': 'Czwartek',
            'piątek': 'Piątek', 'piatek': 'Piątek',
            'sobota': 'Sobota', 'sobote': 'Sobota'
        }
        
        day = None
        for day_key, day_value in days_map.items():
            if day_key in message_lower:
                day = day_value
                break
                
        # Znajdź godzinę (pattern HH:MM)
        import re
        time_match = re.search(r'(\d{1,2}):?(\d{0,2})', message)
        time = None
        if time_match:
            hour = time_match.group(1)
            minute = time_match.group(2) or "00"
            time = f"{hour}:{minute.zfill(2)}"
            
        # Znajdź usługę
        services_map = {
            'strzyżenie': 'Strzyżenie',
            'strzyżenie damskie': 'Strzyżenie damskie',
            'strzyżenie męskie': 'Strzyżenie męskie', 
            'farbowanie': 'Farbowanie',
            'pasemka': 'Pasemka',
            'refleksy': 'Refleksy'
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
        import re
        
        # Pattern: "Imię Nazwisko, telefon" lub "Imię Nazwisko telefon"
        pattern = r'([A-ZĄĆĘŁŃÓŚŹŻ][a-ząćęłńóśźż]+)\s+([A-ZĄĆĘŁŃÓŚŹŻ][a-ząćęłńóśźż]+)[,\s]+(\d{3}[-\s]?\d{3}[-\s]?\d{3}|\d{9})'
        
        match = re.search(pattern, message)
        if match:
            name = f"{match.group(1)} {match.group(2)}"
            phone = re.sub(r'[-\s]', '', match.group(3))
            return {
                'name': name,
                'phone': phone
            }
            
        return None
        
    except Exception as e:
        logger.error(f"❌ Błąd parsowania kontaktu: {e}")
        return None

def create_booking(appointment_data):
    """Utwórz wizytę w kalendarzu Google"""
    try:
        from datetime import datetime, timedelta
        import pytz
        
        # Konwertuj dane na datetime
        day_map = {
            'Poniedziałek': 0, 'Wtorek': 1, 'Środa': 2, 
            'Czwartek': 3, 'Piątek': 4, 'Sobota': 5
        }
        
        target_day = day_map.get(appointment_data['day'])
        if target_day is None:
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
        
        # Utwórz wizytę
        result = create_appointment(
            client_name=appointment_data['name'],
            client_phone=appointment_data['phone'],
            service_type=appointment_data['service'],
            appointment_time=appointment_datetime
        )
        
        return bool(result)
        
    except Exception as e:
        logger.error(f"❌ Błąd tworzenia wizyty: {e}")
        return False

if __name__ == '__main__':
    logger.info("🚀 Uruchamianie Smart FAQ Bot Backend...")
    logger.info(f"🔑 Facebook verify token: {FACEBOOK_VERIFY_TOKEN}")
    logger.info(f"📘 Facebook token configured: {bool(FACEBOOK_PAGE_ACCESS_TOKEN)}")
    
    # Dla developmentu
    app.run(debug=True, host='0.0.0.0', port=5000)