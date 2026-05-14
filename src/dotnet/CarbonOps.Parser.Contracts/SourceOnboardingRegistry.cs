namespace CarbonOps.Parser.Contracts;

public enum SourceOnboardingDiscoveryStrategy
{
    DeclaredReference = 0,
    SourceSpecificDiscovery = 1,
}

public enum SourceOnboardingUpdateCadence
{
    Unknown = 0,
    Annual = 1,
    Periodic = 2,
}

public sealed record SourceOnboardingDocument
{
    public string DocumentId { get; }

    public string DisplayName { get; }

    public string SourceReference { get; }

    public string ExpectedFormat { get; }

    public bool Required { get; }

    public SourceOnboardingDocument(
        string documentId,
        string displayName,
        string sourceReference,
        string expectedFormat,
        bool required = true)
    {
        DocumentId = documentId;
        DisplayName = displayName;
        SourceReference = sourceReference;
        ExpectedFormat = expectedFormat;
        Required = required;
    }
}

public sealed record SourceOnboardingParserCapability
{
    public ParserKey ParserKey { get; }

    public ParserSourceFormat ParserSourceFormat { get; }

    public bool SupportsParserExecution { get; }

    public string CapabilityNotes { get; }

    public SourceOnboardingParserCapability(
        ParserKey parserKey,
        ParserSourceFormat parserSourceFormat,
        bool supportsParserExecution,
        string capabilityNotes)
    {
        ParserKey = parserKey;
        ParserSourceFormat = parserSourceFormat;
        SupportsParserExecution = supportsParserExecution;
        CapabilityNotes = capabilityNotes;
    }
}

public sealed record SourceOnboardingValidationExpectations
{
    public IReadOnlyList<string> RequiredDocumentFields { get; }

    public bool ChecksumRequired { get; }

    public bool SchemaValidationRequired { get; }

    public string ValidationNotes { get; }

    public SourceOnboardingValidationExpectations(
        IEnumerable<string> requiredDocumentFields,
        bool checksumRequired,
        bool schemaValidationRequired,
        string validationNotes)
    {
        RequiredDocumentFields = Array.AsReadOnly(requiredDocumentFields.ToArray());
        ChecksumRequired = checksumRequired;
        SchemaValidationRequired = schemaValidationRequired;
        ValidationNotes = validationNotes;
    }
}

public sealed record SourceOnboardingRuntimeSafety
{
    public bool AllowsNetworkCalls { get; }

    public bool AllowsFileReads { get; }

    public bool AllowsDatabaseWrites { get; }

    public bool RequiresCredentials { get; }

    public string SafetyNotes { get; }

    public SourceOnboardingRuntimeSafety(
        bool allowsNetworkCalls,
        bool allowsFileReads,
        bool allowsDatabaseWrites,
        bool requiresCredentials,
        string safetyNotes)
    {
        AllowsNetworkCalls = allowsNetworkCalls;
        AllowsFileReads = allowsFileReads;
        AllowsDatabaseWrites = allowsDatabaseWrites;
        RequiresCredentials = requiresCredentials;
        SafetyNotes = safetyNotes;
    }
}

public sealed record SourceOnboardingRegistryEntry
{
    public string SourceId { get; }

    public string SourceFamily { get; }

    public string DisplayName { get; }

    public IReadOnlyList<SourceOnboardingDocument> Documents { get; }

    public SourceOnboardingDiscoveryStrategy DiscoveryStrategy { get; }

    public SourceOnboardingParserCapability ParserCapability { get; }

    public SourceOnboardingValidationExpectations ValidationExpectations { get; }

    public SourceOnboardingUpdateCadence UpdateCadence { get; }

    public SourceOnboardingRuntimeSafety RuntimeSafety { get; }

    public bool Enabled { get; }

    public SourceOnboardingRegistryEntry(
        string sourceId,
        string sourceFamily,
        string displayName,
        IEnumerable<SourceOnboardingDocument> documents,
        SourceOnboardingDiscoveryStrategy discoveryStrategy,
        SourceOnboardingParserCapability parserCapability,
        SourceOnboardingValidationExpectations validationExpectations,
        SourceOnboardingUpdateCadence updateCadence,
        SourceOnboardingRuntimeSafety runtimeSafety,
        bool enabled = true)
    {
        SourceId = sourceId;
        SourceFamily = sourceFamily;
        DisplayName = displayName;
        Documents = Array.AsReadOnly(documents.ToArray());
        DiscoveryStrategy = discoveryStrategy;
        ParserCapability = parserCapability;
        ValidationExpectations = validationExpectations;
        UpdateCadence = updateCadence;
        RuntimeSafety = runtimeSafety;
        Enabled = enabled;
    }
}

public sealed record SourceOnboardingRegistry
{
    public static IReadOnlyList<string> Phase2OnboardingSourceFamilies { get; } =
        Array.AsReadOnly(["ghg_protocol", "defra_desnz", "ipcc_efdb"]);

    public IReadOnlyList<SourceOnboardingRegistryEntry> Entries { get; }

    public int EntryCount => Entries.Count;

