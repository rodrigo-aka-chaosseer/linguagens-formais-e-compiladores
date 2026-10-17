#!/usr/bin/env bash
set -e
export ANTLR4_TOOLS_ANTLR_VERSION=4.13.2
cd "$(dirname "$0")/gramatica"
antlr4 -Dlanguage=Python3 -visitor -o ../gerado LocaScript.g4
antlr4 -Dlanguage=Python3 -visitor -lib ../gerado -o ../gerado LocaScriptParser.g4