"""
TESTY AI - SPRAWDZANIE TERMINÓW WIZYT
Celem jest upewnienie się, że AI nie wymyśla własnych terminów
"""

import logging
import sys
import os

# Dodaj ścieżkę do głównego folderu
sys.path.append('/home/dawid/python/smart-faq-bot')

from bot_logic_ai import process_user_message_smart
import time

# Konfiguracja logowania
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

class AvailabilityTestRunner:
    def __init__(self):
        self.test_user_id = "test_availability_user"
        self.passed_tests = 0
        self.failed_tests = 0
        self.results = []
    
    def run_test(self, test_name, user_message, expected_behavior):
        """Wykonaj pojedynczy test"""
        print(f"\n{'='*60}")
        print(f"🧪 TEST: {test_name}")
        print(f"📝 WIADOMOŚĆ: '{user_message}'")
        print(f"🎯 OCZEKIWANE: {expected_behavior}")
        print(f"{'='*60}")
        
        try:
            # Wywołaj AI
            response = process_user_message_smart(user_message, self.test_user_id)
            
            print(f"🤖 ODPOWIEDŹ AI:")
            print(f"'{response}'")
            print(f"\n📊 ANALIZA:")
            
            # Sprawdź czy AI używa CHECK_AVAILABILITY
            has_check_availability = "CHECK_AVAILABILITY:" in response
            
            # Sprawdź czy AI wymyśla terminy
            invented_times = self._detect_invented_times(response)
            
            # Sprawdź procesy myślowe
            has_thinking = self._detect_thinking_process(response)
            
            # Sprawdź czy odpowiedź jest naturalna
            is_natural = self._is_natural_response(response)
            
            # Wyniki analizy
            print(f"✅ Używa CHECK_AVAILABILITY: {'TAK' if has_check_availability else 'NIE'}")
            print(f"❌ Wymyśla terminy: {'TAK' if invented_times else 'NIE'}")
            print(f"🧠 Pokazuje procesy myślowe: {'TAK' if has_thinking else 'NIE'}")
            print(f"💬 Naturalna odpowiedź: {'TAK' if is_natural else 'NIE'}")
            
            # Oceń wynik
            test_passed = self._evaluate_test(
                expected_behavior, 
                has_check_availability, 
                invented_times, 
                has_thinking, 
                is_natural
            )
            
            if test_passed:
                print(f"🎉 WYNIK: ZALICZONY")
                self.passed_tests += 1
            else:
                print(f"💥 WYNIK: NIEZALICZONY")
                self.failed_tests += 1
            
            # Zapisz wyniki
            self.results.append({
                'test_name': test_name,
                'user_message': user_message,
                'response': response,
                'has_check_availability': has_check_availability,
                'invented_times': invented_times,
                'has_thinking': has_thinking,
                'is_natural': is_natural,
                'passed': test_passed
            })
            
            return test_passed
            
        except Exception as e:
            print(f"💥 BŁĄD TESTU: {e}")
            self.failed_tests += 1
            return False
    
    def _detect_invented_times(self, response):
        """Wykryj czy AI wymyślił własne terminy"""
        # Wzorce typowych wymyślonych terminów
        invented_patterns = [
            r'\b\d{1,2}:\d{2}\b.*\b\d{1,2}:\d{2}\b.*\b\d{1,2}:\d{2}\b',  # 9:00, 10:00, 11:00
            r'dostępne terminy:.*\d{1,2}:\d{2}',  # "dostępne terminy: 9:00"
            r'wolne godziny:.*\d{1,2}:\d{2}',     # "wolne godziny: 10:00"
            r'mamy wolne:.*\d{1,2}:\d{2}',        # "mamy wolne: 11:00"
            r'\d{1,2}:\d{2}.*\d{1,2}:\d{2}.*\d{1,2}:\d{2}.*dostępne',  # lista terminów
        ]
        
        import re
        for pattern in invented_patterns:
            if re.search(pattern, response, re.IGNORECASE):
                return True
        return False
    
    def _detect_thinking_process(self, response):
        """Wykryj procesy myślowe AI"""
        thinking_indicators = [
            '<think>', '<thinking>', 'Okay, I need', 'First, I remember',
            'The client wrote', 'I should start', 'Then, on the next',
            'But wait, the system', 'So, the correct', 'Putting it all'
        ]
        
        for indicator in thinking_indicators:
            if indicator in response:
                return True
        return False
    
    def _is_natural_response(self, response):
        """Sprawdź czy odpowiedź jest naturalna"""
        # Odpowiedź powinna być po polsku i zawierać polskie znaki
        polish_indicators = ['ą', 'ć', 'ę', 'ł', 'ń', 'ó', 'ś', 'ź', 'ż']
        has_polish = any(char in response for char in polish_indicators)
        
        # Sprawdź czy ma sensowną długość
        reasonable_length = 10 <= len(response) <= 1000
        
        # Sprawdź czy nie zawiera dziwnych kategorii
        weird_categories = ['BOOKING', 'CONTACT_DATA', 'ASK_AVAILABILITY']
        no_weird_categories = not any(cat in response for cat in weird_categories)
        
        return has_polish and reasonable_length and no_weird_categories
    
    def _evaluate_test(self, expected_behavior, has_check, invented, thinking, natural):
        """Oceń czy test przeszedł"""
        if expected_behavior == "should_use_check_availability":
            return has_check and not invented and not thinking and natural
        elif expected_behavior == "should_not_invent_times":
            return not invented and natural
        elif expected_behavior == "should_be_natural":
            return natural and not thinking
        else:
            return True
    
    def run_all_tests(self):
        """Uruchom wszystkie testy"""
        print("🚀 ROZPOCZYNAM TESTY AI - SPRAWDZANIE TERMINÓW")
        print("="*80)
        
        # KATEGORIA 1: BEZPOŚREDNIE PYTANIA O TERMINY
        print("\n📋 KATEGORIA 1: BEZPOŚREDNIE PYTANIA O TERMINY")
        
        self.run_test(
            "Pytanie o terminy na jutro",
            "Podaj terminy na jutro",
            "should_use_check_availability"
        )
        
        self.run_test(
            "Wolne terminy na sobotę", 
            "Jakie macie wolne terminy na sobotę?",
            "should_use_check_availability"
        )
        
        self.run_test(
            "Sprawdź terminy na piątek",
            "Sprawdź terminy na piątek",
            "should_use_check_availability"
        )
        
        self.run_test(
            "Masz coś wolnego na środę?",
            "Masz coś wolnego na środę?",
            "should_use_check_availability"
        )
        
        self.run_test(
            "Dostępne godziny dzisiaj",
            "Jakie są dostępne godziny dzisiaj?",
            "should_use_check_availability"
        )
        
        # KATEGORIA 2: PUŁAPKI - PYTANIA KTÓRE MOGĄ ZMYLIĆ AI
        print("\n📋 KATEGORIA 2: PUŁAPKI - PYTANIA KTÓRE MOGĄ ZMYLIĆ AI")
        
        self.run_test(
            "Ogólne pytanie o terminy",
            "Kiedy macie wolne terminy?",
            "should_not_invent_times"
        )
        
        self.run_test(
            "Pytanie o godziny pracy",
            "Jakie są wasze godziny pracy?",
            "should_not_invent_times"
        )
        
        self.run_test(
            "Niejasne pytanie",
            "Czy mogę się umówić?",
            "should_be_natural"
        )
        
        # KATEGORIA 3: TESTY MIESZANE
        print("\n📋 KATEGORIA 3: TESTY MIESZANE")
        
        self.run_test(
            "Terminy + dodatkowe pytanie",
            "Podaj terminy na wtorek i powiedz ile kosztuje strzyżenie",
            "should_use_check_availability"
        )
        
        self.run_test(
            "Niedziela (salon zamknięty)",
            "Jakie terminy na niedzielę?",
            "should_be_natural"
        )
        
        # PODSUMOWANIE
        self.print_summary()
    
    def print_summary(self):
        """Wydrukuj podsumowanie testów"""
        print("\n" + "="*80)
        print("📊 PODSUMOWANIE TESTÓW")
        print("="*80)
        
        total_tests = self.passed_tests + self.failed_tests
        success_rate = (self.passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"✅ Zaliczone: {self.passed_tests}")
        print(f"❌ Niezaliczone: {self.failed_tests}")
        print(f"📈 Wskaźnik sukcesu: {success_rate:.1f}%")
        
        if success_rate >= 90:
            print(f"🎉 AI DZIAŁA ŚWIETNIE!")
        elif success_rate >= 70:
            print(f"⚠️ AI działa dobrze, ale można poprawić")
        else:
            print(f"💥 AI WYMAGA POPRAWEK!")
        
        # Szczegółowe wyniki
        print(f"\n📋 SZCZEGÓŁOWE WYNIKI:")
        for result in self.results:
            status = "✅" if result['passed'] else "❌"
            print(f"{status} {result['test_name']}")
            if not result['passed']:
                print(f"   🔍 Problem: ", end="")
                if result['invented_times']:
                    print("Wymyślone terminy, ", end="")
                if result['has_thinking']:
                    print("Procesy myślowe, ", end="")
                if not result['is_natural']:
                    print("Nienaturalna odpowiedź, ", end="")
                if not result['has_check_availability'] and "check_availability" in str(result):
                    print("Brak CHECK_AVAILABILITY, ", end="")
                print()
        
        print("\n" + "="*80)

# URUCHOMIENIE TESTÓW
if __name__ == "__main__":
    print("🧪 URUCHAMIANIE TESTÓW AI - SPRAWDZANIE TERMINÓW")
    
    # Sprawdź czy wszystkie moduły są dostępne
    try:
        tester = AvailabilityTestRunner()
        tester.run_all_tests()
        
    except ImportError as e:
        print(f"❌ Błąd importu: {e}")
        print("Upewnij się, że jesteś w folderze /home/dawid/python/smart-faq-bot")
    except Exception as e:
        print(f"💥 Nieoczekiwany błąd: {e}")