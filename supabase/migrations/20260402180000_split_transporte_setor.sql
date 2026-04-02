-- session-035: Split setor "transporte" em "transporte_servicos" + "frota_veicular"
-- Atualiza alertas que usavam o setor antigo para o novo setor de serviços (mais próximo)
UPDATE alerts
SET filters = jsonb_set(filters, '{setor}', '"transporte_servicos"')
WHERE filters->>'setor' = 'transporte';
