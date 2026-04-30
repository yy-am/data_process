CREATE TABLE IF NOT EXISTS dp_task (
    task_id UUID PRIMARY KEY,
    input_type VARCHAR(32) NOT NULL,
    status VARCHAR(64) NOT NULL,
    current_stage VARCHAR(64) NOT NULL,
    current_rule_version INTEGER NOT NULL DEFAULT 0,
    current_result_version INTEGER NOT NULL DEFAULT 0,
    template_code VARCHAR(128),
    rule_code VARCHAR(128),
    scene_code VARCHAR(128),
    country_code VARCHAR(64),
    source_fix_required BOOLEAN NOT NULL DEFAULT FALSE,
    error_code VARCHAR(128),
    error_message TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS dp_task_file (
    task_file_id UUID PRIMARY KEY,
    task_id UUID NOT NULL REFERENCES dp_task(task_id),
    original_filename TEXT NOT NULL,
    stored_filename TEXT NOT NULL,
    content_type VARCHAR(255) NOT NULL,
    file_size BIGINT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS dp_input_snapshot (
    snapshot_id UUID PRIMARY KEY,
    task_id UUID NOT NULL REFERENCES dp_task(task_id),
    snapshot_version INTEGER NOT NULL,
    input_type VARCHAR(32) NOT NULL,
    snapshot_json JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (task_id, snapshot_version)
);

CREATE TABLE IF NOT EXISTS dp_sheet_snapshot (
    sheet_snapshot_id UUID PRIMARY KEY,
    task_id UUID NOT NULL REFERENCES dp_task(task_id),
    snapshot_version INTEGER NOT NULL,
    sheet_name TEXT NOT NULL,
    headers_json JSONB NOT NULL,
    normalized_headers_json JSONB NOT NULL,
    sample_rows_json JSONB NOT NULL,
    column_stats_json JSONB NOT NULL,
    header_confidence_json JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS dp_template_retrieval_result (
    retrieval_result_id UUID PRIMARY KEY,
    task_id UUID NOT NULL REFERENCES dp_task(task_id),
    snapshot_version INTEGER NOT NULL,
    template_code VARCHAR(128) NOT NULL,
    score NUMERIC(8, 4) NOT NULL,
    score_detail_json JSONB NOT NULL,
    rank_no INTEGER NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS dp_rule_retrieval_result (
    retrieval_result_id UUID PRIMARY KEY,
    task_id UUID NOT NULL REFERENCES dp_task(task_id),
    snapshot_version INTEGER NOT NULL,
    rule_code VARCHAR(128) NOT NULL,
    score NUMERIC(8, 4) NOT NULL,
    score_detail_json JSONB NOT NULL,
    rank_no INTEGER NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS dp_rule_draft (
    rule_draft_id UUID PRIMARY KEY,
    task_id UUID NOT NULL REFERENCES dp_task(task_id),
    draft_version INTEGER NOT NULL,
    template_code VARCHAR(128),
    rule_code VARCHAR(128),
    scene_code VARCHAR(128),
    country_code VARCHAR(64),
    draft_dsl_json JSONB NOT NULL,
    ambiguous_mappings_json JSONB NOT NULL,
    missing_fields_json JSONB NOT NULL,
    default_suggestions_json JSONB NOT NULL,
    blocking_issues_json JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (task_id, draft_version)
);

CREATE TABLE IF NOT EXISTS dp_confirmation_package (
    confirmation_package_id UUID PRIMARY KEY,
    task_id UUID NOT NULL REFERENCES dp_task(task_id),
    package_version INTEGER NOT NULL,
    package_json JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (task_id, package_version)
);

CREATE TABLE IF NOT EXISTS dp_confirmation_result (
    confirmation_result_id UUID PRIMARY KEY,
    task_id UUID NOT NULL REFERENCES dp_task(task_id),
    package_version INTEGER NOT NULL,
    result_json JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS dp_effective_rule (
    effective_rule_id UUID PRIMARY KEY,
    task_id UUID NOT NULL REFERENCES dp_task(task_id),
    rule_version INTEGER NOT NULL,
    template_code VARCHAR(128) NOT NULL,
    rule_code VARCHAR(128) NOT NULL,
    effective_dsl_json JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (task_id, rule_version)
);

CREATE TABLE IF NOT EXISTS kb_template (
    template_code VARCHAR(128) PRIMARY KEY,
    template_name VARCHAR(255) NOT NULL,
    source_type VARCHAR(32) NOT NULL,
    status VARCHAR(32) NOT NULL,
    description TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS kb_template_field (
    template_field_id UUID PRIMARY KEY,
    template_code VARCHAR(128) NOT NULL REFERENCES kb_template(template_code),
    field_code VARCHAR(128) NOT NULL,
    field_name VARCHAR(255) NOT NULL,
    data_type VARCHAR(64) NOT NULL,
    required BOOLEAN NOT NULL DEFAULT FALSE,
    sort_order INTEGER NOT NULL DEFAULT 0,
    UNIQUE (template_code, field_code)
);

CREATE TABLE IF NOT EXISTS kb_template_header_alias (
    template_header_alias_id UUID PRIMARY KEY,
    template_code VARCHAR(128) NOT NULL REFERENCES kb_template(template_code),
    field_code VARCHAR(128) NOT NULL,
    header_alias TEXT NOT NULL,
    normalized_alias TEXT NOT NULL,
    language VARCHAR(32),
    country_code VARCHAR(64),
    priority INTEGER NOT NULL DEFAULT 0,
    confidence NUMERIC(8, 4) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS kb_template_example (
    template_example_id UUID PRIMARY KEY,
    template_code VARCHAR(128) NOT NULL REFERENCES kb_template(template_code),
    example_name VARCHAR(255) NOT NULL,
    example_headers_json JSONB NOT NULL,
    example_rows_json JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS kb_mapping_rule (
    rule_code VARCHAR(128) PRIMARY KEY,
    rule_name VARCHAR(255) NOT NULL,
    scene_code VARCHAR(128) NOT NULL,
    country_code VARCHAR(64) NOT NULL,
    template_code VARCHAR(128) NOT NULL REFERENCES kb_template(template_code),
    source_type VARCHAR(32) NOT NULL,
    status VARCHAR(32) NOT NULL,
    priority INTEGER NOT NULL DEFAULT 0,
    mapping_dsl_json JSONB NOT NULL,
    rule_summary_text TEXT,
    version INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS kb_rule_mapping_item (
    rule_mapping_item_id UUID PRIMARY KEY,
    rule_code VARCHAR(128) NOT NULL REFERENCES kb_mapping_rule(rule_code),
    target_field_code VARCHAR(128) NOT NULL,
    transform_type VARCHAR(64) NOT NULL,
    config_json JSONB NOT NULL,
    sort_order INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS kb_rule_example (
    rule_example_id UUID PRIMARY KEY,
    rule_code VARCHAR(128) NOT NULL REFERENCES kb_mapping_rule(rule_code),
    example_name VARCHAR(255) NOT NULL,
    source_sample_json JSONB NOT NULL,
    target_sample_json JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS dp_staging_result (
    staging_result_id UUID PRIMARY KEY,
    task_id UUID NOT NULL REFERENCES dp_task(task_id),
    result_version INTEGER NOT NULL,
    row_no INTEGER NOT NULL,
    source_row_ref JSONB NOT NULL,
    target_data_json JSONB NOT NULL,
    validation_status VARCHAR(32) NOT NULL,
    warning_flags_json JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (task_id, result_version, row_no)
);

CREATE TABLE IF NOT EXISTS dp_staging_summary (
    staging_summary_id UUID PRIMARY KEY,
    task_id UUID NOT NULL REFERENCES dp_task(task_id),
    result_version INTEGER NOT NULL,
    total_rows INTEGER NOT NULL,
    success_rows INTEGER NOT NULL,
    warning_rows INTEGER NOT NULL,
    error_rows INTEGER NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (task_id, result_version)
);

CREATE TABLE IF NOT EXISTS dp_export_record (
    export_record_id UUID PRIMARY KEY,
    task_id UUID NOT NULL REFERENCES dp_task(task_id),
    result_version INTEGER NOT NULL,
    export_status VARCHAR(32) NOT NULL,
    export_file_path TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_dp_task_status ON dp_task(status);
CREATE INDEX IF NOT EXISTS idx_dp_input_snapshot_task ON dp_input_snapshot(task_id, snapshot_version);
CREATE INDEX IF NOT EXISTS idx_kb_template_header_alias_normalized ON kb_template_header_alias(normalized_alias);
CREATE INDEX IF NOT EXISTS idx_kb_mapping_rule_scene_country_template
    ON kb_mapping_rule(scene_code, country_code, template_code, status);
CREATE INDEX IF NOT EXISTS idx_dp_staging_result_task_version_row
    ON dp_staging_result(task_id, result_version, row_no);
