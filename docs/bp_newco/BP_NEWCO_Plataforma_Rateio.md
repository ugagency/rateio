# Plano de Negócios: Plataforma de Rateio e Gestão de Associações

## Base para decisão de investimento na NEWCO (Mutualiza 50% / RATEIOSA 50%)

Versão 1.0 · uso interno, para discussão com o conselho diretor da Mutualiza

---

## 1. Sumário executivo

Este documento descreve o plano para transformar o motor de rateio já validado e a esteira de admissão já especificada em um produto de produção: uma plataforma que cobre o ciclo completo de uma associação de proteção patrimonial mutualista, da captação e admissão do associado até a emissão do boleto registrado.

O ponto de partida não é uma ideia em papel. Existem hoje, testados e funcionando:

- Um motor de cálculo de rateio com 53 testes automatizados, validado contra a base real de uma associação (AutoTruck), com diferença zero entre o valor alvo e o valor alocado (invariante de fechamento).
- Uma esteira de admissão verificada (cadastro, vistoria, situação de boleto, lançamento de eventos do mês) especificada por Spec Driven Development, com banco de dados modelado, políticas de segurança por associação e um exportador que gera os arquivos de entrada do motor de rateio com prova de equivalência (paridade entre a implementação de referência em Python e a implementação em produção em TypeScript).
- Uma versão web funcional do motor (API e painel), usada em demonstração e homologação técnica.

O que falta para produto é: (a) ligar a admissão à origem real dos dados de cada associação, hoje concentrados no SGA da Hinova; (b) gerar e registrar os boletos em um meio de pagamento com liquidação bancária, hoje proposto como iugu; (c) operar em múltiplas associações ao mesmo tempo, com isolamento de dados e trilha de auditoria; (d) atender às exigências regulatórias da Lei Complementar 213/2025 e da Resolução CNSP 491/2026, que incluem certificação atuarial dos métodos de rateio e contabilidade regulatória segregada.

O achado financeiro mais importante deste plano: a tarifa de meio de pagamento (boleto registrado ou PIX) por veículo, cobrada pelo provedor de pagamento, é da ordem de R$ 1,50 a R$ 2,50 por título. Em escala (150 a 300 mil placas por mês), isso representa entre R$ 200 mil e R$ 470 mil por mês em tarifas de terceiros, um valor muito maior do que a receita da NEWCO nos cenários de preço por placa discutidos até aqui (R$ 0,10 a R$ 0,30). Esse custo não pode ser absorvido pela NEWCO: ele precisa ser repassado ao boleto do associado, como qualquer sistema de cobrança faz hoje. Com esse repasse, o caixa consumido ao longo de 24 meses cai de uma faixa de R$ 5,8 a R$ 6,4 milhões para uma faixa de R$ 400 a 790 mil, dependendo do preço por placa escolhido; nos cenários de R$ 0,20 e R$ 0,30 esse valor corresponde ao investimento necessário até o ponto de equilíbrio operacional, que é de fato atingido dentro do horizonte modelado, enquanto no cenário de R$ 0,10 o equilíbrio não é atingido em 24 meses e o número representa o caixa negativo acumulado no período, não um investimento até um marco alcançado. A seção 10 detalha essa diferença entre os três cenários. Este é o número central que este documento existe para sustentar diante do conselho.

Recomendação central: preço por placa na faixa de R$ 0,25 a R$ 0,30 (ou uma tabela escalonada por volume), tarifa de meio de pagamento sempre repassada ao boleto do associado, e um investimento inicial da ordem de R$ 400 a R$ 800 mil distribuído ao longo de 24 meses, cobrindo equipe, infraestrutura e capital de giro até o ponto de equilíbrio operacional.

---

## 2. Contexto

A Mutualiza é a administradora estruturada para atender à Lei Complementar 213/2025, que trouxe as associações de proteção patrimonial mutualista para dentro de um regime regulado pela SUSEP. Sob a Mutualiza operam hoje três associações: AutoTruck, ELLO e AVAP.

O motor de rateio foi apresentado e validado tecnicamente junto à associação AutoTruck, com reprodução exata (diferença zero) do fechamento mensal já operado hoje pelo sistema atual. Essa validação abriu a conversa de sociedade entre as partes: em vez de uma relação de fornecedor e cliente, as partes concordaram em constituir uma empresa conjunta (a NEWCO, referida aqui como Mutualiza e RATEIOSA), com participação de 50% para cada lado, para levar o produto a mercado.

Até este ponto, as conversas trataram de duas frentes que precisam se manter separadas: a validação técnica do rateio (concluída) e a estruturação da sociedade e do produto (em aberto). Este documento assume a segunda frente e detalha o que é necessário para que a NEWCO opere uma plataforma completa, não apenas o motor de rateio isolado.

Um documento de custo mais restrito, apresentado em julho de 2026, estimou R$ 31 mil de implantação em dois meses e R$ 8 mil por mês de sustentação, para produtizar o motor de rateio no escopo então discutido (uma associação, 75 mil placas, sem captação, sem integração de SGA, sem integração de meio de pagamento próprio). Este plano de negócios amplia esse escopo para o que o conselho está agora decidindo investir: a plataforma completa, multi-associação, com captação, integração de dados e emissão de boletos. Os números aqui são maiores porque o escopo é maior; a seção 10.4 normaliza os dois valores no mesmo horizonte de tempo para tornar essa diferença comparável.

---

## 3. Inventário de ativos existentes

Esta seção documenta o que já existe, porque é a base que justifica a participação de 50% da RATEIOSA na NEWCO sem aporte financeiro em dinheiro: o aporte já foi feito em trabalho e propriedade intelectual.

### 3.1 Motor de rateio (produção)

