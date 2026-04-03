final: prev: let
  oldPackageOverrides =
    if prev.python314 ? packageOverrides
    then prev.python314.packageOverrides
    else (_: _: {});
in {
  python314 = prev.python314.override {
    packageOverrides = pyFinal: pyPrev:
      (oldPackageOverrides pyFinal pyPrev)
      // {
        docling = pyPrev.docling.overridePythonAttrs (_old: let
          version = "2.84.0";
          hash = "sha256-AHsLrTwOxF3JGvYIPL4fCpPd7xaGME9GbooWih+x3Ms=";
        in {
          inherit version;
          src = final.fetchPypi {
            inherit hash version;
            pname = "docling";
          };
        });

        "docling-parse" = pyPrev."docling-parse".overridePythonAttrs (old: let
          version = "5.7.0";
          hash = "sha256-x3IJwuCTyl+CZpUr0TuVrvCd+jjmmV7PhVlxgZeGyT0=";
        in {
          inherit version;
          src = final.fetchPypi {
            inherit hash version;
            pname = "docling_parse";
          };
          buildInputs = old.buildInputs ++ [final.blend2d];
          patches =
            (old.patches or [])
            ++ [
              ../patches/docling-parse/explicit-json-conversions.patch
            ];
          meta = old.meta // {broken = false;};
        });
      };
  };

  python314Packages = final.python314.pkgs;
}
