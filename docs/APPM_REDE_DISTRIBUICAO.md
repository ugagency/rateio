# APPM, Rede de Distribuicao de Protecao Patrimonial Mutualista

Desenho de canais, verificacao e remuneracao. Documento vivo, em evolucao.

## 1. Principio central

Captura descentralizada, verificacao centralizada.

Muitos canais trazem associado (escala). Um unico motor de verificacao decide
quem entra (a vistoria virando admissao verificada, com as regras antifraude por
baixo). A regra de ouro: so se paga comissao sobre associado verificado e ativo,
nunca sobre lead cru. Isso alinha cada canal ao antifraude, porque ninguem ganha
trazendo cadastro fantasma.

## 2. O trilho

```
  CANAIS DE CAPTACAO                  VERIFICACAO            ESCOPO MUTUALIZA
  (nossos, fora do escopo)            (nosso motor)          (rateio)

  Agente de campo        \
  Correspondente/ponto    \                                  +-----------+
  Afiliado/influencer      >--->  APPM  --->  Admissao  --->  BASE/RATEIO  --->  Motor
  Self-onboarding         /       vistoria    Verificada     +-----------+      de Rateio
                         /        + antifraude
                                                            ^
                                  ----- fronteira de escopo -----
                                  tudo a esquerda e nosso (captacao)
                                  a base entra no motor = ponto de entrega
```

A linha de fronteira com a Mutualiza e desenhada no dado: o que e deles comeca
quando a BASE/RATEIO entra no motor. Tudo a montante (captacao, vistoria, CRM,
relacao com o lead) e nosso, fora do escopo e fora do roadmap deles.

## 3. Canais, do mais assistido ao mais self-service

| Canal | Quem capta | Verificacao | Risco de fraude |
|---|---|---|---|
| Agente de campo | Pessoa com APPM em ponto de fluxo (posto, estacionamento) | Vistoria assistida na hora | Baixo |
| Correspondente / ponto afiliado | Estabelecimento fixo (mercado, varejo) faz o onboarding | Vistoria assistida pelo balcao | Baixo a medio |
| Afiliado digital / influencer | Indica o app, nao toca na vistoria | Autosservico guiado | Alto |
| Self-onboarding direto | Associado acha o app e faz sozinho | Autosservico guiado | Alto |

## 4. Verificacao por canal

O rigor do antifraude cresce na exata medida em que a assistencia humana some.

- Assistida (agente, correspondente): a presenca de um agente ja e controle.
  Captura de foto e video supervisionada, conferencia de documento no ato.
  Antifraude roda mais leve, so como malha de seguranca.
- Autosservico guiado (afiliado, self): o app carrega toda a verificacao.
  Prova de vida, OCR e validacao da placa, casamento com FIPE, geolocalizacao,
  deteccao de imagem reaproveitada ou adulterada, cruzamento de base. Antifraude
  no rigor maximo.

Sem essa camada, afiliado e self viram porta aberta pra cadastro fantasma. Com
ela, da pra abrir a porteira com seguranca. E exatamente o que a captura
descentralizada precisa pra escalar.

## 5. Remuneracao

Gatilho sempre apos verificacao. Nunca por lead.

| Canal | Quando paga | Forma |
|---|---|---|
| Agente de campo | Vistoria aprovada + 1a cota paga | Valor por associado verificado |
| Correspondente / ponto | Vistoria aprovada + carteira ativa | Valor por associado + share recorrente sobre a carteira que trouxe |
| Afiliado / influencer | Vistoria aprovada + associado ativo X meses | CPA digital, pago so pos-verificacao |
| Self-onboarding | Nao ha comissao | Menor custo de aquisicao |

Racional: pagar so sobre verificado e ativo transforma o antifraude em guardiao
do caixa. Quanto mais self-service o canal, mais a esteira de verificacao tem que
carregar antes de liberar qualquer pagamento.

Ponto a validar juridicamente (LC 213 / SUSEP): a analogia do correspondente
bancario e perfeita no conceito, mas o veiculo legal e o ponto. Definir, por
canal, se o parceiro entra como indicador de lead (mais seguro) ou como
intermediario remunerado (precisa caber na regra de intermediacao de admissao
mutualista). Validar antes de prometer comissao em contrato.

## 6. Como o trilho monetiza (pra nos)

Separado e bem acima dos centavos do rateio. O rateio e a entrada barata de
proposito (ancora). A rede e onde mora a receita:

- Taxa de onboarding por associado verificado, cobrada da administradora.
- Licenca/SaaS da ferramenta de distribuicao para a administradora.
- Share recorrente sobre a carteira originada pelo trilho.
- O dado e a relacao com o associado, que destravam os modulos seguintes
  (financeiro, sinistro, CRM) por cima da mesma base.

## 7. Por que isso e leapfrog, nao copia

App Visto e ferramenta de vistoria. APPM e uma plataforma de distribuicao de
protecao patrimonial que usa a vistoria como etapa de verificacao. A incumbente
capta com forca de venda linear (vendedor, representante, panfleto no sinal), que
escala somando gente. O trilho escala somando canais. E desenho de rede, nao
software, e e a parte que mentalidade de desenvolvimento tradicional nao copia
rapido.

## 8. Pontos abertos pra evoluir

- Veiculo juridico de cada canal sob LC 213 / SUSEP (indicador vs intermediario).
- Numeros: taxa de onboarding, CPA por canal, percentual de share recorrente.
- Niveis de verificacao: o que exatamente o autosservico guiado exige passo a passo.
- Antifraude: lista de checagens minimas por nivel de risco.
- Painel do parceiro: o que o correspondente e o afiliado veem e acompanham.
- Onde a Mutualiza e as tres associadas entram como primeiros pontos da rede.
