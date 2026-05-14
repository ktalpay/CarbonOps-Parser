using CarbonOps.Parser.Contracts;

namespace CarbonOps.Parser.Contracts.Tests;

public sealed class DataQualityValidationTests
{
    [Fact]
    public void ValidationModelRepresentsBlockingWarningAndInfo()
    {
        var blocking = DataQualityValidation.CreateDiagnostic(
            "BLOCKING",
            "blocking diagnostic",
            DataQualityValidationSeverity.BlockingError,
            DataQualityValidationCheck.RequiredField);
        var warning = DataQualityValidation.CreateDiagnostic(
            "WARNING",
            "warning diagnostic",
            DataQualityValidationSeverity.Warning,
            DataQualityValidationCheck.Unit);
        var info = DataQualityValidation.CreateDiagnostic(
            "INFO",
            "info diagnostic",
            DataQualityValidationSeverity.Info,
            DataQualityValidationCheck.Structure);

        var result = new DataQualityValidationResult([blocking, warning, info]);

        Assert.False(result.IsValid);
        Assert.True(result.HasBlockingErrors);
        Assert.Equal(1, result.BlockingErrorCount);
        Assert.Equal(1, result.WarningCount);
        Assert.Equal(1, result.InfoCount);
    }

    [Fact]
    public void ValidationSeverityAndCheckNamesArePhase2WireNames()
    {
        Assert.Equal("blocking_error", DataQualityValidationSeverity.BlockingError.ToWireName());
        Assert.Equal("warning", DataQualityValidationSeverity.Warning.ToWireName());
        Assert.Equal("info", DataQualityValidationSeverity.Info.ToWireName());

        Assert.Equal("required_field", DataQualityValidationCheck.RequiredField.ToWireName());
        Assert.Equal("numeric_value", DataQualityValidationCheck.NumericValue.ToWireName());
        Assert.Equal("unit", DataQualityValidationCheck.Unit.ToWireName());
        Assert.Equal(
            "duplicate_factor_identity",
            DataQualityValidationCheck.DuplicateFactorIdentity.ToWireName());
        Assert.Equal("provenance", DataQualityValidationCheck.Provenance.ToWireName());
        Assert.Equal("structure", DataQualityValidationCheck.Structure.ToWireName());

        Assert.True(ContractWireNames.TryParseDataQualityValidationSeverityWireName(
            "blocking_error",
            out var severity));
        Assert.Equal(DataQualityValidationSeverity.BlockingError, severity);
        Assert.True(ContractWireNames.TryParseDataQualityValidationCheckWireName(
            "duplicate_factor_identity",
            out var check));
        Assert.Equal(DataQualityValidationCheck.DuplicateFactorIdentity, check);
    }

    [Fact]
    public void MissingRequiredFieldsAreBlockingErrors()
    {
        var row = CreateRow(
        [
            new("source_family", null),
            new("source_id", null),
            new("factor_id", " "),
            new("factor_name", null),
            new("factor_value", null),
        ]);

        var result = DataQualityValidation.ValidateNormalizedFactorOutput(new ParserNormalizedOutputBatch([row]));

        Assert.False(result.IsValid);
        Assert.Equal(
            [
                "NORMALIZED_FACTOR_MISSING_REQUIRED_FIELD",
                "NORMALIZED_FACTOR_MISSING_REQUIRED_FIELD",
                "NORMALIZED_FACTOR_MISSING_REQUIRED_FIELD",
                "NORMALIZED_FACTOR_MISSING_REQUIRED_FIELD",
                "NORMALIZED_FACTOR_MISSING_REQUIRED_FIELD",
            ],
            DiagnosticCodes(result));
        Assert.Equal(
            [
                "factor_id",
                "factor_name",
                "factor_value",
                "source_family",
                "source_id",
            ],
            result.Diagnostics.Select(diagnostic => diagnostic.FieldName));
        Assert.All(
            result.Diagnostics,
            diagnostic => Assert.Equal(DataQualityValidationSeverity.BlockingError, diagnostic.Severity));
    }

