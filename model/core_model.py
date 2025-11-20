from ollama import Client

client = Client(host='http://localhost:11434')

def chat():
    print("Chat started. Type 'exit' to quit.\n")
    msgs = []

    while True:
        user = input("You: ")
        if user.lower() == "exit":
            break

        msgs.append({"role": "user", "content": user})

        response = client.chat(model="llama3.1", messages=msgs)
        reply = response['message']['content']
        print("Llama:", reply)

        msgs.append({"role": "assistant", "content": reply})

if __name__ == "__main__":
    chat()
