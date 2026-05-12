using System.Globalization;

namespace CarbonOps.Parser.Contracts;

public static class IpccEfdbNormalizedContentParser
{
    public static IReadOnlyList<string> Header { get; } = Array.AsReadOnly(new[]
    {
        "record_type",
        "source_year",
        "source_version",
        "factor_id",
        "factor_name",
        "factor_value",
        "unit",
        "category",
        "subcategory",
        "ipcc_sector",
        "gas",
        "region",
        "technology",
        "provenance",
    });

    private static readonly IReadOnlySet<string> RequiredFields = new HashSet<string>(
        new[]
        {
            "source_year",
            "source_version",
            "factor_id",
            "factor_name",
            "factor_value",
            "unit",
            "category",
            "ipcc_sector",
            "gas",
            "provenance",
        },
        StringComparer.Ordinal);

    public static ParserAdapterRunResult Parse(
        ParserAdapterRunRequest request,
        IReadOnlyDictionary<string, string> contentByArtifactReference)
    {
        var requestValidation = request.Validate();
        if (!requestValidation.IsValid)
        {
            return FailedResult(
                request,
                [],
                requestValidation.Errors.Select(error => Issue(
                    request,
                    ParserValidationIssueSeverity.Error,
                    "IPCC_EFDB_CONTENT_INVALID_REQUEST",
                    error)));
        }

        if (request.SourceFamily != SourceFamily.IpccEfdb)
        {
            return FailedResult(
                request,
                [],
                [
                    Issue(
                        request,
                        ParserValidationIssueSeverity.Error,
                        "IPCC_EFDB_CONTENT_SOURCE_FAMILY_MISMATCH",
                        "IPCC EFDB content parser only accepts ipcc_efdb source family.",
                        fieldKey: "source_family"),
                ]);
        }

        var rows = new List<ParserNormalizedOutputRow>();
        var issues = new List<ParserValidationIssue>();

        foreach (var artifact in request.Artifacts)
        {
            if (!contentByArtifactReference.TryGetValue(artifact.ArtifactReference, out var content))
            {
                issues.Add(Issue(
                    request,
                    ParserValidationIssueSeverity.Error,
                    "IPCC_EFDB_CONTENT_MISSING_ARTIFACT_CONTENT",
                    "IPCC EFDB parser content was not provided for an input artifact.",
                    artifact.ArtifactReference,
                    fieldKey: "artifact_reference"));
                continue;
            }

            ParseArtifact(request, artifact, content, rows, issues);
        }

        if (issues.Any(issue => issue.Severity == ParserValidationIssueSeverity.Error))
        {
            return FailedResult(request, rows, issues);
        }

        if (rows.Count == 0)
        {
            issues.Add(Issue(
                request,
                ParserValidationIssueSeverity.Warning,
                "IPCC_EFDB_CONTENT_NO_RECORDS",
                "IPCC EFDB content included no parseable emission factor rows.",
                fieldKey: "content"));
        }

        return new ParserAdapterRunResult(
            request.SourceFamily,
            request.SourceKey,
            request.ParserKey,
            ParserRunStatus.Completed,
            request.Artifacts.Select(artifact => artifact.ArtifactReference),
            rows,
            issues,
            request.RunId,
            request.CorrelationId,
            request.RequestedReportingYear);
    }

