# PRD — Motor de Rateio AutoTruck

> **Status:** especificação aprovada para implementação (MVP).
> **Escopo de isolamento:** o motor ELLO existente (v0 scripts + HTML, v1 backend/frontend) **NÃO é alterado**. AutoTruck entra como módulo paralelo, em **novo menu**, com domínio/engine/dados próprios.
> **Fontes:** Especificação de Negócio (LC 213/2024), tabela "Regras de Rateio e Gestão de Sinistros", planilha `FECHAMENTO`, infográfico de fluxo.

---

## 1. Objetivo

Automatizar o fechamento mensal de rateio de uma administradora de proteção veicular sob o **Modelo Elo Ajustado**, em conformidade com a **LC 213/2024** (transição obrigatória para administradora de benefícios mútuos sob CNSP/SUSEP), comprimindo o ciclo de **D+10 → D+5** e garantindo trilha de auditoria imutável para respaldo do seguro D&O (proteção do CPF dos diretores).

## 2. Segmentação (bases separadas — sem subvenção cruzada)

| Classe | Tipos de veículo | Tratamento |
|---|---|---|
| **LEVES** | AUTOMOVEL, UTILITÁRIO, PREMIUM | Rateio **variável** (base própria) |
| **MOTOS** | MOTOCICLETA | Rateio **variável** (base própria) |
| **PESADOS** | CAMINHAO, SEMI REBOQUE | Casco = **pote fixo** segregado (não entra na divisão de cotas de LEVES/MOTOS) |

Motivação (spec §2): impedir que o ticket médio baixo das motos onere os carros, ou que a alta severidade dos carros prejudique a frequência das motos.

## 3. Separação de produtos (Modelo Elo Ajustado)

1. **Rateio Variável (núcleo mutualista):** Casco LEVES e Casco MOTOS — fórmula mestre, bases separadas.
2. **Potes de Preço Fixo (não entram na divisão de cotas):**
   - **Casco Caminhão (PESADOS):** arrecada valor fixo por associado; confronta com custo real. Excedente → reserva ("gordura"); déficit → postergação de eventos ao próximo ciclo.
   - **Danos a Terceiros (50k/100k):** arrecadação mensal estimada; custo não pode ultrapassar o arrecadado no mês; excesso → reserva ou postergação.
3. **Serviços Adicionais (valor fixo, opcional):** Assistência 24h, Vidros, Carro Reserva, Combo, A.P.P, Moto Reserva — soma direta ao boleto após o rateio.

## 4. Fórmula mestre (por segmento variável: LEVES e MOTOS separados)

```
                 (Σ Sinistros Integrais + Σ Sinistros Parciais)
 Valor da Cota = ─────────────────────────────────────────────────────────────────
   (segmento)            − (Salvados Liquidados + Franquias)
                  ─────────────────────────────────────────────────────────────────
                          Total de Cotas Ativas e Pagas (segmento)
```

> **Decisão N3 (2026-05-15) — governa a transcrição da reunião:** "Danos a Terceiros"
> é **produto à parte (pote fixo), NÃO entra na divisão de cotas** e **não abate**
> a cota variável. A recuperação de terceiros segue rastreada (no pote Terceiros e
> como informativo no segmento), mas **não** subtrai o custo a ratear de LEVES/MOTOS.
> (O abatimento havia sido inferido da aba ANALITICO; a regra de negócio declarada
> na reunião prevalece.)

Referência numérica (aba ANALITICO — bruto = custo a ratear; terceiros só rastreado):

| | Integral | Parcial | Bruto = Custo a ratear | Terceiros (pote, não abate) |
|---|---:|---:|---:|---:|
| **LEVES** | 1.834.103,63 | 782.113,49 | **2.616.217,12** | 756.464,11 |
| **MOTOS** | 453.544,15 | 46.638,40 | **500.182,55** | 32.982,25 |
| **PESADOS** | — | — | (pote fixo) | 14.000,00 |

## 5. Regras de negócio críticas

