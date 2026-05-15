"""Motor de Rateio AutoTruck — núcleo puro (sem I/O, sem framework).

Recebe coleções de domínio, devolve `ResultadoRateioAT`. Implementa o
Modelo Elo Ajustado: segmentação LEVES/MOTOS (variável, bases separadas)
e PESADOS (casco caminhão = pote fixo), regra dos 75%, salvados
liquidados, dedução de terceiros, denominador purista, FIFO com
prioridade de postergados, estabilização e alerta de volatilidade,
e trilha de auditoria das exclusões manuais.

Invariante de auditoria (análogo ao "alvo vs alocado = 0" do ELLO):
por segmento variável, `custo_apurado − custo_dos_eventos_alocados == 0`.
"""

from collections import defaultdict
from datetime import datetime, timezone
from typing import Iterable

from .domain import (
    AuditLog,
    BoletoAT,
    ConsolidadoAT,
    EventoAT,
    EventoRateadoAT,
    ResultadoRateioAT,
    SegmentoResultado,
    VeiculoAT,
)
from .rules import PARAMS_DEFAULT, ParametrosAT, aplica_regra_75, cotas_por_fipe

VARIAVEIS = ("LEVES", "MOTOS")


def _custo_evento(ev: EventoAT, tipo_efetivo: str) -> float:
    """INTEGRAL entra pelo valor FIPE; PARCIAL pelo valor de oficina."""
    return ev.valor_fipe if tipo_efetivo == "INTEGRAL" else ev.valor_evento