    private static void ParseArtifact(
        ParserAdapterRunRequest request,
        ParserInputArtifact artifact,
        string content,
        ICollection<ParserNormalizedOutputRow> rows,
        ICollection<ParserValidationIssue> issues)
    {
        var csvRows = CsvRows(content).ToArray();
        if (csvRows.Length == 0)
        {
            issues.Add(Issue(
                request,
                ParserValidationIssueSeverity.Warning,
                "IPCC_EFDB_CONTENT_EMPTY",
                "IPCC EFDB content input did not include parseable content.",
                artifact.ArtifactReference,
                fieldKey: "content"));
            return;
        }

        if (!csvRows[0].SequenceEqual(Header, StringComparer.Ordinal))
        {
            issues.Add(Issue(
                request,
                ParserValidationIssueSeverity.Error,
                "IPCC_EFDB_CONTENT_INVALID_HEADER",
                "IPCC EFDB content header must match the declared parser contract.",
                artifact.ArtifactReference,
                sourceRowNumber: 1,
                fieldKey: "header"));
            return;
        }

        for (var rowIndex = 1; rowIndex < csvRows.Length; rowIndex++)
        {
            var sourceRowNumber = rowIndex + 1;
            var values = csvRows[rowIndex];
            if (values.Count == 1 && string.IsNullOrWhiteSpace(values[0]))
            {
                continue;
            }

            if (values.Count != Header.Count)
            {
                issues.Add(Issue(
                    request,
                    ParserValidationIssueSeverity.Error,
                    "IPCC_EFDB_CONTENT_INVALID_ROW",
                    "IPCC EFDB content row has an unexpected column count.",
                    artifact.ArtifactReference,
                    sourceRowNumber: sourceRowNumber,
                    fieldKey: $"row[{sourceRowNumber.ToString(CultureInfo.InvariantCulture)}]"));
                continue;
            }

            var row = Header
                .Select((field, index) => new { field, value = values[index].Trim() })
                .ToDictionary(pair => pair.field, pair => pair.value, StringComparer.Ordinal);

            if (!row.Values.Any(value => !string.IsNullOrWhiteSpace(value)))
            {
                continue;
            }

            if (row["record_type"] != "emission_factor")
            {
                issues.Add(Issue(
                    request,
                    ParserValidationIssueSeverity.Warning,
                    "IPCC_EFDB_CONTENT_UNSUPPORTED_ROW_SKIPPED",
                    "IPCC EFDB content row was skipped because record_type is unsupported.",
                    artifact.ArtifactReference,
                    sourceRowNumber: sourceRowNumber,
                    fieldKey: "record_type",
                    context:
                    [
                        new ParserValidationIssueContext("record_type", row["record_type"]),
                    ]));
                continue;
            }

            var rowIssues = RowIssues(request, artifact, row, sourceRowNumber).ToArray();
            foreach (var rowIssue in rowIssues)
            {
                issues.Add(rowIssue);
            }

            if (rowIssues.Length > 0)
            {
                continue;
            }

            rows.Add(CreateOutputRow(request, artifact, row, sourceRowNumber));
        }
    }

    private static IEnumerable<ParserValidationIssue> RowIssues(
        ParserAdapterRunRequest request,
        ParserInputArtifact artifact,
        IReadOnlyDictionary<string, string> row,
        int sourceRowNumber)
    {
        foreach (var field in Header.Where(field => RequiredFields.Contains(field) && string.IsNullOrWhiteSpace(row[field])))
        {
            yield return Issue(
                request,
                ParserValidationIssueSeverity.Error,
                "IPCC_EFDB_CONTENT_MISSING_REQUIRED_FIELD",
                $"IPCC EFDB emission factor row is missing required field: {field}.",
                artifact.ArtifactReference,
                sourceRowNumber: sourceRowNumber,
                fieldKey: field,
                context:
                [
                    new ParserValidationIssueContext("row_number", sourceRowNumber.ToString(CultureInfo.InvariantCulture)),
                    new ParserValidationIssueContext("field_name", field),
                ]);
        }

        if (!int.TryParse(row["source_year"], NumberStyles.None, CultureInfo.InvariantCulture, out var sourceYear) ||
            sourceYear < 1)
        {
            yield return Issue(
                request,
                ParserValidationIssueSeverity.Error,
                "IPCC_EFDB_CONTENT_INVALID_SOURCE_YEAR",
                "IPCC EFDB source_year must be a positive integer.",
                artifact.ArtifactReference,
                sourceRowNumber: sourceRowNumber,
                fieldKey: "source_year",
                context:
                [
                    new ParserValidationIssueContext("row_number", sourceRowNumber.ToString(CultureInfo.InvariantCulture)),
                    new ParserValidationIssueContext("field_name", "source_year"),
                    new ParserValidationIssueContext("raw_value", row["source_year"]),
                ]);
        }

        if (!decimal.TryParse(row["factor_value"], NumberStyles.Number, CultureInfo.InvariantCulture, out _))
        {
            yield return Issue(
                request,
                ParserValidationIssueSeverity.Error,
                "IPCC_EFDB_CONTENT_INVALID_FACTOR_VALUE",
                "IPCC EFDB factor_value must be numeric.",
                artifact.ArtifactReference,
                sourceRowNumber: sourceRowNumber,
                fieldKey: "factor_value",
                context:
                [
                    new ParserValidationIssueContext("row_number", sourceRowNumber.ToString(CultureInfo.InvariantCulture)),
                    new ParserValidationIssueContext("field_name", "factor_value"),
                    new ParserValidationIssueContext("raw_value", row["factor_value"]),
                ]);
        }
    }

