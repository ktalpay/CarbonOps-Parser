CREATE TABLE ingestion_runs (
    ingestion_run_id uuid NOT NULL,
    run_status text NOT NULL,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    CONSTRAINT pk_ingestion_runs PRIMARY KEY (ingestion_run_id)
);

CREATE INDEX idx_ingestion_runs_run_status ON ingestion_runs (run_status);

CREATE TABLE source_documents (
    source_document_id uuid NOT NULL,
    ingestion_run_id uuid NOT NULL,
    source_family text NOT NULL,
    source_document_uri text NOT NULL,
    source_checksum_sha256 text NOT NULL,
    acquisition_status text NOT NULL,
    acquired_at timestamp with time zone,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    CONSTRAINT pk_source_documents PRIMARY KEY (source_document_id),
    CONSTRAINT uq_source_documents_family_uri_checksum UNIQUE (source_family, source_document_uri, source_checksum_sha256),
    CONSTRAINT fk_source_documents_ingestion_run_id FOREIGN KEY (ingestion_run_id) REFERENCES ingestion_runs (ingestion_run_id)
);

CREATE INDEX idx_source_documents_ingestion_run_id ON source_documents (ingestion_run_id);

CREATE TABLE parser_runs (
    parser_run_id uuid NOT NULL,
    source_document_id uuid NOT NULL,
    parser_status text NOT NULL,
    error_details jsonb,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    CONSTRAINT pk_parser_runs PRIMARY KEY (parser_run_id),
    CONSTRAINT fk_parser_runs_source_document_id FOREIGN KEY (source_document_id) REFERENCES source_documents (source_document_id)
);

CREATE INDEX idx_parser_runs_source_document_id ON parser_runs (source_document_id);

CREATE TABLE schema_bootstrap_states (
    schema_bootstrap_state_id uuid NOT NULL,
    schema_contract_version text NOT NULL,
    bootstrap_status text NOT NULL,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    CONSTRAINT pk_schema_bootstrap_states PRIMARY KEY (schema_bootstrap_state_id),
    CONSTRAINT uq_schema_bootstrap_states_contract_version UNIQUE (schema_contract_version)
);

CREATE TABLE source_family_year_states (
    source_family_year_state_id uuid NOT NULL,
    source_family text NOT NULL,
    ingested_year integer NOT NULL,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    CONSTRAINT pk_source_family_year_states PRIMARY KEY (source_family_year_state_id),
    CONSTRAINT uq_source_family_year_states_family_year UNIQUE (source_family, ingested_year)
);

CREATE INDEX idx_source_family_year_states_family_year ON source_family_year_states (source_family, ingested_year);

CREATE TABLE ghg_emission_factor_masters (
    ghg_emission_factor_master_id uuid NOT NULL,
    source_document_id uuid NOT NULL,
    master_external_key text NOT NULL,
    lifecycle_status text NOT NULL,
    effective_from timestamp with time zone,
    effective_to timestamp with time zone,
    record_checksum_sha256 text NOT NULL,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    CONSTRAINT pk_ghg_emission_factor_masters PRIMARY KEY (ghg_emission_factor_master_id),
    CONSTRAINT uq_ghg_emission_factor_masters_external_key UNIQUE (master_external_key),
    CONSTRAINT fk_ghg_emission_factor_masters_source_document_id FOREIGN KEY (source_document_id) REFERENCES source_documents (source_document_id)
);

CREATE TABLE ghg_emission_factor_details (
    ghg_emission_factor_detail_id uuid NOT NULL,
    ghg_emission_factor_master_id uuid NOT NULL,
    detail_external_key text NOT NULL,
    factor_value numeric NOT NULL,
    factor_unit text NOT NULL,
    lifecycle_status text NOT NULL,
    record_checksum_sha256 text NOT NULL,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    CONSTRAINT pk_ghg_emission_factor_details PRIMARY KEY (ghg_emission_factor_detail_id),
    CONSTRAINT uq_ghg_emission_factor_details_master_detail_external_key UNIQUE (ghg_emission_factor_master_id, detail_external_key),
    CONSTRAINT fk_ghg_emission_factor_details_ghg_emission_factor_master_id FOREIGN KEY (ghg_emission_factor_master_id) REFERENCES ghg_emission_factor_masters (ghg_emission_factor_master_id)
);

