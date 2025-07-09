# ZASTĄP cały test_ai_general.py:

"""
🧪 OBSZERNE TESTY INTELIGENTNEGO SYSTEMU BOTA
Testuje wszystkie funkcjonalności process_user_message_smart
"""

# 🔧 IMPORTY:
from bot_logic_ai import (
    analyze_user_intent_ai_robust, 
    process_user_message_smart, 
    get_user_stats, 
    clean_thinking_response_enhanced,
    user_conversations,
    user_sessions
)
import time

def test_cancellation_systems():
    """Porównanie starego i nowego systemu"""
    print("🧪 PORÓWNANIE SYSTEMÓW - ANULOWANIE WIZYTY")
    print("="*60)
    
    # === OBECNY SYSTEM (skomplikowany) ===
    print("\n❌ OBECNY SYSTEM (sesje + AI):")
    print("👤 User: chcę anulować wizytę")
    intent1 = analyze_user_intent_ai_robust("chcę anulować wizytę")
    print(f"🔍 AI Intent: {intent1}")
    print("🗃️ Sesja: state = 'cancelling'")
    
    print("👤 User: Jan Kowalski 123456789 wtorek 10:00")
    intent2 = analyze_user_intent_ai_robust("Jan Kowalski 123456789 wtorek 10:00")
    print(f"🔍 AI Intent: {intent2}")
    print("🧠 Backend: sprawdza sesję + intent → anulowanie")
    
    # === NOWY SYSTEM (tylko AI) ===
    print("\n✅ NOWY SYSTEM (tylko AI z pamięcią):")
    print("👤 User: chcę anulować wizytę")
    
    try:
        response1 = process_user_message_smart("chcę anulować wizytę", "test_user_cancel")
        print(f"🤖 AI: {response1}")
        
        print("👤 User: Jan Kowalski 123456789 wtorek 10:00")
        response2 = process_user_message_smart("Jan Kowalski 123456789 wtorek 10:00", "test_user_cancel")
        print(f"🤖 AI: {response2}")
        
    except Exception as e:
        print(f"❌ BŁĄD: {e}")

def test_booking_complete_flow():
    """Test kompletnego procesu rezerwacji"""
    print("\n🧪 TEST KOMPLETNEGO PROCESU REZERWACJI")
    print("="*50)
    
    user_id = "booking_test_user"
    
    # Krok 1: Inicjacja
    print("📅 KROK 1: Inicjacja rezerwacji")
    print("👤 User: Cześć, chcę się umówić na wizytę")
    r1 = process_user_message_smart("Cześć, chcę się umówić na wizytę", user_id)
    print(f"🤖 AI: {r1}")
    print("-" * 30)
    
    # Krok 2: Podanie terminu i usługi
    print("📅 KROK 2: Podanie terminu i usługi")
    print("👤 User: piątek 11:00 farbowanie")
    r2 = process_user_message_smart("piątek 11:00 farbowanie", user_id)
    print(f"🤖 AI: {r2}")
    print("-" * 30)
    
    # Krok 3: Podanie danych kontaktowych
    print("📅 KROK 3: Podanie danych kontaktowych")
    print("👤 User: Katarzyna Nowak 555-123-456")
    r3 = process_user_message_smart("Katarzyna Nowak 555-123-456", user_id)
    print(f"🤖 AI: {r3}")
    print("-" * 30)
    
    # Sprawdź czy zawiera potwierdzenie
    if "✅ REZERWACJA POTWIERDZONA:" in r3:
        print("✅ SUKCES: Rezerwacja została potwierdzona!")
    else:
        print("❌ BŁĄD: Brak potwierdzenia rezerwacji")

def test_cancellation_complete_flow():
    """Test kompletnego procesu anulowania"""
    print("\n🧪 TEST KOMPLETNEGO PROCESU ANULOWANIA")
    print("="*50)
    
    user_id = "cancel_test_user"
    
    # Krok 1: Żądanie anulowania
    print("❌ KROK 1: Żądanie anulowania")
    print("👤 User: Chcę anulować swoją wizytę")
    r1 = process_user_message_smart("Chcę anulować swoją wizytę", user_id)
    print(f"🤖 AI: {r1}")
    print("-" * 30)
    
    # Krok 2: Podanie danych do anulowania
    print("❌ KROK 2: Podanie danych do anulowania")
    print("👤 User: Marek Kowal 666-999-333 środa 13:00")
    r2 = process_user_message_smart("Marek Kowal 666-999-333 środa 13:00", user_id)
    print(f"🤖 AI: {r2}")
    print("-" * 30)
    
    # Sprawdź czy zawiera potwierdzenie anulowania
    if "❌ ANULACJA POTWIERDZONA:" in r2:
        print("✅ SUKCES: Anulowanie zostało potwierdzone!")
    else:
        print("❌ BŁĄD: Brak potwierdzenia anulowania")

