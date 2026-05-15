using System.Reflection;
using System.Text.Json;
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
    public void Phase2SourceOnboardingRegistryMatchesSharedParityExpectations()
    {
        using var expectations = LoadParityExpectations();
        var root = expectations.RootElement;
        var registry = SourceOnboardingRegistry.CreatePhase2SourceOnboardingRegistry();
        var expectedFamilies = JsonStringArray(root.GetProperty("phase2_source_families"));
        var expectedEntries = root.GetProperty("entries").EnumerateArray().ToArray();

        Assert.Equal(expectedFamilies, SourceOnboardingRegistry.Phase2OnboardingSourceFamilies);
        Assert.Equal(expectedEntries.Length, registry.Entries.Count);

        for (var index = 0; index < expectedEntries.Length; index++)
        {
            var expected = expectedEntries[index];
            var actual = registry.Entries[index];

            Assert.Equal(expected.GetProperty("source_id").GetString(), actual.SourceId);
            Assert.Equal(expected.GetProperty("source_family").GetString(), actual.SourceFamily);
            Assert.Equal(expected.GetProperty("display_name").GetString(), actual.DisplayName);
            Assert.Equal(expected.GetProperty("discovery_strategy").GetString(), DiscoveryStrategyWireName(actual.DiscoveryStrategy));
            Assert.Equal(expected.GetProperty("update_cadence").GetString(), UpdateCadenceWireName(actual.UpdateCadence));
            Assert.Equal(expected.GetProperty("enabled").GetBoolean(), actual.Enabled);

            var expectedDocument = expected.GetProperty("documents")[0];
            Assert.Equal(expectedDocument.GetProperty("document_id").GetString(), actual.Documents[0].DocumentId);
            Assert.Equal(expectedDocument.GetProperty("display_name").GetString(), actual.Documents[0].DisplayName);
            Assert.Equal(expectedDocument.GetProperty("source_reference").GetString(), actual.Documents[0].SourceReference);
            Assert.Equal(expectedDocument.GetProperty("expected_format").GetString(), actual.Documents[0].ExpectedFormat);
            Assert.Equal(expectedDocument.GetProperty("required").GetBoolean(), actual.Documents[0].Required);

            var expectedCapability = expected.GetProperty("parser_capability");
            Assert.Equal(expectedCapability.GetProperty("parser_key").GetString(), actual.ParserCapability.ParserKey.Value);
            Assert.Equal(expectedCapability.GetProperty("parser_source_format").GetString(), actual.ParserCapability.ParserSourceFormat.ToWireName());
            Assert.Equal(expectedCapability.GetProperty("supports_parser_execution").GetBoolean(), actual.ParserCapability.SupportsParserExecution);
            Assert.Equal(expectedCapability.GetProperty("capability_notes").GetString(), actual.ParserCapability.CapabilityNotes);

            var expectedValidation = expected.GetProperty("validation_expectations");
            Assert.Equal(JsonStringArray(expectedValidation.GetProperty("required_document_fields")), actual.ValidationExpectations.RequiredDocumentFields);
            Assert.Equal(expectedValidation.GetProperty("checksum_required").GetBoolean(), actual.ValidationExpectations.ChecksumRequired);
            Assert.Equal(expectedValidation.GetProperty("schema_validation_required").GetBoolean(), actual.ValidationExpectations.SchemaValidationRequired);
            Assert.Equal(expectedValidation.GetProperty("validation_notes").GetString(), actual.ValidationExpectations.ValidationNotes);

            var expectedSafety = expected.GetProperty("runtime_safety");
            Assert.Equal(expectedSafety.GetProperty("allows_network_calls").GetBoolean(), actual.RuntimeSafety.AllowsNetworkCalls);
            Assert.Equal(expectedSafety.GetProperty("allows_file_reads").GetBoolean(), actual.RuntimeSafety.AllowsFileReads);
            Assert.Equal(expectedSafety.GetProperty("allows_database_writes").GetBoolean(), actual.RuntimeSafety.AllowsDatabaseWrites);
            Assert.Equal(expectedSafety.GetProperty("requires_credentials").GetBoolean(), actual.RuntimeSafety.RequiresCredentials);
            Assert.Equal(expectedSafety.GetProperty("safety_notes").GetString(), actual.RuntimeSafety.SafetyNotes);
        }

        Assert.Equal(
            [
                "Python validation raises TypeError or ValueError for invalid registries; .NET validation returns ContractValidationResult errors and lookup helpers throw ArgumentException when an invalid custom registry is supplied.",
            ],
            JsonStringArray(root.GetProperty("accepted_asymmetries")));
    }

    [Fact]
    public void Phase2SourceOnboardingParserKeysAlignWithPhaseOneDescriptorRegistry()
    {
        var registry = SourceOnboardingRegistry.CreatePhase2SourceOnboardingRegistry();

        foreach (var entry in registry.Entries)
        {
            Assert.True(ParserAdapterDescriptorRegistry.TryGetBySourceFamily(ParseSourceFamily(entry.SourceFamily), out var descriptor));
            Assert.NotNull(descriptor);
            Assert.Equal(descriptor!.ParserKey, entry.ParserCapability.ParserKey);
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
        var mixedSourceIds = new SourceOnboardingRegistry(
            [
                ValidEntry("z_custom_source_id", "ghg_protocol"),
                ValidEntry("a_custom_source_id", "custom_source_family"),
            ]);
        var mixedSourceIdsReordered = new SourceOnboardingRegistry(mixedSourceIds.Entries.Reverse());

        Assert.Equal(SourceOnboardingRegistry.Phase2OnboardingSourceFamilies, registry.Entries.Select(entry => entry.SourceFamily));
        Assert.Equal(registry.Entries, SourceOnboardingRegistry.ListEntries(registry));
        Assert.True(mixedSourceIds.Validate().IsValid);
        Assert.Contains(
            "Entries must follow Phase 1 source order, then SourceId order.",
            reordered.Validate().Errors);
        Assert.Contains(
            "Entries must follow Phase 1 source order, then SourceId order.",
            mixedSourceIdsReordered.Validate().Errors);
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
    public void LookupRejectsInvalidCustomRegistry()
    {
        var entry = ValidEntry("duplicate_registry_source");
        var registry = new SourceOnboardingRegistry(
            [
                entry,
                ValidEntry("duplicate_registry_source", "duplicate_registry_source_two"),
            ]);

        var exception = Assert.Throws<ArgumentException>(() =>
            SourceOnboardingRegistry.TryGetBySourceFamily("duplicate_registry_source", out _, registry));

        Assert.Contains("Duplicate SourceId found: duplicate_registry_source", exception.Message);
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

    private static JsonDocument LoadParityExpectations() =>
        JsonDocument.Parse(File.ReadAllText(Path.Combine(ParityFixtureDirectory(), "source_onboarding_registry_expectations.json")));

    private static IReadOnlyList<string> JsonStringArray(JsonElement array) =>
        array.EnumerateArray().Select(item => item.GetString() ?? string.Empty).ToArray();

    private static string DiscoveryStrategyWireName(SourceOnboardingDiscoveryStrategy strategy) =>
        strategy switch
        {
            SourceOnboardingDiscoveryStrategy.DeclaredReference => "declared_reference",
            SourceOnboardingDiscoveryStrategy.SourceSpecificDiscovery => "source_specific_discovery",
            _ => throw new ArgumentOutOfRangeException(nameof(strategy), strategy, "Unknown discovery strategy."),
        };

    private static string UpdateCadenceWireName(SourceOnboardingUpdateCadence cadence) =>
        cadence switch
        {
            SourceOnboardingUpdateCadence.Unknown => "unknown",
            SourceOnboardingUpdateCadence.Annual => "annual",
            SourceOnboardingUpdateCadence.Periodic => "periodic",
            _ => throw new ArgumentOutOfRangeException(nameof(cadence), cadence, "Unknown update cadence."),
        };

    private static SourceFamily ParseSourceFamily(string sourceFamily) =>
        sourceFamily switch
        {
            "ghg_protocol" => SourceFamily.GhgProtocol,
            "defra_desnz" => SourceFamily.DefraDesnz,
            "ipcc_efdb" => SourceFamily.IpccEfdb,
            _ => throw new ArgumentOutOfRangeException(nameof(sourceFamily), sourceFamily, "Unknown source family."),
        };

    private static ParserKey ExpectedParserKey(string sourceFamily) =>
        sourceFamily switch
        {
            "ghg_protocol" => ParserSelectionRegistry.GetParserKey(SourceFamily.GhgProtocol),
            "defra_desnz" => ParserSelectionRegistry.GetParserKey(SourceFamily.DefraDesnz),
            "ipcc_efdb" => ParserSelectionRegistry.GetParserKey(SourceFamily.IpccEfdb),
            _ => throw new ArgumentOutOfRangeException(nameof(sourceFamily), sourceFamily, "Unknown source family."),
        };

    private static string ParityFixtureDirectory()
    {
        var directory = new DirectoryInfo(AppContext.BaseDirectory);
        while (directory is not null)
        {
            var fixtureDirectory = Path.Combine(directory.FullName, "tests", "fixtures", "parity");
            if (Directory.Exists(fixtureDirectory))
            {
                return fixtureDirectory;
            }

            directory = directory.Parent;
        }

        throw new DirectoryNotFoundException("Could not locate parity fixture directory.");
    }
}
