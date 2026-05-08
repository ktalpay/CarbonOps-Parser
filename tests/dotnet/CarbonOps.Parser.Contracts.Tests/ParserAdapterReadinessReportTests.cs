using System.Reflection;
using CarbonOps.Parser.Contracts;

namespace CarbonOps.Parser.Contracts.Tests;

public sealed class ParserAdapterReadinessReportTests
{
    [Fact]
    public void ReportContainsExactlyPhaseOneParserAdapterDescriptors()
    {
        var report = ParserAdapterReadinessReport.CreateDefault();

        Assert.Equal(3, report.AdapterCount);
        Assert.Equal(
            ParserAdapterDescriptorRegistry.Descriptors.Select(descriptor => descriptor.SourceFamily),
            report.Adapters.Select(adapter => adapter.SourceFamily));
        Assert.Equal(
            [
                SourceFamily.GhgProtocol,
                SourceFamily.DefraDesnz,
                SourceFamily.IpccEfdb,
            ],
            report.Adapters.Select(adapter => adapter.SourceFamily));
    }

    [Fact]
    public void ReportSourceKeysAlignWithDescriptorRegistryMetadata()
    {
        var report = ParserAdapterReadinessReport.CreateDefault();

        Assert.Equal(
            ParserAdapterDescriptorRegistry.Descriptors.Select(descriptor => descriptor.SourceFamily.ToWireName()),
            report.Adapters.Select(adapter => adapter.SourceKey));

        foreach (var adapter in report.Adapters)
        {
            Assert.True(ParserAdapterDescriptorRegistry.TryGetBySourceKey(adapter.SourceKey, out var descriptor));
            Assert.NotNull(descriptor);
            Assert.Equal(descriptor!.SourceFamily, adapter.SourceFamily);
        }
    }

    [Fact]
    public void ReportParserKeysAlignWithDescriptorRegistryMetadata()
    {
        var report = ParserAdapterReadinessReport.CreateDefault();

        Assert.Equal(
            ParserAdapterDescriptorRegistry.Descriptors.Select(descriptor => descriptor.ParserKey),
            report.Adapters.Select(adapter => adapter.ParserKey));

        foreach (var adapter in report.Adapters)
        {
            Assert.True(ParserAdapterDescriptorRegistry.TryGetByParserKey(adapter.ParserKey, out var descriptor));
            Assert.NotNull(descriptor);
            Assert.Equal(descriptor!.ParserKey, adapter.ParserKey);
        }
    }

    [Fact]
    public void ReportOrderingIsDeterministic()
    {
        var first = ParserAdapterReadinessReport.CreateDefault();
        var second = ParserAdapterReadinessReport.CreateDefault();

        Assert.NotSame(first, second);
        Assert.NotSame(first.Adapters, second.Adapters);
        Assert.Equal(
            first.Adapters.Select(adapter => adapter.SourceKey),
            second.Adapters.Select(adapter => adapter.SourceKey));
        Assert.Equal(
            first.Adapters.Select(adapter => adapter.ParserKey),
            second.Adapters.Select(adapter => adapter.ParserKey));
        Assert.Equal(
            first.Adapters.Select(adapter => adapter.AdapterName),
            second.Adapters.Select(adapter => adapter.AdapterName));
        Assert.Equal(
            ParserAdapterDescriptorRegistry.Descriptors.Select(descriptor => descriptor.SourceFamily),
            first.Adapters.Select(adapter => adapter.SourceFamily));
        Assert.Equal(
            ParserAdapterDescriptorRegistry.Descriptors.Select(descriptor => descriptor.ParserKey),
            first.Adapters.Select(adapter => adapter.ParserKey));
    }

