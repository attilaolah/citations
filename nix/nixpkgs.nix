{overlays ? [], ...} @ args: let
  src = (builtins.fromJSON (builtins.readFile ../flake.lock)).nodes.nixpkgs.locked;
in
  import (fetchTarball {
    url = "https://github.com/${src.owner}/${src.repo}/archive/${src.rev}.tar.gz";
    sha256 = src.narHash;
  }) (args
    // {
      overlays = [(import ./overlays/python.nix)] ++ overlays;
    })
