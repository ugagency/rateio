"""
Modelo financeiro do BP NEWCO (Mutualiza 50% / RATEIOSA 50%).
Horizonte: 24 meses. Todos os valores em R$, mensal, PJ, sem impostos da NEWCO (Lucro Presumido/Real a definir com contador).
"""

# ---------- 1. EQUIPE (custo mensal por papel, ramp por mês) ----------
# cada papel: (mes_inicio, custo_mensal, mes_fim_ou_None)
EQUIPE = {
    "Tech Lead / Arquiteto":        (1, 5500, None),
    "Dev Backend Senior":           (1, 12000, None),
    "Dev Backend Pleno":            (3, 9000, None),
    "Dev Frontend/Mobile Pleno":    (1, 9000, None),
    "DevOps/SRE (part-time)":       (2, 4000, None),
    "QA (part-time)":               (3, 3000, None),
    "Atuario IBA (fracionario)":    (1, 3500, None),
    "Contador regulatorio (frac.)": (4, 2500, None),
    "DPO / Compliance LGPD (frac.)":(1, 1500, None),
    "Suporte N1 (part-time)":       (7, 2500, None),
}

INFRA = {
    1: 1500, 2: 1800, 3: 1800, 4: 2200, 5: 2200, 6: 2500,
}
INFRA_STEADY = 3500  # a partir do mes 7, cresce com escala

def custo_equipe(mes):
    total = 0
    detalhe = {}
    for papel, (ini, valor, fim) in EQUIPE.items():
        if mes >= ini and (fim is None or mes <= fim):
            total += valor
            detalhe[papel] = valor
    return total, detalhe

def custo_infra(mes):
    if mes <= 6:
        return INFRA.get(mes, 1500)
    # cresce levemente com o numero de associacoes ativas
    assoc = associacoes_ativas(mes)
    return INFRA_STEADY + max(0, assoc - 1) * 300

# ---------- 2. RAMPA DE ASSOCIACOES E PLACAS ----------
# meses 1-6: build, sem operacao paga (piloto interno com dados reais no mes 6)
# mes 7: 1a associacao (AutoTruck) migrada, ~90k placas
# mes 10: 2a associacao (ELLO), +60k placas
# mes 13: 3a associacao (AVAP), +40k placas -> ~190k placas (as 3 da Mutualiza)
# mes 16-24: expansao para associacoes adicionais da carteira Mutualiza, +40k placas a cada 3 meses ate ~10 associacoes

def associacoes_ativas(mes):
    if mes < 7: return 0
    if mes < 10: return 1
    if mes < 13: return 2
    if mes < 16: return 3
    # expansao gradual
    extra = (mes - 16) // 3 + 1
    return min(3 + extra, 10)

def placas_ativas(mes):
    if mes < 7: return 0
    if mes < 10: return 90_000
    if mes < 13: return 150_000
    if mes < 16: return 190_000
    extra_assoc = associacoes_ativas(mes) - 3
    return 190_000 + extra_assoc * 40_000

# ---------- 3. RECEITA ----------
PRECO_CENARIOS = {"R$0,10/placa": 0.10, "R$0,20/placa": 0.20, "R$0,30/placa": 0.30}
MINIMO_MENSAL = 8000  # piso contratual por associacao ativa (protege contra oscilacao de volume)

def receita_mes(mes, preco_placa, n_associacoes_min=True):
    placas = placas_ativas(mes)
    assoc = associacoes_ativas(mes)
    bruta = placas * preco_placa
    piso = assoc * MINIMO_MENSAL
    return max(bruta, piso), placas, assoc

# ---------- 4. TARIFAS DE MEIO DE PAGAMENTO (iugu) ----------
# 1 boleto/pix por veiculo ativo por mes (mesmo denominador de placas)
TARIFA_BOLETO = 2.00   # media da faixa pesquisada R$1,99-2,50 (fixo por titulo pago)
TARIFA_PIX    = 1.20   # media da faixa pesquisada (fixo) OU 0,99% do valor - usamos fixo conservador
MIX_PIX = 0.6          # premissa: 60% pagam via PIX, 40% boleto registrado

def custo_meios_pagamento(mes):
    placas = placas_ativas(mes)
    boletos = placas * (1 - MIX_PIX)
    pix = placas * MIX_PIX
    return boletos * TARIFA_BOLETO + pix * TARIFA_PIX

# ---------- 5. SIMULACAO ----------
def simular(preco_placa, repasse_iugu):
    linhas = []
    caixa_acumulado = 0
    investimento_total = 0
    mes_breakeven_op = None
    for mes in range(1, 25):
        c_equipe, _ = custo_equipe(mes)
        c_infra = custo_infra(mes)
        c_pagamento = custo_meios_pagamento(mes)
        receita, placas, assoc = receita_mes(mes, preco_placa)

        opex = c_equipe + c_infra
        if not repasse_iugu:
            opex += c_pagamento
        # se repasse: custo de meios de pagamento sai do boleto do associado, nao do opex da NEWCO

        resultado = receita - opex
        caixa_acumulado += resultado
        if resultado < 0:
            investimento_total += -resultado
        if mes_breakeven_op is None and resultado >= 0 and mes >= 7:
            mes_breakeven_op = mes

        linhas.append(dict(mes=mes, equipe=c_equipe, infra=c_infra,
                            pagamento=c_pagamento if not repasse_iugu else 0,
                            pagamento_repassado=c_pagamento if repasse_iugu else 0,
                            opex=opex, receita=receita, placas=placas, assoc=assoc,
                            resultado=resultado, caixa_acum=caixa_acumulado))
    return linhas, investimento_total, mes_breakeven_op, caixa_acumulado

if __name__ == "__main__":
    for repasse in (False, True):
        print("=" * 90)
        print("REPASSE DA TARIFA IUGU AO ASSOCIADO:" , "SIM" if repasse else "NAO (absorvida pela NEWCO)")
        for nome, preco in PRECO_CENARIOS.items():
            linhas, invest, breakeven, caixa_final = simular(preco, repasse)
            print(f"\n--- Cenario {nome} ---")
            print(f"Investimento total necessario (soma dos meses negativos): R$ {invest:,.0f}")
            print(f"Mes de break-even operacional (receita >= opex, apos mes 7): {breakeven}")
            print(f"Caixa acumulado ao final do mes 24: R$ {caixa_final:,.0f}")
            l12 = linhas[11]
            l24 = linhas[23]
            print(f"Mes 12 -> placas {l12['placas']:,} | assoc {l12['assoc']} | receita R$ {l12['receita']:,.0f} | opex R$ {l12['opex']:,.0f} | resultado R$ {l12['resultado']:,.0f}")
            print(f"Mes 24 -> placas {l24['placas']:,} | assoc {l24['assoc']} | receita R$ {l24['receita']:,.0f} | opex R$ {l24['opex']:,.0f} | resultado R$ {l24['resultado']:,.0f}")

    # detalhe do custo de meios de pagamento em regime (mes 16, 190k placas)
    print("\n" + "=" * 90)
    for mes in (7, 12, 16, 24):
        c = custo_meios_pagamento(mes)
        p = placas_ativas(mes)
        print(f"Mes {mes}: {p:,} placas -> custo total meios de pagamento (iugu) R$ {c:,.0f}/mes "
              f"(R$ {c/max(p,1):.2f}/placa)")

    print("\n--- custo de equipe por mes (ramp) ---")
    for mes in (1, 3, 5, 7, 12, 24):
        total, det = custo_equipe(mes)
        print(f"Mes {mes}: equipe R$ {total:,.0f} | infra R$ {custo_infra(mes):,.0f}")
