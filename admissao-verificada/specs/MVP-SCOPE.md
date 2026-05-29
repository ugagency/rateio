# MVP-SCOPE — Admissão Verificada

> Escopo, requisitos e critérios de aceite do MVP. Fonte de verdade do que
> entra e do que não entra. Enxuto por decisão.

## 1. Norte

Gerar uma base que produza os arquivos BASE e RATEIO no layout que o motor
aprovado já consome. Tudo que não serve diretamente a esse fim fica fora do
MVP.

## 2. Fronteira de escopo

### Dentro
- Acesso de operadores de uma associação (mínimo).
- Cadastro de associado (dados mínimos de identificação).
- Cadastro de veículo com segmento (LEVES, MOTOS, PESADOS), valor FIPE e
  cobertura de terceiros.
- Cota do veículo derivada da faixa de FIPE (parametrizável), espelhando a
  regra do motor.
- Admissão verificada: esteira de vistoria antifraude inspirada no App Visto.
- Situação de boleto por competência mensal (baixado, aberto, cancelado) por
  veículo, que define o denominador da BASE.
- Captura mínima de eventos do mês para compor o RATEIO.
- Exportação de BASE.xlsx e RATEIO.xlsx no layout do motor.
- Harness de reconciliação que roda o motor aprovado sobre os arquivos
  exportados e confere invariante zero.

### Fora (explicitamente)
- Funil de lead, cotação e proposta comercial (território de CRM).
- Integração com SGA ou qualquer sistema externo.
- Gateway de pagamento real, conciliação bancária, emissão de boleto no banco.
- Gestão completa de sinistros (workflow de reparo, oficina, perícia).
- OCR de documentos e IA (entram em fase posterior; no MVP, entrada manual).
- App nativo iOS e Android (MVP é PWA com câmera).
- Motor de rateio genérico do protótipo anterior (descartado).
- Cálculo do rateio dentro do app novo (quem calcula é o motor aprovado).

## 3. Requisitos funcionais

Autenticação e associação
- RF-AUTH-01: O sistema DEVE permitir login por e-mail e senha para operadores.
- RF-AUTH-02: O sistema DEVE vincular todo registro a uma associação (tenant).

Associado
- RF-ASSOC-01: O sistema DEVE cadastrar associado com nome e CPF.
- RF-ASSOC-02: O sistema DEVE validar o CPF pelo algoritmo oficial.
- RF-ASSOC-03: O sistema DEVE impedir CPF duplicado na mesma associação.

Veículo e cota
- RF-VEIC-01: O sistema DEVE cadastrar veículo com placa, segmento, valor FIPE
  e cobertura de terceiros (nenhuma, 50k, 100k).
- RF-VEIC-02: O sistema DEVE validar a placa (padrão antigo e Mercosul).
- RF-VEIC-03: O sistema DEVE classificar o segmento em LEVES, MOTOS ou PESADOS.
- RF-VEIC-04: O sistema DEVE calcular a cota do veículo pela faixa de FIPE,
  com a mesma regra do motor (parametrizável).

Admissão verificada (vistoria)
- RF-VIST-01: O sistema DEVE permitir definir scripts de vistoria por tipo
  (carro, moto, reboque, revistoria), com quantidade e ordem de fotos.
- RF-VIST-02: O sistema DEVE capturar fotos somente ao vivo, bloqueando upload
  da galeria.
- RF-VIST-03: O sistema DEVE carimbar cada foto com data, hora e
  geolocalização.
- RF-VIST-04: O sistema DEVE exigir o fluxo sequencial completo (selfie,
  documento, fotos do veículo) e só marcar a vistoria como finalizada quando
  concluída inteira.
- RF-VIST-05: O sistema DEVE registrar o início, cada captura e a finalização
  com horário (base da timeline antifraude).
- RF-VIST-06: O sistema DEVE vincular a vistoria finalizada ao veículo,
  habilitando-o à admissão.

Situação de boleto (denominador da BASE)
- RF-SIT-01: O sistema DEVE registrar, por veículo e competência, a situação
  do boleto (baixado, aberto, cancelado).
- RF-SIT-02: O sistema DEVE consolidar, por segmento, as cotas baixadas,
  abertas e canceladas da competência.

Eventos (numerador do RATEIO)
- RF-EVT-01: O sistema DEVE cadastrar evento com marcador de seção (segmento
  mais envolvimento associado ou terceiro), tipo (INTEGRAL ou PARCIAL),
  protocolo, placa, data de comunicação e valor rateado.
- RF-EVT-02: O sistema DEVE rejeitar evento sem protocolo ou com valor rateado
  menor ou igual a zero.

Exportação
- RF-EXP-01: O sistema DEVE exportar a BASE da competência no layout do motor.
- RF-EXP-02: O sistema DEVE exportar o RATEIO da competência no layout do motor.
- RF-EXP-03: Os arquivos exportados DEVEM passar em `detectar_tipo` com o tipo
  correto.

## 4. Requisitos não funcionais (mínimos)

- RNF-01: Toda tabela DEVE ter isolamento por associação (RLS).
- RNF-02: Toda operação de admissão DEVE deixar trilha de auditoria imutável.
- RNF-03: Fotos e metadados de vistoria DEVEM ser imutáveis após finalização.
- RNF-04: Comunicação por HTTPS; dados pessoais tratados conforme a LGPD.

## 5. Critério de aceite do MVP

Given uma associação com associados admitidos pela esteira e eventos lançados
na competência,
When o operador exporta BASE e RATEIO e roda o harness de reconciliação,
Then `detectar_tipo` reconhece cada arquivo, o motor aprovado processa sem
erro e o invariante de fechamento é igual a zero.

## 6. Questões em aberto

- Arquivo PRODUTOS: tratado como opcional e informativo no MVP (decisão de
  negócio ainda pendente, herdada da especificação de insumos).
- Perfil ELLO: o MVP mira o layout AutoTruck; o perfil ELLO entra depois.
- Casos sem vistoria por câmera (frota, pessoa jurídica, associado sem
  smartphone): porta alternativa fica para fase posterior.
