#!/usr/bin/env bash
set -euo pipefail

VERSION=${1:?Usage: ./release.sh <version>  e.g. ./release.sh 1.0.0}
REPO="verwilst/hass-polytropic-heatpump"
MANIFEST="custom_components/polytropic_heatpump/manifest.json"

# ── Checks ────────────────────────────────────────────────────────────────────

if ! command -v jq &>/dev/null; then
  echo "Error: jq is required (pacman -S jq)" && exit 1
fi

if ! command -v zip &>/dev/null; then
  echo "Error: zip is required (pacman -S zip)" && exit 1
fi

if ! command -v python3 &>/dev/null; then
  echo "Error: python3 is required (pacman -S python)" && exit 1
fi

if ! command -v curl &>/dev/null; then
  echo "Error: curl is required (pacman -S curl)" && exit 1
fi

if [[ -z "${GITHUB_TOKEN:-}" ]]; then
  echo "Error: GITHUB_TOKEN env var not set"
  echo "  export GITHUB_TOKEN=<your token>"
  exit 1
fi

if ! git diff --quiet || ! git diff --cached --quiet; then
  echo "Error: uncommitted changes present, please commit first"
  exit 1
fi

if git tag | grep -q "^v${VERSION}$"; then
  echo "Error: tag v${VERSION} already exists"
  exit 1
fi

# ── Bump manifest.json ────────────────────────────────────────────────────────

echo "→ Bumping manifest.json to ${VERSION}..."
python3 -c "
import json
with open('${MANIFEST}') as f:
    m = json.load(f)
m['version'] = '${VERSION}'
with open('${MANIFEST}', 'w') as f:
    json.dump(m, f, indent=2)
    f.write('\n')
"

git add "${MANIFEST}"
if git diff --cached --quiet; then
  echo "  (manifest already at ${VERSION}, skipping commit)"
else
  git commit -m "chore: bump version to ${VERSION}"
fi

# ── Tag & push ────────────────────────────────────────────────────────────────

echo "→ Tagging v${VERSION} and pushing..."
git tag "v${VERSION}"
git push origin main
git push origin "v${VERSION}"

# ── Build ZIP ─────────────────────────────────────────────────────────────────

ZIPFILE="/tmp/polytropic_heatpump_${VERSION}.zip"
echo "→ Building release ZIP..."
(cd custom_components && zip -qr "${ZIPFILE}" polytropic_heatpump/)

# ── Create GitHub release ─────────────────────────────────────────────────────

echo "→ Creating release on GitHub..."
RESPONSE=$(curl -s -X POST \
  -H "Authorization: Bearer ${GITHUB_TOKEN}" \
  -H "Content-Type: application/json" \
  "https://api.github.com/repos/${REPO}/releases" \
  -d "{
    \"tag_name\": \"v${VERSION}\",
    \"name\": \"v${VERSION}\",
    \"draft\": false,
    \"prerelease\": false
  }")

RELEASE_ID=$(echo "${RESPONSE}" | jq -r '.id')
UPLOAD_URL=$(echo "${RESPONSE}" | jq -r '.upload_url' | sed 's/{?name,label}//')

if [[ -z "${RELEASE_ID}" || "${RELEASE_ID}" == "null" ]]; then
  echo "Error: failed to create release"
  echo "${RESPONSE}" | jq .
  exit 1
fi

# ── Upload ZIP asset ──────────────────────────────────────────────────────────

echo "→ Uploading ZIP asset..."
curl -s -X POST \
  -H "Authorization: Bearer ${GITHUB_TOKEN}" \
  -H "Content-Type: application/zip" \
  "${UPLOAD_URL}?name=polytropic_heatpump.zip" \
  --data-binary "@${ZIPFILE}" \
  | jq -r '.browser_download_url'

rm "${ZIPFILE}"

echo ""
echo "✓ Released v${VERSION}: https://github.com/${REPO}/releases/tag/v${VERSION}"
