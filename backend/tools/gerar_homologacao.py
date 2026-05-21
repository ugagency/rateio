"""Pacote de homologação para o Rodrigo (AutoTruck).

Lê os 3 arquivos do Remonta/, aplica jitter ±5% sobre valores numéricos,
permuta placas, substitui protocolos por HOM-NNNNN, roda o nosso motor
sobre o resultado, e gera 4 entregáveis + trilha textual:

  simulacoes/HOMOLOGACAO/INPUT_BASE.xlsx
  simulacoes/HOMOLOGACAO/INPUT_RATEIO.xlsx
  simulacoes/HOMOLOGACAO/INPUT_PRODUTOS.xlsx
  simulacoes/HOMOLOGACAO/FECHAMENTO_AutoTruck_Homologacao.xlsx (formato 6-abas)
  docs/evidencias/HOMOLOGACAO_trilha.txt  (interna — não vai pro Rodrigo)

Semente fixa (20260521): cada execução produz o mesmo pacote.
Uso: cd backend && .venv/bin/python -m tools.gerar_homologacao
"""

import random
import shutil
import sys
from pathlib import Path

import openpyxl
from openpyxl.styles import Font, PatternFill

# importa os módulos do app
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.autotruck.engine import calcular_rateio_at
from app.autotruck.ingestao_partes import compor
from tools.gerar_fechamento_motor import _mapa_analitico, _terc_split

SEED = 20260521
JITTER = 0.05            # ±5%
COTAS_LEVES_OVERRIDE = 4275   # base 4500 com jitter -5% (chute calibrado)

ROOT = Path("/root/projetos/Mut")
REMONTA = ROOT / "Remonta"
OUT = ROOT / "simulacoes" / "HOMOLOGACAO"
TRILHA_PATH = ROOT / "docs" / "evidencias" / "HOMOLOGACAO_trilha.txt"
TEMPLATE_FECH = ROOT / "backend" / "tests" / "fixtures" / "FECHAMENTO_referencia.xlsx"

SRC_BASE = REMONTA / "BASE_Reconstruida.xlsx"
SRC_RATEIO = REMONTA / "Rateio_POC_Completo.xlsx"
SRC_PRODUTOS = REMONTA / "Produtos_Reconstruido.xlsx"

OK = PatternFill("solid", fgColor="C6EFCE")
H = Font(bold=True, color="FFFFFF")
HF = PatternFill("solid", fgColor="1F4E79")
MONEY = "#,##0.00"


