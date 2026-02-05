
import sys
import importlib.util

def check_import(module_name, pip_name=None):
    if pip_name is None:
        pip_name = module_name
    if importlib.util.find_spec(module_name) is None:
        print(f"[FAIL] {pip_name} is NOT installed.")
        return False
    else:
        print(f"[OK] {pip_name} is installed.")
        return True

print("--- Python Environment Check ---")
print(f"Python Version: {sys.version.split()[0]}")

# 1. Check Torch & GPU
try:
    import torch
    print(f"[OK] torch is installed (version: {torch.__version__})")
    
    if torch.cuda.is_available():
        print(f"[OK] GPU is available via torch.cuda (Count: {torch.cuda.device_count()})")
        print(f"     Device Name: {torch.cuda.get_device_name(0)}")
        
        # Test small tensor allocation
        try:
            x = torch.ones(1).cuda()
            print("[OK] Tensor allocation on GPU successful.")
        except Exception as e:
            print(f"[FAIL] Tensor allocation on GPU failed: {e}")
    else:
        print("[FAIL] torch.cuda.is_available() is False. GPU will NOT be used.")
except ImportError:
    print("[FAIL] torch is NOT installed.")

# 2. Check Core ML Libs
check_import("transformers")
check_import("datasets")
check_import("peft")
check_import("accelerate")

# 3. Check IndicTransToolkit (for dataset generation)
if check_import("IndicTransToolkit"):
    # Optional: Check if IndicProcessor is importable
    try:
        from IndicTransToolkit.processor import IndicProcessor
        print("[OK] IndicTransToolkit.processor.IndicProcessor imported successfully.")
    except ImportError as e:
        print(f"[FAIL] Error importing IndicProcessor: {e}")

# 4. Check bitsandbytes (for 4-bit quantization)
if check_import("bitsandbytes"):
    try:
        import bitsandbytes as bnb
        print(f"[OK] bitsandbytes imported (version: {bnb.__version__})")
    except Exception as e:
        print(f"[FAIL] Error importing bitsandbytes: {e}")

print("--- End Check ---")
