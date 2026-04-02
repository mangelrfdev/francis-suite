-- Example data for Estación Inmobiliaria `public.properties`.
-- Schema source of truth (web repo): `supabase/migrations/20260401100000_properties.sql`
--   (+ optional `last_ingestion_run_id` from `20260401120000_ingestion_runs.sql`).
-- Run in Supabase SQL Editor (bypasses RLS for manual runs).
--
-- HOW THIS CONNECTS TO THE SITE + ADMIN
-- - Same table the Next app reads; `source = 'demo_seed'` marks demo rows.
-- - Remove demo rows: DELETE FROM public.properties WHERE source = 'demo_seed';

-- Optional: insert a row in `ingestion_runs` first, then set `last_ingestion_run_id` on properties
-- if you want lineage in admin (see second migration).

INSERT INTO public.properties (
  source,
  external_id,
  title,
  price,
  currency,
  property_type,
  operation_type,
  comuna,
  bedrooms,
  bathrooms,
  surface,
  image_url,
  source_url
) VALUES
(
  'demo_seed',
  'demo-001',
  'Depto ejemplo Las Condes',
  450000,
  'CLP',
  'departamento',
  'arriendo',
  'Las Condes',
  2,
  2,
  85,
  'https://example.com/img/demo-001.jpg',
  'https://example.com/listings/demo-001'
),
(
  'demo_seed',
  'demo-002',
  'Casa ejemplo Ñuñoa',
  12000.5,
  'UF',
  'casa',
  'venta',
  'Ñuñoa',
  3,
  2,
  120,
  'https://example.com/img/demo-002.jpg',
  'https://example.com/listings/demo-002'
)
ON CONFLICT (source, external_id) DO NOTHING;
