"""Ajusta o sys.path para os testes encontrarem o código e o parser gerado.

Ajuste os nomes das pastas conforme o repositório.
"""
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
for pasta in ("src", "gerado"):
    sys.path.insert(0, str(RAIZ / pasta))
