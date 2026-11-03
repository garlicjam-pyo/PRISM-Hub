#!/bin/sh
# PRISM-Hub 졸업작품 논문 빌드(XeLaTeX, 2단 학회 양식). 결과: build/paper.pdf
cd "$(dirname "$0")"
latexmk -xelatex -interaction=nonstopmode -halt-on-error -outdir=build paper.tex