def test_memory_and_context():
    """Test pamięci i kontekstu AI"""
    print("\n🧪 TEST PAMIĘCI I KONTEKSTU")
    print("="*40)
    
    user_id = "memory_test_user"
    
    # Test 1: Przedstawienie się
    print("🧠 TEST 1: Przedstawienie się")
    print("👤 User: Cześć, nazywam się Aleksandra")
    r1 = process_user_message_smart("Cześć, nazywam się Aleksandra", user_id)
    print(f"🤖 AI: {r1}")
    print("-" * 20)
    
    # Test 2: Sprawdzenie pamięci imienia
    print("🧠 TEST 2: Sprawdzenie pamięci imienia")
    print("👤 User: Jak mam na imię?")
    r2 = process_user_message_smart("Jak mam na imię?", user_id)
    print(f"🤖 AI: {r2}")
    
    if "Aleksandra" in r2:
        print("✅ SUKCES: AI pamięta imię!")
    else:
        print("❌ BŁĄD: AI nie pamięta imienia")
    print("-" * 20)
    
    # Test 3: Kontekst rezerwacji
    print("🧠 TEST 3: Kontekst w trakcie rezerwacji")
    print("👤 User: Chcę się umówić")
    r3 = process_user_message_smart("Chcę się umówić", user_id)
    print(f"🤖 AI: {r3}")
    
    print("👤 User: sobota 10:00")
    r4 = process_user_message_smart("sobota 10:00", user_id)
    print(f"🤖 AI: {r4}")
    
    print("👤 User: stylizacja")
    r5 = process_user_message_smart("stylizacja", user_id)
    print(f"🤖 AI: {r5}")
    print("-" * 20)
    
    # Test 4: Użycie imienia w kontekście
    print("🧠 TEST 4: Użycie imienia w dalszej rozmowie")
    print("👤 User: Dziękuję za pomoc")
    r6 = process_user_message_smart("Dziękuję za pomoc", user_id)
    print(f"🤖 AI: {r6}")
    
    if "Aleksandra" in r6:
        print("✅ SUKCES: AI używa imienia w kontekście!")
    else:
        print("⚠️ INFO: AI nie użyło imienia (może być OK)")

def test_user_isolation():
    """Test izolacji różnych użytkowników"""
    print("\n🧪 TEST IZOLACJI UŻYTKOWNIKÓW")
    print("="*40)
    
    # Użytkownik 1
    print("👤 USER 1: Nazywam się Anna, chcę się umówić na wtorek")
    r1 = process_user_message_smart("Nazywam się Anna, chcę się umówić na wtorek", "user_1")
    print(f"🤖 → User1: {r1[:80]}...")
    
    # Użytkownik 2  
    print("👤 USER 2: Jestem Jan, potrzebuję wizyty w czwartek")
    r2 = process_user_message_smart("Jestem Jan, potrzebuję wizyty w czwartek", "user_2")
    print(f"🤖 → User2: {r2[:80]}...")
    
    # Sprawdzenie izolacji - User 1
    print("👤 USER 1: Jak mam na imię?")
    r3 = process_user_message_smart("Jak mam na imię?", "user_1")
    print(f"🤖 → User1: {r3}")
    
    # Sprawdzenie izolacji - User 2
    print("👤 USER 2: Jak mam na imię?")
    r4 = process_user_message_smart("Jak mam na imię?", "user_2")
    print(f"🤖 → User2: {r4}")
    
    # Weryfikacja
    if "Anna" in r3 and "Jan" in r4:
        print("✅ SUKCES: Izolacja użytkowników działa!")
    else:
        print("❌ BŁĄD: Problem z izolacją użytkowników")

