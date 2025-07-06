"""
Backend - Flask server z webhook'ami Facebook
Obsługuje tylko komunikację, logika w bot_logic.py
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import logging
import requests
import json
import time
from dotenv import load_dotenv

# IMPORT LOGIKI BOTA
from bot_logic import process_user_message, clean_thinking_response, SYSTEM_PROMPT, client

# Załaduj zmienne z .env
load_dotenv()

# Konfiguracja logowania 
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# ==============================================
# FACEBOOK WEBHOOK CONFIGURATION
# ==============================================

FACEBOOK_VERIFY_TOKEN = os.getenv('FACEBOOK_VERIFY_TOKEN', 'Qweqweqwe1')
FACEBOOK_PAGE_ACCESS_TOKEN = os.getenv('FACEBOOK_PAGE_ACCESS_TOKEN')
FACEBOOK_PAGE_ID = os.getenv('FACEBOOK_PAGE_ID')

# Sprawdź czy wszystkie klucze są dostępne
required_vars = ['FACEBOOK_PAGE_ACCESS_TOKEN', 'TOGETHER_API_KEY']
missing_vars = [var for var in required_vars if not os.getenv(var)]

if missing_vars:
    logger.error(f"❌ Brakujące zmienne środowiskowe: {missing_vars}")
    logger.error("💡 Sprawdź plik .env")
else:
    logger.info("✅ Wszystkie zmienne środowiskowe załadowane")

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

# ==============================================
# FACEBOOK MESSAGING
# ==============================================

def send_facebook_message(recipient_id, message_text):
    """Wyślij wiadomość przez Facebook Messenger"""
    if not FACEBOOK_PAGE_ACCESS_TOKEN:
        logger.error("Brak Facebook Page Access Token")
        return False
        
    try:
        # Ogranicz długość wiadomości (Facebook limit: 2000 znaków)
        if len(message_text) > 1500:  # Bezpieczny limit
            # Podziel na części
            parts = [message_text[i:i+1500] for i in range(0, len(message_text), 1500)]
            for i, part in enumerate(parts):
                if i > 0:  # Przerwa między częściami
                    time.sleep(0.5)
                success = _send_single_message(recipient_id, part)
                if not success:
                    return False
            return True
        else:
            return _send_single_message(recipient_id, message_text)
            
    except Exception as e:
        logger.error(f"❌ Błąd Facebook API: {e}")
        return False

def _send_single_message(recipient_id, message_text):
    """Wyślij pojedynczą wiadomość"""
    try:
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
        logger.error(f"❌ Błąd wysyłania wiadomości: {e}")
        return False

# ==============================================
# FACEBOOK WEBHOOK ENDPOINTS
# ==============================================

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
                            
                            # PRZETWÓRZ PRZEZ BOT LOGIC
                            ai_response = process_user_message(message_text, sender_id)
                            
                            # Wyślij odpowiedź
                            send_facebook_message(sender_id, ai_response)
            
            return "OK", 200
            
        except Exception as e:
            logger.error(f"❌ Błąd webhook: {e}")
            return "Error", 500

# ==============================================
# WEB CHAT API ENDPOINTS (dla strony www)
# ==============================================

@app.route('/api/chat', methods=['POST'])
def chat():
    """API endpoint dla chat'a na stronie www"""
    try:
        if not request.json or 'messages' not in request.json:
            return jsonify({'error': 'Brak wiadomości w zapytaniu'}), 400
        
        data = request.json
        user_messages = data['messages']
        
        # Pobierz ostatnią wiadomość użytkownika
        if user_messages:
            last_message = user_messages[-1]
            user_message = last_message.get('content', '')
            
            # Użyj bot logic (bez user_id dla web chat)
            response_text = process_user_message(user_message, user_id=None)
            
            return jsonify({
                'response': response_text,
                'status': 'success'
            })
        else:
            return jsonify({'error': 'Brak wiadomości'}), 400
        
    except Exception as e:
        logger.error(f"Błąd API: {str(e)}")
        return jsonify({
            'error': 'Wystąpił błąd serwera',
            'status': 'error'
        }), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    try:
        from bot_logic import get_active_sessions_count
        return jsonify({
            'status': 'ok',
            'service': 'Smart FAQ Bot Backend + Facebook Messenger',
            'model': 'deepseek-ai/DeepSeek-R1-Distill-Llama-70B-free',
            'facebook_configured': bool(FACEBOOK_PAGE_ACCESS_TOKEN),
            'verify_token': FACEBOOK_VERIFY_TOKEN,
            'active_sessions': get_active_sessions_count(),
            'calendar_service': 'enabled'
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

# ==============================================
# DEBUG ENDPOINTS (opcjonalne)
# ==============================================

@app.route('/api/debug/sessions', methods=['GET'])
def debug_sessions():
    """Debug endpoint - pokaż aktywne sesje"""
    try:
        from bot_logic import user_sessions
        sessions_info = {}
        for user_id, session in user_sessions.items():
            sessions_info[user_id] = {
                'state': session.state,
                'appointment_data': session.appointment_data,
                'last_activity': session.last_activity.isoformat()
            }
        return jsonify({
            'active_sessions': len(sessions_info),
            'sessions': sessions_info
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/debug/reset/<user_id>', methods=['POST'])
def debug_reset_session(user_id):
    """Debug endpoint - resetuj sesję użytkownika"""
    try:
        from bot_logic import reset_user_session
        success = reset_user_session(user_id)
        return jsonify({
            'success': success,
            'message': f'Sesja {user_id} {"zresetowana" if success else "nie znaleziona"}'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ==============================================
# MAIN
# ==============================================

if __name__ == '__main__':
    logger.info("🚀 Uruchamianie Smart FAQ Bot Backend...")
    logger.info(f"🔑 Facebook verify token: {FACEBOOK_VERIFY_TOKEN}")
    logger.info(f"📘 Facebook token configured: {bool(FACEBOOK_PAGE_ACCESS_TOKEN)}")
    logger.info(f"🤖 Bot Logic: enabled")
    
    # Dla developmentu
    app.run(debug=True, host='0.0.0.0', port=5000)