- Lógica de cálculo (esteira de risco em degraus cumulativos, alocação cronológica de eventos, rateio parcial, idempotência por competência) implementada e testada.
- 53 testes automatizados cobrindo o motor, a ingestão de dados reais em planilha, o fechamento mensal e a paridade entre a exportação de referência e a exportação em produção.
- API (FastAPI) e painel web (React) funcionais, usados em demonstração.
- Validado contra a base real da associação AutoTruck: diferença zero entre valor alvo e valor alocado, reprodução do fechamento oficial do mês de referência.

### 3.2 Esteira de admissão verificada

- Especificação por Spec Driven Development: oito especificações de módulo (autenticação e associação, associado, veículo e cota, admissão e vistoria, situação de boleto, eventos do mês, exportador, harness de reconciliação), mais três decisões de arquitetura registradas.
- Modelagem de dados em PostgreSQL (Supabase), com isolamento por associação via política de segurança em nível de linha (RLS) amarrada ao token de autenticação, e trilha de auditoria imutável por gatilho de banco.
- Exportador que gera os arquivos de entrada do motor de rateio (base de veículos e planilha de eventos) a partir dos dados cadastrados na esteira, com prova de equivalência: a implementação de referência em Python e a implementação em produção em TypeScript geram o mesmo resultado, verificado por um harness automatizado que roda na suíte de testes do motor.
- Interface web inicial (Next.js) com fluxo de cadastro de associado.

### 3.3 O que isso vale como ativo

O documento de valoração para a mesa de sociedade (elaborado antes deste plano) estimou o custo de reconstrução deste conjunto por um time contratado do zero em R$ 150 a 200 mil, com base em aproximadamente 800 horas técnicas a R$ 110/hora (valor de venda). Este plano de negócios não reabre essa conta: ele assume a participação de 50% já como premissa fechada entre as partes (registrada na negociação de julho de 2026) e concentra-se no que falta construir e operar a partir daqui.

---

## 4. Escopo do produto

O produto cobre o ciclo completo de uma associação de proteção patrimonial mutualista sob gestão da administradora:

1. **Captação e admissão**: cadastro do associado e do veículo, vistoria fotográfica com trava antifraude (a esteira já especificada segue as regras de negócio observadas no App Visto da Hinova: captura só ao vivo, carimbo de data/hora/GPS por foto, fluxo sequencial obrigatório, selfie de vínculo de identidade).
2. **Entrada de dados operacionais**: situação de boleto (adimplência), veículos ativos, e eventos do mês (sinistros), vindos de duas origens possíveis: a esteira de admissão própria, ou a base já existente na associação, hoje mantida no SGA da Hinova. A disponibilidade de adimplência e eventos do mês pela API do SGA (Camada 1, seção 6.2) ainda precisa ser confirmada; enquanto isso não for verificado, esses dois insumos continuam vindo da Camada 0 (arquivo) ou da esteira própria.
3. **Cálculo do rateio**: o motor já validado, sem alteração da lógica matemática.
4. **Emissão e registro de boletos**: geração do boleto ou cobrança PIX por associado, registrada em um provedor de pagamento com liquidação bancária (iugu), com conciliação automática.
5. **Compliance e auditoria**: trilha completa do valor de cada boleto até sua origem (evento, associado, regra de cálculo), discriminação analítica de taxa administrativa, taxa de rateio e fundo de estabilização (exigência da LC 213/2025), e certificação atuarial dos métodos.
6. **Gestão multi-associação**: a administradora opera várias associações na mesma plataforma, com dados isolados por associação e visão consolidada para a administradora.

O motor de cálculo em si não muda. O que se constrói a partir daqui é tudo que está ao redor dele: entrada de dados confiável em escala, saída de dados (boletos) que efetivamente cobram o associado, e as camadas de conformidade que sustentam a operação diante da SUSEP.

---

## 5. Arquitetura técnica proposta

### 5.1 Princípio de dimensionamento

O roadmap de referência elaborado anteriormente (documento "Roadmap de Desenvolvimento de Software: Plataforma para Administradoras") propõe uma arquitetura de microsserviços com Kafka, Kubernetes e Snowflake. Essa proposta é a arquitetura correta para uma plataforma operando em grande escala, mas está superdimensionada para o estágio atual: o que existe hoje é um monolito modular em FastAPI e Next.js, com PostgreSQL via Supabase, e é isso que o conselho já viu precificado (sustentação de R$ 8 mil por mês para uma associação). Este plano propõe uma trajetória de dois estágios:

**Estágio 1 (meses 1 a 18, até 3 a 5 associações)**: monolito modular. Backend em Python (FastAPI), frontend em Next.js (TypeScript), banco PostgreSQL (Supabase), fila de tarefas simples (para processamento assíncrono de rateio e integração com SGA e iugu, sem exigir Kafka), isolamento multi-tenant por RLS (já provado na esteira de admissão). Hospedagem em VPS gerenciado ou serviço de cloud único (não multi-cloud).

**Estágio 2 (a partir de 6 a 10 associações, ou quando o volume de eventos e webhooks justificar)**: extração dos componentes de maior carga (processamento de rateio em lote, ingestão de webhooks de pagamento) para serviços independentes, adoção de fila de mensagens dedicada, e avaliação de Kubernetes se o número de ambientes justificar a complexidade operacional adicional.

A decisão de quando migrar de Estágio 1 para Estágio 2 deve ser tomada com dados de carga real, não antecipada por hipótese. Antecipar a complexidade do Estágio 2 é o principal risco de estouro de orçamento de um projeto como este.

### 5.2 Componentes do Estágio 1

