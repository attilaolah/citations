{
  description = "Citations repository flake";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/ba6620cf1df0361c9737822330edba8bd5816377";
    flake-parts.url = "github:hercules-ci/flake-parts";
    systems.url = "github:nix-systems/default";
  };

  outputs = inputs @ {
    self,
    flake-parts,
    systems,
    ...
  }:
    flake-parts.lib.mkFlake {inherit inputs;} {
      systems = import systems;
      flake.overlays = import ./nix/overlays/default.nix;

      perSystem = {system, ...}: let
        pkgs = import inputs.nixpkgs {
          inherit system;
          overlays = [self.overlays.default];
        };
      in {
        formatter = pkgs.alejandra;
        packages = {
          inherit (pkgs) gnfinder gnparser;
          bazel = pkgs.bazel_9;
        };
        devShells.default = pkgs.mkShell {
          packages = with pkgs; [
            bazel_9
            gnfinder
            gnparser
            (python314.withPackages (ps:
              with ps; [
                docling
                docling-parse
              ]))

            alejandra
            black
            buildifier
            prettier
            pyright
            pyupgrade
            ruff
            ty
            uv
          ];
        };
      };
    };
}
