let
  bazel = import ./bazel.nix;
  pythonDocling = import ./python-docling.nix;
in {
  inherit bazel pythonDocling;

  default = final: prev:
    (bazel final prev)
    // (pythonDocling final prev);
}
