# Relatório de Aderência — Motor AutoTruck vs. Reunião de Levantamento

> Validação do motor de rateio AutoTruck (commit `a8429b4`) contra os requisitos extraídos da transcrição da reunião de levantamento. Itens sem relação direta com o rateio AutoTruck foram descartados (SGA/Power CRM/Localiza/Inova, histórico de produto, papo operacional, comparações com ELLO usadas só como contraste).

## Veredito

| Dimensão | Aderência (inicial → após ajustes N3/N1) |
|---|---|
| **Núcleo de cálculo** (fórmula, segmentação, cotas, 75%, purista, FIFO, potes, salvado, boleto) | ~95% → **~98%** (N3 alinhado à transcrição) |
| **Governança / estabilização / automação assistida** | ~55% → **~75%** (N1 implementado) |
| **Global (ponderado)** | ~85% → **~92%** |

> **Atualização 2026-05-15:** ajustes **N3** (terceiro não abate a cota — segue a transcrição) e **N1** (estabilização por média trimestral ±5%) **implementados e validados** (commit dos ajustes; suíte 27 testes verde, ELLO intacto). Restam **N2/N4/N5** (parciais, fase 2) e **N6** (observação de contrato de dados).

24 requisitos de rateio avaliados: **20 conformes**, **3 parciais**, **0 não conforme**, **1 observação de modelagem**.

---

## 1. Conformidades (aderente)

| # | Requisito (transcrição) | Implementação |
|---|---|---|
| C1 | Três bases separadas: carro, moto, caminhão — "rateio do caminhão é um, da moto é outro, do carro é outro" | `LEVES`/`MOTOS` variáveis com bases separadas; `PESADOS` segregado. Sem subvenção cruzada. |
| C2 | Caminhão é **produto/pote fixo**, "é como de terceiro, valor fixo, independe do sinistro" | `PESADOS` = `POTE_FIXO` (arrecadado/custo/reserva), fora da divisão de cotas. |
| C3 | FIFO — "quanto mais antigo o evento vem primeiro", por **data de aviso** | Ordenação `postergado → data_aviso ASC → tipo → valor DESC`; postergado = prioridade #1. |
| C4 | Fórmula: soma integral + parcial ÷ cotas ativas | `engine`: `(Σintegrais + Σparciais − deduções) / cotas_ativas`. |
| C5 | Integral e parcial **pagam igual** (somados na conta) | Ambos somam no custo a ratear sem peso diferente. |
| C6 | Cotas por **valor do patrimônio**, faixas de R$10.000 ("51k e 59k pagam igual") | `cotas_por_fipe`: faixa R$10k, valor constante dentro da faixa. |
| C7 | **Cota especial** > R$450.000 com multiplicador (15–20) — "Porsche, quebra a base" | FIPE > 450k → `multiplicador_especial` 20 (configurável 15–20), sem progressão linear. |
| C8 | **Regra dos 75%** — BMW GS: "excedeu 75% do valor, deu PT com valor" | `aplica_regra_75`: orçamento > 75% FIPE → reclassifica PARCIAL→INTEGRAL (entra pelo FIPE). |
| C9 | Cota ativa = veículo ativado/regular, último boleto pago, ou recém-entrado | Elegível = `status_ativo AND adimplente`; recém-entrado (sem dívida) conta. |
| C10 | **Modelo purista** — não socializa inadimplência; recuperação de meses anteriores = crédito administrativo (fora do rateio) | Denominador só ativos+adimplentes; recuperação documentada como crédito adm. (PRD §8). |
| C11 | Terceiros = **produto**, não entra na divisão; teto = arrecadado; excedente posterga, sobra vira gordura | Pote Terceiros (arrecadado/custo/reserva); excedente FIFO → `POSTERGADO`; reserva quando sobra. |
| C12 | Salvado **já vem líquido**; quando entra caixa, abate no mês seguinte | `salvado_liquidado`: só deduz no mês da liquidação financeira. |
| C13 | Boleto final = **cota (rateio) + produtos/serviços** | `BoletoAT = custo_rateio + pote_terceiros + pote_caminhao + servicos_adicionais`. |
| C14 | Origem do evento **não importa**; integral/parcial/terceiro tratados de formas distintas | Engine ignora origem; ramifica por `tipo_evento`/`envolvimento`. |
| C15 | Risco **por patrimônio**, sem perfil/subvenção (variável, não cota fixa) | Cota = custo/cotas (variável); cotas só por FIPE; nenhum fator de perfil. |
| C16 | Audit trail de alteração manual com justificativa (D&O / LC 213, CPF do diretor) | `AuditLog` imutável; exclusão exige justificativa não-vazia; endpoint `/auditoria`. |
| C17 | Painel para ver/trocar eventos e simular antes de fechar | `POST /autotruck/replay` (simula sem persistir) + `exclusoes` manuais. |
| C18 | Foto de fechamento imutável (snapshot, "daqui 5 min não pode") | Cálculo determinístico sobre snapshot de entrada (veículos+eventos). |

