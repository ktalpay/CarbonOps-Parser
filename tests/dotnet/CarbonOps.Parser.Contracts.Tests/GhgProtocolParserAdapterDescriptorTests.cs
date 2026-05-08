using System.Reflection;
using CarbonOps.Parser.Contracts;

namespace CarbonOps.Parser.Contracts.Tests;

public sealed class GhgProtocolParserAdapterDescriptorTests
{
    [Fact]
    public void GhgProtocolDescriptorSupportsOnlyGhgProtocol()
    {
        var descriptor = GhgProtocolParserAdapterDescriptor.CreateDefault();

        Assert.Equal(SourceFamily.GhgProtocol, descriptor.SourceFamily);
        Assert.Equal([SourceFamily.GhgProtocol], descriptor.Capability.SupportedSourceFamilies);
        Assert.DoesNotContain(SourceFamily.DefraDesnz, descriptor.Capability.SupportedSourceFamilies);
        Assert.DoesNotContain(SourceFamily.IpccEfdb, descriptor.Capability.SupportedSourceFamilies);
    }

    [Fact]
    public void GhgProtocolDescriptorUsesExistingParserSelectionKey()
    {
        var descriptor = GhgProtocolParserAdapterDescriptor.CreateDefault();

        Assert.Equal(ParserSelectionRegistry.GetParserKey(SourceFamily.GhgProtocol), descriptor.ParserKey);
        Assert.Equal("ghg_protocol_phase1_parser", descriptor.ParserKey.Value);
    }

    [Fact]
    public void GhgProtocolDescriptorCapabilityAndReadinessMetadataAreDeterministic()
    {
        var first = GhgProtocolParserAdapterDescriptor.CreateDefault();
        var second = GhgProtocolParserAdapterDescriptor.CreateDefault();

        Assert.Equal(first.AdapterName, second.AdapterName);
        Assert.Equal(first.SourceFamily, second.SourceFamily);
        Assert.Equal(first.ParserKey, second.ParserKey);
        Assert.Equal(first.Readiness, second.Readiness);
        Assert.Equal(first.IsExecutionImplemented, second.IsExecutionImplemented);
        Assert.Equal(first.Capability.SupportedSourceFamilies, second.Capability.SupportedSourceFamilies);
        Assert.Equal(first.Capability.SupportedSourceFormats, second.Capability.SupportedSourceFormats);
        Assert.Equal(first.Capability.SupportedContentTypes, second.Capability.SupportedContentTypes);
        Assert.Equal(first.Capability.SupportedFormatHints, second.Capability.SupportedFormatHints);
        Assert.Equal(first.ReadinessNotes, second.ReadinessNotes);
        Assert.Equal("ghg_protocol_parser_adapter", first.AdapterName);
        Assert.Equal(ParserAdapterReadiness.ExecutionNotImplemented, first.Readiness);
        Assert.Equal("execution_not_implemented", first.Readiness.ToWireName());
        Assert.False(first.IsExecutionImplemented);
        Assert.Equal([ParserSourceFormat.DiscoveryReference], first.Capability.SupportedSourceFormats);
        Assert.Equal(["application/x-carbonops-discovery-reference"], first.Capability.SupportedContentTypes);
        Assert.Equal(["discovery"], first.Capability.SupportedFormatHints);
        Assert.Equal(
            ["GHG Protocol parser adapter skeleton: parser execution is not implemented yet."],
            first.ReadinessNotes);
    }

    [Fact]
    public void ParserAdapterReadinessWireNamesCanBeParsed()
    {
        Assert.True(
            ContractWireNames.TryParseParserAdapterReadinessWireName(
                "execution_not_implemented",
                out var readiness));
        Assert.False(ContractWireNames.TryParseParserAdapterReadinessWireName("ready", out var invalid));

        Assert.Equal(ParserAdapterReadiness.ExecutionNotImplemented, readiness);
        Assert.Equal(default, invalid);
    }

