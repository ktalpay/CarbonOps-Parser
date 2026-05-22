using Npgsql;

namespace CarbonOps.Parser.Contracts;

public sealed record PostgreSQLRuntimeSchemaBootstrapExecutionResult(
    IReadOnlyList<string> RequiredTableNames,
    IReadOnlyList<string> PresentTableNames,
    IReadOnlyList<string> MissingTableNames,
    IReadOnlyList<string> CreatedTableNames,
    int StatementCount);

public static class PostgreSQLRuntimeSchemaDdl
{
    public static IReadOnlyList<string> RenderIdempotentSchemaStatements() =>
        Array.AsReadOnly(
            PostgreSQLRuntimeSchemaCatalog.Tables
                .Select(RenderCreateTableStatement)
                .Concat(PostgreSQLRuntimeSchemaCatalog.Tables.SelectMany(RenderIndexStatements))
                .ToArray());

    public static IReadOnlyList<string> DestructiveSqlTokens { get; } = Array.AsReadOnly(
        new[]
        {
            "DROP ",
            "TRUNCATE ",
            "DELETE ",
            "ALTER TABLE ",
            "RENAME ",
        });

    public static bool ContainsDestructiveSql(string statement) =>
        DestructiveSqlTokens.Any(token => statement.Contains(token, StringComparison.OrdinalIgnoreCase));

    private static string RenderCreateTableStatement(PostgreSQLRuntimeTable table)
    {
        var lines = new List<string>();
        var primaryKeyColumns = new List<string>();

        foreach (var column in table.Columns)
        {
            var columnSql = $"{column.Name} {RenderDataType(column.DataType)}";
            if (!column.Nullable)
            {
                columnSql += " NOT NULL";
            }

            lines.Add(columnSql);
            if (column.IsPrimaryKey)
            {
                primaryKeyColumns.Add(column.Name);
            }
        }

        if (primaryKeyColumns.Count > 0)
        {
            lines.Add($"CONSTRAINT pk_{table.Name} PRIMARY KEY ({string.Join(", ", primaryKeyColumns)})");
        }

        foreach (var uniqueConstraint in table.UniqueConstraints ?? [])
        {
            lines.Add(
                $"CONSTRAINT {uniqueConstraint.Name} UNIQUE ({string.Join(", ", uniqueConstraint.ColumnNames)})");
        }

        foreach (var foreignKey in table.ForeignKeys ?? [])
        {
            lines.Add(
                $"CONSTRAINT fk_{table.Name}_{foreignKey.ColumnName} FOREIGN KEY ({foreignKey.ColumnName}) " +
                $"REFERENCES {foreignKey.ReferencedTableName} ({foreignKey.ReferencedColumnName})");
        }

        return $"CREATE TABLE IF NOT EXISTS {table.Name} (\n    {string.Join(",\n    ", lines)}\n);";
    }

    private static IEnumerable<string> RenderIndexStatements(PostgreSQLRuntimeTable table)
    {
        foreach (var index in table.Indexes ?? [])
        {
            var uniquePrefix = index.Unique ? "UNIQUE " : string.Empty;
            yield return
                $"CREATE {uniquePrefix}INDEX IF NOT EXISTS {index.Name} " +
                $"ON {table.Name} ({string.Join(", ", index.ColumnNames)});";
        }
    }

    private static string RenderDataType(PostgreSQLRuntimeColumnType dataType) =>
        dataType switch
        {
            PostgreSQLRuntimeColumnType.Uuid => "uuid",
            PostgreSQLRuntimeColumnType.Text => "text",
            PostgreSQLRuntimeColumnType.Integer => "integer",
            PostgreSQLRuntimeColumnType.Numeric => "numeric",
            PostgreSQLRuntimeColumnType.TimestampWithTimeZone => "timestamp with time zone",
            PostgreSQLRuntimeColumnType.Jsonb => "jsonb",
            _ => throw new ArgumentOutOfRangeException(nameof(dataType), dataType, null),
        };
}

