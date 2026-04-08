DROP TYPE IF EXISTS col_name_status;
DROP TYPE IF EXISTS col_taxon_rank;

CREATE TYPE col_name_status AS ENUM (
  'accepted',
  'ambiguous synonym',
  'misapplied',
  'provisionally accepted',
  'synonym'
);

CREATE TYPE col_taxon_rank AS ENUM (
  'aberration',
  'class',
  'domain',
  'epifamily',
  'family',
  'form',
  'forma specialis',
  'genus',
  'gigaclass',
  'infraclass',
  'infrafamily',
  'infrageneric name',
  'infrakingdom',
  'infraphylum',
  'infraorder',
  'infraspecific name',
  'infrasubspecific name',
  'infratribe',
  'kingdom',
  'lusus',
  'megaclass',
  'morph',
  'mutatio',
  'nanorder',
  'natio',
  'order',
  'other',
  'parvorder',
  'parvphylum',
  'phylum',
  'proles',
  'realm',
  'section botany',
  'section zoology',
  'series',
  'species',
  'species aggregate',
  'subclass',
  'subfamily',
  'subform',
  'subgenus',
  'subkingdom',
  'suborder',
  'subphylum',
  'subsection botany',
  'subsection zoology',
  'subspecies',
  'subterclass',
  'subtribe',
  'subvariety',
  'superclass',
  'superfamily',
  'superorder',
  'supertribe',
  'tribe',
  'unranked',
  'variety'
);

DROP TABLE IF EXISTS col_name_usage;

CREATE TABLE col_name_usage (
  id VARCHAR PRIMARY KEY CHECK (length(id) > 0),
  parent_id VARCHAR,
  basionym_id VARCHAR,
  status col_name_status NOT NULL,
  rank col_taxon_rank,
  scientific_name VARCHAR NOT NULL CHECK (length(scientific_name) > 0),
  authorship VARCHAR,
  source_id VARCHAR,
  extinct BOOLEAN,
  canonical_id VARCHAR NOT NULL CHECK (length(canonical_id) > 0),
  canonical_scientific_name VARCHAR NOT NULL CHECK (length(canonical_scientific_name) > 0)
);

DROP TABLE IF EXISTS col_name_hierarchy;

CREATE TABLE col_name_hierarchy (
  parent_id VARCHAR NOT NULL CHECK (length(parent_id) > 0),
  child_id VARCHAR NOT NULL CHECK (length(child_id) > 0),
  PRIMARY KEY (parent_id, child_id)
);
