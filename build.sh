#!/usr/bin/env bash
# Build and optionally serve the CISOinaBox Jekyll site locally
#
# Usage:
#   ./build.sh              # Build the site only
#   ./build.sh serve        # Build and serve on port 4000 (default)
#   ./build.sh serve 4001   # Build and serve on custom port

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=== Building CISOinaBox Site ==="

# Step 1: Run the conversion script (cleans docs/ and regenerates)
echo ""
echo ">> Running conversion script..."
python3 convert_to_jekyll_improved.py

# Step 2: Remove any leftover duplicates that the converter might have missed
echo ""
echo ">> Checking for duplicates..."
declare -A seen_permalinks
dupes_found=0
for f in docs/*.markdown; do
    permalink=$(grep "^permalink:" "$f" | sed 's/permalink: *//' | tr -d '/')
    if [[ -n "${seen_permalinks[$permalink]}" ]]; then
        echo "   Removing duplicate: $f (conflicts with ${seen_permalinks[$permalink]})"
        # Keep the one that's NOT auto-generated (prefer hand-crafted files)
        if [[ "$f" == *ciso-resources* ]]; then
            rm "$f"
        elif [[ "${seen_permalinks[$permalink]}" == *ciso-resources* ]]; then
            rm "${seen_permalinks[$permalink]}"
            seen_permalinks[$permalink]="$f"
        else
            rm "$f"
        fi
        dupes_found=$((dupes_found + 1))
    else
        seen_permalinks[$permalink]="$f"
    fi
done
if [[ $dupes_found -eq 0 ]]; then
    echo "   No duplicates found"
fi

# Step 3: Rebuild navigation to match the final set of pages
echo ""
echo ">> Rebuilding navigation..."
python3 rebuild_navigation.py

echo ""
echo "=== Build Complete ==="
echo "   Pages: $(ls docs/*.markdown | wc -l)"
echo ""

# Step 4: Optionally serve the site
if [[ "$1" == "serve" ]]; then
    PORT="${2:-4000}"
    echo ">> Serving site on http://localhost:$PORT"
    echo "   Press Ctrl+C to stop"
    echo ""
    python3 -m http.server "$PORT" --directory _site
fi
