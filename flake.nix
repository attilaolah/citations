{
  description = "Citations repository flake";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/24d724fc55d4bf31a7283621f2b456950531d030";
    flake-parts.url = "github:hercules-ci/flake-parts";
    systems.url = "github:nix-systems/default";
  };

  outputs = inputs @ {
    flake-parts,
    systems,
    ...
  }: let
    python314Overlay = final: prev: {
      python = prev.python314.withPackages (ps:
        with ps; [
          pydantic
          pytest
        ]);
    };
  in
    flake-parts.lib.mkFlake {inherit inputs;} {
      systems = import systems;
      flake.overlays.default = python314Overlay;

      perSystem = {system, ...}: let
        pkgs = import inputs.nixpkgs {
          inherit system;
          overlays = [python314Overlay];
        };
      in {
        formatter = pkgs.alejandra;
        devShells.default = pkgs.mkShell {
          packages = with pkgs; [
            bazel_9
            gnfinder
            gnparser
            python

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
