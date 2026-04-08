.read '{SCHEMA_SQL_PATH}'

CREATE TEMP TABLE raw_name_usage AS
SELECT
  NULLIF("col:ID", '') AS id,
  NULLIF("col:parentID", '') AS parent_id,
  NULLIF("col:basionymID", '') AS basionym_id,
  trim(lower(NULLIF("col:status", ''))) AS status,
  trim(lower(NULLIF("col:rank", ''))) AS rank,
  NULLIF("col:scientificName", '') AS scientific_name,
  NULLIF("col:authorship", '') AS authorship,
  NULLIF("col:sourceID", '') AS source_id,
  CASE
    WHEN lower(NULLIF("col:extinct", '')) = 'true' THEN true
    WHEN lower(NULLIF("col:extinct", '')) = 'false' THEN false
    ELSE NULL
  END AS extinct
FROM read_csv(
  '{NAME_USAGE_PATH}',
  delim='\t',
  header=true,
  all_varchar=true,
  quote=''
);

INSERT INTO col_name_usage (
  id,
  parent_id,
  basionym_id,
  status,
  rank,
  scientific_name,
  authorship,
  source_id,
  extinct,
  canonical_id,
  canonical_scientific_name
)
WITH normalized AS (
  SELECT
    id,
    parent_id,
    basionym_id,
    status,
    rank,
    scientific_name,
    authorship,
    source_id,
    extinct
  FROM raw_name_usage
  WHERE id IS NOT NULL AND scientific_name IS NOT NULL
),
resolved AS (
  SELECT
    n.*,
    CASE
      WHEN n.status IN ('accepted', 'provisionally accepted') THEN n.id
      WHEN n.parent_id IS NOT NULL AND p.status IN ('accepted', 'provisionally accepted') THEN n.parent_id
      ELSE n.id
    END AS canonical_id
  FROM normalized n
  LEFT JOIN normalized p
    ON p.id = n.parent_id
)
SELECT
  r.id,
  r.parent_id,
  r.basionym_id,
  r.status::col_name_status,
  CASE
    WHEN r.rank IS NULL THEN NULL
    ELSE r.rank::col_taxon_rank
  END AS rank,
  r.scientific_name,
  r.authorship,
  r.source_id,
  r.extinct,
  r.canonical_id,
  COALESCE(c.scientific_name, r.scientific_name) AS canonical_scientific_name
FROM resolved r
LEFT JOIN normalized c
  ON c.id = r.canonical_id;

CREATE INDEX col_name_usage_scientific_name_idx ON col_name_usage(scientific_name);
CREATE INDEX col_name_usage_canonical_scientific_name_idx ON col_name_usage(canonical_scientific_name);
CREATE INDEX col_name_usage_canonical_id_idx ON col_name_usage(canonical_id);
CREATE INDEX col_name_usage_parent_id_idx ON col_name_usage(parent_id);
