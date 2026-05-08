namespace CarbonOps.Parser.Contracts;

public interface IParserAdapterDescriptor
{
    string AdapterName { get; }

    SourceFamily SourceFamily { get; }

    ParserKey ParserKey { get; }

    ParserAdapterCapability Capability { get; }

    ParserAdapterReadiness Readiness { get; }

    bool IsExecutionImplemented { get; }

    IReadOnlyList<string> ReadinessNotes { get; }
}
