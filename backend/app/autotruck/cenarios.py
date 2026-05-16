"""Cenários de simulação AutoTruck — distintos, determinísticos e auditáveis.

NÃO são dados mocados: cada veículo/evento é construído com regra explícita
(FIPE realista, cobertura contratada, eventos nomeados do levantamento —
Mercedes GLA, BMW GS 1200, Porsche). Seed fixo por cenário ⇒ reprodutível.
Inputs e saídas são exportados em planilha com fórmulas nativas que
recomputam tudo (ver tools/gerar_planilhas.py).

Três cenários que fazem regras distintas dispararem:
  A  Mês saudável            — cota na faixa R$30–35, potes com gordura.
  B  Estresse sazonal (jan)  — sinistro catastrófico (>25% pool), regra dos
                               75% (BMW GS), cota especial (Porsche), PT de
                               caminhão estourando o teto do pote.
  C  Inadimplência alta      — modelo purista esvazia o denominador.
"""

import random
from dataclasses import dataclass, field

from .domain import EventoAT, VeiculoAT
from .rules import ParametrosAT, cotas_por_fipe

_LEVES = ["AUTOMOVEL", "UTILITÁRIO"]
_COBERTURAS = ["NENHUM", "50K", "100K"]


@dataclass
class Cenario:
    nome: str
    titulo: str
    descricao: str
    mes_ano_ref: str
    veiculos: list[VeiculoAT]
    eventos: list[EventoAT]
    params: ParametrosAT
    historico_cotas: dict[str, list[float]] = field(default_factory=dict)
    esperado: dict = field(default_factory=dict)


def _placa(rng: random.Random) -> str:
    L = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    return f"{''.join(rng.choice(L) for _ in range(3))}{rng.randint(0,9)}{rng.choice(L)}{rng.randint(10,99)}"


def _split(total: float, n: int, rng: random.Random) -> list[float]:
    """Divide `total` em n parcelas positivas; última absorve o resto (soma EXATA)."""
    if n <= 1:
        return [round(total, 2)]
    pesos = [rng.uniform(0.6, 1.4) for _ in range(n)]
    s = sum(pesos)
    vals = [round(total * w / s, 2) for w in pesos[:-1]]
    vals.append(round(total - sum(vals), 2))
    return vals


def _frota(rng: random.Random, n_leves: int, n_motos: int, n_pesados: int,
           inadim: float = 0.10, inativo: float = 0.05) -> list[VeiculoAT]:
    """Frota realista: FIPE por faixa, cobertura de terceiros contratada,
    serviços adicionais tabelados, parcela inadimplente/inativa controlada."""
    vs: list[VeiculoAT] = []
    vid = 0

    def add(seg, tipo, fipe):
        nonlocal vid
        vid += 1
        vs.append(VeiculoAT(
            id_veiculo=f"{seg[:1]}{vid:05d}", placa=_placa(rng), segmento=seg,
            tipo_veiculo=tipo, valor_fipe=float(fipe),
            status_ativo=rng.random() > inativo,
            adimplente=rng.random() > inadim,
            servicos_adicionais=float(rng.choice([0, 0, 0, 29.9, 49.9, 79.9])),
            cobertura_terceiros=rng.choices(_COBERTURAS, weights=[0.35, 0.40, 0.25])[0],
        ))

    for _ in range(n_leves):
        if rng.random() < 0.025:                       # ~2,5% premium > R$450k
            add("LEVES", "PREMIUM", rng.randint(460_000, 850_000))
        else:
            add("LEVES", rng.choice(_LEVES), rng.randint(25_000, 180_000))
    for _ in range(n_motos):
        add("MOTOS", "MOTOCICLETA", rng.randint(8_000, 60_000))
    for _ in range(n_pesados):
        add("PESADOS", rng.choice(["CAMINHAO", "SEMI REBOQUE"]), rng.randint(160_000, 520_000))
    return vs


def _cotas_seg(veics: list[VeiculoAT], seg: str, p: ParametrosAT) -> float:
    return round(sum(
        cotas_por_fipe(v.valor_fipe, p)[0]
        for v in veics if v.segmento == seg and v.status_ativo and v.adimplente
    ), 2)