def test_edge_cases():
    """Test przypadków brzegowych"""
    print("\n🧪 TEST PRZYPADKÓW BRZEGOWYCH")
    print("="*40)
    
    user_id = "edge_case_user"
    
    # Test 1: Pusta wiadomość
    print("🔍 TEST 1: Reakcja na różne typy wiadomości")
    test_messages = [
        "",  # Pusta
        "   ",  # Same spacje
        "🤔",  # Samo emoji
        "123456789",  # Same cyfry
        "ąćęłńóśźż",  # Polskie znaki
        "Co?",  # Bardzo krótka
        "Bardzo długa wiadomość " * 20,  # Bardzo długa
    ]
    
    for i, msg in enumerate(test_messages, 1):
        print(f"   {i}. Wiadomość: '{msg[:30]}{'...' if len(msg) > 30 else ''}'")
        try:
            response = process_user_message_smart(msg, f"{user_id}_{i}")
            print(f"      Odpowiedź: {response[:50]}{'...' if len(response) > 50 else ''}")
        except Exception as e:
            print(f"      ❌ Błąd: {e}")
        print()

def test_services_and_pricing():
    """Test pytań o usługi i ceny"""
    print("\n🧪 TEST PYTAŃ O USŁUGI I CENY")
    print("="*40)
    
    user_id = "services_test_user"
    
    questions = [
        "Jakie usługi oferujecie?",
        "Ile kosztuje strzyżenie?",
        "Czy robicie farbowanie?",
        "Jakie są godziny otwarcia?",
        "Czy pracujecie w niedziele?",
        "Ile trwa stylizacja?",
        "Czy potrzeba umówić wizytę?",
    ]
    
    for i, question in enumerate(questions, 1):
        print(f"❓ PYTANIE {i}: {question}")
        response = process_user_message_smart(question, f"{user_id}_{i}")
        print(f"🤖 ODPOWIEDŹ: {response}")
        print("-" * 30)

def test_cleaning_function_extended():
    """Rozszerzony test funkcji czyszczenia"""
    print("\n🧪 TEST FUNKCJI CZYSZCZENIA - ROZSZERZONY")
    print("="*50)
    
    test_cases = [
        # Podstawowe przypadki
        "<think>Analyzing...</think>Cześć! Jak mogę pomóc?",
        "BOOKING",
        "CONTACT_DATA - to jest kategoria", 
        
        # Przypadki z rzeczywistymi odpowiedziami
        "<think>Let me think</think>✅ REZERWACJA POTWIERDZONA: Anna Kowalska, wtorek 15:00, Strzyżenie, tel: 987654321",
        "<thinking>This is thinking</thinking>❌ ANULACJA POTWIERDZONA: Jan Kowalski, środa 14:00, tel: 123456789",
        
        # Mieszane przypadki
        "OTHER_QUESTION\n\nCześć! W czym mogę pomóc?",
        "Oczywiście! Proszę podać swoje dane.",
        "WANT_APPOINTMENT Super! Jaki termin Ci odpowiada?",
        
        # Przypadki brzegowe
        "<think>Complex thinking process with multiple lines\nand reasoning steps</think>Finalna odpowiedź",
        "ASK_AVAILABILITY\nBOOKING\nCONTACT_DATA\nFaktyczna odpowiedź na końcu",
        "<think>Nested <think>thinking</think> blocks</think>Czysta odpowiedź",
        
        # Tylko kategorie (powinny zostać zastąpione)
        "CANCEL_VISIT",
        "OTHER_QUESTION",
        "   BOOKING   ",
    ]
    
    print("🧹 SZCZEGÓŁOWY TEST CZYSZCZENIA:")
    
    for i, test in enumerate(test_cases, 1):
        print(f"\n{i:2d}. PRZED: {test}")
        cleaned = clean_thinking_response_enhanced(test)
        print(f"    PO:    {cleaned}")
        
        # Sprawdź jakość czyszczenia
        if "<think" in cleaned or "<thinking" in cleaned:
            print("    ❌ BŁĄD: Pozostały tagi <think>")
        elif cleaned in ["BOOKING", "CONTACT_DATA", "OTHER_QUESTION", "ASK_AVAILABILITY", "WANT_APPOINTMENT", "CANCEL_VISIT"]:
            print("    ⚠️ KATEGORIA: Zamieniono na domyślną odpowiedź")
        elif len(cleaned) < 5:
            print("    ⚠️ KRÓTKA: Bardzo krótka odpowiedź")
        else:
            print("    ✅ OK: Poprawnie oczyszczona")
        
        print("-" * 40)

