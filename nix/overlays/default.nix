let
  bazel = import ./bazel.nix;
in {
  inherit bazel;

  default = final: prev: bazel final prev;
}
