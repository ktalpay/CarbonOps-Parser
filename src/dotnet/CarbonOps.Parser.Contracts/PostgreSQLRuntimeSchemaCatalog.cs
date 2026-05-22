namespace CarbonOps.Parser.Contracts;

public enum PostgreSQLRuntimeColumnType
{
    Uuid = 0,
    Text = 1,
    Integer = 2,
    Numeric = 3,
    TimestampWithTimeZone = 4,
    Jsonb = 5,
}

public sealed record PostgreSQLRuntimeColumn(
    string Name,
    PostgreSQLRuntimeColumnType DataType,
    bool Nullable,
    bool IsPrimaryKey = false);

public sealed record PostgreSQLRuntimeForeignKey(
    string ColumnName,
    string ReferencedTableName,
    string ReferencedColumnName);

public sealed record PostgreSQLRuntimeUniqueConstraint(
    string Name,
    IReadOnlyList<string> ColumnNames);

public sealed record PostgreSQLRuntimeIndex(
    string Name,
    IReadOnlyList<string> ColumnNames,
    bool Unique = false);

public sealed record PostgreSQLRuntimeTable(
    string Name,
    IReadOnlyList<PostgreSQLRuntimeColumn> Columns,
    IReadOnlyList<PostgreSQLRuntimeForeignKey>? ForeignKeys = null,
    IReadOnlyList<PostgreSQLRuntimeUniqueConstraint>? UniqueConstraints = null,
    IReadOnlyList<PostgreSQLRuntimeIndex>? Indexes = null);

public static class PostgreSQLRuntimeSchemaCatalog
{
    public static IReadOnlyList<PostgreSQLRuntimeTable> Tables { get; } = Array.AsReadOnly(
        SharedTables()
            .Concat(SourceFamilyTables("ghg"))
            .Concat(SourceFamilyTables("defra"))
            .Concat(SourceFamilyTables("ipcc"))
            .ToArray());

    public static IReadOnlyList<string> RequiredTableNames { get; } = Array.AsReadOnly(
        Tables
            .Select(table => table.Name)
            .Order(StringComparer.Ordinal)
            .ToArray());

    public static string ToPostgreSQLRuntimeValue(this SourceFamily sourceFamily) =>
        sourceFamily switch
        {
            SourceFamily.GhgProtocol => "ghg_protocol",
            SourceFamily.DefraDesnz => "defra_desnz",
            SourceFamily.IpccEfdb => "ipcc_efdb",
            _ => throw new ArgumentOutOfRangeException(nameof(sourceFamily), sourceFamily, null),
        };

