"""Gera as duas páginas publicadas para apresentar o rateio AVAP no tablet.

1. Demonstração estática: roda o motor de verdade sobre os arquivos de 09/2026 (mesmo caminho do botão
   "Demonstração 09/2026" da tela AVAP) e embute o resultado em demo_estatica_avap.html. Placas saem
   mascaradas e a matrícula não entra. Como carrega números reais da associação, a saída vai para
   AVAP/publicacao/ (fora do git).
2. Cópia publicável do deck decks/rateio-avap-setembro/: troca as bibliotecas por versões fixas dos CDNs
   aceitos pelo Artifact, embute o CSS do AOS e tira as tags de documento.

Uso:
    backend/.venv/bin/python backend/scripts/gerar_publicacao_avap.py --deck-url URL --demo-url URL
"""

import argparse
import json
import re
import sys
import urllib.request
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "backend"))

DESTINO = RAIZ / "AVAP" / "publicacao"
DECK = RAIZ / "decks" / "rateio-avap-setembro" / "index.html"
MOLDE = Path(__file__).with_name("demo_estatica_avap.html")
AOS_CSS = "https://unpkg.com/aos@2.3.1/dist/aos.css"
TROCAS = {
    '<script src="https://cdn.tailwindcss.com"></script>': '<script src="https://cdn.tailwindcss.com/3.4.17"></script>',
    "https://unpkg.com/lucide@latest": "https://unpkg.com/lucide@0.460.0/dist/umd/lucide.min.js",
    "https://d3js.org/d3.v7.min.js": "https://cdn.jsdelivr.net/npm/d3@7.9.0/dist/d3.min.js",
}


def mascara(p):
    return f"{p[:3]}****" if p else None


def dados_demo() -> dict:
    from fastapi.testclient import TestClient

    from app.main import app

    c = TestClient(app)
    sel = c.post("/avap/demo-setembro").json()
    m = "09-2026"
    ev = c.get(f"/avap/{m}/eventos", params={"page_size": 500}).json()
    lanc = c.get(f"/avap/{m}/lancamentos").json()
    res = {k: c.post(f"/avap/{m}/calcular", json={"criterio": k}).json() for k in ["AMBOS", "ASSOCIADO", "TODOS"]}
    res["VEICULO"] = c.post(f"/avap/{m}/calcular", json={"criterio": "VEICULO"}).json()  # por último: boletos vigentes
    itens, pg = [], 1
    while True:
        r = c.get(f"/avap/{m}/boletos", params={"page_size": 500, "page": pg}).json()
        itens += r["items"]
        if len(itens) >= r["total"]:
            break
        pg += 1
    for e in ev["items"]:
        e["placa"] = mascara(e.get("placa"))
    for e in sel["eventos_pendentes"]:
        e["placa"] = mascara(e.get("placa"))
    boletos = [{"placa": mascara(b.get("placa")), "peso_cota": b["peso_cota"],
                "contribuicao_rateio": b["contribuicao_rateio"], "total": b["total"]} for b in itens]
    return {"selecao": sel, "eventos": ev, "lancamentos": lanc, "resultados": res,
            "boletos": {"total": len(boletos), "items": boletos}}


def gerar_demo(deck_url: str) -> Path:
    d = json.dumps(dados_demo(), ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    html = MOLDE.read_text(encoding="utf-8").replace("DECK_URL", deck_url).replace("__DADOS__", d)
    saida = DESTINO / "demo-rateio-avap.html"
    saida.write_text(html, encoding="utf-8")
    return saida


def gerar_deck(demo_url: str) -> Path:
    h = DECK.read_text(encoding="utf-8")
    for a, b in TROCAS.items():
        h = h.replace(a, b)
    aos = urllib.request.urlopen(AOS_CSS).read().decode("utf-8")
    h = h.replace(f'<link href="{AOS_CSS}" rel="stylesheet">', f"<style>{aos}</style>")
    h = re.sub(r"<!DOCTYPE html>\s*<html[^>]*>\s*<head>\s*", "", h, count=1)
    for tag in ['<meta charset="UTF-8">', '<meta name="viewport" content="width=device-width, initial-scale=1.0">',
                "</head>", "</body>", "</html>"]:
        h = h.replace(tag, "")
    h = re.sub(r"<body[^>]*>", "", h, count=1)
    h = h.replace("DEMO_URL", demo_url)
    saida = DESTINO / "rateio-avap-setembro.html"
    saida.write_text(h, encoding="utf-8")
    return saida


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--deck-url", default="DECK_URL")
    ap.add_argument("--demo-url", default="DEMO_URL")
    a = ap.parse_args()
    DESTINO.mkdir(parents=True, exist_ok=True)
    print(gerar_deck(a.demo_url))
    print(gerar_demo(a.deck_url))
