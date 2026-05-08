namespace CarbonOps.Parser.Contracts;

public sealed record ContractValidationResult(IReadOnlyList<string> Errors)
{
    public bool IsValid => Errors.Count == 0;

    public static ContractValidationResult Valid { get; } = new(Array.Empty<string>());

    public static ContractValidationResult FromErrors(IEnumerable<string> errors)
    {
        var collectedErrors = errors.ToArray();

        return collectedErrors.Length == 0
            ? Valid
            : new ContractValidationResult(collectedErrors);
    }
}
