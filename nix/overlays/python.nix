let
  pyproject = builtins.fromTOML (builtins.readFile ../../pyproject.toml);
  deps = pyproject.project.dependencies or [];

  depname = requirement: let
    # PEP 508 requirement strings start with the distribution name.
    match = builtins.match "^([A-Za-z0-9][A-Za-z0-9._-]*)" requirement;
  in
    if match == null
    then throw "Unsupported Python requirement in pyproject.toml: ${requirement}"
    else builtins.elemAt match 0;
in
  final: prev: {
    python =
      prev.python314.withPackages (ps:
        map (name: ps.${name}) (map depname deps));
  }
