"""Ingestão de partes separadas — BASE.xlsx + RATEIO.xlsx + PRODUTOS.xlsx.

O Rodrigo (AutoTruck) envia cada aba como xlsx isolado por restrição de
diretoria. Esta ingestão compõe os 3 (ou 2) arquivos no insumo que o
engine entende: uma lista de VeiculoAT (denominador) + uma lista de
EventoAT (numerador).

Compatível com o layout dos arquivos do `Remonta/`:
- BASE_Reconstruida.xlsx  → aba "BASE", 3 segmentos lado a lado.
- Rateio_POC_Completo.xlsx → aba "Rateio POC", layout sem coluna
  Fornecedor (1 coluna a menos que o FECHAMENTO integrado).
- Produtos_Reconstruido.xlsx → aba "FORNECEDOR", catálogo de planos
  (opcional — preserva metadados de fornecedor p/ telas futuras).
"""

from dataclasses import dataclass, field
from datetime import date, datetime

import openpyxl

from .domain import EventoAT, VeiculoAT


def _num(v) -> float:
    if v is None:
        return 0.0
    if isinstance(v, (int, float)):
        return float(v)
    s = str(v).strip().replace("R$", "").replace(" ", "")
    s = s.replace(".", "").replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return 0.0


def _int(v) -> int:
    return int(_num(v))


def _data(v) -> str:
    if isinstance(v, (datetime, date)):
        return v.strftime("%Y-%m-%d")
    if not v:
        return ""
    s = str(v).strip()
    # dd/mm/YYYY
    if len(s) >= 10 and s[2] == "/" and s[5] == "/":
        try:
            return datetime.strptime(s[:10], "%d/%m/%Y").strftime("%Y-%m-%d")
        except ValueError:
            return s[:10]
    return s[:10]


@dataclass
class BaseCounts:
    cotas_baixadas: dict[str, int] = field(default_factory=dict)   # LEVES/MOTOS/PESADOS
    cotas_abertas: dict[str, int] = field(default_factory=dict)
    boletos_baixados: dict[str, int] = field(default_factory=dict)
    boletos_abertos: dict[str, int] = field(default_factory=dict)
    valor_recebido: dict[str, float] = field(default_factory=dict)
    valor_inadimplencia: dict[str, float] = field(default_factory=dict)


# -------- Detecção de tipo do arquivo (validação anti-troca-de-slot) --------

def detectar_tipo(path: str) -> str:
    """Retorna 'BASE' | 'RATEIO' | 'PRODUTOS' | 'DESCONHECIDO' inspecionando
    apenas a primeira aba e as ~30 primeiras linhas. Custo desprezível.

    Assinaturas:
    - BASE     → L1 col A/G/N contém 'PESADO'/'MOTO'/'LEVE' (segmentos lado a lado)
                 ou L4 tem cabeçalho 'DESCRIÇÃO/ABERTO/BAIXADO/CANCELADO/TOTAL'.
    - RATEIO   → col A nas primeiras linhas tem marcador 'PESADOS TERCEIROS' /
                 'MOTOS ASSOCIADOS' / 'LEVES TERCEIROS' / etc. + header row
                 'Protocolo | ... | Valor Rateado'.
    - PRODUTOS → L1 tem 'FORNECEDOR' e 'SERVIÇO' como cabeçalhos.
    """
    try:
        # NÃO usar read_only=True: arquivos re-salvos por outros programas
        # (ex.: Google Sheets) podem omitir a tag <dimension>, e nesse modo
        # ws.max_row/max_column vêm None → quebra a janela abaixo. Sem read_only
        # o openpyxl calcula as dimensões a partir das células (igual ao leitor).
        wb = openpyxl.load_workbook(path, data_only=True)
    except Exception:
        return "DESCONHECIDO"
    ws = wb.worksheets[0]
    # coleta strings em UPPER da janela inicial (linhas 1..30, cols 1..20)
    max_row = ws.max_row or 0
    max_col = ws.max_column or 0
    cels: dict[tuple[int, int], str] = {}
    for r in range(1, min(31, max_row + 1)):
        for c in range(1, min(21, max_col + 1)):
            v = ws.cell(r, c).value
            if isinstance(v, str) and v.strip():
                cels[(r, c)] = v.strip().upper()

    row1 = {c: s for (r, c), s in cels.items() if r == 1}

    # PRODUTOS: linha 1 tem FORNECEDOR + SERVIÇO (ou SERVICO sem acento)
    if any("FORNECED" in s for s in row1.values()) and any(s.startswith("SERVI") for s in row1.values()):
        return "PRODUTOS"

    # RATEIO: marcador de seção em col A nas primeiras linhas
    col_a_strs = [s for (r, c), s in cels.items() if c == 1 and r <= 20]
    tem_marcador_secao = any(
        ("ASSOCIADOS" in s or "TERCEIROS" in s) and any(k in s for k in ("PESADOS", "MOTOS", "LEVES"))
        for s in col_a_strs
    )
    tem_header_valor_rateado = any("VALOR RATEADO" in s for s in cels.values())
    if tem_marcador_secao and tem_header_valor_rateado:
        return "RATEIO"

    # BASE: 'PESADO'/'MOTO'/'LEVE' como rótulo de segmento em row 1
    segmentos_row1 = sum(1 for s in row1.values() if s in ("PESADO", "MOTO", "LEVE"))
    if segmentos_row1 >= 2:
        return "BASE"
    # fallback BASE: header 'DESCRIÇÃO/ABERTO/BAIXADO/CANCELADO/TOTAL' em row 3 ou 4
    headers_base = {"DESCRIÇÃO", "DESCRICAO", "ABERTO", "BAIXADO", "CANCELADO", "TOTAL"}
    for r in (3, 4, 5):
        row_strs = {s for (rr, c), s in cels.items() if rr == r}
        if len(row_strs & headers_base) >= 4:
            return "BASE"

    return "DESCONHECIDO"