| Camada | Tecnologia | Situação |
|---|---|---|
| API de rateio e admissão | Python / FastAPI | Existe, validada |
| Frontend de gestão | Next.js / TypeScript | Existe (esteira de admissão), a expandir |
| Banco de dados | PostgreSQL (Supabase) | Existe, modelado com RLS multi-tenant |
| Autenticação e autorização | Supabase Auth com claim de associação | Existe |
| Processamento assíncrono | Fila simples (tarefas agendadas / worker dedicado) | A construir |
| Armazenamento de evidências (fotos de vistoria) | Bucket de objetos (Supabase Storage ou equivalente) | A configurar |
| Observabilidade | Logs estruturados + alerta básico (sem stack Prometheus/Grafana completa no Estágio 1) | A construir |
| CI/CD | GitHub Actions | A construir |

---

## 6. Integração com o SGA da Hinova

### 6.1 O que existe hoje

O SGA da Hinova oferece uma API de leitura, com token gerado por cliente (associação) na área de administração do próprio SGA, e um usuário dedicado com permissões restritas a veículos, associados e produtos. A integração é unidirecional (os dados saem do SGA, não há escrita de volta) e roda em ciclo automático, tipicamente a cada seis horas ou uma vez ao dia, dependendo da configuração. Se a situação de boleto (adimplência) e os eventos do mês (sinistros) também estão disponíveis nesses mesmos endpoints, ou apenas veículos, associados e produtos, ainda não foi confirmado; é um ponto a validar diretamente com a documentação da API antes de assumir que a Camada 1 (seção 6.2) automatiza a entrada de todos os dados operacionais listados na seção 4.

Isso significa duas coisas importantes para o plano: primeiro, a integração é tecnicamente viável e documentada, não depende de engenharia reversa. Segundo, o SGA continua sendo a fonte de verdade dos dados enquanto a associação não migrar totalmente para a esteira própria; a plataforma não substitui integralmente o SGA da Hinova enquanto essa migração não ocorrer, ela lê dele.

### 6.2 Modelo em camadas, com risco nomeado

**Camada 0, arquivo**: leitura de planilha exportada manualmente do SGA (ou de qualquer sistema legado), no layout já provado pelo motor de rateio hoje (`ingestao_partes`, com invariante de fechamento zero). Esta camada já funciona, é o caminho mais simples de colocar uma nova associação em produção, e serve de retaguarda permanente mesmo depois que outras camadas existirem.

**Camada 1, leitura via API**: consumo periódico da API do SGA com o token da própria associação, alimentando automaticamente a base de veículos e associados na plataforma. Elimina a exportação manual, mas mantém o SGA como fonte de verdade.

**Camada 2, sincronização contínua**: leitura em ciclo mais curto (horas) e reconciliação automática de divergências, com alerta quando a base local diverge da base do SGA.

**Risco identificado**: a Hinova é fornecedora de um sistema concorrente em parte da tese de longo prazo da plataforma (gestão de associação). Existe risco de que a Hinova restrinja ou descontinue o acesso via API a um concorrente direto. Duas mitigações: primeiro, o dado pertence à associação, não à Hinova, e a credencial usada é da própria associação (não da NEWCO), o que dá amparo de portabilidade de dados sob a LGPD; segundo, a Camada 0 (arquivo) nunca deixa de ser uma opção operacional, então a operação não trava se o acesso via API for interrompido.

---

## 7. Integração com iugu (emissão e registro de boletos)

### 7.1 Modelo de tarifas (pesquisa de mercado, a confirmar em contrato)

A pesquisa de mercado (documentação pública da iugu, sem contrato negociado) indica tarifas fixas por título pago na faixa de R$ 1,99 a R$ 2,50 por boleto registrado, e R$ 1,20 a R$ 1,50 por PIX (ou um percentual sobre o valor, dependendo do plano contratado). Estes números não são definitivos: dependem do plano comercial negociado com a iugu em volume, e devem ser tratados como premissa a validar diretamente com o provedor antes da assinatura de qualquer contrato com a Mutualiza que precifique a operação.

### 7.2 Split de pagamento e estrutura de contas

A iugu oferece um modelo de conta mestre e subcontas com split automático: a fatura pode ser emitida em nome da associação (subconta) com uma regra de divisão automática entre a associação e a NEWCO (por exemplo, a NEWCO recebe sua remuneração por placa automaticamente no momento da liquidação, sem depender de repasse manual). Este modelo resolve dois problemas ao mesmo tempo: mantém a fatura no nome da associação perante o associado (preservando a relação institucional) e automatiza a cobrança da NEWCO.

### 7.3 A decisão que mais afeta o resultado financeiro do plano

A tarifa de meio de pagamento não pode ser absorvida pela NEWCO. Em qualquer cenário de preço por placa discutido (R$ 0,10 a R$ 0,30), a tarifa por título (R$ 1,20 a R$ 2,50) é maior que a receita da NEWCO por placa. Absorver essa tarifa transforma cada placa ativa em prejuízo estrutural, independente de escala: quanto mais a plataforma cresce, maior o prejuízo. A seção 10 mostra o efeito numérico dessa escolha.

**Recomendação**: a tarifa de meio de pagamento é repassada ao boleto do associado, como qualquer sistema de cobrança já faz hoje (é prática padrão de mercado, não uma inovação desfavorável ao associado: o custo de meio de pagamento já existe hoje na operação atual da associação, só não está sendo modelado explicitamente neste plano até aqui). A remuneração da NEWCO (preço por placa) é um valor separado, cobrado à parte, tipicamente embutido na taxa administrativa que a associação já cobra. Este plano não levantou o valor que cada associação paga hoje, fora da NEWCO, pelo meio de pagamento em uso no arranjo vigente; esse levantamento é um item a apurar antes de comunicar o repasse aos associados, para demonstrar que a mudança de emissor é neutra e não um custo novo.

---

## 8. Compliance regulatório (LC 213/2025 e Resolução CNSP 491/2026)

