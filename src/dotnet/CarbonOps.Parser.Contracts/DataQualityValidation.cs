using System.Globalization;
using System.Text.RegularExpressions;

namespace CarbonOps.Parser.Contracts;

public static partial class DataQualityValidation
{
    public const string RedactedDiagnosticValue = "[REDACTED]";

    public static readonly IReadOnlyList<string> DefaultSupportedFactorUnits = Array.AsReadOnly(new[]
    {
        "kg",
        "kg CO2e",
        "kg CO2e/kWh",
        "kWh",
    });

    private static readonly string[] RequiredFactorFields =
    [
        "source_family",
        "source_id",
        "factor_id",
        "factor_name",
        "factor_value",
        "unit",
    ];

    private static readonly string[] ProvenanceFieldNames =
    [
        "provenance",
        "row_number",
        "source_document_id",
        "document_id",
    ];

    private static readonly string[] SensitiveFieldTokens =
    [
        "api_key",
        "authorization",
        "credential",
        "password",
        "secret",
        "token",
    ];

    [GeneratedRegex("//[^/\\s:@]+:[^@\\s/]+@")]
    private static partial Regex UserInfoUriPattern();

    [GeneratedRegex("\\b(api[_-]?key|authorization|credential|password|secret|token)=([^\\s&;,]+)", RegexOptions.IgnoreCase)]
    private static partial Regex SensitiveAssignmentPattern();

    public static DataQualityDiagnostic CreateDiagnostic(
        string code,
        string message,
        DataQualityValidationSeverity severity,
        DataQualityValidationCheck check,
        string? fieldName = null,
        string? sourceFamily = null,
        DataQualityProvenanceContext? provenance = null,
        IEnumerable<DataQualityDiagnosticContext>? context = null) =>
        new(code, message, severity, check, fieldName, sourceFamily, provenance, context);

    public static DataQualityValidationResult ValidateNormalizedFactorOutput(
        ParserNormalizedOutputBatch output,
        IEnumerable<string>? supportedUnits = null)
    {
        var unitSet = (supportedUnits ?? DefaultSupportedFactorUnits).ToHashSet(StringComparer.Ordinal);
        var diagnostics = new List<DataQualityDiagnostic>();
        var identityPositions = new Dictionary<string, int>(StringComparer.Ordinal);

        for (var index = 0; index < output.Rows.Count; index++)
        {
            var position = index + 1;
            var row = output.Rows[index];
            var fields = RowFields(row);
            var sourceFamily = TextOrNull(FieldValue(fields, "source_family")) ?? row.SourceFamily.ToWireName();
            var provenance = ProvenanceContext(row, fields);

            diagnostics.AddRange(MissingRequiredFieldDiagnostics(fields, position, sourceFamily, provenance));
            diagnostics.AddRange(InvalidNumericDiagnostics(fields, position, sourceFamily, provenance));
            diagnostics.AddRange(UnsupportedUnitDiagnostics(fields, unitSet, position, sourceFamily, provenance));
            diagnostics.AddRange(ProvenanceGapDiagnostics(row, fields, position, sourceFamily, provenance));

            var identity = FactorIdentity(fields);
            if (identity is null)
            {
                continue;
            }

            if (identityPositions.TryGetValue(identity, out var firstPosition))
            {
                diagnostics.Add(CreateDiagnostic(
                    "NORMALIZED_FACTOR_DUPLICATE_IDENTITY",
                    "normalized factor identity must be unique within the validation result.",
                    DataQualityValidationSeverity.BlockingError,
                    DataQualityValidationCheck.DuplicateFactorIdentity,
                    fieldName: "factor_id",
                    sourceFamily: sourceFamily,
                    provenance: provenance,
                    context:
                    [
                        new("first_record_position", firstPosition.ToString(CultureInfo.InvariantCulture)),
                        new("record_position", position.ToString(CultureInfo.InvariantCulture)),
                    ]));
            }
            else
            {
                identityPositions[identity] = position;
            }
        }

        return new DataQualityValidationResult(diagnostics
            .OrderBy(diagnostic => ContextIntValue(diagnostic, "record_position"))
            .ThenBy(diagnostic => diagnostic.Code, StringComparer.Ordinal)
            .ThenBy(diagnostic => diagnostic.FieldName ?? string.Empty, StringComparer.Ordinal));
    }