    public SourceOnboardingRegistry(IEnumerable<SourceOnboardingRegistryEntry> entries)
    {
        Entries = Array.AsReadOnly(entries.ToArray());
    }

    public static SourceOnboardingRegistry CreatePhase2SourceOnboardingRegistry()
    {
        var entries = SourceFamilyRegistry.SupportedFamilies.Select(sourceFamily =>
        {
            var sourceId = sourceFamily.ToWireName();
            var displayName = GetDisplayName(sourceFamily);

            return new SourceOnboardingRegistryEntry(
                sourceId,
                sourceId,
                displayName,
                [
                    new SourceOnboardingDocument(
                        $"{sourceId}_declared_reference",
                        $"{displayName} declared reference",
                        $"discovery://{sourceId}/onboarding",
                        "discovery"),
                ],
                SourceOnboardingDiscoveryStrategy.DeclaredReference,
                new SourceOnboardingParserCapability(
                    ParserSelectionRegistry.GetParserKey(sourceFamily),
                    ParserSourceFormat.DiscoveryReference,
                    supportsParserExecution: false,
                    "Registry metadata only; parser execution is outside this onboarding contract."),
                new SourceOnboardingValidationExpectations(
                    ["document_id", "display_name", "source_reference", "expected_format"],
                    checksumRequired: false,
                    schemaValidationRequired: false,
                    "Declared discovery references are validated for contract shape only."),
                SourceOnboardingUpdateCadence.Unknown,
                new SourceOnboardingRuntimeSafety(
                    allowsNetworkCalls: false,
                    allowsFileReads: false,
                    allowsDatabaseWrites: false,
                    requiresCredentials: false,
                    "Default onboarding registry is runtime-passive and local-only."));
        });

        var registry = new SourceOnboardingRegistry(entries);
        var validation = registry.Validate();

        if (!validation.IsValid)
        {
            throw new InvalidOperationException(
                $"Default source onboarding registry is invalid: {string.Join("; ", validation.Errors)}");
        }

        return registry;
    }

    public static IReadOnlyList<SourceOnboardingRegistryEntry> ListEntries(SourceOnboardingRegistry? registry = null) =>
        (registry ?? CreatePhase2SourceOnboardingRegistry()).Entries;

    public static bool TryGetBySourceFamily(
        string sourceFamily,
        out SourceOnboardingRegistryEntry? entry,
        SourceOnboardingRegistry? registry = null)
    {
        entry = ListEntries(registry).SingleOrDefault(candidate => candidate.SourceFamily == sourceFamily);

        return entry is not null;
    }

    public static bool TryGetBySourceFamily(
        SourceFamily sourceFamily,
        out SourceOnboardingRegistryEntry? entry,
        SourceOnboardingRegistry? registry = null) =>
        TryGetBySourceFamily(sourceFamily.ToWireName(), out entry, registry);

    public ContractValidationResult Validate()
    {
        var errors = new List<string>();
        var sourceIds = new HashSet<string>(StringComparer.Ordinal);
        var sourceFamilies = new HashSet<string>(StringComparer.Ordinal);
        var documentIds = new HashSet<string>(StringComparer.Ordinal);

        for (var index = 0; index < Entries.Count; index++)
        {
            var entry = Entries[index];

            if (entry is null)
            {
                errors.Add($"Entries[{index}] is required.");
                continue;
            }

            ValidateEntry(entry, errors, sourceIds, sourceFamilies, documentIds);
        }

        ValidateOrdering(errors);

        return ContractValidationResult.FromErrors(errors);
    }

    private static string GetDisplayName(SourceFamily sourceFamily) =>
        sourceFamily switch
        {
            SourceFamily.GhgProtocol => "GHG Protocol",
            SourceFamily.DefraDesnz => "DEFRA/DESNZ",
            SourceFamily.IpccEfdb => "IPCC EFDB",
            _ => throw new ArgumentOutOfRangeException(nameof(sourceFamily), sourceFamily, "Unknown source family."),
        };

    private static void ValidateEntry(
        SourceOnboardingRegistryEntry entry,
        ICollection<string> errors,
        ISet<string> sourceIds,
        ISet<string> sourceFamilies,
        ISet<string> documentIds)
    {
        AddRequiredError(errors, entry.SourceId, "SourceId");

        AddRequiredError(errors, entry.SourceFamily, "SourceFamily");

        AddRequiredError(errors, entry.DisplayName, "DisplayName");

        if (!string.IsNullOrWhiteSpace(entry.SourceId) && !sourceIds.Add(entry.SourceId))
        {
            errors.Add($"Duplicate SourceId found: {entry.SourceId}");
        }

        if (!string.IsNullOrWhiteSpace(entry.SourceFamily) && !sourceFamilies.Add(entry.SourceFamily))
        {
            errors.Add($"Duplicate SourceFamily found: {entry.SourceFamily}");
        }

        if (entry.Documents.Count == 0)
        {
            errors.Add($"Documents must include at least one document for SourceId '{entry.SourceId}'.");
        }

        ValidateDocumentOrdering(entry, errors);

        foreach (var document in entry.Documents)
        {
            ValidateDocument(entry, document, errors, documentIds);
        }

        if (!Enum.IsDefined(entry.DiscoveryStrategy))
        {
            errors.Add("DiscoveryStrategy must be a defined source onboarding discovery strategy.");
        }

        if (!Enum.IsDefined(entry.UpdateCadence))
        {
            errors.Add("UpdateCadence must be a defined source onboarding update cadence.");
        }

        ValidateParserCapability(entry, errors);
        ValidateValidationExpectations(entry, errors);
        ValidateRuntimeSafety(entry, errors);
    }

