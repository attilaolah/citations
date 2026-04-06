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
  }:
    flake-parts.lib.mkFlake {inherit inputs;} {
      systems = import systems;

      perSystem = {system, ...}: let
        pkgs = import inputs.nixpkgs {inherit system;};
        python315 = pkgs.python315.override {
          packageOverrides = final: prev: let
            py3o.PYO3_USE_ABI3_FORWARD_COMPATIBILITY = "1";
          in
            {
              pydantic = prev.pydantic.overridePythonAttrs (_old: rec {
                version = "2.13.0b3";
                src = pkgs.fetchFromGitHub {
                  owner = "pydantic";
                  repo = "pydantic";
                  tag = "v${version}";
                  hash = "sha256-zxooO1fMqtD8Vy59odEcKBHaD6b7sSL4vScn0Z2+/Rs=";
                };
              });
              pydantic-core = prev."pydantic-core".overridePythonAttrs (old: rec {
                version = "2.45.0";
                src = pkgs.fetchPypi {
                  pname = "pydantic_core";
                  inherit version;
                  hash = "sha256-o/9lkhfcs9E0Qu00jhLhLtbIdnkRVKV13vH+qbtmfY4=";
                };
                cargoDeps = pkgs.rustPlatform.fetchCargoVendor {
                  inherit src version;
                  pname = old.pname;
                  hash = "sha256-OD2nw4tf5Xt75tfp5faaWz5BjEVsFSyLSqSeEXIZWl4=";
                };
              });
            }
            // (builtins.listToAttrs (map (name: {
                inherit name;
                value = prev.${name}.overridePythonAttrs (_old: py3o);
              }) [
                "python-bidi"
                "rpds-py"
              ]))
            // (builtins.listToAttrs (map (name: {
                inherit name;
                value = prev.${name}.overridePythonAttrs (_old: {doCheck = false;});
              }) [
                "et-xmlfile"
                "exceptiongroup"
                "parso"
                "pure-eval"
                "readme-renderer"
                "setproctitle"
                "time-machine"
                "tkinter"
                "toolz"
                "tornado"
              ]));
        };
      in {
        formatter = pkgs.alejandra;
        devShells.default = pkgs.mkShell {
          packages = with pkgs; [
            bazel_9
            gnfinder
            gnparser
            (python315.withPackages (ps:
              with ps; [
                pydantic
                pytest
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
