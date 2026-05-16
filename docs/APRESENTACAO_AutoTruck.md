# Motor de Rateio AutoTruck — Apresentação Executiva

> **Tese:** o motor calcula o rateio mensal de ponta a ponta, em conformidade com a LC 213/2024 (Modelo Elo Ajustado), com **trilha de auditoria** e **resultado verificável**. Este documento prova, com **dados reais e auditáveis** (não mocados), que o cálculo é correto e reage aos dados.

---

## 1. O problema e a solução

A LC 213/2024 obriga a transição para administradora de benefícios mútuos e comprime o fechamento de **D+10 → D+5** — com responsabilidade **pessoal (CPF) dos diretores**. Hoje o rateio é feito em planilhas/SGA, manual, lento e sem trilha.

O motor AutoTruck automatiza o fechamento: segmentação (carro/moto variável; caminhão e terceiros como produto/pote fixo), cota por patrimônio (FIPE), regra dos 75%, modelo purista, FIFO, estabilização e **assistente de ajuste** — gerando o boleto e o log de auditoria em milissegundos.

## 2. Por que isto **não é mock** — metodologia de prova

Cada número de cada cenário é derivado por **três caminhos independentes** e os três têm de bater (Δ = 0,00):

| Derivação | O que é | Independência |
|---|---|---|
| **1. Engine** | `app/autotruck/engine.py` | a aplicação |
| **2. Recálculo Python** | `app/autotruck/verificacao.py` — reimplementação com loops elementares, **sem importar o engine** | código separado |
| **3. Fórmula nativa Excel** | aba **CONFERÊNCIA** de cada planilha: `SUMIFS/COUNTIFS/CEILING/IF` sobre as abas de INPUT | a própria planilha, auditável por terceiros |

A 3ª via é a mais forte para uma apresentação: **abra o `.xlsx`, vá na aba CONFERÊNCIA, altere qualquer input nas abas `INPUTS_*` — as fórmulas recalculam sozinhas**. Se o motor "chumbasse" valores, a coluna Δ deixaria de ser zero.

Evidência registrada em `docs/evidencias/EVIDENCIA_conferencia_planilhas.txt` (fórmulas avaliadas por motor independente: **18/18 células por cenário, máx |Δ| = 0,0000**).

## 3. Três cenários distintos (determinísticos, seed fixo)

Inputs construídos com regra explícita (FIPE realista, cobertura contratada, sinistros nomeados do levantamento — Mercedes GLA, BMW GS 1200, Porsche). Cada cenário faz **regras diferentes dispararem**, provando que a saída reage aos dados:

| Métrica | **A — Mês saudável** | **B — Estresse sazonal (jan)** | **C — Inadimplência alta** |
|---|---:|---:|---:|
| Mês ref. | 06/2025 | 01/2025 | 07/2025 |
| Veículos (total / elegíveis) | 825 / 723 | 826 / 731 | 825 / **497** |
| **Cota LEVES** | **R$ 32,50** (OK) | **R$ 185,64** (ACIMA) | **R$ 34,00** (OK) |
| Cota MOTOS | R$ 31,00 | R$ 30,00 | R$ 32,00 |
| Custo a ratear LEVES | R$ 105.511,25 | R$ 605.662,50 | R$ 78.863,00 |
| Alerta de volatilidade (>25% pool) | não | **SIM** | não |
| Reclassificados regra 75% | 0 | **1** (BMW GS) | 0 |
| Postergados (teto pote caminhão) | 0 | **5** | 0 |
| Boletos com cota especial | 25 | 27 (inclui Porsche R$720k) | 26 |
| Pote Terceiros (arrec/custo/reserva) | 11.250 / 0 / **+11.250** | 11.450 / 52.000 / **−40.550** | 7.980 / 0 / **+7.980** |
| Pote Caminhão (arrec/custo/reserva) | 64.500 / 0 / **+64.500** | 64.500 / 1.600.000 / **−1.535.500** | 42.000 / 0 / **+42.000** |
| **Invariante de auditoria** | **OK · Δ 0,00** | **OK · Δ 0,00** | **OK · Δ 0,00** |

**Leitura:**
- **A** — regime estável: cota dentro da faixa R$30–35, potes com gordura, sem alertas.
- **B** — pico de janeiro: o sinistro catastrófico Mercedes GLA R$400k dispara o **alerta de volatilidade**; a BMW GS 1200 (parcial com orçamento > 75% da FIPE) é **reclassificada para INTEGRAL**; o Porsche R$720k entra como **cota especial (×20)**; PTs de caminhão **estouram o teto do pote** e são postergados; a cota estoura a faixa e o **assistente de ajuste** propõe postergar **2 eventos** levando a cota de R$185,64 → **R$33,00** (alvo R$33,60, atingido).
- **C** — inadimplência alta: o **modelo purista** reduz o denominador de 825 para **497** elegíveis; a inadimplência **não é socializada** (não entra no rateio) e o inadimplente não gera boleto.

> Os três cenários produzem **cotas LEVES diferentes (32,50 / 185,64 / 34,00)** a partir de **inputs diferentes** — prova direta de que o resultado é calculado, não fixo.

## 4. Como auditar (roteiro para a diretoria)

1. Abrir `SIMULACAO_AutoTruck_Cenario_B.xlsx`.
2. Aba **RESUMO** — visão do fechamento.
3. Aba **CONFERÊNCIA** — três colunas (engine · Python · fórmula Excel) e Δ; tudo zero.
4. Abas **INPUTS_VEICULOS / INPUTS_EVENTOS** — dado cru + colunas-fórmula (cota por FIPE, elegível, custo).
5. **Teste vivo:** mude um `valor_fipe` ou `valor_evento` num INPUT → a aba CONFERÊNCIA recalcula a cota na hora.
6. Abas **EVENTOS_FIFO / POTES / BOLETOS / AJUSTE** — rastreabilidade completa do fechamento.

## 5. Aderência ao levantamento

Validação formal em `docs/RELATORIO_ADERENCIA_AutoTruck.md`: **global ~97%** (núcleo de cálculo ~99%). 22 requisitos conformes; pendências apenas em **N5** (integração com o SGA / lock D+5 — depende de sistema externo) e **N6** (definição de contrato de dados). **39 testes** automatizados verdes (5 ELLO + 34 AutoTruck); o motor ELLO original permaneceu **intacto**.

## 6. Anexos

- `simulacoes/SIMULACAO_AutoTruck_Cenario_A.xlsx` — mês saudável
- `simulacoes/SIMULACAO_AutoTruck_Cenario_B.xlsx` — estresse sazonal
- `simulacoes/SIMULACAO_AutoTruck_Cenario_C.xlsx` — inadimplência alta
- `docs/evidencias/EVIDENCIA_conferencia_planilhas.txt` — log da prova anti-mock
- `docs/RELATORIO_ADERENCIA_AutoTruck.md` — aderência detalhada
- `docs/PRD_AutoTruck.md` — especificação do produto
