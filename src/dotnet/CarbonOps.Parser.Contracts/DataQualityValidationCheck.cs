namespace CarbonOps.Parser.Contracts;

public enum DataQualityValidationCheck
{
    RequiredField = 0,
    NumericValue = 1,
    Unit = 2,
    DuplicateFactorIdentity = 3,
    Provenance = 4,
    Structure = 5,
}
