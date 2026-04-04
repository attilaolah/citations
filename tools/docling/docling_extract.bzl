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

def docling_pdf_to_markdown(name, src, out, models_tar = None):
    srcs = [src]
    artifacts_cmd = ""
    artifacts_flag = ""
    if models_tar != None:
        srcs.append(models_tar)
        artifacts_cmd = """
mkdir -p "$$tmp_dir/artifacts"
tar -C "$$tmp_dir/artifacts" -xf "$(location {models_tar})"
""".format(models_tar = models_tar)
        artifacts_flag = '--artifacts-path "$$tmp_dir/artifacts"'

    native.genrule(
        name = name,
        srcs = srcs,
        tools = ["@docling//:docling"],
        outs = [out],
        cmd = """
set -euo pipefail
tmp_dir="$(@D)/tmp"
rm -rf "$$tmp_dir"
mkdir -p "$$tmp_dir/out"
mkdir -p "$$tmp_dir/home" "$$tmp_dir/cache/huggingface"
export HOME="$$tmp_dir/home"
export XDG_CACHE_HOME="$$tmp_dir/cache"
export HF_HOME="$$tmp_dir/cache/huggingface"

{artifacts_cmd}

input="$(location {src})"
device="$${{DOCLING_DEVICE:-auto}}"
$(location @docling//:docling) --from pdf --to md --image-export-mode placeholder --pipeline standard --pdf-backend docling_parse --no-ocr --device "$$device" {artifacts_flag} --output "$$tmp_dir/out" "$$input"

base_name="$${{input##*/}}"
stem="$${{base_name%.*}}"
md_out="$$tmp_dir/out/$$stem.md"

if [ ! -f "$$md_out" ]; then
  echo "Expected markdown output not found: $$md_out" >&2
  find "$$tmp_dir/out" -maxdepth 2 -type f >&2 || true
  exit 1
fi

cp "$$md_out" "$@"
""".format(
            artifacts_cmd = artifacts_cmd,
            artifacts_flag = artifacts_flag,
            src = src,
        ),
        message = "Extracting Markdown from %s" % src,
    )

def ppt_to_pptx(name, src, out):
    native.genrule(
        name = name,
        srcs = [src],
        tools = ["@libreoffice//:soffice"],
        outs = [out],
        cmd = """
set -euo pipefail
tmp_dir="$(@D)/tmp_pptx"
rm -rf "$$tmp_dir"
mkdir -p "$$tmp_dir/in" "$$tmp_dir/out" "$$tmp_dir/home"
export HOME="$$tmp_dir/home"

input="$(location {src})"
local_ppt="$$tmp_dir/in/input.ppt"
cp "$$input" "$$local_ppt"
$(location @libreoffice//:soffice) --headless --nologo --nolockcheck --nodefault --nofirststartwizard --convert-to pptx --outdir "$$tmp_dir/out" "$$local_ppt"

cp "$$tmp_dir/out/input.pptx" "$@"
""".format(src = src),
        message = "Converting PPT to PPTX for %s" % src,
    )

def docling_pptx_to_markdown(name, src, out, models_tar = None):
    srcs = [src]
    artifacts_cmd = ""
    artifacts_flag = ""
    if models_tar != None:
        srcs.append(models_tar)
        artifacts_cmd = """
mkdir -p "$$tmp_dir/artifacts"
tar -C "$$tmp_dir/artifacts" -xf "$(location {models_tar})"
""".format(models_tar = models_tar)
        artifacts_flag = '--artifacts-path "$$tmp_dir/artifacts"'

    native.genrule(
        name = name,
        srcs = srcs,
        tools = [
            "@docling//:docling",
        ],
        outs = [out],
        cmd = """
set -euo pipefail
tmp_dir="$(@D)/tmp"
rm -rf "$$tmp_dir"
mkdir -p "$$tmp_dir/out" "$$tmp_dir/home"
mkdir -p "$$tmp_dir/cache/huggingface"
export HOME="$$tmp_dir/home"
export XDG_CACHE_HOME="$$tmp_dir/cache"
export HF_HOME="$$tmp_dir/cache/huggingface"

{artifacts_cmd}

input="$(location {src})"
device="$${{DOCLING_DEVICE:-auto}}"
$(location @docling//:docling) --from pptx --to md --image-export-mode placeholder --device "$$device" {artifacts_flag} --output "$$tmp_dir/out" "$$input"

base_name="$${{input##*/}}"
stem="$${{base_name%.*}}"
md_out="$$tmp_dir/out/$$stem.md"

if [ ! -f "$$md_out" ]; then
  echo "Expected markdown output not found: $$md_out" >&2
  find "$$tmp_dir/out" -maxdepth 2 -type f >&2 || true
  exit 1
fi

cp "$$md_out" "$@"
""".format(
            artifacts_cmd = artifacts_cmd,
            artifacts_flag = artifacts_flag,
            src = src,
        ),
        message = "Extracting Markdown from %s" % src,
    )