- **Regra dos 75% (Perda Total):** evento cujo orçamento de reparo > 75% do valor FIPE é reclassificado automaticamente como **INTEGRAL** (entra pelo valor FIPE integral). Caso BMW GS 1200: dano estético caro porém mecanicamente funcional → integral para preservar a segurança do associado.
- **Liquidação de Salvados:** rastrear **dois campos distintos** — `valor_evento` (bruto) e `custo_a_ratear`. O crédito do salvado/franquia só reduz o custo a ratear **no mês em que o recurso entra no caixa** (`salvado_liquidado=true`).
- **Cotas por patrimônio (FIPE):** progressão a cada **R$ 10.000**. Default (infográfico): ≤ R$10.000 = **1,0 cota**; R$10.001–20.000 = **1,5**; +0,5 por faixa de R$10k (configurável).
- **Cotas Especiais (High-End):** FIPE > **R$ 450.000** não segue progressão linear — aplica **Multiplicador de Risco = 20,0 cotas** (configurável 15–20). Evita que um único sinistro de luxo pulverize a base comum.

## 6. FIFO e estabilização

- **Ordenação FIFO:** `Data de Aviso (ASC) → Tipo de Evento → Valor`.
- **Prioridade de postergados:** eventos cortados em meses anteriores (teto de cota) assumem **Prioridade #1 absoluta** no fechamento seguinte.
- **Regra de ouro:** o alvo de **estabilização (R$ 30,00–R$ 35,00 por cota)** tem **precedência sobre a FIFO** para retenção de base e controle de churn.
- **Alerta de Instabilidade de Cota:** se um único sinistro representar **> 25% do pool** a ratear do segmento, dispara alerta e sugere postergar eventos parciais recentes (caso Mercedes GLA R$ 400k).

## 7. Controle de churn e ajuste inteligente

- Variação **> 5%** na média **trimestral** da cota (média dos últimos 3 meses persistidos, por segmento) → dispara o alerta do assistente de ajuste. **Implementado** (N1): o motor recebe o histórico de cotas dos meses anteriores e compara a cota apurada com a média 3M.
- **Assistente de ajuste (N2 — implementado):** dado um alvo (default = topo da banda ±5% da média 3M, ou R$35), o motor sugere o **conjunto mínimo de eventos a postergar** — candidatos ASSOCIADO ALOCADO, **só INTEGRAL** por padrão (parcial = oficina/nota fechada, raramente se mexe; opcional via `incluir_parciais`), ordenados por valor DESC (menos eventos) com desempate pelo **mais recente**. Endpoints `POST /autotruck/sugerir-ajuste` e `POST /autotruck/aplicar-ajuste` (aplica postergando via exclusão com justificativa → **audit trail**). Aba "Ajuste" no frontend.
- Cota preliminar **< R$ 30** → sugere acelerar pagamentos pendentes (usar o fôlego financeiro) — advisory.
- **Painel de Simulação:** trocas hipotéticas com recálculo imediato (endpoint de *replay* sem persistir).

## 8. Modelo Purista (denominador) e SGA

- **Foto de Fechamento (D+0, snapshot imutável):** inadimplentes são inativados; seus CPFs/placas são **excluídos do denominador** — a inadimplência **não é socializada**.
- Denominador = soma de cotas de veículos **ativos E pagos** do segmento.
- Recuperação de inadimplência de meses anteriores = **crédito administrativo**, não afeta o custo do rateio atual.

## 9. Audit Trail (governança LC 213 / D&O)

Toda alteração manual na sugestão do motor (inclusão/exclusão discricionária de evento) **exige justificativa técnica** e é registrada em **log imutável**, devolvido no resultado e consultável por mês.

## 10. Fluxo de fechamento

| Dia | Etapa |
|---|---|
| **D+0** (último dia) | Foto de Fechamento + lock da base |
| **D+1–D+3** | Processamento, simulação e homologação com auditoria |
| **D+4** | Ingestão de dados de cobrança no SGA |
| **D+5** | Emissão e envio em lote (improrrogável) |

## 11. Saídas do motor

