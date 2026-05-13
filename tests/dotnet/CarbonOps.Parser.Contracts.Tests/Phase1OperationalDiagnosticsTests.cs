using System.Text.Json;
using CarbonOps.Parser.Contracts;

namespace CarbonOps.Parser.Contracts.Tests;

public sealed class Phase1OperationalDiagnosticsTests
{
    [Fact]
    public void PostgreSQLOptionsDiagnosticsRedactSensitiveRuntimeValues()
    {
        var options = new PostgreSQLPersistenceOptions(
            "db.internal.example",
            5432,
            "carbonops_prod",
            "service_user",
            PasswordSet: true,
            SslMode: "require",
            ApplicationName: "carbonops-phase1",
            ConnectTimeoutSeconds: 10);

        var summary = Phase1OperationalDiagnostics.SummarizePostgreSQLOptionsForDiagnostics(options);

        Assert.Equal(Phase1OperationalDiagnostics.Redacted, summary["application_name"]);
        Assert.Equal(10, summary["connect_timeout_seconds"]);
        Assert.Equal(Phase1OperationalDiagnostics.Redacted, summary["database"]);
        Assert.Equal(Phase1OperationalDiagnostics.Redacted, summary["host"]);
        Assert.Equal(true, summary["password_set"]);
        Assert.Equal(5432, summary["port"]);
        Assert.Equal("require", summary["ssl_mode"]);
        Assert.Equal(Phase1OperationalDiagnostics.Redacted, summary["username"]);
    }

    [Fact]
    public void RedactionRemovesSecretFieldsAndConnectionUserInfo()
    {
        var value = new Dictionary<string, object?>
        {
            ["password"] = "super-secret",
            ["connectionString"] = "Host=db;Username=svc;" + "Password" + "=raw-secret",
            ["apiKey"] = "api-secret",
            ["nested"] = new Dictionary<string, object?>
            {
                ["message"] = "failed dsn=postgresql://svc:secret@db.internal/carbonops " + "connectionString" + "=postgresql://svc:raw-secret@db.internal/carbonops " + "token" + "=abc123",
            },
            ["safe_count"] = 3,
        };

        var redacted = Phase1OperationalDiagnostics.RedactDiagnosticValue("payload", value);
        var redactedMapping = Assert.IsAssignableFrom<IReadOnlyDictionary<string, object?>>(redacted);
        var nestedMapping = Assert.IsAssignableFrom<IReadOnlyDictionary<string, object?>>(
            redactedMapping["nested"]);

        Assert.Equal(
            "failed dsn=<redacted> " + "connectionString" + "=<redacted> " + "token" + "=<redacted>",
            nestedMapping["message"]);
        Assert.Equal(Phase1OperationalDiagnostics.Redacted, redactedMapping["apiKey"]);
        Assert.Equal(Phase1OperationalDiagnostics.Redacted, redactedMapping["connectionString"]);
        Assert.Equal(Phase1OperationalDiagnostics.Redacted, redactedMapping["password"]);
        Assert.Equal(3, redactedMapping["safe_count"]);

        var json = JsonSerializer.Serialize(redacted);
        Assert.DoesNotContain("super-secret", json, StringComparison.Ordinal);
        Assert.DoesNotContain("svc:secret", json, StringComparison.Ordinal);
        Assert.DoesNotContain("abc123", json, StringComparison.Ordinal);
        Assert.DoesNotContain("api-secret", json, StringComparison.Ordinal);
        Assert.DoesNotContain("raw-secret", json, StringComparison.Ordinal);
    }