def _eventos_para_cota(veics, seg, cota_alvo, n_int, n_par, rng, p, dia0=1) -> list[EventoAT]:
    """Gera eventos ASSOCIADO cuja soma = cota_alvo × cotas ativas do segmento.
    Integral entra pelo FIPE; parcial pelo valor de oficina."""
    base = _cotas_seg(veics, seg, p)
    total = round(cota_alvo * base, 2)
    integral = round(total * 0.62, 2)
    parcial = round(total - integral, 2)
    out: list[EventoAT] = []
    eid = [0]

    def mk(env, tipo, custo):
        eid[0] += 1
        fipe = round(custo, 2) if tipo == "INTEGRAL" else round(custo * rng.uniform(1.4, 2.2), 2)
        val = round(custo, 2) if tipo != "INTEGRAL" else round(custo * rng.uniform(0.85, 1.0), 2)
        out.append(EventoAT(
            id_evento=f"{seg[:1]}EV-{eid[0]:04d}", protocolo=f"PRT{seg[:1]}{eid[0]:05d}",
            placa=_placa(rng), segmento=seg, envolvimento=env, tipo_evento=tipo,
            valor_evento=val, orcamento_reparo=round(custo * 0.45, 2), valor_fipe=fipe,
            data_aviso=f"2025-{rng.randint(1,11):02d}-{rng.randint(1,28):02d}",
            franquia=0.0, valor_salvado=0.0, salvado_liquidado=False, postergado=False,
        ))

    for v in _split(integral, n_int, rng):
        if v > 0:
            mk("ASSOCIADO", "INTEGRAL", v)
    for v in _split(parcial, n_par, rng):
        if v > 0:
            mk("ASSOCIADO", "PARCIAL", v)
    return out


# ---------------------------------------------------------------- Cenário A

def cenario_a() -> Cenario:
    rng = random.Random(101)
    p = ParametrosAT(preco_casco_caminhao=1_500.0)
    veics = _frota(rng, n_leves=600, n_motos=180, n_pesados=45, inadim=0.08, inativo=0.04)
    evs = _eventos_para_cota(veics, "LEVES", 32.50, 14, 26, rng, p)
    evs += _eventos_para_cota(veics, "MOTOS", 31.00, 6, 12, rng, p)
    # PESADOS sem PT no mês → pote caminhão fica com a gordura (transcrição:
    # "se nenhum caminhão bater, tá lá o superávit").
    return Cenario(
        nome="A", titulo="Mês saudável (operação estável)",
        descricao=("Sinistralidade normal: cota LEVES/MOTOS dentro da faixa de "
                   "estabilização (R$30–35), potes Terceiros e Caminhão com "
                   "gordura, sem alerta de volatilidade. Demonstra o regime estável."),
        mes_ano_ref="06/2025", veiculos=veics, eventos=evs, params=p,
        esperado={"cota_leves_faixa": "OK", "alerta_volatilidade": False,
                  "pote_caminhao_reserva_positiva": True},
    )


# ---------------------------------------------------------------- Cenário B

