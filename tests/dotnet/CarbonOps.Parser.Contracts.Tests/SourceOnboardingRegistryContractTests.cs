using System.Reflection;
using CarbonOps.Parser.Contracts;

namespace CarbonOps.Parser.Contracts.Tests;

public sealed class SourceOnboardingRegistryContractTests
{
    [Fact]
    public void Phase2SourceOnboardingRegistryContainsPhaseOneSourceFamilies()
    {
        var registry = SourceOnboardingRegistry.CreatePhase2SourceOnboardingRegistry();

        Assert.Equal(3, registry.EntryCount);
        Assert.Equal(
            [
                "ghg_protocol",
                "defra_desnz",
                "ipcc_efdb",
            ],
            registry.Entries.Select(entry => entry.SourceFamily));
        Assert.Equal(["ghg_protocol", "defra_desnz", "ipcc_efdb"], SourceOnboardingRegistry.Phase2OnboardingSourceFamilies);
        Assert.Equal(["ghg_protocol", "defra_desnz", "ipcc_efdb"], registry.Entries.Select(entry => entry.SourceId));
        Assert.All(registry.Entries, entry => Assert.True(entry.Enabled));
    }

    [Fact]
    public void Phase2SourceOnboardingRegistryRepresentsFutureOnboardingMetadata()
    {
        var registry = SourceOnboardingRegistry.CreatePhase2SourceOnboardingRegistry();

        foreach (var entry in registry.Entries)
        {
            Assert.Equal(SourceOnboardingDiscoveryStrategy.DeclaredReference, entry.DiscoveryStrategy);
            Assert.Equal(SourceOnboardingUpdateCadence.Unknown, entry.UpdateCadence);
            Assert.Equal(ExpectedParserKey(entry.SourceFamily), entry.ParserCapability.ParserKey);
            Assert.Equal(ParserSourceFormat.DiscoveryReference, entry.ParserCapability.ParserSourceFormat);
            Assert.Equal(
                ["document_id", "display_name", "source_reference", "expected_format"],
                entry.ValidationExpectations.RequiredDocumentFields);
            Assert.StartsWith($"discovery://{entry.SourceId}/", entry.Documents[0].SourceReference, StringComparison.Ordinal);
        }
    }

    [Fact]
    public void Phase2SourceOnboardingRegistryIsRuntimeSafeByDefault()
    {
        var registry = SourceOnboardingRegistry.CreatePhase2SourceOnboardingRegistry();

        foreach (var entry in registry.Entries)
        {
            Assert.False(entry.ParserCapability.SupportsParserExecution);
            Assert.False(entry.ValidationExpectations.ChecksumRequired);
            Assert.False(entry.ValidationExpectations.SchemaValidationRequired);
            Assert.False(entry.RuntimeSafety.AllowsNetworkCalls);
            Assert.False(entry.RuntimeSafety.AllowsFileReads);
            Assert.False(entry.RuntimeSafety.AllowsDatabaseWrites);
            Assert.False(entry.RuntimeSafety.RequiresCredentials);
        }
    }

    [Fact]
    public void ValidRegistryEntryPassesValidation()
    {
        var registry = new SourceOnboardingRegistry([ValidEntry("new_registry_source")]);

        var result = registry.Validate();

        Assert.True(result.IsValid);
        Assert.Empty(result.Errors);
    }

    [Fact]
    public void InvalidEntryValuesFailValidation()
    {
        var registry = new SourceOnboardingRegistry(
            [
                ValidEntry(
                    "invalid_registry_source",
                    " ",
                    discoveryStrategy: (SourceOnboardingDiscoveryStrategy)999,
                    updateCadence: (SourceOnboardingUpdateCadence)999),
            ]);

        var result = registry.Validate();

        Assert.False(result.IsValid);
        Assert.Contains("SourceFamily is required.", result.Errors);
        Assert.Contains("DiscoveryStrategy must be a defined source onboarding discovery strategy.", result.Errors);
        Assert.Contains("UpdateCadence must be a defined source onboarding update cadence.", result.Errors);
    }

