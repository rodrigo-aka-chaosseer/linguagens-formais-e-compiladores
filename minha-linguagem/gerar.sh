#!/usr/bin/env bash
set -e
cd "$(dirname "$0")/gramatica"
antlr4 -Dlanguage=Python3 -visitor -o ../gerado LocaScript.g4