    [Fact]
    public void GhgProtocolDescriptorDoesNotExposeParserExecutionMethods()
    {
        var declaredInstanceMethods = typeof(GhgProtocolParserAdapterDescriptor)
            .GetMethods(BindingFlags.Instance | BindingFlags.Public | BindingFlags.DeclaredOnly)
            .Select(method => method.Name)
            .ToArray();

        Assert.DoesNotContain("Parse", declaredInstanceMethods);
        Assert.DoesNotContain("Execute", declaredInstanceMethods);
    }

    [Fact]
    public void GhgProtocolDescriptorDoesNotContainUrlLookingReferences()
    {
        var descriptor = GhgProtocolParserAdapterDescriptor.CreateDefault();
        var metadataValues = descriptor.Capability.SupportedContentTypes
            .Concat(descriptor.Capability.SupportedFormatHints)
            .Concat(descriptor.ReadinessNotes)
            .Append(descriptor.AdapterName)
            .Append(descriptor.ParserKey.Value);

        foreach (var value in metadataValues)
        {
            Assert.DoesNotContain("://", value);
            Assert.DoesNotContain("http", value, StringComparison.OrdinalIgnoreCase);
        }
    }

    [Fact]
    public void GhgProtocolDescriptorDoesNotIncludePlaceholderParserKeysOrSourceFamilies()
    {
        var blockedTerms = new[] { "placeholder", "manual", "test", "fake" };
        var descriptor = GhgProtocolParserAdapterDescriptor.CreateDefault();
        var names = descriptor.Capability.SupportedSourceFamilies.SelectMany(sourceFamily => new[]
            {
                sourceFamily.ToString(),
                sourceFamily.ToWireName(),
            })
            .Concat([descriptor.ParserKey.Value]);

        foreach (var name in names)
        {
            Assert.DoesNotContain(blockedTerms, term => name.Contains(term, StringComparison.OrdinalIgnoreCase));
        }
    }

    [Fact]
    public void ParserAdapterCapabilitySnapshotsCollections()
    {
        var sourceFamilies = new List<SourceFamily> { SourceFamily.GhgProtocol };
        var sourceFormats = new List<ParserSourceFormat> { ParserSourceFormat.DiscoveryReference };
        var contentTypes = new List<string> { "application/x-carbonops-discovery-reference" };
        var formatHints = new List<string> { "discovery" };

        var capability = new ParserAdapterCapability(
            sourceFamilies,
            sourceFormats,
            contentTypes,
            formatHints);

        sourceFamilies.Clear();
        sourceFormats.Clear();
        contentTypes.Clear();
        formatHints.Clear();

        Assert.Equal([SourceFamily.GhgProtocol], capability.SupportedSourceFamilies);
        Assert.Equal([ParserSourceFormat.DiscoveryReference], capability.SupportedSourceFormats);
        Assert.Equal(["application/x-carbonops-discovery-reference"], capability.SupportedContentTypes);
        Assert.Equal(["discovery"], capability.SupportedFormatHints);
    }

    [Fact]
    public void GhgProtocolDescriptorSnapshotsReadinessNotes()
    {
        var readinessNotes = new List<string>
        {
            "GHG Protocol parser adapter skeleton: parser execution is not implemented yet.",
        };
        var descriptor = new GhgProtocolParserAdapterDescriptor(
            "ghg_protocol_parser_adapter",
            SourceFamily.GhgProtocol,
            ParserSelectionRegistry.GetParserKey(SourceFamily.GhgProtocol),
            new ParserAdapterCapability(
                [SourceFamily.GhgProtocol],
                [ParserSourceFormat.DiscoveryReference],
                ["application/x-carbonops-discovery-reference"],
                ["discovery"]),
            ParserAdapterReadiness.ExecutionNotImplemented,
            isExecutionImplemented: false,
            readinessNotes);

        readinessNotes.Clear();

        Assert.Equal(
            ["GHG Protocol parser adapter skeleton: parser execution is not implemented yet."],
            descriptor.ReadinessNotes);
    }
}
