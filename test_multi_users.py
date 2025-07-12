"""
TESTY WIELODOSTĘPU UŻYTKOWNIKÓW
Sprawdza czy bot obsługuje wielu użytkowników jednocześnie
"""

import requests
import json
import time
import threading
import logging
from datetime import datetime
import sys
import os

# Dodaj ścieżkę do głównego folderu
sys.path.append('/home/dawid/python/smart-faq-bot')

# Konfiguracja logowania
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MultiUserTester:
    def __init__(self, base_url="http://localhost:5000"):
        self.base_url = base_url
        self.test_results = []
        self.errors = []
    
    def test_api_endpoints(self):
        """Test dostępności endpointów API"""
        print("🔍 TESTOWANIE ENDPOINTÓW API")
        print("="*50)
        
        endpoints = [
            "/api/health",
            "/api/debug/sessions",
            "/api/debug/users"
        ]
        
        for endpoint in endpoints:
            try:
                response = requests.get(f"{self.base_url}{endpoint}", timeout=5)
                status = "✅ OK" if response.status_code == 200 else f"❌ {response.status_code}"
                print(f"{endpoint}: {status}")
                
                if response.status_code == 200:
                    data = response.json()
                    print(f"   📊 Response: {json.dumps(data, indent=2, ensure_ascii=False)[:200]}...")
                
            except requests.exceptions.ConnectionError:
                print(f"{endpoint}: ❌ CONNECTION ERROR - Czy backend działa?")
                self.errors.append(f"Backend nie odpowiada na {endpoint}")
            except Exception as e:
                print(f"{endpoint}: ❌ ERROR - {e}")
                self.errors.append(f"Błąd {endpoint}: {e}")
        
        print()
    
    def simulate_user_message(self, user_id, message, delay=0):
        """Symuluj wiadomość od użytkownika"""
        if delay > 0:
            time.sleep(delay)
        
        try:
            # Bezpośrednie wywołanie logiki bota
            from bot_logic_ai import process_user_message_smart
            
            logger.info(f"🧪 SYMULACJA: {user_id} → '{message}'")
            start_time = time.time()
            
            response = process_user_message_smart(message, user_id)
            
            end_time = time.time()
            response_time = end_time - start_time
            
            result = {
                'user_id': user_id,
                'message': message,
                'response': response,
                'response_time': response_time,
                'timestamp': datetime.now().isoformat(),
                'success': True
            }
            
            self.test_results.append(result)
            
            logger.info(f"✅ {user_id}: '{response[:50]}...' ({response_time:.2f}s)")
            return result
            
        except Exception as e:
            logger.error(f"❌ BŁĄD {user_id}: {e}")
            error_result = {
                'user_id': user_id,
                'message': message,
                'error': str(e),
                'success': False,
                'timestamp': datetime.now().isoformat()
            }
            self.test_results.append(error_result)
            self.errors.append(f"{user_id}: {e}")
            return error_result
    
    def test_concurrent_users(self):
        """Test równoczesnych użytkowników"""
        print("👥 TESTOWANIE RÓWNOCZESNYCH UŻYTKOWNIKÓW")
        print("="*50)
        
        test_scenarios = [
            {'user_id': 'user_laptop1', 'message': 'Cześć! Jakie macie godziny pracy?'},
            {'user_id': 'user_laptop2', 'message': 'Podaj terminy na jutro'},
            {'user_id': 'user_phone', 'message': 'Ile kosztuje strzyżenie?'},
            {'user_id': 'user_tablet', 'message': 'Sprawdź terminy na sobotę'},
            {'user_id': 'user_desktop', 'message': 'Chcę się umówić na piątek o 15:00'},
        ]
        
        # Uruchom testy równocześnie
        threads = []
        for i, scenario in enumerate(test_scenarios):
            thread = threading.Thread(
                target=self.simulate_user_message,
                args=(scenario['user_id'], scenario['message'], i * 0.2)  # Lekkie opóźnienie
            )
            threads.append(thread)
            thread.start()
        
        # Poczekaj na zakończenie wszystkich testów
        for thread in threads:
            thread.join()
        
        # Podsumowanie
        successful_tests = [r for r in self.test_results if r.get('success', False)]
        failed_tests = [r for r in self.test_results if not r.get('success', False)]
        
        print(f"\n📊 WYNIKI TESTÓW RÓWNOCZESNYCH:")
        print(f"✅ Udane: {len(successful_tests)}")
        print(f"❌ Nieudane: {len(failed_tests)}")
        
        for result in successful_tests:
            print(f"   ✅ {result['user_id']}: {result['response_time']:.2f}s")
        
        for result in failed_tests:
            print(f"   ❌ {result['user_id']}: {result.get('error', 'Unknown error')}")
    
    def test_sequential_conversation(self):
        """Test sekwencyjnej rozmowy z różnymi użytkownikami"""
        print("\n💬 TESTOWANIE SEKWENCYJNYCH ROZMÓW")
        print("="*50)
        
        conversations = [
            {
                'user_id': 'conversation_user1',
                'messages': [
                    'Cześć!',
                    'Chcę się umówić',
                    'jutro o 15:00',
                    'strzyżenie',
                    'Jan Kowalski 123456789',
                    'TAK'
                ]
            },
            {
                'user_id': 'conversation_user2', 
                'messages': [
                    'Witaj',
                    'Podaj terminy na sobotę',
                    'Ile kosztuje farbowanie?'
                ]
            }
        ]
        
        for conv in conversations:
            print(f"\n🗣️ ROZMOWA: {conv['user_id']}")
            print("-" * 30)
            
            for i, message in enumerate(conv['messages']):
                print(f"\n👤 [{i+1}] {message}")
                result = self.simulate_user_message(conv['user_id'], message)
                if result['success']:
                    print(f"🤖 {result['response']}")
                else:
                    print(f"❌ BŁĄD: {result.get('error')}")
                time.sleep(0.5)  # Przerwa między wiadomościami
    
    def test_session_separation(self):
        """Test separacji sesji użytkowników"""
        print("\n🔒 TESTOWANIE SEPARACJI SESJI")
        print("="*50)
        
        # Dwóch użytkowników zaczyna rezerwacje jednocześnie
        user1_messages = [
            'Chcę się umówić',
            'jutro o 15:00',
            'strzyżenie'
        ]
        
        user2_messages = [
            'Umów mnie',
            'pojutrze o 16:30',
            'farbowanie'
        ]
        
        # Przeplataj wiadomości
        for i in range(max(len(user1_messages), len(user2_messages))):
            if i < len(user1_messages):
                print(f"\n👤 USER1: {user1_messages[i]}")
                result1 = self.simulate_user_message('session_user1', user1_messages[i])
                if result1['success']:
                    print(f"🤖 USER1: {result1['response'][:100]}...")
            
            if i < len(user2_messages):
                print(f"\n👤 USER2: {user2_messages[i]}")
                result2 = self.simulate_user_message('session_user2', user2_messages[i])
                if result2['success']:
                    print(f"🤖 USER2: {result2['response'][:100]}...")
            
            time.sleep(0.3)
    
    def check_session_states(self):
        """Sprawdź stany sesji wszystkich użytkowników"""
        print("\n📊 SPRAWDZANIE STANÓW SESJI")
        print("="*50)
        
        try:
            from bot_logic_ai import user_sessions, user_conversations
            
            print(f"Aktywne sesje: {len(user_sessions)}")
            print(f"Rozmowy w pamięci: {len(user_conversations)}")
            
            for user_id, session in user_sessions.items():
                conv_length = len(user_conversations.get(user_id, []))
                print(f"   👤 {user_id}: {session.state} | {conv_length} wiadomości")
            
            # Sprawdź przez API
            response = requests.get(f"{self.base_url}/api/debug/sessions", timeout=5)
            if response.status_code == 200:
                data = response.json()
                print(f"\nAPI Debug Info:")
                print(f"   Sesje przez API: {data.get('active_sessions', 0)}")
                print(f"   Rozmowy przez API: {data.get('conversations', 0)}")
            
        except Exception as e:
            print(f"❌ Błąd sprawdzania sesji: {e}")
    
    def cleanup_test_data(self):
        """Wyczyść dane testowe"""
        print("\n🧹 CZYSZCZENIE DANYCH TESTOWYCH")
        print("="*30)
        
        test_users = [
            'user_laptop1', 'user_laptop2', 'user_phone', 'user_tablet', 'user_desktop',
            'conversation_user1', 'conversation_user2', 
            'session_user1', 'session_user2'
        ]
        
        try:
            from bot_logic_ai import user_sessions, user_conversations
            
            cleaned_sessions = 0
            cleaned_conversations = 0
            
            for user_id in test_users:
                if user_id in user_sessions:
                    del user_sessions[user_id]
                    cleaned_sessions += 1
                
                if user_id in user_conversations:
                    del user_conversations[user_id]
                    cleaned_conversations += 1
            
            print(f"✅ Wyczyszczono {cleaned_sessions} sesji")
            print(f"✅ Wyczyszczono {cleaned_conversations} rozmów")
            
        except Exception as e:
            print(f"❌ Błąd czyszczenia: {e}")
    
    def generate_report(self):
        """Wygeneruj raport z testów"""
        print("\n📋 RAPORT Z TESTÓW")
        print("="*50)
        
        total_tests = len(self.test_results)
        successful_tests = len([r for r in self.test_results if r.get('success', False)])
        failed_tests = total_tests - successful_tests
        
        if total_tests > 0:
            success_rate = (successful_tests / total_tests) * 100
            avg_response_time = sum(r.get('response_time', 0) for r in self.test_results if r.get('success')) / max(successful_tests, 1)
            
            print(f"📊 STATYSTYKI:")
            print(f"   Łączna liczba testów: {total_tests}")
            print(f"   ✅ Udane: {successful_tests}")
            print(f"   ❌ Nieudane: {failed_tests}")
            print(f"   📈 Wskaźnik sukcesu: {success_rate:.1f}%")
            print(f"   ⏱️ Średni czas odpowiedzi: {avg_response_time:.2f}s")
            
            if success_rate >= 90:
                print(f"\n🎉 WSZYSTKO DZIAŁA ŚWIETNIE!")
            elif success_rate >= 70:
                print(f"\n⚠️ Większość testów przeszła, ale są problemy")
            else:
                print(f"\n💥 POWAŻNE PROBLEMY - sprawdź logi")
        
        if self.errors:
            print(f"\n❌ BŁĘDY ({len(self.errors)}):")
            for error in self.errors[:5]:  # Pokaż pierwsze 5
                print(f"   • {error}")
            if len(self.errors) > 5:
                print(f"   ... i {len(self.errors) - 5} więcej")
    
    def run_all_tests(self):
        """Uruchom wszystkie testy"""
        print("🧪 ROZPOCZYNAM TESTY WIELODOSTĘPU UŻYTKOWNIKÓW")
        print("="*60)
        print(f"🕐 Start: {datetime.now().strftime('%H:%M:%S')}")
        print()
        
        # 1. Test endpointów API
        self.test_api_endpoints()
        
        # 2. Test równoczesnych użytkowników
        self.test_concurrent_users()
        
        # 3. Test sekwencyjnych rozmów
        self.test_sequential_conversation()
        
        # 4. Test separacji sesji
        self.test_session_separation()
        
        # 5. Sprawdź stany sesji
        self.check_session_states()
        
        # 6. Wygeneruj raport
        self.generate_report()
        
        # 7. Wyczyść dane testowe
        self.cleanup_test_data()
        
        print(f"\n🏁 TESTY ZAKOŃCZONE: {datetime.now().strftime('%H:%M:%S')}")
        print("="*60)

