#!/bin/bash
# setup-steelbox.sh
# Run this after cloning your quetzal fork

set -e

echo "=== SteelBox Setup ==="

# Check if we're in the right directory
if [ ! -f "InitGui.py" ]; then
    echo "Error: Run this from the root of your quetzal fork"
    exit 1
fi

# Detect OS for sed compatibility
if [[ "$OSTYPE" == "darwin"* ]]; then
    echo "Detected macOS - using BSD sed syntax"
else
    echo "Detected Linux - using GNU sed syntax"
fi

echo "1. Renaming quetzal -> steelbox in Python files..."
find . -name "*.py" -type f | while read -r file; do
    if [[ "$OSTYPE" == "darwin"* ]]; then
        sed -i '' 's/quetzal/steelbox/g' "$file"
        sed -i '' 's/Quetzal/SteelBox/g' "$file"
    else
        sed -i 's/quetzal/steelbox/g' "$file"
        sed -i 's/Quetzal/SteelBox/g' "$file"
    fi
done

echo "2. Updating package.xml..."
if [[ "$OSTYPE" == "darwin"* ]]; then
    sed -i '' 's/quetzal/steelbox/g' package.xml
    sed -i '' 's/Quetzal/SteelBox/g' package.xml
else
    sed -i 's/quetzal/steelbox/g' package.xml
    sed -i 's/Quetzal/SteelBox/g' package.xml
fi

echo "3. Creating new directory structure..."
mkdir -p core joinery holes profiles/custom export ui/dialogs docs examples templates

echo "4. Setting up profiles directory..."
if [ -d "profiles/custom" ]; then
    echo "   profiles/custom/ ready for your tube profiles"
    echo "   See EXAMPLE_*.json for profile structure"
fi

echo "5. Moving docs into place..."
if [ -f "CLAUDE.md" ]; then
    echo "   CLAUDE.md already exists"
else
    echo "   Copy CLAUDE.md to this directory"
fi

echo "6. Creating __init__.py files..."
touch core/__init__.py
touch joinery/__init__.py
touch holes/__init__.py
touch profiles/__init__.py
touch export/__init__.py
touch ui/__init__.py

echo "=== Setup Complete ==="
echo ""
echo "Next steps:"
echo "  1. Copy CLAUDE.md and docs/*.md to this repo"
echo "  2. Update package.xml with your info (maintainer, description)"
echo "  3. Symlink to FreeCAD: ln -s \$(pwd) ~/.local/share/FreeCAD/Mod/SteelBox"
echo "  4. Start FreeCAD and verify SteelBox workbench appears"
echo "  5. Run: claude"
echo ""