- **Valor final da cota** por segmento (LEVES, MOTOS).
- **Composição do boleto:** Rateio (cota_seg × qtd_cotas) + Potes fixos aplicáveis (Terceiros; Casco Caminhão p/ PESADOS) + Serviços Adicionais contratados.
- **Eventos rateados** (FIFO, status liquidado/parcial/postergado).
- **Potes fixos:** arrecadado, custo, reserva/déficit.
- **Alertas:** instabilidade de cota, variação trimestral > 5%, cota fora da faixa R$30–35.
- **Log de auditoria** das intervenções manuais.
- **Invariante de auditoria:** por segmento, `Σ(cota × cotas ativas) − custo_a_ratear ≈ 0` (análogo ao invariante = 0 do ELLO).

## 12. Premissas e decisões (corrigíveis)

1. **Sem dataset real por veículo:** a aba `RATEIO` do `FECHAMENTO` é template (zeros); os números reais são agregados em `ANALITICO`. Seguindo o padrão do v0 (ELLO), geramos **dados simulados calibrados** para reproduzir os agregados de §4 como invariante de validação.
2. **Tabela de cotas por faixa:** passo de +0,5 cota por R$10k (infográfico). Parametrizável em `rules.py`.
3. **Multiplicador cota especial:** 20,0 (faixa permitida 15–20). Parametrizável.
4. **Faixa de estabilização:** R$ 30,00–R$ 35,00. Parametrizável.
5. **Persistência:** repositório **in-memory + JSON** próprio (`dados_autotruck.json`), análogo ao ELLO `json` repo — não usa o repositório/DB do ELLO.
6. **Isolamento:** nenhum arquivo do motor ELLO é modificado. Toques aditivos: +1 `include_router` em `main.py`, +1 entrada de proxy no `vite.config.js`, seletor de produto no `App.jsx` preservando 100% o render ELLO.

## 13. Arquitetura de implementação

**Backend (`backend/app/autotruck/`, isolado):**
- `domain.py` — dataclasses puras (VeiculoAT, EventoAT, SegmentoResultado, BoletoAT, ConsolidadoAT, ResultadoRateioAT, AuditLog).
- `rules.py` — parâmetros (tabela de cotas FIPE, multiplicador especial, faixa estabilização, % churn, % volatilidade, valor fixo terceiros/caminhão).
- `engine.py` — motor puro (sem I/O): segmentação, 75%, cotas FIPE, fórmula, FIFO+postergados, potes fixos, purista, estabilização, alertas, auditoria, invariante.
- `service.py` — orquestra repo + engine + persistência.
- `repo.py` — repositório in-memory/JSON próprio.
- `config.py` — settings próprios (`AUTOTRUCK_JSON_PATH`).
- `gerar_dados.py` — gerador de dados simulados calibrado.
- `backend/app/api/autotruck.py` — router `prefix=/autotruck`.
- `backend/app/schemas/autotruck.py` — schemas Pydantic de saída.

**Frontend:**
- `frontend/src/AutoTruck.jsx` — UI nova (sub-abas: Visão, Segmentos, Eventos, Potes, Boletos, Auditoria).
- `App.jsx` — seletor de produto **ELLO | AutoTruck** (aditivo; ELLO inalterado).
- `vite.config.js` — +1 proxy `/autotruck`.

**Endpoints:**
- `POST /autotruck/calcular` — calcula e persiste (idempotente, `force`).
- `POST /autotruck/replay` — simula sem persistir (painel de simulação).
- `GET /autotruck/{mes_ano_ref}` — consolidado.
- `GET /autotruck/{mes_ano_ref}/segmentos` — cota por segmento + alertas.
- `GET /autotruck/{mes_ano_ref}/eventos` — eventos rateados (FIFO).
- `GET /autotruck/{mes_ano_ref}/potes` — potes fixos (Terceiros, Caminhão).
- `GET /autotruck/{mes_ano_ref}/boletos` — boletos.
- `GET /autotruck/{mes_ano_ref}/auditoria` — log imutável.
