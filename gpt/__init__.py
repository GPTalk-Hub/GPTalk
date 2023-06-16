import openai
import os
from dotenv import load_dotenv

load_dotenv()

openai.organization = os.environ.get("OPEN_AI_ORG_ID")
openai.api_key = os.environ.get("OPEN_AI_AUTH_KEY")
