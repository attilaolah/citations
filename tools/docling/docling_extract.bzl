def docling_models_tar(name, out, all_models = False):
    all_models_flag = "--all" if all_models else ""
    native.genrule(
        name = name,
        tools = ["@docling//:docling-tools"],
        outs = [out],
        cmd = """
set -euo pipefail
tmp_dir="$(@D)/tmp_models"
rm -rf "$$tmp_dir"
mkdir -p "$$tmp_dir/out" "$$tmp_dir/home" "$$tmp_dir/cache/huggingface"
export HOME="$$tmp_dir/home"
export XDG_CACHE_HOME="$$tmp_dir/cache"
export HF_HOME="$$tmp_dir/cache/huggingface"

$(location @docling//:docling-tools) models download --output-dir "$$tmp_dir/out" --quiet {all_models_flag}
tar -C "$$tmp_dir/out" -cf "$@" .
""".format(all_models_flag = all_models_flag),
        message = "Downloading docling model artifacts",
    )
