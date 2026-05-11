namespace CarbonOps.Parser.Contracts;

public static class SourceDocumentRepositoryRegistry
{
    public static SourceDocumentRepositoryPersistResult CreatePersistResult(
        string providerName,
        IEnumerable<SourceDocumentPersistenceRecord?> records,
        IEnumerable<SourceDocumentRepositoryIssue>? issues = null)
    {
        var recordSnapshot = records.ToArray();
        var collectedIssues = ValidateInputs(providerName, recordSnapshot).Issues
            .Select(issue => new SourceDocumentRepositoryIssue(
                issue.Code,
                issue.Message,
                issue.FieldName,
                issue.Severity))
            .ToList();
        collectedIssues.AddRange(issues ?? []);

        var status = collectedIssues.Count == 0
            ? SourceDocumentRepositoryPersistStatus.Declared
            : SourceDocumentRepositoryPersistStatus.FailedValidation;

        return new SourceDocumentRepositoryPersistResult(
            providerName,
            status,
            status == SourceDocumentRepositoryPersistStatus.Declared ? recordSnapshot.Length : 0,
            collectedIssues);
    }

    public static SourceDocumentRepositoryValidationResult ValidateInputs(
        string providerName,
        IEnumerable<SourceDocumentPersistenceRecord?> records)
    {
        var errors = new List<SourceDocumentRepositoryIssue>();

        if (string.IsNullOrWhiteSpace(providerName))
        {
            errors.Add(new SourceDocumentRepositoryIssue(
                "SOURCE_DOCUMENT_REPOSITORY_MISSING_PROVIDER_NAME",
                "ProviderName must be a non-empty string.",
                "ProviderName"));
        }

        var recordSnapshot = records.ToArray();
        for (var index = 0; index < recordSnapshot.Length; index++)
        {
            var record = recordSnapshot[index];
            if (record is null)
            {
                errors.Add(new SourceDocumentRepositoryIssue(
                    "SOURCE_DOCUMENT_REPOSITORY_INVALID_RECORD",
                    "Records must contain SourceDocumentPersistenceRecord instances.",
                    $"Records[{index}]"));
            }
        }

        return new SourceDocumentRepositoryValidationResult(errors);
    }
}
