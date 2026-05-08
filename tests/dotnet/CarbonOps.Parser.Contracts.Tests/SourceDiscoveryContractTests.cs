using CarbonOps.Parser.Contracts;

namespace CarbonOps.Parser.Contracts.Tests;

public sealed class SourceDiscoveryContractTests
{
    [Fact]
    public void SourceDiscoveryDocumentCarriesDiscoveryMetadata()
    {
        var document = new SourceDiscoveryDocument(
            SourceFamily.DefraDesnz,
            "DEFRA/DESNZ",
            "defra_desnz_discovery_reference",
            ReportingYear: null);

        Assert.Equal(SourceFamily.DefraDesnz, document.SourceFamily);
        Assert.Equal("DEFRA/DESNZ", document.SourceName);
        Assert.Equal("defra_desnz_discovery_reference", document.SourceReference);
        Assert.Null(document.ReportingYear);
        Assert.Equal(SourceDiscoveryStatus.Declared, document.Status);
    }

    [Fact]
    public void SourceDiscoveryDocumentSupportsImmutableRecordCopy()
    {
        var declared = new SourceDiscoveryDocument(
            SourceFamily.GhgProtocol,
            "GHG Protocol",
            "ghg_protocol_discovery_reference",
            ReportingYear: null);

        var annual = declared with { ReportingYear = 2024 };

        Assert.Null(declared.ReportingYear);
        Assert.Equal(2024, annual.ReportingYear);
        Assert.Equal(declared.SourceFamily, annual.SourceFamily);
        Assert.Equal(declared.SourceReference, annual.SourceReference);
    }

    [Fact]
    public void SourceDiscoveryResultPreservesDeterministicDocumentOrder()
    {
        var documents = BuildPhaseOneDocuments();
        var result = new SourceDiscoveryResult(SourceDiscoveryStatus.Declared, documents);

        Assert.Equal(SourceDiscoveryStatus.Declared, result.Status);
        Assert.Equal(
            [
                SourceFamily.GhgProtocol,
                SourceFamily.DefraDesnz,
                SourceFamily.IpccEfdb,
            ],
            result.Documents.Select(document => document.SourceFamily));
        Assert.Empty(result.Warnings);
    }

    [Fact]
    public void SourceDiscoveryResultSnapshotsInputCollections()
    {
        var documents = BuildPhaseOneDocuments().ToList();
        var warnings = new List<string> { "first warning" };
        var result = new SourceDiscoveryResult(SourceDiscoveryStatus.Declared, documents, warnings);

        documents.Clear();
        warnings.Add("second warning");

        Assert.Equal(3, result.Documents.Count);
        Assert.Equal(["first warning"], result.Warnings);
    }

    [Fact]
    public void SourceDiscoveryDocumentsUseSupportedSourceFamilies()
    {
        var result = new SourceDiscoveryResult(
            SourceDiscoveryStatus.Declared,
            BuildPhaseOneDocuments());

        Assert.Equal(SourceFamilyRegistry.SupportedFamilies, result.Documents.Select(document => document.SourceFamily));
    }

    [Fact]
    public void SourceDiscoveryStatusUsesPythonAlignedWireName()
    {
        Assert.Equal("declared", SourceDiscoveryStatus.Declared.ToWireName());
        Assert.True(ContractWireNames.TryParseSourceDiscoveryStatusWireName("declared", out var parsed));
        Assert.Equal(SourceDiscoveryStatus.Declared, parsed);
        Assert.False(ContractWireNames.TryParseSourceDiscoveryStatusWireName("unknown", out _));
        Assert.Throws<ArgumentOutOfRangeException>(() => ((SourceDiscoveryStatus)999).ToWireName());
    }

    [Fact]
    public void SourceDiscoveryReferencesUseSafePlaceholders()
    {
        var result = new SourceDiscoveryResult(
            SourceDiscoveryStatus.Declared,
            BuildPhaseOneDocuments());

        foreach (var document in result.Documents)
        {
            Assert.DoesNotContain("://", document.SourceReference);
            Assert.DoesNotContain("http", document.SourceReference, StringComparison.OrdinalIgnoreCase);
            Assert.EndsWith("_discovery_reference", document.SourceReference);
        }
    }

    [Fact]
    public void SourceDiscoveryDocumentsDoNotIncludePlaceholderSourceFamilies()
    {
        var blockedTerms = new[] { "placeholder", "manual", "test", "fake" };
        var result = new SourceDiscoveryResult(
            SourceDiscoveryStatus.Declared,
            BuildPhaseOneDocuments());

        var familyNames = result.Documents
            .SelectMany(document => new[] { document.SourceFamily.ToString(), document.SourceFamily.ToWireName() });

        foreach (var name in familyNames)
        {
            Assert.DoesNotContain(blockedTerms, term => name.Contains(term, StringComparison.OrdinalIgnoreCase));
        }
    }

    private static SourceDiscoveryDocument[] BuildPhaseOneDocuments() =>
        [
            new SourceDiscoveryDocument(
                SourceFamily.GhgProtocol,
                "GHG Protocol",
                "ghg_protocol_discovery_reference",
                ReportingYear: null),
            new SourceDiscoveryDocument(
                SourceFamily.DefraDesnz,
                "DEFRA/DESNZ",
                "defra_desnz_discovery_reference",
                ReportingYear: null),
            new SourceDiscoveryDocument(
                SourceFamily.IpccEfdb,
                "IPCC EFDB",
                "ipcc_efdb_discovery_reference",
                ReportingYear: null),
        ];
}
