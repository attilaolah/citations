"""Rule for building a DuckDB database from Catalogue of Life exports."""

def _col_name_db_impl(ctx):
    name_usage = ctx.file.name_usage
    duckdb_bin = ctx.file._duckdb
    schema_sql = ctx.file._schema_sql
    import_sql_template = ctx.file._import_sql_template
    out = ctx.actions.declare_file(ctx.label.name + ".duckdb")
    import_sql = ctx.actions.declare_file(ctx.label.name + ".import.sql")

    ctx.actions.expand_template(
        template = import_sql_template,
        output = import_sql,
        substitutions = {
            "{NAME_USAGE_PATH}": name_usage.path,
            "{SCHEMA_SQL_PATH}": schema_sql.path,
        },
        is_executable = False,
    )

    args = ctx.actions.args()
    args.add(out.path)
    args.add("-f", import_sql.path)
    ctx.actions.run(
        executable = duckdb_bin,
        arguments = [args],
        inputs = [name_usage, duckdb_bin, import_sql, import_sql_template, schema_sql],
        outputs = [out],
        mnemonic = "BuildColNameDb",
        progress_message = "Building CoL name DB from %s" % name_usage.short_path,
    )

    return DefaultInfo(files = depset([out]))

col_name_db = rule(
    implementation = _col_name_db_impl,
    attrs = {
        "name_usage": attr.label(
            allow_single_file = True,
            mandatory = True,
        ),
        "_duckdb": attr.label(
            cfg = "exec",
            allow_single_file = True,
            default = "@duckdb//:bin/duckdb",
        ),
        "_import_sql_template": attr.label(
            allow_single_file = True,
            default = "//tools/col:import.sql.tpl",
        ),
        "_schema_sql": attr.label(
            allow_single_file = True,
            default = "//tools/col:schema.sql",
        ),
    },
)
