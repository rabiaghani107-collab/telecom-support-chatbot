"""
Configuration settings for the Telecom Support Chatbot.
Centralizes all environment variables, model settings, and application constants.
"""

import os
from dotenv import load_dotenv

load_dotenv()

# ── OpenAI Configuration ──────────────────────────────────────────────
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4")
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.3"))

# ── LangSmith Tracing (Bonus Feature) ────────────────────────────────
LANGSMITH_TRACING = os.getenv("LANGCHAIN_TRACING_V2", "false").lower() == "true"
LANGSMITH_API_KEY = os.getenv("LANGCHAIN_API_KEY") 
LANGSMITH_PROJECT = os.getenv("LANGCHAIN_PROJECT", "telecom-support-chatbot")

# ── Database Configuration ────────────────────────────────────────────
DATABASE_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "telecom.db")

# ── RAG / Vector Store Configuration ──────────────────────────────────
KNOWLEDGE_BASE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "knowledge_base")
CHROMA_PERSIST_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "chroma_db")
EMBEDDING_MODEL = "text-embedding-3-small"
RAG_CHUNK_SIZE = 500
RAG_CHUNK_OVERLAP = 50
RAG_TOP_K = 3

# ── Application Constants ─────────────────────────────────────────────
APP_TITLE = "TelcoBot — AI Customer Support Assistant"
APP_DESCRIPTION = "Intelligent customer support for TelcoMax powered by LangChain & LangGraph"
MAX_HISTORY_TURNS = 20
