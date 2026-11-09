#!/bin/sh
# 요약보고서 빌드(XeLaTeX)
cd "$(dirname "$0")" && latexmk -xelatex -interaction=nonstopmode main.tex
