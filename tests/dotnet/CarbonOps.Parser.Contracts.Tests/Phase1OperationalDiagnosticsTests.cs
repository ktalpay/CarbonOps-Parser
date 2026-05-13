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
            ["nested"] = new Dictionary<string, object?>
            {
                ["message"] = "failed dsn=postgresql://svc:secret@db.internal/carbonops token=abc123",
            },
            ["safe_count"] = 3,
        };

        var redacted = Phase1OperationalDiagnostics.RedactDiagnosticValue("payload", value);
        var redactedMapping = Assert.IsAssignableFrom<IReadOnlyDictionary<string, object?>>(redacted);
        var nestedMapping = Assert.IsAssignableFrom<IReadOnlyDictionary<string, object?>>(
            redactedMapping["nested"]);

        Assert.Equal(
            "failed dsn=<redacted> token=<redacted>",
            nestedMapping["message"]);
        Assert.Equal(Phase1OperationalDiagnostics.Redacted, redactedMapping["password"]);
        Assert.Equal(3, redactedMapping["safe_count"]);

        var json = JsonSerializer.Serialize(redacted);
        Assert.DoesNotContain("super-secret", json, StringComparison.Ordinal);
        Assert.DoesNotContain("svc:secret", json, StringComparison.Ordinal);
        Assert.DoesNotContain("abc123", json, StringComparison.Ordinal);
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
                        "failed password=raw-secret"),
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
                    "failed password=raw-secret"),
            ]);

        var json = JsonSerializer.Serialize(
            Phase1OperationalDiagnostics.SummarizeFamilyResultForDiagnostics(
                familyResult,
                "run-001",
                "corr-001"));

        Assert.Contains("\"checksum_sha256\":\"" + checksum.ToLowerInvariant() + "\"", json, StringComparison.Ordinal);
        Assert.Contains("\"document_id\":\"document-001\"", json, StringComparison.Ordinal);
        Assert.Contains("\"accepted_row_count\":0", json, StringComparison.Ordinal);
        Assert.Contains("\"source_document_count\":1", json, StringComparison.Ordinal);
        Assert.Contains("\"code\":\"GHG_PROTOCOL_CONTENT_INVALID_HEADER\"", json, StringComparison.Ordinal);
        Assert.DoesNotContain("raw-secret", json, StringComparison.Ordinal);
    }
}
