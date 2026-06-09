# Folha de apoio — Demonstracao AutoTruck (Modelo Ello retreinado)

Mes de referencia: use 05/2026 ou outro de sua preferencia. O carimbo de mes e
cosmetico. Os valores vem dos arquivos. Numeros abaixo calculados pelo motor
real (app.autotruck.engine), identicos ao que a tela mostra.

Conceitos:

- Cota: custo a ratear do segmento dividido pelas cotas adimplentes (BAIXADO)
  daquele segmento. Aplica-se a LEVES e MOTOS.
- Custo a ratear (bruto): soma dos eventos de associados (integral mais parcial)
  do segmento no mes.
- Terceiros: rastreados em separado. Nao abatem a cota dos associados.
- Invariante de auditoria: diferenca entre o total a ratear e o total alocado.
  Deve ser sempre R$ 0,00.

---

# CENARIO BASE

Arquivos: BASE_completa.xlsx, RATEIO_completo.xlsx, PRODUTOS.xlsx.

- Cotas adimplentes: LEVES 1.000, MOTOS 2.000, PESADOS 300
- Eventos lidos: 7
- Custo a ratear LEVES: R$ 60.000,00
- Custo a ratear MOTOS: R$ 40.000,00
- Cota LEVES: R$ 60,00
- Cota MOTOS: R$ 20,00
- Terceiros LEVES (nao abate): R$ 5.000,00
- Terceiros MOTOS (nao abate): R$ 6.000,00
- Eventos alocados: 7
- Invariante (Delta): R$ 0,00

---

# DEMONSTRACAO 1 — mover a COTA (troca o arquivo de BASE)

Mantenha fixos: RATEIO_completo.xlsx e PRODUTOS.xlsx. Troque so a BASE.

## 1A) BASE_completa (MOTOS 2.000 adimplentes)

- Custo a ratear MOTOS: R$ 40.000,00
- Cota MOTOS: R$ 20,00
- Cota LEVES: R$ 60,00

## 1B) BASE_reduzida (MOTOS 1.000 adimplentes)

- Custo a ratear MOTOS: R$ 40.000,00 (inalterado)
- Cota MOTOS: R$ 40,00
- Cota LEVES: R$ 60,00 (inalterado)

Frase para a reuniao: "Reduzi os motociclistas adimplentes de 2.000 para 1.000.
O custo do mes e o mesmo, entao cada cota de MOTOS passa a pagar o dobro, de
R$ 20,00 para R$ 40,00. A cota de LEVES nao muda, porque nao mexi nela."

---

# DEMONSTRACAO 2 — mover o CUSTO A RATEAR (troca o arquivo de RATEIO)

Mantenha fixos: BASE_completa.xlsx e PRODUTOS.xlsx. Troque so o RATEIO.

## 2A) RATEIO_completo (7 eventos)

- Eventos lidos: 7
- Custo a ratear MOTOS: R$ 40.000,00
- Cota MOTOS: R$ 20,00
- Eventos alocados: 7

## 2B) RATEIO_reduzido (removido o evento parcial de MOTOS, R$ 10.000,00)

- Eventos lidos: 6
- Custo a ratear MOTOS: R$ 30.000,00
- Cota MOTOS: R$ 15,00
- Eventos alocados: 6

Frase para a reuniao: "Removi um evento de MOTOS no valor de R$ 10.000,00. O
custo a ratear de MOTOS cai de R$ 40.000,00 para R$ 30.000,00, a cota cai de
R$ 20,00 para R$ 15,00, e os eventos lidos caem de 7 para 6."

---

# Resumo dos numeros (referencia rapida)

Cenario                              | Cota MOTOS | Cota LEVES | Custo MOTOS  | Eventos
BASE_completa + RATEIO_completo      | R$ 20,00   | R$ 60,00   | R$ 40.000,00 | 7
BASE_reduzida + RATEIO_completo      | R$ 40,00   | R$ 60,00   | R$ 40.000,00 | 7
BASE_completa + RATEIO_reduzido      | R$ 15,00   | R$ 60,00   | R$ 30.000,00 | 6

Em todos os cenarios o Invariante de auditoria fecha em R$ 0,00.