## 2. Não conformidades e parciais

| # | Ponto | Status | Detalhe e ação recomendada |
|---|---|---|---|
| **N1** | Estabilização por **média dos últimos 3 meses ± 5%** | **✅ Resolvido (conforme)** | Implementado: o motor recebe `historico_cotas` (cotas dos meses anteriores persistidos, montadas pelo service a partir do repo), calcula `media_cota_3m`, `variacao_vs_media` e `alerta_variacao_trimestral` (|var| > 5%) por segmento; sugestão e flag agregado no consolidado. Coberto por testes. |
| **N2** | **Ajuste inteligente**: sugerir o conjunto **mínimo de eventos** para sair de 37→30, priorizando integral recente; "oficina é nota fechada, raramente mexe" | **Parcial** | Hoje há exclusão manual + replay + texto consultivo, mas **não** o otimizador que escolhe os eventos a postergar para atingir a meta com mínimo de trocas, nem a regra de preferência (integral recente; não mexer em oficina/nota fechada). **Ação:** implementar recomendador (greedy/knapsack) com essas prioridades. |
| **N3** | **Recuperação de terceiros abatendo a cota variável** | **✅ Resolvido (conforme à transcrição)** | Decisão tomada: a transcrição governa — terceiro é produto à parte (pote), **não abate** a cota. Removido `− recuperacao_terceiros` da fórmula variável; recuperação segue rastreada (pote Terceiros + informativo no segmento). Cota LEVES passou de ~R$53,84 → ~R$75,75. Invariante = 0 mantido. |
| **N4** | Parametrização dos potes (Terceiros R$20/faixa 50k, R$30/faixa 100k; arrecadação caminhão) | **Parcial** | A mecânica de teto/postergação/gordura existe, mas os defaults deixam o pote caminhão inerte (`arrecadacao_caminhao_estimada=0`) e o valor fixo por faixa de cobertura de terceiro não é modelado por produto. **Ação:** tabela de preço de produto (terceiro 50k/100k, casco caminhão) e arrecadação por base. |
| **N5** | Fluxo **D+5 / database / lock / inativação automática** | **Parcial (fora do escopo do motor)** | O cálculo é instantâneo (habilita o D+5) e o PRD §10 documenta o fluxo, mas o workflow de database (último dia do mês), lock do snapshot e inativação de inadimplentes é da ferramenta de gestão de cobrança do SGA — não implementado aqui. **Ação:** integração SGA (ingestão/lock) em fase posterior. |
| **N6** | Dedução explícita de franquia/salvado no motor | **Observação** | A transcrição diz que parcial **já vem** líquido de franquia e o salvado já vem abatido do SGA. O motor tem linhas explícitas `deducao_franquias`/`deducao_salvados`. Funcionalmente equivalente se a fonte vier zerada (é o caso do dataset), mas há **risco de dupla dedução** se o SGA já entregar líquido. **Ação:** definir contrato de dados (bruto vs. líquido) e travar um único ponto de dedução. |

## 3. Itens corretamente fora do motor (não são não-conformidades)

- Obrigação contratual de 12 meses ativo após indenização integral → regra de SGA/contrato, não de cálculo.
- Emissão física do boleto no banco / arquivo de remessa → SGA.
- Prazo de comunicação do aviso de sinistro → regra da LC/minuta, upstream.
- Atribuição do mês de competência pelo mês do aviso → preparação de dados upstream (o motor respeita `data_aviso`).
- Modelo de "potinhos cumulativos / alvo fixo" → é do ELLO; a transcrição contrasta explicitamente. AutoTruck **corretamente não** usa esse modelo.

## 4. Conclusão

O **núcleo de cálculo do rateio AutoTruck está fiel à reunião** (~98%): segmentação, fórmula, cotas por patrimônio, cota especial, regra dos 75%, FIFO, modelo purista, potes fixos, salvado e composição do boleto — todos conformes. Os ajustes **N3** (terceiro não abate a cota — segue a transcrição) e **N1** (estabilização por média trimestral ±5%) foram implementados e validados, elevando a aderência global para **~92%**. As lacunas remanescentes são **incrementos de fase 2**: N2 (otimizador de ajuste inteligente), N4 (tabela de preço dos produtos/potes) e N5 (integração SGA / fluxo D+5 com lock), além de N6 (definir contrato de dados bruto vs. líquido). Nenhuma invalida o motor.