_NOME_HUMANO = {"BASE": "BASE (cotas/boletos por situação)",
                "RATEIO": "RATEIO (eventos sinistrados do mês)",
                "PRODUTOS": "PRODUTOS (catálogo fornecedor)",
                "DESCONHECIDO": "formato desconhecido"}


def validar_slot(slot_esperado: str, path: str) -> str | None:
    """None se OK; senão retorna a mensagem de erro pronta para o usuário."""
    tipo = detectar_tipo(path)
    if tipo == slot_esperado:
        return None
    if tipo == "DESCONHECIDO":
        return (f"Arquivo no slot '{slot_esperado}' não tem assinatura reconhecida. "
                f"Esperado: {_NOME_HUMANO[slot_esperado]}.")
    return (f"Arquivo no slot '{slot_esperado}' parece ser {_NOME_HUMANO[tipo]}. "
            f"Esperado: {_NOME_HUMANO[slot_esperado]}. Verifique se trocou os arquivos.")


def ler_base(path: str) -> BaseCounts:
    """Lê BASE com 3 segmentos lado a lado. Localiza por rótulos
    (PESADO/MOTO/LEVE no L1) a coluna-inicial de cada bloco e extrai
    'Quantidade de Boletos TOTAL' e 'Cota por Situação TOTAL'.
    """
    wb = openpyxl.load_workbook(path, data_only=True)
    ws = wb.worksheets[0]  # assume primeira aba (chamada "BASE" no arquivo do Rodrigo)
    bc = BaseCounts()

    # Mapeia segmento → coluna inicial pelo rótulo na linha 1
    cols: dict[str, int] = {}
    for c in range(1, ws.max_column + 1):
        v = ws.cell(1, c).value
        if not v:
            continue
        s = str(v).strip().upper()
        if s == "PESADO":
            cols["PESADOS"] = c
        elif s == "MOTO":
            cols["MOTOS"] = c
        elif s == "LEVE":
            cols["LEVES"] = c

    # Para cada segmento, varre apenas a faixa de colunas do segmento
    # procurando: "Quantidade de Boletos…", "Cota por Situação…", e o
    # primeiro TOTAL (bloco "Valor de Classificação"). Usa o último
    # cabeçalho BAIXADO/ABERTO encontrado dentro do mesmo sub-intervalo
    # para localizar as colunas dos valores.
    seg_starts = sorted(cols.items(), key=lambda x: x[1])
    for i, (seg, c0) in enumerate(seg_starts):
        c_end = seg_starts[i + 1][1] - 1 if i + 1 < len(seg_starts) else ws.max_column
        ja_pegou_valor = False
        last_header_cols: dict[str, int] = {}
        last_header_row = 0
        for r in range(1, ws.max_row + 1):
            for c in range(c0, c_end + 1):
                v = ws.cell(r, c).value
                if v is None:
                    continue
                s = str(v).strip().upper()
                # memoriza posições dos cabeçalhos BAIXADO/ABERTO/CANCELADO do bloco
                if s in ("BAIXADO", "ABERTO", "CANCELADO"):
                    last_header_cols[s] = c
                    last_header_row = r
                if s.startswith("QUANTIDADE DE BOLETO"):
                    _capt_counts(ws, r, c0, c_end, bc.boletos_baixados, bc.boletos_abertos, seg,
                                 fallback_header_cols=dict(last_header_cols))
                elif s.startswith("COTA POR"):
                    _capt_counts(ws, r, c0, c_end, bc.cotas_baixadas, bc.cotas_abertas, seg,
                                 fallback_header_cols=dict(last_header_cols))
                elif s == "TOTAL" and not ja_pegou_valor and last_header_cols and r > last_header_row:
                    # primeiro TOTAL APÓS uma linha de cabeçalho = bloco "Valor de Classificação"
                    bx_c = last_header_cols.get("BAIXADO")
                    ab_c = last_header_cols.get("ABERTO")
                    if bx_c:
                        bc.valor_recebido[seg] = _num(ws.cell(r, bx_c).value)
                    if ab_c:
                        bc.valor_inadimplencia[seg] = _num(ws.cell(r, ab_c).value)
                    ja_pegou_valor = True
    return bc


