# --- TEMPORARY VERIFICATION CODE ---
import sys
import platform
import os
import time

def verify_environment():
    # Get the path to the currently running Python executable
    exe_path = sys.executable 
    
    # Get the name of the active conda environment
    conda_env = os.environ.get('CONDA_DEFAULT_ENV', 'Base/None')
    
    print("-" * 50)
    print("VERIFICATION CHECK: ACTIVE PYTHON ENVIRONMENT")
    print(f"Time: {time.ctime()}")
    print(f"Python Version: {platform.python_version()}")
    print(f"Conda Environment Name: {conda_env}")
    print(f"Executable Path: {exe_path}")
    print("-" * 50)

verify_environment()
# --- END VERIFICATION CODE ---

# The rest of your ResourceEngine.py code follows below...
from experta import Fact, Field, KnowledgeEngine, Rule, MATCH, TEST
# ...