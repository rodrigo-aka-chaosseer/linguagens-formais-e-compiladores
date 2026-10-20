# minha-linguagem — LocaScript


LocaScript é uma linguagem de marcação para interpolar variáveis, pluralizar
números e flexionar gênero/gramática em textos de jogos, resolvida em tempo
de execução. Exemplo:


```locascript
Voce encontrou { $quantidade ->
    [zero]  nenhuma moeda.
    [one]   1 moeda de ouro.
    [*]     # moedas de ouro.
}
```


A especificação completa está em [`docs/especificacao.md`](docs/especificacao.md).


## Como instalar e rodar


Requer Python 3.10 ou mais recente. O pacote `antlr4-tools` baixa um JRE
compatível na primeira execução do comando `antlr4`; não é necessário instalar
Java manualmente quando esse download automático for permitido. Execute os
comandos a partir da raiz deste diretório (`minha-linguagem/`).


### Windows (PowerShell)


```powershell
python -m pip install antlr4-tools antlr4-python3-runtime


# usa a versão do ANTLR especificada neste projeto
$env:ANTLR4_TOOLS_ANTLR_VERSION = "4.13.2"


# gera o lexer sem depender de o diretório Scripts estar no PATH
$antlr = Join-Path (python -c "import sysconfig; print(sysconfig.get_path('scripts'))") "antlr4.exe"
Push-Location gramatica
& $antlr -Dlanguage=Python3 -visitor -o ..\gerado LocaScript.g4
& $antlr -Dlanguage=Python3 -visitor -lib ..\gerado -o ..\gerado LocaScriptParser.g4
Pop-Location


# roda os analisadores léxico e sintático sobre exemplos
python src/lexico.py exemplos/ola.loca
python src/sintatico.py exemplos/dano.loca
```

O analisador léxico mostra os tokens em uma tabela com linha, coluna, tipo e
texto reconhecido. Caracteres especiais, como quebras de linha, aparecem
escapados; as colunas são contadas a partir de zero.
O analisador sintático exibe a árvore de regras e tokens com indentação; cada
folha mostra o texto reconhecido e sua posição no arquivo.


Na primeira execução, o `antlr4-tools` pode solicitar a instalação automática
de um JRE. Responda `yes` quando aparecer essa pergunta. A gramática é um lexer
ANTLR puro; a segunda gramática gera `gerado/LocaScriptParser.py`, que depende
dos tokens criados pelo lexer.


### Linux e macOS


```bash
python3 -m pip install antlr4-tools antlr4-python3-runtime


# gera o lexer e o parser a partir das gramáticas (pasta gerado/, ignorada pelo Git)
bash gerar.sh


# roda o analisador léxico sobre um exemplo
python3 src/lexico.py exemplos/ola.loca
```


No Git Bash do Windows, use preferencialmente os comandos da seção
**Windows (PowerShell)**. O script `gerar.sh` só funciona se o executável
`antlr4` estiver disponível no `PATH` do Git Bash; no PowerShell, use o comando
explícito mostrado acima.


Versão do ANTLR usada neste projeto: **4.13.2**.


## Em que fase o projeto está


**E3 — analisador sintático.** O lexer reconhece identificadores, números,
texto literal, palavras-chave (categorias plurais do CLDR), operadores/símbolos
e comentários, e localiza erros léxicos com linha e coluna. A gramática do
parser e o script `src/sintatico.py` já analisam mensagens, interpolações,
seleções e tags; a análise semântica (E4) ainda não foi implementada.


## Como rodar os testes


Não há suíte automatizada nesta fase; a validação é manual, rodando os
analisadores sobre os exemplos válidos e inválidos. Execute os comandos a
partir de `minha-linguagem/`.


```bash
# análise léxica: estes exemplos devem ser aceitos
python src/lexico.py exemplos/ola.loca
python src/lexico.py exemplos/dano.loca
python src/lexico.py exemplos/pluralizacao.loca


# análise léxica: estes exemplos devem reportar erro com linha/coluna
python src/lexico.py exemplos/invalidos/caractere_invalido.loca
python src/lexico.py exemplos/invalidos/numero_malformado.loca
python src/lexico.py exemplos/invalidos/tag_sem_fechar.loca


# análise sintática: devem aceitar e imprimir a árvore indentada
python src/sintatico.py exemplos/ola.loca
python src/sintatico.py exemplos/dano.loca
python src/sintatico.py exemplos/pluralizacao.loca


# análise sintática: devem reportar erro e terminar com código diferente de zero
python src/sintatico.py exemplos/invalidos/caractere_invalido.loca
python src/sintatico.py exemplos/invalidos/numero_malformado.loca
python src/sintatico.py exemplos/invalidos/tag_sem_fechar.loca
```

