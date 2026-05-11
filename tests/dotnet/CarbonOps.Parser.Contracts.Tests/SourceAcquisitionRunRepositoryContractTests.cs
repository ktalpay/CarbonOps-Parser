using System.Reflection;
using CarbonOps.Parser.Contracts;

namespace CarbonOps.Parser.Contracts.Tests;

public sealed class SourceAcquisitionRunRepositoryContractTests
{
    [Fact]
    public void SourceAcquisitionRunRepositoryInterfaceSupportsMetadataOnlyPersistenceContract()
    {
        ISourceAcquisitionRunRepository repository = new InMemorySourceAcquisitionRunRepository();

        var result = repository.PersistRuns(SourceAcquisitionRunRegistry.CreateDefaultRunResults());

        Assert.Equal("in_memory", repository.ProviderName);
        Assert.Equal(SourceAcquisitionRunRepositoryPersistStatus.Declared, result.Status);
        Assert.Equal(3, result.PersistedCount);
        Assert.Empty(result.Issues);
    }

    [Fact]
    public void SourceAcquisitionRunRepositoryValidationRequiresProviderName()
    {
        var validation = SourceAcquisitionRunRepositoryRegistry.ValidateInputs(
            "",
            SourceAcquisitionRunRegistry.CreateDefaultRunResults());

        Assert.False(validation.IsValid);
        Assert.Equal(
            "SOURCE_ACQUISITION_RUN_REPOSITORY_MISSING_PROVIDER_NAME",
            validation.Issues[0].Code);
        Assert.Equal("ProviderName", validation.Issues[0].FieldName);
    }

    [Fact]
    public void SourceAcquisitionRunRepositoryValidationRejectsNullRuns()
    {
        var validation = SourceAcquisitionRunRepositoryRegistry.ValidateInputs(
            "in_memory",
            [null]);

        Assert.False(validation.IsValid);
        Assert.Equal("SOURCE_ACQUISITION_RUN_REPOSITORY_INVALID_RUN", validation.Issues[0].Code);
        Assert.Equal("Runs[0]", validation.Issues[0].FieldName);
    }

    [Fact]
    public void SourceAcquisitionRunRepositoryPersistResultReportsValidationFailure()
    {
        var result = SourceAcquisitionRunRepositoryRegistry.CreatePersistResult(
            "",
            [null]);

        Assert.Equal(SourceAcquisitionRunRepositoryPersistStatus.FailedValidation, result.Status);
        Assert.Equal(0, result.PersistedCount);
        Assert.Equal(2, result.Issues.Count);
    }

    [Fact]
    public void SourceAcquisitionRunRepositoryPersistResultSnapshotsIssueCollections()
    {
        var issues = new List<SourceAcquisitionRunRepositoryIssue>
        {
            new("CUSTOM_REPOSITORY_WARNING", "custom issue", "Runs", "warning"),
        };

        var result = SourceAcquisitionRunRepositoryRegistry.CreatePersistResult(
            "in_memory",
            SourceAcquisitionRunRegistry.CreateDefaultRunResults(),
            issues);
        issues.Clear();

        Assert.Equal(SourceAcquisitionRunRepositoryPersistStatus.FailedValidation, result.Status);
        Assert.Equal(0, result.PersistedCount);
        Assert.Single(result.Issues);
        Assert.Equal("CUSTOM_REPOSITORY_WARNING", result.Issues[0].Code);
    }

    [Fact]
    public void SourceAcquisitionRunRepositoryPersistStatusValuesAreDeterministic()
    {
        Assert.Equal(
            [
                SourceAcquisitionRunRepositoryPersistStatus.Declared,
                SourceAcquisitionRunRepositoryPersistStatus.FailedValidation,
            ],
            Enum.GetValues<SourceAcquisitionRunRepositoryPersistStatus>());
    }

    [Fact]
    public void SourceAcquisitionRunRepositoryContractRemainsRuntimePassive()
    {
        var publicMembers = new[]
        {
            typeof(ISourceAcquisitionRunRepository),
            typeof(SourceAcquisitionRunRepositoryIssue),
            typeof(SourceAcquisitionRunRepositoryPersistResult),
            typeof(SourceAcquisitionRunRepositoryRegistry),
            typeof(SourceAcquisitionRunRepositoryValidationResult),
        }
            .SelectMany(type => type.GetMembers(BindingFlags.Public | BindingFlags.Static | BindingFlags.Instance | BindingFlags.DeclaredOnly))
            .Select(member => member.Name)
            .ToArray();
        var blockedTerms = new[]
        {
            "Db",
            "Sql",
            "Postgres",
            "Http",
            "Open",
            "ReadFile",
            "Write",
            "StatFile",
            "Exists",
            "Fetch",
            "Calculate",
            "Factor",
        };

        foreach (var term in blockedTerms)
        {
            Assert.DoesNotContain(publicMembers, member => member.Contains(term, StringComparison.OrdinalIgnoreCase));
        }

        Assert.DoesNotContain("Parse", publicMembers);
        Assert.DoesNotContain("Execute", publicMembers);
    }

    private sealed class InMemorySourceAcquisitionRunRepository : ISourceAcquisitionRunRepository
    {
        public string ProviderName => "in_memory";

        public SourceAcquisitionRunRepositoryPersistResult PersistRuns(
            IEnumerable<SourceAcquisitionRunResult> runs)
        {
            return SourceAcquisitionRunRepositoryRegistry.CreatePersistResult(ProviderName, runs);
        }
    }
}
