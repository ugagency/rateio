# Folha de apoio — Demonstração Rateio ELLO

Mês de referência usado: 05/2026 (default da tela). O carimbo de mês
é cosmético; os valores vêm dos arquivos. Números abaixo calculados pelo
motor real (app.core.engine), idênticos ao que a tela mostra.

Todos os veículos têm 1 cota. Cota acumulada por categoria: ROUBO_FURTO
R$14, MOTO_FIP R$18, VENTURE_1 R$36, VENTURE_2 R$54.

---

# DEMONSTRAÇÃO 1 — mover o ALVO (troca o arquivo de VEÍCULOS)

Mantenha fixos: eventos_cobre.xlsx e servicos.xlsx. Troque só o veículos.

## 1A) veiculos_completo (100 veículos)

- Linhas lidas: 100 veículos, 2 eventos
- Veículos elegíveis: 100
- Cotas apuradas: 100,00
- ALVO DO MÊS: R$ 2.010,00
  - P1 Roubo/Furto: R$ 1.400,00
  - P2 Moto FIP: R$ 160,00
  - P3 Venture 1: R$ 360,00
  - P4 Venture 2: R$ 90,00
- Eventos alocados: 2 (1 liquidados, 1 parciais)
- Saldo p/ próximo mês: R$ 290,00
- Invariante (Δ alvo vs alocado): R$ 0,00

## 1B) veiculos_reduzido (removidos 10 Roubo/Furto)

- Linhas lidas: 90 veículos, 2 eventos
- Veículos elegíveis: 90
- Cotas apuradas: 90,00
- ALVO DO MÊS: R$ 1.870,00
  - P1 Roubo/Furto: R$ 1.260,00
  - P2 Moto FIP: R$ 160,00
  - P3 Venture 1: R$ 360,00
  - P4 Venture 2: R$ 90,00
- Eventos alocados: 2 (1 liquidados, 1 parciais)
- Saldo p/ próximo mês: R$ 430,00
- Invariante (Δ alvo vs alocado): R$ 0,00

Frase para a reunião: "Removi 10 veículos Roubo/Furto. Cada um paga R$14
no P1, então o Alvo deve cair R$140: de R$ 2.010,00 para R$ 1.870,00."

---

# DEMONSTRAÇÃO 2 — mover o INVARIANTE (troca o arquivo de EVENTOS)

Mantenha fixos: veiculos_completo.xlsx e servicos.xlsx. Troque só o eventos.

## 2A) eventos_cobre (cobre o alvo)

- Linhas lidas: 100 veículos, 2 eventos
- Veículos elegíveis: 100
- Cotas apuradas: 100,00
- ALVO DO MÊS: R$ 2.010,00
  - P1 Roubo/Furto: R$ 1.400,00
  - P2 Moto FIP: R$ 160,00
  - P3 Venture 1: R$ 360,00
  - P4 Venture 2: R$ 90,00
- Eventos alocados: 2 (1 liquidados, 1 parciais)
- Saldo p/ próximo mês: R$ 290,00
- Invariante (Δ alvo vs alocado): R$ 0,00

## 2B) eventos_falta (deletei EV-002, falta cobertura)

- Linhas lidas: 100 veículos, 1 eventos
- Veículos elegíveis: 100
- Cotas apuradas: 100,00
- ALVO DO MÊS: R$ 2.010,00
  - P1 Roubo/Furto: R$ 1.400,00
  - P2 Moto FIP: R$ 160,00
  - P3 Venture 1: R$ 360,00
  - P4 Venture 2: R$ 90,00
- Eventos alocados: 1 (1 liquidados, 0 parciais)
- Saldo p/ próximo mês: R$ 0,00
- Invariante (Δ alvo vs alocado): R$ 510,00

Frase para a reunião: "Deletei o evento EV-002. Agora os eventos não cobrem
o alvo: o Δ sai de R$ 0,00 e acusa exatamente R$ 510,00 de diferença, e os
eventos alocados caem de 2 para 1."