    [Fact]
    public void RedactionRemovesPrefixedAndSuffixedSensitiveKeyNames()
    {
        var json = Phase1OperationalDiagnostics.SerializeOperationalEvent(
            "phase1_test_event",
            new Dictionary<string, object?>
            {
                ["primaryConnectionString"] = "Host=db;Username=svc;Password=connection-secret",
                ["providerApiKey"] = "provider-api-secret",
                ["externalDatabaseUrl"] = "postgresql://svc:database-secret@db.internal/carbonops",
                ["privateAccessKey"] = "private-access-secret",
                ["safe_count"] = 4,
            });

        Assert.Contains("\"primaryConnectionString\":\"<redacted>\"", json, StringComparison.Ordinal);
        Assert.Contains("\"providerApiKey\":\"<redacted>\"", json, StringComparison.Ordinal);
        Assert.Contains("\"externalDatabaseUrl\":\"<redacted>\"", json, StringComparison.Ordinal);
        Assert.Contains("\"privateAccessKey\":\"<redacted>\"", json, StringComparison.Ordinal);
        Assert.Contains("\"safe_count\":4", json, StringComparison.Ordinal);
        Assert.DoesNotContain("connection-secret", json, StringComparison.Ordinal);
        Assert.DoesNotContain("provider-api-secret", json, StringComparison.Ordinal);
        Assert.DoesNotContain("database-secret", json, StringComparison.Ordinal);
        Assert.DoesNotContain("private-access-secret", json, StringComparison.Ordinal);
    }

    [Fact]
    public void OperationalEventJsonShapeIsStable()
    {
        var json = Phase1OperationalDiagnostics.SerializeOperationalEvent(
            "phase1_test_event",
            new Dictionary<string, object?>
            {
                ["z_count"] = 2,
                ["a_context"] = new Dictionary<string, object?>
                {
                    ["source_family"] = "ghg_protocol",
                },
            });

        Assert.Equal(
            "{\"a_context\":{\"source_family\":\"ghg_protocol\"},\"event\":\"phase1_test_event\",\"z_count\":2}",
            json);
    }

    [Fact]
    public void DiagnosticsShapeMatchesSharedParityFixture()
    {
        using var document = JsonDocument.Parse(File.ReadAllText(ParityFixturePath()));
        var fixture = document.RootElement;

        Assert.Equal(
            ["correlation_id", "execution_mode", "max_degree_of_parallelism", "run_id", "source_families"],
            Strings(fixture.GetProperty("request_keys")));
        Assert.Equal(
            ["correlation_id", "documents", "failures", "parser", "persistence", "run_id", "source_family", "source_key", "status"],
            Strings(fixture.GetProperty("family_keys")));
        Assert.Equal(
            ["checksum_sha256", "document_id", "source_family", "source_key"],
            Strings(fixture.GetProperty("document_keys")));
        Assert.Equal(
            ["accepted_row_count", "failure_count", "result_status", "run_id", "validation_issue_count"],
            Strings(fixture.GetProperty("parser_keys")));
        Assert.Equal(
            ["code", "field_name", "message", "severity", "source_family", "source_key", "stage"],
            Strings(fixture.GetProperty("failure_keys")));
        Assert.Equal(
            [
                "completed_family_count",
                "failed_family_count",
                "failure_count",
                "parsed_factor_row_count",
                "parser_run_count",
                "persisted_detail_count",
                "persisted_master_count",
                "persisted_parser_run_count",
                "persisted_source_document_count",
                "persisted_source_run_count",
                "requested_family_count",
                "source_artifact_count",
                "source_candidate_count",
            ],
            Strings(fixture.GetProperty("summary_keys")));
        Assert.Equal(
            [
                "phase1_ingestion_orchestrator_started",
                "phase1_source_family_completed",
                "phase1_ingestion_orchestrator_completed",
            ],
            Strings(fixture.GetProperty("orchestrator_event_names")));
        Assert.Equal(
            [
                "phase1_service_host_starting",
                "phase1_service_host_started",
                "phase1_service_host_scheduled_run_started",
                "phase1_service_host_scheduled_run_completed",
                "phase1_service_host_scheduled_run_skipped",
            ],
            Strings(fixture.GetProperty("service_host_event_names")));
        Assert.Equal(Phase1OperationalDiagnostics.Redacted, fixture.GetProperty("redacted").GetString());
        Assert.Contains(
            "intentionally coarser",
            fixture.GetProperty("intentional_status_difference").GetString(),
            StringComparison.Ordinal);
    }

