namespace CarbonOps.Parser.Contracts;

public static class ParserRunRepositoryRegistry
{
    public static ParserRunRepositoryPersistResult CreatePersistResult(
        string providerName,
        IEnumerable<ParserRunResult?> runs,
        IEnumerable<ParserRunRepositoryIssue>? issues = null)
    {
        var runSnapshot = runs.ToArray();
        var collectedIssues = ValidateInputs(providerName, runSnapshot).Issues
            .Select(issue => new ParserRunRepositoryIssue(
                issue.Code,
                issue.Message,
                issue.FieldName,
                issue.Severity))
            .ToList();
        collectedIssues.AddRange(issues ?? []);

        var status = collectedIssues.Count == 0
            ? ParserRunRepositoryPersistStatus.Declared
            : ParserRunRepositoryPersistStatus.FailedValidation;

        return new ParserRunRepositoryPersistResult(
            providerName,
            status,
            status == ParserRunRepositoryPersistStatus.Declared ? runSnapshot.Length : 0,
            collectedIssues);
    }

    public static ParserRunRepositoryValidationResult ValidateInputs(
        string providerName,
        IEnumerable<ParserRunResult?> runs)
    {
        var errors = new List<ParserRunRepositoryIssue>();

        if (string.IsNullOrWhiteSpace(providerName))
        {
            errors.Add(new ParserRunRepositoryIssue(
                "PARSER_RUN_REPOSITORY_MISSING_PROVIDER_NAME",
                "ProviderName must be a non-empty string.",
                "ProviderName"));
        }

        var runSnapshot = runs.ToArray();
        for (var index = 0; index < runSnapshot.Length; index++)
        {
            var run = runSnapshot[index];
            if (run is null)
            {
                errors.Add(new ParserRunRepositoryIssue(
                    "PARSER_RUN_REPOSITORY_INVALID_RUN",
                    "Runs must contain ParserRunResult instances.",
                    $"Runs[{index}]"));
            }
        }

        return new ParserRunRepositoryValidationResult(errors);
    }
}
