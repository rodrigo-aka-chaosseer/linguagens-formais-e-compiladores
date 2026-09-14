#!/usr/bin/env bash
set -e
antlr4 -Dlanguage=Python3 -visitor -o gerado gramatica/LocaScript.g4
