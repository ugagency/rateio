# Aceite Técnico — Motor de Rateio AutoTruck

> **Documento para a AutoTruck.** Prova objetiva de que o motor pega os
> insumos que alimentam a planilha de vocês, roda, e **bate o rateio nos
> centavos** contra os números de vocês.

## A afirmação

> Dado o arquivo **FECHAMENTO** da AutoTruck (o mesmo que hoje alimenta a
> planilha manual), o motor **lê os eventos da aba RATEIO no layout de
> vocês**, executa o cálculo e **reproduz o ANALITICO de vocês com
> diferença de R$ 0,00**.

## A prova (executada sobre o arquivo real entregue por vocês)

Arquivo: `FECHAMENTO__Copia.xlsx` · **284 eventos** lidos da aba RATEIO
(9 seções: LEVES/MOTOS/PESADOS × ASSOCIADO/TERCEIRO × INTEGRAL/PARCIAL).

| Conferência | Declarado (ANALITICO de vocês) | Calculado (nosso engine) | Δ |
|---|---:|---:|---:|
| LEVES — RATEIO (bruto) | 2.616.217,12 | 2.616.217,12 | **0,00** |
| LEVES — integral | 1.834.103,63 | 1.834.103,63 | **0,00** |
| LEVES — parcial | 782.113,49 | 782.113,49 | **0,00** |
| MOTOS — RATEIO (bruto) | 500.182,55 | 500.182,55 | **0,00** |
| MOTOS — integral | 453.544,15 | 453.544,15 | **0,00** |
| MOTOS — parcial | 46.638,40 | 46.638,40 | **0,00** |
| LEVES — terceiros | 756.464,11 | 756.464,11 | **0,00** |
| MOTOS — terceiros | 32.982,25 | 32.982,25 | **0,00** |
| PESADOS — terceiros | 14.000,00 | 14.000,00 | **0,00** |
| Identidades internas do ANALITICO (4) | — | — | **0,00** |

**RESULTADO: APROVADO** — 13/13 linhas com Δ = R$ 0,00.

## Critério de aceite

Nenhuma linha em FALHA, sendo FALHA qualquer **|Δ| > R$ 0,01**. O caminho
de cálculo é o **engine de produção** (`app/autotruck/engine.py`), rodando
sobre os **eventos extraídos do arquivo de vocês** — não há números fixos.

## Como a AutoTruck verifica, com o próprio arquivo mensal

```
cd backend
.venv/bin/python -m tools.reconciliar  /caminho/para/SEU_FECHAMENTO.xlsx
```

Saída: tabela linha a linha (declarado × calculado × Δ × status) no
console **e** uma planilha `RECONCILIACAO_<arquivo>.xlsx`. Código de saída
`0` = APROVADO, `1` = REPROVADO. Basta trocar o arquivo a cada fechamento.

## Garantia permanente (não regride)

A reconciliação contra o arquivo real é um **teste automatizado**
(`tests/test_ingestao_fechamento.py`, fixture `FECHAMENTO_referencia.xlsx`)
dentro da suíte — **42 testes verdes** (5 ELLO + 37 AutoTruck). Qualquer
mudança que quebre a paridade ao centavo falha o build.

## Camadas de evidência (defesa em profundidade)

1. **Arquivo real → engine → ANALITICO deles**: Δ = 0,00 (este documento).
2. **3 cenários distintos** (`simulacoes/SIMULACAO_*.xlsx`) cujas **fórmulas
   nativas do Excel** recomputam tudo dos inputs e batem com o engine
   (`docs/evidencias/EVIDENCIA_conferencia_planilhas.txt`).
3. **Recálculo independente** em Python (3ª via, `verificacao.py`) — testes
   anti-mock asseguram engine == recálculo.
4. **Aderência ao levantamento** ~97% (`RELATORIO_ADERENCIA_AutoTruck.md`).

## Anexos

- `simulacoes/RECONCILIACAO_FECHAMENTO_referencia.xlsx` — esta reconciliação
- `tools/reconciliar.py` — ferramenta de aceite (rode no seu arquivo)
- `docs/APRESENTACAO_AutoTruck.md` — apresentação executiva
- `docs/RELATORIO_ADERENCIA_AutoTruck.md` — aderência detalhada