A Resolução CNSP 491/2026 exige que a cobrança emitida pela administradora discrimine analiticamente taxa de administração, taxa de rateio e fundo de estabilização, com individualização contábil por grupo. A não incidência tributária sobre o valor do rateio só vale se esse valor estiver segregado e discriminado dessa forma. O motor de rateio já entrega o fechamento auditável (diferença zero, rastreável evento a evento); a plataforma precisa garantir que essa discriminação chegue até o boleto e até a contabilidade regulatória da administradora.

Isso implica papéis que não são de engenharia de software, mas são obrigatórios para o produto ser aceito pela SUSEP e pelo próprio conselho da Mutualiza:

- **Certificação atuarial**: a Resolução exige que os métodos de rateio sejam certificados por um atuário com registro no IBA (Instituto Brasileiro de Atuária). O cálculo do rateio já é auditável tecnicamente, mas precisa da certificação formal do método por um atuário registrado, e essa certificação deve ser renovada ou revisada quando o método mudar.
- **Contabilidade regulatória**: o plano de contas e os relatórios exigidos pela SUSEP (semelhantes ao COSIF do setor de seguros) precisam ser gerados a partir dos dados da plataforma, o que exige envolvimento de um contador especializado em contabilidade regulatória de seguros e mutualismo desde a fase de modelagem de dados, não só na entrega final.
- **LGPD e proteção de dados**: a plataforma trata dados pessoais sensíveis (documentos, geolocalização de vistoria, dados financeiros). Um responsável por proteção de dados (DPO), ainda que em regime fracionário, deve revisar o desenho de dados e os fluxos de consentimento.
- **Trilha de auditoria**: já existe como princípio de arquitetura na esteira de admissão (auditoria imutável por gatilho de banco); precisa se estender a toda a plataforma, incluindo o registro de boletos e a integração com o SGA.

O calendário regulatório da LC 213/2025 estabelece um prazo de adequação global de 24 meses a partir de maio de 2026, o que coloca o horizonte de adequação plena por volta de maio de 2028. Este plano usa esse horizonte como referência de fundo, sem assumir prazos de janela de protocolo específicos, que dependem de decisões já tomadas (ou não) pela administradora e não são de conhecimento deste documento.

Nesta estrutura, a Mutualiza, como administradora regulada, mantém a responsabilidade final perante a SUSEP por essas obrigações; a NEWCO opera como prestadora da tecnologia e dos processos que sustentam o cumprimento delas, sob contrato entre as partes. A seção 12 trata do mecanismo de decisão societária correspondente.

---

## 9. Equipe e perfis necessários

A equipe abaixo é dimensionada para o Estágio 1 (monolito modular, até 3 a 5 associações). Os valores de custo mensal são estimativas de mercado para contratação PJ no Brasil, na mesma base de referência já usada no documento de custo de julho de 2026 (dev pleno PJ na faixa de R$ 9 a 12 mil por mês, arquiteto part-time na faixa de R$ 3,3 a 5,5 mil por mês). Estes valores devem ser confirmados no momento da contratação; tratam-se de estimativas para fins de planejamento de investimento, não de uma tabela salarial fechada.

| Papel | Dedicação | Início | Custo mensal estimado | Por quê |
|---|---|---|---|---|
| Tech Lead / Arquiteto | Parcial, crescendo para integral nas fases de integração | Mês 1 | R$ 5.500 | Decisões de arquitetura, revisão técnica, integração com SGA e iugu |
| Dev Backend Sênior | Integral | Mês 1 | R$ 12.000 | Motor, API, integrações externas |
| Dev Backend Pleno | Integral | Mês 3 | R$ 9.000 | Módulos de admissão, exportação, testes |
| Dev Frontend / Mobile Pleno | Integral | Mês 1 | R$ 9.000 | Painel de gestão, PWA de vistoria |
| DevOps / SRE | Parcial | Mês 2 | R$ 4.000 | Infraestrutura, CI/CD, backup, monitoramento |
| QA | Parcial | Mês 3 | R$ 3.000 | Testes de regressão, homologação por associação |
| Atuário com registro IBA | Fracionário (consultoria) | Mês 1 | R$ 3.500 | Certificação regulatória dos métodos de rateio, exigência da Res. CNSP 491/2026 |
| Contador regulatório | Fracionário (consultoria) | Mês 4 | R$ 2.500 | Plano de contas e relatórios exigidos pela SUSEP |
| DPO / Compliance LGPD | Fracionário (consultoria) | Mês 1 | R$ 1.500 | Revisão de dados sensíveis, consentimento, retenção |
| Suporte N1 | Parcial | Mês 7 (início da operação) | R$ 2.500 | Atendimento às associações em produção |

Custo de equipe em regime (a partir do mês 7): aproximadamente R$ 52.500 por mês. Este valor cresce pouco com o número de associações no Estágio 1 (a arquitetura multi-tenant é desenhada para isso); o que cresce é a infraestrutura. O Suporte N1 é orçado em regime parcial fixo (R$ 2.500 por mês) do início da operação até o fim do horizonte modelado, sem crescer com o número de associações ou de placas ativas; isso é tratado como ponto de atenção na seção 12, com um gatilho de redimensionamento a definir conforme o volume real de chamados.

A tabela não inclui um papel dedicado de segurança da informação (hardening, gestão de segredos, revisão de superfície de ataque) nem um responsável nomeado para harmonização de layout de dados entre associações, risco já citado na seção 12. Enquanto a equipe não crescer para incluir esses papéis de forma explícita, essa responsabilidade fica com o Tech Lead e os desenvolvedores backend já previstos, como parte do escopo de trabalho deles nas fases de integração (seção 11), o que deve ser revisto se a carga de integrações competir com o cronograma de engenharia.

Papéis que a NEWCO não precisa contratar diretamente, mas que fazem parte do plano operacional: gestão comercial e relacionamento com associações (função da administradora, pelo histórico da negociação), e liderança executiva da NEWCO (função dos sócios).

