let
  src = (builtins.fromJSON (builtins.readFile ../flake.lock)).nodes.nixpkgs.locked;
  pythonOverlay = import ./overlays/python.nix;
in
  import (fetchTarball {
    url = "https://github.com/${src.owner}/${src.repo}/archive/${src.rev}.tar.gz";
    sha256 = src.narHash;
  }) {
    overlays = [pythonOverlay];
  }