# ==============================================
# DODATKOWE NARZĘDZIA TESTOWE
# ==============================================

def test_facebook_simulation():
    """Symuluj wiadomości Facebook z różnymi PSID"""
    print("📘 SYMULACJA FACEBOOK MESSENGER")
    print("="*40)
    
    # Symuluj różnych użytkowników Facebook
    facebook_users = [
        {'psid': 'fb_user_12345', 'name': 'Jan Kowalski'},
        {'psid': 'fb_user_67890', 'name': 'Anna Nowak'},
        {'psid': 'fb_user_11111', 'name': 'Piotr Wiśniewski'},
    ]
    
    messages = [
        'Cześć! Jakie macie godziny pracy?',
        'Podaj terminy na jutro',
        'Ile kosztuje strzyżenie?'
    ]
    
    try:
        from bot_logic_ai import process_user_message_smart
        
        for i, user in enumerate(facebook_users):
            message = messages[i % len(messages)]
            print(f"\n👤 {user['name']} ({user['psid']}): {message}")
            
            response = process_user_message_smart(message, user['psid'])
            print(f"🤖 {response}")
            
            time.sleep(0.5)
    
    except Exception as e:
        print(f"❌ Błąd symulacji Facebook: {e}")

def check_memory_usage():
    """Sprawdź zużycie pamięci przez sesje"""
    print("\n🧠 SPRAWDZANIE ZUŻYCIA PAMIĘCI")
    print("="*40)
    
    try:
        from bot_logic_ai import user_sessions, user_conversations
        import sys
        
        sessions_size = sys.getsizeof(user_sessions)
        conversations_size = sys.getsizeof(user_conversations)
        
        print(f"Sesje: {len(user_sessions)} elementów, {sessions_size} bajtów")
        print(f"Rozmowy: {len(user_conversations)} elementów, {conversations_size} bajtów")
        
        total_messages = sum(len(conv) for conv in user_conversations.values())
        print(f"Łączna liczba wiadomości w pamięci: {total_messages}")
        
    except Exception as e:
        print(f"❌ Błąd sprawdzania pamięci: {e}")

# ==============================================
# URUCHOMIENIE TESTÓW
# ==============================================

if __name__ == "__main__":
    print("🚀 URUCHAMIANIE TESTÓW WIELODOSTĘPU")
    
    # Sprawdź czy backend działa
    try:
        response = requests.get("http://localhost:5000/api/health", timeout=5)
        print("✅ Backend dostępny")
    except:
        print("⚠️ Backend może nie działać - testy będą używać bezpośredniego wywołania")
    
    # Główne testy
    tester = MultiUserTester()
    tester.run_all_tests()
    
    # Dodatkowe testy
    print("\n" + "="*60)
    test_facebook_simulation()
    check_memory_usage()
    
    print("\n🎯 WSZYSTKIE TESTY ZAKOŃCZONE!")
    print("💡 Jeśli widzisz błędy, sprawdź czy:")
    print("   1. Backend działa (python backend.py)")
    print("   2. Moduły są poprawnie załadowane")
    print("   3. Baza danych / zmienne środowiskowe są OK")