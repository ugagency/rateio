# PRD: Motor de Rateio AVAP

Status: especificação para implementação (MVP), com decisões abertas listadas na seção 12.
Regras vigentes: `docs/REGRAS_RATEIO_AVAP.md` é a fonte única. Em caso de conflito, vale ela.
Data: 01/10/2026.
Isolamento: os motores ELLO (`app/core`) e AutoTruck (`app/autotruck`) **não são alterados**. A AVAP entra como terceira vertical, em módulo próprio, com domínio, engine e dados próprios.

Fontes:

- `docs/RELATORIO_ANALISE_AVAP_modelo_rateio.md`: análise dos dados reais do SGA (base de cotas de 09/2026, fotos de eventos de 28/09 e 30/09).
- `docs/LEVANTAMENTO_AVAP_organizado.md`: regras levantadas na reunião de 30/09/2026.
- LC 213/2025 e Res. CNSP 491/2026 (arts. 69 e 70), como registrado no projeto.

## 1. Objetivo

Automatizar o fechamento mensal do rateio da AVAP:

- ler as exportações do SGA Hinova;
- montar a base de eventos candidatos;
- aplicar as linhas de soma e dedução;
- dividir o total pelo peso das cotas elegíveis;
- emitir a composição do boleto por veículo.

Tudo com foto lacrada, trilha de auditoria e conciliação com diferença zero contra o fechamento feito hoje pela associação. O motor tem que reproduzir o rateio atual antes de qualquer mudança de modelo.

## 2. Diferenças em relação às outras verticais

| Ponto | ELLO | AutoTruck | AVAP |
|---|---|---|---|
| Lógica | valor-alvo por cota; os eventos preenchem os potes até o alvo | custo do mês dividido pelas cotas, por segmento | custo dos eventos selecionados, mais linhas de soma, menos linhas de dedução, dividido pelas cotas |
| Segmentos | 4 categorias | LEVES, MOTOS e PESADOS | **nenhum**: pote único |
| Peso da cota | por categoria | calculado pela FIPE (faixas de R$ 10 mil, +0,5) | **lido do SGA** (degraus de R$ 5 mil, com ajustes) |
| Regra dos 75% | não | sim | **não se aplica** |
| FIFO e postergação | não | sim | **não se aplica** (não há regime de postergação declarado) |
| Faixa de estabilização | o próprio alvo | R$ 30 a 35 por cota | a definir (D5) |
| Terceiros | n/a | pote fixo | fora do rateio (vendido como produto) |
| Linhas extras | não | serviços somados ao boleto | linhas de soma e dedução **dentro** do numerador |

Consequência: a AVAP reaproveita a forma do AutoTruck (numerador de custo dividido por cotas), mas não reaproveita suas regras de segmentação, cota, 75% e FIFO.

## 3. Fórmula

Pote único:

```
                Σ custo dos eventos selecionados
              + Σ linhas de SOMA
              − Σ linhas de DEDUÇÃO
valor_cota = ───────────────────────────────────
                Σ peso das cotas elegíveis
```

Por veículo:

```
rateio_veiculo = peso_cota_veiculo × valor_cota
```

Arredondamento: `valor_cota` é calculado em precisão total. Cada parcela do boleto é arredondada a 2 casas. A diferença de arredondamento é reportada no invariante (seção 10) e nunca redistribuída em silêncio.

Referência de ordem de grandeza (fechamento real de set/2026, planilha `rateio_agosto.xlsx`):

- total a ratear de R$ 1.802.067,92 no mês (agosto: R$ 1.806.046,24);
- 231.556 cotas de veículos ativos;
- R$ 7,78 por cota.

Os valores antigos (R$ 0,74 milhão e R$ 3,18 por cota) vinham do campo `Valor Rateado` do SGA, que não reflete o fechamento, e estão superados.

## 4. Contrato de dados (entradas)

### 4.1 Base de veículos (SGA, relatório de veículos)