    [Fact]
    public void DuplicateIdentifiersFailValidation()
    {
        var sourceIdRegistry = new SourceOnboardingRegistry(
            [
                ValidEntry("duplicate_registry_source", "duplicate_registry_source"),
                ValidEntry("duplicate_registry_source", "duplicate_registry_source_two"),
            ]);
        var sourceFamilyRegistry = new SourceOnboardingRegistry(
            [
                ValidEntry("duplicate_registry_family_one", "duplicate_registry_family"),
                ValidEntry("duplicate_registry_family_two", "duplicate_registry_family"),
            ]);
        var documentRegistry = new SourceOnboardingRegistry(
            [
                ValidEntry(
                    "duplicate_registry_document",
                    "duplicate_registry_document",
                    documents:
                    [
                        ValidDocument("duplicate_document"),
                        ValidDocument("duplicate_document"),
                    ]),
            ]);

        Assert.Contains("Duplicate SourceId found: duplicate_registry_source", sourceIdRegistry.Validate().Errors);
        Assert.Contains("Duplicate SourceFamily found: duplicate_registry_family", sourceFamilyRegistry.Validate().Errors);
        Assert.Contains("Duplicate DocumentId found: duplicate_document", documentRegistry.Validate().Errors);
    }

    [Fact]
    public void MissingRequiredFieldsFailValidation()
    {
        var registry = new SourceOnboardingRegistry(
            [
                new SourceOnboardingRegistryEntry(
                    "",
                    "",
                    " ",
                    [],
                    SourceOnboardingDiscoveryStrategy.SourceSpecificDiscovery,
                    new SourceOnboardingParserCapability(
                        new ParserKey(" "),
                        (ParserSourceFormat)999,
                        supportsParserExecution: false,
                        ""),
                    new SourceOnboardingValidationExpectations(
                        [],
                        checksumRequired: true,
                        schemaValidationRequired: true,
                        ""),
                    SourceOnboardingUpdateCadence.Periodic,
                    new SourceOnboardingRuntimeSafety(
                        allowsNetworkCalls: false,
                        allowsFileReads: false,
                        allowsDatabaseWrites: false,
                        requiresCredentials: false,
                        "")),
            ]);

        var result = registry.Validate();

        Assert.False(result.IsValid);
        Assert.Contains("SourceId is required.", result.Errors);
        Assert.Contains("DisplayName is required.", result.Errors);
        Assert.Contains("Documents must include at least one document for SourceId ''.", result.Errors);
        Assert.Contains("ParserCapability.ParserKey is required.", result.Errors);
        Assert.Contains("ParserCapability.ParserSourceFormat must be a defined parser source format.", result.Errors);
        Assert.Contains("ParserCapability.CapabilityNotes is required.", result.Errors);
        Assert.Contains("RequiredDocumentFields must not be empty for SourceId ''.", result.Errors);
        Assert.Contains("ValidationNotes is required.", result.Errors);
        Assert.Contains("SafetyNotes is required.", result.Errors);
    }

    [Fact]
    public void DeterministicOrderingIsEnforced()
    {
        var registry = SourceOnboardingRegistry.CreatePhase2SourceOnboardingRegistry();
        var reordered = new SourceOnboardingRegistry(
            [
                registry.Entries[1],
                registry.Entries[0],
                registry.Entries[2],
            ]);
        var unorderedDocuments = new SourceOnboardingRegistry(
            [
                ValidEntry(
                    "unordered_documents",
                    "unordered_documents",
                    documents:
                    [
                        ValidDocument("z_document"),
                        ValidDocument("a_document"),
                    ]),
            ]);

        Assert.Equal(SourceOnboardingRegistry.Phase2OnboardingSourceFamilies, registry.Entries.Select(entry => entry.SourceFamily));
        Assert.Equal(registry.Entries, SourceOnboardingRegistry.ListEntries(registry));
        Assert.Contains(
            "Entries must follow Phase 1 source order, then SourceId order.",
            reordered.Validate().Errors);
        Assert.Contains(
            "Documents must be ordered by DocumentId for SourceId 'unordered_documents'.",
            unorderedDocuments.Validate().Errors);
    }

