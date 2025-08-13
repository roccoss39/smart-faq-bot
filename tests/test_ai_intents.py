"""
Testy AI klasyfikacji intencji - dokładna weryfikacja
"""

import os
import sys
sys.path.append('.')

from bot_logic_ai import analyze_user_intent_ai, UserSession

def test_ai_intent_classification():
    """Test wszystkich kategorii intencji AI"""
    
    print("🧪 TESTY AI KLASYFIKACJI INTENCJI")
    print("=" * 60)
    
    # DEFINICJA TESTÓW
    test_cases = [
        # CONTACT_DATA - dane kontaktowe
        {
            "category": "CONTACT_DATA",
            "messages": [
                "Jan Kowalski 123456789",
                "Anna Nowak, 987654321", 
                "Piotr Wiśniewski tel. 555666777",
                "Maria Kowalczyk 111222333",
                "nazywam się Adam Nowak, 444555666"
            ],
            "expected": "CONTACT_DATA"
        },
        
        # BOOKING - konkretny termin  
        {
            "category": "BOOKING",
            "messages": [
                "umawiam się na wtorek 10:00",
                "środa 15:30",
                "chcę na poniedziałek o 11:00",
                "rezerwuję piątek 14:00",
                "piątek o 16:00 na strzyżenie"
            ],
            "expected": "BOOKING"
        },
        
        # ASK_AVAILABILITY - pytania o dostępność
        {
            "category": "ASK_AVAILABILITY", 
            "messages": [
                "wolne terminy",
                "jakie macie wolne terminy?",
                "godziny w środę",
                "dostępność na wtorek", 
                "kiedy można się umówić?",
                "czy są jakieś wolne miejsca?"
            ],
            "expected": "ASK_AVAILABILITY"
        },
        
        # WANT_APPOINTMENT - ogólna chęć umówienia
        {
            "category": "WANT_APPOINTMENT",
            "messages": [
                "chcę się umówić",
                "Chce się umówić",  # ← PROBLEMATYCZNY PRZYPADEK!
                "potrzebuję wizyty",
                "umów mnie",
                "zapisać się",
                "szukam terminu",
                "mogę się zapisać?"
            ],
            "expected": "WANT_APPOINTMENT"
        },
        
        # CANCEL_VISIT - anulowanie
        {
            "category": "CANCEL_VISIT",
            "messages": [
                "anuluj wizytę",
                "chcę anulować wizytę",
                "rezygnuję z wizyty",
                "odwołuję termin", 
                "nie mogę przyjść",
                "chcę przełożyć wizytę"
            ],
            "expected": "CANCEL_VISIT"
        },
        
        # OTHER_QUESTION - pozostałe
        {
            "category": "OTHER_QUESTION",
            "messages": [
                "hej",
                "cześć", 
                "dzień dobry",
                "ile kosztuje strzyżenie?",
                "gdzie jesteście?",
                "godziny otwarcia",
                "jakie usługi oferujecie?",
                "kontakt"
            ],
            "expected": "OTHER_QUESTION"
        }
    ]
    
    # STATYSTYKI
    total_tests = 0
    passed_tests = 0
    failed_tests = []
    
    # TESTOWANIE
    for test_group in test_cases:
        category = test_group["category"]
        expected = test_group["expected"]
        messages = test_group["messages"]
        
        print(f"\n🎯 KATEGORIA: {category}")
        print("-" * 40)
        
        for message in messages:
            total_tests += 1
            
            # Test bez sesji
            result = analyze_user_intent_ai(message, session=None)
            
            if result == expected:
                status = "✅ PASS"
                passed_tests += 1
            else:
                status = "❌ FAIL"
                failed_tests.append({
                    "message": message,
                    "expected": expected, 
                    "got": result
                })
            
            print(f"{status} \"{message}\" → {result}")
    
    # WYNIKI
    print(f"\n{'='*60}")
    print(f"📊 WYNIKI TESTÓW AI KLASYFIKACJI")
    print(f"{'='*60}")
    print(f"✅ Zaliczone: {passed_tests}/{total_tests} ({passed_tests/total_tests*100:.1f}%)")
    print(f"❌ Błędne: {len(failed_tests)}/{total_tests} ({len(failed_tests)/total_tests*100:.1f}%)")
    
    if failed_tests:
        print(f"\n🔍 BŁĘDNE KLASYFIKACJE:")
        for i, fail in enumerate(failed_tests, 1):
            print(f"{i}. \"{fail['message']}\"")
            print(f"   Oczekiwano: {fail['expected']}")
            print(f"   Otrzymano: {fail['got']}")
    
    return passed_tests, total_tests

