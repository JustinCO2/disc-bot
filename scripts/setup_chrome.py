import sys, os
sys.path.insert(0, os.getcwd())
from utils.setup_chrome_testing_binaries.py import setup_chrome_testing_binaries

def main():
    setup_chrome_testing_binaries()

if __name__ == "__main__":
    main()