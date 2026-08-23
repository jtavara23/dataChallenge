import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("API_KEY", "globant-challenge-jtavara")
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data-challenge.db")