def test_performance_and_stats():
    """Test wydajności i statystyk"""
    print("\n🧪 TEST WYDAJNOŚCI I STATYSTYK")
    print("="*40)
    
    print("📊 STATYSTYKI PRZED TESTAMI:")
    stats_before = get_user_stats()
    print(f"   Sesje: {stats_before['total_sessions']}")
    print(f"   Rozmowy: {stats_before['conversations_total']}")
    print(f"   Aktywni ostatnio: {stats_before['active_last_hour']}")
    
    # Test wydajności - wiele szybkich zapytań
    print("\n⚡ TEST WYDAJNOŚCI - 10 szybkich zapytań:")
    start_time = time.time()
    
    for i in range(10):
        response = process_user_message_smart(f"Testowa wiadomość {i+1}", f"perf_user_{i}")
        print(f"   {i+1}. Odpowiedź: {len(response)} znaków")
    
    end_time = time.time()
    print(f"⏱️ Czas wykonania: {end_time - start_time:.2f} sekund")
    print(f"⚡ Średni czas na zapytanie: {(end_time - start_time)/10:.2f} sekund")
    
    print("\n📊 STATYSTYKI PO TESTACH:")
    stats_after = get_user_stats()
    print(f"   Sesje: {stats_after['total_sessions']}")
    print(f"   Rozmowy: {stats_after['conversations_total']}")
    print(f"   Aktywni ostatnio: {stats_after['active_last_hour']}")
    
    print(f"\n📈 PRZYROST:")
    print(f"   Nowe rozmowy: +{stats_after['conversations_total'] - stats_before['conversations_total']}")

def run_all_tests():
    """Uruchom wszystkie testy"""
    print("🚀 URUCHAMIANIE WSZYSTKICH TESTÓW")
    print("="*60)
    
    tests = [
        ("Porównanie systemów", test_cancellation_systems),
        ("Kompletna rezerwacja", test_booking_complete_flow),
        ("Kompletne anulowanie", test_cancellation_complete_flow),
        ("Pamięć i kontekst", test_memory_and_context),
        ("Izolacja użytkowników", test_user_isolation),
        ("Przypadki brzegowe", test_edge_cases),
        ("Usługi i ceny", test_services_and_pricing),
        ("Funkcja czyszczenia", test_cleaning_function_extended),
        ("Wydajność i statystyki", test_performance_and_stats),
    ]
    
    for test_name, test_function in tests:
        print(f"\n{'='*60}")
        print(f"🧪 {test_name.upper()}")
        print('='*60)
        
        try:
            test_function()
            print(f"✅ Test '{test_name}' zakończony")
        except Exception as e:
            print(f"❌ Test '{test_name}' nie powiódł się: {e}")
        
        time.sleep(0.5)  # Krótka pauza między testami

# Funkcje z poprzednich wersji (zachowane dla kompatybilności)
def test_advanced_scenarios():
    """Podstawowe scenariusze (zachowane)"""
    test_booking_complete_flow()
    test_memory_and_context()

def test_smart_with_existing_calendar():
    """Test z kalendarzem (zachowany)"""
    test_booking_complete_flow()
    test_cancellation_complete_flow()

def test_cleaning_function():
    """Podstawowy test czyszczenia (zachowany)"""
    test_cleaning_function_extended()

