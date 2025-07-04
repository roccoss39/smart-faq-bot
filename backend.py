# backend.py
from flask import Flask, request, jsonify
from flask_cors import CORS
from together import Together
import os
import logging
import re

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

NASZ ZESPÓŁ:
- Anna Kowalska - Senior Stylist (10 lat doświadczenia)
  * Specjalizacja: koloryzacja, stylizacja ślubna
  * Tel. bezpośredni: 123-456-790
- Kasia Nowak - Hair Artist (8 lat doświadczenia)
  * Specjalizacja: strzyżenia kreatywne, przedłużanie włosów
  * Tel. bezpośredni: 123-456-791

CENNIK USŁUG:
STRZYŻENIE:
- Damskie (mycie + strzyżenie + styling): 80-120 zł
- Męskie: 50-70 zł
- Dziecięce (do 12 lat): 40 zł

KOLORYZACJA:
- Całościowe farbowanie: 120-180 zł
- Retusz odrostów: 80 zł
- Pasemka/refleksy: 150-250 zł
- Ombre/Balayage: 200-350 zł
- Rozjaśnianie: 180-300 zł

STYLIZACJA & PIELĘGNACJA:
- Mycie + styling: 60 zł
- Upięcie okolicznościowe: 80-120 zł
- Maseczka regenerująca: +30 zł
- Keratynowe prostowanie: 300 zł
- Przedłużanie włosów: od 400 zł

DODATKOWE INFORMACJE:
- Parking dostępny za salonem
- Płatność: gotówka, karta, BLIK
- Rezerwacja online: www.salon-kleopatra.pl/rezerwacja
- Social media: @salon_kleopatra (Instagram), Salon Kleopatra Warszawa (Facebook)

ZASADY KOMUNIKACJI:
1. Bądź miły, pomocny i profesjonalny
2. Używaj emoji, ale nie przesadzaj (max 2-3 na wiadomość)
3. Odpowiadaj krótko i konkretnie
4. Jeśli nie znasz odpowiedzi, przekieruj do recepcji (tel. 123-456-789)
5. Zawsze oferuj pomoc w umówieniu wizyty
6. W sytuacjach pilnych lub skomplikowanych, od razu przekierowuje do człowieka
7. Pamiętaj o godzinach otwarcia przy ustalaniu terminów

PRZYKŁADOWE SYTUACJE:
- Reklamacje → przekieruj do kierownika
- Pilne sprawy → połącz z recepcją
- Szczegółowe porady → umów konsultację ze stylistą
- Problemy techniczne → podaj alternatywny kontakt

Odpowiadaj TYLKO po polsku. Bądź pomocny i empatyczny.
Pamiętaj: NIE pokazuj procesu myślowego!
"""

def clean_thinking_response(response_text):
    """
    Usuwa sekcje 'thinking' z odpowiedzi modelu DeepSeek-R1
    """
    # Usuń wszystko między <thinking> i </thinking>
    cleaned = re.sub(r'<thinking>.*?</thinking>', '', response_text, flags=re.DOTALL)
    
    # Usuń inne możliwe markery
    cleaned = re.sub(r'<think>.*?</think>', '', cleaned, flags=re.DOTALL)
    
    # Usuń ewentualne puste linie na początku
    cleaned = cleaned.strip()
    
    # Jeśli nadal zawiera oznaki "thinking", spróbuj usunąć wszystko do pierwszego zdania po polsku
    if any(marker in cleaned.lower() for marker in ['thinking', 'let me', 'okay, the user']):
        # Znajdź pierwsze zdanie po polsku (zawierające polskie znaki lub słowa)
        polish_pattern = r'[ĄąĆćĘęŁłŃńÓóŚśŹźŻż]|(?:salon|fryzjer|kleopatra|warszawa|usług|cen)'
        match = re.search(polish_pattern, cleaned, re.IGNORECASE)
        if match:
            # Znajdź początek zdania zawierającego polskie elementy
            start_pos = max(0, cleaned.rfind('.', 0, match.start()) + 1)
            cleaned = cleaned[start_pos:].strip()
    
    return cleaned

@app.route('/api/chat', methods=['POST'])
def chat():
    try:
        # Sprawdź czy dane są prawidłowe
        if not request.json or 'messages' not in request.json:
            return jsonify({'error': 'Brak wiadomości w zapytaniu'}), 400
        
        data = request.json
        user_messages = data['messages']
        
        # Ogranicz liczbę wiadomości (bezpieczeństwo)
        if len(user_messages) > 20:
            user_messages = user_messages[-20:]
        
        # Przygotuj wiadomości z systemowym promptem
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT}
        ]
        
        # Dodaj wiadomości użytkownika (bez systemowych z frontend)
        for msg in user_messages:
            if msg.get('role') != 'system':  # Ignoruj systemowe z frontend
                messages.append(msg)
        
        logger.info(f"Wysyłam {len(messages)} wiadomości do API")
        
        # Wywołaj Together AI
        response = client.chat.completions.create(
            model="deepseek-ai/DeepSeek-R1-Distill-Llama-70B-free",
            messages=messages,
            max_tokens=500,
            temperature=0.5,  # Niższa temperatura = mniej "kreatywności"
            stream=False
        )
        
        # Pobierz odpowiedź
        raw_response = response.choices[0].message.content
        logger.info(f"Surowa odpowiedź: {raw_response[:100]}...")
        
        # Oczyść odpowiedź z "thinking"
        cleaned_response = clean_thinking_response(raw_response)
        logger.info(f"Oczyszczona odpowiedź: {cleaned_response[:100]}...")
        
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
        'service': 'Smart FAQ Bot Backend',
        'model': 'deepseek-ai/DeepSeek-R1-Distill-Llama-70B-free'
    })

if __name__ == '__main__':
    # Dla developmentu
    app.run(debug=True, host='0.0.0.0', port=5000)