---

## 10. Modelo financeiro

O modelo completo (script e memória de cálculo) está em `docs/bp_newco/modelo_financeiro_bp.py`, para que qualquer premissa possa ser alterada e o resultado recalculado. Esta seção resume os resultados.

### 10.1 Premissas de rampa (associações e placas ativas)

| Mês | Associações ativas | Placas ativas |
|---|---|---|
| 1 a 6 | 0 (fase de construção) | 0 |
| 7 a 9 | 1 (primeira associação migrada) | 90.000 |
| 10 a 12 | 2 | 150.000 |
| 13 a 15 | 3 (as três associações da Mutualiza) | 190.000 |
| 16 a 24 | Expansão gradual até 6 | 230.000 a 310.000 |

Estas são premissas de planejamento, não uma promessa comercial. A velocidade real de migração das associações depende de decisões da administradora (contratos, priorização, capacidade de onboarding), não só da plataforma estar pronta. O modelo tem um teto técnico de 10 associações na função de rampa; o horizonte de 24 meses simulado aqui chega a 6 associações e 310 mil placas, sem esgotar esse teto.

O modelo também assume um mínimo mensal contratual de R$ 8.000 por associação ativa (piso de faturamento, protegendo a receita contra oscilação de volume): a receita de cada mês é o maior valor entre placas ativas vezes o preço por placa e esse piso. No cenário de R$ 0,10 por placa, esse piso é o que sustenta a maior parte da receita nos primeiros meses (por exemplo, a receita de R$ 16.000 no mês 12 vem inteiramente do piso de duas associações, não das 150 mil placas a R$ 0,10, que dariam R$ 15.000 isoladamente). O valor de R$ 8.000 é uma premissa de planejamento deste modelo, não um número já negociado com a Mutualiza; a seção 13, item 2, trata esse valor como ponto em aberto. Se o piso final for diferente, os resultados da seção 10.3 mudam, com efeito mais visível no cenário de R$ 0,10.

### 10.2 Tarifa de meio de pagamento em escala

Com a premissa de 60% dos boletos pagos via PIX (R$ 1,20) e 40% via boleto registrado (R$ 2,00), a tarifa média fica em R$ 1,52 por placa por mês:

| Mês | Placas ativas | Custo total de meios de pagamento por mês |
|---|---|---|
| 7 | 90.000 | R$ 136.800 |
| 12 | 150.000 | R$ 228.000 |
| 16 | 230.000 | R$ 349.600 |
| 24 | 310.000 | R$ 471.200 |

Comparação direta: a receita da NEWCO no cenário de R$ 0,30 por placa, no mês 24 com 310 mil placas, é de R$ 93.000. A tarifa de meio de pagamento no mesmo mês é de R$ 471.200, cinco vezes maior. Absorver essa tarifa inviabiliza o modelo em qualquer preço por placa razoável para o mercado atual.

### 10.3 Cenários de investimento (24 meses), com repasse da tarifa de meio de pagamento

"Investimento total necessário" é a soma dos resultados mensais negativos ao longo dos 24 meses: um piso de capital de giro que cobre os meses em que a operação está no vermelho, mês a mês. Não é o mesmo que o caixa acumulado ao final do mês 24, que também aparece na tabela abaixo e mostra se o capital investido já foi recuperado dentro do horizonte modelado.

| Preço por placa | Investimento total necessário (soma dos meses de caixa negativo) | Mês de equilíbrio operacional | Resultado mensal no mês 24 | Caixa acumulado no mês 24 |
|---|---|---|---|---|
| R$ 0,10 | R$ 791.000 | Não atingido em 24 meses | R$ - 9.500 | R$ - 791.000 |
| R$ 0,20 | R$ 567.500 | Mês 22 | R$ + 4.500 | R$ - 554.000 |
| R$ 0,30 | R$ 397.400 | Mês 13 | R$ + 35.500 | R$ - 182.000 |

Mesmo no melhor cenário (R$ 0,30), a operação passa a ser positiva mês a mês a partir do mês 13, mas o capital investido ainda não é totalmente recuperado dentro dos 24 meses simulados: o caixa acumulado no mês 24 continua negativo em R$ 182.000. Um conselho avaliando aporte deve ler esses números como capital de giro necessário e ponto em que a operação mensal se sustenta sozinha, não como um payback pleno do investimento dentro do horizonte deste plano.

No cenário de R$ 0,10, o equilíbrio operacional não é atingido em nenhum mês do horizonte simulado; o valor de R$ 791.000 é o caixa negativo acumulado nos 24 meses, não um investimento até um marco alcançado.

Para referência, sem o repasse da tarifa (cenário que este plano não recomenda), o investimento necessário sobe para a faixa de R$ 5,8 a R$ 6,4 milhões nos mesmos 24 meses, e o equilíbrio operacional não é atingido em nenhum cenário de preço testado. A diferença entre as duas colunas é inteiramente a decisão de repasse descrita na seção 7.3.

### 10.4 Leitura do modelo para o conselho

Com repasse da tarifa de pagamento, o caixa consumido ao longo de 24 meses está, nos três cenários, entre R$ 400 mil e R$ 800 mil. Nos cenários de R$ 0,20 e R$ 0,30, esse valor é de fato o investimento necessário até o ponto de equilíbrio operacional, que é atingido dentro do horizonte modelado (mês 22 e mês 13, respectivamente); no cenário de R$ 0,10, o equilíbrio não é atingido em 24 meses e o valor de R$ 791.000 é o caixa negativo acumulado no período, o que reforça a recomendação de não adotar esse preço isoladamente. O preço por placa é a alavanca que mais move esse número: sair de R$ 0,10 para R$ 0,30 reduz o caixa consumido em quase 50% e leva o equilíbrio operacional de "não atingido" para o mês 13. Uma estrutura de preço escalonado por volume (por exemplo, R$ 0,30 até 100 mil placas, R$ 0,25 até 250 mil, R$ 0,20 acima disso) preserva a maior parte desse efeito e é mais fácil de negociar com uma administradora que já sinalizou resistência a um valor fixo mais alto.

