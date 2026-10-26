import sys
import tomllib
from pathlib import Path


def has_config():
    return Path("zelkel.toml").is_file()

def get_config():
    if not has_config():
        print("Not in a Zelkel project: No zelkel.toml found")
        sys.exit(1)
    
    with open("zelkel.toml", "rb") as f:
        data = tomllib.load(f)
    
    return data