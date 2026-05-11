using System.Reflection;
using CarbonOps.Parser.Contracts;

namespace CarbonOps.Parser.Contracts.Tests;

public sealed class SourceDocumentRepositoryContractTests
{
    [Fact]
    public void SourceDocumentRepositoryTypesArePublic()
    {
        var publicContractTypes = new[]
        {
            typeof(ISourceDocumentRepository),
            typeof(SourceDocumentRepositoryPersistStatus),
            typeof(SourceDocumentRepositoryIssue),
            typeof(SourceDocumentRepositoryPersistResult),
            typeof(SourceDocumentRepositoryValidationResult),
            typeof(SourceDocumentRepositoryRegistry),
        };

        Assert.Equal(
            [
                "ISourceDocumentRepository",
                "SourceDocumentRepositoryPersistStatus",
                "SourceDocumentRepositoryIssue",
                "SourceDocumentRepositoryPersistResult",
                "SourceDocumentRepositoryValidationResult",
                "SourceDocumentRepositoryRegistry",
            ],
            publicContractTypes.Select(type => type.Name));
        Assert.All(publicContractTypes, type => Assert.True(type.IsPublic, $"{type.Name} must be public."));
    }

    [Fact]
    public void SourceDocumentRepositoryInterfaceSupportsMetadataOnlyPersistenceContract()
    {
        ISourceDocumentRepository repository = new InMemorySourceDocumentRepository();

        var result = repository.PersistSourceDocuments(
            SourceDocumentPersistenceMapper.MapDefaultDryRunManifest().Records);

        Assert.Equal("in_memory", repository.ProviderName);
        Assert.Equal(SourceDocumentRepositoryPersistStatus.Declared, result.Status);
        Assert.Equal(3, result.PersistedCount);
        Assert.Empty(result.Issues);
    }

    [Fact]
    public void SourceDocumentRepositoryValidationRequiresProviderName()
    {
        var validation = SourceDocumentRepositoryRegistry.ValidateInputs(
            "",
            SourceDocumentPersistenceMapper.MapDefaultDryRunManifest().Records);

        Assert.False(validation.IsValid);
        Assert.Equal("SOURCE_DOCUMENT_REPOSITORY_MISSING_PROVIDER_NAME", validation.Issues[0].Code);
        Assert.Equal("ProviderName", validation.Issues[0].FieldName);
    }

    [Fact]
    public void SourceDocumentRepositoryValidationRejectsNullRecords()
    {
        var validation = SourceDocumentRepositoryRegistry.ValidateInputs(
            "in_memory",
            [null]);

        Assert.False(validation.IsValid);
        Assert.Equal("SOURCE_DOCUMENT_REPOSITORY_INVALID_RECORD", validation.Issues[0].Code);
        Assert.Equal("Records[0]", validation.Issues[0].FieldName);
    }

    [Fact]
    public void SourceDocumentRepositoryPersistResultReportsValidationFailure()
    {
        var result = SourceDocumentRepositoryRegistry.CreatePersistResult(
            "",
            [null]);

        Assert.Equal(SourceDocumentRepositoryPersistStatus.FailedValidation, result.Status);
        Assert.Equal(0, result.PersistedCount);
        Assert.Equal(2, result.Issues.Count);
    }

    [Fact]
    public void SourceDocumentRepositoryPersistResultSnapshotsIssueCollections()
    {
        var issues = new List<SourceDocumentRepositoryIssue>
        {
            new("CUSTOM_SOURCE_DOCUMENT_REPOSITORY_WARNING", "custom issue", "Records", "warning"),
        };

        var result = SourceDocumentRepositoryRegistry.CreatePersistResult(
            "in_memory",
            SourceDocumentPersistenceMapper.MapDefaultDryRunManifest().Records,
            issues);
        issues.Clear();

        Assert.Equal(SourceDocumentRepositoryPersistStatus.FailedValidation, result.Status);
        Assert.Equal(0, result.PersistedCount);
        Assert.Single(result.Issues);
        Assert.Equal("CUSTOM_SOURCE_DOCUMENT_REPOSITORY_WARNING", result.Issues[0].Code);
    }

    [Fact]
    public void SourceDocumentRepositoryPersistStatusValuesAreDeterministic()
    {
        Assert.Equal(
            [
                SourceDocumentRepositoryPersistStatus.Declared,
                SourceDocumentRepositoryPersistStatus.FailedValidation,
            ],
            Enum.GetValues<SourceDocumentRepositoryPersistStatus>());
    }

    [Fact]
    public void SourceDocumentRepositoryContractRemainsRuntimePassive()
    {
        var publicMembers = new[]
        {
            typeof(ISourceDocumentRepository),
            typeof(SourceDocumentRepositoryIssue),
            typeof(SourceDocumentRepositoryPersistResult),
            typeof(SourceDocumentRepositoryRegistry),
            typeof(SourceDocumentRepositoryValidationResult),
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

    private sealed class InMemorySourceDocumentRepository : ISourceDocumentRepository
    {
        public string ProviderName => "in_memory";

        public SourceDocumentRepositoryPersistResult PersistSourceDocuments(
            IEnumerable<SourceDocumentPersistenceRecord> records)
        {
            return SourceDocumentRepositoryRegistry.CreatePersistResult(ProviderName, records);
        }
    }
}