Arquivo de referência: `Cotas_ativasAVAP_09_26.xlsx`.

| Coluna SGA | Campo no domínio | Tratamento |
|---|---|---|
| Placa | `placa` | pode vir vazia (69 casos); não é chave única da vida do veículo |
| Cota | `rotulo_cota`, `peso_cota`, `sufixo_cota` | ver 4.1.1 |
| Categoria | `categoria` | PASSEIO, GRUPO ESPECIAL, ALUGUEL, APLICATIVO, OFICIAL; só atributo, não segmenta |
| Tipo Veículo | `tipo_veiculo` | hoje só AUTOMOVEL |
| Valor FIPE Veiculo | `valor_fipe` | pode ser 0 ou vazio (80 casos) |
| Situação Veículo | `situacao_veiculo` | ATIVO, INADIMPLENTE |
| Situação Associado | `situacao_associado` | ATIVO, INADIMPLENTE, PENDENTE, PENDENTE REVISTORIA, PENDENTE ADESÃO |
| Matrícula Associado | `matricula` | chave do associado; um associado pode ter vários veículos |

Particularidades do layout:

- O cabeçalho fica na linha 1.
- O rodapé começa na linha cuja Placa é "Resumo" e traz o total de veículos, o total de cotas (texto no formato `361,530.00`) e o usuário que gerou o arquivo. O rodapé deve ser lido para **conferência**, nunca como dado.
- O leitor deve falhar se a contagem e a soma lidas divergirem do rodapé.

#### 4.1.1 Leitura da cota

O peso é o número entre parênteses no **fim** do rótulo, por exemplo `COTA 6,0 - (25.000,01 A 30.000,00) - VP (6.00)` tem peso 6,0. Regras:

- Usar o peso informado, **nunca recalcular pela FIPE**. Em 2.270 veículos o peso difere de `ceil(FIPE / 5000)`, por ajuste ou por não reenquadramento.
- A regex precisa tolerar as variações reais de escrita: `20.0000,00`, `R$ 210.000,00`, `15.000.01`, `COTA 80.00 -`, `COTA 73,00-`, `COTA 8,0 (35.000,01...` sem hífen.
- Sufixo: `VP`, `DP`, `CP`, `TP` ou vazio, guardado em `sufixo_cota` (significado em aberto, D3).
- `COTA 0,0 - PRODUTOS AVULSOS (0.00)` e `COTA 0.00 (0.00)` têm peso 0.
- Divergência entre FIPE e faixa da cota gera **alerta informativo**, sem efeito no cálculo.

### 4.2 Eventos (SGA, relatório de eventos)

Arquivos de referência: `foto28-09.xlsx` e `foto30-09.xlsx`.

| Coluna SGA | Campo no domínio | Tratamento |
|---|---|---|
| Protocolo | `protocolo` | chave do evento; 8, 9 ou 10 dígitos (o prefixo é o ano) |
| Situacao | `situacao` | FINALIZADO, FINALIZADO SEM RATEIO, VEICULO ENTREGUE, CANCELADO, PENDENTE NF |
| Data Finalizacao | `data_finalizacao` | data |
| Valor Reparo | `valor_reparo` | número |
| Valor Participacao | `valor_participacao` | texto numérico (`"0.00"`) |
| Valor CustoEvento | `custo_evento` | texto numérico; vale `custo = reparo − participação` (validar) |
| Previsao Valor Reparo | `previsao_reparo` | informativo |
| Motivo | `motivo` | COLISAO, V.F.I, FURTO, ROUBO, ROUBO PARCIAL, CONTINUACaO DE PROCESSO, CARRO RESERVA, REPAROS, ALAGAMENTO, PROTECAO DE VIDROS, INCENDIO, FROTA, SOMENTE TERCEIRO |
| Valor Rateado | `estado_rateio`, `valor_rateado` | ver 4.2.1 |
| Data Cadastro Evento | `data_cadastro` | data |
| Cota, Categoria, Modelo | atributos | o rótulo da cota segue a regra 4.1.1 |
| Tipo Veiculo | `tipo_veiculo` | só no layout de 30/09 |
| Tipo Evento | `tipo_evento` | Evento Associado ou Evento Terceiro |
| Nome, Placa | `placa` | só no layout de 28/09; o Nome **não** é carregado (dado pessoal desnecessário) |

