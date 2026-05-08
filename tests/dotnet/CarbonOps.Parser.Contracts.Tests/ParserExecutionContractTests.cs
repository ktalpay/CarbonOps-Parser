using CarbonOps.Parser.Contracts;

namespace CarbonOps.Parser.Contracts.Tests;

public sealed class ParserExecutionContractTests
{
    [Fact]
    public void ParserExecutionBoundaryDescriptorCarriesMetadataOnlyShape()
    {
        var descriptor = new ParserExecutionBoundaryDescriptor(
            SourceFamily.DefraDesnz,
            new ParserKey("defra_desnz_phase1_parser"),
            ParserSourceFormat.DiscoveryReference,
            "application/x-carbonops-discovery-reference",
            "discovery");

        Assert.Equal(SourceFamily.DefraDesnz, descriptor.SourceFamily);
        Assert.Equal("defra_desnz_phase1_parser", descriptor.ParserKey.Value);
        Assert.Equal(ParserSourceFormat.DiscoveryReference, descriptor.SourceFormat);
        Assert.Equal("application/x-carbonops-discovery-reference", descriptor.ContentType);
        Assert.Equal("discovery", descriptor.FormatHint);
    }

    [Fact]
    public void ParserExecutionRequestCarriesSelectionInputAndParserRunMetadata()
    {
        var inputDocument = new ParserInputDocument(
            SourceFamily.DefraDesnz,
            "defra_desnz_discovery_reference",
            ParserSourceFormat.DiscoveryReference,
            "application/x-carbonops-discovery-reference",
            "discovery",
            "dry_run_sha256",
            "defra_desnz_dry_run_checksum",
            IsDryRunChecksum: true);
        var parserKey = new ParserKey("defra_desnz_phase1_parser");
        var parserRunRequest = new ParserRunRequest(
            SourceFamily.DefraDesnz,
            "defra_desnz_discovery_reference",
            "dry_run_sha256",
            "defra_desnz_dry_run_checksum",
            IsDryRunChecksum: true);
        var descriptor = new ParserExecutionBoundaryDescriptor(
            SourceFamily.DefraDesnz,
            parserKey,
            ParserSourceFormat.DiscoveryReference,
            "application/x-carbonops-discovery-reference",
            "discovery");

        var request = new ParserExecutionRequest(
            SourceFamily.DefraDesnz,
            parserKey,
            inputDocument,
            parserRunRequest,
            descriptor);

        Assert.Equal(SourceFamily.DefraDesnz, request.SourceFamily);
        Assert.Equal(parserKey, request.ParserKey);
        Assert.Equal(inputDocument, request.InputDocument);
        Assert.Equal(parserRunRequest, request.ParserRunRequest);
        Assert.Equal(descriptor, request.BoundaryDescriptor);
    }

    [Fact]
    public void ParserExecutionBatchSnapshotsRequests()
    {
        var requests = new List<ParserExecutionRequest>
        {
            CreateRequest(SourceFamily.IpccEfdb, "ipcc_efdb"),
        };

        var batch = new ParserExecutionBatch(requests);

        requests.Clear();

        Assert.Equal(1, batch.RequestCount);
        Assert.Single(batch.Requests);
        Assert.Equal(SourceFamily.IpccEfdb, batch.Requests[0].SourceFamily);
    }

    private static ParserExecutionRequest CreateRequest(SourceFamily sourceFamily, string sourceFamilyWireName)
    {
        var inputDocument = new ParserInputDocument(
            sourceFamily,
            $"{sourceFamilyWireName}_discovery_reference",
            ParserSourceFormat.DiscoveryReference,
            "application/x-carbonops-discovery-reference",
            "discovery",
            "dry_run_sha256",
            $"{sourceFamilyWireName}_dry_run_checksum",
            IsDryRunChecksum: true);
        var parserKey = new ParserKey($"{sourceFamilyWireName}_phase1_parser");

        return new ParserExecutionRequest(
            sourceFamily,
            parserKey,
            inputDocument,
            new ParserRunRequest(
                sourceFamily,
                inputDocument.SourceDocumentReference,
                inputDocument.SourceChecksumAlgorithm,
                inputDocument.SourceChecksumValue,
                inputDocument.IsDryRunChecksum),
            new ParserExecutionBoundaryDescriptor(
                sourceFamily,
                parserKey,
                inputDocument.SourceFormat,
                inputDocument.ContentType,
                inputDocument.FormatHint));
    }
}
