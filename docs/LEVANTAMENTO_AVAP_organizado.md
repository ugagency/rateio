# Levantamento AVAP: informações organizadas por tema

Fonte: `AVAP/Levantamento AVAP.pdf`, transcrição automática (22 páginas) de uma reunião presencial com o contato da Mutualiza em 30/09/2026.
Organizado em: 01/10/2026.

Sobre a fonte:

- A transcrição começa com a conversa já em andamento e tem muitos erros de reconhecimento de voz ("roteado", "mateio" e "neteado" no lugar de "rateado"; "Davap" e "VAP" no lugar de AVAP; "ELA" no lugar de ELLO).
- Cada item abaixo está marcado como **afirmado** (dito com clareza na reunião) ou **a confirmar** (trecho truncado, ambíguo ou em conflito com os dados).
- Credenciais de rede ditas durante a reunião e conversas paralelas sem relação com o negócio foram deixadas de fora.

## 1. Regras do rateio AVAP

| # | Regra | Status |
|---|---|---|
| 1.1 | Só entram eventos **totalmente finalizados**. Não existe rateio parcial na AVAP. | afirmado |
| 1.2 | O rateio é uma **foto estática** do dia do fechamento. Não entra nota fiscal nova durante o processo. | afirmado |
| 1.3 | Corte: entra o que foi finalizado **até a meia-noite do dia anterior** ao fechamento. Evento aberto ontem ainda passa por orçamento e não entra. | afirmado |
| 1.4 | O rateio de setembro foi feito em 30/09; os boletos são lançados nos dias seguintes. | afirmado |
| 1.5 | Indenização integral com acordo assinado é **rateada por inteiro**, mesmo que o pagamento ao associado seja parcelado ("por força do sistema"). | afirmado, mas em conflito com os dados (ver seção 9) |
| 1.6 | O rateio não tem caráter de competência contábil. É um registro da despesa do período. | afirmado |
| 1.7 | **Sem categoria e sem classificação de risco.** O valor é dividido só por cota. | afirmado |
| 1.8 | Cota por faixa de FIPE: carro de R$ 20 mil tem 4 cotas, de R$ 100 mil tem 20 cotas (1 cota a cada R$ 5 mil). | afirmado, e os dados confirmam |
| 1.9 | Veículo depreciado (ex.: com sinistro anterior) paga a cota cheia, mas recebe indenização menor. A diferença fica como benefício para a associação. | afirmado |
| 1.10 | Existem **ajustes de cota** por motivo. Veículo remarcado é um dos casos, possivelmente com fator 0,9. São casos raros. | a confirmar (trecho truncado) |
| 1.11 | **Salvados vendidos** no período entram como **linha de dedução** do rateio. Não entram como participação. | afirmado |
| 1.12 | **Recuperação de inadimplentes** (quem pagou atrasado o mês anterior) entra como **linha de dedução**. | afirmado |
| 1.13 | Benefícios como **telemedicina** entram como **linha de soma** (cerca de R$ 15 a 20 mil). O associado não paga à parte. | afirmado |
| 1.14 | Ao todo, há **mais de cinco linhas** de soma ou dedução separadas dos protocolos. | afirmado (lista completa pendente) |
| 1.15 | Custos de guincho e pátio do salvado ficam **dentro do custo do evento**. Não têm linha própria. | afirmado |
| 1.16 | **Terceiros não são rateados** na AVAP, porque são vendidos como produto. | afirmado |
| 1.17 | Deduções não têm efeito contábil ou tributário: o valor entra cheio. | afirmado |
| 1.18 | Quem entra no denominador: o veículo ativo. Pendente de adesão e pendente de revistoria **não entram**. Sobre os inadimplentes, a fala se contradiz ("não entra"... "entra"). | a confirmar |

Para a AVAP, o salvado não é fonte de lucro: o objetivo é se livrar do veículo e regularizá-lo. O comprador do salvado muitas vezes retira o carro direto da oficina.

### 1.1 Critério para montar a base a ratear (afirmado)

Partir de todos os eventos finalizados no período e então:

1. Tirar os eventos de terceiro (coluna Tipo Evento).
2. Tirar os eventos já rateados. Ficam os que têm `Valor Rateado` **vazio ou zero**.
3. O que sobra são os finalizados não rateados, que são os candidatos ao rateio.
4. Excluir os outliers: protocolos muito antigos (2012, 2014) ou com padrão estranho, eventos finalizados sem participação e com custo baixo, eventos cancelados que ficaram como finalizados.

O histórico do rateio do mês anterior, prometido, vai servir de parâmetro: nele não aparece, por exemplo, protocolo de 2024 nem protocolo sem participação.