def _capt_counts(ws, header_row: int, c0: int, c_end: int,
                 dest_bx: dict, dest_ab: dict, seg: str,
                 fallback_header_cols: dict | None = None) -> None:
    """A partir do rótulo 'Quantidade…' / 'Cota…' em (header_row, *),
    descobre BAIXADO/ABERTO restritos ao sub-intervalo [c0, c_end]:

      1) TOTAL nas 5 linhas seguintes (caso 'Quantidade de Boletos').
      2) Valores inline na mesma linha (caso PESADO 'Cota por Situação').
      3) Valores na linha imediatamente seguinte (caso MOTO 'Cota por
         Situação' — header fica acima, valores embaixo), reaproveitando
         `fallback_header_cols`.
    """
    # caso 1: TOTAL nas 5 linhas seguintes, dentro do sub-intervalo do segmento
    for r in range(header_row + 1, min(header_row + 6, ws.max_row + 1)):
        for c in range(c0, c_end + 1):
            if str(ws.cell(r, c).value or "").strip().upper() == "TOTAL":
                idx = {}
                for cc in range(c0, c_end + 1):
                    h = str(ws.cell(r - 1, cc).value or "").strip().upper()
                    if h in ("BAIXADO", "ABERTO"):
                        idx[h] = cc
                if not idx and fallback_header_cols:
                    idx = {k: v for k, v in fallback_header_cols.items()
                           if c0 <= v <= c_end}
                if "BAIXADO" in idx:
                    dest_bx[seg] = _int(ws.cell(r, idx["BAIXADO"]).value)
                if "ABERTO" in idx:
                    dest_ab[seg] = _int(ws.cell(r, idx["ABERTO"]).value)
                return
    # caso 2/3: usa fallback_header_cols restrito ao sub-intervalo
    if not fallback_header_cols:
        return
    bx_c = fallback_header_cols.get("BAIXADO")
    ab_c = fallback_header_cols.get("ABERTO")
    if not (bx_c and c0 <= bx_c <= c_end):
        bx_c = None
    if not (ab_c and c0 <= ab_c <= c_end):
        ab_c = None
    for try_row in (header_row, header_row + 1):
        if try_row > ws.max_row:
            continue
        bx = _int(ws.cell(try_row, bx_c).value) if bx_c else 0
        ab = _int(ws.cell(try_row, ab_c).value) if ab_c else 0
        if bx or ab:
            dest_bx[seg] = bx
            dest_ab[seg] = ab
            return


# -------- Rateio (layout do Rateio_POC_Completo.xlsx) --------

# Colunas (1-indexed) no layout sem "Fornecedor" e sem "Custo Evento":
# 1=Protocolo  2=Campo  3=Motivo  4=Envolvimento  5=Situação
# 6=Placa  7=Participação  8=Data Comunic  9=Tipo Evento  10=Mês Refe
# 11=Valor Rateado
_RC = dict(protocolo=1, motivo=3, envolv=4, situacao=5, placa=6,
           participacao=7, data_com=8, tipo_evento=9, mes_ref=10,
           valor_rateado=11)

_SEG_NAMES = ("LEVES", "MOTOS", "PESADOS")


