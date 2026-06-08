#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

mkdir -p figures

echo "Checking Mermaid CLI..."
command -v mmdc
mmdc --version || true

echo "Rendering Mermaid diagrams..."
mmdc -p puppeteer-config.json -i diagrams/er_conceptual.mmd -o figures/er_conceptual.png -b white -w 2400 -H 1600
mmdc -p puppeteer-config.json -i diagrams/er_logical.mmd -o figures/er_logical.png -b white -w 2600 -H 1800

echo "Compiling LaTeX report..."
xelatex -interaction=nonstopmode main.tex
xelatex -interaction=nonstopmode main.tex

echo "Done. Output: report/main.pdf"
