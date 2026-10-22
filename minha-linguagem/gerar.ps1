$ErrorActionPreference = "Stop"
$env:ANTLR4_TOOLS_ANTLR_VERSION = "4.13.2"

$pythonScripts = & python -c "import sysconfig; print(sysconfig.get_path('scripts'))"
if ($LASTEXITCODE -ne 0) {
    throw "Nao foi possivel localizar o diretorio Scripts do Python. Verifique se o Python esta instalado e no PATH."
}

$antlr = Join-Path $pythonScripts.Trim() "antlr4.exe"
if (-not (Test-Path $antlr)) {
    throw "antlr4.exe nao encontrado em '$pythonScripts'. Instale com: python -m pip install antlr4-tools"
}

$grammarDirectory = Join-Path $PSScriptRoot "gramatica"
$outputDirectory = Join-Path $PSScriptRoot "gerado"
Push-Location $grammarDirectory
try {
    & $antlr -Dlanguage=Python3 -visitor -o $outputDirectory LocaScript.g4
    if ($LASTEXITCODE -ne 0) {
        throw "Falha ao gerar o lexer ANTLR."
    }

    & $antlr -Dlanguage=Python3 -visitor -lib $outputDirectory -o $outputDirectory LocaScriptParser.g4
    if ($LASTEXITCODE -ne 0) {
        throw "Falha ao gerar o parser ANTLR."
    }
}
finally {
    Pop-Location
}