    private static IReadOnlyList<PostgreSQLRuntimeTable> SharedTables() =>
    [
        new(
            "ingestion_runs",
            [
                new("ingestion_run_id", PostgreSQLRuntimeColumnType.Uuid, Nullable: false, IsPrimaryKey: true),
                new("run_status", PostgreSQLRuntimeColumnType.Text, Nullable: false),
                new("created_at", PostgreSQLRuntimeColumnType.TimestampWithTimeZone, Nullable: false),
                new("updated_at", PostgreSQLRuntimeColumnType.TimestampWithTimeZone, Nullable: false),
            ],
            Indexes: [new("idx_ingestion_runs_run_status", ["run_status"])]),
        new(
            "source_documents",
            [
                new("source_document_id", PostgreSQLRuntimeColumnType.Uuid, Nullable: false, IsPrimaryKey: true),
                new("ingestion_run_id", PostgreSQLRuntimeColumnType.Uuid, Nullable: false),
                new("source_family", PostgreSQLRuntimeColumnType.Text, Nullable: false),
                new("source_document_uri", PostgreSQLRuntimeColumnType.Text, Nullable: false),
                new("source_checksum_sha256", PostgreSQLRuntimeColumnType.Text, Nullable: false),
                new("acquisition_status", PostgreSQLRuntimeColumnType.Text, Nullable: false),
                new("acquired_at", PostgreSQLRuntimeColumnType.TimestampWithTimeZone, Nullable: true),
                new("created_at", PostgreSQLRuntimeColumnType.TimestampWithTimeZone, Nullable: false),
                new("updated_at", PostgreSQLRuntimeColumnType.TimestampWithTimeZone, Nullable: false),
            ],
            ForeignKeys: [new("ingestion_run_id", "ingestion_runs", "ingestion_run_id")],
            UniqueConstraints:
            [
                new(
                    "uq_source_documents_family_uri_checksum",
                    ["source_family", "source_document_uri", "source_checksum_sha256"]),
            ],
            Indexes: [new("idx_source_documents_ingestion_run_id", ["ingestion_run_id"])]),
        new(
            "parser_runs",
            [
                new("parser_run_id", PostgreSQLRuntimeColumnType.Uuid, Nullable: false, IsPrimaryKey: true),
                new("source_document_id", PostgreSQLRuntimeColumnType.Uuid, Nullable: false),
                new("parser_status", PostgreSQLRuntimeColumnType.Text, Nullable: false),
                new("error_details", PostgreSQLRuntimeColumnType.Jsonb, Nullable: true),
                new("created_at", PostgreSQLRuntimeColumnType.TimestampWithTimeZone, Nullable: false),
                new("updated_at", PostgreSQLRuntimeColumnType.TimestampWithTimeZone, Nullable: false),
            ],
            ForeignKeys: [new("source_document_id", "source_documents", "source_document_id")],
            Indexes: [new("idx_parser_runs_source_document_id", ["source_document_id"])]),
        new(
            "schema_bootstrap_states",
            [
                new("schema_bootstrap_state_id", PostgreSQLRuntimeColumnType.Uuid, Nullable: false, IsPrimaryKey: true),
                new("schema_contract_version", PostgreSQLRuntimeColumnType.Text, Nullable: false),
                new("bootstrap_status", PostgreSQLRuntimeColumnType.Text, Nullable: false),
                new("created_at", PostgreSQLRuntimeColumnType.TimestampWithTimeZone, Nullable: false),
                new("updated_at", PostgreSQLRuntimeColumnType.TimestampWithTimeZone, Nullable: false),
            ],
            UniqueConstraints:
            [
                new("uq_schema_bootstrap_states_contract_version", ["schema_contract_version"]),
            ]),
        new(
            "source_family_year_states",
            [
                new("source_family_year_state_id", PostgreSQLRuntimeColumnType.Uuid, Nullable: false, IsPrimaryKey: true),
                new("source_family", PostgreSQLRuntimeColumnType.Text, Nullable: false),
                new("ingested_year", PostgreSQLRuntimeColumnType.Integer, Nullable: false),
                new("created_at", PostgreSQLRuntimeColumnType.TimestampWithTimeZone, Nullable: false),
                new("updated_at", PostgreSQLRuntimeColumnType.TimestampWithTimeZone, Nullable: false),
            ],
            UniqueConstraints:
            [
                new("uq_source_family_year_states_family_year", ["source_family", "ingested_year"]),
            ],
            Indexes: [new("idx_source_family_year_states_family_year", ["source_family", "ingested_year"])]),
        new(
            "normalized_factor_records",
            [
                new("normalized_factor_record_id", PostgreSQLRuntimeColumnType.Text, Nullable: false, IsPrimaryKey: true),
                new("idempotency_key_sha256", PostgreSQLRuntimeColumnType.Text, Nullable: false),
                new("source_family", PostgreSQLRuntimeColumnType.Text, Nullable: false),
                new("source_id", PostgreSQLRuntimeColumnType.Text, Nullable: false),
                new("source_year", PostgreSQLRuntimeColumnType.Integer, Nullable: true),
                new("source_version", PostgreSQLRuntimeColumnType.Text, Nullable: true),
                new("record_id", PostgreSQLRuntimeColumnType.Text, Nullable: false),
                new("source_row_number", PostgreSQLRuntimeColumnType.Integer, Nullable: true),
                new("source_document_reference", PostgreSQLRuntimeColumnType.Text, Nullable: true),
                new("source_artifact_reference", PostgreSQLRuntimeColumnType.Text, Nullable: true),
                new("source_checksum_sha256", PostgreSQLRuntimeColumnType.Text, Nullable: true),
                new("factor_id", PostgreSQLRuntimeColumnType.Text, Nullable: true),
                new("factor_name", PostgreSQLRuntimeColumnType.Text, Nullable: true),
                new("factor_value", PostgreSQLRuntimeColumnType.Numeric, Nullable: false),
                new("factor_unit", PostgreSQLRuntimeColumnType.Text, Nullable: false),
                new("validation_status", PostgreSQLRuntimeColumnType.Text, Nullable: false),
                new("run_id", PostgreSQLRuntimeColumnType.Text, Nullable: true),
                new("parser_key", PostgreSQLRuntimeColumnType.Text, Nullable: false),
                new("metadata", PostgreSQLRuntimeColumnType.Jsonb, Nullable: false),
                new("normalized_fields", PostgreSQLRuntimeColumnType.Jsonb, Nullable: false),
                new("warnings", PostgreSQLRuntimeColumnType.Jsonb, Nullable: false),
                new("errors", PostgreSQLRuntimeColumnType.Jsonb, Nullable: false),
                new("created_at", PostgreSQLRuntimeColumnType.TimestampWithTimeZone, Nullable: false),
                new("updated_at", PostgreSQLRuntimeColumnType.TimestampWithTimeZone, Nullable: false),
            ],
            UniqueConstraints:
            [
                new("uq_normalized_factor_records_idempotency_key", ["idempotency_key_sha256"]),
            ],
            Indexes: [new("idx_normalized_factor_records_source_year", ["source_family", "source_id", "source_year"])]),
    ];

