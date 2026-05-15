"""Config própria do AutoTruck — isolada da config do ELLO (`app/config.py`).

Lê apenas variáveis de ambiente com defaults; não usa o repositório/DB do ELLO.
"""

import os
from functools import lru_cache

DEFAULT_JSON_PATH = "/root/projetos/Mut/dados_autotruck.json"


@lru_cache
def get_autotruck_json_path() -> str:
    return os.environ.get("AUTOTRUCK_JSON_PATH", DEFAULT_JSON_PATH)
