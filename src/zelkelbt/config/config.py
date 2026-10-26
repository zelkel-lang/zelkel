from pathlib import Path


def has_config():
    return Path("zelkel.toml").is_file()