    public static string? SafeDiagnosticText(string? value)
    {
        var text = TextOrNull(value);
        if (text is null)
        {
            return null;
        }

        var withoutUserInfo = UserInfoUriPattern().Replace(text, $"//{RedactedDiagnosticValue}@");
        return SensitiveAssignmentPattern().Replace(
            withoutUserInfo,
            match => $"{match.Groups[1].Value}={RedactedDiagnosticValue}");
    }

    public static string? SafeDiagnosticValue(string fieldName, string? value) =>
        IsSensitiveField(fieldName) && value is not null
            ? RedactedDiagnosticValue
            : SafeDiagnosticText(value);

    private static IReadOnlyDictionary<string, string?> RowFields(ParserNormalizedOutputRow row) =>
        row.Fields
            .GroupBy(field => field.Key, StringComparer.Ordinal)
            .ToDictionary(group => group.Key, group => group.First().Value, StringComparer.Ordinal);

    private static IEnumerable<DataQualityDiagnostic> MissingRequiredFieldDiagnostics(
        IReadOnlyDictionary<string, string?> fields,
        int position,
        string? sourceFamily,
        DataQualityProvenanceContext provenance)
    {
        foreach (var fieldName in RequiredFactorFields)
        {
            if (!MissingField(fields, fieldName))
            {
                continue;
            }

            yield return CreateDiagnostic(
                "NORMALIZED_FACTOR_MISSING_REQUIRED_FIELD",
                "normalized factor output is missing a required field.",
                DataQualityValidationSeverity.BlockingError,
                DataQualityValidationCheck.RequiredField,
                fieldName: fieldName,
                sourceFamily: sourceFamily,
                provenance: provenance,
                context:
                [
                    new("field_name", fieldName),
                    new("record_position", position.ToString(CultureInfo.InvariantCulture)),
                ]);
        }
    }

    private static IEnumerable<DataQualityDiagnostic> InvalidNumericDiagnostics(
        IReadOnlyDictionary<string, string?> fields,
        int position,
        string? sourceFamily,
        DataQualityProvenanceContext provenance)
    {
        if (MissingField(fields, "factor_value") || IsValidNumeric(FieldValue(fields, "factor_value")))
        {
            return [];
        }

        return
        [
            CreateDiagnostic(
                "NORMALIZED_FACTOR_INVALID_NUMERIC_VALUE",
                "normalized factor_value must be numeric.",
                DataQualityValidationSeverity.BlockingError,
                DataQualityValidationCheck.NumericValue,
                fieldName: "factor_value",
                sourceFamily: sourceFamily,
                provenance: provenance,
                context:
                [
                    new("field_name", "factor_value"),
                    new("record_position", position.ToString(CultureInfo.InvariantCulture)),
                ]),
        ];
    }

    private static IEnumerable<DataQualityDiagnostic> UnsupportedUnitDiagnostics(
        IReadOnlyDictionary<string, string?> fields,
        HashSet<string> supportedUnits,
        int position,
        string? sourceFamily,
        DataQualityProvenanceContext provenance)
    {
        var unit = TextOrNull(FieldValue(fields, "unit"));
        if (unit is null || supportedUnits.Contains(unit))
        {
            return [];
        }

        return
        [
            CreateDiagnostic(
                "NORMALIZED_FACTOR_UNSUPPORTED_UNIT",
                "normalized factor unit is not in the configured supported unit set.",
                DataQualityValidationSeverity.Warning,
                DataQualityValidationCheck.Unit,
                fieldName: "unit",
                sourceFamily: sourceFamily,
                provenance: provenance,
                context:
                [
                    new("field_name", "unit"),
                    new("record_position", position.ToString(CultureInfo.InvariantCulture)),
                    new("supported_unit_count", supportedUnits.Count.ToString(CultureInfo.InvariantCulture)),
                ]),
        ];
    }

