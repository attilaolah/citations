let
  bazel = import ./bazel.nix;
  python-docling = import ./python-docling.nix;
in {
  inherit bazel python-docling;

  default = final: prev:
    (bazel final prev)
    // (python-docling final prev);
}
