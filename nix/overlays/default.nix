let
  bazel = import ./bazel.nix;
  gnfinder = import ./gnfinder.nix;
in {
  inherit bazel;
  inherit gnfinder;

  default = final: prev:
    (bazel final prev)
    // (gnfinder final prev);
}
