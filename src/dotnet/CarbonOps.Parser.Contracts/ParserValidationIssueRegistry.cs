namespace CarbonOps.Parser.Contracts;

public static class ParserValidationIssueRegistry
{
    public static ParserValidationIssueBatch CreateDefaultDryRunBatch() =>
        new(ParserNormalizedOutputRegistry.CreateDefaultDryRunBatch()
            .Rows
            .Select(ParserValidationIssue.FromNormalizedRow));
}
