"""Settings read from environment variables, with safe defaults for local use.

Keeping settings out of the code means the same code runs on your laptop,
in Docker and on a server, just by changing environment variables.
"""
import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./kb.db")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
