final: prev: {
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
          ../patches/docling-parse-explicit-json-conversions.patch
        ];
      meta = old.meta // {broken = false;};
    });
  });
}