Particularidades do layout:

- O cabeçalho fica na linha 1.
- O layout de 30/09 repete um bloco de 14 colunas vazias depois de Tipo Evento, que deve ser ignorado.
- O rodapé começa em "Resumo". Ele traz o número de eventos e de eventos relacionados, além dos totais de reparo, participação, custo, valor a ratear e valor rateado. Os totais aparecem na coluna Situacao. O leitor confere a soma lida contra o "Valor Total Custo Evento".
- O leitor aceita os dois layouts. O layout recomendado para a AVAP é o de 28/09 com a coluna Tipo Veiculo acrescentada.

#### 4.2.1 Estados de Valor Rateado

| Valor na planilha | `estado_rateio` | Significado |
|---|---|---|
| igual ao custo | `RATEADO` | já entrou num fechamento anterior |
| `"0.00"` | `NA_FILA` | candidato do fechamento em curso (a soma confere com o "Valor a Ratear" do rodapé); pode voltar para vazio se for tirado da fila no fechamento |
| vazio | `NAO_RATEADO` | fora da fila do SGA; só entra no fechamento por inclusão manual do operador (ver 5.1) |
| outro valor | `RATEADO_DIVERGENTE` | alerta; não deveria acontecer na AVAP, que não faz rateio parcial |

### 4.3 Lançamentos (linhas de soma e dedução): entrada nova

Catálogo real observado em ago e set/2026 (ver D7 e `REGRAS_RATEIO_AVAP.md` seção 5). Tabela informada pela operação a cada competência:

| Campo | Tipo | Exemplo |
|---|---|---|
| `competencia` | MM/AAAA | 09/2026 |
| `tipo` | SOMA ou DEDUCAO | DEDUCAO |
| `codigo` | texto | SALVADOS, RECUP_INADIMPLENCIA, TELEMEDICINA |
| `descricao` | texto | Salvados vendidos no período |
| `valor` | número maior que 0 | 48.000,00 |
| `documento` | texto opcional | referência do comprovante |

Regras:

- A lista de códigos é **aberta** e configurável. Foram citadas mais de cinco linhas; já conhecemos salvados e recuperação de inadimplentes (dedução) e telemedicina (soma).
- O valor é sempre positivo. O sinal vem do `tipo`.
- As deduções não têm efeito tributário ou contábil: o valor entra cheio.
- Custos de guincho e pátio do salvado **não** são linhas: já estão no custo do evento.

### 4.4 Histórico do rateio: entrada de aceite

Recebido em parte. CORREÇÃO de 10/10/2026: o rateio real de agosto e setembro (`AVAP/rateio_agosto.xlsx`, ver `ANALISE_RATEIO_AGOSTO_SETEMBRO_AVAP.md`) mostrou que o campo `Valor Rateado` do SGA não é a verdade do fechamento. O rateio real de setembro tem 103 eventos (R$ 1.733.393,65), incluindo 6 dos 7 eventos que eu havia dado como retirados; só o furto 2026819916 ficou de fora. A diferença entre as fotos mostra apenas o que o SGA marcou, não o fechamento. O aceite usa a planilha `rateio_agosto.xlsx` (ago e set), com totais de R$ 1.806.046,24 e R$ 1.802.067,92. As linhas de soma e dedução já vêm na planilha, e o denominador está decidido (veículos ativos, D2). O boleto real não separa o rateio dos produtos e não serve de aceite. Serve só para a conciliação (seção 11); não alimenta o cálculo.

## 5. Seleção dos eventos