O investimento cobre, nesta ordem de prioridade: (1) a equipe técnica descrita na seção 9 durante a fase de construção (meses 1 a 6, sem receita); (2) o capital de giro para sustentar os meses de resultado negativo enquanto a base de placas ainda não cobre o opex integral; (3) a infraestrutura de produção (servidores, backup, ambientes de homologação).

**Comparação com o documento de julho de 2026**: para tornar o salto de escopo comparável, o custo de julho (R$ 31 mil de implantação mais R$ 8 mil por mês) projetado para o mesmo horizonte de 24 meses somaria aproximadamente R$ 31.000 + 22 × R$ 8.000 ≈ R$ 207.000 (assumindo sustentação a partir do terceiro mês, na mesma lógica de rampa curta daquele documento). Contra o investimento deste plano (R$ 400 mil a R$ 800 mil nos mesmos 24 meses), o salto real é de aproximadamente 2 a 4 vezes, não de 13 a 25 vezes como uma leitura literal dos dois números pontuais sugeriria. A diferença é explicada, em termos qualitativos, pelos itens de escopo que o documento de julho não cobria: captação e admissão do associado, integração com o SGA de cada associação, meio de pagamento próprio com split automático, compliance regulatório (certificação atuarial, contabilidade regulatória, DPO) e operação simultânea de múltiplas associações. Este plano não tem uma memória de cálculo que separe o investimento por esses componentes individualmente; a decomposição acima é qualitativa, não uma tabela de custo por item.

### 10.5 O que este modelo não inclui

Este modelo não inclui: custos de constituição societária e jurídicos da NEWCO; imposto sobre o lucro ou sobre a receita da NEWCO (depende do regime tributário a definir com o contador, Lucro Presumido ou Real, já que uma administradora exclusiva não pode optar pelo Simples); despesas comerciais de captação de novas associações fora da carteira já existente da Mutualiza; e o custo de capital (se o aporte vier de terceiros com remuneração, ou dos próprios sócios sem remuneração). Estes pontos devem ser tratados na negociação de estrutura societária e não são estimados aqui por falta de premissa validada.

---

## 11. Roadmap e cronograma (sprints de duas semanas)

O cronograma abaixo é organizado em sprints quinzenais, agrupados em fases. As fases têm sobreposição parcial (a fase seguinte começa antes da anterior terminar totalmente), o que é o desenho pretendido, não um atraso.

### Fase 0, constituição (paralela, sem depender de sprint de engenharia)
Abertura da NEWCO, definição societária, contrato entre as partes, registro na SUSEP como estrutura vinculada à administradora. Não bloqueia o início da Fase 1; a equipe técnica pode iniciar sob contrato de prestação de serviço até a formalização societária da NEWCO, caso o conselho priorize o início da execução em vez de aguardar a conclusão da estruturação societária.

### Fase 1, meses 1 a 3 (sprints 1 a 6): hardening do que já existe
- Sprint 1 a 2: fechar os pré-requisitos de produção da esteira de admissão já especificada (provisionar projeto Supabase real, ativar o hook de claim de autenticação, criar o bucket de vistorias, completar os endpoints de edição e reenvio de foto que ficaram pendentes na especificação).
- Sprint 3 a 4: subir o motor de rateio e a esteira de admissão em ambiente de produção real, com uma associação piloto (a que tiver a base de dados mais organizada, provavelmente AutoTruck pela validação já feita).
- Sprint 5 a 6: fechar o ciclo completo com dados reais de um mês fechado: admissão, eventos, exportação, rateio, sem gerar boleto ainda (validação de ponta a ponta antes de processar qualquer transação financeira real).

Entregável de fase: primeiro rateio de produção rodando com dados reais de uma associação, sem intervenção manual na exportação.

### Fase 2, meses 3 a 5 (sprints 5 a 10): integração com o SGA da Hinova (Camada 0 e 1)
- Sprint 5 a 6 (sobreposição com a Fase 1): construir o adaptador de leitura de planilha exportada do SGA no layout já provado (Camada 0), para associações que ainda não migraram para a esteira própria.
- Sprint 7 a 8: construir o adaptador de leitura via API do SGA (Camada 1), com o token da associação, sincronização diária.
- Sprint 9 a 10: reconciliação e alerta de divergência entre a base local e a base do SGA.

Entregável de fase: uma associação operando com cadastro de veículos e associados vindo automaticamente do SGA (Camada 1), sem exportação manual de planilha para esses dados. Situação de boleto e eventos do mês permanecem pela Camada 0 (arquivo) até que a disponibilidade desses dados pela API do SGA seja confirmada, conforme a ressalva da seção 6.1.

### Fase 3, meses 5 a 7 (sprints 9 a 14): integração com iugu (sobreposição com Fase 2)
- Sprint 9 a 10: contratação e homologação da conta iugu (conta mestre e subcontas), ambiente de testes (sandbox). Esta etapa depende da negociação comercial de tarifas com o provedor (seção 7.1), não é uma tarefa puramente de engenharia; um desvio relevante em relação à faixa pesquisada deve disparar recálculo do modelo financeiro (seção 10) antes de qualquer sprint seguinte que dependa desse número.
- Sprint 11 a 12: geração de boleto e cobrança PIX a partir do resultado do rateio, com o valor discriminado (taxa administrativa, taxa de rateio, fundo de estabilização) exigido pela Resolução CNSP 491/2026.
- Sprint 13 a 14: webhook de confirmação de pagamento, conciliação automática, e split de pagamento entre associação e NEWCO. O primeiro ciclo de cobrança real roda em piloto controlado, iniciando com um subconjunto de placas da associação piloto (por exemplo, 5 a 10 mil de 90 mil) antes de estender para a base completa, com acompanhamento reforçado do Suporte N1 nas primeiras semanas.