    private static IReadOnlyList<PostgreSQLRuntimeTable> SourceFamilyTables(string family)
    {
        var masterTable = $"{family}_emission_factor_masters";
        var detailTable = $"{family}_emission_factor_details";
        var masterId = $"{family}_emission_factor_master_id";
        var detailId = $"{family}_emission_factor_detail_id";

        return
        [
            new(
                masterTable,
                [
                    new(masterId, PostgreSQLRuntimeColumnType.Uuid, Nullable: false, IsPrimaryKey: true),
                    new("source_family", PostgreSQLRuntimeColumnType.Text, Nullable: false),
                    new("source_year", PostgreSQLRuntimeColumnType.Integer, Nullable: false),
                    new("source_version", PostgreSQLRuntimeColumnType.Text, Nullable: false),
                    new("source_release", PostgreSQLRuntimeColumnType.Text, Nullable: true),
                    new("source_document_id", PostgreSQLRuntimeColumnType.Uuid, Nullable: false),
                    new("ingestion_run_id", PostgreSQLRuntimeColumnType.Uuid, Nullable: true),
                    new("run_id", PostgreSQLRuntimeColumnType.Text, Nullable: true),
                    new("master_external_key", PostgreSQLRuntimeColumnType.Text, Nullable: false),
                    new("status", PostgreSQLRuntimeColumnType.Text, Nullable: false),
                    new("artifact_reference", PostgreSQLRuntimeColumnType.Text, Nullable: true),
                    new("artifact_checksum_sha256", PostgreSQLRuntimeColumnType.Text, Nullable: true),
                    new("archive_reference", PostgreSQLRuntimeColumnType.Text, Nullable: true),
                    new("archive_checksum_sha256", PostgreSQLRuntimeColumnType.Text, Nullable: true),
                    new("effective_from", PostgreSQLRuntimeColumnType.TimestampWithTimeZone, Nullable: true),
                    new("effective_to", PostgreSQLRuntimeColumnType.TimestampWithTimeZone, Nullable: true),
                    new("record_checksum_sha256", PostgreSQLRuntimeColumnType.Text, Nullable: false),
                    new("metadata", PostgreSQLRuntimeColumnType.Jsonb, Nullable: false),
                    new("created_at", PostgreSQLRuntimeColumnType.TimestampWithTimeZone, Nullable: false),
                    new("updated_at", PostgreSQLRuntimeColumnType.TimestampWithTimeZone, Nullable: false),
                ],
                ForeignKeys:
                [
                    new("source_document_id", "source_documents", "source_document_id"),
                    new("ingestion_run_id", "ingestion_runs", "ingestion_run_id"),
                ],
                UniqueConstraints:
                [
                    new(
                        $"uq_{masterTable}_family_year_version_key",
                        ["source_family", "source_year", "source_version", "master_external_key"]),
                ],
                Indexes:
                [
                    new($"idx_{masterTable}_source_year", ["source_family", "source_year", "source_version"]),
                    new($"idx_{masterTable}_ingestion_run_id", ["ingestion_run_id"]),
                ]),
            new(
                detailTable,
                [
                    new(detailId, PostgreSQLRuntimeColumnType.Uuid, Nullable: false, IsPrimaryKey: true),
                    new(masterId, PostgreSQLRuntimeColumnType.Uuid, Nullable: false),
                    new("detail_external_key", PostgreSQLRuntimeColumnType.Text, Nullable: false),
                    new("source_row_number", PostgreSQLRuntimeColumnType.Integer, Nullable: true),
                    new("factor_id", PostgreSQLRuntimeColumnType.Text, Nullable: true),
                    new("factor_name", PostgreSQLRuntimeColumnType.Text, Nullable: true),
                    new("factor_value", PostgreSQLRuntimeColumnType.Numeric, Nullable: false),
                    new("factor_unit", PostgreSQLRuntimeColumnType.Text, Nullable: false),
                    new("status", PostgreSQLRuntimeColumnType.Text, Nullable: false),
                    new("record_checksum_sha256", PostgreSQLRuntimeColumnType.Text, Nullable: false),
                    new("raw_fields", PostgreSQLRuntimeColumnType.Jsonb, Nullable: false),
                    new("normalized_fields", PostgreSQLRuntimeColumnType.Jsonb, Nullable: false),
                    new("created_at", PostgreSQLRuntimeColumnType.TimestampWithTimeZone, Nullable: false),
                    new("updated_at", PostgreSQLRuntimeColumnType.TimestampWithTimeZone, Nullable: false),
                ],
                ForeignKeys: [new(masterId, masterTable, masterId)],
                UniqueConstraints:
                [
                    new($"uq_{detailTable}_master_detail_external_key", [masterId, "detail_external_key"]),
                ],
                Indexes: [new($"idx_{detailTable}_{masterId}", [masterId])]),
        ];
    }
}