### 5.1 Candidatos

Um evento é candidato quando atende às quatro condições:

1. `situacao == FINALIZADO`;
2. `tipo_evento == Evento Associado`;
3. `estado_rateio == NA_FILA` (a fila do SGA). O vazio (`NAO_RATEADO`) NÃO é candidato por regra: entra só por decisão INCLUIR do operador, com justificativa. Evidência: no fechamento real de 09/2026, 79 dos 80 eventos da fila de 28/09 entraram (o 80º, o furto 2026819916, foi excluído) mais 24 inclusões manuais de eventos vazios (22 integrais, 1 colisão, 1 continuação);
4. `data_finalizacao <` data do fechamento (corte à meia-noite do dia anterior).

Ficam fora por regra, sem precisar de decisão:

- FINALIZADO SEM RATEIO, CANCELADO, PENDENTE NF, VEICULO ENTREGUE;
- eventos de terceiro;
- eventos já rateados.

### 5.2 Alertas que exigem decisão (o motor não exclui sozinho)

| Código | Condição | Motivo |
|---|---|---|
| A1 | protocolo com 8 ou 9 dígitos, ou prefixo de ano anterior a um parâmetro (default 2023) | outlier citado na reunião |
| A2 | `custo_evento <= 0` | participação lançada antes de ser paga; não deveria estar na base |
| A3 | `valor_participacao == 0` e custo abaixo de um parâmetro (default R$ 500) | padrão estranho citado na reunião |
| A4 | evento sozinho acima de um percentual do numerador (default 10%) | concentração |
| A5 | motivo V.F.I, FURTO ou ROUBO | integral (ver D1) |
| A6 | `data_finalizacao` alterada em relação à foto anterior | reabertura ou ajuste de data |
| A7 | `custo != reparo − participação` | inconsistência do SGA |

O operador marca cada evento com alerta como INCLUIR ou EXCLUIR. Sem marcação, o fechamento não é homologado.

### 5.3 Duplicidade

A chave é o `protocolo`:

- Duplicata **idêntica**: deduplica e registra na auditoria.
- Duplicata com **valores diferentes**: **bloqueia** a homologação até haver decisão manual, porque no SGA isso pode ser recadastro com outro valor ou outra nota fiscal.

### 5.4 Inclusão e exclusão manual

Qualquer inclusão ou exclusão fora da regra 5.1 exige justificativa e entra no log imutável, como no AutoTruck.

### 5.5 Competência

A competência do evento é a do **fechamento em que ele foi rateado** (`mes_rateio`), nunca a data de finalização. O fechamento de setembro levou eventos finalizados em agosto.

## 6. Denominador

- Soma do `peso_cota` dos veículos elegíveis na foto do fechamento.
- Critério de elegibilidade (D2, decidido): situação do **veículo** ATIVO. O parâmetro continua existindo, mas o default é `VEICULO`.
- Ficam sempre fora, com alerta: peso 0, situações PENDENTE (adesão e revistoria) e linhas sem placa e sem FIPE (D4).
- Veículo inadimplente fica fora. A perda entra como linha de soma INADIMPLÊNCIA, e o que for recuperado depois entra como linha de dedução (4.3).

## 7. Regras de valor

| Regra | Especificação |
|---|---|
| Valor do evento | `custo_evento` cheio, sem descontar nada além da participação, que já vem descontada |
| Integral com acordo | entra pelo valor total do evento, mesmo com pagamento parcelado (regra dita, a calibrar em D1) |
| Veículo depreciado | paga o peso cheio da cota; indenização menor não afeta o rateio |
| Ajuste de cota (ex.: remarcado) | já vem refletido no peso do SGA; o motor não aplica fator próprio |
| Salvado | só como linha de DEDUÇÃO no período em que foi vendido |
| Terceiros | fora |

## 8. Fechamento e lacre