def calcular_rateio_at(
    *,
    mes_ano_ref: str,
    veiculos: Iterable[VeiculoAT],
    eventos: Iterable[EventoAT],
    params: ParametrosAT = PARAMS_DEFAULT,
    exclusoes: dict[str, str] | None = None,
    historico_cotas: dict[str, list[float]] | None = None,
) -> ResultadoRateioAT:
    """Roda o motor. `exclusoes` = {id_evento: justificativa_tecnica} — toda
    exclusão exige justificativa não-vazia e é registrada em log imutável.
    `historico_cotas` = {segmento: [cotas de meses anteriores]} para o
    cálculo de estabilização (média dos últimos 3 meses ± var_trimestral_max).
    """
    veiculos_list = list(veiculos)
    eventos_list = list(eventos)
    exclusoes = exclusoes or {}
    agora = datetime.now(timezone.utc).isoformat()

    auditoria: list[AuditLog] = []
    excl_validas: set[str] = set()
    for id_ev, just in exclusoes.items():
        if just and just.strip():
            excl_validas.add(id_ev)
            auditoria.append(
                AuditLog(mes_ano_ref, "EXCLUSAO_MANUAL", id_ev, just.strip(), agora)
            )

    # 1) Cotas por veículo (FIPE) + denominador purista (ativo E adimplente)
    cotas_veic: dict[str, tuple[float, bool]] = {}
    cotas_ativas: dict[str, float] = defaultdict(float)
    n_assoc_eleg: dict[str, int] = defaultdict(int)
    n_eleg_total = 0
    for v in veiculos_list:
        qc, especial = cotas_por_fipe(v.valor_fipe, params)
        cotas_veic[v.id_veiculo] = (qc, especial)
        if v.status_ativo and v.adimplente:
            cotas_ativas[v.segmento] += qc
            n_assoc_eleg[v.segmento] += 1
            n_eleg_total += 1

    # 2) Reclassificação pela regra dos 75% + filtro de exclusões manuais
    eventos_proc: list[tuple[EventoAT, str, bool]] = []  # (ev, tipo_efetivo, reclassificado)
    n_reclass = 0
    for e in eventos_list:
        if e.id_evento in excl_validas:
            continue
        tipo_ef = e.tipo_evento
        recl = False
        if tipo_ef != "INTEGRAL" and aplica_regra_75(e.orcamento_reparo, e.valor_fipe, params):
            tipo_ef, recl, n_reclass = "INTEGRAL", True, n_reclass + 1
        eventos_proc.append((e, tipo_ef, recl))

    def _acc(seg: str, excluir: set[str] | None = None):
        """Acumula custos do segmento; `excluir` ignora ids (eventos postergados)."""
        excluir = excluir or set()
        ci = cp = ds = df = rt = 0.0
        maior = 0.0
        for e, tipo_ef, _ in eventos_proc:
            if e.segmento != seg or e.id_evento in excluir:
                continue
            custo = _custo_evento(e, tipo_ef)
            if e.envolvimento == "TERCEIRO":
                rt += custo
                continue
            if tipo_ef == "INTEGRAL":
                ci += custo
            else:
                cp += custo
            if e.salvado_liquidado:
                ds += e.valor_salvado
            df += e.franquia
            maior = max(maior, custo)
        return ci, cp, ds, df, rt, maior

    # 3) Eventos rateados — FIFO (postergado → data ASC → tipo → valor DESC),
    #    com teto do pote caminhão (PESADOS associado corta no arrecadado)
    pote_caminhao_arrec = round(
        params.valor_fixo_caminhao_por_assoc * n_assoc_eleg.get("PESADOS", 0)
        if params.valor_fixo_caminhao_por_assoc > 0
        else params.arrecadacao_caminhao_estimada,
        2,
    )
    tipo_rank = {"INTEGRAL": 0, "PARCIAL": 1}
    ordenados = sorted(
        eventos_proc,
        key=lambda t: (
            0 if t[0].postergado else 1,
            t[0].data_aviso,
            tipo_rank.get(t[1], 9),
            -_custo_evento(t[0], t[1]),
            t[0].id_evento,
        ),
    )
    eventos_rateados: list[EventoRateadoAT] = []
    postergados_ids: set[str] = set()
    gasto_caminhao = 0.0
    n_post = 0
    for i, (e, tipo_ef, recl) in enumerate(ordenados, start=1):
        custo = round(_custo_evento(e, tipo_ef), 2)
        status = "ALOCADO"
        if e.segmento == "PESADOS" and e.envolvimento == "ASSOCIADO":
            if pote_caminhao_arrec > 0 and gasto_caminhao + custo > pote_caminhao_arrec + 0.005:
                status = "POSTERGADO"
                postergados_ids.add(e.id_evento)
                n_post += 1
            else:
                gasto_caminhao = round(gasto_caminhao + custo, 2)
        eventos_rateados.append(
            EventoRateadoAT(
                mes_ano_ref=mes_ano_ref, id_evento=e.id_evento, protocolo=e.protocolo,
                segmento=e.segmento, envolvimento=e.envolvimento, data_aviso=e.data_aviso,
                tipo_evento=tipo_ef, reclassificado_75pct=recl, valor_evento=round(e.valor_evento, 2),
                custo_a_ratear=custo, ordem_fifo=i, status=status,
            )
        )

    # 4) Apuração por segmento variável + invariante (apurado − alocado == 0)
    segmentos: list[SegmentoResultado] = []
    cota_por_seg: dict[str, float] = {}
    bruto_por_seg: dict[str, float] = {}
    recup_por_seg: dict[str, float] = {}
    custo_ratear_seg: dict[str, float] = {}
    hist_all = historico_cotas or {}
    alerta_var_global = False
    for seg in VARIAVEIS:
        ci, cp, ds, df, rt, maior = _acc(seg)
        aci, acp, ads, adf, art, _ = _acc(seg, postergados_ids)
        # N3 (transcrição): terceiro é produto à parte (pote) — NÃO abate a cota
        # variável. Fórmula = (integrais + parciais − salvados − franquias) / cotas.
        custo_a_ratear = round(ci + cp - ds - df, 2)
        custo_alocado = round(aci + acp - ads - adf, 2)
        dif_seg = round(custo_a_ratear - custo_alocado, 2)
        cotas = round(cotas_ativas.get(seg, 0.0), 2)
        valor_cota = round(custo_a_ratear / cotas, 2) if cotas > 0 else 0.0
        bruto = round(ci + cp, 2)
        vol = bruto > 0 and maior > params.pct_volatilidade * bruto
        # N1: estabilização pela média dos últimos 3 meses (variação ± var_trimestral_max)
        hist = [h for h in hist_all.get(seg, []) if h > 0][-3:]
        media_3m = round(sum(hist) / len(hist), 2) if hist else 0.0
        var_media = round((valor_cota - media_3m) / media_3m, 4) if media_3m > 0 else 0.0
        alerta_var = media_3m > 0 and abs(var_media) > params.var_trimestral_max
        if valor_cota < params.cota_alvo_min:
            faixa, sug = "ABAIXO", "Cota abaixo do alvo: acelerar pagamentos pendentes (fôlego financeiro)."
        elif valor_cota > params.cota_alvo_max:
            faixa, sug = "ACIMA", "Cota acima do alvo: postergar eventos integrais recentes (estabilização > FIFO)."
        else:
            faixa, sug = "OK", "Cota dentro da faixa de estabilização."
        if alerta_var:
            alerta_var_global = True
            sug = (f"ALERTA Variação trimestral {var_media:+.1%} (limite ±"
                   f"{params.var_trimestral_max:.0%} vs média 3M R$ {media_3m}) — "
                   f"assistente de ajuste. ") + sug
        if vol:
            sug = "ALERTA Instabilidade de Cota: sinistro único > 25% do pool — postergar parciais recentes. " + sug
        cota_por_seg[seg] = valor_cota
        bruto_por_seg[seg] = bruto
        recup_por_seg[seg] = round(rt, 2)
        custo_ratear_seg[seg] = custo_a_ratear
        segmentos.append(
            SegmentoResultado(
                segmento=seg, modo="RATEIO_VARIAVEL",
                custo_integrais=round(ci, 2), custo_parciais=round(cp, 2),
                deducao_salvados=round(ds, 2), deducao_franquias=round(df, 2),
                recuperacao_terceiros=round(rt, 2), custo_a_ratear=custo_a_ratear,
                cotas_ativas=cotas, valor_cota=valor_cota,
                arrecadado=0.0, reserva_ou_deficit=0.0,
                alerta_volatilidade=vol, faixa_estabilizacao=faixa, sugestao=sug,
                diferenca_alvo_vs_alocado=dif_seg,
                media_cota_3m=media_3m, variacao_vs_media=var_media,
                alerta_variacao_trimestral=alerta_var,
            )
        )

    # 5) PESADOS — casco caminhão = pote fixo segregado (não entra nas cotas).
    #    A recuperação de terceiros NÃO abate aqui (pertence ao pote Terceiros).
    pc_ci, pc_cp, pc_ds, pc_df, pc_rt, _ = _acc("PESADOS")
    pote_caminhao_custo = round(pc_ci + pc_cp - pc_ds - pc_df, 2)
    pote_caminhao_reserva = round(pote_caminhao_arrec - pote_caminhao_custo, 2)
    segmentos.append(
        SegmentoResultado(
            segmento="PESADOS", modo="POTE_FIXO",
            custo_integrais=round(pc_ci, 2), custo_parciais=round(pc_cp, 2),
            deducao_salvados=round(pc_ds, 2), deducao_franquias=round(pc_df, 2),
            recuperacao_terceiros=round(pc_rt, 2), custo_a_ratear=pote_caminhao_custo,
            cotas_ativas=0.0, valor_cota=0.0,
            arrecadado=pote_caminhao_arrec, reserva_ou_deficit=pote_caminhao_reserva,
            alerta_volatilidade=False,
            faixa_estabilizacao="OK" if pote_caminhao_reserva >= 0 else "ACIMA",
            sugestao=("Pote caminhão com reserva (gordura)." if pote_caminhao_reserva >= 0
                      else "Déficit no pote caminhão: postergar PTs ao próximo ciclo."),
            diferenca_alvo_vs_alocado=0.0,
        )
    )

    # 6) Pote Danos a Terceiros (50k/100k) — fixo, per-capita.
    #    Custo proxy = recuperações de terceiros de todos os segmentos.
    pote_terc_custo = round(sum(recup_por_seg.values()) + pc_rt, 2)
    pote_terc_arrec = round(
        params.valor_fixo_terceiros_por_assoc * n_eleg_total
        if params.valor_fixo_terceiros_por_assoc > 0
        else params.arrecadacao_terceiros_estimada,
        2,
    )
    pote_terc_reserva = round(pote_terc_arrec - pote_terc_custo, 2)

    # 7) Boletos (todos os veículos; gera_boleto só p/ ativo+adimplente)
    pote_terc_percap = round(pote_terc_arrec / n_eleg_total, 2) if n_eleg_total else 0.0
    n_pes = n_assoc_eleg.get("PESADOS", 0)
    pote_cam_percap = round(pote_caminhao_arrec / n_pes, 2) if n_pes else 0.0
    boletos: list[BoletoAT] = []
    for v in veiculos_list:
        qc, especial = cotas_veic[v.id_veiculo]
        eleg = v.status_ativo and v.adimplente
        rateio = round(qc * cota_por_seg.get(v.segmento, 0.0), 2) if (eleg and v.segmento in VARIAVEIS) else 0.0
        c_cam = pote_cam_percap if (eleg and v.segmento == "PESADOS") else 0.0
        c_terc = pote_terc_percap if eleg else 0.0
        total = round(rateio + c_cam + c_terc + v.servicos_adicionais, 2)
        boletos.append(
            BoletoAT(
                id_veiculo=v.id_veiculo, placa=v.placa, mes_ano_ref=mes_ano_ref,
                segmento=v.segmento, valor_fipe=v.valor_fipe, qtd_cotas=qc,
                cota_especial=especial, custo_rateio=rateio, custo_pote_terceiros=c_terc,
                custo_pote_caminhao=c_cam, servicos_adicionais=round(v.servicos_adicionais, 2),
                valor_total_boleto=total, gera_boleto=eleg,
            )
        )

    # 8) Consolidado + invariante de auditoria
    dif = round(
        sum(s.diferenca_alvo_vs_alocado for s in segmentos if s.modo == "RATEIO_VARIAVEL"), 2
    )
    consolidado = ConsolidadoAT(
        mes_ano_ref=mes_ano_ref,
        cota_leves=cota_por_seg.get("LEVES", 0.0),
        cota_motos=cota_por_seg.get("MOTOS", 0.0),
        custo_a_ratear_leves=custo_ratear_seg.get("LEVES", 0.0),
        custo_a_ratear_motos=custo_ratear_seg.get("MOTOS", 0.0),
        bruto_leves=bruto_por_seg.get("LEVES", 0.0),
        bruto_motos=bruto_por_seg.get("MOTOS", 0.0),
        recuperacao_terceiros_leves=recup_por_seg.get("LEVES", 0.0),
        recuperacao_terceiros_motos=recup_por_seg.get("MOTOS", 0.0),
        pote_caminhao_arrecadado=pote_caminhao_arrec,
        pote_caminhao_custo=pote_caminhao_custo,
        pote_caminhao_reserva=pote_caminhao_reserva,
        pote_terceiros_arrecadado=pote_terc_arrec,
        pote_terceiros_custo=pote_terc_custo,
        pote_terceiros_reserva=pote_terc_reserva,
        total_veiculos=len(veiculos_list),
        total_veiculos_elegiveis=n_eleg_total,
        total_cotas_leves=round(cotas_ativas.get("LEVES", 0.0), 2),
        total_cotas_motos=round(cotas_ativas.get("MOTOS", 0.0), 2),
        eventos_alocados=sum(1 for er in eventos_rateados if er.status == "ALOCADO"),
        eventos_postergados=n_post,
        eventos_reclassificados_75pct=n_reclass,
        diferenca_total=dif,
        invariante_ok=abs(dif) < 0.01,
        alerta_variacao_trimestral=alerta_var_global,
    )
    return ResultadoRateioAT(
        mes_ano_ref=mes_ano_ref, consolidado=consolidado, segmentos=segmentos,
        eventos_rateados=eventos_rateados, boletos=boletos, auditoria=auditoria,
    )