# MAIN - wybór testów
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        test_name = sys.argv[1].lower()
        
        if test_name == "all":
            run_all_tests()
        def test_intent_classification_accuracy():
            """Test dokładności klasyfikacji intencji AI"""
            print("\n🧪 TEST DOKŁADNOŚCI KLASYFIKACJI INTENCJI")
            print("="*50)
            
            test_cases = [
                # CONTACT_DATA cases
                ("Jan Kowalski 123456789", "CONTACT_DATA"),
                ("Anna Nowak, tel. 555666777", "CONTACT_DATA"),
                ("Piotr Wiśniewski, numer: 111222333", "CONTACT_DATA"),
                
                # BOOKING cases  
                ("poniedziałek 10:00", "BOOKING"),
                ("wtorek 11:30 strzyżenie", "BOOKING"),
                ("środa 15:00", "BOOKING"),
                
                # CANCEL_VISIT cases
                ("chcę anulować wizytę", "CANCEL_VISIT"),
                ("odwołaj termin", "CANCEL_VISIT"),
                ("rezygnuję z wizyty", "CANCEL_VISIT"),
                
                # ASK_AVAILABILITY cases
                ("wolne terminy?", "ASK_AVAILABILITY"),
                ("dostępne godziny w piątek?", "ASK_AVAILABILITY"),
                ("kiedy można się umówić?", "ASK_AVAILABILITY"),
                
                # WANT_APPOINTMENT cases
                ("chcę się umówić", "WANT_APPOINTMENT"),
                ("potrzebuję wizyty", "WANT_APPOINTMENT"),
                ("umów mnie", "WANT_APPOINTMENT"),
            ]
            
            correct = 0
            total = len(test_cases)
            
            for message, expected_intent in test_cases:
                actual_intent = analyze_user_intent_ai_robust(message)
                is_correct = actual_intent == expected_intent
                
                print(f"📝 '{message}' → {actual_intent} {'✅' if is_correct else '❌'}")
                if not is_correct:
                    print(f"   Oczekiwano: {expected_intent}")
                
                if is_correct:
                    correct += 1
            
            accuracy = (correct / total) * 100
            print(f"\n📊 DOKŁADNOŚĆ: {correct}/{total} ({accuracy:.1f}%)")
            
            if accuracy >= 85:
                print("✅ SUKCES: Wysoka dokładność klasyfikacji!")
            elif accuracy >= 70:
                print("⚠️ UWAGA: Średnia dokładność, może wymagać poprawy")
            else:
                print("❌ BŁĄD: Niska dokładność, wymaga natychmiastowej poprawy")

        def test_conversation_flow_variations():
            """Test różnych wariantów przepływu rozmowy"""
            print("\n🧪 TEST WARIANTÓW PRZEPŁYWU ROZMOWY")
            print("="*50)
            
            # Wariant 1: Wszystko w jednej wiadomości
            print("🔄 WARIANT 1: Wszystko naraz")
            user_id = "flow_test_1"
            response = process_user_message_smart("Jan Kowalski 123456789 piątek 14:00 strzyżenie", user_id)
            print(f"👤 User: Jan Kowalski 123456789 piątek 14:00 strzyżenie")
            print(f"🤖 AI: {response}")
            
            if "REZERWACJA POTWIERDZONA" in response:
                print("✅ SUKCES: Pełna rezerwacja w jednej wiadomości")
            else:
                print("❌ BŁĄD: Nie rozpoznano pełnej rezerwacji")
            print("-" * 30)
            
            # Wariant 2: Odwrócona kolejność (najpierw dane, potem termin)
            print("🔄 WARIANT 2: Najpierw dane, potem termin")
            user_id = "flow_test_2"
            r1 = process_user_message_smart("chcę się umówić", user_id)
            r2 = process_user_message_smart("Maria Kowalczyk 987654321", user_id)
            r3 = process_user_message_smart("czwartek 16:00", user_id)
            
            print(f"🤖 Step 1: {r1[:50]}...")
            print(f"🤖 Step 2: {r2[:50]}...")
            print(f"🤖 Step 3: {r3[:50]}...")
            
            if "REZERWACJA POTWIERDZONA" in r3:
                print("✅ SUKCES: Rezerwacja w odwróconej kolejności")
            else:
                print("❌ BŁĄD: Nie zadziałała odwrócona kolejność")
            print("-" * 30)
            
            # Wariant 3: Z przerwami i dodatkowymi pytaniami
            print("🔄 WARIANT 3: Z przerwami")
            user_id = "flow_test_3"
            responses = []
            messages = [
                "cześć",
                "chcę się umówić", 
                "ile kosztuje strzyżenie?",
                "ok, wtorek 10:00",
                "Tomasz Nowak 555444333"
            ]
            
            for msg in messages:
                response = process_user_message_smart(msg, user_id)
                responses.append(response)
                print(f"👤 {msg} → 🤖 {response[:40]}...")
            
            final_response = responses[-1]
            if "REZERWACJA POTWIERDZONA" in final_response:
                print("✅ SUKCES: Rezerwacja z przerwami")
            else:
                print("❌ BŁĄD: Nie zadziałała rezerwacja z przerwami")

        def test_error_handling_and_recovery():