| Dia | Etapa |
|---|---|
| D+0 (dia do fechamento) | importar as exportações do SGA; gerar a foto da base e dos eventos com lacre SHA-256 |
| D+0 | montar candidatos, alertas e lançamentos |
| D+1 | decisões do operador sobre os alertas e homologação |
| D+1 e D+2 | emissão do arquivo de cobrança para o SGA |

Máquina de estados: ABERTO, depois HOMOLOGADO, depois EMITIDO, igual ao AutoTruck. Depois de HOMOLOGADO, qualquer alteração exige reabrir com justificativa. A verificação de integridade compara o hash da foto.

Foto incremental: a cada mês entra uma nova exportação de eventos. O motor cruza com o histórico persistido para detectar eventos novos, alterados (A6) e já rateados, e registra o que mudou entre as fotos.

## 9. Saídas

1. **Resumo do fechamento:**
   - numerador por bloco: custo dos eventos selecionados, cada linha de soma, cada linha de dedução;
   - total de cotas elegíveis e `valor_cota`;
   - quantidade de eventos por motivo.
2. **Eventos rateados:** protocolo, motivo, custo, decisão (regra ou manual), alertas.
3. **Eventos não rateados:** com o motivo (fora de regra, excluído manualmente, bloqueado).
4. **Composição do boleto por veículo**, com o split exigido pela Res. 491, art. 70, presente desde o MVP mesmo que alguns componentes sejam 0:

| Componente | Destino | MVP |
|---|---|---|
| Contribuição de rateio = `peso × valor_cota` | grupo | calculado |
| Contribuição de estabilização | grupo | 0 até D5 |
| Taxa de administração | administradora | parâmetro (default 0) |
| Produtos e benefícios (assistência 24h etc.) | associação | parâmetro (default 0) |

5. **Alertas:** A1 a A7, divergências FIPE e cota, linhas descartadas da base.
6. **Log de auditoria** imutável.
7. **Arquivo de cobrança** para importação no SGA (layout a definir com a operação).

## 10. Invariantes

- `Σ rateio_veiculo − numerador` deve ser igual à diferença de arredondamento, que precisa ficar abaixo de R$ 0,01 × número de veículos e ser reportada.
- Soma dos eventos lidos igual ao rodapé do SGA (veículos e eventos).
- `custo = reparo − participação` em todas as linhas (exceção vira alerta A7).
- Nenhum protocolo rateado duas vezes em competências diferentes.

## 11. Aceite

1. **Principal:** reproduzir o histórico do rateio do mês anterior (4.4) com diferença zero:
   - mesmo conjunto de eventos;
   - mesmas linhas;
   - mesmo total;
   - mesmo valor por cota.

   D1 e D2 já estão decididos (ver seção 12). O boleto real traz só o total da mensalidade e não serve de aceite. A ferramenta é uma CLI `python -m tools.reconciliar_avap <histórico.xlsx>`, que retorna código 0 quando aprovado, no padrão do AutoTruck.
2. **Seleção do fechamento de 09/2026 (dados já disponíveis):** rodando o motor sobre a foto de 28/09, a fila tem 80 eventos (R$ 849.115,48). Com as decisões de alerta registradas, a seleção final tem que reproduzir os eventos da aba `Rateio_setembro` (103 eventos, R$ 1.733.393,65). Dos 7 antes tidos como retirados, 6 entram; só o furto 2026819916 (R$ 67.092,44) aparece como EXCLUIR, com a justificativa a obter da AVAP. Mesma conferência para agosto (150 eventos, R$ 1.775.640,36).

## 12. Decisões abertas