def ler_rateio_partes(path: str) -> list[EventoAT]:
    """Lê o Rateio (arquivo separado). Coluna A: marcadores de seção
    ('PESADOS TERCEIROS', 'MOTOS ASSOCIADOS', etc.) e protocolo (numérico)
    nas linhas-evento. Coluna B: 'INDENIZAÇÃO INTEGRAL/PARCIAL'
    embutido na própria linha do evento (não em linha marcadora separada).
    """
    wb = openpyxl.load_workbook(path, data_only=True)
    ws = wb.worksheets[0]
    eventos: list[EventoAT] = []
    seg = env = None
    eid = 0
    for r in range(1, ws.max_row + 1):
        a_raw = ws.cell(r, 1).value
        a = str(a_raw or "").strip().upper()
        b = str(ws.cell(r, 2).value or "").strip().upper()
        # marcador de seção em A (string sem número)
        if a and not isinstance(a_raw, (int, float)) and (
            a.endswith("ASSOCIADOS") or a.endswith("TERCEIROS")
        ):
            for k in _SEG_NAMES:
                if k in a:
                    seg = k
                    break
            env = "ASSOCIADO" if "ASSOCIADOS" in a else "TERCEIRO"
            continue
        if a == "PROTOCOLO":
            continue
        if seg is None or env is None:
            continue
        # tipo vem da própria coluna B da linha do evento
        if "INTEGRAL" in b:
            tipo = "INTEGRAL"
        elif "PARCIAL" in b:
            tipo = "PARCIAL"
        else:
            continue
        valor_rateado = _num(ws.cell(r, _RC["valor_rateado"]).value)
        proto = ws.cell(r, _RC["protocolo"]).value
        datacom = ws.cell(r, _RC["data_com"]).value
        # linha-evento real: protocolo numérico (ou string com dígito) + valor rateado > 0
        if valor_rateado <= 0 or not proto:
            continue
        eid += 1
        if tipo == "INTEGRAL":
            valor_fipe, valor_evento, orc = valor_rateado, valor_rateado, 0.0
        else:  # PARCIAL: FIPE alto p/ não disparar a regra dos 75%
            valor_fipe, valor_evento, orc = round(valor_rateado / 0.5, 2), valor_rateado, 0.0
        eventos.append(EventoAT(
            id_evento=f"UP-{eid:05d}",
            protocolo=str(proto),
            placa=str(ws.cell(r, _RC["placa"]).value or ""),
            segmento=seg, envolvimento=env, tipo_evento=tipo,
            valor_evento=valor_evento, orcamento_reparo=orc, valor_fipe=valor_fipe,
            data_aviso=_data(datacom),
            franquia=0.0, valor_salvado=0.0,
            salvado_liquidado=False, postergado=False,
        ))
    return eventos


# -------- Produtos (catálogo fornecedor — informativo, não entra no engine) --------

@dataclass
class ProdutoCatalogo:
    fornecedor: str
    servico: str
    produto: str       # MOTO / AUTOMOVEL / CAMINHAO
    tipo: str
    qtd_boletos: int
    valor_unit: float
    total: float


def ler_produtos(path: str) -> list[ProdutoCatalogo]:
    wb = openpyxl.load_workbook(path, data_only=True)
    ws = wb.worksheets[0]
    out: list[ProdutoCatalogo] = []
    headers = [str(ws.cell(1, c).value or "").strip().upper() for c in range(1, ws.max_column + 1)]
    def idx(name: str) -> int:
        for i, h in enumerate(headers, 1):
            if name in h:
                return i
        return 0
    cF, cS, cP, cT, cQ, cV, cTot = (idx("FORNECED"), idx("SERVI"), idx("PRODUTO"),
                                     idx("TIPO"), idx("QTD"), idx("VALOR"), idx("TOTAL"))
    for r in range(2, ws.max_row + 1):
        forn = str(ws.cell(r, cF).value or "").strip()
        if not forn:
            continue
        out.append(ProdutoCatalogo(
            fornecedor=forn,
            servico=str(ws.cell(r, cS).value or "").strip() if cS else "",
            produto=str(ws.cell(r, cP).value or "").strip() if cP else "",
            tipo=str(ws.cell(r, cT).value or "").strip() if cT else "",
            qtd_boletos=_int(ws.cell(r, cQ).value) if cQ else 0,
            valor_unit=_num(ws.cell(r, cV).value) if cV else 0.0,
            total=_num(ws.cell(r, cTot).value) if cTot else 0.0,
        ))
    return out


