import os
from dotenv import load_dotenv

load_dotenv()

deepseek_client = None
api_key = os.getenv("DEEPSEEK_API_KEY")
if api_key and api_key.startswith("sk-"):
    from openai import OpenAI
    deepseek_client = OpenAI(
        api_key=api_key,
        base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1"),
    )
