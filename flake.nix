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
      flake.overlays.default = final: prev: {
        bazel = prev.bazel_8.overrideAttrs (
          old: let
            inherit (builtins) any filter listToAttrs replaceStrings throw;
            inherit (prev) replaceVars;
            inherit (final.lib) getExe getExe' hasInfix;

            version = "9.0.1";
            hash = "sha256-tdrSgtIXi8Xd03BgxLRWhw1bB1Zhuo0E2pWMCskBDG8=";
          in
            {
              inherit version;
              # Bazel ships a self-extracting wrapper archive in bin/.bazel-*-wrapped.
              # The default strip step in fixupPhase corrupts that embedded zip.
              dontStrip = true;
              src = prev.fetchzip {
                inherit hash;
                url = "https://github.com/bazelbuild/bazel/releases/download/${version}/bazel-${version}-dist.zip";
                stripRoot = false;
              };
              patches =
                filter (p:
                  !(any (needle: hasInfix needle (toString p)) (map (n: "${n}.patch") [
                    "add_file"
                    "deps_patches"
                    "env_bash"
                    "gen_completion"
                    "md5sum"
                  ])))
                old.patches
                ++ map (p: replaceVars p {env = getExe' prev.coreutils "env";}) [
                  ./patches/rules_python.add_file.patch
                  ./patches/md5_shebang.patch
                ]
                ++ map (p: replaceVars p {bash = getExe prev.bash;}) [
                  ./patches/rules_java.add_file.patch
                  ./patches/jvm_module_options_bash.patch
                ]
                ++ [
                  ./patches/bazel-9-deps_patches.patch
                ];
            }
            // (listToAttrs (map (name: {
              inherit name;
              value =
                if hasInfix old.version old.${name}
                then replaceStrings [old.version] [version] old.${name}
                else throw "bazel override: ${name} no longer contains ${old.version}; drop manual version rewrite";
            }) ["buildPhase" "installPhase" "postFixup"]))
        );

        python314Packages = prev.python314Packages.overrideScope (_pyFinal: pyPrev: {
          docling = pyPrev.docling.overridePythonAttrs (_old: rec {
            version = "2.84.0";
            src = final.fetchPypi {
              inherit version;
              pname = "docling";
              hash = "sha256-AHsLrTwOxF3JGvYIPL4fCpPd7xaGME9GbooWih+x3Ms=";
            };
          });
          "docling-parse" = pyPrev."docling-parse".overridePythonAttrs (old: rec {
            version = "5.7.0";
            src = final.fetchPypi {
              inherit version;
              pname = "docling_parse";
              hash = "sha256-x3IJwuCTyl+CZpUr0TuVrvCd+jjmmV7PhVlxgZeGyT0=";
            };
            buildInputs = old.buildInputs ++ [final.blend2d];
            patches =
              (old.patches or [])
              ++ [
                ./patches/docling-parse-explicit-json-conversions.patch
              ];
            meta = old.meta // {broken = false;};
          });
        });
      };

      perSystem = {system, ...}: let
        pkgs = import inputs.nixpkgs {
          inherit system;
          overlays = [self.overlays.default];
        };
      in {
        formatter = pkgs.alejandra;
        devShells.default = pkgs.mkShell {
          packages = with pkgs; [
            alejandra
            bazel
            buildifier
            prettier
            (python314.withPackages (ps: [
              ps.docling
              ps."docling-parse"
            ]))
          ];
        };
      };
    };
}