# -------- Compositor: BASE + RATEIO + (PRODUTOS) → (veiculos, eventos) --------

def sintetizar_veiculos(base: BaseCounts,
                        *,
                        cotas_leves_override: int | None = None,
                        cotas_motos_override: int | None = None) -> list[VeiculoAT]:
    """Gera VeiculoAT sintéticos com FIPE=5000 (1 cota cada — fica ≤10k da
    regra da rules.py). Cada veículo conta exatamente 1 cota no denominador,
    então N veículos adimplentes ≡ N cotas adimplentes (cota purista).

    `override` permite informar manualmente quando BASE não trouxer
    (caso típico: LEVES no Remonta — Rodrigo não publica esse total).
    """
    out: list[VeiculoAT] = []
    nid = 0

    def push(seg: str, n_ok: int, n_ab: int, tipo: str):
        nonlocal nid
        for _ in range(n_ok):
            nid += 1
            out.append(VeiculoAT(
                id_veiculo=f"V{nid:06d}", placa=f"AUTO{nid:04d}", segmento=seg,
                tipo_veiculo=tipo, valor_fipe=5000.0,
                status_ativo=True, adimplente=True,
            ))
        for _ in range(n_ab):
            nid += 1
            out.append(VeiculoAT(
                id_veiculo=f"V{nid:06d}", placa=f"AUTO{nid:04d}", segmento=seg,
                tipo_veiculo=tipo, valor_fipe=5000.0,
                status_ativo=True, adimplente=False,
            ))

    n_leves_ok = cotas_leves_override if cotas_leves_override is not None else base.cotas_baixadas.get("LEVES", 0)
    n_leves_ab = base.cotas_abertas.get("LEVES", 0)
    n_motos_ok = cotas_motos_override if cotas_motos_override is not None else base.cotas_baixadas.get("MOTOS", 0)
    n_motos_ab = base.cotas_abertas.get("MOTOS", 0)
    n_pes_ok = base.cotas_baixadas.get("PESADOS", 0)
    n_pes_ab = base.cotas_abertas.get("PESADOS", 0)

    push("LEVES", n_leves_ok, n_leves_ab, "AUTOMOVEL")
    push("MOTOS", n_motos_ok, n_motos_ab, "MOTOCICLETA")
    push("PESADOS", n_pes_ok, n_pes_ab, "CAMINHAO")
    return out


@dataclass
class ParteIngestaoResumo:
    cotas_leves: int
    cotas_motos: int
    cotas_pesados: int
    veiculos_total: int
    eventos_total: int
    n_produtos_catalogo: int
    valor_recebido_leves: float
    valor_recebido_motos: float
    valor_recebido_pesados: float
    secoes_rateio: list[str]


def compor(
    base_path: str,
    rateio_path: str,
    *,
    produtos_path: str | None = None,
    cotas_leves_override: int | None = None,
    cotas_motos_override: int | None = None,
) -> tuple[list[VeiculoAT], list[EventoAT], list[ProdutoCatalogo], BaseCounts, ParteIngestaoResumo]:
    base = ler_base(base_path)
    eventos = ler_rateio_partes(rateio_path)
    produtos = ler_produtos(produtos_path) if produtos_path else []
    veiculos = sintetizar_veiculos(
        base,
        cotas_leves_override=cotas_leves_override,
        cotas_motos_override=cotas_motos_override,
    )
    secoes = sorted({f"{e.segmento}/{e.envolvimento}/{e.tipo_evento}" for e in eventos})
    resumo = ParteIngestaoResumo(
        cotas_leves=cotas_leves_override if cotas_leves_override is not None else base.cotas_baixadas.get("LEVES", 0),
        cotas_motos=cotas_motos_override if cotas_motos_override is not None else base.cotas_baixadas.get("MOTOS", 0),
        cotas_pesados=base.cotas_baixadas.get("PESADOS", 0),
        veiculos_total=len(veiculos),
        eventos_total=len(eventos),
        n_produtos_catalogo=len(produtos),
        valor_recebido_leves=base.valor_recebido.get("LEVES", 0.0),
        valor_recebido_motos=base.valor_recebido.get("MOTOS", 0.0),
        valor_recebido_pesados=base.valor_recebido.get("PESADOS", 0.0),
        secoes_rateio=secoes,
    )
    return veiculos, eventos, produtos, base, resumo
