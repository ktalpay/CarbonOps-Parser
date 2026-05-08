namespace CarbonOps.Parser.Contracts;

public sealed record ParserExecutionRequest(
    SourceFamily SourceFamily,
    ParserKey ParserKey,
    ParserInputDocument InputDocument,
    ParserRunRequest ParserRunRequest,
    ParserExecutionBoundaryDescriptor BoundaryDescriptor);
