"""Test poprawek parsowania"""

from bot_logic_ai import parse_contact_data_ai, parse_booking_message_ai

def test_parsing_fixes():
    print("🧪 TEST POPRAWEK PARSOWANIA")
    print("-" * 50)
    
    # Test kontaktów
    contact_tests = [
        ("Jan Kowalski 123456789", True),
        ("Anna Nowak, 987-654-321", True), 
        ("Piotr Wiśniewski tel. 555 666 777", True),
        ("chcę się umówić", False)
    ]
    
    print("📞 KONTAKTY:")
    for message, should_work in contact_tests:
        result = parse_contact_data_ai(message)
        status = "✅" if bool(result) == should_work else "❌"
        print(f"{status} '{message}' → {result}")
    
    print("\n📅 REZERWACJE:")
    booking_tests = [
        ("umawiam się na wtorek 10:00", True),
        ("środa 15:30 na farbowanie", True),
        ("piątek o 14:00", True),
        ("chcę się umówić", False)
    ]
    
    for message, should_work in booking_tests:
        result = parse_booking_message_ai(message)
        status = "✅" if bool(result) == should_work else "❌"
        print(f"{status} '{message}' → {result}")

if __name__ == "__main__":
    test_parsing_fixes()