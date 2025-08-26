from google import genai

client = genai.Client(api_key="AIzaSyDmeXKxN1lCxwsyua5zCZm3pK44_a08fdI")

response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents="Explain how AI works in a few words",
)

print(response.text)


def suggest_idea():
    