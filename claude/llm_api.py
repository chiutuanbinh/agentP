import anthropic

client = anthropic.Client()

message = client.messages.create(
    model="claude-opus-4-7",
    max_tokens=1000,
    messages=[
        {
            "role": "user",
            "content": "Write a haiku about the ocean."
        }
    ]
)
print(message.content)