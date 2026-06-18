namespace CarbonOps.Parser.Contracts;

public static class PostgreSQLRuntimeConfigGateEvaluator
{
    public static PostgreSQLRuntimeConfigGateDecision Evaluate(PostgreSQLRuntimeConfigGate? gate = null)
    {
        var activeGate = gate ?? new PostgreSQLRuntimeConfigGate();
        var requiredComponents = RequiredFutureComponents(activeGate);

        if (!activeGate.Requested)
        {
            return new PostgreSQLRuntimeConfigGateDecision(
                PostgreSQLRuntimeConfigGateStatus.Disabled,
                requested: false,
                reason: "PostgreSQL runtime configuration loading is disabled by default.",
                configLoadingEnabled: false,
                runtimeEnabled: false,
                loadsEnvironment: false,
                loadsConfigFiles: false,
                loadsCredentials: false,
                requiredFutureComponents: requiredComponents,
                safeOperationalNotes: SafeOperationalNotes(),
                issues:
                [
                    new PostgreSQLRuntimeConfigGateIssue(
                        "POSTGRESQL_RUNTIME_CONFIG_DISABLED_BY_DEFAULT",
                        "Runtime PostgreSQL configuration loading requires explicit future enablement and remains disabled."),
                ]);
        }

        var readyMetadataOnly = requiredComponents.Count == 0;

        return new PostgreSQLRuntimeConfigGateDecision(
            readyMetadataOnly
                ? PostgreSQLRuntimeConfigGateStatus.NotEnabled
                : PostgreSQLRuntimeConfigGateStatus.Blocked,
            requested: true,
            reason: RequestedReason(readyMetadataOnly),
            configLoadingEnabled: false,
            runtimeEnabled: false,
            loadsEnvironment: false,
            loadsConfigFiles: false,
            loadsCredentials: false,
            requiredFutureComponents: requiredComponents,
            safeOperationalNotes: SafeOperationalNotes(),
            issues: RequestedIssues(requiredComponents));
    }

    public static PostgreSQLRuntimeConfigGateDescription Describe() =>
        new(
            PostgreSQLRuntimeConfigGateStatus.Disabled,
            disabledByDefault: true,
            acceptsCallerIntent: true,
            loadsEnvironment: false,
            loadsConfigFiles: false,
            loadsCredentials: false,
            opensConnection: false,
            runsSql: false,
            [
                "Runtime configuration gate metadata only.",
                "Default decision is disabled/no-loading.",
                "Requested runtime configuration remains blocked in this boundary.",
                "No environment/config file/credential loading occurs.",
            ]);

    private static IReadOnlyList<string> RequiredFutureComponents(PostgreSQLRuntimeConfigGate gate)
    {
        var requiredComponents = new List<string>();

        if (!gate.SafetyGateApproved)
        {
            requiredComponents.Add("postgresql_implementation_safety_gate");
        }

        if (!gate.OptionsContractAvailable)
        {
            requiredComponents.Add("postgresql_persistence_options_contract");
        }

        if (!gate.ExplicitRuntimeOptIn)
        {
            requiredComponents.Add("explicit_runtime_configuration_opt_in");
        }

        if (!gate.SecretSourceApproved)
        {
            requiredComponents.Add("approved_secret_source");
        }

        return Array.AsReadOnly(requiredComponents.ToArray());
    }

    private static IReadOnlyList<PostgreSQLRuntimeConfigGateIssue> RequestedIssues(
        IReadOnlyList<string> requiredComponents)
    {
        if (requiredComponents.Count > 0)
        {
            return
            [
                new PostgreSQLRuntimeConfigGateIssue(
                    "POSTGRESQL_RUNTIME_CONFIG_BLOCKED",
                    "Runtime PostgreSQL configuration loading remains blocked until future safety-gated components are complete.",
                    FieldName: "requested"),
            ];
        }

        return
        [
            new PostgreSQLRuntimeConfigGateIssue(
                "POSTGRESQL_RUNTIME_CONFIG_NOT_ENABLED",
                "All supplied gate metadata is marked complete, but this boundary still does not enable runtime config loading.",
                FieldName: "requested"),
        ];
    }

    private static string RequestedReason(bool readyMetadataOnly) =>
        readyMetadataOnly
            ? "PostgreSQL runtime configuration was requested, but this boundary does not enable runtime config loading."
            : "PostgreSQL runtime configuration was requested, but this boundary does not enable config loading and required future components are not complete.";

    private static IReadOnlyList<string> SafeOperationalNotes() =>
    [
        "No environment variables are loaded.",
        "No config files are read.",
        "No credentials are loaded.",
        "No PostgreSQL connection is opened.",
        "No SQL runtime is created.",
    ];
}
