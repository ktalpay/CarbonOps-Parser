CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE SCHEMA IF NOT EXISTS carbonops;

CREATE TABLE IF NOT EXISTS carbonops.carbon_sources (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_code TEXT NOT NULL UNIQUE,
    source_name TEXT NOT NULL,
    provider_name TEXT,
    source_home_url TEXT,
    is_enabled BOOLEAN NOT NULL DEFAULT TRUE,
    metadata_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS carbonops.carbon_source_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_id UUID NOT NULL REFERENCES carbonops.carbon_sources(id),
    version_key TEXT NOT NULL,
    published_at TIMESTAMPTZ,
    check_url TEXT,
    download_url TEXT,
    source_hash TEXT,
    metadata_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_carbon_source_versions_source_version UNIQUE (source_id, version_key)
);

CREATE TABLE IF NOT EXISTS carbonops.carbon_import_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_id UUID NOT NULL REFERENCES carbonops.carbon_sources(id),
    source_version_id UUID REFERENCES carbonops.carbon_source_versions(id),
    status TEXT NOT NULL,
    started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    total_rows INTEGER NOT NULL DEFAULT 0,
    valid_rows INTEGER NOT NULL DEFAULT 0,
    warning_rows INTEGER NOT NULL DEFAULT 0,
    error_rows INTEGER NOT NULL DEFAULT 0,
    skipped_rows INTEGER NOT NULL DEFAULT 0,
    raw_file_sha256 TEXT,
    error_message TEXT,
    metadata_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS carbonops.carbon_raw_files (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_id UUID NOT NULL REFERENCES carbonops.carbon_sources(id),
    source_version_id UUID REFERENCES carbonops.carbon_source_versions(id),
    import_run_id UUID REFERENCES carbonops.carbon_import_runs(id),
    file_name TEXT NOT NULL,
    file_path TEXT NOT NULL,
    content_type TEXT,
    size_bytes BIGINT,
    sha256 TEXT NOT NULL,
    downloaded_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_carbon_raw_files_source_sha256 UNIQUE (source_id, sha256)
);

CREATE TABLE IF NOT EXISTS carbonops.carbon_validation_issues (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    import_run_id UUID NOT NULL REFERENCES carbonops.carbon_import_runs(id),
    source_code TEXT NOT NULL,
    table_name TEXT,
    record_id UUID,
    source_row_reference TEXT,
    severity TEXT NOT NULL,
    code TEXT NOT NULL,
    field_name TEXT,
    raw_value TEXT,
    message TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS carbonops.carbon_job_locks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_code TEXT NOT NULL,
    lock_key TEXT NOT NULL,
    locked_until TIMESTAMPTZ NOT NULL,
    locked_by TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_carbon_job_locks_source_lock UNIQUE (source_code, lock_key)
);

CREATE TABLE IF NOT EXISTS carbonops.source_family_year_states (
    source_family_year_state_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_family TEXT NOT NULL,
    ingested_year INTEGER NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_source_family_year_states_family_year UNIQUE (source_family, ingested_year)
);

CREATE INDEX IF NOT EXISTS idx_source_family_year_states_family_year
    ON carbonops.source_family_year_states (source_family, ingested_year);

