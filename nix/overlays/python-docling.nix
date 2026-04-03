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
        docling = pyPrev.docling.overridePythonAttrs (old: let
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
          nativeBuildInputs =
            (old.nativeBuildInputs or [])
            ++ [pyFinal.pythonRelaxDepsHook];
          pythonRelaxDeps = (old.pythonRelaxDeps or []) ++ ["defusedxml" "typer"];
          propagatedBuildInputs =
            (old.propagatedBuildInputs or [])
            ++ [pyFinal.polyfactory];
        });

        docling-ibm-models = pyPrev."docling-ibm-models".overridePythonAttrs (_old: let
          version = "3.13.0";
          hash = "sha256-T8sVXG9s7jlhoRNexPRmCaiHPtQUAhDa9Z0Ri9i0zcc=";
        in {
          inherit version;
          src = final.fetchFromGitHub {
            inherit hash version;
            owner = "docling-project";
            repo = "docling-ibm-models";
            rev = "v${version}";
          };
          disabledTests = [
            "test_figure_classifier"
            "test_layoutpredictor"
            "test_tableformer_v2_batch_inference"
            "test_tableformer_v2_forward_pass"
            "test_tableformer_v2_image_encoding"
            "test_tableformer_v2_model_loading"
            "test_tableformer_v2_numpy_input"
            "test_tableformer_v2_predict"
            "test_tableformer_v2_tokenizer_loading"
            "test_tableformer_v2_unsupported_input"
            "test_tf_predictor"
          ];
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
