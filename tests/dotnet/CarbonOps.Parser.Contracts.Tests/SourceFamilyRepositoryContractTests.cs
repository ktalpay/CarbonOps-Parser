using System.Reflection;
using CarbonOps.Parser.Contracts;

namespace CarbonOps.Parser.Contracts.Tests;

public sealed class SourceFamilyRepositoryContractTests
{
    [Fact]
    public void SourceFamilyRepositoryTypesArePublic()
    {
        var publicContractTypes = new[]
        {
            typeof(ISourceFamilyRepository),
            typeof(SourceFamilyMasterRecord),
            typeof(SourceFamilyDetailRecord),
            typeof(SourceFamilyRepositoryPersistStatus),
            typeof(SourceFamilyRepositoryIssue),
            typeof(SourceFamilyRepositoryPersistResult),
            typeof(SourceFamilyRepositoryValidationResult),
            typeof(SourceFamilyRepositoryTableNames),
            typeof(SourceFamilyRepositoryRegistry),
        };

        Assert.Equal(
            [
                "ISourceFamilyRepository",
                "SourceFamilyMasterRecord",
                "SourceFamilyDetailRecord",
                "SourceFamilyRepositoryPersistStatus",
                "SourceFamilyRepositoryIssue",
                "SourceFamilyRepositoryPersistResult",
                "SourceFamilyRepositoryValidationResult",
                "SourceFamilyRepositoryTableNames",
                "SourceFamilyRepositoryRegistry",
            ],
            publicContractTypes.Select(type => type.Name));
        Assert.All(publicContractTypes, type => Assert.True(type.IsPublic, $"{type.Name} must be public."));
    }

    [Fact]
    public void SourceFamilyRepositoryInterfaceSupportsMetadataOnlyPersistenceContract()
    {
        ISourceFamilyRepository repository = new InMemorySourceFamilyRepository();

        var result = repository.PersistSourceFamilyRecords(
            [CreateMasterRecord()],
            [CreateDetailRecord()]);

        Assert.Equal("in_memory", repository.ProviderName);
        Assert.Equal(SourceFamilyRepositoryPersistStatus.Declared, result.Status);
        Assert.Equal(1, result.PersistedMasterCount);
        Assert.Equal(1, result.PersistedDetailCount);
        Assert.Empty(result.Issues);
    }

    [Fact]
    public void SourceFamilyRepositoryValidationRequiresProviderName()
    {
        var validation = SourceFamilyRepositoryRegistry.ValidateInputs(
            "",
            [CreateMasterRecord()],
            [CreateDetailRecord()]);

        Assert.False(validation.IsValid);
        Assert.Equal("SOURCE_FAMILY_REPOSITORY_MISSING_PROVIDER_NAME", validation.Issues[0].Code);
        Assert.Equal("ProviderName", validation.Issues[0].FieldName);
    }

    [Fact]
    public void SourceFamilyRepositoryValidationRejectsNullRecords()
    {
        var validation = SourceFamilyRepositoryRegistry.ValidateInputs(
            "in_memory",
            [null],
            [null]);

        Assert.False(validation.IsValid);
        Assert.Equal("SOURCE_FAMILY_REPOSITORY_INVALID_MASTER_RECORD", validation.Issues[0].Code);
        Assert.Equal("MasterRecords[0]", validation.Issues[0].FieldName);
        Assert.Equal("SOURCE_FAMILY_REPOSITORY_INVALID_DETAIL_RECORD", validation.Issues[1].Code);
        Assert.Equal("DetailRecords[0]", validation.Issues[1].FieldName);
    }

    [Fact]
    public void SourceFamilyRepositoryValidationRejectsMissingRequiredFields()
    {
        var validation = SourceFamilyRepositoryRegistry.ValidateInputs(
            "in_memory",
            [CreateMasterRecord(sourceFamilyMasterId: "")],
            []);

        Assert.False(validation.IsValid);
        Assert.Equal("SOURCE_FAMILY_REPOSITORY_MISSING_REQUIRED_FIELD", validation.Issues[0].Code);
        Assert.Equal("MasterRecords[0].SourceFamilyMasterId", validation.Issues[0].FieldName);
    }

    [Fact]
    public void SourceFamilyRepositoryValidationRequiresDetailMasterReference()
    {
        var validation = SourceFamilyRepositoryRegistry.ValidateInputs(
            "in_memory",
            [CreateMasterRecord()],
            [CreateDetailRecord(sourceFamilyMasterId: "missing_master")]);

        Assert.False(validation.IsValid);
        Assert.Equal("SOURCE_FAMILY_REPOSITORY_DETAIL_MASTER_NOT_DECLARED", validation.Issues[0].Code);
        Assert.Equal("DetailRecords[0].SourceFamilyMasterId", validation.Issues[0].FieldName);
    }

    [Fact]
    public void SourceFamilyRepositoryValidationRequiresDetailMasterReferenceForSameSourceFamily()
    {
        var validation = SourceFamilyRepositoryRegistry.ValidateInputs(
            "in_memory",
            [CreateMasterRecord(SourceFamily.DefraDesnz, sourceFamilyMasterId: "shared_master")],
            [CreateDetailRecord(SourceFamily.IpccEfdb, sourceFamilyMasterId: "shared_master")]);

        Assert.False(validation.IsValid);
        Assert.Equal("SOURCE_FAMILY_REPOSITORY_DETAIL_MASTER_NOT_DECLARED", validation.Issues[0].Code);
    }

