# backend.py
from flask import Flask, request, jsonify
from flask_cors import CORS
from together import Together
import os
import logging

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

@app.route('/api/chat', methods=['POST'])
def chat():
    try:
        # Sprawdź czy dane są prawidłowe
        if not request.json or 'messages' not in request.json:
            return jsonify({'error': 'Brak wiadomości w zapytaniu'}), 400
        
        data = request.json
        messages = data['messages']
        
        # Ogranicz liczbę wiadomości (bezpieczeństwo)
        if len(messages) > 20:
            messages = messages[-20:]
        
        # Wywołaj Together AI
        response = client.chat.completions.create(
            model="deepseek-ai/DeepSeek-R1-Distill-Llama-70B-free",
            messages=messages,
            max_tokens=500,
            temperature=0.7
        )
        
        return jsonify({
            'response': response.choices[0].message.content,
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
        'service': 'Smart FAQ Bot Backend'
    })

if __name__ == '__main__':
    # Dla developmentu
    app.run(debug=True, host='0.0.0.0', port=5000)