public sealed class PostgreSQLRuntimeSchemaBootstrapper
{
    public async Task<PostgreSQLRuntimeSchemaBootstrapExecutionResult> BootstrapAsync(
        PostgreSQLRuntimeConnectionSettings settings,
        CancellationToken cancellationToken = default)
    {
        var validation = PostgreSQLRuntimeConnectionBoundary.Validate(settings);
        if (!validation.IsValid)
        {
            throw new ArgumentException("PostgreSQL runtime settings are invalid.", nameof(settings));
        }

        var statements = PostgreSQLRuntimeSchemaDdl.RenderIdempotentSchemaStatements();
        if (statements.Any(PostgreSQLRuntimeSchemaDdl.ContainsDestructiveSql))
        {
            throw new InvalidOperationException("Schema bootstrap contains destructive SQL.");
        }

        await using var dataSource = NpgsqlDataSource.Create(
            PostgreSQLRuntimeConnectionBoundary.BuildConnectionString(settings));
        await using var connection = await dataSource.OpenConnectionAsync(cancellationToken).ConfigureAwait(false);

        var requiredTableNames = PostgreSQLRuntimeSchemaCatalog.RequiredTableNames;
        var schema = PostgreSQLRuntimeConnectionBoundary.RenderIdentifier(settings.Schema, "schema");
        await using (var schemaCommand = connection.CreateCommand())
        {
            schemaCommand.CommandText = $"CREATE SCHEMA IF NOT EXISTS {schema};";
            await schemaCommand.ExecuteNonQueryAsync(cancellationToken).ConfigureAwait(false);
        }

        await using (var searchPathCommand = connection.CreateCommand())
        {
            searchPathCommand.CommandText = $"SET search_path TO {schema};";
            await searchPathCommand.ExecuteNonQueryAsync(cancellationToken).ConfigureAwait(false);
        }

        var presentBefore = await FetchPresentTableNamesAsync(connection, requiredTableNames, cancellationToken)
            .ConfigureAwait(false);

        foreach (var statement in statements)
        {
            await using var command = connection.CreateCommand();
            command.CommandText = statement;
            await command.ExecuteNonQueryAsync(cancellationToken).ConfigureAwait(false);
        }

        var presentAfter = await FetchPresentTableNamesAsync(connection, requiredTableNames, cancellationToken)
            .ConfigureAwait(false);
        var created = requiredTableNames
            .Where(tableName => presentAfter.Contains(tableName, StringComparer.Ordinal) &&
                !presentBefore.Contains(tableName, StringComparer.Ordinal))
            .ToArray();
        var missing = requiredTableNames
            .Where(tableName => !presentAfter.Contains(tableName, StringComparer.Ordinal))
            .ToArray();

        return new PostgreSQLRuntimeSchemaBootstrapExecutionResult(
            requiredTableNames,
            Array.AsReadOnly(presentAfter.ToArray()),
            Array.AsReadOnly(missing),
            Array.AsReadOnly(created),
            statements.Count + 2);
    }

    private static async Task<IReadOnlyList<string>> FetchPresentTableNamesAsync(
        NpgsqlConnection connection,
        IReadOnlyList<string> requiredTableNames,
        CancellationToken cancellationToken)
    {
        await using var command = connection.CreateCommand();
        command.CommandText = """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = current_schema()
              AND table_name = ANY($1)
            ORDER BY table_name
            """;
        command.Parameters.AddWithValue(requiredTableNames.ToArray());

        var present = new HashSet<string>(StringComparer.Ordinal);
        await using var reader = await command.ExecuteReaderAsync(cancellationToken).ConfigureAwait(false);
        while (await reader.ReadAsync(cancellationToken).ConfigureAwait(false))
        {
            present.Add(reader.GetString(0));
        }

        return Array.AsReadOnly(
            requiredTableNames
                .Where(tableName => present.Contains(tableName))
                .ToArray());
    }
}
