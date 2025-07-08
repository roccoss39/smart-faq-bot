"""
Test porównawczy: REGEX vs AI
"""

import bot_logic as regex_bot
import bot_logic_ai as ai_bot

def test_both_versions():
    print("🧪 TEST PORÓWNAWCZY: REGEX vs AI")
    print("=" * 60)
    
    test_cases = [
        "hej",
        "chce się umówić", 
        "Chce się umówić",
        "umawiam się na wtorek 10:00",
        "Jan Kowalski, 123456789",
        "wolne terminy",
        "godziny w środę",
        "anuluj wizytę",
        "ile kosztuje strzyżenie?",
        "gdzie jesteście?",
        "Jan Nowak, 987654321, piątek 15:00"
    ]
    
    for i, message in enumerate(test_cases, 1):
        print(f"\n{i}️⃣ USER: \"{message}\"")
        print("-" * 40)
        
        # REGEX VERSION
        try:
            regex_response = regex_bot.process_user_message(message, f'regex_user_{i}')
            print(f"🔧 REGEX: {regex_response[:80]}...")
        except Exception as e:
            print(f"🔧 REGEX: ERROR - {e}")
        
        # AI VERSION  
        try:
            ai_response = ai_bot.process_user_message(message, f'ai_user_{i}')
            print(f"🤖 AI: {ai_response[:80]}...")
        except Exception as e:
            print(f"🤖 AI: ERROR - {e}")

if __name__ == "__main__":
    test_both_versions()