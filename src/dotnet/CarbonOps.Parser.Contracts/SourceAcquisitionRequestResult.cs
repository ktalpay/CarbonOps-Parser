namespace CarbonOps.Parser.Contracts;

public sealed record SourceAcquisitionRequestResult(
    SourceAcquisitionRequest Request,
    SourceAcquisitionRequestResultStatus Status = SourceAcquisitionRequestResultStatus.Planned);
