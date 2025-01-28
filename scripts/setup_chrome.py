import sys
import os

# Ensure `/app` is in Python's search path so `utils` is importable
sys.path.insert(0, os.getcwd())

from utils.setup_chrome_testing_binaries import setup_chrome_testing_binaries

def main():
    setup_chrome_testing_binaries()

if __name__ == "__main__":
    main()
