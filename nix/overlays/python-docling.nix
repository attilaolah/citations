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
          hash = "sha256-rjRGBZDWqao32AGM4WTFubZ50cNqRWxKAOLojgR7uBk=";
        in {
          inherit version;
          src = final.fetchFromGitHub {
            inherit hash version;
            owner = "docling-project";
            repo = "docling";
            rev = "v${version}";
          };
        });

        docling-parse = pyPrev.docling-parse.overridePythonAttrs (old: let
          version = "5.7.0";
          hash = "sha256-HKhS6sIhUAr+VFo4jikQ1MMQpcLY6sS7RZaqcjaKvQc=";
        in {
          inherit version;
          src = final.fetchFromGitHub {
            inherit hash version;
            owner = "docling-project";
            repo = "docling-parse";
            rev = "v${version}";
          };
          buildInputs = old.buildInputs ++ [final.blend2d];
          patches =
            (old.patches or [])
            ++ [
              ../patches/docling-parse/pr-248.patch
            ];
          meta = old.meta // {broken = false;};
        });
      };
  };

  python314Packages = final.python314.pkgs;
}
