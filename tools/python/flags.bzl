"""Custom build settings for Python tooling."""

def _bool_flag_impl(_ctx):
    return []

bool_flag = rule(
    implementation = _bool_flag_impl,
    build_setting = config.bool(flag = True),
)
