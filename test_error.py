import sys, os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
from server.voice_pipeline_adapter import _invoke_genesis_core

# Reproduce the exact problem condition identified in Step 3
res = _invoke_genesis_core({}, "Thank you.")
print("FINAL RESPONSE:", res)
import time; time.sleep(8)
