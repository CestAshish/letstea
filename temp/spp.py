from groq import Groq

# Initialize the client
client = Groq()

# Set up conversation parameters
model_name = "llama-3.1-8b-instant"
temperature = .1
max_tokens = 1024
top_p = 1

# Initialize the conversation history
messages = []

print("Chatbot: Hello! How can I assist you today? Type 'exit' to end the conversation.")

while True:
    # Get user input
    user_input = input("You: ")
    if user_input.lower() == 'exit':
        print("Chatbot: Goodbye! Have a great day!")
        break

    # Add user message to conversation history
    messages.append({"role": "user", "content": user_input})

    # Generate response from the model
    completion = client.chat.completions.create(
        model=model_name,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
        top_p=top_p,
        stream=True,
        stop=None,
    )

    # Print the chatbot's response
    print("Chatbot: ", end="")
    for chunk in completion:
        # Get the content of each chunk and print it
        print(chunk.choices[0].delta.content or "", end="")

    # Add chatbot's response to conversation history
    bot_response = "".join([chunk.choices[0].delta.content or "" for chunk in completion])
    messages.append({"role": "assistant", "content": bot_response})

    print("\n")  # New line for readability between conversation turns
