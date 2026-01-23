import os

# The script is in agcoding/, so the project root is one level up.
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Directories to create, relative to the project root.
directories = [
    "docs/concept",
    "docs/devlogs"
]

for directory in directories:
    # Create the full path
    path = os.path.join(project_root, directory)
    # Create the directory, ignoring errors if it already exists.
    os.makedirs(path, exist_ok=True)
    print(f"Ensured directory exists: {path}")
