using System.Reflection;
using CarbonOps.Parser.Contracts;

namespace CarbonOps.Parser.Contracts.Tests;

public sealed class IpccEfdbParserAdapterDescriptorTests
{
    [Fact]
    public void IpccEfdbDescriptorSupportsOnlyIpccEfdb()
    {
        var descriptor = IpccEfdbParserAdapterDescriptor.CreateDefault();

        Assert.Equal(SourceFamily.IpccEfdb, descriptor.SourceFamily);
        Assert.Equal([SourceFamily.IpccEfdb], descriptor.Capability.SupportedSourceFamilies);
        Assert.DoesNotContain(SourceFamily.GhgProtocol, descriptor.Capability.SupportedSourceFamilies);
        Assert.DoesNotContain(SourceFamily.DefraDesnz, descriptor.Capability.SupportedSourceFamilies);
    }

    [Fact]
    public void IpccEfdbDescriptorUsesExistingParserSelectionKey()
    {
        var descriptor = IpccEfdbParserAdapterDescriptor.CreateDefault();

        Assert.Equal(ParserSelectionRegistry.GetParserKey(SourceFamily.IpccEfdb), descriptor.ParserKey);
        Assert.Equal("ipcc_efdb_phase1_parser", descriptor.ParserKey.Value);
    }

    [Fact]
    public void IpccEfdbDescriptorCapabilityAndReadinessMetadataAreDeterministic()
    {
        var first = IpccEfdbParserAdapterDescriptor.CreateDefault();
        var second = IpccEfdbParserAdapterDescriptor.CreateDefault();

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
        Assert.Equal("ipcc_efdb_parser_adapter", first.AdapterName);
        Assert.Equal(ParserAdapterReadiness.ExecutionNotImplemented, first.Readiness);
        Assert.Equal("execution_not_implemented", first.Readiness.ToWireName());
        Assert.False(first.IsExecutionImplemented);
        Assert.Equal([ParserSourceFormat.DiscoveryReference], first.Capability.SupportedSourceFormats);
        Assert.Equal(["application/x-carbonops-discovery-reference"], first.Capability.SupportedContentTypes);
        Assert.Equal(["discovery"], first.Capability.SupportedFormatHints);
        Assert.Equal(
            ["IPCC EFDB parser adapter skeleton: parser execution is not implemented yet."],
            first.ReadinessNotes);
    }

    [Fact]
    public void IpccEfdbDescriptorDoesNotExposeParserExecutionMethods()
    {
        var declaredInstanceMethods = typeof(IpccEfdbParserAdapterDescriptor)
            .GetMethods(BindingFlags.Instance | BindingFlags.Public | BindingFlags.DeclaredOnly)
            .Select(method => method.Name)
            .ToArray();

        Assert.DoesNotContain("Parse", declaredInstanceMethods);
        Assert.DoesNotContain("Execute", declaredInstanceMethods);
    }

    [Fact]
    public void IpccEfdbDescriptorDoesNotContainUrlLookingReferences()
    {
        var descriptor = IpccEfdbParserAdapterDescriptor.CreateDefault();
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
    public void IpccEfdbDescriptorDoesNotIncludePlaceholderParserKeysOrSourceFamilies()
    {
        var blockedTerms = new[] { "placeholder", "manual", "test", "fake" };
        var descriptor = IpccEfdbParserAdapterDescriptor.CreateDefault();
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
    public void IpccEfdbDescriptorSnapshotsReadinessNotes()
    {
        var readinessNotes = new List<string>
        {
            "IPCC EFDB parser adapter skeleton: parser execution is not implemented yet.",
        };
        var descriptor = new IpccEfdbParserAdapterDescriptor(
            "ipcc_efdb_parser_adapter",
            SourceFamily.IpccEfdb,
            ParserSelectionRegistry.GetParserKey(SourceFamily.IpccEfdb),
            new ParserAdapterCapability(
                [SourceFamily.IpccEfdb],
                [ParserSourceFormat.DiscoveryReference],
                ["application/x-carbonops-discovery-reference"],
                ["discovery"]),
            ParserAdapterReadiness.ExecutionNotImplemented,
            isExecutionImplemented: false,
            readinessNotes);

        readinessNotes.Clear();

        Assert.Equal(
            ["IPCC EFDB parser adapter skeleton: parser execution is not implemented yet."],
            descriptor.ReadinessNotes);
    }
}
