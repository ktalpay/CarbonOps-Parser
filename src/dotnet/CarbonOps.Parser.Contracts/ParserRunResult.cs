namespace CarbonOps.Parser.Contracts;

public sealed record ParserRunResult
{
    public ParserRunRequest Request { get; }

    public ParserRunStatus Status { get; }

    public int TotalRows { get; }

    public int AcceptedRows { get; }

    public int RejectedRows { get; }

    public IReadOnlyList<ParserRunIssue> Issues { get; }

    public ParserRunResult(
        ParserRunRequest request,
        ParserRunStatus status,
        int totalRows,
        int acceptedRows,
        int rejectedRows,
        IEnumerable<ParserRunIssue>? issues = null)
    {
        Request = request;
        Status = status;
        TotalRows = totalRows;
        AcceptedRows = acceptedRows;
        RejectedRows = rejectedRows;
        Issues = Array.AsReadOnly((issues ?? []).ToArray());
    }
}
