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
        python315Patched = pkgs.python315.override {
          packageOverrides = final: prev: {
            exceptiongroup = prev.exceptiongroup.overridePythonAttrs (old: {
              disabledTests =
                (old.disabledTests or [])
                ++ [
                  "test_nameerror_suggestions_in_group[patched]"
                ];
            });
            "pydantic-core" = prev."pydantic-core".overridePythonAttrs (_old: {
              PYO3_USE_ABI3_FORWARD_COMPATIBILITY = "1";
            });
            "rpds-py" = prev."rpds-py".overridePythonAttrs (_old: {
              PYO3_USE_ABI3_FORWARD_COMPATIBILITY = "1";
            });
          };
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
            (python315Patched.withPackages (ps:
              with ps; [
                docling
                docling-parse
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
