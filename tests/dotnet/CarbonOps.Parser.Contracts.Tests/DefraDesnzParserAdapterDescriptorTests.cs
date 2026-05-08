using System.Reflection;
using CarbonOps.Parser.Contracts;

namespace CarbonOps.Parser.Contracts.Tests;

public sealed class DefraDesnzParserAdapterDescriptorTests
{
    [Fact]
    public void DefraDesnzDescriptorSupportsOnlyDefraDesnz()
    {
        var descriptor = DefraDesnzParserAdapterDescriptor.CreateDefault();

        Assert.Equal(SourceFamily.DefraDesnz, descriptor.SourceFamily);
        Assert.Equal([SourceFamily.DefraDesnz], descriptor.Capability.SupportedSourceFamilies);
        Assert.DoesNotContain(SourceFamily.GhgProtocol, descriptor.Capability.SupportedSourceFamilies);
        Assert.DoesNotContain(SourceFamily.IpccEfdb, descriptor.Capability.SupportedSourceFamilies);
    }

    [Fact]
    public void DefraDesnzDescriptorUsesExistingParserSelectionKey()
    {
        var descriptor = DefraDesnzParserAdapterDescriptor.CreateDefault();

        Assert.Equal(ParserSelectionRegistry.GetParserKey(SourceFamily.DefraDesnz), descriptor.ParserKey);
        Assert.Equal("defra_desnz_phase1_parser", descriptor.ParserKey.Value);
    }

    [Fact]
    public void DefraDesnzDescriptorCapabilityAndReadinessMetadataAreDeterministic()
    {
        var first = DefraDesnzParserAdapterDescriptor.CreateDefault();
        var second = DefraDesnzParserAdapterDescriptor.CreateDefault();

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
        Assert.Equal("defra_desnz_parser_adapter", first.AdapterName);
        Assert.Equal(ParserAdapterReadiness.ExecutionNotImplemented, first.Readiness);
        Assert.Equal("execution_not_implemented", first.Readiness.ToWireName());
        Assert.False(first.IsExecutionImplemented);
        Assert.Equal([ParserSourceFormat.DiscoveryReference], first.Capability.SupportedSourceFormats);
        Assert.Equal(["application/x-carbonops-discovery-reference"], first.Capability.SupportedContentTypes);
        Assert.Equal(["discovery"], first.Capability.SupportedFormatHints);
        Assert.Equal(
            ["DEFRA/DESNZ parser adapter skeleton: parser execution is not implemented yet."],
            first.ReadinessNotes);
    }

    [Fact]
    public void DefraDesnzDescriptorDoesNotExposeParserExecutionMethods()
    {
        var declaredInstanceMethods = typeof(DefraDesnzParserAdapterDescriptor)
            .GetMethods(BindingFlags.Instance | BindingFlags.Public | BindingFlags.DeclaredOnly)
            .Select(method => method.Name)
            .ToArray();

        Assert.DoesNotContain("Parse", declaredInstanceMethods);
        Assert.DoesNotContain("Execute", declaredInstanceMethods);
    }

    [Fact]
    public void DefraDesnzDescriptorDoesNotContainUrlLookingReferences()
    {
        var descriptor = DefraDesnzParserAdapterDescriptor.CreateDefault();
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
    public void DefraDesnzDescriptorDoesNotIncludePlaceholderParserKeysOrSourceFamilies()
    {
        var blockedTerms = new[] { "placeholder", "manual", "test", "fake" };
        var descriptor = DefraDesnzParserAdapterDescriptor.CreateDefault();
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
    public void DefraDesnzDescriptorSnapshotsReadinessNotes()
    {
        var readinessNotes = new List<string>
        {
            "DEFRA/DESNZ parser adapter skeleton: parser execution is not implemented yet.",
        };
        var descriptor = new DefraDesnzParserAdapterDescriptor(
            "defra_desnz_parser_adapter",
            SourceFamily.DefraDesnz,
            ParserSelectionRegistry.GetParserKey(SourceFamily.DefraDesnz),
            new ParserAdapterCapability(
                [SourceFamily.DefraDesnz],
                [ParserSourceFormat.DiscoveryReference],
                ["application/x-carbonops-discovery-reference"],
                ["discovery"]),
            ParserAdapterReadiness.ExecutionNotImplemented,
            isExecutionImplemented: false,
            readinessNotes);

        readinessNotes.Clear();

        Assert.Equal(
            ["DEFRA/DESNZ parser adapter skeleton: parser execution is not implemented yet."],
            descriptor.ReadinessNotes);
    }
}
