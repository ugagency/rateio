# CONTEXT: Motor de Rateio - Plataforma Mutualiza
# Data: 09/05/2026
# Tech Lead: Ronaldim
# Projeto: Sistema alternativo ao SGA para associação de proteção veicular

## 1. O QUE JA ESTA PRONTO

### Arquivos nesta pasta (/home/ronaldim/Mut/):
- `dados_simulados.json` (3MB) — 10.027 veículos, 500 eventos, 10K serviços fixos
- `rodar_motor_rateio.py` (7.3KB) — Motor de rateio 100% funcional e validado
- `gerar_dados_simulados.py` (3.2KB) — Gerador de dados com seed 42
- `MotorRateio_Demo.html` (3MB) — Demo interativo com 6 abas (Tailwind+CDN)
- `outputs/` — 3 planilhas xlsx de saída (consolidado, eventos rateados, boletos)
- `PRD.md`, `SETUP.md`, `CONTEXTO.md`

### Métricas validadas:
- Alvo financeiro: R$ 716.964,00
- Diferença alvo vs alocação: R$ 0,00 (bate exato!)
- Boletos a gerar: 8.390 (isentos: 1.637)
- Receita total esperada: R$ 803.405,30
- Ticket médio: R$ 95,76
- Eventos rateados: 26 (25 liquidados, 1 parcial)

---

## 2. REGRAS DE NEGOCIO — LEIA COM ATENCAO

### Esteira de Risco (4 Potinhos Cumulativos):

P1 (Roubo/Furto): R$ 14/cota × **TODOS** os veículos elegíveis
P2 (Moto FIP): R$ 4/cota × (todos - somente Roubo/Furto)
P3 (Venture 1): R$ 18/cota × (todos - Roubo/Furto - FIP)
P4 (Venture 2): R$ 18/cota × (todos - Roubo/Furto - FIP - V1)

Valor final por categoria de veículo:
- ROUBO_FURTO: R$ 14/cota (só P1)
- MOTO_FIP: R$ 18/cota (P1 + P2 = 14 + 4)
- VENTURE_1: R$ 36/cota (P1 + P2 + P3 = 14 + 4 + 18)
- VENTURE_2: R$ 54/cota (P1 + P2 + P3 + P4 = 14 + 4 + 18 + 18)

### Pre-processamento:
- Data de quebra: dia 25 do mês
- Contratos até dia 25 → entram no fechamento atual
- Contratos após 25 → entram no próximo mês
- Inadimplentes (>5 dias de atraso) perdem cobertura
- Execução do rateio: ~dia 27

### Elegibilidade:
- Base: veículos com status "Ativo" e contrato até dia 25
- **Funcionários**: NÃO entram na matemática do rateio, NÃO geram boleto
- **Plano Anual**: cotas entram como peso no cálculo do alvo, mas NÃO gera boleto mensal

### Alocação de Eventos:
- Eventos são inseridos na base até bater o valor exato do alvo
- Independência de origem: não importa a categoria do sinistro
- Prioridade: **data de ocorrência ASC** → **valor DESC** → sorteio
- **Rateio parcial habilitado**: fatiar um evento para atingir os centavos exatos do alvo
- Exemplo: de um evento de R$ 10.000, usar R$ 5.000 neste mês, resto no próximo
- Se eventos somarem MENOS que o alvo: sobra → guarda para o próximo mês

### Enriquecimento Pós-Rateio:
- Unir valor do rateio + produtos fixos (Taxa Adm, Assist 24h, rastreador, etc.)
- ~10.000 boletos gerados fora do SGA

### Preocupações Arquiteturais:
- **Idempotência**: lock por Mes_Ano_Ref — só 1 rateio por mês
- **Rateio parcial**: campo `Valor_Saldo_Pendente` atualizado a cada rateio
- **Teto**: se eventos < alvo, sobra vai para próximo mês
- **Auditoria**: LC 213/2025 exige rastreabilidade completa (cada associado vê seu boleto detalhado)

---

## 3. ESTRUTURA DOS DADOS

### Veículo:
```
ID_Veiculo, Status_Ativo(bool), Data_Quebra, Tipo_Categoria_Risco, Qtd_Cotas(1-26), Tipo_Pagamento, Is_Funcionario(bool)
```

### Evento:
```
ID_Evento, Data_Ocorrencia_Evento, Valor_Total_Evento, Valor_Saldo_Pendente
```

