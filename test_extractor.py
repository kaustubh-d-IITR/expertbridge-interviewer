import os
import sys

# Add project root to path
sys.path.append(os.path.abspath("."))

from src.core.brain import Brain
from src.ingestion.cv_parser import extract_profile_to_json
import dotenv

dotenv.load_dotenv()

# Dummy resume text
dummy_resume = """
John Doe
Software Engineer
Email: john@example.com

EXPERIENCE:
Senior Developer at Acme Corp (2020-2023)
- Built an AI-driven matching engine using Python, Redis, and OpenAI APIs. Resulted in 20% latency reduction.

PROJECTS:
Data Pipeline Migration
- Migrated legacy ETL pipelines to Apache Airflow and Snowflake.

SKILLS:
Python, SQL, React, AWS
"""

try:
    print("Initializing Brain...")
    brain = Brain()
    print("Calling Extractor...")
    extract_profile_to_json(dummy_resume, brain)
    print("Extraction Complete.")
except Exception as e:
    print(f"Error during test: {e}")
