from together import Together

print("🤖 Witaj w interaktywnym chacie z Together AI!")
print("💡 Wpisz 'quit' lub 'exit' żeby zakończyć")
print("-" * 50)

client = Together()
conversation_history = []

while True:
    # Pobierz wiadomość od użytkownika
    user_input = input("\n👤 Ty: ").strip()
    
    # Sprawdź czy użytkownik chce wyjść
    if user_input.lower() in ['quit', 'exit', 'bye', 'koniec']:
        print("👋 Do zobaczenia!")
        break
    
    # Pomiń puste wiadomości
    if not user_input:
        continue
    
    # Dodaj wiadomość użytkownika do historii
    conversation_history.append({"role": "user", "content": user_input})
    
    try:
        print("🤖 Bot: ", end="", flush=True)
        
        # Wyślij zapytanie do AI
        response = client.chat.completions.create(
            model="deepseek-ai/DeepSeek-R1-Distill-Llama-70B-free",
            messages=conversation_history,
            max_tokens=500,
            temperature=0.7
        )
        
        # Pobierz odpowiedź
        bot_response = response.choices[0].message.content
        print(bot_response)
        
        # Dodaj odpowiedź bota do historii
        conversation_history.append({"role": "assistant", "content": bot_response})
        
        # Ogranicz historię do ostatnich 10 wiadomości (żeby nie przekroczyć limitów)
        if len(conversation_history) > 10:
            conversation_history = conversation_history[-10:]
            
    except Exception as e:
        print(f"❌ Błąd: {e}")
        print("Spróbuj ponownie...")