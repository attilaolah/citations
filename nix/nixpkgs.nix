let
  src = (builtins.fromJSON (builtins.readFile ../flake.lock)).nodes.nixpkgs.locked;
  overlay = final: prev: {
    python = prev.python314.withPackages (ps:
      with ps; [
        pydantic
        pytest
      ]);
  };
in
  import (fetchTarball {
    url = "https://github.com/${src.owner}/${src.repo}/archive/${src.rev}.tar.gz";
    sha256 = src.narHash;
  }) {
    overlays = [overlay];
  }
