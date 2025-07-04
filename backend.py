# backend.py - UZUPEŁNIONY O FACEBOOK INTEGRATION
from flask import Flask, request, jsonify
from flask_cors import CORS
from together import Together
import os
import logging
import re
import requests
import json

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

def process_ai_message(user_message):
    """Przetwórz wiadomość przez AI"""
    try:
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message}
        ]
        
        # Wywołaj AI
        response = client.chat.completions.create(
            model="deepseek-ai/DeepSeek-R1-Distill-Llama-70B-free",
            messages=messages,
            max_tokens=300,  # Krótsze odpowiedzi dla Messenger
            temperature=0.3  # Mniej kreatywności = bardziej konsekwentne odpowiedzi
        )
        
        raw_response = response.choices[0].message.content
        cleaned_response = clean_thinking_response(raw_response)
        
        return cleaned_response
        
    except Exception as e:
        logger.error(f"❌ Błąd AI: {e}")
        return "Przepraszam, wystąpił problem. Spróbuj ponownie lub zadzwoń: 123-456-789 📞"

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
                            ai_response = process_ai_message(message_text)
                            
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

if __name__ == '__main__':
    logger.info("🚀 Uruchamianie Smart FAQ Bot Backend...")
    logger.info(f"🔑 Facebook verify token: {FACEBOOK_VERIFY_TOKEN}")
    logger.info(f"📘 Facebook token configured: {bool(FACEBOOK_PAGE_ACCESS_TOKEN)}")
    
    # Dla developmentu
    app.run(debug=True, host='0.0.0.0', port=5000)