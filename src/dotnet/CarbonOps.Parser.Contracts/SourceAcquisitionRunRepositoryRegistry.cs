namespace CarbonOps.Parser.Contracts;

public static class SourceAcquisitionRunRepositoryRegistry
{
    public static SourceAcquisitionRunRepositoryPersistResult CreatePersistResult(
        string providerName,
        IEnumerable<SourceAcquisitionRunResult?> runs,
        IEnumerable<SourceAcquisitionRunRepositoryIssue>? issues = null)
    {
        var runSnapshot = runs.ToArray();
        var collectedIssues = ValidateInputs(providerName, runSnapshot).Issues
            .Select(issue => new SourceAcquisitionRunRepositoryIssue(
                issue.Code,
                issue.Message,
                issue.FieldName,
                issue.Severity))
            .ToList();
        collectedIssues.AddRange(issues ?? []);

        var status = collectedIssues.Count == 0
            ? SourceAcquisitionRunRepositoryPersistStatus.Declared
            : SourceAcquisitionRunRepositoryPersistStatus.FailedValidation;

        return new SourceAcquisitionRunRepositoryPersistResult(
            providerName,
            status,
            status == SourceAcquisitionRunRepositoryPersistStatus.Declared ? runSnapshot.Length : 0,
            collectedIssues);
    }

    public static SourceAcquisitionRunRepositoryValidationResult ValidateInputs(
        string providerName,
        IEnumerable<SourceAcquisitionRunResult?> runs)
    {
        var errors = new List<SourceAcquisitionRunRepositoryIssue>();

        if (string.IsNullOrWhiteSpace(providerName))
        {
            errors.Add(new SourceAcquisitionRunRepositoryIssue(
                "SOURCE_ACQUISITION_RUN_REPOSITORY_MISSING_PROVIDER_NAME",
                "ProviderName must be a non-empty string.",
                "ProviderName"));
        }

        var runSnapshot = runs.ToArray();
        for (var index = 0; index < runSnapshot.Length; index++)
        {
            var run = runSnapshot[index];
            if (run is null)
            {
                errors.Add(new SourceAcquisitionRunRepositoryIssue(
                    "SOURCE_ACQUISITION_RUN_REPOSITORY_INVALID_RUN",
                    "Runs must contain SourceAcquisitionRunResult instances.",
                    $"Runs[{index}]"));
            }
        }

        return new SourceAcquisitionRunRepositoryValidationResult(errors);
    }
}