def _is_num(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def jitter(rng: random.Random, v):
    """±5% multiplicativo. Preserva zero, ints inteiros viram float."""
    if not _is_num(v) or v == 0:
        return v
    fator = 1 + rng.uniform(-JITTER, JITTER)
    return round(v * fator, 2)


def jitter_int(rng: random.Random, v: int) -> int:
    """jitter inteiro com mínimo 1 (preserva contagem positiva)."""
    if not _is_num(v) or v == 0:
        return int(v) if _is_num(v) else v
    fator = 1 + rng.uniform(-JITTER, JITTER)
    return max(1, round(int(v) * fator))


def parse_brl_num(s: str):
    """Converte 'R$ 1.234,56' em float; devolve None se não for número."""
    if not isinstance(s, str):
        return None
    txt = s.strip().replace("R$", "").replace(" ", "")
    if not txt or txt == "-":
        return None
    txt = txt.replace(".", "").replace(",", ".")
    try:
        return float(txt)
    except ValueError:
        return None


def fmt_brl(v: float) -> str:
    """Formata 1234.56 → 'R$ 1.234,56' (estilo Rodrigo)."""
    sinal = "-" if v < 0 else ""
    v = abs(v)
    inteiro = f"{int(v):,}".replace(",", ".")
    decimal = f"{v:.2f}".split(".")[1]
    return f"{sinal}R$ {inteiro},{decimal}"


# ====================== BASE ======================

def variar_base(rng: random.Random, src: Path, dst: Path, trilha: list[str]) -> None:
    shutil.copy(src, dst)
    wb = openpyxl.load_workbook(dst)
    ws = wb.active
    mudancas = 0
    for r in range(1, ws.max_row + 1):
        for c in range(1, ws.max_column + 1):
            cell = ws.cell(r, c)
            v = cell.value
            if v is None:
                continue
            # número direto
            if _is_num(v) and v != 0:
                novo = jitter(rng, v)
                if novo != v:
                    trilha.append(f"BASE  L{r}C{c}: {v} → {novo}")
                    cell.value = novo
                    mudancas += 1
                continue
            # string "R$ ..."
            if isinstance(v, str):
                n = parse_brl_num(v)
                if n is not None and n != 0:
                    novo = round(n * (1 + rng.uniform(-JITTER, JITTER)), 2)
                    cell.value = fmt_brl(novo)
                    trilha.append(f"BASE  L{r}C{c}: '{v}' → '{cell.value}'")
                    mudancas += 1
    wb.save(dst)
    trilha.append(f"\n  BASE total de células variadas: {mudancas}\n")


# ====================== RATEIO ======================

def variar_rateio(rng: random.Random, src: Path, dst: Path, trilha: list[str]) -> None:
    """Para cada linha-evento: novo protocolo HOM-NNNNN, placa permutada,
    Participação e Valor Rateado com jitter independente. Subtotais
    (col K com valor mas sem Protocolo na col A) são recalculados como
    soma dos eventos da seção acima."""
    shutil.copy(src, dst)
    wb = openpyxl.load_workbook(dst)
    ws = wb.active

    # 1ª passada: coleta placas únicas (não-vazias) para permutar
    placas = []
    for r in range(1, ws.max_row + 1):
        proto = ws.cell(r, 1).value
        placa = ws.cell(r, 6).value
        if _is_num(proto) and isinstance(placa, str) and placa.strip():
            placas.append(placa.strip())
    placas_unicas = sorted(set(placas))
    placas_novas = list(placas_unicas)
    rng.shuffle(placas_novas)
    perm = dict(zip(placas_unicas, placas_novas))

    # 2ª passada: substituir protocolo + placa + jitter nos valores;
    # acumular subtotais por seção (linhas sem protocolo, com Valor Rateado)
    eid = 0
    soma_part = 0.0
    soma_rat = 0.0
    mudancas = 0
    for r in range(1, ws.max_row + 1):
        proto = ws.cell(r, 1).value
        vr_cell = ws.cell(r, 11)
        part_cell = ws.cell(r, 7)
        placa_cell = ws.cell(r, 6)
        # linha-evento
        if _is_num(proto):
            eid += 1
            novo_proto = f"HOM-{eid:05d}"
            ws.cell(r, 1).value = novo_proto
            placa_orig = str(placa_cell.value or "").strip()
            if placa_orig and placa_orig in perm:
                placa_cell.value = perm[placa_orig]
            # jitter na Participação (pode ser número, "R$ ..." ou "R$ -")
            pv = part_cell.value
            if _is_num(pv) and pv != 0:
                novo = round(pv * (1 + rng.uniform(-JITTER, JITTER)), 2)
                part_cell.value = novo
            elif isinstance(pv, str):
                n = parse_brl_num(pv)
                if n is not None and n != 0:
                    novo = round(n * (1 + rng.uniform(-JITTER, JITTER)), 2)
                    part_cell.value = fmt_brl(novo)
            # jitter no Valor Rateado
            vrv = vr_cell.value
            if _is_num(vrv) and vrv != 0:
                novo = round(vrv * (1 + rng.uniform(-JITTER, JITTER)), 2)
                vr_cell.value = novo
                soma_rat += novo
                trilha.append(f"RATEIO L{r}: {proto} → {novo_proto}; placa {placa_orig}→{placa_cell.value}; valor_rateado {vrv}→{novo}")
            # também soma participação se número
            pv2 = part_cell.value
            if _is_num(pv2):
                soma_part += pv2
            mudancas += 1
        # linha de subtotal: protocolo vazio mas col 11 com valor → recalcula
        elif (proto is None or proto == "") and _is_num(vr_cell.value):
            vr_cell.value = round(soma_rat, 2)
            if _is_num(part_cell.value):
                part_cell.value = round(soma_part, 2)
            trilha.append(f"RATEIO L{r}: subtotal recalculado → part={soma_part:.2f}, rateado={soma_rat:.2f}")
            soma_part = 0.0
            soma_rat = 0.0

    wb.save(dst)
    trilha.append(f"\n  RATEIO total de eventos variados: {mudancas}; placas permutadas: {len(perm)}\n")


# ====================== PRODUTOS ======================

def variar_produtos(rng: random.Random, src: Path, dst: Path, trilha: list[str]) -> None:
    """Linha 1 = header. Para cada linha de dados: QTD ±5% inteiro, VALOR
    ±5% (R$), TOTAL = QTD * VALOR. Preserva FORNECEDOR/SERVIÇO/PRODUTO/TIPO."""
    shutil.copy(src, dst)
    wb = openpyxl.load_workbook(dst)
    ws = wb.active
    headers = [str(ws.cell(1, c).value or "").strip().upper() for c in range(1, ws.max_column + 1)]
    cQ = headers.index("QTD BOLETOS") + 1 if "QTD BOLETOS" in headers else 5
    cV = headers.index("VALOR") + 1 if "VALOR" in headers else 6
    cT = headers.index("TOTAL") + 1 if "TOTAL" in headers else 7
    mudancas = 0
    for r in range(2, ws.max_row + 1):
        q = ws.cell(r, cQ).value
        v = ws.cell(r, cV).value
        if not (_is_num(q) and _is_num(v)):
            continue
        if q == 0 and v == 0:
            continue
        novo_q = jitter_int(rng, q) if q > 0 else q
        novo_v = jitter(rng, v) if v > 0 else v
        novo_t = round(novo_q * novo_v, 2)
        ws.cell(r, cQ).value = novo_q
        ws.cell(r, cV).value = novo_v
        ws.cell(r, cT).value = novo_t
        trilha.append(f"PRODUTOS L{r}: QTD {q}→{novo_q}; VALOR {v}→{novo_v}; TOTAL→{novo_t}")
        mudancas += 1
    wb.save(dst)
    trilha.append(f"\n  PRODUTOS total de linhas variadas: {mudancas}\n")


# ====================== FECHAMENTO (saída no layout do Rodrigo) ======================

def escrever_fechamento(resultado, template_path: Path, dst: Path) -> dict:
    """Carrega template, escreve ANALITICO com os valores do nosso motor.
    Mantém todas as 6 abas. Acrescenta aba CONFERENCIA_HOMOLOGACAO."""
    seg = {s.segmento: s for s in resultado.segmentos}
    ev = resultado.eventos_rateados
    val = {
        "leves_rateio":    resultado.consolidado.bruto_leves,
        "leves_assoc":     resultado.consolidado.bruto_leves,
        "leves_int":       seg["LEVES"].custo_integrais,
        "leves_par":       seg["LEVES"].custo_parciais,
        "leves_terc_hdr": -round(resultado.consolidado.recuperacao_terceiros_leves, 2),
        "leves_terc_int":  _terc_split(ev, "LEVES", "INTEGRAL"),
        "leves_terc_par":  _terc_split(ev, "LEVES", "PARCIAL"),
        "leves_terc_tot":  round(resultado.consolidado.recuperacao_terceiros_leves, 2),
        "motos_rateio":    resultado.consolidado.bruto_motos,
        "motos_assoc":     resultado.consolidado.bruto_motos,
        "motos_int":       seg["MOTOS"].custo_integrais,
        "motos_par":       seg["MOTOS"].custo_parciais,
        "motos_terc_hdr": -round(resultado.consolidado.recuperacao_terceiros_motos, 2),
        "motos_terc_int":  _terc_split(ev, "MOTOS", "INTEGRAL"),
        "motos_terc_par":  _terc_split(ev, "MOTOS", "PARCIAL"),
        "motos_terc_tot":  round(resultado.consolidado.recuperacao_terceiros_motos, 2),
        "pesados_terc_hdr": -_terc_split(ev, "PESADOS", "INTEGRAL") - _terc_split(ev, "PESADOS", "PARCIAL"),
        "pesados_terc_int": _terc_split(ev, "PESADOS", "INTEGRAL"),
        "pesados_terc_par": _terc_split(ev, "PESADOS", "PARCIAL"),
        "pesados_terc_tot": _terc_split(ev, "PESADOS", "INTEGRAL") + _terc_split(ev, "PESADOS", "PARCIAL"),
    }

    wb = openpyxl.load_workbook(template_path)
    ws = wb["ANALITICO"]
    mp = _mapa_analitico(ws)
    escritas = 0
    for chave, (row, col) in mp.items():
        if chave not in val:
            continue
        ws.cell(row, col, round(val[chave], 2)).number_format = MONEY
        escritas += 1

    # aba CONFERENCIA_HOMOLOGACAO — resumo executivo pro Rodrigo
    cs = wb.create_sheet("CONFERENCIA_HOMOLOGACAO")
    cs["A1"] = "Pacote de Homologação — AutoTruck × Motor de Rateio"
    cs["A1"].font = Font(bold=True, size=13)
    cs["A2"] = ("Dados de entrada são reconstrução dos prints/transcrições do Rodrigo "
                "com jitter ±5%, placas permutadas, protocolos HOM-NNNNN. "
                "Cotas LEVES adotadas como override (faltavam na BASE). "
                "Objetivo: o Rodrigo joga os 3 INPUTs na sua planilha e confere "
                "se a LÓGICA bate — não os centavos.")
    cs.merge_cells("A2:D2"); cs["A2"].alignment = openpyxl.styles.Alignment(wrap_text=True)
    cs.row_dimensions[2].height = 60
    hdr = [("métrica", "valor")]
    co = resultado.consolidado
    metricas = [
        ("Cota LEVES (R$ / cota)",          co.cota_leves),
        ("Cota MOTOS (R$ / cota)",          co.cota_motos),
        ("Cotas LEVES adimplentes (override)", co.total_cotas_leves),
        ("Cotas MOTOS adimplentes",         co.total_cotas_motos),
        ("Bruto LEVES (integrais + parciais)", co.bruto_leves),
        ("Bruto MOTOS (integrais + parciais)", co.bruto_motos),
        ("Terceiros LEVES (não abate cota)", co.recuperacao_terceiros_leves),
        ("Terceiros MOTOS (não abate cota)", co.recuperacao_terceiros_motos),
        ("Eventos alocados",                co.eventos_alocados),
        ("Eventos postergados",             co.eventos_postergados),
        ("Invariante de auditoria (Δ)",     co.diferenca_total),
        ("Invariante OK?",                  "SIM" if co.invariante_ok else "NÃO"),
    ]
    for i, h in enumerate(hdr[0], 1):
        c = cs.cell(4, i, h); c.font = H; c.fill = HF
    for j, (k, v) in enumerate(metricas, start=5):
        cs.cell(j, 1, k)
        c = cs.cell(j, 2, v)
        if isinstance(v, (int, float)) and not isinstance(v, bool):
            c.number_format = MONEY if abs(v) > 1 or v == 0 else "#,##0.0000"
    for col, w in [("A", 50), ("B", 22)]:
        cs.column_dimensions[col].width = w

    dst.parent.mkdir(parents=True, exist_ok=True)
    wb.save(dst)
    return {"abas_preservadas": wb.sheetnames, "celulas_analitico_escritas": escritas}


# ====================== ORQUESTRA ======================

def main() -> int:
    rng = random.Random(SEED)
    OUT.mkdir(parents=True, exist_ok=True)
    TRILHA_PATH.parent.mkdir(parents=True, exist_ok=True)

    trilha: list[str] = [
        f"PACOTE DE HOMOLOGAÇÃO — AutoTruck",
        f"Semente: {SEED}  |  Jitter: ±{int(JITTER*100)}%  |  cotas_leves_override: {COTAS_LEVES_OVERRIDE}",
        f"Fontes (Remonta/):",
        f"  BASE     {SRC_BASE.name}",
        f"  RATEIO   {SRC_RATEIO.name}",
        f"  PRODUTOS {SRC_PRODUTOS.name}",
        f"Saídas (simulacoes/HOMOLOGACAO/):",
        f"  INPUT_BASE.xlsx / INPUT_RATEIO.xlsx / INPUT_PRODUTOS.xlsx",
        f"  FECHAMENTO_AutoTruck_Homologacao.xlsx (formato 6-abas do Rodrigo)",
        f"-" * 80,
        "",
    ]

    dst_base = OUT / "INPUT_BASE.xlsx"
    dst_rateio = OUT / "INPUT_RATEIO.xlsx"
    dst_produtos = OUT / "INPUT_PRODUTOS.xlsx"
    dst_fech = OUT / "FECHAMENTO_AutoTruck_Homologacao.xlsx"

    print(f"[1/4] Variando BASE → {dst_base.name}")
    variar_base(rng, SRC_BASE, dst_base, trilha)

    print(f"[2/4] Variando RATEIO → {dst_rateio.name}")
    variar_rateio(rng, SRC_RATEIO, dst_rateio, trilha)

    print(f"[3/4] Variando PRODUTOS → {dst_produtos.name}")
    variar_produtos(rng, SRC_PRODUTOS, dst_produtos, trilha)

    print(f"[4/4] Rodando motor + escrevendo FECHAMENTO no template do Rodrigo")
    veiculos, eventos, _produtos, _base, resumo = compor(
        str(dst_base), str(dst_rateio),
        produtos_path=str(dst_produtos),
        cotas_leves_override=COTAS_LEVES_OVERRIDE,
    )
    r = calcular_rateio_at(mes_ano_ref="HOMOLOGACAO", veiculos=veiculos, eventos=eventos)
    meta = escrever_fechamento(r, TEMPLATE_FECH, dst_fech)
    co = r.consolidado

    trilha.append("\n" + "=" * 80)
    trilha.append("RESULTADO DO MOTOR sobre os inputs variados:")
    trilha.append(f"  Cota LEVES    = R$ {co.cota_leves:.2f}  ({co.total_cotas_leves} cotas)")
    trilha.append(f"  Cota MOTOS    = R$ {co.cota_motos:.2f}  ({co.total_cotas_motos} cotas)")
    trilha.append(f"  Bruto LEVES   = R$ {co.bruto_leves:,.2f}")
    trilha.append(f"  Bruto MOTOS   = R$ {co.bruto_motos:,.2f}")
    trilha.append(f"  Terc LEVES    = R$ {co.recuperacao_terceiros_leves:,.2f} (não abate)")
    trilha.append(f"  Terc MOTOS    = R$ {co.recuperacao_terceiros_motos:,.2f} (não abate)")
    trilha.append(f"  Eventos alocados: {co.eventos_alocados}  |  postergados: {co.eventos_postergados}")
    trilha.append(f"  Invariante: Δ={co.diferenca_total}  |  OK={co.invariante_ok}")
    trilha.append(f"  FECHAMENTO: {meta['celulas_analitico_escritas']} células escritas no ANALITICO")
    trilha.append(f"  abas no template preservadas: {meta['abas_preservadas']}")

    TRILHA_PATH.write_text("\n".join(trilha), encoding="utf-8")
    print(f"\n✅ Pacote pronto em: {OUT}")
    print(f"   Trilha (interna):   {TRILHA_PATH}")
    print(f"\n   Cota LEVES = R$ {co.cota_leves:.2f}  |  Cota MOTOS = R$ {co.cota_motos:.2f}")
    print(f"   Invariante: Δ={co.diferenca_total}  |  OK={co.invariante_ok}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
