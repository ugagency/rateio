# Kit de demonstração — Rateio ELLO (reunião)

Objetivo: provar ao vivo que o processamento lê os arquivos de verdade e
não é mocado. Nada aqui toca a publicação atual nem o AutoTruck.

## Arquivos

- `veiculos_completo.xlsx` — 100 veículos (pool base)
- `veiculos_reduzido.xlsx` — 90 veículos (removidos 10 Roubo/Furto)
- `eventos_cobre.xlsx` — eventos que cobrem o alvo (EV-001 + EV-002)
- `eventos_falta.xlsx` — só EV-001, deixa o alvo descoberto
- `servicos.xlsx` — serviços fixos (R$50 por veículo), usado em todos os cenários
- `FOLHA_DE_APOIO.md` — números esperados de cada cenário, para conferir ao vivo
- `gerar_kit_demo.py` — script que regenera tudo (reprodutível)

## Como demonstrar (aba "Rodar Mês")

Demonstração 1 — mover o ALVO (número grande da tela):
1. Suba `veiculos_completo.xlsx` + `eventos_cobre.xlsx` + `servicos.xlsx`. Calcule.
   Alvo esperado: R$ 2.010,00.
2. Troque só o veículos por `veiculos_reduzido.xlsx`. Calcule de novo.
   Alvo esperado: R$ 1.870,00 (caiu R$140 = 10 cotas x R$14 do P1).

Demonstração 2 — mover o INVARIANTE (prova da conta):
1. Suba `veiculos_completo.xlsx` + `eventos_cobre.xlsx` + `servicos.xlsx`. Calcule.
   Δ esperado: R$ 0,00.
2. Troque só o eventos por `eventos_falta.xlsx`. Calcule de novo.
   Δ esperado: R$ 510,00 e eventos alocados caem de 2 para 1.

## Reforço

- No resultado, abra "Detalhes da ingestão": ele mostra a contagem de linhas
  lida de cada arquivo. Abra o xlsx ao lado e confira que bate.
- Deixe um gestor ditar quantos veículos remover do arquivo na hora: como o
  número não foi combinado, mock nenhum acompanharia.

## Regenerar

    backend/.venv/bin/python3 demos/reuniao_ello/gerar_kit_demo.py
