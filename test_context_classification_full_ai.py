"""Test klasyfikacji z kontekstem sesji"""

from bot_logic_ai import analyze_user_intent_ai_robust, UserSession

def test_context_classification():
    print("🧪 TEST KLASYFIKACJI Z KONTEKSTEM SESJI")
    print("-" * 60)
    
    # Symuluj sesję anulowania
    session = UserSession("test_user")
    session.state = "cancelling"
    
    test_cases = [
        # Bez kontekstu
        ("Dawid Podziewski 222222222 czwartek 18", None, "CONTACT_DATA"),
        ("wtorek 10:00", None, "BOOKING"),
        
        # Z kontekstem anulowania  
        ("Dawid Podziewski 222222222 czwartek 18", session, "CONTACT_DATA"),
        ("Jan Kowalski 123456789 środa 15:00", session, "CONTACT_DATA"),
        
        # Z kontekstem booking
        ("Jan Kowalski 123456789", None, "CONTACT_DATA"),
    ]
    
    for message, sess, expected in test_cases:
        result = analyze_user_intent_ai_robust(message, sess)
        status = "✅" if result == expected else "❌"
        context = sess.state if sess else "brak"
        print(f"{status} '{message}' [sesja: {context}] → {result} (expected: {expected})")

if __name__ == "__main__":
    test_context_classification()