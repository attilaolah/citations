{
  description = "Citations repository flake";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
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
          inherit (pkgs.python314Packages) docling docling-parse docling-ibm-models;
          bazel = pkgs.bazel_9;
        };
        devShells.default = pkgs.mkShell {
          packages = with pkgs; [
            bazel_9
            (python314.withPackages (ps:
              with ps; [
                docling
                docling-parse
              ]))

            alejandra
            buildifier
            prettier
          ];
        };
      };
    };
}
