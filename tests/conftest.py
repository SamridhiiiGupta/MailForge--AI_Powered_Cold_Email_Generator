"""
Pytest configuration: inject dummy environment variables before any app
module is imported, so unit tests that don't touch the LLM never need
a real API key.
"""

import os

# Set all required env vars before app modules are imported.
# These values are only used during the test session.
os.environ.setdefault("GROQ_API_KEY", "test-dummy-key-not-used-in-unit-tests")
os.environ.setdefault("ENV", "development")
os.environ.setdefault("LOG_LEVEL", "WARNING")   # Keep test output quiet
