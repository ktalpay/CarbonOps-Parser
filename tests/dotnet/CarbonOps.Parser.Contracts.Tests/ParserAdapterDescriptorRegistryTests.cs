using System.Reflection;
using CarbonOps.Parser.Contracts;

namespace CarbonOps.Parser.Contracts.Tests;

public sealed class ParserAdapterDescriptorRegistryTests
{
    [Fact]
    public void RegistryContainsAllPhaseOneParserAdapterDescriptors()
    {
        var descriptors = ParserAdapterDescriptorRegistry.Descriptors;

        Assert.Equal(
            [
                SourceFamily.GhgProtocol,
                SourceFamily.DefraDesnz,
                SourceFamily.IpccEfdb,
            ],
            descriptors.Select(descriptor => descriptor.SourceFamily));
        Assert.IsType<GhgProtocolParserAdapterDescriptor>(descriptors[0]);
        Assert.IsType<DefraDesnzParserAdapterDescriptor>(descriptors[1]);
        Assert.IsType<IpccEfdbParserAdapterDescriptor>(descriptors[2]);
    }

    [Fact]
    public void RegistrySourceKeysAlignWithDescriptorMetadata()
    {
        foreach (var descriptor in ParserAdapterDescriptorRegistry.Descriptors)
        {
            var found = ParserAdapterDescriptorRegistry.TryGetBySourceKey(
                descriptor.SourceFamily.ToWireName(),
                out var lookupDescriptor);

            Assert.True(found);
            Assert.NotNull(lookupDescriptor);
            Assert.Same(descriptor, lookupDescriptor);
            Assert.Equal(descriptor.SourceFamily.ToWireName(), lookupDescriptor!.SourceFamily.ToWireName());
        }
    }

    [Fact]
    public void RegistryParserKeysAlignWithDescriptorMetadata()
    {
        foreach (var descriptor in ParserAdapterDescriptorRegistry.Descriptors)
        {
            var found = ParserAdapterDescriptorRegistry.TryGetByParserKey(
                descriptor.ParserKey,
                out var lookupDescriptor);

            Assert.True(found);
            Assert.NotNull(lookupDescriptor);
            Assert.Same(descriptor, lookupDescriptor);
            Assert.Equal(ParserSelectionRegistry.GetParserKey(descriptor.SourceFamily), lookupDescriptor!.ParserKey);
        }
    }

    [Fact]
    public void RegistryLookupsAreDeterministic()
    {
        var first = ParserAdapterDescriptorRegistry.Descriptors;
        var second = ParserAdapterDescriptorRegistry.Descriptors;

        Assert.Same(first, second);
        Assert.Equal(first, second);
        Assert.Equal(SourceFamilyRegistry.SupportedFamilies, first.Select(descriptor => descriptor.SourceFamily));
        Assert.Equal(
            [
                "ghg_protocol_phase1_parser",
                "defra_desnz_phase1_parser",
                "ipcc_efdb_phase1_parser",
            ],
            first.Select(descriptor => descriptor.ParserKey.Value));
    }

    [Fact]
    public void UnknownSourceKeyLookupFailsClearly()
    {
        var found = ParserAdapterDescriptorRegistry.TryGetBySourceKey(
            "unknown_source_family",
            out var descriptor);

        Assert.False(found);
        Assert.Null(descriptor);
    }

    [Fact]
    public void UnknownParserKeyLookupFailsClearly()
    {
        var found = ParserAdapterDescriptorRegistry.TryGetByParserKey(
            new ParserKey("unknown_phase1_parser"),
            out var descriptor);

        Assert.False(found);
        Assert.Null(descriptor);
    }

    [Fact]
    public void RegistryDoesNotExposeParserExecutionMethods()
    {
        var registryMethods = typeof(ParserAdapterDescriptorRegistry)
            .GetMethods(BindingFlags.Public | BindingFlags.Static | BindingFlags.DeclaredOnly)
            .Select(method => method.Name)
            .ToArray();
        var descriptorMethods = ParserAdapterDescriptorRegistry.Descriptors
            .SelectMany(descriptor => descriptor.GetType()
                .GetMethods(BindingFlags.Instance | BindingFlags.Public | BindingFlags.DeclaredOnly)
                .Select(method => method.Name))
            .ToArray();

        Assert.DoesNotContain("Parse", registryMethods);
        Assert.DoesNotContain("Execute", registryMethods);
        Assert.DoesNotContain("Parse", descriptorMethods);
        Assert.DoesNotContain("Execute", descriptorMethods);
    }

    [Fact]
    public void RegistryMetadataDoesNotContainUrlLookingReferences()
    {
        var metadataValues = ParserAdapterDescriptorRegistry.Descriptors.SelectMany(descriptor =>
            descriptor.Capability.SupportedContentTypes
                .Concat(descriptor.Capability.SupportedFormatHints)
                .Concat(descriptor.ReadinessNotes)
                .Append(descriptor.AdapterName)
                .Append(descriptor.ParserKey.Value)
                .Append(descriptor.SourceFamily.ToWireName()));

        foreach (var value in metadataValues)
        {
            Assert.DoesNotContain("://", value);
            Assert.DoesNotContain("http", value, StringComparison.OrdinalIgnoreCase);
        }
    }
}
