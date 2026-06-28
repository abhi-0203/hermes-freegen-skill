#!/bin/bash
# FreeGen Plugin — One-line Installer for Hermes Agent
# Usage: bash install.sh
#
# What it does:
#   1. Creates ~/.hermes/plugins/freegen/ directory
#   2. Copies plugin.yaml and __init__.py into it
#   3. Checks if image_gen config block exists, prompts to add if missing
#   4. Verifies with hermes plugins list

set -euo pipefail

HERMES_DIR="${HOME}/.hermes"
PLUGIN_DIR="${HERMES_DIR}/plugins/freegen"
SKILL_DIR="$(cd "$(dirname "$0")/.." && pwd)"

echo "🎨 FreeGen Image Gen — Installer"
echo "================================="

# Step 1: Create plugin directory
echo "📁 Creating plugin directory..."
mkdir -p "${PLUGIN_DIR}"

# Step 2: Copy files
echo "📋 Copying plugin files..."
cp "${SKILL_DIR}/scripts/__init__.py" "${PLUGIN_DIR}/__init__.py"
cp "${SKILL_DIR}/templates/plugin.yaml" "${PLUGIN_DIR}/plugin.yaml"
echo "   ✅ ${PLUGIN_DIR}/__init__.py"
echo "   ✅ ${PLUGIN_DIR}/plugin.yaml"

# Step 3: Check config
echo ""
echo "⚙️  Checking config..."
CONFIG="${HERMES_DIR}/config.yaml"

if [ ! -f "${CONFIG}" ]; then
    echo "   ⚠️  No config.yaml found at ${CONFIG}"
    echo "   Creating minimal config with freegen enabled..."
    mkdir -p "${HERMES_DIR}"
    cat > "${CONFIG}" << 'EOF'
image_gen:
  provider: freegen
  model: zimage
  use_gateway: false

plugins:
  enabled:
    - freegen
EOF
    echo "   ✅ Config created"
else
    # Check if image_gen block exists
    if grep -q "^image_gen:" "${CONFIG}"; then
        echo "   ✅ image_gen block already exists"
    else
        echo "   ⚠️  image_gen block missing — appending..."
        cat >> "${CONFIG}" << 'EOF'

image_gen:
  provider: freegen
  model: zimage
  use_gateway: false
EOF
        echo "   ✅ image_gen block added"
    fi

    # Check if freegen is in plugins.enabled
    if grep -q "freegen" "${CONFIG}"; then
        echo "   ✅ freegen already in plugins.enabled"
    else
        echo "   ⚠️  freegen not in plugins.enabled — you may need to add it manually"
        echo "   Add to config.yaml:"
        echo "     plugins:"
        echo "       enabled:"
        echo "         - freegen"
    fi
fi

# Step 4: Verify
echo ""
echo "🔍 Verifying installation..."
if [ -f "${PLUGIN_DIR}/__init__.py" ] && [ -f "${PLUGIN_DIR}/plugin.yaml" ]; then
    echo "   ✅ Plugin files in place"
    echo ""
    echo "🎉 Installation complete!"
    echo ""
    echo "Next steps:"
    echo "  1. Run: hermes plugins list    (verify freegen shows as enabled)"
    echo "  2. Test: /gen a corgi astronaut in space"
    echo "  3. Or ask your agent to generate an image"
    echo ""
    echo "Note: Portrait (9:16) is broken upstream. Use square or landscape."
else
    echo "   ❌ Plugin files missing — installation failed"
    exit 1
fi