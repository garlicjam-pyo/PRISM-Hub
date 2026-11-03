#!/bin/sh
# PRISM-Hub 최종 보고서 빌드(XeLaTeX). 결과: build/main.pdf
cd "$(dirname "$0")"
latexmk -xelatex -interaction=nonstopmode -halt-on-error -outdir=build main.tex
