# weather_mcp/config.py
import tomllib
from pathlib import Path

CONFIG_PATH = Path(__file__).resolve().parents[2] / "pyproject.toml"

with open(CONFIG_PATH, "rb") as f:
    config = tomllib.load(f)

server_config = config["tool"]["server"]