### Serviço Fixo:
```
ID_Veiculo, Taxa_Administrativa, Valor_Assistencia_24h, Valor_Outros_Produtos
```

### Tabelas de Saída (geradas pelo motor):

**TB_SAIDA_CONSOLIDADO_ALVO_MES** (1 linha/mês):
```
Mes_Ano_Ref, Total_Cotas_Apuradas, Valor_Alvo_Total, Valor_Degrau_FIP, Valor_Degrau_Venture
```

**TB_SAIDA_EVENTOS_RATEADOS**:
```
Mes_Ano_Ref, ID_Evento, Valor_Rateado_Neste_Mes, Status_Evento(LIQUIDADO/SALDO_RESTANTE)
```

**TB_SAIDA_FATURAMENTO_BOLETOS**:
```
ID_Veiculo, Mes_Ano_Ref, Custo_Rateio_Calculado, Custo_Produtos_Fixos, Valor_Total_Boleto, Gera_Boleto(bool)
```

---

## 4. O QUE PRECISA SER FEITO

Esta é a fase de construção da plataforma completa. Você tem a lógica validada, agora precisa transformar em aplicação real.

### 4.1 API Backend (sugestão: FastAPI + uvicorn + SQLAlchemy)
- `POST /rateio/calcular` — roda o motor para um Mes_Ano_Ref
- `GET /rateio/{mes_ano}` — consulta resultado consolidado
- `GET /rateio/{mes_ano}/eventos` — lista eventos rateados
- `GET /boletos/{mes_ano}` — lista boletos com filtros (por ID, categoria, status)
- `POST /rateio/{mes_ano}/replay` — simular recálculo sem gravar
- Validar idempotência (trava por Mes_Ano_Ref)
- Adaptador de leitura para dados reais (Supabase, PostgreSQL)

### 4.2 Web Frontend (sugestão: React/Next.js ou Vue)
- Dashboard com:
  - Visão geral do mês selecionado
  - Animacão dos 4 potinhos (igual o HTML demo)
  - Tabela de eventos rateados com filtros
  - Tabela de boletos com export CSV/XLSX
  - Detalhe do veículo com breakdown completo (auditoria)
- Autenticação (JWT)
- Responsivo (gestor mobile)
- Integração com backend API

### 4.3 Integração com Sistema Real
- Adaptador para ler dados do Supabase real do cliente (já temos conexão)
- Gerar eventos/sinistros reais
- Sincronizar inadimplência com banco
- Export de boletos para gateway de pagamento

### 4.4 Deploy
- Dockerizar tudo
- Configurar variáveis de ambiente
- Pipeline de CI/CD
- Monitoramento e logging

---

## 5. PREMISSAS E RESTRICOES

### Não alterar:
1. A lógica matemática dos 4 potinhos
2. A validação cruzada (diff = 0)
3. A priorização de eventos (data ASC, valor DESC)
4. O rateio parcial

### Parametrizáveis:
1. Valores dos degraus (14, 4, 18, 18)
2. Data de quebra (dia 25)
3. Dias de inadimplência (5)
4. Categorias de risco

---

## 6. STATUS ATUAL

✅ Motor de rateio rodando com dados simulados
✅ HTML demo interativo pronto (MotorRateio_Demo.html)
✅ Dados simulados gerados (10K veículos, 500 eventos)
✅ Planilhas de entrada e saída em xlsx
✅ PRD documentado
✅ Validação cruzada passando

⏳ API backend (não existe ainda)
⏳ Web frontend (não existe ainda)
⏳ Integração com Supabase real (não existe ainda)
⏳ Auth (não existe ainda)
⏳ Deploy containerizado (não existe ainda)

---

## 7. PRIMEIROS PASSOS SUGERIDOS

1. **Ler** `dados_simulados.json` para entender a estrutura real dos dados
2. **Rodar** `python3 rodar_motor_rateio.py` para ver o motor funcionando
3. **Propor** uma arquitetura detalhada (diretórios, tecnologias, endpoints)
4. **Implementar** backend primeiro (FastAPI com a lógica já validada)
5. **Testar** com dados simulados
6. **Montar** frontend conectando com a API
7. **Preparar** integração com o sistema real do cliente (Supabase)

---

Boa! Todo o contexto está aqui. O projeto está no `/home/ronaldim/Mut/`.
Os dados para simulação estão em `dados_simulados.json`.
O motor existente em `rodar_motor_rateio.py`.
O PRD em `PRD.md`.
