#!/usr/bin/env python3
"""
Test Runner Script - Otomatik test çalıştırma
"""
import subprocess
import sys
import os
from pathlib import Path

# Proje kök dizini
project_root = Path(__file__).parent.parent.parent
os.chdir(project_root)

def run_tests():
    """Tüm testleri çalıştır"""
    print("🧪 Testler başlatılıyor...\n")
    
    # Pytest komutu
    cmd = [
        sys.executable, "-m", "pytest",
        "backend/tests",
        "-v",
        "--tb=short",
        "--color=yes"
    ]
    
    # Coverage ekle (opsiyonel)
    if "--coverage" in sys.argv:
        cmd.extend(["--cov=backend", "--cov-report=html", "--cov-report=term"])
    
    # Sadece belirli testleri çalıştır
    if "--unit" in sys.argv:
        cmd.extend(["-m", "unit"])
    elif "--integration" in sys.argv:
        cmd.extend(["-m", "integration"])
    elif "--api" in sys.argv:
        cmd.extend(["-m", "api"])
    
    result = subprocess.run(cmd)
    return result.returncode

if __name__ == "__main__":
    exit_code = run_tests()
    sys.exit(exit_code)

