#!/bin/bash
# full rebuild: project, schematic, board, autoroute + pours, checks, fab files
set -e
cd "$(dirname "$0")"
python3 gen_pro.py
python3 gen_sch.py
python3 gen_pcb.py
python3 route.py ${1:-100} 2>&1 | grep -E "stitching|routed|Auto-routing stage completed" || true
./check.sh
python3 fab.py
