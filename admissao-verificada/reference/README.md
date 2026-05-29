# Reference: exportador e harness (marco M1)

Implementação de referência e oráculo do contrato de exportação. Prova, com um
caso conhecido, que os arquivos BASE e RATEIO gerados servem ao motor aprovado
e fecham o invariante. Espelha o leitor real `backend/app/autotruck/ingestao_partes.py`.

- `exportador.py` (SPEC-007): gera BASE.xlsx e RATEIO.xlsx no layout do motor.
- `harness.py` (SPEC-008): fixture, exporta, valida `detectar_tipo`, confere o
  roundtrip da BASE, compõe e roda o motor, confirma `invariante_ok`.

O exportador do app (TypeScript) deve produzir arquivos compatíveis com o que
estas funções geram. Esta referência é o guardião automático dessa fidelidade.

## Rodar

```
backend/.venv/bin/python admissao-verificada/reference/harness.py
```

Saída esperada: tipos BASE e RATEIO reconhecidos, cotas baixadas idênticas ao
escrito, invariante zero, HARNESS APROVADO. O motor não é alterado; a fronteira
é o arquivo.