### 1.2 Diferença em relação à ELLO (afirmado)

- **ELLO:** a operadora escolhe eventos até completar um valor-alvo do mês. Precisamos saber qual é esse valor a cada mês.
- **AVAP:** repassa o custo dos eventos escolhidos, com linhas de soma e dedução.

As duas fazem escolha de eventos. O que muda é o critério de parada.

## 2. Extração de dados do SGA

| # | Ponto | Status |
|---|---|---|
| 2.1 | O SGA não tem um botão "eventos não rateados". O filtro precisa ser montado na mão (finalizados, sem terceiro, com NF etc.). | afirmado |
| 2.2 | O cálculo do rateio não é feito dentro do SGA. O sistema só registra a escolha dos eventos e dos valores. | afirmado |
| 2.3 | Proposta: **salvar a consulta-modelo** e pedir a mesma exportação para cada associação nova. A maioria usa o mesmo SGA (Hinova). | afirmado |
| 2.4 | A base vai ser **incremental**: todo mês vem uma nova foto, os eventos repetidos são eliminados, e em cerca de seis meses teremos todos os eventos a ratear. | afirmado |
| 2.5 | A situação que vale é a do **associado**. A base de veículos foi exportada com matrícula e placa para fazer o cruzamento. | afirmado |
| 2.6 | Um associado pode ter vários veículos e receber um boleto único ou vários (filha, ex-cônjuge). O normal é boleto único. | afirmado |
| 2.7 | **A placa não serve como chave da vida do veículo.** Um veículo indenizado pode voltar com outro associado e outro ID de veículo, mantendo a mesma placa. | afirmado |
| 2.8 | O Renave guarda a vida completa do veículo (entradas e saídas, tempo parado em loja). É útil para medir exposição ao risco. | afirmado |
| 2.9 | Todos os campos de data são relevantes para cruzamentos ao longo do tempo (data do BO, ocorrência, chegada de peça, validação, contrato do veículo). | afirmado |
| 2.10 | A "data do contrato do veículo" é a primeira entrada na associação. Saídas e retornos exigem consultar o histórico. | afirmado |
| 2.11 | O contato da Mutualiza tem um robô em Python que entra no SGA e baixa os documentos de associados e eventos, para auditoria por amostra (testes com 40 e com 100). | afirmado |
| 2.12 | O SGA é pouco confiável: permite exportar protocolos duplicados com valores diferentes. | afirmado |

## 3. Marco regulatório, como foi lido na reunião

Os pontos abaixo foram lidos em voz alta da resolução da SUSEP (Res. CNSP 491/2026, que regulamenta a LC 213/2025). A transcrição embaralha o texto. Antes de usar em material formal, conferir no texto oficial.

| # | Ponto | Status |
|---|---|---|
| 3.1 | O **grupo** é definido pela administradora, por critério de **patrimônio** (o bem), nunca pelo perfil da pessoa. | afirmado |
| 3.2 | Três caixas separados: grupo, associação e administradora. A administradora gere o dinheiro do grupo, mas o dinheiro não é dela. | afirmado |
| 3.3 | A administradora responde à SUSEP. A associação defende os interesses do grupo diante da administradora. | afirmado |
| 3.4 | Art. 69: a contribuição de rateio é calculada pela administradora, com metodologia atuarial. | a confirmar no texto |
| 3.5 | Art. 69: é **obrigatório** instituir uma **contribuição mensal de estabilização do rateio**, prevista no contrato de participação. | a confirmar no texto |
| 3.6 | Art. 69: o montante a ratear considera as indenizações pagas, a variação das provisões, a variação de ativos do grupo, a dedução de salvados, a dedução das contribuições arrecadadas e **"outras receitas e despesas do grupo previstas no contrato de participação"**. Essa última é a porta para as linhas extras. | a confirmar no texto |
| 3.7 | O período de rateio tem um limite de cerca de 3 meses e deve estar no contrato. | a confirmar (trecho truncado) |
| 3.8 | Art. 70: a contribuição se divide em taxa de administração (vai para a administradora), contribuição de rateio e contribuição de estabilização (as duas vão para o grupo). | a confirmar no texto |
| 3.9 | Produtos fora da resolução (assistência 24h e outros benefícios) podem ser um quarto componente, pago direto à associação. Hoje esses produtos ficam escondidos dentro da mensalidade. | afirmado como proposta |
| 3.10 | A administradora só pode remunerar a associação por apoio a sinistros e a adesões. Se o dinheiro passar pela administradora, é tributado. Precisa de planejamento tributário. | afirmado como risco |
| 3.11 | Terceiros podem passar a ser rateados num grupo específico (ex.: motoristas de aplicativo), se o contrato de participação desse grupo previr. | afirmado como possibilidade |