    [Fact]
    public void LookupIsDeterministicAndReturnsDeclaredEntries()
    {
        var registry = SourceOnboardingRegistry.CreatePhase2SourceOnboardingRegistry();

        foreach (var sourceFamily in SourceFamilyRegistry.SupportedFamilies)
        {
            Assert.True(SourceOnboardingRegistry.TryGetBySourceFamily(sourceFamily, out var entry, registry));
            Assert.NotNull(entry);
            Assert.Equal(sourceFamily.ToWireName(), entry!.SourceFamily);
            Assert.Equal(sourceFamily.ToWireName(), entry.SourceId);
        }

        Assert.False(SourceOnboardingRegistry.TryGetBySourceFamily("unknown_source", out var missing, registry));
        Assert.Null(missing);
    }

    [Fact]
    public void RegistrySnapshotsInputCollections()
    {
        var entries = new List<SourceOnboardingRegistryEntry>
        {
            ValidEntry("snapshot_source"),
        };
        var registry = new SourceOnboardingRegistry(entries);

        entries.Clear();

        Assert.Single(registry.Entries);
        Assert.Equal("snapshot_source", registry.Entries[0].SourceId);
    }

    [Fact]
    public void ContractDoesNotIntroduceRuntimeDiscoveryParserDatabaseOrDownloadSurface()
    {
        var publicMembers = typeof(SourceOnboardingRegistry)
            .GetMembers(BindingFlags.Public | BindingFlags.Static | BindingFlags.Instance | BindingFlags.DeclaredOnly)
            .Concat(typeof(SourceOnboardingRegistryEntry)
                .GetMembers(BindingFlags.Public | BindingFlags.Static | BindingFlags.Instance | BindingFlags.DeclaredOnly))
            .Select(member => member.Name)
            .ToArray();
        var blockedTerms = new[]
        {
            "Db",
            "Sql",
            "Postgres",
            "Open",
            "Write",
            "Download",
            "Fetch",
            "Persist",
        };

        foreach (var term in blockedTerms)
        {
            Assert.DoesNotContain(publicMembers, member => member.Contains(term, StringComparison.OrdinalIgnoreCase));
        }

        Assert.DoesNotContain("Parse", publicMembers);
        Assert.DoesNotContain("Execute", publicMembers);
    }

    private static SourceOnboardingRegistryEntry ValidEntry(
        string sourceId,
        string? sourceFamily = null,
        SourceOnboardingDiscoveryStrategy discoveryStrategy = SourceOnboardingDiscoveryStrategy.SourceSpecificDiscovery,
        SourceOnboardingUpdateCadence updateCadence = SourceOnboardingUpdateCadence.Periodic,
        IReadOnlyList<SourceOnboardingDocument>? documents = null) =>
        new(
            sourceId,
            sourceFamily ?? sourceId,
            "New Registry Source",
            documents ?? [ValidDocument($"{sourceId}_document")],
            discoveryStrategy,
            new SourceOnboardingParserCapability(
                new ParserKey($"{sourceId}_parser"),
                ParserSourceFormat.DiscoveryReference,
                supportsParserExecution: false,
                "metadata only"),
            new SourceOnboardingValidationExpectations(
                ["document_id", "source_reference"],
                checksumRequired: true,
                schemaValidationRequired: true,
                "shape validation only"),
            updateCadence,
            new SourceOnboardingRuntimeSafety(
                allowsNetworkCalls: false,
                allowsFileReads: false,
                allowsDatabaseWrites: false,
                requiresCredentials: false,
                "contract metadata only"));

    private static SourceOnboardingDocument ValidDocument(string documentId) =>
        new(
            documentId,
            "Declared document",
            $"discovery://{documentId}",
            "discovery");

    private static ParserKey ExpectedParserKey(string sourceFamily) =>
        sourceFamily switch
        {
            "ghg_protocol" => ParserSelectionRegistry.GetParserKey(SourceFamily.GhgProtocol),
            "defra_desnz" => ParserSelectionRegistry.GetParserKey(SourceFamily.DefraDesnz),
            "ipcc_efdb" => ParserSelectionRegistry.GetParserKey(SourceFamily.IpccEfdb),
            _ => throw new ArgumentOutOfRangeException(nameof(sourceFamily), sourceFamily, "Unknown source family."),
        };
}
