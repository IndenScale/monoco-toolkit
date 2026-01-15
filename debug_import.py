import sys
import os
sys.path.append(os.getcwd())

try:
    print("Importing monoco.main...")
    import monoco.main
    print("Import successful.")
except Exception as e:
    print(f"Import failed: {e}")
    import traceback
    traceback.print_exc()