Entregável de fase: primeiro boleto real emitido, registrado e liquidado pela plataforma, com a remuneração da NEWCO sendo recebida automaticamente pelo split. Este primeiro ciclo real roda sob supervisão do atuário contratado desde o mês 1 (seção 9), com a certificação formal do método de rateio (Fase 4) concluída antes da liquidação do primeiro boleto real, ainda que a modelagem do plano de contas regulatório e os demais itens da Fase 4 continuem em paralelo.

### Fase 4, meses 6 a 9 (sprints 12 a 18, sobreposta às Fases 2 e 3): compliance regulatório
- Certificação atuarial do método de rateio (atuário registrado no IBA), com conclusão priorizada para o mês 7, antes da liquidação do primeiro boleto real da Fase 3.
- Modelagem do plano de contas regulatório junto ao contador especializado, que pode se estender até o mês 9.
- Revisão de LGPD de todo o fluxo de dados (admissão, vistoria, pagamento) pelo DPO fracionário.
- Geração dos relatórios de auditoria e trilha completa (evento até boleto) exigidos para eventual inspeção da SUSEP.

Entregável de fase: a operação está defensável diante de uma auditoria da SUSEP, com certificação atuarial válida desde o primeiro boleto real e contabilidade regulatória gerando os relatórios exigidos até o mês 9.

### Fase 5, meses 9 a 13 (sprints 17 a 26): migração da segunda e terceira associação da Mutualiza
- Cada associação nova segue o mesmo ciclo das Fases 1 a 3, mas mais rápido, porque a plataforma já existe (o trabalho por associação nova é principalmente configuração multi-tenant, migração de dados históricos e homologação, não desenvolvimento novo).
- Processo de migração por associação, com etapas nomeadas: extração e inventário dos dados no SGA de origem; saneamento com checklist objetivo (campos obrigatórios, formatos aceitos, duplicidades, veículos sem cota), com inconsistência de cadastro corrigida pela associação na fonte e inconsistência de mapeamento ou layout corrigida pelo adaptador da NEWCO; carga em ambiente de homologação; fechamento em paralelo por um mês, usando o critério de diferença zero (seções 3.1 e 6) como gate formal de aceite; corte para produção; acompanhamento reforçado do Suporte N1 nos dois primeiros ciclos de cobrança pós-corte. A responsabilidade por cada etapa é do time de engenharia já dimensionado na seção 9, com o Suporte N1 assumindo o acompanhamento pós-corte.
- Capacitação da equipe da associação no novo fluxo e plano de comunicação aos associados sobre a troca de emissor do boleto, sob responsabilidade do Suporte N1 em conjunto com a gestão comercial da administradora (seção 9), incluindo aviso prévio e acompanhamento do primeiro ciclo de cobrança para reduzir o risco de contestação ou não pagamento por associados que não reconheçam o novo boleto (seção 12).
- Meta: as três associações da Mutualiza (AutoTruck, ELLO, AVAP) operando na plataforma até o fim desta fase.

### Fase 6, a partir do mês 13: expansão para a carteira ampliada da Mutualiza
Onboarding de associações adicionais fora das três iniciais, no ritmo comercial que a administradora definir, seguindo o mesmo processo de migração descrito na Fase 5. Tecnicamente, cada nova associação é um evento de configuração, não um novo ciclo de desenvolvimento, desde que permaneça no mesmo desenho de esteira de risco. Uma associação com regras de rateio muito diferentes das já implementadas pode exigir trabalho de engenharia adicional, a ser dimensionado e orçado no momento em que essa associação for identificada.

---

## 12. Riscos e mitigação

| Risco | Impacto | Mitigação |
|---|---|---|
| Hinova restringe acesso à API do SGA para um concorrente | Alto para associações que dependem de dados automáticos | Camada 0 (arquivo) sempre disponível como retaguarda; credencial é da associação, amparo de portabilidade de dados sob LGPD |
| Tarifa de meio de pagamento absorvida em vez de repassada | Crítico, inviabiliza o modelo financeiro em qualquer escala | Decisão de repasse tratada como pré-condição do contrato com cada associação, não como opção futura |
| Prazo de certificação atuarial ou contábil atrasa a entrada em operação | Médio, atrasa a Fase 4 | Iniciar a contratação do atuário e do contador regulatório no mês 1, em paralelo ao desenvolvimento, não depois dele |
| Ritmo de migração das associações mais lento que o premissado | Médio, adia o ponto de equilíbrio operacional | Modelo financeiro já trata isso como variável (seção 10.1); mínimo mensal contratual por associação protege a receita mínima independente do volume |
| Escopo de integração do SGA maior que o previsto (dados inconsistentes, layouts variados entre associações) | Médio, pode estender a Fase 2 e a Fase 5 | Camada 0 (arquivo) absorve a variação inicial; o processo de migração por associação (seção 11, Fase 5) define o checklist de saneamento e a regra de responsabilidade entre associação e NEWCO |
| Complexidade de arquitetura antecipada (Estágio 2 antes da hora) | Médio, estoura orçamento sem necessidade | Decisão de migração de estágio arquitetural condicionada a dados de carga real, não a hipótese (seção 5.1) |
| Suporte N1 orçado em regime parcial fixo não escala com o número de associações ou de placas ativas | Médio, risco de atendimento insuficiente a partir de determinado volume | Redimensionar o Suporte N1 (parcial para integral, ou posições adicionais) quando o volume de chamados por associação justificar, com recálculo do custo de equipe no momento da decisão |
| Queda de adimplência na transição de emissor de boleto (associado não reconhece o novo boleto emitido via iugu) | Médio, impacta a receita da NEWCO (dependente do split sobre o valor liquidado) e a relação da associação com seus associados | Comunicação prévia ao associado sobre a troca de emissor e acompanhamento reforçado pelo Suporte N1 nos dois primeiros ciclos de cobrança de cada associação recém-migrada (seção 11, Fase 5) |
| Ausência de mecanismo de decisão definido para a sociedade 50/50 sem sócio de desempate | Médio, pode travar decisões relevantes da NEWCO | A definir na estruturação societária (Fase 0); reconhecido aqui como ponto em aberto em vez de omitido |

