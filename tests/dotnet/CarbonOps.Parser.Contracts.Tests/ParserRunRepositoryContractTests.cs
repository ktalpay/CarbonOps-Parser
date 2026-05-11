using System.Reflection;
using CarbonOps.Parser.Contracts;

namespace CarbonOps.Parser.Contracts.Tests;

public sealed class ParserRunRepositoryContractTests
{
    [Fact]
    public void ParserRunRepositoryInterfaceSupportsMetadataOnlyPersistenceContract()
    {
        IParserRunRepository repository = new InMemoryParserRunRepository();

        var result = repository.PersistRuns(ParserRunResultRegistry.CreateDefaultDryRunResultSet().Results);

        Assert.Equal("in_memory", repository.ProviderName);
        Assert.Equal(ParserRunRepositoryPersistStatus.Declared, result.Status);
        Assert.Equal(3, result.PersistedCount);
        Assert.Empty(result.Issues);
    }

    [Fact]
    public void ParserRunRepositoryValidationRequiresProviderName()
    {
        var validation = ParserRunRepositoryRegistry.ValidateInputs(
            "",
            ParserRunResultRegistry.CreateDefaultDryRunResultSet().Results);

        Assert.False(validation.IsValid);
        Assert.Equal(
            "PARSER_RUN_REPOSITORY_MISSING_PROVIDER_NAME",
            validation.Issues[0].Code);
        Assert.Equal("ProviderName", validation.Issues[0].FieldName);
    }

    [Fact]
    public void ParserRunRepositoryValidationRejectsNullRuns()
    {
        var validation = ParserRunRepositoryRegistry.ValidateInputs(
            "in_memory",
            [null]);

        Assert.False(validation.IsValid);
        Assert.Equal("PARSER_RUN_REPOSITORY_INVALID_RUN", validation.Issues[0].Code);
        Assert.Equal("Runs[0]", validation.Issues[0].FieldName);
    }

    [Fact]
    public void ParserRunRepositoryPersistResultReportsValidationFailure()
    {
        var result = ParserRunRepositoryRegistry.CreatePersistResult(
            "",
            [null]);

        Assert.Equal(ParserRunRepositoryPersistStatus.FailedValidation, result.Status);
        Assert.Equal(0, result.PersistedCount);
        Assert.Equal(2, result.Issues.Count);
    }

    [Fact]
    public void ParserRunRepositoryPersistResultSnapshotsIssueCollections()
    {
        var issues = new List<ParserRunRepositoryIssue>
        {
            new("CUSTOM_REPOSITORY_WARNING", "custom issue", "Runs", "warning"),
        };

        var result = ParserRunRepositoryRegistry.CreatePersistResult(
            "in_memory",
            ParserRunResultRegistry.CreateDefaultDryRunResultSet().Results,
            issues);
        issues.Clear();

        Assert.Equal(ParserRunRepositoryPersistStatus.FailedValidation, result.Status);
        Assert.Equal(0, result.PersistedCount);
        Assert.Single(result.Issues);
        Assert.Equal("CUSTOM_REPOSITORY_WARNING", result.Issues[0].Code);
    }

    [Fact]
    public void ParserRunRepositoryPersistStatusValuesAreDeterministic()
    {
        Assert.Equal(
            [
                ParserRunRepositoryPersistStatus.Declared,
                ParserRunRepositoryPersistStatus.FailedValidation,
            ],
            Enum.GetValues<ParserRunRepositoryPersistStatus>());
    }

    [Fact]
    public void ParserRunRepositoryContractRemainsRuntimePassive()
    {
        var publicMembers = new[]
        {
            typeof(IParserRunRepository),
            typeof(ParserRunRepositoryIssue),
            typeof(ParserRunRepositoryPersistResult),
            typeof(ParserRunRepositoryRegistry),
            typeof(ParserRunRepositoryValidationResult),
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

    private sealed class InMemoryParserRunRepository : IParserRunRepository
    {
        public string ProviderName => "in_memory";

        public ParserRunRepositoryPersistResult PersistRuns(
            IEnumerable<ParserRunResult> runs)
        {
            return ParserRunRepositoryRegistry.CreatePersistResult(ProviderName, runs);
        }
    }
}