    [Fact]
    public void ReportUsesDescriptorMetadataWithoutDivergentCopies()
    {
        var report = ParserAdapterReadinessReport.CreateDefault();

        foreach (var pair in ParserAdapterDescriptorRegistry.Descriptors.Zip(report.Adapters))
        {
            var descriptor = pair.First;
            var adapter = pair.Second;

            Assert.Equal(descriptor.SourceFamily.ToWireName(), adapter.SourceKey);
            Assert.Equal(descriptor.SourceFamily, adapter.SourceFamily);
            Assert.Equal(descriptor.ParserKey, adapter.ParserKey);
            Assert.Equal(descriptor.AdapterName, adapter.AdapterName);
            Assert.Equal(descriptor.Readiness, adapter.Readiness);
            Assert.Equal(descriptor.IsExecutionImplemented, adapter.IsExecutionImplemented);
            Assert.Same(descriptor.Capability, adapter.Capability);
            Assert.Equal(descriptor.ReadinessNotes, adapter.ReadinessNotes);
        }
    }

    [Fact]
    public void ReportSnapshotsEntryEnumerationAndReadinessNotes()
    {
        var readinessNotes = new List<string> { "parser execution is not implemented" };
        var entry = new ParserAdapterReadinessReportEntry(
            SourceFamily.GhgProtocol.ToWireName(),
            SourceFamily.GhgProtocol,
            ParserSelectionRegistry.GetParserKey(SourceFamily.GhgProtocol),
            "ghg_protocol_parser_adapter",
            ParserAdapterReadiness.ExecutionNotImplemented,
            isExecutionImplemented: false,
            GhgProtocolParserAdapterDescriptor.CreateDefault().Capability,
            readinessNotes);
        var entries = new List<ParserAdapterReadinessReportEntry> { entry };

        var report = new ParserAdapterReadinessReport(entries);
        entries.Clear();
        readinessNotes.Clear();

        Assert.Equal([SourceFamily.GhgProtocol], report.Adapters.Select(adapter => adapter.SourceFamily));
        Assert.Equal(["parser execution is not implemented"], report.Adapters[0].ReadinessNotes);
        Assert.NotSame(readinessNotes, report.Adapters[0].ReadinessNotes);
    }

    [Fact]
    public void ReportConstructionRemainsRuntimePassive()
    {
        var report = ParserAdapterReadinessReport.CreateDefault();
        var reportMethods = typeof(ParserAdapterReadinessReport)
            .GetMethods(BindingFlags.Public | BindingFlags.Static | BindingFlags.Instance | BindingFlags.DeclaredOnly)
            .Select(method => method.Name)
            .ToArray();
        var entryMethods = typeof(ParserAdapterReadinessReportEntry)
            .GetMethods(BindingFlags.Public | BindingFlags.Static | BindingFlags.Instance | BindingFlags.DeclaredOnly)
            .Select(method => method.Name)
            .ToArray();

        Assert.All(report.Adapters, adapter => Assert.False(adapter.IsExecutionImplemented));
        Assert.DoesNotContain("Parse", reportMethods);
        Assert.DoesNotContain("Execute", reportMethods);
        Assert.DoesNotContain("Parse", entryMethods);
        Assert.DoesNotContain("Execute", entryMethods);
    }

    [Fact]
    public void ReportDoesNotIntroduceDbHttpFileIoOrParserExecutionSurface()
    {
        var publicMembers = typeof(ParserAdapterReadinessReport)
            .GetMembers(BindingFlags.Public | BindingFlags.Static | BindingFlags.Instance | BindingFlags.DeclaredOnly)
            .Concat(typeof(ParserAdapterReadinessReportEntry)
                .GetMembers(BindingFlags.Public | BindingFlags.Static | BindingFlags.Instance | BindingFlags.DeclaredOnly))
            .Select(member => member.Name)
            .ToArray();
        var blockedIoTerms = new[] { "Db", "Sql", "Http", "File", "Csv", "Xlsx", "Pdf", "Json" };

        foreach (var term in blockedIoTerms)
        {
            Assert.DoesNotContain(publicMembers, member => member.Contains(term, StringComparison.OrdinalIgnoreCase));
        }

        Assert.DoesNotContain("Parse", publicMembers);
        Assert.DoesNotContain("Execute", publicMembers);
    }
}
