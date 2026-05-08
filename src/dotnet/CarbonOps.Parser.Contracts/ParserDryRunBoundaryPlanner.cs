namespace CarbonOps.Parser.Contracts;

public static class ParserDryRunBoundaryPlanner
{
    public static ParserDryRunBoundaryPlanBatch CreateDefaultDryRunPlanBatch() =>
        new(ParserAdapterRunRegistry.CreateDefaultDryRunRequestBatch()
            .Requests
            .Select(CreatePlan));

    public static ParserDryRunBoundaryResultBatch CreateDefaultDryRunResultBatch() =>
        new(CreateDefaultDryRunPlanBatch().Plans.Select(CreateResult));

    public static ParserDryRunBoundaryPlan CreatePlan(ParserAdapterRunRequest request)
    {
        var validationResult = request.Validate();
        var descriptorFound = ParserAdapterDescriptorRegistry.TryGetBySourceFamily(
            request.SourceFamily,
            out var descriptor);
        var readiness = descriptor?.Readiness ?? ParserAdapterReadiness.ExecutionNotImplemented;
        var isExecutionImplemented = descriptor?.IsExecutionImplemented ?? false;
        var isStructurallyExecutable = validationResult.IsValid && descriptorFound;
        var validationIssues = validationResult.Errors
            .Select((error, index) => CreateValidationIssue(request, error, index))
            .ToList();

        if (validationResult.IsValid && !isExecutionImplemented)
        {
            validationIssues.Add(CreateReadinessIssue(request, readiness));
        }

        var status = validationResult.IsValid
            ? isExecutionImplemented ? ParserDryRunStatus.Planned : ParserDryRunStatus.ExecutionNotImplemented
            : ParserDryRunStatus.InvalidRequest;

        return new ParserDryRunBoundaryPlan(
            request.SourceFamily,
            request.SourceKey,
            request.ParserKey,
            request,
            status,
            readiness,
            isExecutionImplemented,
            isStructurallyExecutable,
            validationIssues);
    }

    public static ParserDryRunBoundaryResult CreateResult(ParserDryRunBoundaryPlan plan)
    {
        var runResult = new ParserAdapterRunResult(
            plan.SourceFamily,
            plan.SourceKey,
            plan.ParserKey,
            ParserRunStatus.Pending,
            plan.Request.Artifacts.Select(artifact => artifact.ArtifactReference),
            [],
            plan.ValidationIssues,
            plan.Request.RunId,
            plan.Request.CorrelationId,
            plan.Request.RequestedReportingYear);

        return new ParserDryRunBoundaryResult(
            plan.SourceFamily,
            plan.SourceKey,
            plan.ParserKey,
            plan.Request,
            runResult,
            plan.Status,
            plan.Readiness,
            plan.IsExecutionImplemented,
            plan.IsStructurallyExecutable,
            plan.ValidationIssues);
    }

    private static ParserValidationIssue CreateReadinessIssue(
        ParserAdapterRunRequest request,
        ParserAdapterReadiness readiness) =>
        new(
            request.SourceFamily,
            request.SourceKey,
            request.ParserKey,
            ParserValidationIssueSeverity.Info,
            "PARSER_DRY_RUN_EXECUTION_NOT_IMPLEMENTED",
            "Parser adapter execution is not implemented; dry-run remains metadata-only.",
            request.Artifacts.FirstOrDefault()?.ArtifactReference,
            context:
            [
                new ParserValidationIssueContext("readiness", readiness.ToWireName()),
                new ParserValidationIssueContext("is_execution_implemented", "false"),
            ]);

    private static ParserValidationIssue CreateValidationIssue(
        ParserAdapterRunRequest request,
        string error,
        int index) =>
        new(
            request.SourceFamily,
            request.SourceKey,
            request.ParserKey,
            ParserValidationIssueSeverity.Error,
            "PARSER_DRY_RUN_REQUEST_INVALID",
            error,
            request.Artifacts.FirstOrDefault()?.ArtifactReference,
            context:
            [
                new ParserValidationIssueContext("validation_error_index", index.ToString()),
            ]);
}