CREATE TABLE IF NOT EXISTS carbonops.defra_categories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_version_id UUID NOT NULL REFERENCES carbonops.carbon_source_versions(id),
    category_code TEXT,
    category_name TEXT NOT NULL,
    sort_order INTEGER,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS carbonops.defra_subcategories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    category_id UUID NOT NULL REFERENCES carbonops.defra_categories(id),
    subcategory_code TEXT,
    subcategory_name TEXT NOT NULL,
    sort_order INTEGER,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS carbonops.defra_factor_sets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_version_id UUID NOT NULL REFERENCES carbonops.carbon_source_versions(id),
    category_id UUID REFERENCES carbonops.defra_categories(id),
    subcategory_id UUID REFERENCES carbonops.defra_subcategories(id),
    activity_name TEXT NOT NULL,
    activity_description TEXT,
    scope_hint TEXT,
    region TEXT,
    year INTEGER,
    source_sheet_name TEXT,
    source_row_reference TEXT,
    metadata_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS carbonops.defra_factor_values (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    factor_set_id UUID NOT NULL REFERENCES carbonops.defra_factor_sets(id),
    gas TEXT,
    factor_value NUMERIC,
    factor_unit TEXT,
    activity_unit TEXT,
    conversion_factor_type TEXT,
    quality_flag TEXT,
    notes TEXT,
    metadata_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS carbonops.ghg_tools (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_version_id UUID NOT NULL REFERENCES carbonops.carbon_source_versions(id),
    tool_code TEXT,
    tool_name TEXT NOT NULL,
    description TEXT,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS carbonops.ghg_factor_sheets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tool_id UUID NOT NULL REFERENCES carbonops.ghg_tools(id),
    sheet_name TEXT NOT NULL,
    sheet_type TEXT,
    header_row_index INTEGER,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS carbonops.ghg_factor_groups (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_version_id UUID NOT NULL REFERENCES carbonops.carbon_source_versions(id),
    tool_id UUID REFERENCES carbonops.ghg_tools(id),
    sheet_id UUID REFERENCES carbonops.ghg_factor_sheets(id),
    group_name TEXT,
    category_name TEXT,
    subcategory_name TEXT,
    region TEXT,
    year INTEGER,
    source_row_reference TEXT,
    metadata_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS carbonops.ghg_factor_values (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    factor_group_id UUID NOT NULL REFERENCES carbonops.ghg_factor_groups(id),
    activity_name TEXT,
    activity_description TEXT,
    fuel_or_material TEXT,
    gas TEXT,
    factor_value NUMERIC,
    factor_unit TEXT,
    activity_unit TEXT,
    co2e_factor_value NUMERIC,
    notes TEXT,
    metadata_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS carbonops.ipcc_sectors (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_version_id UUID NOT NULL REFERENCES carbonops.carbon_source_versions(id),
    sector_code TEXT,
    sector_name TEXT NOT NULL,
    parent_sector_id UUID REFERENCES carbonops.ipcc_sectors(id),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS carbonops.ipcc_categories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    sector_id UUID NOT NULL REFERENCES carbonops.ipcc_sectors(id),
    category_code TEXT,
    category_name TEXT NOT NULL,
    parent_category_id UUID REFERENCES carbonops.ipcc_categories(id),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS carbonops.ipcc_references (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_version_id UUID NOT NULL REFERENCES carbonops.carbon_source_versions(id),
    reference_title TEXT,
    authors TEXT,
    publication_year INTEGER,
    publisher TEXT,
    reference_type TEXT,
    url TEXT,
    metadata_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS carbonops.ipcc_factor_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_version_id UUID NOT NULL REFERENCES carbonops.carbon_source_versions(id),
    sector_id UUID REFERENCES carbonops.ipcc_sectors(id),
    category_id UUID REFERENCES carbonops.ipcc_categories(id),
    reference_id UUID REFERENCES carbonops.ipcc_references(id),
    parameter_name TEXT,
    activity_name TEXT,
    technology_or_practice TEXT,
    region TEXT,
    country TEXT,
    gas TEXT,
    unit TEXT,
    source_row_reference TEXT,
    metadata_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS carbonops.ipcc_factor_values (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    factor_record_id UUID NOT NULL REFERENCES carbonops.ipcc_factor_records(id),
    factor_value NUMERIC,
    min_value NUMERIC,
    max_value NUMERIC,
    default_value NUMERIC,
    uncertainty TEXT,
    data_quality TEXT,
    notes TEXT,
    metadata_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_carbon_sources_source_code
    ON carbonops.carbon_sources (source_code);

CREATE INDEX IF NOT EXISTS idx_carbon_source_versions_source_id
    ON carbonops.carbon_source_versions (source_id);

CREATE INDEX IF NOT EXISTS idx_carbon_source_versions_source_hash
    ON carbonops.carbon_source_versions (source_hash);

CREATE INDEX IF NOT EXISTS idx_carbon_import_runs_source_id
    ON carbonops.carbon_import_runs (source_id);

CREATE INDEX IF NOT EXISTS idx_carbon_import_runs_source_version_id
    ON carbonops.carbon_import_runs (source_version_id);

CREATE INDEX IF NOT EXISTS idx_carbon_raw_files_source_id
    ON carbonops.carbon_raw_files (source_id);

CREATE INDEX IF NOT EXISTS idx_carbon_raw_files_source_version_id
    ON carbonops.carbon_raw_files (source_version_id);

CREATE INDEX IF NOT EXISTS idx_carbon_raw_files_import_run_id
    ON carbonops.carbon_raw_files (import_run_id);

CREATE INDEX IF NOT EXISTS idx_carbon_validation_issues_import_run_id
    ON carbonops.carbon_validation_issues (import_run_id);

CREATE INDEX IF NOT EXISTS idx_carbon_validation_issues_source_code
    ON carbonops.carbon_validation_issues (source_code);

CREATE INDEX IF NOT EXISTS idx_carbon_validation_issues_source_row_reference
    ON carbonops.carbon_validation_issues (source_row_reference);

CREATE INDEX IF NOT EXISTS idx_carbon_job_locks_source_code
    ON carbonops.carbon_job_locks (source_code);

CREATE INDEX IF NOT EXISTS idx_defra_categories_source_version_id
    ON carbonops.defra_categories (source_version_id);

CREATE INDEX IF NOT EXISTS idx_defra_categories_category_name
    ON carbonops.defra_categories (category_name);

CREATE INDEX IF NOT EXISTS idx_defra_subcategories_category_id
    ON carbonops.defra_subcategories (category_id);

CREATE INDEX IF NOT EXISTS idx_defra_subcategories_subcategory_name
    ON carbonops.defra_subcategories (subcategory_name);

CREATE INDEX IF NOT EXISTS idx_defra_factor_sets_source_version_id
    ON carbonops.defra_factor_sets (source_version_id);

CREATE INDEX IF NOT EXISTS idx_defra_factor_sets_category_id
    ON carbonops.defra_factor_sets (category_id);

CREATE INDEX IF NOT EXISTS idx_defra_factor_sets_subcategory_id
    ON carbonops.defra_factor_sets (subcategory_id);

CREATE INDEX IF NOT EXISTS idx_defra_factor_sets_activity_name
    ON carbonops.defra_factor_sets (activity_name);

CREATE INDEX IF NOT EXISTS idx_defra_factor_sets_region_year
    ON carbonops.defra_factor_sets (region, year);

CREATE INDEX IF NOT EXISTS idx_defra_factor_sets_source_row_reference
    ON carbonops.defra_factor_sets (source_row_reference);

CREATE INDEX IF NOT EXISTS idx_defra_factor_values_factor_set_id
    ON carbonops.defra_factor_values (factor_set_id);

CREATE INDEX IF NOT EXISTS idx_defra_factor_values_gas
    ON carbonops.defra_factor_values (gas);

CREATE INDEX IF NOT EXISTS idx_ghg_tools_source_version_id
    ON carbonops.ghg_tools (source_version_id);

CREATE INDEX IF NOT EXISTS idx_ghg_tools_tool_name
    ON carbonops.ghg_tools (tool_name);

CREATE INDEX IF NOT EXISTS idx_ghg_factor_sheets_tool_id
    ON carbonops.ghg_factor_sheets (tool_id);

CREATE INDEX IF NOT EXISTS idx_ghg_factor_sheets_sheet_name
    ON carbonops.ghg_factor_sheets (sheet_name);

CREATE INDEX IF NOT EXISTS idx_ghg_factor_groups_source_version_id
    ON carbonops.ghg_factor_groups (source_version_id);

CREATE INDEX IF NOT EXISTS idx_ghg_factor_groups_tool_id
    ON carbonops.ghg_factor_groups (tool_id);

CREATE INDEX IF NOT EXISTS idx_ghg_factor_groups_sheet_id
    ON carbonops.ghg_factor_groups (sheet_id);

CREATE INDEX IF NOT EXISTS idx_ghg_factor_groups_category_name
    ON carbonops.ghg_factor_groups (category_name);

CREATE INDEX IF NOT EXISTS idx_ghg_factor_groups_region_year
    ON carbonops.ghg_factor_groups (region, year);

CREATE INDEX IF NOT EXISTS idx_ghg_factor_groups_source_row_reference
    ON carbonops.ghg_factor_groups (source_row_reference);

CREATE INDEX IF NOT EXISTS idx_ghg_factor_values_factor_group_id
    ON carbonops.ghg_factor_values (factor_group_id);

CREATE INDEX IF NOT EXISTS idx_ghg_factor_values_activity_name
    ON carbonops.ghg_factor_values (activity_name);

CREATE INDEX IF NOT EXISTS idx_ghg_factor_values_gas
    ON carbonops.ghg_factor_values (gas);

CREATE INDEX IF NOT EXISTS idx_ipcc_sectors_source_version_id
    ON carbonops.ipcc_sectors (source_version_id);

CREATE INDEX IF NOT EXISTS idx_ipcc_sectors_sector_name
    ON carbonops.ipcc_sectors (sector_name);

CREATE INDEX IF NOT EXISTS idx_ipcc_sectors_parent_sector_id
    ON carbonops.ipcc_sectors (parent_sector_id);

CREATE INDEX IF NOT EXISTS idx_ipcc_categories_sector_id
    ON carbonops.ipcc_categories (sector_id);

CREATE INDEX IF NOT EXISTS idx_ipcc_categories_category_name
    ON carbonops.ipcc_categories (category_name);

CREATE INDEX IF NOT EXISTS idx_ipcc_categories_parent_category_id
    ON carbonops.ipcc_categories (parent_category_id);

CREATE INDEX IF NOT EXISTS idx_ipcc_references_source_version_id
    ON carbonops.ipcc_references (source_version_id);

CREATE INDEX IF NOT EXISTS idx_ipcc_factor_records_source_version_id
    ON carbonops.ipcc_factor_records (source_version_id);

CREATE INDEX IF NOT EXISTS idx_ipcc_factor_records_sector_id
    ON carbonops.ipcc_factor_records (sector_id);

CREATE INDEX IF NOT EXISTS idx_ipcc_factor_records_category_id
    ON carbonops.ipcc_factor_records (category_id);

CREATE INDEX IF NOT EXISTS idx_ipcc_factor_records_reference_id
    ON carbonops.ipcc_factor_records (reference_id);

CREATE INDEX IF NOT EXISTS idx_ipcc_factor_records_activity_name
    ON carbonops.ipcc_factor_records (activity_name);

CREATE INDEX IF NOT EXISTS idx_ipcc_factor_records_region_country
    ON carbonops.ipcc_factor_records (region, country);

CREATE INDEX IF NOT EXISTS idx_ipcc_factor_records_gas
    ON carbonops.ipcc_factor_records (gas);

CREATE INDEX IF NOT EXISTS idx_ipcc_factor_records_source_row_reference
    ON carbonops.ipcc_factor_records (source_row_reference);

CREATE INDEX IF NOT EXISTS idx_ipcc_factor_values_factor_record_id
    ON carbonops.ipcc_factor_values (factor_record_id);
