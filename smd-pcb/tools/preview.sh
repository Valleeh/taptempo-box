#!/bin/bash
# render board preview PNG: preview.sh out.png [layers]
K=$(cd "$(dirname "$0")/../kicad" && pwd)
L=${2:-F.Cu,B.Cu,F.Silkscreen,F.Courtyard,Edge.Cuts,User.Drawings,F.Fab}
T=$(mktemp -d)
kicad-cli pcb export svg --mode-single -l "$L" --fit-page-to-board --exclude-drawing-sheet -o "$T/b.svg" "$K/taptempo-smd.kicad_pcb" >/dev/null 2>&1
rsvg-convert -w ${3:-1400} -b white "$T/b.svg" -o "$1"; rm -rf "$T"
