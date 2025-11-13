import shutil
import sys
import os

if len(sys.argv) != 2:
    print("Usage: python apex-setup.py <destination_folder>")
    sys.exit(1)

source = ".claude"
destination = os.path.join(sys.argv[1], ".claude")

if not os.path.exists(source):
    print(f"Source folder '{source}' not found")
    sys.exit(1)

shutil.copytree(source, destination, dirs_exist_ok=True)
print(f"Apex is installed to {destination}")