Os pontos 3.5 e 3.8 batem com o que já temos registrado sobre a resolução: a cobrança precisa discriminar taxa de administração, rateio e fundo de estabilização.

### 3.1 Desenho de grupos (afirmado)

- Agrupar todo o risco alto num só grupo (ex.: aplicativo, motos abaixo de 160 cc com 3 a 4 anos) faz o rateio explodir. Um exemplo dito: 50 motos roubadas num mês, a R$ 20 mil cada, num grupo de mil motos. Em três meses o grupo acaba e fica a dívida.
- A administradora pode **fechar um grupo** para novas entradas quando ele estiver cheio.
- Os grupos precisam ser equilibrados, com quem tem menos risco ajudando a pagar o risco dos outros.
- Antes de agrupar, é preciso entender a base: análise exploratória, distribuições e clusterização. O resultado tem que ser explicável a partir dos dados.
- A AVAP é considerada organizada e foi a primeira associação analisada. Exemplo em estudo: quantos eventos envolvem um motorista que não é o dono do carro.

## 4. Modelo de negócio da Mutualiza

| # | Ponto | Status |
|---|---|---|
| 4.1 | A AVAP está garantida dentro da Mutualiza. Outras associações estão entrando. | afirmado |
| 4.2 | Proposta comercial: a associação entra como **cotista** da administradora e não paga por placa. Só o associado final paga a taxa de administração. | afirmado |
| 4.3 | Esse arranjo deve ficar **reservado**, sem divulgação. | afirmado |
| 4.4 | **Risco regulatório:** pelo que já levantamos da Res. 491, a associação gerida **não pode ter participação na administradora** (vedação de partes relacionadas). O modelo cotista precisa de parecer jurídico. | a confirmar com o jurídico |
| 4.5 | A cadeia de fornecimento traz outras oportunidades: consultoria, compra de peças, destino dos cascos e salvados. | afirmado |
| 4.6 | Fechar o rateio com uma associação que esteja fora da Mutualiza é improvável. Com outra administradora é possível. A Mutualiza funciona como posicionamento ("organizados, com solução de rateio"). | afirmado |
| 4.7 | A administradora quer ter **base de dados própria** (data lake), sob seu controle. Houve oferta de apoio em arquitetura de dados (data warehouse, fatos e dimensões). | afirmado |

## 5. Adesão, eventos, fraude e auditoria

### 5.1 Foco da administradora (afirmado)

São três processos principais: **adesão, rateio e eventos**. Depois que a associação entra na administradora, a responsabilidade pela fraude passa a ser da administradora.

### 5.2 Ferramenta de auditoria por documentos (afirmado)

O contato da Mutualiza usa uma ferramenta de auditoria vinda da prática de SOX. Ela cruza os documentos (com OCR) com os dados do sistema e gera um papel de trabalho com as exceções marcadas. O produto final vai ter outro nome. Itens que ela checa na adesão:

- ficha de adesão assinada e documentos obrigatórios;
- validade da CNH e do CRLV na data da adesão;
- se os dados do veículo batem com o laudo de vistoria e o chassi;
- depreciação e background check;
- se o valor FIPE protegido cabe na faixa de cota;
- situação do gravame;
- se a data de adesão é coerente com a assinatura e o pagamento.

Num teste, ela detectou um erro de amostra: dois veículos do mesmo modelo, mesmo ano e placas parecidas, do mesmo associado, com os dados trocados.

Na parte de eventos, uma primeira lista passou de 400 quesitos (integridade, totalidade, temporalidade, tempestividade). A ideia é dividir os eventos numa árvore por tipo: colisão simples, roubo e furto, roubo localizado (recuperar, reparar e devolver), perda total direta (ex.: alagamento), perda total vinda de colisão, e acordo (com terceiro ou com oficina sem vínculo).

### 5.3 Validação de documentos (afirmado)

- É preciso checar se a CNH é **válida** (data) e se é **íntegra** (não adulterada). A segunda parte ainda não existe. Exemplo de técnica: fonte e espaçamento de impressão mudam conforme o ano de emissão.
- Comprovante de endereço importa pouco no mutualismo, porque o que conta é o bem.
- O documento único (CNH, CRLV) facilita a checagem.

### 5.4 Consultas de veículo e de pessoa (afirmado)

