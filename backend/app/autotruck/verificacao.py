"""Recálculo independente — 3ª via de auditoria (prova anti-mock).

Reimplementa a apuração com loops elementares, SEM importar nada de
`engine.py`. Se o engine devolvesse valores "chumbados", esta função
divergiria. Usada nos testes e embutida nas planilhas de simulação.
"""

import math


def _cotas(fipe: float, p) -> float:
    if fipe > p.fipe_cota_especial:
        return p.multiplicador_especial
    faixas = max(0, math.ceil(fipe / p.faixa_fipe) - 1)
    return round(p.cota_base + p.passo_cota * faixas, 2)


def _preco_terc(cob: str, p) -> float:
    return {"NENHUM": 0.0, "50K": p.preco_terceiros_50k, "100K": p.preco_terceiros_100k}.get(
        (cob or "NENHUM").upper(), 0.0
    )


def recomputar(veiculos, eventos, params) -> dict:
    """Recomputa cota/potes por LEVES/MOTOS de forma independente do engine."""
    elig = [v for v in veiculos if v.status_ativo and v.adimplente]
    cotas = {"LEVES": 0.0, "MOTOS": 0.0}
    for v in elig:
        if v.segmento in cotas:
            cotas[v.segmento] += _cotas(v.valor_fipe, params)

    out = {}
    for seg in ("LEVES", "MOTOS"):
        ci = cp = ds = df = rt = 0.0
        for e in eventos:
            if e.segmento != seg:
                continue
            tipo = e.tipo_evento
            if tipo != "INTEGRAL" and e.valor_fipe > 0 and \
               e.orcamento_reparo > params.threshold_perda_total * e.valor_fipe:
                tipo = "INTEGRAL"
            custo = e.valor_fipe if tipo == "INTEGRAL" else e.valor_evento
            if e.envolvimento == "TERCEIRO":
                rt += custo
                continue
            if tipo == "INTEGRAL":
                ci += custo
            else:
                cp += custo
            if e.salvado_liquidado:
                ds += e.valor_salvado
            df += e.franquia
        # N3: terceiro NÃO abate a cota variável
        custo_a_ratear = round(ci + cp - ds - df, 2)
        base = round(cotas[seg], 2)
        out[seg] = {
            "custo_integrais": round(ci, 2),
            "custo_parciais": round(cp, 2),
            "deducao_salvados": round(ds, 2),
            "deducao_franquias": round(df, 2),
            "recuperacao_terceiros": round(rt, 2),
            "custo_a_ratear": custo_a_ratear,
            "cotas_ativas": base,
            "valor_cota": round(custo_a_ratear / base, 2) if base > 0 else 0.0,
        }

    # Potes
    tem_cob = any((v.cobertura_terceiros or "NENHUM").upper() != "NENHUM" for v in elig)
    if tem_cob:
        terc_arrec = round(sum(_preco_terc(v.cobertura_terceiros, params) for v in elig), 2)
    elif params.valor_fixo_terceiros_por_assoc > 0:
        terc_arrec = round(params.valor_fixo_terceiros_por_assoc * len(elig), 2)
    else:
        terc_arrec = round(params.arrecadacao_terceiros_estimada, 2)
    terc_custo = round(sum(
        (e.valor_fipe if e.tipo_evento == "INTEGRAL" else e.valor_evento)
        for e in eventos if e.envolvimento == "TERCEIRO"
    ), 2)

    n_pes = sum(1 for v in elig if v.segmento == "PESADOS")
    if params.preco_casco_caminhao > 0:
        cam_arrec = round(params.preco_casco_caminhao * n_pes, 2)
    elif params.valor_fixo_caminhao_por_assoc > 0:
        cam_arrec = round(params.valor_fixo_caminhao_por_assoc * n_pes, 2)
    else:
        cam_arrec = round(params.arrecadacao_caminhao_estimada, 2)
    cam_custo = round(sum(
        (e.valor_fipe if e.tipo_evento == "INTEGRAL" else e.valor_evento)
        for e in eventos if e.segmento == "PESADOS" and e.envolvimento == "ASSOCIADO"
    ), 2)

    out["POTES"] = {
        "terceiros_arrecadado": terc_arrec,
        "terceiros_custo": terc_custo,
        "caminhao_arrecadado": cam_arrec,
        "caminhao_custo": cam_custo,
    }
    out["total_veiculos"] = len(veiculos)
    out["total_elegiveis"] = len(elig)
    return out
