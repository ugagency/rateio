-- Seed de desenvolvimento (não é migration de schema).
-- Cria uma associação de teste e a tabela de faixas de cota reproduzindo
-- exatamente cotas_por_fipe do motor (rules.py), conforme ADR-002 C5.

-- Associação de desenvolvimento (uuid fixo para facilitar testes).
insert into public.associacoes (id, nome, slug)
values ('00000000-0000-0000-0000-000000000001', 'Associação Demo', 'demo')
on conflict (id) do nothing;

-- Faixas de cota = espelho de cotas_por_fipe (rules.py):
--   FIPE até 10.000 -> 1,0 cota; +0,5 por faixa de 10.000; até 450.000.
--   Acima de 450.000 -> cota especial 20,0 (faixa com fipe_ate nulo).
-- Seleção: primeira faixa com fipe_ate >= fipe_valor; se nenhuma, a faixa nula.
insert into public.faixas_cota (associacao_id, fipe_ate, cota_valor, vigente_desde)
select
  '00000000-0000-0000-0000-000000000001',
  (g * 10000)::numeric(12,2),
  (1.0 + 0.5 * (g - 1))::numeric(10,2),
  date '2026-01-01'
from generate_series(1, 45) as g;

insert into public.faixas_cota (associacao_id, fipe_ate, cota_valor, vigente_desde)
values ('00000000-0000-0000-0000-000000000001', null, 20.0, date '2026-01-01');

-- Script de vistoria de exemplo (carro), com etapas mínimas em sequência.
insert into public.scripts_vistoria (id, associacao_id, tipo, descricao, tempo_max_min)
values ('00000000-0000-0000-0000-0000000000a1',
        '00000000-0000-0000-0000-000000000001',
        'carro', 'Vistoria de admissão de carro (demo)', 25)
on conflict (id) do nothing;

insert into public.etapas_script (script_id, sequencia, tipo_etapa, camera_preferencial, obrigatoria, instrucao_texto)
values
  ('00000000-0000-0000-0000-0000000000a1', 1, 'selfie', 'frontal', true, 'Selfie do executante com a placa ao fundo.'),
  ('00000000-0000-0000-0000-0000000000a1', 2, 'documento', 'traseira', true, 'Foto do documento do veículo.'),
  ('00000000-0000-0000-0000-0000000000a1', 3, 'frente', 'traseira', true, 'Frente do veículo.'),
  ('00000000-0000-0000-0000-0000000000a1', 4, 'lateral_esquerda', 'traseira', true, 'Lateral esquerda.'),
  ('00000000-0000-0000-0000-0000000000a1', 5, 'lateral_direita', 'traseira', true, 'Lateral direita.'),
  ('00000000-0000-0000-0000-0000000000a1', 6, 'traseira', 'traseira', true, 'Traseira do veículo.')
on conflict (script_id, sequencia) do nothing;