**Governança e responsabilidade regulatória**: a Mutualiza, como administradora regulada pela LC 213/2025, mantém a responsabilidade final perante a SUSEP pelas obrigações descritas na seção 8 (certificação atuarial, contabilidade regulatória, LGPD, trilha de auditoria); a NEWCO opera como prestadora da tecnologia e dos processos que sustentam esse cumprimento, sob contrato entre as partes. O mecanismo de decisão e desempate na sociedade 50/50 ainda não está definido e é tratado como ponto em aberto na tabela acima, a fechar na estruturação societária da Fase 0.

---

## 13. Pontos em aberto (a fechar com a Mutualiza)

Estes pontos já estavam em aberto no registro de entendimentos de julho de 2026 e continuam sem definição neste plano, porque dependem de negociação, não de engenharia:

1. **Valor final por placa**: este plano recomenda a faixa de R$ 0,25 a R$ 0,30, ou uma tabela escalonada por volume, com base no modelo financeiro da seção 10. O valor de referência de R$ 0,10 discutido anteriormente cobre apenas a sustentação de uma associação isolada, no escopo restrito do documento de julho; não cobre o investimento de plataforma descrito aqui.
2. **Mínimo mensal contratual por associação**: necessário como piso de faturamento independente de oscilação de volume; valor a fechar. O modelo financeiro da seção 10 usa R$ 8.000 por associação por mês como premissa de planejamento (seção 10.1 e seção 15); este é o valor que sustenta boa parte da receita do cenário de R$ 0,10 por placa nos primeiros meses de cada associação, e o resultado da seção 10.3 muda se o valor final negociado for diferente.
3. **Forma de pagamento do investimento inicial**: aporte à vista, por marcos de entrega (por fase, conforme a seção 11), ou diluído no fluxo de caixa da operação.
4. **Ritmo de migração das três associações da Mutualiza**: a data de início de cada associação afeta diretamente a rampa da seção 10.1 e, portanto, o ponto de equilíbrio.
5. **Tarifas efetivas da iugu**: os números da seção 7.1 vêm de pesquisa pública, não de contrato negociado. Precisam ser confirmados antes de qualquer compromisso de preço final com as associações.
6. **Regime tributário e estrutura de custos societários da NEWCO**: fora do escopo deste modelo financeiro (seção 10.5), a definir com o contador responsável pela constituição.

---

## 14. Como este plano se conecta ao que o conselho já viu

O documento de custo de julho de 2026 (R$ 31 mil de implantação, R$ 8 mil por mês de sustentação, 75 mil placas) tratava de produtizar o motor de rateio isoladamente, para uma associação, sem captação própria, sem integração de SGA, sem meio de pagamento próprio. Era o escopo certo para aquela conversa, e o motor que ele descreve é o mesmo motor usado neste plano, sem alteração da lógica.

Este documento amplia o escopo para o que a decisão de investimento na NEWCO exige: uma plataforma que atenda às três associações da Mutualiza e à carteira futura, com dados entrando automaticamente (do SGA ou da esteira própria) e boletos saindo registrados e liquidados por um provedor de pagamento real. O custo de julho, normalizado para o mesmo horizonte de 24 meses, é o custo de "um motor de rateio funcionando" para uma associação; o investimento deste plano, nos mesmos 24 meses, é o custo de "uma plataforma operando até dez associações com compliance regulatório e meio de pagamento próprio". A seção 10.4 normaliza os dois valores no mesmo horizonte e mostra que o salto real é de aproximadamente 2 a 4 vezes, não de 13 a 25 vezes como a comparação direta dos dois números pontuais sugeriria.

---

## 15. Premissas explícitas (para revisão e correção)

Todas as premissas abaixo devem ser tratadas como hipóteses de planejamento, sujeitas a correção antes de qualquer compromisso formal:

- Tarifas de iugu (R$ 1,99 a R$ 2,50 por boleto, R$ 1,20 a R$ 1,50 por PIX) vêm de documentação pública, não de contrato negociado.
- Custos de equipe (PJ, Brasil, faixas de mercado para pleno, sênior e fracionário) são estimativas de mercado, não propostas fechadas com profissionais específicos.
- A rampa de associações e placas (seção 10.1) é uma premissa de planejamento, não uma promessa comercial da Mutualiza.
- O mix de 60% PIX e 40% boleto registrado é uma premissa razoável de mercado, não um dado medido da base real das associações.
- Mínimo mensal contratual usado no modelo: R$ 8.000 por associação (premissa de planejamento; o valor real é objeto de negociação, ver seção 13, item 2).
- O horizonte regulatório de 24 meses (até maio de 2028) é o prazo geral de adequação da LC 213/2025; prazos específicos de protocolo já eventualmente cumpridos pela Mutualiza não são de conhecimento deste documento e devem ser confirmados por quem acompanha o processo regulatório diretamente.

---

*Documento de uso interno. Não constitui proposta comercial nem compromisso contratual. Todos os números são estimativas de planejamento sujeitas a validação.*