- Por placa: remarcação de chassi, histórico de roubo e furto, recuperação, leilão, restrição judicial, financiamento e parcelas restantes.
- **Risco do financiamento:** se a dívida for maior que o valor do veículo, a associação paga a indenização mas não consegue transferir o salvado sem quitar o banco.
- Fornecedores citados: PH3A (produtos DataTag, DataBusca, DataFraud, Dossiê); Check Pro (bom preço por volume); um fornecedor de base de leilão (a maior do país, mas caro).
- A administradora deve **unificar a contratação** dessas consultas para ganhar preço por volume.
- A SUSEP tem dados de seguradoras (ex.: se o CPF tem outro seguro) que ainda ninguém está explorando.

### 5.5 Casos de fraude relatados (afirmado)

- Associado compra a peça original, manda a nota fiscal, depois cancela a nota e devolve a peça.
- Associada que atrasava todo mês e refazia a revistoria: numa delas colocou a placa em outro carro igual. O BO tinha data anterior à revistoria, quando ela estava sem cobertura. Foi descoberta comparando as fotos dos meses anteriores.
- Vendedor que deixou de vender para a associação e depois colocou nela um carro já sinistrado.
- Veículo deixado de propósito em ponto de alagamento conhecido.

Lições:

- **Golpe** (com lojista ou alguém de dentro) é diferente de fraude.
- Fraudadores organizados trocam técnicas em grupo, e os casos sobem de repente (ex.: de 8 para 250 por semana).
- **Um falso positivo é pior do que deixar passar.** Ele queima o nome da empresa.
- A entrevista com o associado continua sendo a ferramenta mais eficaz.

## 6. Ação comercial em feira (stand da Mutualiza)

| # | Ponto | Status |
|---|---|---|
| 6.1 | Demonstração guiada no stand, num totem ou tablet, com pessoas treinadas. | afirmado |
| 6.2 | Fazer 3 ou 4 perguntas ao visitante (número de placas, ticket médio, custo mensal de eventos) e completar o resto com estatística. Mostrar o rateio simulado (ex.: "o seu deve dar uns R$ 800 mil por mês"), inclusive com o valor represado. | afirmado |
| 6.3 | Ter uma distribuição padrão da carteira (ex.: 20% acima de R$ 100 mil, mais de 50% entre R$ 50 e 70 mil) para gerar a base simulada na hora. | afirmado |
| 6.4 | Permitir incluir linhas de despesa próprias (porta do art. 69). | afirmado |
| 6.5 | QR code para o visitante abrir no celular. A pessoa não vai querer passar cinco minutos preenchendo. | afirmado |
| 6.6 | Vender a plataforma e a Mutualiza juntas. | afirmado |
| 6.7 | Equipe: a nossa equipe técnica, um desenvolvedor de apoio (para explicar quando um número não bater) e um integrante comercial da Mutualiza com boa abordagem. | afirmado |
| 6.8 | Opção visual: alugar um painel de LED modular, espelhado no tablet. Há um contato que aluga. Custo a levantar. | afirmado |
| 6.9 | Levantar os custos e ter a demonstração pronta em 2 a 3 dias. | afirmado |

## 7. Pendências da ELLO esclarecidas na mesma reunião

| # | Ponto | Status |
|---|---|---|
| 7.1 | Os 100 protocolos duplicados não têm justificativa conhecida. Hipótese: um evento rateado parcialmente é cadastrado de novo com outro valor ou outra NF. O contato vai consultar o histórico no sistema. | a confirmar |
| 7.2 | Os valores negativos são participação lançada antes de ser paga (o SGA registra o crédito sem o débito). Esses eventos não deveriam estar na base. A pergunta passa a ser por que entraram na exportação. | afirmado |
| 7.3 | A versão nova do SGA usada pela ELLO **permite rateio parcial**. Exemplo: um evento de R$ 20.696 com R$ 2.212 a ratear, porque o restante já tinha sido rateado. | afirmado |
| 7.4 | O "valor a ratear" do arquivo da ELLO talvez não desconte a participação, o que sugere outro tratamento depois. | a confirmar |
| 7.5 | A ELLO escolhe eventos até completar o valor-alvo do mês. Precisamos receber esse valor a cada mês. | afirmado |
| 7.6 | Não temos acesso ao SGA da ELLO para reproduzir a extração. Na AVAP o acesso é total. | afirmado |
| 7.7 | O contato vai buscar o histórico de rateio e a base de veículos da ELLO. | afirmado |

## 8. O que foi prometido e ainda não chegou

