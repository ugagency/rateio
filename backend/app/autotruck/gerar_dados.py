"""Gerador de dados simulados AutoTruck — calibrado para reproduzir
exatamente os agregados da aba ANALITICO do FECHAMENTO (invariante de
validação, análogo ao alvo R$716.964 do ELLO v0).

Determinístico (seed fixo). Uso: `python -m app.autotruck.gerar_dados`.
"""

import json
import random
import sys

# Agregados-alvo extraídos da aba ANALITICO do FECHAMENTO (R$).
ALVOS = {
    "LEVES": {"integral": 1_834_103.63, "parcial": 782_113.49, "terceiros": 756_464.11},
    "MOTOS": {"integral": 453_544.15, "parcial": 46_638.40, "terceiros": 32_982.25},
    "PESADOS": {"integral": 0.0, "parcial": 0.0, "terceiros": 14_000.00},
}

_TIPOS = {
    "LEVES": ["AUTOMOVEL", "UTILITÁRIO", "PREMIUM"],
    "MOTOS": ["MOTOCICLETA"],
    "PESADOS": ["CAMINHAO", "SEMI REBOQUE"],
}
_FIPE_RANGE = {"LEVES": (25_000, 130_000), "MOTOS": (7_000, 45_000), "PESADOS": (150_000, 520_000)}
_QTD_VEIC = {"LEVES": 8000, "MOTOS": 2500, "PESADOS": 600}


def _placa(rng: random.Random) -> str:
    L = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    return f"{''.join(rng.choice(L) for _ in range(3))}{rng.randint(0,9)}{rng.choice(L)}{rng.randint(10,99)}"


def _split(total: float, n: int, rng: random.Random) -> list[float]:
    """Divide `total` em n parcelas positivas; a última absorve o resto (soma EXATA)."""
    if n <= 1:
        return [round(total, 2)]
    pesos = [rng.uniform(0.5, 1.5) for _ in range(n)]
    s = sum(pesos)
    vals = [round(total * w / s, 2) for w in pesos[:-1]]
    vals.append(round(total - sum(vals), 2))
    return vals


def build_dataset(seed: int = 42) -> dict:
    rng = random.Random(seed)
    veiculos: list[dict] = []
    vid = 0
    for seg, qtd in _QTD_VEIC.items():
        lo, hi = _FIPE_RANGE[seg]
        for _ in range(qtd):
            vid += 1
            # ~3% PREMIUM/luxo > R$450k em LEVES (cota especial)
            if seg == "LEVES" and rng.random() < 0.03:
                fipe = rng.randint(460_000, 900_000)
                tipo = "PREMIUM"
            else:
                fipe = rng.randint(lo, hi)
                tipo = rng.choice(_TIPOS[seg])
            veiculos.append({
                "id_veiculo": f"AT-{vid:06d}",
                "placa": _placa(rng),
                "segmento": seg,
                "tipo_veiculo": tipo,
                "valor_fipe": float(fipe),
                "status_ativo": rng.random() > 0.05,      # ~5% inativos
                "adimplente": rng.random() > 0.10,         # ~10% inadimplentes (purista)
                "servicos_adicionais": float(rng.choice([0, 0, 0, 29.9, 49.9, 79.9])),
            })

    eventos: list[dict] = []
    eid = 0

    def add(seg: str, env: str, tipo: str, custo: float):
        nonlocal eid
        eid += 1
        # INTEGRAL: engine usa valor_fipe como custo. PARCIAL/TERCEIRO-parcial: valor_evento.
        fipe = round(custo, 2) if tipo == "INTEGRAL" else round(custo * rng.uniform(1.3, 2.0), 2)
        valor_ev = round(custo, 2) if tipo != "INTEGRAL" else round(custo * rng.uniform(0.8, 1.0), 2)
        eventos.append({
            "id_evento": f"EVT-{eid:05d}",
            "protocolo": f"PRT{eid:06d}",
            "placa": _placa(rng),
            "segmento": seg,
            "envolvimento": env,
            "tipo_evento": tipo,
            "valor_evento": valor_ev,
            "orcamento_reparo": round(custo * 0.5, 2),  # < 75% do FIPE → não reclassifica
            "valor_fipe": fipe,
            "data_aviso": f"2025-{rng.randint(1,12):02d}-{rng.randint(1,28):02d}",
            "franquia": 0.0,
            "valor_salvado": 0.0,
            "salvado_liquidado": False,
            "postergado": False,
        })

    for seg, alvo in ALVOS.items():
        for v in _split(alvo["integral"], 35, rng):
            if v > 0:
                add(seg, "ASSOCIADO", "INTEGRAL", v)
        for v in _split(alvo["parcial"], 55, rng):
            if v > 0:
                add(seg, "ASSOCIADO", "PARCIAL", v)
        for v in _split(alvo["terceiros"], 20, rng):
            if v > 0:
                add(seg, "TERCEIRO", "PARCIAL", v)

    return {"mes_ref": "12/2025", "veiculos": veiculos, "eventos": eventos, "alvos": ALVOS}


def main() -> int:
    from .config import get_autotruck_json_path

    path = sys.argv[1] if len(sys.argv) > 1 else get_autotruck_json_path()
    ds = build_dataset()
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(ds, fh, ensure_ascii=False)
    print(f"OK: {len(ds['veiculos'])} veículos, {len(ds['eventos'])} eventos → {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
