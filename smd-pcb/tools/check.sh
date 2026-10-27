#!/bin/bash
# run ERC + DRC (with schematic parity) and summarise; reports go to ../kicad/
K=$(cd "$(dirname "$0")/../kicad" && pwd)
kicad-cli sch erc --severity-all -o "$K/erc.rpt" "$K/taptempo-smd.kicad_sch" 2>/dev/null | grep -i "violations"
kicad-cli pcb drc --schematic-parity --severity-all -o "$K/drc.rpt" "$K/taptempo-smd.kicad_pcb" 2>/dev/null | grep -i "found"
grep -E "^\[" "$K/drc.rpt" | sed 's/(.*//' | sort | uniq -c | sort -rn
