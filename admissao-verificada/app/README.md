# App — Admissão Verificada (Next.js 15 + Supabase)

Frontend e backend-for-frontend do MVP (ADR-001). As rotas autenticadas ficam
sob o segmento `/app/*`, protegidas por middleware. A RLS por claim
`associacao_id` no JWT (ADR-002 C2) isola o tenant.

## Estado

Fundação e a fatia vertical de referência (associados) implementadas. As
demais fatias (veículos, vistoria, situação de boleto, eventos, exportação)
seguem o mesmo padrão. Ainda NÃO foi feito `pnpm install` nem build; não roda
sem dependências e sem um projeto Supabase configurado.

## Estrutura

```
src/
  middleware.ts                  protege /app/*
  lib/
    supabase/{server,client}.ts  clientes (sessão do operador e service_role)
    validators/{cpf,placa}.ts    validações de domínio
    schemas/associado.ts         schema zod compartilhado
  app/
    layout.tsx, page.tsx         raiz (redireciona ao painel)
    login/page.tsx               login (Supabase Auth)
    app/                         rotas autenticadas (URL /app/*)
      layout.tsx                 navegação
      associados/{page,novo}     lista e cadastro (FATIA DE REFERÊNCIA)
    api/associados/route.ts      GET lista, POST cria (validação autoritativa)
```

## Padrão de uma fatia (para as próximas)

1. Validadores e schema zod em `lib/`.
2. Route handler em `app/api/<recurso>/route.ts`: checa sessão (401), valida
   payload (422), infere `associacao_id` do operador, deixa a RLS e as
   constraints garantirem isolamento e unicidade (409).
3. Página de lista (server component) e formulário (client component) sob
   `app/app/<recurso>/`.

## Rodar (quando houver ambiente)

```
cp .env.example .env   # preencher URL e chaves do Supabase
pnpm install
pnpm dev
```

Pré-requisitos no Supabase: aplicar as migrations (ver `../supabase`), registrar
o auth hook `custom_jwt_claims` e criar o bucket `vistorias`.