| # | Decisão | Default do MVP | O que desbloqueia |
|---|---|---|---|
| D1 | Integrais (V.F.I, furto, roubo): entram por regra? Os dados mostram que quase nunca entraram (13 de 322 V.F.I em 21 meses), mas a reunião diz que entram por inteiro. RESOLVIDA em 10/10/2026: integral é rateada inteira (set: 32 integrais, R$ 1.288.358,60; ago: 19, R$ 647.695,42), e o campo `Valor Rateado` do SGA não serve de seleção. Falta só o critério de corte (39 integrais, R$ 1,88 mi, ficaram fora de ago e set). | candidatas, rateio pelo valor total, alerta A5 para decisão do operador | critério de corte, perguntado à AVAP |
| D2 | Elegibilidade no denominador. RESOLVIDA: conta a situação do **veículo**; só veículo ativo entra; inadimplente fica fora e é compensado pelas linhas de inadimplência e recuperados (levantamento 1.18 e resposta da AVAP, ver análise de ago/set seção 2). R$ 7,78 por cota em set/2026. | `VEICULO` | nada |
| D3 | Sufixos VP, DP, CP, TP | mesmo peso; guardados como atributo | resposta da AVAP |
| D4 | Veículos com peso 0, FIPE 0 ou sem placa | fora do denominador, com alerta | resposta da AVAP |
| D5 | Estabilização: a Res. 491, art. 69, torna obrigatória, mas a AVAP não tem hoje | informativa (média de 3 meses), componente 0 no boleto | definição da Mutualiza e do atuário |
| D6 | Reuso de código do AutoTruck (lacre, máquina de estados, leitura de xlsx) | cópia adaptada dentro de `app/avap/`, mantendo o isolamento; extração para um módulo comum só depois do aceite das três verticais, numa tarefa própria | decisão técnica nossa |
| D7 | Lista completa das linhas de soma e dedução | catálogo observado em ago/set: E-SAUDE, RASTREAMENTO, INADIMPLÊNCIA do mês (soma), recuperados do mês anterior e salvados (deduções). Inadimplência é por veículo. Confirmar fórmula da inadimplência, E-SAUDE x3 em agosto e a linha sem descrição de -R$ 129.253,00 em setembro | resposta da AVAP |
| D8 | Layout do arquivo de cobrança para o SGA | CSV por placa e matrícula com os componentes do split | operação AVAP |

## 12.1 Configuração da demonstração (10/2026)

A tela `/avap` roda com:

- **D2 (denominador):** veículos ativos (`VEICULO`), decidido. R$ 7,78 por cota em 09/2026. A tela ainda mostra os outros critérios lado a lado, só como comparação.
- **D5:** contribuição de estabilização, taxa de administração e produtos em 0 no boleto.
- **D7:** linhas de soma e dedução digitadas pelo operador, com código reconhecido pela descrição.
- **Integrais:** viram alerta A5 e exigem decisão do operador, com justificativa na trilha de auditoria.
- **Placas e matrículas** ficam ocultas por padrão na tela de boletos (demonstração pública).

## 13. Dados de teste

- A pasta `AVAP/` está no `.gitignore` (dados de cliente). **Nenhum arquivo real entra no repositório**, diferente do precedente do AutoTruck.
- Testes automatizados usam um dataset **sintético calibrado** (`app/avap/gerar_dados.py`), versionado, que reproduz os layouts reais, inclusive rodapé, variações de rótulo, os três estados de Valor Rateado, negativos e duplicatas.
- A conciliação com dados reais roda pela CLI, apontando para arquivos fora do git. O resultado vai para `docs/evidencias/` sem dados pessoais.

## 14. Arquitetura

Backend (`backend/app/avap/`, isolado, sem importar `app/core` nem `app/autotruck`):

| Arquivo | Responsabilidade |
|---|---|
| `domain.py` | dataclasses puras: VeiculoAVAP, EventoAVAP, Lancamento, Alerta, DecisaoEvento, BoletoAVAP, ResultadoAVAP, AuditLog |
| `rules.py` | parâmetros: critério de elegibilidade, limites dos alertas, códigos de lançamento, componentes do boleto |
| `ingestao.py` | leitores dos dois layouts de eventos e do relatório de veículos, parser de cota, conferência com o rodapé |
| `selecao.py` | candidatos, alertas, deduplicação, aplicação das decisões |
| `engine.py` | motor puro: numerador, denominador, valor da cota, boletos, invariantes |
| `fechamento.py` | foto com lacre SHA-256, estados, trilha e diferença entre fotos |
| `service.py` | orquestração |
| `repo.py` | persistência JSON própria (`AVAP_JSON_PATH`) |
| `config.py` | settings |
| `gerar_dados.py` | dataset sintético calibrado |