    private static ParserNormalizedOutputRow CreateOutputRow(
        ParserAdapterRunRequest request,
        ParserInputArtifact artifact,
        IReadOnlyDictionary<string, string> row,
        int sourceRowNumber)
    {
        var sourceYear = int.Parse(row["source_year"], CultureInfo.InvariantCulture);
        var rowIdentifier = string.Join(
            "_",
            new[]
            {
                "ipcc_efdb",
                row["source_year"],
                row["source_version"],
                row["factor_id"],
                $"row_{sourceRowNumber.ToString(CultureInfo.InvariantCulture)}",
            });
        var masterId = $"ipcc_master_{row["source_year"]}_{row["source_version"]}_{row["factor_id"]}";
        var detailId = $"ipcc_detail_{row["source_year"]}_{row["source_version"]}_{row["factor_id"]}";

        return new ParserNormalizedOutputRow(
            SourceFamily.IpccEfdb,
            request.SourceKey,
            request.ParserKey,
            artifact.ArtifactReference,
            rowIdentifier,
            sourceRowNumber,
            [
                new ParserNormalizedField("source_family", SourceFamily.IpccEfdb.ToWireName()),
                new ParserNormalizedField("source_year", row["source_year"]),
                new ParserNormalizedField("source_version", row["source_version"]),
                new ParserNormalizedField("factor_id", row["factor_id"]),
                new ParserNormalizedField("factor_name", row["factor_name"]),
                new ParserNormalizedField("factor_value", row["factor_value"]),
                new ParserNormalizedField("unit", row["unit"]),
                new ParserNormalizedField("category", row["category"]),
                new ParserNormalizedField("subcategory", NullIfEmpty(row["subcategory"])),
                new ParserNormalizedField("ipcc_sector", row["ipcc_sector"]),
                new ParserNormalizedField("gas", row["gas"]),
                new ParserNormalizedField("region", NullIfEmpty(row["region"])),
                new ParserNormalizedField("technology", NullIfEmpty(row["technology"])),
                new ParserNormalizedField("provenance_artifact_reference", artifact.ArtifactReference),
                new ParserNormalizedField("provenance_checksum_algorithm", artifact.ChecksumAlgorithm),
                new ParserNormalizedField("provenance_checksum_value", artifact.ChecksumValue),
                new ParserNormalizedField("provenance_row_number", sourceRowNumber.ToString(CultureInfo.InvariantCulture)),
                new ParserNormalizedField("provenance", row["provenance"]),
                new ParserNormalizedField("source_family_master_id", masterId),
                new ParserNormalizedField("source_family_detail_id", detailId),
                new ParserNormalizedField("master_external_key", $"{row["source_year"]}:{row["source_version"]}:{row["factor_id"]}"),
                new ParserNormalizedField("detail_external_key", $"{row["factor_id"]}:{row["unit"]}:{row["gas"]}:{row["ipcc_sector"]}"),
            ],
            reportingYear: sourceYear);
    }

    private static ParserAdapterRunResult FailedResult(
        ParserAdapterRunRequest request,
        IEnumerable<ParserNormalizedOutputRow> rows,
        IEnumerable<ParserValidationIssue> issues) =>
        new(
            request.SourceFamily,
            request.SourceKey,
            request.ParserKey,
            ParserRunStatus.Failed,
            request.Artifacts.Select(artifact => artifact.ArtifactReference),
            rows,
            issues,
            request.RunId,
            request.CorrelationId,
            request.RequestedReportingYear);

    private static ParserValidationIssue Issue(
        ParserAdapterRunRequest request,
        ParserValidationIssueSeverity severity,
        string code,
        string message,
        string? artifactReference = null,
        string? rowIdentifier = null,
        int? sourceRowNumber = null,
        string? fieldKey = null,
        IEnumerable<ParserValidationIssueContext>? context = null) =>
        new(
            request.SourceFamily,
            request.SourceKey,
            request.ParserKey,
            severity,
            code,
            message,
            artifactReference,
            rowIdentifier,
            sourceRowNumber,
            fieldKey,
            context);

    private static IEnumerable<IReadOnlyList<string>> CsvRows(string content)
    {
        var row = new List<string>();
        var field = new List<char>();
        var inQuotes = false;

        for (var index = 0; index < content.Length; index++)
        {
            var current = content[index];
            if (inQuotes)
            {
                if (current == '"' && index + 1 < content.Length && content[index + 1] == '"')
                {
                    field.Add('"');
                    index++;
                    continue;
                }

                if (current == '"')
                {
                    inQuotes = false;
                    continue;
                }

                field.Add(current);
                continue;
            }

            switch (current)
            {
                case '"':
                    inQuotes = true;
                    break;
                case ',':
                    row.Add(new string(field.ToArray()));
                    field.Clear();
                    break;
                case '\r':
                    break;
                case '\n':
                    row.Add(new string(field.ToArray()));
                    field.Clear();
                    yield return row.ToArray();
                    row.Clear();
                    break;
                default:
                    field.Add(current);
                    break;
            }
        }

        if (field.Count > 0 || row.Count > 0)
        {
            row.Add(new string(field.ToArray()));
            yield return row.ToArray();
        }
    }

    private static string? NullIfEmpty(string value) =>
        string.IsNullOrWhiteSpace(value) ? null : value;
}
