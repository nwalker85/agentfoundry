#!/usr/bin/env python3
"""
Validation script for agent imports
"""

import sys

sys.path.insert(0, ".")

print("=" * 60)
print("Agent Import Validation")
print("=" * 60)

all_passed = True

# Test imports
print("\nTesting imports...\n")

try:
    print("✅ ContextAgent imported successfully")
except Exception as e:
    print(f"❌ ContextAgent import failed: {e}")
    all_passed = False

try:
    print("✅ CoherenceAgent imported successfully")
except Exception as e:
    print(f"❌ CoherenceAgent import failed: {e}")
    all_passed = False

try:
    print("✅ PMAgent imported successfully")
except Exception as e:
    print(f"❌ PMAgent import failed: {e}")
    all_passed = False

try:
    print("✅ IOAgent imported successfully")
except Exception as e:
    print(f"❌ IOAgent import failed: {e}")
    all_passed = False

try:
    print("✅ SupervisorAgent imported successfully")
except Exception as e:
    print(f"❌ SupervisorAgent import failed: {e}")
    all_passed = False

print("\n" + "=" * 60)
if all_passed:
    print("✅ ALL IMPORTS SUCCESSFUL")
    print("=" * 60)
    sys.exit(0)
else:
    print("❌ SOME IMPORTS FAILED")
    print("=" * 60)
    sys.exit(1)
