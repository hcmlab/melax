from ollama import chat

def chatbot():
    # Initialize the conversation with a system message
    messages = [
        {
            'role': 'system',
            'content': 'You are a helpful and knowledgeable assistant that answers questions short and clear.',
        }
    ]

    print("Chatbot initialized. Type 'exit' to end the conversation.")

    while True:
        # User input
        user_input = input("You: ")
        if user_input.lower() == 'exit':
            print("Chatbot session ended.")
            break

        # Add user message to the conversation
        messages.append({'role': 'user', 'content': user_input})

        # Stream assistant's response
        print("Assistant: ", end='', flush=True)
        try:
            stream = chat(model='llama3.2', messages=messages, stream=True)
            response_content = ""
            for chunk in stream:
                # Append chunks of assistant response
                response_content += chunk['message']['content']
                print(chunk['message']['content'], end='', flush=True)
            print()  # Add a newline after the assistant's response

            # Add the assistant's response to the conversation
            messages.append({'role': 'assistant', 'content': response_content})

        except Exception as e:
            print(f"\nError: {e}")
            break

if __name__ == "__main__":
    chatbot()
