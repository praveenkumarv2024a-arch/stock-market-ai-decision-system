
import sys
import os
sys.path.append(os.getcwd())

from src.models.explain import ModelExplainer
import traceback

try:
    print("Testing Explanation for AXISBANK.NS...")
    explainer = ModelExplainer()
    print("Explainer initialized.")
    
    # 1. Test Text Explanation
    print("\n[1] Testing Natural Language Explanation...")
    try:
        text = explainer.get_natural_language_explanation("AXISBANK.NS")
        print(f"Result: {text.encode('utf-8', 'ignore')}")
    except Exception as e:
        print(f"FAILED (Text): {e}")
        traceback.print_exc()

    # 2. Test Plot Generation
    print("\n[2] Testing Plot Generation...")
    try:
        explainer.explain_latest("AXISBANK.NS")
        print("Plot generation function called.")
        
        path = "data/AXISBANK.NS_explanation.png"
        if os.path.exists(path):
            print(f"SUCCESS: Plot created at {path}")
        else:
            print("FAILED: File does not exist after call.")
            
    except Exception as e:
        print(f"FAILED (Plot): {e}")
        traceback.print_exc()

except Exception as e:
    print(f"Global Crash: {e}")
    traceback.print_exc()
