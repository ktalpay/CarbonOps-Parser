using Npgsql;

namespace CarbonOps.Parser.Contracts;

public sealed record SourceFamilyYearState(
    SourceFamily SourceFamily,
    int? LatestYear,
    int NextYear,
    int InitialYear);

public interface IPostgreSQLSourceFamilyYearStateSession
{
    Task<int?> LatestSuccessfulYearAsync(SourceFamily sourceFamily, CancellationToken cancellationToken = default);

    Task RecordSuccessfulYearAsync(
        SourceFamily sourceFamily,
        int ingestedYear,
        CancellationToken cancellationToken = default);
}

public sealed class PostgreSQLSourceFamilyYearStateRepository
{
    public const int DefaultInitialYear = 2024;

    private readonly IPostgreSQLSourceFamilyYearStateSession _session;

    public PostgreSQLSourceFamilyYearStateRepository(
        IPostgreSQLSourceFamilyYearStateSession session,
        int initialYear = DefaultInitialYear)
    {
        if (initialYear < 1)
        {
            throw new ArgumentOutOfRangeException(nameof(initialYear), initialYear, "initialYear must be positive.");
        }

        _session = session;
        InitialYear = initialYear;
    }

    public string ProviderName => "postgresql";

    public int InitialYear { get; }

    public async Task<int?> LatestSuccessfulYearAsync(
        SourceFamily sourceFamily,
        CancellationToken cancellationToken = default) =>
        await _session.LatestSuccessfulYearAsync(sourceFamily, cancellationToken).ConfigureAwait(false);

    public async Task<int> NextTargetYearAsync(
        SourceFamily sourceFamily,
        CancellationToken cancellationToken = default)
    {
        var latestYear = await LatestSuccessfulYearAsync(sourceFamily, cancellationToken).ConfigureAwait(false);
        return latestYear is null ? InitialYear : latestYear.Value + 1;
    }

    public async Task<SourceFamilyYearState> GetYearStateAsync(
        SourceFamily sourceFamily,
        CancellationToken cancellationToken = default)
    {
        var latestYear = await LatestSuccessfulYearAsync(sourceFamily, cancellationToken).ConfigureAwait(false);
        return new SourceFamilyYearState(
            sourceFamily,
            latestYear,
            latestYear is null ? InitialYear : latestYear.Value + 1,
            InitialYear);
    }

    public async Task RecordSuccessfulYearAsync(
        SourceFamily sourceFamily,
        int ingestedYear,
        CancellationToken cancellationToken = default)
    {
        if (ingestedYear < 1)
        {
            throw new ArgumentOutOfRangeException(nameof(ingestedYear), ingestedYear, "ingestedYear must be positive.");
        }

        await _session.RecordSuccessfulYearAsync(sourceFamily, ingestedYear, cancellationToken).ConfigureAwait(false);
    }
}

public sealed class NpgsqlSourceFamilyYearStateSession : IPostgreSQLSourceFamilyYearStateSession
{
    private readonly NpgsqlDataSource _dataSource;

    public NpgsqlSourceFamilyYearStateSession(NpgsqlDataSource dataSource)
    {
        _dataSource = dataSource;
    }

    public async Task<int?> LatestSuccessfulYearAsync(
        SourceFamily sourceFamily,
        CancellationToken cancellationToken = default)
    {
        await using var command = _dataSource.CreateCommand("""
            SELECT MAX(ingested_year)
            FROM source_family_year_states
            WHERE source_family = $1
            """);
        command.Parameters.AddWithValue(sourceFamily.ToPostgreSQLRuntimeValue());

        var value = await command.ExecuteScalarAsync(cancellationToken).ConfigureAwait(false);
        return value is null or DBNull ? null : Convert.ToInt32(value, System.Globalization.CultureInfo.InvariantCulture);
    }

    public async Task RecordSuccessfulYearAsync(
        SourceFamily sourceFamily,
        int ingestedYear,
        CancellationToken cancellationToken = default)
    {
        await using var command = _dataSource.CreateCommand("""
            INSERT INTO source_family_year_states (
                source_family_year_state_id,
                source_family,
                ingested_year,
                created_at,
                updated_at
            )
            VALUES ($1, $2, $3, NOW(), NOW())
            ON CONFLICT (source_family, ingested_year)
            DO UPDATE SET updated_at = EXCLUDED.updated_at
            """);
        command.Parameters.AddWithValue(Guid.NewGuid());
        command.Parameters.AddWithValue(sourceFamily.ToPostgreSQLRuntimeValue());
        command.Parameters.AddWithValue(ingestedYear);

        await command.ExecuteNonQueryAsync(cancellationToken).ConfigureAwait(false);
    }
}
