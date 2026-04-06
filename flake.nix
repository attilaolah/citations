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
              pydantic-core = prev."pydantic-core".overridePythonAttrs (_old:
                py3o
                // {
                  preBuild =
                    (_old.preBuild or "")
                    + ''
                      export PYO3_USE_ABI3_FORWARD_COMPATIBILITY=1
                    '';
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
