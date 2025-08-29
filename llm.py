from langchain.chat_models import init_chat_model

chat_model = init_chat_model(
    model="gemini-2.5-flash",
    model_provider="google_genai",
    temperature=0.7,
)
