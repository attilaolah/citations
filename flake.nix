{
  description = "Citations repository flake";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
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

      perSystem = {pkgs, ...}: let
        bazel = pkgs.bazel_8.overrideAttrs (oldAttrs: {
          version = "9.0.1";
          src = pkgs.fetchzip {
            url = "https://github.com/bazelbuild/bazel/releases/download/9.0.1/bazel-9.0.1-dist.zip";
            hash = "sha256-tdrSgtIXi8Xd03BgxLRWhw1bB1Zhuo0E2pWMCskBDG8=";
            stripRoot = false;
          };
          buildPhase = builtins.replaceStrings ["8.6.0"] ["9.0.1"] oldAttrs.buildPhase;
          installPhase = builtins.replaceStrings ["8.6.0"] ["9.0.1"] oldAttrs.installPhase;
          postFixup = builtins.replaceStrings ["8.6.0"] ["9.0.1"] oldAttrs.postFixup;
          patches =
            builtins.filter (
              p: let
                s = toString p;
              in
                !(
                  pkgs.lib.hasInfix "deps_patches.patch" s
                  || pkgs.lib.hasInfix "add_file.patch" s
                  || pkgs.lib.hasInfix "env_bash.patch" s
                  || pkgs.lib.hasInfix "gen_completion.patch" s
                  || pkgs.lib.hasInfix "md5sum.patch" s
                )
            )
            oldAttrs.patches
            ++ [
              (pkgs.replaceVars ./patches/rules_python.add_file.patch {
                usrBinEnv = "${pkgs.coreutils}/bin/env";
              })
              (pkgs.replaceVars ./patches/rules_java.add_file.patch {
                defaultBash = "${pkgs.bash}/bin/bash";
              })
              (pkgs.replaceVars ./patches/jvm_module_options_bash.patch {
                defaultBash = "${pkgs.bash}/bin/bash";
              })
              (pkgs.replaceVars ./patches/md5_shebang.patch {
                usrBinEnv = "${pkgs.coreutils}/bin/env";
              })
              ./patches/bazel-9-deps_patches.patch
            ];
        });
      in {
        formatter = pkgs.alejandra;

        devShells.default = pkgs.mkShell {
          packages = with pkgs; [
            alejandra
            bazel
          ];
        };
      };
    };
}