    [Fact]
    public void InvalidNumericValuesAreBlockingErrorsWithoutValueLeakage()
    {
        var row = CreateRow([new("factor_value", "not-a-number")]);

        var result = DataQualityValidation.ValidateNormalizedFactorOutput(new ParserNormalizedOutputBatch([row]));

        Assert.False(result.IsValid);
        var diagnostic = Assert.Single(result.Diagnostics);
        Assert.Equal("NORMALIZED_FACTOR_INVALID_NUMERIC_VALUE", diagnostic.Code);
        Assert.Equal("factor_value", diagnostic.FieldName);
        Assert.Equal(DataQualityValidationCheck.NumericValue, diagnostic.Check);
        Assert.DoesNotContain("not-a-number", diagnostic.Message, StringComparison.Ordinal);
        Assert.DoesNotContain("not-a-number", diagnostic.ToString(), StringComparison.Ordinal);
    }

    [Fact]
    public void UnsupportedUnitsAreWarnings()
    {
        var row = CreateRow([new("unit", "widgets per fortnight")]);

        var result = DataQualityValidation.ValidateNormalizedFactorOutput(
            new ParserNormalizedOutputBatch([row]),
            supportedUnits: ["kg CO2e/kWh"]);

        Assert.True(result.IsValid);
        Assert.Equal(1, result.WarningCount);
        var diagnostic = Assert.Single(result.Diagnostics);
        Assert.Equal("NORMALIZED_FACTOR_UNSUPPORTED_UNIT", diagnostic.Code);
        Assert.Equal(DataQualityValidationSeverity.Warning, diagnostic.Severity);
        Assert.Equal(DataQualityValidationCheck.Unit, diagnostic.Check);
    }

    [Fact]
    public void DuplicateFactorIdentityIsBlockingError()
    {
        var first = CreateRow(rowIdentifier: "row-1", fields: [new("factor_id", "F1")]);
        var duplicate = CreateRow(rowIdentifier: "row-2", fields: [new("factor_id", "F1")]);

        var result = DataQualityValidation.ValidateNormalizedFactorOutput(
            new ParserNormalizedOutputBatch([first, duplicate]));

        Assert.False(result.IsValid);
        var diagnostic = Assert.Single(result.Diagnostics);
        Assert.Equal("NORMALIZED_FACTOR_DUPLICATE_IDENTITY", diagnostic.Code);
        Assert.Equal(DataQualityValidationCheck.DuplicateFactorIdentity, diagnostic.Check);
        Assert.Equal("1", ContextValue(diagnostic, "first_record_position"));
        Assert.Equal("2", ContextValue(diagnostic, "record_position"));
    }

    [Fact]
    public void ProvenanceGapsAreWarningsWithSafeSourceContext()
    {
        var row = CreateRow(artifactReference: "", sourceRowNumber: null, fields: []);

        var result = DataQualityValidation.ValidateNormalizedFactorOutput(new ParserNormalizedOutputBatch([row]));

        Assert.True(result.IsValid);
        var diagnostic = Assert.Single(result.Diagnostics);
        Assert.Equal("NORMALIZED_FACTOR_PROVENANCE_GAP", diagnostic.Code);
        Assert.Equal("defra_desnz", diagnostic.SourceFamily);
        Assert.Equal(DataQualityValidationSeverity.Warning, diagnostic.Severity);
        Assert.Equal(
            new DataQualityProvenanceContext(
                "row-1",
                "defra_desnz",
                "defra_desnz",
                sourceReference: null,
                rowNumber: null,
                provenance: null,
                documentId: null),
            diagnostic.Provenance);
        Assert.Equal("1", ContextValue(diagnostic, "record_position"));
    }

    [Fact]
    public void DiagnosticsAreDeterministicallyOrderedByRecordThenCode()
    {
        var first = CreateRow(
            rowIdentifier: "row-1",
            fields:
            [
                new("factor_id", ""),
                new("factor_value", "bad"),
                new("unit", "bad-unit"),
            ]);
        var second = CreateRow(
            rowIdentifier: "row-2",
            fields:
            [
                new("factor_id", ""),
                new("unit", "bad-unit"),
            ]);

        var result = DataQualityValidation.ValidateNormalizedFactorOutput(
            new ParserNormalizedOutputBatch([second, first]));

        Assert.Equal(
            [
                ("1", "NORMALIZED_FACTOR_MISSING_REQUIRED_FIELD"),
                ("1", "NORMALIZED_FACTOR_UNSUPPORTED_UNIT"),
                ("2", "NORMALIZED_FACTOR_INVALID_NUMERIC_VALUE"),
                ("2", "NORMALIZED_FACTOR_MISSING_REQUIRED_FIELD"),
                ("2", "NORMALIZED_FACTOR_UNSUPPORTED_UNIT"),
            ],
            result.Diagnostics.Select(diagnostic => (ContextValue(diagnostic, "record_position"), diagnostic.Code)));
    }