    [Fact]
    public void FamilyDiagnosticsIncludeSafeDocumentParserPersistenceAndFailureShape()
    {
        var checksum = new string('A', 64);
        var familyResult = new Phase1IngestionFamilyResult(
            SourceFamily.GhgProtocol,
            "ghg_protocol",
            Phase1IngestionFamilyRunStatus.Failed,
            acquisitionRun: new SourceAcquisitionRunResult(
                SourceFamily.GhgProtocol,
                "ghg_protocol",
                SourceAcquisitionRunStatus.Completed,
                [],
                [
                    new SourceDownloadArtifact(
                        SourceFamily.GhgProtocol,
                        "ghg_protocol",
                        "candidate-001",
                        "document-001",
                        ParserSourceFormat.DiscoveryReference,
                        "https://example.invalid/source.csv",
                        "local/document.csv",
                        "Document",
                        "text/csv",
                        checksum: new SourceDocumentChecksum("sha256", checksum, IsDryRunPlaceholder: false)),
                ],
                "run-001",
                "corr-001"),
            sourceDocumentPersistResult: new SourceDocumentRepositoryPersistResult(
                "fake_documents",
                SourceDocumentRepositoryPersistStatus.Declared,
                1),
            parserRun: new ParserAdapterRunResult(
                SourceFamily.GhgProtocol,
                "ghg_protocol",
                ParserSelectionRegistry.GetParserKey(SourceFamily.GhgProtocol),
                ParserRunStatus.Failed,
                ["document-001"],
                [],
                [
                    new ParserValidationIssue(
                        SourceFamily.GhgProtocol,
                        "ghg_protocol",
                        ParserSelectionRegistry.GetParserKey(SourceFamily.GhgProtocol),
                        ParserValidationIssueSeverity.Error,
                        "GHG_PROTOCOL_CONTENT_INVALID_HEADER",
                        "failed password" + "=raw-secret"),
                ],
                "run-001-ghg_protocol-parser",
                "corr-001"),
            failures:
            [
                new Phase1IngestionFailure(
                    SourceFamily.GhgProtocol,
                    "ghg_protocol",
                    "parser",
                    "GHG_PROTOCOL_CONTENT_INVALID_HEADER",
                    "failed password" + "=raw-secret"),
            ]);

        var json = JsonSerializer.Serialize(
            Phase1OperationalDiagnostics.SummarizeFamilyResultForDiagnostics(
                familyResult,
                "run-001",
                "corr-001"));

        Assert.Contains("\"checksum_sha256\":\"" + checksum.ToLowerInvariant() + "\"", json, StringComparison.Ordinal);
        Assert.Contains("\"document_id\":\"document-001\"", json, StringComparison.Ordinal);
        Assert.Contains("\"source_key\":\"ghg_protocol\"", json, StringComparison.Ordinal);
        Assert.Contains("\"accepted_row_count\":0", json, StringComparison.Ordinal);
        Assert.Contains("\"validation_issue_count\":1", json, StringComparison.Ordinal);
        Assert.Contains("\"failure_count\":1", json, StringComparison.Ordinal);
        Assert.Contains("\"status\":\"failed\"", json, StringComparison.Ordinal);
        Assert.Contains("\"source_document_count\":1", json, StringComparison.Ordinal);
        Assert.Contains("\"code\":\"GHG_PROTOCOL_CONTENT_INVALID_HEADER\"", json, StringComparison.Ordinal);
        Assert.DoesNotContain("raw-secret", json, StringComparison.Ordinal);
    }

    private static string[] Strings(JsonElement element) =>
        element.EnumerateArray().Select(item => item.GetString() ?? string.Empty).ToArray();

    private static string ParityFixturePath()
    {
        var directory = new DirectoryInfo(AppContext.BaseDirectory);
        while (directory is not null)
        {
            var fixturePath = Path.Combine(
                directory.FullName,
                "tests",
                "fixtures",
                "parity",
                "phase1_operational_diagnostics_expectations.json");
            if (File.Exists(fixturePath))
            {
                return fixturePath;
            }

            directory = directory.Parent;
        }

        throw new FileNotFoundException("Phase 1 operational diagnostics parity fixture was not found.");
    }
}
