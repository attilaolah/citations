"""Shared action helpers for Python-backed Starlark rules."""

def run_py(
        ctx,
        *,
        executable,
        arguments = [],
        inputs = [],
        outputs = [],
        tools = [],
        mnemonic = "",
        progress_message = "",
        env = {}):
    """Run an action with PATH set to `ctx.file._python`'s directory.

    Args:
      ctx: Rule context.
      executable: Executable file to run.
      arguments: Sequence of action arguments.
      inputs: Additional input files for the action.
      outputs: Output files for the action.
      tools: Tool files needed by the action.
      mnemonic: Mnemonic label for the action.
      progress_message: Progress message displayed during execution.
      env: Extra environment variables merged into the action environment.
    """
    action_env = dict(env)
    action_env["PATH"] = ctx.file._python.path.rsplit("/", 1)[0]
    action_inputs = inputs + [ctx.file._python]

    ctx.actions.run(
        executable = executable,
        arguments = arguments,
        env = action_env,
        inputs = action_inputs,
        outputs = outputs,
        tools = tools,
        mnemonic = mnemonic,
        progress_message = progress_message,
    )
