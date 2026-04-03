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
        bazel = pkgs.bazel_8.overrideAttrs (
          old: let
            inherit (builtins) any filter listToAttrs replaceStrings throw;
            inherit (pkgs) replaceVars;
            inherit (pkgs.lib) getExe getExe' hasInfix;

            version = "9.0.1";
            hash = "sha256-tdrSgtIXi8Xd03BgxLRWhw1bB1Zhuo0E2pWMCskBDG8=";
          in
            {
              inherit version;
              # Bazel ships a self-extracting wrapper archive in bin/.bazel-*-wrapped.
              # The default strip step in fixupPhase corrupts that embedded zip.
              dontStrip = true;
              src = pkgs.fetchzip {
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
                ++ map (p: replaceVars p {env = getExe' pkgs.coreutils "env";}) [
                  ./patches/rules_python.add_file.patch
                  ./patches/md5_shebang.patch
                ]
                ++ map (p: replaceVars p {bash = getExe pkgs.bash;}) [
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
      in {
        formatter = pkgs.alejandra;

        devShells.default = pkgs.mkShell {
          packages = with pkgs; [
            alejandra
            bazel
            buildifier
          ];
        };
      };
    };
}
