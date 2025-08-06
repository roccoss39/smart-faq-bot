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
# from bot_logic import process_user_message, clean_thinking_response, SYSTEM_PROMPT, client

#AI VERSION (nowa)
from bot_logic_ai import process_user_message_smart

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

processed_messages = set()  # Cache przetworzonych wiadomości
MAX_CACHE_SIZE = 1000       # Maksymalny rozmiar cache

def is_message_processed(message_id):
    """Sprawdź czy wiadomość została już przetworzona"""
    return message_id in processed_messages

def mark_message_processed(message_id):
    """Oznacz wiadomość jako przetworzoną"""
    processed_messages.add(message_id)
    
    # Ogranicz rozmiar cache
    if len(processed_messages) > MAX_CACHE_SIZE:
        # Usuń najstarsze elementy (simplified)
        oldest_items = list(processed_messages)[:100]
        for item in oldest_items:
            processed_messages.remove(item)

def handle_message(sender_id, message_text, message_id):
    """Obsłuż wiadomość z deduplikacją"""
    
    # 🔧 SPRAWDŹ CZY WIADOMOŚĆ BYŁA JUŻ PRZETWORZONA:
    if is_message_processed(message_id):
        logger.info(f"🔄 Wiadomość już przetworzona: {message_id} - POMIJAM")
        return
    
    # Oznacz jako przetworzoną
    mark_message_processed(message_id)
    
    logger.info(f"💬 Wiadomość od {sender_id}: {message_text}")
    
    # Przetwórz wiadomość
    response = process_user_message_smart(message_text, sender_id)
    
    # 🔧 POPRAWKA - UŻYJ PRAWIDŁOWEJ NAZWY FUNKCJI:
    send_facebook_message(sender_id, response)
    logger.info(f"✅ Wiadomość wysłana do {sender_id}: '{response[:50]}...'")
    
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

# ==============================================
# FACEBOOK WEBHOOK ENDPOINTS
# ==============================================

@app.route('/', methods=['GET'])
def webhook_verify():
    """Weryfikacja webhook'a Facebook"""
    try:
        # Pobierz parametry z zapytania
        mode = request.args.get('hub.mode')
        challenge = request.args.get('hub.challenge')
        verify_token = request.args.get('hub.verify_token')
        
        logger.info(f"🔍 Weryfikacja webhook: mode={mode}, token={verify_token}")
        
        # Sprawdź czy to żądanie weryfikacji
        if mode == 'subscribe' and verify_token == FACEBOOK_VERIFY_TOKEN:
            logger.info("✅ Webhook zweryfikowany pomyślnie!")
            return challenge, 200
        else:
            logger.error(f"❌ Weryfikacja nieudana: oczekiwano '{FACEBOOK_VERIFY_TOKEN}', otrzymano '{verify_token}'")
            return 'Błąd weryfikacji', 403
            
    except Exception as e:
        logger.error(f"❌ Błąd weryfikacji webhook: {e}")
        return 'Błąd serwera', 500

@app.route('/', methods=['POST'])
def webhook():
    """Obsługa wiadomości Facebook"""
    data = request.get_json()
    
    # Log przychodzących danych
    logger.info(f"📨 Webhook data: {json.dumps(data, indent=2, ensure_ascii=False)}")
    
    if data['object'] == 'page':
        for entry in data['entry']:
            for messaging_event in entry['messaging']:
                
                # 🔧 SPRAWDŹ CZY TO WIADOMOŚĆ TEKSTOWA:
                if 'message' in messaging_event and 'text' in messaging_event['message']:
                    
                    # 🔧 POMIJAJ ECHO WIADOMOŚCI (wiadomości wysłane przez bota):
                    if messaging_event['message'].get('is_echo', False):
                        logger.info("🔄 Echo wiadomości - pomijam")
                        continue
                    
                    sender_id = messaging_event['sender']['id']
                    message_text = messaging_event['message']['text']
                    message_id = messaging_event['message']['mid']  # ← KLUCZOWE!
                    
                    # 🔧 OBSŁUŻ Z DEDUPLIKACJĄ:
                    handle_message(sender_id, message_text, message_id)
                
                # Inne typy eventów (delivery, read, etc.)
                elif 'delivery' in messaging_event:
                    logger.info("📨 Delivery receipt - pomijam")
                elif 'read' in messaging_event:
                    logger.info("📨 Read receipt - pomijam")
                else:
                    logger.info(f"📨 Nieznany event: {messaging_event}")
    
    return 'OK', 200

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    try:
        # 🔧 ZMIEŃ IMPORT:
        from bot_logic_ai import user_conversations
        stats = {
            'total_sessions': len(user_conversations),
            'active_last_hour': len(user_conversations)
        }
        
        return jsonify({
            'status': 'ok',
            'service': 'Smart FAQ Bot Backend + Facebook Messenger (AI with Memory)',
            'model': 'deepseek-ai/DeepSeek-R1-Distill-Llama-70B-free',
            'facebook_configured': bool(FACEBOOK_PAGE_ACCESS_TOKEN),
            'verify_token': FACEBOOK_VERIFY_TOKEN,
            'active_sessions': stats['total_sessions'],
            'active_last_hour': stats['active_last_hour'],
            'memory_enabled': True,
            'calendar_service': 'enabled'
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

@app.route('/api/debug/sessions', methods=['GET'])
def debug_sessions():
    """Debug endpoint - pokaż aktywne sesje"""
    try:
        # 🔧 ZMIEŃ IMPORT:
        from bot_logic_ai import user_conversations
        
        conversations_info = {}
        for user_id, conversation in user_conversations.items():
            conversations_info[user_id] = {
                'conversation_length': len(conversation),
                'last_message': conversation[-1] if conversation else None
            }
        return jsonify({
            'active_conversations': len(user_conversations),
            'conversations': conversations_info
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/debug/reset/<user_id>', methods=['POST'])
def debug_reset_session(user_id):
    """Debug endpoint - resetuj sesję użytkownika"""
    try:
        # 🔧 NOWA FUNKCJA RESET Z PAMIĘCIĄ:
        from bot_logic_ai import user_conversations
        
        success = False        
        if user_id in user_conversations:
            del user_conversations[user_id]
            success = True
        
        return jsonify({
            'success': success,
            'message': f'Sesja i pamięć {user_id} {"zresetowana" if success else "nie znaleziona"}'
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