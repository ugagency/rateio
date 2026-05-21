# Homologação do Motor de Rateio AutoTruck — pedido de validação

**Para:** Rodrigo (AutoTruck)
**De:** Eduardo / Mut
**Anexos:** 4 arquivos em `simulacoes/HOMOLOGACAO/`

---

## O que estamos te pedindo

Construímos um motor de rateio que processa exatamente a estrutura da sua planilha de fechamento mensal (BASE / RATEIO / PRODUTOS → ANALITICO no layout das 6 abas). Antes de você nos liberar a base real sob NDA, queremos **te provocar a fazer o exercício inverso**:

1. Pegue os 3 arquivos de entrada (INPUT_BASE / INPUT_RATEIO / INPUT_PRODUTOS) e jogue na sua planilha de fechamento real.
2. Abra o nosso `FECHAMENTO_AutoTruck_Homologacao.xlsx` em paralelo.
3. Olhe se **a lógica, o layout e a mecânica fazem sentido** — não os centavos.
4. Nos diga: "faz sentido" ou "não faz, está errado em X".

Se fizer sentido → assinamos NDA → rodamos sua base real e geramos o ANALITICO mensal de verdade.

---

## Importante: estes não são seus dados reais

Os 3 inputs foram construídos por **reconstrução dos prints/transcrições da nossa videoconferência de 19/05**, com:

- **Jitter ±5%** sobre cada valor numérico (cotas, valores recebidos, valores rateados, participação, quantidades de boletos)
- **Placas permutadas** entre os eventos (mantém o conjunto, troca quem é quem)
- **Protocolos substituídos** por `HOM-NNNNN` sequencial
- **Cotas LEVES adimplentes adotadas em 4.275** (faltava esse dado na BASE — chutamos um valor coerente; o real você confirma depois)

Por que essa variação: **proteção mútua**. Se mandássemos seu dado intacto, você (legitimamente) suspeitaria que tínhamos feito engenharia reversa pesada antes do NDA. Variando levemente, fica claro que é nossa reconstrução brincando com o que vimos em chamada.

Estrutura, fórmulas e proporções entre segmentos foram **preservadas 100%**. Você vai reconhecer o formato na hora.

---

## Os 4 arquivos

| Arquivo | Pra que serve |
|---|---|
| `INPUT_BASE.xlsx` | Os 3 inputs no formato que nossa plataforma consome (você vai ver — é o seu layout) |
| `INPUT_RATEIO.xlsx` | |
| `INPUT_PRODUTOS.xlsx` | |
| **`FECHAMENTO_AutoTruck_Homologacao.xlsx`** | **Peça principal.** Sua planilha de fechamento (6 abas, layout idêntico), com o ANALITICO populado pelo nosso motor a partir dos 3 inputs acima. Acrescentei uma aba `CONFERENCIA_HOMOLOGACAO` com o resumo executivo do que o motor calculou. |

---

## Resultado do motor sobre esses inputs

| Métrica | Valor |
|---|---:|
| Cota LEVES / cota | **R$ 258,45** |
| Cota MOTOS / cota | **R$ 137,82** |
| Cotas LEVES adimplentes (override) | 4.275 |
| Cotas MOTOS adimplentes (da BASE) | 2.450 (aprox., pós-jitter) |
| Bruto LEVES (integrais + parciais associados) | ~ R$ 1.105.000 |
| Bruto MOTOS (integrais + parciais associados) | ~ R$ 338.000 |
| Terceiros (rastreado, **não abate cota** — regra N3) | LEVES ~R$ 229k · MOTOS ~R$ 39k |
| Eventos alocados | 92 |
| Invariante de auditoria (Σcusto − Σalocado) | **Δ = R$ 0,00** |

---

## O que pedimos especificamente

1. **Faz sentido a estrutura?** As 6 abas, o jeito como o ANALITICO é populado, as proporções entre LEVES/MOTOS/PESADOS associados vs terceiros — está coerente com o que você faz mensalmente?
2. **Faltou alguma regra?** O motor implementa: regra dos 75% (parcial → integral por perda total), salvados só abatem quando liquidados, cota por FIPE em faixas de 10k, terceiros como pote separado, estabilização ±5% trimestral, FIFO com prioridade pra postergados, audit trail de exclusões manuais. Esquecemos algo?
3. **O quanto está fora do real?** Sem ver seu número, você consegue dizer se a ordem de grandeza (cota ~R$ 250 / LEVES, ~R$ 130 / MOTOS) está próxima ou absurda?

---

## Próximos passos (se passar)

1. Você confirma "faz sentido"
2. NDA assinado
3. Rodamos sobre a sua base real do mês corrente
4. Você compara os números pra fechar a homologação técnica
5. Se bater → vira ferramenta mensal

Qualquer dúvida ou se preferir uma chamada rápida pra eu te mostrar a plataforma rodando, é só falar.

Abraço,
Eduardo
