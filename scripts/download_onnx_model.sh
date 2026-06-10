#!/bin/bash
# 下载 all-MiniLM-L6-v2 的 ONNX 导出版本
# Xenova 项目维护，与 sentence-transformers 输出一致（mean pooling + L2 normalize）
#
# 用法：
#   bash scripts/download_onnx_model.sh [target_dir]
#
# 默认下载到 ../models/all-MiniLM-L6-v2/（相对于脚本目录）

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET_DIR="${1:-$SCRIPT_DIR/../models/all-MiniLM-L6-v2}"
TARGET_DIR="$(cd "$(dirname "$TARGET_DIR")" && pwd)/$(basename "$TARGET_DIR")"

# Xenova 提供即用型 ONNX（与 sentence-transformers 等价）
HF_REPO="Xenova/all-MiniLM-L6-v2"
FILES=(
  "onnx/model.onnx"
  "tokenizer.json"
  "tokenizer_config.json"
  "config.json"
  "special_tokens_map.json"
)

echo "=== Downloading $HF_REPO ONNX model ==="
echo "Target: $TARGET_DIR"
mkdir -p "$TARGET_DIR"

if command -v huggingface-cli >/dev/null 2>&1; then
  for f in "${FILES[@]}"; do
    huggingface-cli download "$HF_REPO" "$f" --local-dir "$TARGET_DIR" --quiet
    echo "  ✓ $f"
  done
else
  # 回退：直接用 wget/curl
  BASE_URL="https://huggingface.co/$HF_REPO/resolve/main"
  for f in "${FILES[@]}"; do
    DEST="$TARGET_DIR/$f"
    mkdir -p "$(dirname "$DEST")"
    URL="$BASE_URL/$f"
    echo "  ↓ $f"
    curl -fL --retry 3 -o "$DEST" "$URL"
  done
fi

echo ""
echo "=== Done ==="
ls -lh "$TARGET_DIR/onnx/model.onnx" "$TARGET_DIR/tokenizer.json"
echo ""
echo "Total size:"
du -sh "$TARGET_DIR"