def test_ai_with_session_context():
    """Test AI z kontekstem sesji"""
    
    print(f"\n{'='*60}")
    print("🧪 TESTY AI Z KONTEKSTEM SESJI")
    print("=" * 60)
    
    # Sesja oczekująca danych kontaktowych
    session = UserSession("test_user")
    session.state = "waiting_for_details"
    session.appointment_data = {"day": "Wtorek", "time": "10:00", "service": "Strzyżenie"}
    
    contact_tests = [
        ("Jan Kowalski 123456789", "CONTACT_DATA"),
        ("Anna Nowak, 987654321", "CONTACT_DATA"),
        ("hej", "OTHER_QUESTION"),  # Powinno zostać OTHER_QUESTION mimo sesji
        ("wolne terminy", "ASK_AVAILABILITY")  # Powinno zostać ASK_AVAILABILITY
    ]
    
    print("\n🎯 SESJA: waiting_for_details (oczekuje danych kontaktowych)")
    print("-" * 50)
    
    session_passed = 0
    session_total = len(contact_tests)
    
    for message, expected in contact_tests:
        result = analyze_user_intent_ai(message, session)
        status = "✅ PASS" if result == expected else "❌ FAIL"
        print(f"{status} \"{message}\" → {result} (oczekiwano: {expected})")
        if result == expected:
            session_passed += 1
    
    print(f"\n📊 WYNIKI Z SESJĄ: {session_passed}/{session_total} ({session_passed/session_total*100:.1f}%)")
    
    return session_passed, session_total

def test_ai_parsing():
    """Test AI parsowania danych"""
    
    from bot_logic_ai import parse_contact_data_ai, parse_booking_message_ai
    
    print(f"\n{'='*60}")
    print("🧪 TESTY AI PARSOWANIA DANYCH")
    print("=" * 60)
    
    # Test parsowania kontaktów
    contact_cases = [
        ("Jan Kowalski 123456789", {"name": "Jan Kowalski", "phone": "123456789"}),
        ("Anna Nowak, 987-654-321", {"name": "Anna Nowak", "phone": "987654321"}),
        ("Piotr Wiśniewski tel. 555 666 777", {"name": "Piotr Wiśniewski", "phone": "555666777"}),
        ("chcę się umówić", None),  # Brak danych kontaktowych
        ("Jan 123456789", None),    # Brak nazwiska
        ("Jan Kowalski", None)      # Brak telefonu
    ]
    
    print("\n🎯 PARSOWANIE KONTAKTÓW:")
    print("-" * 30)
    
    contact_passed = 0
    for message, expected in contact_cases:
        result = parse_contact_data_ai(message)
        if result == expected:
            status = "✅ PASS"
            contact_passed += 1
        else:
            status = "❌ FAIL"
        
        print(f"{status} \"{message}\"")
        print(f"   Oczekiwano: {expected}")
        print(f"   Otrzymano: {result}")
        print()
    
    # Test parsowania rezerwacji
    booking_cases = [
        ("umawiam się na wtorek 10:00", {"day": "Wtorek", "time": "10:00", "service": "Strzyżenie"}),
        ("środa 15:30 na farbowanie", {"day": "Środa", "time": "15:30", "service": "Farbowanie"}),
        ("piątek o 14:00", {"day": "Piątek", "time": "14:00", "service": "Strzyżenie"}),
        ("chcę się umówić", None),  # Brak terminu
        ("wtorek", None),           # Brak godziny
        ("10:00", None)             # Brak dnia
    ]
    
    print("🎯 PARSOWANIE REZERWACJI:")
    print("-" * 30)
    
    booking_passed = 0
    for message, expected in booking_cases:
        result = parse_booking_message_ai(message)
        if result == expected:
            status = "✅ PASS"
            booking_passed += 1
        else:
            status = "❌ FAIL"
        
        print(f"{status} \"{message}\"")
        print(f"   Oczekiwano: {expected}")
        print(f"   Otrzymano: {result}")
        print()
    
    print(f"📊 PARSOWANIE - Kontakty: {contact_passed}/{len(contact_cases)}, Rezerwacje: {booking_passed}/{len(booking_cases)}")
    
    return contact_passed + booking_passed, len(contact_cases) + len(booking_cases)

if __name__ == "__main__":
    print("🤖 TESTY AI BOT LOGIC")
    print("=" * 60)
    
    try:
        # Test klasyfikacji
        passed1, total1 = test_ai_intent_classification()
        
        # Test z sesją
        passed2, total2 = test_ai_with_session_context()
        
        # Test parsowania
        passed3, total3 = test_ai_parsing()
        
        # PODSUMOWANIE
        total_passed = passed1 + passed2 + passed3
        total_tests = total1 + total2 + total3
        
        print(f"\n{'🎉' if total_passed == total_tests else '⚠️'} PODSUMOWANIE WSZYSTKICH TESTÓW:")
        print(f"✅ Zaliczone: {total_passed}/{total_tests} ({total_passed/total_tests*100:.1f}%)")
        
        if total_passed == total_tests:
            print("🏆 WSZYSTKIE TESTY ZALICZONE! AI DZIAŁA PERFEKCYJNIE!")
        else:
            print("🔧 POTRZEBNE DALSZE POPRAWKI PROMPTÓW")
        
    except Exception as e:
        print(f"❌ BŁĄD TESTÓW: {e}")
        import traceback
        traceback.print_exc()