import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ.setdefault("RATEIO_REPOSITORY", "json")
os.environ.setdefault("RATEIO_JSON_PATH", "/home/ronaldim/Mut/dados_simulados.json")
