#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
output_dir="${1:-${repo_root}/_site}"

if [[ -z "${output_dir}" || "${output_dir}" == "/" || "${output_dir}" == "${repo_root}" ]]; then
  echo "Refusing unsafe Pages output directory: ${output_dir}" >&2
  exit 2
fi

rm -rf "${output_dir}"
mkdir -p "${output_dir}"

public_files=(
  index.html
  app.js
  calculator.js
  page-agent-bridge.js
  styles.css
  seresarte-web-lab/README.md
  seresarte-web-lab/app.js
  seresarte-web-lab/data/projects.json
  seresarte-web-lab/docs/deployment.md
  seresarte-web-lab/docs/editorial-governance.md
  seresarte-web-lab/docs/roadmap.md
  seresarte-web-lab/index.html
  seresarte-web-lab/styles.css
  sites/renova-press-seresarte-portal/index.html
  web3-starter/docs/IPFS_ARWEAVE.md
  web3-starter/docs/IPHONE_MINT_GUIDE.md
  web3-starter/docs/LICENSE_NOTES.md
  web3-starter/docs/MANIFIESTO_WEB3.md
  web3-starter/docs/QR_ACCESS.md
  web3-starter/metadata/renova-genesis/0001.json
  web3-starter/metadata/renova-genesis/manifest.demo.json
  web3-starter/site/index.html
  web3-starter/site/styles.css
)

for asset in "${public_files[@]}"; do
  source_path="${repo_root}/${asset}"
  if [[ ! -f "${source_path}" || -L "${source_path}" ]]; then
    echo "Missing or unsafe public asset: ${asset}" >&2
    exit 1
  fi
  mkdir -p "${output_dir}/$(dirname "${asset}")"
  install -m 0644 "${source_path}" "${output_dir}/${asset}"
done

if find "${output_dir}" -type l -print -quit | grep -q .; then
  echo "Pages output must not contain symbolic links." >&2
  exit 1
fi

for forbidden in .git .env config memory node_modules contracts; do
  if find "${output_dir}" -name "${forbidden}" -print -quit | grep -q .; then
    echo "Forbidden path leaked into Pages output: ${forbidden}" >&2
    exit 1
  fi
done

echo "Built allowlisted Pages site at ${output_dir}"
