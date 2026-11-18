#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"

# NixOS does not expose the C++ runtime to pip's manylinux wheels by default.
if [[ -d /run/current-system/sw/share/nix-ld/lib ]]; then
  export LD_LIBRARY_PATH="/run/current-system/sw/share/nix-ld/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
fi
if [[ ! -x .venv/bin/python ]]; then
  printf '%s\n' 'Chưa có .venv. Xem README.md để cài môi trường Python.' >&2
  exit 1
fi
if [[ $# -gt 0 ]]; then
  exec .venv/bin/python "$@"
fi
exec .venv/bin/python -m streamlit run app.py --server.address 127.0.0.1