    private static IEnumerable<DataQualityDiagnostic> ProvenanceGapDiagnostics(
        ParserNormalizedOutputRow row,
        IReadOnlyDictionary<string, string?> fields,
        int position,
        string? sourceFamily,
        DataQualityProvenanceContext provenance)
    {
        var hasFieldProvenance = ProvenanceFieldNames.Any(name => !MissingField(fields, name));
        if (!string.IsNullOrWhiteSpace(row.ArtifactReference) || row.SourceRowNumber is not null || hasFieldProvenance)
        {
            return [];
        }

        return
        [
            CreateDiagnostic(
                "NORMALIZED_FACTOR_PROVENANCE_GAP",
                "normalized factor output should include row or document provenance before downstream use.",
                DataQualityValidationSeverity.Warning,
                DataQualityValidationCheck.Provenance,
                sourceFamily: sourceFamily,
                provenance: provenance,
                context:
                [
                    new("record_position", position.ToString(CultureInfo.InvariantCulture)),
                ]),
        ];
    }

    private static string? FactorIdentity(IReadOnlyDictionary<string, string?> fields)
    {
        string[] identityFields =
        [
            "source_family",
            "source_id",
            "source_year",
            "source_version",
            "factor_id",
            "unit",
        ];

        if (identityFields.Any(fieldName => MissingField(fields, fieldName)))
        {
            return null;
        }

        return string.Join("\u001f", identityFields.Select(fieldName => TextOrNull(FieldValue(fields, fieldName))));
    }

    private static DataQualityProvenanceContext ProvenanceContext(
        ParserNormalizedOutputRow row,
        IReadOnlyDictionary<string, string?> fields) =>
        new(
            row.RowIdentifier,
            TextOrNull(FieldValue(fields, "source_family")) ?? row.SourceFamily.ToWireName(),
            TextOrNull(FieldValue(fields, "source_id")) ?? row.SourceKey,
            row.ArtifactReference,
            TextOrNull(FieldValue(fields, "row_number")) ??
                row.SourceRowNumber?.ToString(CultureInfo.InvariantCulture),
            TextOrNull(FieldValue(fields, "provenance")),
            TextOrNull(FieldValue(fields, "source_document_id")) ?? TextOrNull(FieldValue(fields, "document_id")));

    private static bool MissingField(IReadOnlyDictionary<string, string?> fields, string fieldName) =>
        !fields.TryGetValue(fieldName, out var value) || string.IsNullOrWhiteSpace(value);

    private static string? FieldValue(IReadOnlyDictionary<string, string?> fields, string fieldName) =>
        fields.TryGetValue(fieldName, out var value) ? value : null;

    private static bool IsValidNumeric(string? value) =>
        !string.IsNullOrWhiteSpace(value) &&
        decimal.TryParse(value, NumberStyles.Float, CultureInfo.InvariantCulture, out _);

    private static string? TextOrNull(string? value) =>
        string.IsNullOrWhiteSpace(value) ? null : value.Trim();

    private static string ContextValue(DataQualityDiagnostic diagnostic, string key) =>
        diagnostic.Context.FirstOrDefault(item => item.Key == key)?.Value ?? "0";

    private static int ContextIntValue(DataQualityDiagnostic diagnostic, string key) =>
        int.TryParse(ContextValue(diagnostic, key), NumberStyles.Integer, CultureInfo.InvariantCulture, out var value)
            ? value
            : 0;

    private static bool IsSensitiveField(string fieldName)
    {
        var normalized = fieldName.ToLowerInvariant();
        return SensitiveFieldTokens.Any(token => normalized.Contains(token, StringComparison.Ordinal));
    }
}
