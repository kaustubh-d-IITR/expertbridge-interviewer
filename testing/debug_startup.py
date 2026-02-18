import os
import sys

# Add src to path
sys.path.append(os.getcwd())

print("Importing modules...")
try:
    from dotenv import load_dotenv
    load_dotenv(override=True)
    print("Dotenv loaded.")
    
    import streamlit as st
    print("Streamlit imported.")
    
    from src.core.orchestrator import Orchestrator
    print("Orchestrator imported.")
    
    print("Initializing Orchestrator...")
    orc = Orchestrator()
    print("Orchestrator initialized.")
    
    print("Initializing Brain...")
    # Brain is init in Orchestrator, but let's test it explicitly if needed
    from src.core.brain import Brain
    brain = Brain()
    print("Brain initialized.")
    
    print("All checks passed.")
except Exception as e:
    print(f"CRASHED: {e}")
    import traceback
    traceback.print_exc()