    [Fact]
    public void SourceFamilyRepositoryPersistResultReportsValidationFailure()
    {
        var result = SourceFamilyRepositoryRegistry.CreatePersistResult(
            "",
            [null],
            [null]);

        Assert.Equal(SourceFamilyRepositoryPersistStatus.FailedValidation, result.Status);
        Assert.Equal(0, result.PersistedMasterCount);
        Assert.Equal(0, result.PersistedDetailCount);
        Assert.Equal(3, result.Issues.Count);
    }

    [Fact]
    public void SourceFamilyRepositoryPersistResultSnapshotsInputAndIssueCollections()
    {
        var masterRecords = new List<SourceFamilyMasterRecord> { CreateMasterRecord() };
        var detailRecords = new List<SourceFamilyDetailRecord> { CreateDetailRecord() };
        var issues = new List<SourceFamilyRepositoryIssue>
        {
            new("CUSTOM_SOURCE_FAMILY_REPOSITORY_WARNING", "custom issue", "MasterRecords", "warning"),
        };

        var result = SourceFamilyRepositoryRegistry.CreatePersistResult(
            "in_memory",
            masterRecords,
            detailRecords,
            issues);
        masterRecords.Clear();
        detailRecords.Clear();
        issues.Clear();

        Assert.Equal(SourceFamilyRepositoryPersistStatus.FailedValidation, result.Status);
        Assert.Equal(0, result.PersistedMasterCount);
        Assert.Equal(0, result.PersistedDetailCount);
        Assert.Single(result.Issues);
        Assert.Equal("CUSTOM_SOURCE_FAMILY_REPOSITORY_WARNING", result.Issues[0].Code);
    }

    [Fact]
    public void SourceFamilyRepositoryExposesCatalogTableNames()
    {
        Assert.Equal(
            new SourceFamilyRepositoryTableNames(
                "ghg_emission_factor_masters",
                "ghg_emission_factor_details"),
            SourceFamilyRepositoryRegistry.GetTableNames(SourceFamily.GhgProtocol));
        Assert.Equal(
            new SourceFamilyRepositoryTableNames(
                "defra_emission_factor_masters",
                "defra_emission_factor_details"),
            SourceFamilyRepositoryRegistry.GetTableNames(SourceFamily.DefraDesnz));
        Assert.Equal(
            new SourceFamilyRepositoryTableNames(
                "ipcc_emission_factor_masters",
                "ipcc_emission_factor_details"),
            SourceFamilyRepositoryRegistry.GetTableNames(SourceFamily.IpccEfdb));
    }

    [Fact]
    public void SourceFamilyRepositoryPersistStatusValuesAreDeterministic()
    {
        Assert.Equal(
            [
                SourceFamilyRepositoryPersistStatus.Declared,
                SourceFamilyRepositoryPersistStatus.FailedValidation,
            ],
            Enum.GetValues<SourceFamilyRepositoryPersistStatus>());
    }

    [Fact]
    public void SourceFamilyRepositoryContractRemainsRuntimePassive()
    {
        var publicMembers = new[]
        {
            typeof(ISourceFamilyRepository),
            typeof(SourceFamilyMasterRecord),
            typeof(SourceFamilyDetailRecord),
            typeof(SourceFamilyRepositoryIssue),
            typeof(SourceFamilyRepositoryPersistResult),
            typeof(SourceFamilyRepositoryRegistry),
            typeof(SourceFamilyRepositoryValidationResult),
            typeof(SourceFamilyRepositoryTableNames),
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
        };

        foreach (var term in blockedTerms)
        {
            Assert.DoesNotContain(publicMembers, member => member.Contains(term, StringComparison.OrdinalIgnoreCase));
        }

        Assert.DoesNotContain("Parse", publicMembers);
        Assert.DoesNotContain("Execute", publicMembers);
    }

    private static SourceFamilyMasterRecord CreateMasterRecord(
        SourceFamily sourceFamily = SourceFamily.DefraDesnz,
        string sourceFamilyMasterId = "defra_master_001")
    {
        return new SourceFamilyMasterRecord(
            sourceFamily,
            sourceFamilyMasterId,
            "source_document_001",
            "defra_2025_publication",
            "declared",
            null,
            null,
            "checksum_master_001",
            "dry_run_timestamp_unavailable",
            "dry_run_timestamp_unavailable");
    }

    private static SourceFamilyDetailRecord CreateDetailRecord(
        SourceFamily sourceFamily = SourceFamily.DefraDesnz,
        string sourceFamilyMasterId = "defra_master_001")
    {
        return new SourceFamilyDetailRecord(
            sourceFamily,
            "defra_detail_001",
            sourceFamilyMasterId,
            "defra_row_001",
            "1.25",
            "kgco2e",
            "declared",
            "checksum_detail_001",
            "dry_run_timestamp_unavailable",
            "dry_run_timestamp_unavailable");
    }

    private sealed class InMemorySourceFamilyRepository : ISourceFamilyRepository
    {
        public string ProviderName => "in_memory";

        public SourceFamilyRepositoryPersistResult PersistSourceFamilyRecords(
            IEnumerable<SourceFamilyMasterRecord> masterRecords,
            IEnumerable<SourceFamilyDetailRecord> detailRecords)
        {
            return SourceFamilyRepositoryRegistry.CreatePersistResult(
                ProviderName,
                masterRecords,
                detailRecords);
        }
    }
}
