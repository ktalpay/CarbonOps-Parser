using System.Reflection;
using CarbonOps.Parser.Contracts;

namespace CarbonOps.Parser.Contracts.Tests;

public sealed class PostgreSQLRuntimeConfigGateContractTests
{
    [Fact]
    public void DescriptionDeclaresRuntimePassiveBoundary()
    {
        var description = PostgreSQLRuntimeConfigGateEvaluator.Describe();

        Assert.Equal(PostgreSQLRuntimeConfigGateStatus.Disabled, description.DefaultStatus);
        Assert.True(description.DisabledByDefault);
        Assert.True(description.AcceptsCallerIntent);
        Assert.False(description.LoadsEnvironment);
        Assert.False(description.LoadsConfigFiles);
        Assert.False(description.LoadsCredentials);
        Assert.False(description.OpensConnection);
        Assert.False(description.RunsSql);
        Assert.Contains("Runtime configuration gate metadata only.", description.Notes);
    }

    [Fact]
    public void DefaultEvaluationIsDisabledAndDoesNotLoadRuntimeConfiguration()
    {
        var decision = PostgreSQLRuntimeConfigGateEvaluator.Evaluate();

        Assert.Equal(PostgreSQLRuntimeConfigGateStatus.Disabled, decision.Status);
        Assert.False(decision.Requested);
        Assert.False(decision.ConfigLoadingEnabled);
        Assert.False(decision.RuntimeEnabled);
        Assert.False(decision.LoadsEnvironment);
        Assert.False(decision.LoadsConfigFiles);
        Assert.False(decision.LoadsCredentials);
        Assert.Equal(4, decision.RequiredFutureComponentCount);
        Assert.Equal(1, decision.IssueCount);
        Assert.Equal("POSTGRESQL_RUNTIME_CONFIG_DISABLED_BY_DEFAULT", decision.Issues[0].Code);
    }

    [Fact]
    public void RequestedEvaluationIsBlockedUntilFutureGateMetadataIsComplete()
    {
        var decision = PostgreSQLRuntimeConfigGateEvaluator.Evaluate(
            new PostgreSQLRuntimeConfigGate(
                Requested: true,
                SafetyGateApproved: true));

        Assert.Equal(PostgreSQLRuntimeConfigGateStatus.Blocked, decision.Status);
        Assert.True(decision.Requested);
        Assert.False(decision.ConfigLoadingEnabled);
        Assert.False(decision.RuntimeEnabled);
        Assert.Equal(
            [
                "postgresql_persistence_options_contract",
                "explicit_runtime_configuration_opt_in",
                "approved_secret_source",
            ],
            decision.RequiredFutureComponents);
        Assert.Equal("POSTGRESQL_RUNTIME_CONFIG_BLOCKED", decision.Issues[0].Code);
        Assert.Equal("requested", decision.Issues[0].FieldName);
    }

    [Fact]
    public void CompleteCallerMetadataStillDoesNotEnableRuntimeConfigurationLoading()
    {
        var decision = PostgreSQLRuntimeConfigGateEvaluator.Evaluate(
            new PostgreSQLRuntimeConfigGate(
                Requested: true,
                SafetyGateApproved: true,
                OptionsContractAvailable: true,
                ExplicitRuntimeOptIn: true,
                SecretSourceApproved: true));

        Assert.Equal(PostgreSQLRuntimeConfigGateStatus.NotEnabled, decision.Status);
        Assert.True(decision.Requested);
        Assert.False(decision.ConfigLoadingEnabled);
        Assert.False(decision.RuntimeEnabled);
        Assert.Empty(decision.RequiredFutureComponents);
        Assert.Equal("POSTGRESQL_RUNTIME_CONFIG_NOT_ENABLED", decision.Issues[0].Code);
        Assert.Contains("does not enable runtime config loading", decision.Reason);
    }

    [Fact]
    public void DecisionsSnapshotCollectionInputs()
    {
        var requiredComponents = new List<string> { "component" };
        var notes = new List<string> { "note" };
        var issues = new List<PostgreSQLRuntimeConfigGateIssue>
        {
            new("CODE", "message"),
        };

        var decision = new PostgreSQLRuntimeConfigGateDecision(
            PostgreSQLRuntimeConfigGateStatus.Blocked,
            requested: true,
            reason: "reason",
            configLoadingEnabled: false,
            runtimeEnabled: false,
            loadsEnvironment: false,
            loadsConfigFiles: false,
            loadsCredentials: false,
            requiredFutureComponents: requiredComponents,
            safeOperationalNotes: notes,
            issues: issues);
        requiredComponents.Clear();
        notes.Clear();
        issues.Clear();

        Assert.Equal(1, decision.RequiredFutureComponentCount);
        Assert.Single(decision.SafeOperationalNotes);
        Assert.Equal(1, decision.IssueCount);
    }

    [Fact]
    public void StatusValuesMapToStableWireNames()
    {
        Assert.Equal(
            [
                PostgreSQLRuntimeConfigGateStatus.Disabled,
                PostgreSQLRuntimeConfigGateStatus.Blocked,
                PostgreSQLRuntimeConfigGateStatus.NotEnabled,
            ],
            Enum.GetValues<PostgreSQLRuntimeConfigGateStatus>());
        Assert.Equal("disabled", PostgreSQLRuntimeConfigGateStatus.Disabled.ToWireName());
        Assert.Equal("blocked", PostgreSQLRuntimeConfigGateStatus.Blocked.ToWireName());
        Assert.Equal("not_enabled", PostgreSQLRuntimeConfigGateStatus.NotEnabled.ToWireName());
        Assert.True(ContractWireNames.TryParsePostgreSQLRuntimeConfigGateStatusWireName("disabled", out var disabled));
        Assert.True(ContractWireNames.TryParsePostgreSQLRuntimeConfigGateStatusWireName("blocked", out var blocked));
        Assert.True(
            ContractWireNames.TryParsePostgreSQLRuntimeConfigGateStatusWireName(
                "not_enabled",
                out var notEnabled));
        Assert.False(ContractWireNames.TryParsePostgreSQLRuntimeConfigGateStatusWireName("enabled", out _));

        Assert.Equal(PostgreSQLRuntimeConfigGateStatus.Disabled, disabled);
        Assert.Equal(PostgreSQLRuntimeConfigGateStatus.Blocked, blocked);
        Assert.Equal(PostgreSQLRuntimeConfigGateStatus.NotEnabled, notEnabled);
        Assert.Throws<ArgumentOutOfRangeException>(() => ((PostgreSQLRuntimeConfigGateStatus)999).ToWireName());
    }

    [Fact]
    public void RuntimeConfigGatePublicApiIsRuntimePassive()
    {
        var evaluatorMethods = typeof(PostgreSQLRuntimeConfigGateEvaluator)
            .GetMethods(BindingFlags.Public | BindingFlags.Static | BindingFlags.DeclaredOnly)
            .Select(method => method.Name)
            .ToArray();
        var blockedMethodNames = new[]
        {
            "Load",
            "Read",
            "Connect",
            "Open",
            "Execute",
            "Run",
            "Migrate",
            "Create",
            "Drop",
            "Delete",
        };

        Assert.Equal(["Evaluate", "Describe"], evaluatorMethods);

        foreach (var methodName in blockedMethodNames)
        {
            Assert.DoesNotContain(evaluatorMethods, method => method.Contains(methodName, StringComparison.OrdinalIgnoreCase));
        }
    }
}
