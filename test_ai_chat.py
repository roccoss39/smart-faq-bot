"""
🤖 INTERAKTYWNY CHAT Z TOGETHER AI
Test pamięci kontekstu i jakości odpowiedzi
"""

from together import Together
import os
from datetime import datetime

def main():
    print("🤖 INTERAKTYWNY CHAT Z TOGETHER AI")
    print("="*60)
    print("💡 Testuj pamięć kontekstu i jakość odpowiedzi")
    print("💡 Komendy specjalne:")
    print("   📜 'historia' - pokaż historię rozmowy")
    print("   🗑️  'wyczyść' - wyczyść historię")
    print("   🔧 'model' - pokaż aktualny model")
    print("   🚪 'quit/exit' - zakończ")
    print("-"*60)
    
    # Inicjalizacja
    client = Together()
    conversation_history = []
    start_time = datetime.now()
    message_count = 0
    
    # Model do testowania
    model = "deepseek-ai/DeepSeek-R1-Distill-Llama-70B-free"
    print(f"🧠 Model: {model}")
    print(f"⏰ Start: {start_time.strftime('%H:%M:%S')}")
    print()
    
    while True:
        try:
            # Pobierz wiadomość od użytkownika
            user_input = input("👤 Ty: ").strip()
            
            # Komendy specjalne
            if user_input.lower() in ['quit', 'exit', 'bye', 'koniec', 'q']:
                print("\n👋 Dziękuję za test! Do zobaczenia!")
                print(f"📊 Statystyki sesji:")
                print(f"   ⏱️  Czas trwania: {datetime.now() - start_time}")
                print(f"   💬 Liczba wiadomości: {message_count}")
                print(f"   🧠 Model: {model}")
                break
            
            elif user_input.lower() == 'historia':
                print("\n📜 HISTORIA ROZMOWY:")
                print("-" * 40)
                for i, msg in enumerate(conversation_history, 1):
                    role = "👤 Ty" if msg["role"] == "user" else "🤖 AI"
                    content = msg["content"][:100] + "..." if len(msg["content"]) > 100 else msg["content"]
                    print(f"{i:2d}. {role}: {content}")
                print(f"\n📊 Łącznie: {len(conversation_history)} wiadomości w historii")
                continue
            
            elif user_input.lower() == 'wyczyść':
                conversation_history.clear()
                message_count = 0
                print("🗑️  Historia wyczyszczona! Zaczynamy od nowa.")
                continue
            
            elif user_input.lower() == 'model':
                print(f"🧠 Aktualny model: {model}")
                print(f"🔗 API: Together AI")
                print(f"💾 Historia: {len(conversation_history)} wiadomości")
                continue
            
            # Pomiń puste wiadomości
            if not user_input:
                continue
            
            # Dodaj wiadomość użytkownika do historii
            conversation_history.append({"role": "user", "content": user_input})
            message_count += 1
            
            print("🤖 AI: ", end="", flush=True)
            
            # Wyślij zapytanie do AI
            response = client.chat.completions.create(
                model=model,
                messages=conversation_history,
                max_tokens=1000,
                temperature=0.7,
                stream=True  # Streaming dla płynniejszej odpowiedzi
            )
            
            # Zbierz odpowiedź ze streaming
            bot_response = ""
            for chunk in response:
                if chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    print(content, end="", flush=True)
                    bot_response += content
            
            print()  # Nowa linia po odpowiedzi
            
            # Dodaj odpowiedź bota do historii
            conversation_history.append({"role": "assistant", "content": bot_response})
            
            # Ogranicz historię do ostatnich 20 wiadomości (10 par pytanie-odpowiedź)
            if len(conversation_history) > 20:
                # Zachowaj ostatnie 16 wiadomości + informuj o skróceniu
                old_count = len(conversation_history)
                conversation_history = conversation_history[-16:]
                print(f"\n💡 Historia skrócona z {old_count} do {len(conversation_history)} wiadomości")
            
        except KeyboardInterrupt:
            print("\n\n⚠️  Przerwano przez Ctrl+C")
            break
            
        except Exception as e:
            print(f"\n❌ Błąd: {e}")
            print("🔄 Spróbuj ponownie...")
            continue

if __name__ == "__main__":
    # Sprawdź klucz API
    if not os.getenv('TOGETHER_API_KEY'):
        print("❌ Brak klucza TOGETHER_API_KEY w zmiennych środowiskowych!")
        print("💡 Ustaw klucz: export TOGETHER_API_KEY='twój_klucz'")
        exit(1)
    
    main()