# ADR-002 — Convenções Canônicas (pós-revisão SDD)

Status: aceito. Data: 2026-05-29.

## Contexto

A revisão SDD da primeira rodada de specs encontrou divergências entre módulos
(status do veículo, forma de RLS, formato de competência, rótulos de segmento).
Esta ADR fixa as convenções únicas que todas as specs devem seguir, para a
cadeia até a BASE e o RATEIO fechar e o aceite por reconciliação ser possível.
Todos os valores de referência foram extraídos do motor aprovado.

## Decisões

### C1. Status do veículo (resolve I-01)

O enum único de `veiculos.status` é: `pendente_vistoria`, `ativo`, `inativo`.

- Veículo nasce `pendente_vistoria`.
- A vistoria finalizada transiciona `pendente_vistoria` para `ativo`. Não
  existe o valor `admitido`. A admissão é o processo; o estado resultante é
  `ativo`.
- O denominador da BASE é veículo com `status = ativo` E situação de boleto da
  competência igual a `baixado`. Status e situação de boleto são eixos
  distintos: um veículo ativo com boleto aberto entra em cotas abertas, não no
  denominador.

### C2. Isolamento multi-tenant por RLS (resolve I-02)

Forma única: claim customizado `associacao_id` no JWT. As policies usam
`auth.jwt() ->> 'associacao_id'`. Proibido subquery em `operadores` dentro de
policy (evita N+1). Vale para todas as tabelas.

### C3. Formato de competência (resolve I-03)

Armazenamento único: coluna `competencia` do tipo `date`, sempre o primeiro dia
do mês (por exemplo 2026-06-01). Entrada de API aceita `AAAA-MM`. Exibição na
UI em `MM/AAAA`. BASE e RATEIO de uma mesma exportação usam a mesma
`competencia`.

### C4. Segmentos e mapeamento de rótulos (resolve I-04)

No banco e na aplicação, o segmento é sempre plural canônico: `LEVES`, `MOTOS`,
`PESADOS`. O envolvimento do evento é `ASSOCIADOS` ou `TERCEIROS`.

Mapeamento para os arquivos do rateio:
- BASE, rótulo de coluna por segmento (singular): LEVES para LEVE, MOTOS para
  MOTO, PESADOS para PESADO.
- RATEIO, marcador de seção na coluna A: `SEGMENTO ENVOLVIMENTO`, gerando os
  seis marcadores: LEVES ASSOCIADOS, LEVES TERCEIROS, MOTOS ASSOCIADOS,
  MOTOS TERCEIROS, PESADOS ASSOCIADOS, PESADOS TERCEIROS.

Origem da classificação de segmento: a mesma do motor (`segmento_por_tipo` em
`rules.py`): MOTOCICLETA para MOTOS; CAMINHAO e SEMI REBOQUE para PESADOS;
demais para LEVES.

### C5. Cota por FIPE, seed de referência (resolve L-01)

A tabela `faixas_cota` deve reproduzir exatamente `cotas_por_fipe` do motor
(`rules.py`). Seed de referência (parametrizável, mas idêntico ao motor por
padrão): cota base 1,0 para FIPE até 10.000; mais 0,5 por faixa de 10.000;
cota especial para FIPE acima de 450.000 com multiplicador 20,0 (sem progressão
linear). Preço de Danos a Terceiros por faixa: NENHUM 0, 50K 20, 100K 30. O
motor é a fonte de verdade; o seed do app espelha esses números.

### C6. Invariante de fechamento (resolve L-05)

O invariante é calculado e devolvido pelo motor aprovado, não pelo app. Em
concreto (`engine.py`): por segmento variável (LEVES e MOTOS), soma-se a
diferença entre alvo e alocado; `invariante_ok` é verdadeiro quando o valor
absoluto dessa soma é menor que 0,01. O harness de reconciliação lê esse campo
do resultado do motor. O app está correto quando o motor, rodando sobre os
arquivos exportados, retorna `invariante_ok` verdadeiro.

### C7. Situação CANCELADO na BASE (resolve L-06)

O motor usa a coluna BAIXADO como denominador e ABERTO como informativo de
inadimplência. CANCELADO é exportado como informativo e não entra no
denominador nem no invariante. A consolidação por segmento ainda registra
cotas canceladas para conferência.

### C8. Bloqueio de galeria na vistoria, alcance no MVP (resolve L-02)

No MVP, a barreira contra foto de galeria é a captura ao vivo pela câmera do
PWA (sem campo de upload de arquivo). Verificação server-side por metadados
fica para fase posterior. Decisão aceita pelo Spec Lead e registrada como
limite conhecido do MVP.
