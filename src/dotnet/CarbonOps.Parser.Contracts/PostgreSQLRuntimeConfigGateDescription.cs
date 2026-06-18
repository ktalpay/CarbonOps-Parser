namespace CarbonOps.Parser.Contracts;

public sealed record PostgreSQLRuntimeConfigGateDescription
{
    public PostgreSQLRuntimeConfigGateStatus DefaultStatus { get; }

    public bool DisabledByDefault { get; }

    public bool AcceptsCallerIntent { get; }

    public bool LoadsEnvironment { get; }

    public bool LoadsConfigFiles { get; }

    public bool LoadsCredentials { get; }

    public bool OpensConnection { get; }

    public bool RunsSql { get; }

    public IReadOnlyList<string> Notes { get; }

    public PostgreSQLRuntimeConfigGateDescription(
        PostgreSQLRuntimeConfigGateStatus defaultStatus,
        bool disabledByDefault,
        bool acceptsCallerIntent,
        bool loadsEnvironment,
        bool loadsConfigFiles,
        bool loadsCredentials,
        bool opensConnection,
        bool runsSql,
        IEnumerable<string> notes)
    {
        DefaultStatus = defaultStatus;
        DisabledByDefault = disabledByDefault;
        AcceptsCallerIntent = acceptsCallerIntent;
        LoadsEnvironment = loadsEnvironment;
        LoadsConfigFiles = loadsConfigFiles;
        LoadsCredentials = loadsCredentials;
        OpensConnection = opensConnection;
        RunsSql = runsSql;
        Notes = Array.AsReadOnly(notes.ToArray());
    }
}