CREATE INDEX idx_ghg_emission_factor_details_ghg_emission_factor_master_id ON ghg_emission_factor_details (ghg_emission_factor_master_id);

CREATE TABLE defra_emission_factor_masters (
    defra_emission_factor_master_id uuid NOT NULL,
    source_document_id uuid NOT NULL,
    master_external_key text NOT NULL,
    lifecycle_status text NOT NULL,
    effective_from timestamp with time zone,
    effective_to timestamp with time zone,
    record_checksum_sha256 text NOT NULL,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    CONSTRAINT pk_defra_emission_factor_masters PRIMARY KEY (defra_emission_factor_master_id),
    CONSTRAINT uq_defra_emission_factor_masters_external_key UNIQUE (master_external_key),
    CONSTRAINT fk_defra_emission_factor_masters_source_document_id FOREIGN KEY (source_document_id) REFERENCES source_documents (source_document_id)
);

CREATE TABLE defra_emission_factor_details (
    defra_emission_factor_detail_id uuid NOT NULL,
    defra_emission_factor_master_id uuid NOT NULL,
    detail_external_key text NOT NULL,
    factor_value numeric NOT NULL,
    factor_unit text NOT NULL,
    lifecycle_status text NOT NULL,
    record_checksum_sha256 text NOT NULL,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    CONSTRAINT pk_defra_emission_factor_details PRIMARY KEY (defra_emission_factor_detail_id),
    CONSTRAINT uq_defra_emission_factor_details_master_detail_external_key UNIQUE (defra_emission_factor_master_id, detail_external_key),
    CONSTRAINT fk_defra_emission_factor_details_defra_emission_fa_98fe08fa20f4 FOREIGN KEY (defra_emission_factor_master_id) REFERENCES defra_emission_factor_masters (defra_emission_factor_master_id)
);

CREATE INDEX idx_defra_emission_factor_details_defra_emission_f_532bf4e61faf ON defra_emission_factor_details (defra_emission_factor_master_id);

CREATE TABLE ipcc_emission_factor_masters (
    ipcc_emission_factor_master_id uuid NOT NULL,
    source_document_id uuid NOT NULL,
    master_external_key text NOT NULL,
    lifecycle_status text NOT NULL,
    effective_from timestamp with time zone,
    effective_to timestamp with time zone,
    record_checksum_sha256 text NOT NULL,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    CONSTRAINT pk_ipcc_emission_factor_masters PRIMARY KEY (ipcc_emission_factor_master_id),
    CONSTRAINT uq_ipcc_emission_factor_masters_external_key UNIQUE (master_external_key),
    CONSTRAINT fk_ipcc_emission_factor_masters_source_document_id FOREIGN KEY (source_document_id) REFERENCES source_documents (source_document_id)
);

CREATE TABLE ipcc_emission_factor_details (
    ipcc_emission_factor_detail_id uuid NOT NULL,
    ipcc_emission_factor_master_id uuid NOT NULL,
    detail_external_key text NOT NULL,
    factor_value numeric NOT NULL,
    factor_unit text NOT NULL,
    lifecycle_status text NOT NULL,
    record_checksum_sha256 text NOT NULL,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    CONSTRAINT pk_ipcc_emission_factor_details PRIMARY KEY (ipcc_emission_factor_detail_id),
    CONSTRAINT uq_ipcc_emission_factor_details_master_detail_external_key UNIQUE (ipcc_emission_factor_master_id, detail_external_key),
    CONSTRAINT fk_ipcc_emission_factor_details_ipcc_emission_factor_master_id FOREIGN KEY (ipcc_emission_factor_master_id) REFERENCES ipcc_emission_factor_masters (ipcc_emission_factor_master_id)
);

CREATE INDEX idx_ipcc_emission_factor_details_ipcc_emission_factor_master_id ON ipcc_emission_factor_details (ipcc_emission_factor_master_id);