Ferramentas: `backend/tools/reconciliar_avap.py`.
API: `backend/app/api/avap.py` com prefixo `/avap`. Schemas em `backend/app/schemas/avap.py`.

Toques aditivos fora do módulo:

- `main.py`: +1 `include_router`;
- `vite.config.js`: +1 proxy `/avap`;
- `App.jsx`: seletor de produto ELLO, AutoTruck e AVAP, sem mudar o render dos outros dois.

Frontend: `frontend/src/AVAP.jsx`, com as sub-abas Importação, Candidatos e alertas, Lançamentos, Fechamento, Boletos e Auditoria.

### 14.1 Endpoints

| Método | Rota | Função |
|---|---|---|
| POST | `/avap/importar` | recebe as exportações do SGA, valida contra o rodapé e devolve o perfil da importação |
| POST | `/avap/{competencia}/lancamentos` | grava as linhas de soma e dedução |
| GET | `/avap/{competencia}/candidatos` | candidatos e alertas |
| POST | `/avap/{competencia}/decisoes` | decisões do operador (com justificativa) |
| POST | `/avap/{competencia}/simular` | calcula sem persistir |
| POST | `/avap/{competencia}/homologar` | lacra e homologa |
| POST | `/avap/{competencia}/emitir` | gera o arquivo de cobrança |
| GET | `/avap/{competencia}` | resumo |
| GET | `/avap/{competencia}/boletos` | composição por veículo |
| GET | `/avap/{competencia}/auditoria` | log imutável |

## 15. Testes mínimos

1. Parser de cota cobrindo todas as variações de rótulo da seção 4.1.1.
2. Leitura dos dois layouts de eventos, com conferência do rodapé (aprovada e reprovada).
3. Os três estados de Valor Rateado e o caso `RATEADO_DIVERGENTE`.
4. Seleção: cada regra de 5.1 e cada alerta de 5.2.
5. Duplicata idêntica deduplicada; duplicata divergente bloqueando a homologação.
6. Linhas de soma e dedução alterando o numerador com o sinal correto.
7. Os três critérios de elegibilidade de D2.
8. Invariantes da seção 10.
9. Lacre: alterar a foto depois de homologar quebra a verificação.
10. Isolamento: as suítes ELLO e AutoTruck continuam verdes, sem nenhum arquivo delas alterado.

## 16. Fases

| Fase | Entrega | Depende de |
|---|---|---|
| 0 | `ingestao.py` com parser de cota e conferência de rodapé, rodando sobre os arquivos reais (perfil igual ao do relatório) | nada; pode começar já |
| 1 | `selecao.py`, `engine.py` e lançamentos; aceite da seleção de 08/2026 e 09/2026 (planilha real) | lista de linhas (D7), mesmo que parcial |
| 2 | CLI `reconciliar_avap` e aceite principal com diferença zero; parâmetros D1 e D2 fixados | histórico do rateio (4.4) |
| 3 | fechamento lacrado, API e tela AVAP | fase 2 aprovada (setembro aprovado; agosto é só comparação) |
| 4 | estabilização e split completo do boleto | D5 |

## 17. Fora de escopo

- Grupos por perfil de patrimônio (art. 69) e rateio de terceiros por grupo.
- Auditoria de adesão, antifraude e consultas a bureaus.
- Integração direta com a API do SGA. O MVP trabalha com as exportações em xlsx.
- Qualquer mudança no modelo de rateio da AVAP antes do aceite com diferença zero.
