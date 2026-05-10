# PRD - Motor de Rateio - Plataforma Mutualiza

## Visao Geral
Sistema alternativo ao SGA para calcular rateio mensal de associacao de protecao veicular.

## Pre-processamento
- Data quebra: dia 25 do mes
- Inadimplentes (+5 dias) perdem cobertura
- Execucao: ~dia 27

## Elegibilidade
- Ativo + contrato ate 25
- Funcionarios: NAO entram, NAO geram boleto
- Plano Anual: entra no peso, NAO gera boleto

## Esteira de Risco
P1 Roubo/Furto: R$ 14/cota x TODOS elegiveis
P2 Moto FIP: R$ 4/cota x (todos - so R/F)
P3 Venture 1: R$ 18/cota x (todos - R/F - FIP)
P4 Venture 2: R$ 18/cota x (todos - R/F - FIP - V1)

Valor por cat: R/F=14, FIP=18, V1=36, V2=54

## Alocacao Eventos
- Cronologico ASC -> valor DESC -> ID
- Rateio parcial habilitado
- Evento fatiavel se necessario

## Preocupacoes
- Idempotencia (lock por mes)
- Saldo pendente atualizavel
- Se evts < alvo = sobra pro proximo mes
