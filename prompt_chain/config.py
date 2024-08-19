import os

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

DB_URL = os.getenv("DB_URL", "sqlite:///prompt_chain.db")
