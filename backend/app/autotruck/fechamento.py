"""Fechamento mensal AutoTruck — Foto imutável + fluxo D+0..D+5.

Implementa a "Foto de Fechamento" do levantamento: no D+0 tira-se um
snapshot LACRADO dos insumos (hash SHA-256); qualquer alteração posterior
na fonte é detectada ("daqui 5 min não pode"). Máquina de estados:

    ABERTO ──homologar(D+3)──> HOMOLOGADO ──emitir(D+5)──> EMITIDO

Não depende do ELLO; reutiliza o engine AutoTruck.
"""

import hashlib
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone

from .domain import AuditLog, ResultadoRateioAT
from .engine import calcular_rateio_at
from .rules import PARAMS_DEFAULT, ParametrosAT


def _hash_insumos(veiculos, eventos, params: ParametrosAT) -> str:
    payload = {
        "veiculos": sorted((asdict(v) for v in veiculos),
                           key=lambda d: d.get("id_veiculo", "")),
        "eventos": sorted((asdict(e) for e in eventos),
                          key=lambda d: d.get("id_evento", "")),
        "params": asdict(params),
    }
    blob = json.dumps(payload, sort_keys=True, default=str, ensure_ascii=False)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


@dataclass
class FotoFechamento:
    id: str
    mes_ano_ref: str
    criado_em: str
    hash_insumos: str
    origem: str
    status: str                      # ABERTO | HOMOLOGADO | EMITIDO
    n_veiculos: int
    n_eventos: int
    base_cotas_leves: float
    base_cotas_motos: float
    resultado: ResultadoRateioAT
    auditoria_fechamento: list[AuditLog] = field(default_factory=list)
    params: ParametrosAT = field(default=PARAMS_DEFAULT, repr=False)


class FechamentoError(RuntimeError):
    pass


class FechamentoService:
    """Orquestra o ciclo D+0..D+5 sobre uma fonte (conector SGA/xlsx)."""

    def __init__(self) -> None:
        self._fotos: dict[str, FotoFechamento] = {}

    # ---- D+0: Foto de Fechamento (lock) ----
    def abrir(
        self,
        fonte,
        *,
        veiculos_base=None,
        base_cotas_leves: float = 0.0,
        base_cotas_motos: float = 0.0,
        params: ParametrosAT = PARAMS_DEFAULT,
        force: bool = False,
    ) -> FotoFechamento:
        veiculos_fonte, eventos, meta = fonte.carregar()
        # lacre = SOMENTE os insumos da fonte (SGA/xlsx). A frota auxiliar
        # (veiculos_base) é parâmetro de cálculo do lote, não entra no lacre.
        h = _hash_insumos(veiculos_fonte, eventos, params)
        veiculos = (list(veiculos_fonte) if veiculos_fonte
                    else list(veiculos_base) if veiculos_base else [])
        mes = meta.get("mes_ano_ref", "FECHAMENTO")
        fid = f"FCH-{mes.replace('/', '')}"
        if fid in self._fotos and not force:
            raise FechamentoError(
                f"Fechamento {fid} já aberto (status "
                f"{self._fotos[fid].status}). Use force para reabrir."
            )
        resultado = calcular_rateio_at(
            mes_ano_ref=mes, veiculos=veiculos, eventos=eventos, params=params
        )
        # cota com base informada (a fonte xlsx não traz a frota)
        seg = {s.segmento: s for s in resultado.segmentos}
        agora = datetime.now(timezone.utc).isoformat()
        log = [AuditLog(mes, "FOTO_FECHAMENTO_D0",
                        fid, f"Snapshot lacrado · origem={fonte.nome} · "
                        f"hash={h[:12]}…", agora)]
        foto = FotoFechamento(
            id=fid, mes_ano_ref=mes, criado_em=agora, hash_insumos=h,
            origem=fonte.nome, status="ABERTO",
            n_veiculos=len(veiculos), n_eventos=len(eventos),
            base_cotas_leves=base_cotas_leves, base_cotas_motos=base_cotas_motos,
            resultado=resultado, auditoria_fechamento=log, params=params,
        )
        self._fotos[fid] = foto
        return foto

    def buscar(self, fid: str) -> FotoFechamento:
        if fid not in self._fotos:
            raise FechamentoError(f"Fechamento {fid} não encontrado.")
        return self._fotos[fid]

    # ---- Integridade do lacre (a foto não pode mudar) ----
    def verificar_integridade(self, fid: str, fonte) -> dict:
        foto = self.buscar(fid)
        v, e, _ = fonte.carregar()
        h = _hash_insumos(v, e, foto.params)
        intacto = h == foto.hash_insumos
        return {
            "id": fid, "intacto": intacto,
            "hash_foto": foto.hash_insumos, "hash_atual": h,
            "mensagem": ("Lacre íntegro — insumos idênticos ao D+0."
                         if intacto else
                         "VIOLAÇÃO: a fonte mudou após o lacre do fechamento."),
        }

    # ---- D+3: Homologação ----
    def homologar(self, fid: str, justificativa: str) -> FotoFechamento:
        foto = self.buscar(fid)
        if foto.status != "ABERTO":
            raise FechamentoError(
                f"Só é possível homologar um fechamento ABERTO (atual: {foto.status})."
            )
        if not (justificativa and justificativa.strip()):
            raise FechamentoError("Homologação exige justificativa técnica (D&O / LC 213).")
        foto.status = "HOMOLOGADO"
        foto.auditoria_fechamento.append(AuditLog(
            foto.mes_ano_ref, "HOMOLOGACAO_D3", fid, justificativa.strip(),
            datetime.now(timezone.utc).isoformat()))
        return foto

    # ---- D+5: Emissão (lote de boletos) ----
    def emitir(self, fid: str) -> FotoFechamento:
        foto = self.buscar(fid)
        if foto.status != "HOMOLOGADO":
            raise FechamentoError(
                f"Emissão exige fechamento HOMOLOGADO (atual: {foto.status})."
            )
        foto.status = "EMITIDO"
        foto.auditoria_fechamento.append(AuditLog(
            foto.mes_ano_ref, "EMISSAO_D5", fid,
            f"Lote emitido: {len(self.lote_boletos(fid))} boletos.",
            datetime.now(timezone.utc).isoformat()))
        return foto

    def lote_boletos(self, fid: str) -> list:
        foto = self.buscar(fid)
        return [b for b in foto.resultado.boletos if b.gera_boleto]

    def cota(self, fid: str) -> dict:
        """Cota final usando a base informada (ou a frota, se houver)."""
        foto = self.buscar(fid)
        seg = {s.segmento: s for s in foto.resultado.segmentos}
        out = {}
        for nome, base in (("LEVES", foto.base_cotas_leves),
                           ("MOTOS", foto.base_cotas_motos)):
            s = seg[nome]
            denom = base if base > 0 else s.cotas_ativas
            out[nome] = {
                "custo_a_ratear": s.custo_a_ratear,
                "cotas_base": round(denom, 2),
                "valor_cota": round(s.custo_a_ratear / denom, 2) if denom > 0 else 0.0,
            }
        return out
