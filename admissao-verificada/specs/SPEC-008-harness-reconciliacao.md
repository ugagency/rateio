# SPEC-008 — Harness de Reconciliação

> Oráculo de aceite de ponta a ponta do MVP. Roda o motor aprovado sobre os
> arquivos exportados e confirma o invariante. Segue ADR-002 e SPEC-000.

## 1. Contexto

O critério de sucesso do MVP é que os arquivos gerados pelo app sirvam ao motor
aprovado. O harness automatiza essa prova. Ele não altera o motor; consome-o
como caixa-preta, pelo mesmo caminho que a operação real usaria.

## 2. Requisitos

- Verificar que os arquivos exportados são reconhecidos por `detectar_tipo`.
- Rodar o motor aprovado sobre BASE e RATEIO de uma competência.
- Confirmar que o motor retorna `invariante_ok` verdadeiro (ADR-002 C6).
- Rodar na suíte automatizada.

## 3. Critérios de aceite (Given/When/Then)

- AC-1: Given BASE e RATEIO exportados de uma competência, When o harness chama
  `detectar_tipo` em cada um, Then o tipo retornado é BASE e RATEIO
  respectivamente.
- AC-2: Given os dois arquivos, When o harness roda o motor aprovado
  (`tools/reconciliar.py` ou o serviço de fechamento equivalente), Then o
  processamento conclui sem erro e `invariante_ok` é verdadeiro (valor absoluto
  da soma das diferenças alvo versus alocado por segmento variável menor que
  0,01).
- AC-3: Given um arquivo posto no slot errado, When passa por `validar_slot`,
  Then a validação acusa a troca.

## 4. Fixture determinística

O harness inclui uma competência mínima conhecida (poucos veículos por segmento
com situação de boleto e poucos eventos) construída para fechar com invariante
verdadeiro. Serve de caso dourado de regressão. A fixture é gerada pela própria
esteira do app (cadastro, vistoria, situação, eventos) ou por seed equivalente,
nunca por números chumbados no arquivo.

## 5. Integração com o motor

- O harness localiza o motor aprovado no repositório (`backend`), invoca o
  caminho de reconciliação ou fechamento sobre os arquivos exportados e lê o
  resultado (`detectar_tipo`, `validar_slot`, `invariante_ok`).
- Nenhuma dependência do app é injetada no motor; a fronteira é o arquivo.

## 6. Observabilidade

Saída do harness reporta, por execução: tipo detectado de cada arquivo, cota
por segmento, diferença alvo versus alocado por segmento e o veredito do
invariante.

## 7. Testes e CI

O harness é, ele próprio, um teste de aceite. Roda na suíte (verde quando o
invariante fecha) e bloqueia o build quando a paridade quebra, espelhando a
garantia que o motor já tem para o arquivo real.

## 8. Rollout

Entra junto com a SPEC-007. É o marco M1 (harness verde contra um caso
conhecido) e o marco M4 (fim a fim a partir da esteira de admissão).

## 9. Questões em aberto

- Forma de invocar o motor a partir do ambiente do app (subprocesso Python,
  serviço local ou execução na suíte do backend): definir na implementação,
  sem alterar o motor.