def cenario_b() -> Cenario:
    rng = random.Random(202)
    p = ParametrosAT(preco_casco_caminhao=1_500.0)
    veics = _frota(rng, n_leves=600, n_motos=180, n_pesados=45, inadim=0.08, inativo=0.04)
    # garante ao menos 1 Porsche > R$450k (cota especial ×20)
    veics.append(VeiculoAT("LPORSCHE", _placa(rng), "LEVES", "PREMIUM", 720_000.0,
                            True, True, 79.9, "100K"))
    evs = _eventos_para_cota(veics, "LEVES", 33.00, 12, 22, rng, p, dia0=1)
    evs += _eventos_para_cota(veics, "MOTOS", 30.00, 5, 10, rng, p)
    # Sinistro catastrófico — Mercedes GLA R$400k (caso do levantamento):
    evs.append(EventoAT(
        id_evento="LEV-CAT-GLA", protocolo="PRTL99001", placa="GLA4A01",
        segmento="LEVES", envolvimento="ASSOCIADO", tipo_evento="INTEGRAL",
        valor_evento=395_000.0, orcamento_reparo=400_000.0, valor_fipe=400_000.0,
        data_aviso="2025-01-08", franquia=0.0, valor_salvado=0.0,
        salvado_liquidado=False, postergado=False,
    ))
    # BMW GS 1200 — parcial cujo orçamento excede 75% da FIPE → vira INTEGRAL:
    evs.append(EventoAT(
        id_evento="LEV-BMWGS", protocolo="PRTL99002", placa="GS12B07",
        segmento="LEVES", envolvimento="ASSOCIADO", tipo_evento="PARCIAL",
        valor_evento=78_000.0, orcamento_reparo=78_000.0, valor_fipe=98_000.0,
        data_aviso="2025-01-15", franquia=0.0, valor_salvado=0.0,
        salvado_liquidado=False, postergado=False,
    ))
    # Recuperação de terceiros (rastreada, NÃO abate — N3):
    evs.append(EventoAT(
        id_evento="LEV-TERC", protocolo="PRTL99003", placa="TRC0A11",
        segmento="LEVES", envolvimento="TERCEIRO", tipo_evento="PARCIAL",
        valor_evento=52_000.0, orcamento_reparo=1.0, valor_fipe=80_000.0,
        data_aviso="2025-01-20", franquia=0.0, valor_salvado=0.0,
        salvado_liquidado=False, postergado=False,
    ))
    # PESADOS — vários PTs estourando o teto do pote caminhão → postergação:
    for i, custo in enumerate((360_000.0, 340_000.0, 320_000.0, 300_000.0, 280_000.0), 1):
        evs.append(EventoAT(
            id_evento=f"PEV-CAT-{i}", protocolo=f"PRTP9{i:03d}", placa=_placa(rng),
            segmento="PESADOS", envolvimento="ASSOCIADO", tipo_evento="INTEGRAL",
            valor_evento=custo, orcamento_reparo=custo, valor_fipe=custo,
            data_aviso=f"2025-01-{10+i:02d}", franquia=0.0, valor_salvado=0.0,
            salvado_liquidado=False, postergado=False,
        ))
    return Cenario(
        nome="B", titulo="Estresse sazonal (janeiro — alta sinistralidade)",
        descricao=("Mês de pico: sinistro catastrófico Mercedes GLA R$400k "
                   "(>25% do pool → alerta de volatilidade); BMW GS 1200 "
                   "parcial reclassificado p/ INTEGRAL pela regra dos 75%; "
                   "Porsche R$720k (cota especial ×20); PTs de caminhão "
                   "estourando o teto do pote (postergação). Cota acima da "
                   "faixa → assistente de ajuste atua."),
        mes_ano_ref="01/2025", veiculos=veics, eventos=evs, params=p,
        historico_cotas={"LEVES": [31.0, 32.0, 33.0], "MOTOS": [29.0, 30.0, 30.5]},
        esperado={"cota_leves_faixa": "ACIMA", "alerta_volatilidade": True,
                  "reclassificado_75pct_min": 1, "tem_cota_especial": True,
                  "eventos_postergados_min": 1},
    )


# ---------------------------------------------------------------- Cenário C

def cenario_c() -> Cenario:
    rng = random.Random(303)
    p = ParametrosAT(preco_casco_caminhao=1_500.0)
    # inadimplência/inatividade altas → modelo purista esvazia o denominador
    veics = _frota(rng, n_leves=600, n_motos=180, n_pesados=45, inadim=0.32, inativo=0.12)
    evs = _eventos_para_cota(veics, "LEVES", 34.00, 12, 20, rng, p)
    evs += _eventos_para_cota(veics, "MOTOS", 32.00, 5, 10, rng, p)
    return Cenario(
        nome="C", titulo="Inadimplência alta (modelo purista)",
        descricao=("~32% inadimplentes + ~12% inativos. O denominador usa só "
                   "veículos ativos E adimplentes — a inadimplência NÃO é "
                   "socializada (não entra no rateio); inadimplente não gera "
                   "boleto. Demonstra o purismo do modelo."),
        mes_ano_ref="07/2025", veiculos=veics, eventos=evs, params=p,
        esperado={"elegiveis_menor_que_total": True},
    )


CENARIOS = {"A": cenario_a, "B": cenario_b, "C": cenario_c}


def build(nome: str) -> Cenario:
    return CENARIOS[nome.upper()]()
