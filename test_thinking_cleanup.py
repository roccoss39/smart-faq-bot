"""Test czyszczenia thinking tags"""

from bot_logic_ai import analyze_user_intent_ai_robust, clean_thinking_response_enhanced

def test_cleanup():
    print("🧪 TEST CZYSZCZENIA THINKING TAGS")
    print("-" * 50)
    
    # Przykłady odpowiedzi z thinking tags
    raw_responses = [
        "Okay, so I need to classify the client's message... CONTACT_DATA",
        "<think>Let me analyze this...</think>WANT_APPOINTMENT",
        "Looking at this message, I can see... OTHER_QUESTION",
        "BOOKING"  # Czysta odpowiedź
    ]
    
    for raw in raw_responses:
        cleaned = clean_thinking_response_enhanced(raw)
        print(f"RAW: '{raw[:50]}...'")
        print(f"CLEANED: '{cleaned}'")
        print()

def test_robust_classification():
    print("🧪 TEST NIEZAWODNEJ KLASYFIKACJI")
    print("-" * 50)
    
    test_cases = [
        "Jan Kowalski 123456789",
        "chcę się umówić", 
        "wolne terminy",
        "umawiam się na wtorek 10:00"
    ]
    
    for message in test_cases:
        result = analyze_user_intent_ai_robust(message)
        print(f"'{message}' → {result}")

if __name__ == "__main__":
    test_cleanup()
    test_robust_classification()