    [Fact]
    public void SensitiveValuesAreRedactedFromDiagnosticContext()
    {
        var diagnostic = DataQualityValidation.CreateDiagnostic(
            "SAFE_CONTEXT",
            "safe context diagnostic",
            DataQualityValidationSeverity.Info,
            DataQualityValidationCheck.Structure,
            context:
            [
                new("api_key", "abc123"),
                new("password", "secret-value"),
                new("source_reference", "https://user:pass@example.invalid/?token=abc123"),
                new("visible", "ok"),
            ]);

        Assert.Equal(DataQualityValidation.RedactedDiagnosticValue, ContextValue(diagnostic, "api_key"));
        Assert.Equal(DataQualityValidation.RedactedDiagnosticValue, ContextValue(diagnostic, "password"));
        Assert.Equal(
            "https://[REDACTED]@example.invalid/?token=[REDACTED]",
            ContextValue(diagnostic, "source_reference"));
        Assert.Equal("ok", ContextValue(diagnostic, "visible"));
        Assert.DoesNotContain("abc123", diagnostic.ToString(), StringComparison.Ordinal);
        Assert.DoesNotContain("pass", diagnostic.ToString(), StringComparison.Ordinal);
        Assert.DoesNotContain("secret-value", diagnostic.ToString(), StringComparison.Ordinal);
    }

    [Fact]
    public void SensitiveValuesAreRedactedFromProvenanceContext()
    {
        var row = CreateRow(
            artifactReference: "https://user:pass@example.invalid/factors.csv?token=abc123",
            sourceRowNumber: null,
            fields: [new("unit", "unsupported")]);

        var result = DataQualityValidation.ValidateNormalizedFactorOutput(new ParserNormalizedOutputBatch([row]));

        var diagnostic = Assert.Single(result.Diagnostics);
        Assert.NotNull(diagnostic.Provenance);
        Assert.Equal(
            "https://[REDACTED]@example.invalid/factors.csv?token=[REDACTED]",
            diagnostic.Provenance!.SourceReference);
        Assert.DoesNotContain("pass", diagnostic.ToString(), StringComparison.Ordinal);
        Assert.DoesNotContain("abc123", diagnostic.ToString(), StringComparison.Ordinal);
    }

    [Fact]
    public void ValidFactorOutputHasNoDiagnostics()
    {
        var result = DataQualityValidation.ValidateNormalizedFactorOutput(
            new ParserNormalizedOutputBatch([CreateRow()]));

        Assert.True(result.IsValid);
        Assert.Empty(result.Diagnostics);
    }

    private static ParserNormalizedOutputRow CreateRow(
        IEnumerable<ParserNormalizedField>? fields = null,
        string rowIdentifier = "row-1",
        string artifactReference = "memory://defra",
        int? sourceRowNumber = 2)
    {
        var values = new Dictionary<string, string?>(StringComparer.Ordinal)
        {
            ["source_family"] = "defra_desnz",
            ["source_id"] = "defra_desnz",
            ["source_year"] = "2024",
            ["source_version"] = "v1",
            ["row_number"] = sourceRowNumber?.ToString(),
            ["factor_id"] = "F1",
            ["factor_name"] = "Electricity",
            ["factor_value"] = "0.233",
            ["unit"] = "kg CO2e/kWh",
        };

        foreach (var field in fields ?? [])
        {
            if (field.Value is null)
            {
                values.Remove(field.Key);
            }
            else
            {
                values[field.Key] = field.Value;
            }
        }

        return new ParserNormalizedOutputRow(
            SourceFamily.DefraDesnz,
            "defra_desnz",
            new ParserKey("defra_desnz"),
            artifactReference,
            rowIdentifier,
            sourceRowNumber,
            values.Select(pair => new ParserNormalizedField(pair.Key, pair.Value)));
    }

    private static string[] DiagnosticCodes(DataQualityValidationResult result) =>
        result.Diagnostics.Select(diagnostic => diagnostic.Code).ToArray();

    private static string? ContextValue(DataQualityDiagnostic diagnostic, string key) =>
        diagnostic.Context.FirstOrDefault(item => item.Key == key)?.Value;
}
