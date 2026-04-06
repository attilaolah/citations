final: prev: {
  python = prev.python314.withPackages (ps:
    with ps; [
      pydantic
      pytest
    ]);
}