1. **Histórico do rateio do mês anterior da AVAP** (eventos escolhidos, valor rateado e total, com as linhas de soma e dedução). É a peça mais importante: serve de aceite para o motor.
2. Os valores das linhas de dedução (salvados, recuperação de inadimplentes) e de soma (telemedicina e outras), para completar a simulação.
3. Um modelo genérico de contrato de participação, para comparar com o que a resolução exige.
4. A lista de quesitos da ferramenta de auditoria de adesão.
5. O histórico de rateio e a base de veículos da ELLO.
6. A explicação dos protocolos duplicados da ELLO, com prints do sistema.

## 9. Impacto na análise anterior dos dados da AVAP

Referência: `docs/RELATORIO_ANALISE_AVAP_modelo_rateio.md`.

### 9.1 Correção feita

No relatório anterior, `Valor Rateado` vazio estava descrito como "evento que não entrou no rateio". Pelo critério da reunião (seção 1.1), vazio ou zero significa **ainda não rateado**, ou seja, candidato. O relatório foi corrigido.

### 9.2 Tensão (explicada em 10/10/2026)

> CORREÇÃO de 10/10/2026: o rateio real de agosto e setembro (`AVAP/rateio_agosto.xlsx`, ver `ANALISE_RATEIO_AGOSTO_SETEMBRO_AVAP.md`) mostrou que o campo `Valor Rateado` do SGA não é a verdade do fechamento. O rateio real de setembro tem 103 eventos (R$ 1.733.393,65), incluindo 6 dos 7 eventos que eu havia dado como retirados; só o furto 2026819916 ficou de fora. A diferença entre as fotos mostra apenas o que o SGA marcou, não o fechamento. A tensão dos 712 finalizados vazios se explica em boa parte assim: integrais entram no rateio real mesmo com o campo vazio no SGA. Inadimplência é por veículo, fora do rateio, compensada pelas linhas de inadimplência e recuperados.

Texto original:

O critério da reunião não fecha com os números:

- Há 712 eventos FINALIZADO com `Valor Rateado` vazio, somando R$ 23,3 milhões. O rateio de verdade fica em torno de R$ 0,74 milhão por mês.
- Na reunião foi dito que a integral com acordo é rateada por inteiro. Mesmo assim, só 13 de 322 V.F.I e 2 de 156 furtos têm `Valor Rateado` em 21 meses.
- Também foi dito que alguns eventos "não foram escolhidos ainda", o que confirma que existe uma escolha além do simples repasse.

Explicações possíveis: as integrais seguem outro caminho; existe um grande volume represado; ou a escolha deixa de fora eventos que o critério incluiria. O histórico do rateio (item 8.1) deve resolver isso.

### 9.3 Situação das 12 perguntas do relatório

| Pergunta | Situação |
|---|---|
| 1. Integrais | mais precisa: o que foi dito contradiz os dados (ver 9.2) |
| 2. Colisões e terceiros sem rateio | terceiros respondido (são produto, não se rateiam); colisões sem rateio continuam abertas |
| 3. Denominador | em parte: pendentes não entram; inadimplente ficou contraditório |
| 4. Valor por cota cobrado | aguardando o histórico de rateio |
| 5. Sufixos VP, DP, CP, TP | em aberto; podem ter relação com os ajustes de cota da regra 1.10 |
| 6. Reenquadramento de cota | em parte: existem ajustes por motivo (remarcado), raros |
| 7. Categorias | respondido: não há categoria, só cota |
| 8. Competência e corte | respondido: corte à meia-noite do dia anterior ao fechamento |
| 9. Eventos relacionados | em aberto |
| 10. Negativos | explicação dada no caso da ELLO (participação lançada antes de ser paga); vale confirmar para a AVAP |
| 11. Layout | em aberto |
| 12. Modelo novo | em parte: a resolução obriga estabilização e permite linhas extras e grupos com terceiro rateado |

### 9.4 Diferenças em relação ao motor AutoTruck

| Regra AVAP | Motor AutoTruck hoje |
|---|---|
| Custo dos eventos escolhidos dividido pelas cotas | já faz |
| Dedução de salvados vendidos | já faz (abate o salvado liquidado) |
| Dedução da recuperação de inadimplentes | **não faz**, precisa de linha nova |
| Linhas de soma (telemedicina e outras) | **não faz**, precisa de linha nova |
| Cota a cada R$ 5 mil, sem categoria | o motor usa faixas de R$ 10 mil e segmenta leves e motos; precisa parametrizar |
| Ajuste de cota por motivo (remarcado) | **não faz**; ler o peso informado pelo SGA |
| Terceiros fora do rateio | já faz (terceiro como produto) |
| Contribuição de estabilização obrigatória (art. 69) | já existe a estabilização trimestral; falta separá-la na cobrança |
