namespace CarbonOps.Parser.Contracts;

public static class SourceDocumentManifestRegistry
{
    public static SourceDocumentManifest CreateDefaultDryRunManifest() =>
        CreateDryRunManifest(SourceDownloadPlanRegistry.CreateDefaultDryRunPlan());

    public static SourceDocumentManifest CreateDryRunManifest(SourceDownloadPlan downloadPlan) =>
        new(downloadPlan.Requests.Select(request => new SourceDocumentManifestEntry(
            request.SourceFamily,
            request.SourceName,
            request.SourceReference,
            CreateDryRunChecksum(request.SourceFamily))));

    private static SourceDocumentChecksum CreateDryRunChecksum(SourceFamily sourceFamily) =>
        new(
            "dry_run_sha256",
            $"{sourceFamily.ToWireName()}_dry_run_checksum",
            IsDryRunPlaceholder: true);
}