    private static void ValidateDocument(
        SourceOnboardingRegistryEntry entry,
        SourceOnboardingDocument document,
        ICollection<string> errors,
        ISet<string> documentIds)
    {
        if (document is null)
        {
            errors.Add($"Documents for SourceId '{entry.SourceId}' must not contain null entries.");
            return;
        }

        AddRequiredError(errors, document.DocumentId, "DocumentId");
        AddRequiredError(errors, document.DisplayName, "Document.DisplayName");
        AddRequiredError(errors, document.SourceReference, "SourceReference");
        AddRequiredError(errors, document.ExpectedFormat, "ExpectedFormat");

        if (!string.IsNullOrWhiteSpace(document.DocumentId) && !documentIds.Add(document.DocumentId))
        {
            errors.Add($"Duplicate DocumentId found: {document.DocumentId}");
        }
    }

    private static void ValidateParserCapability(
        SourceOnboardingRegistryEntry entry,
        ICollection<string> errors)
    {
        if (entry.ParserCapability is null)
        {
            errors.Add($"ParserCapability is required for SourceId '{entry.SourceId}'.");
            return;
        }

        if (entry.ParserCapability.ParserKey is null || string.IsNullOrWhiteSpace(entry.ParserCapability.ParserKey.Value))
        {
            errors.Add("ParserCapability.ParserKey is required.");
        }

        if (!Enum.IsDefined(entry.ParserCapability.ParserSourceFormat))
        {
            errors.Add("ParserCapability.ParserSourceFormat must be a defined parser source format.");
        }

        AddRequiredError(errors, entry.ParserCapability.CapabilityNotes, "ParserCapability.CapabilityNotes");
    }

    private static void ValidateValidationExpectations(
        SourceOnboardingRegistryEntry entry,
        ICollection<string> errors)
    {
        if (entry.ValidationExpectations is null)
        {
            errors.Add($"ValidationExpectations is required for SourceId '{entry.SourceId}'.");
            return;
        }

        if (entry.ValidationExpectations.RequiredDocumentFields.Count == 0)
        {
            errors.Add($"RequiredDocumentFields must not be empty for SourceId '{entry.SourceId}'.");
        }

        foreach (var fieldName in entry.ValidationExpectations.RequiredDocumentFields)
        {
            AddRequiredError(errors, fieldName, "RequiredDocumentFields");
        }

        AddRequiredError(errors, entry.ValidationExpectations.ValidationNotes, "ValidationNotes");
    }

    private static void ValidateRuntimeSafety(
        SourceOnboardingRegistryEntry entry,
        ICollection<string> errors)
    {
        if (entry.RuntimeSafety is null)
        {
            errors.Add($"RuntimeSafety is required for SourceId '{entry.SourceId}'.");
            return;
        }

        AddRequiredError(errors, entry.RuntimeSafety.SafetyNotes, "SafetyNotes");
    }

    private static void ValidateDocumentOrdering(
        SourceOnboardingRegistryEntry entry,
        ICollection<string> errors)
    {
        var documentIds = entry.Documents
            .Where(document => document is not null)
            .Select(document => document.DocumentId)
            .ToArray();

        if (!documentIds.SequenceEqual(documentIds.OrderBy(documentId => documentId, StringComparer.Ordinal)))
        {
            errors.Add($"Documents must be ordered by DocumentId for SourceId '{entry.SourceId}'.");
        }
    }

    private void ValidateOrdering(ICollection<string> errors)
    {
        var expectedOrder = Entries
            .Where(entry => entry is not null)
            .OrderBy(entry => SourceOrderIndex(entry.SourceFamily))
            .ThenBy(entry => entry.SourceId, StringComparer.Ordinal)
            .ToArray();

        if (!Entries.Where(entry => entry is not null).SequenceEqual(expectedOrder))
        {
            errors.Add("Entries must follow Phase 1 source order, then SourceId order.");
        }
    }

    private static int SourceOrderIndex(string sourceFamily)
    {
        var index = Phase2OnboardingSourceFamilies
            .Select((candidate, position) => new { candidate, position })
            .SingleOrDefault(item => item.candidate == sourceFamily)
            ?.position ?? -1;

        return index >= 0 ? index : Phase2OnboardingSourceFamilies.Count;
    }

    private static void AddRequiredError(ICollection<string> errors, string? value, string fieldName)
    {
        if (string.IsNullOrWhiteSpace(value))
        {
            errors.Add($"{fieldName} is required.");
        }
    }
}
