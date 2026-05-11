namespace CarbonOps.Parser.Contracts;

public sealed record PostgreSQLRuntimeConfigGate(
    bool Requested = false,
    bool SafetyGateApproved = false,
    bool OptionsContractAvailable = false,
    bool ExplicitRuntimeOptIn = false,
    bool SecretSourceApproved = false);
