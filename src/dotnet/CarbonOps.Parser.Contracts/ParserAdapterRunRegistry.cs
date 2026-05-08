namespace CarbonOps.Parser.Contracts;

public static class ParserAdapterRunRegistry
{
    public static ParserAdapterRunRequestBatch CreateDefaultDryRunRequestBatch()
    {
        var artifactsBySourceFamily = ParserInputArtifactRegistry.CreateDefaultDryRunBatch()
            .Artifacts
            .GroupBy(artifact => artifact.SourceFamily)
            .ToDictionary(group => group.Key, group => group.ToArray());

        return new ParserAdapterRunRequestBatch(ParserAdapterDescriptorRegistry.Descriptors.Select(descriptor =>
        {
            if (!artifactsBySourceFamily.TryGetValue(descriptor.SourceFamily, out var artifacts))
            {
                throw new InvalidOperationException(
                    $"Parser input artifacts are missing for source family '{descriptor.SourceFamily.ToWireName()}'.");
            }

            return ParserAdapterRunRequest.FromDescriptorAndArtifacts(descriptor, artifacts);
        }));
    }

    public static ParserAdapterRunResultBatch CreateDefaultDryRunResultBatch()
    {
        var rowsBySourceFamily = ParserNormalizedOutputRegistry.CreateDefaultDryRunBatch()
            .Rows
            .GroupBy(row => row.SourceFamily)
            .ToDictionary(group => group.Key, group => group.ToArray());
        var issuesBySourceFamily = ParserValidationIssueRegistry.CreateDefaultDryRunBatch()
            .Issues
            .GroupBy(issue => issue.SourceFamily)
            .ToDictionary(group => group.Key, group => group.ToArray());

        return new ParserAdapterRunResultBatch(CreateDefaultDryRunRequestBatch().Requests.Select(request =>
            ParserAdapterRunResult.FromRequestRowsAndIssues(
                request,
                rowsBySourceFamily.TryGetValue(request.SourceFamily, out var rows) ? rows : [],
                issuesBySourceFamily.TryGetValue(request.SourceFamily, out var issues) ? issues : [])));
    }
}
