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

Requer Python 3 e Java (o ANTLR baixa o Java automaticamente na primeira
execução, se necessário).

```bash
pip install antlr4-tools antlr4-python3-runtime

# gera o lexer a partir da gramática (pasta gerado/, ignorada pelo Git)
bash gerar.sh

# roda o analisador léxico sobre um exemplo
python src/lexico.py exemplos/ola.loca
```

Versão do ANTLR usada neste projeto: **4.13.2**.

## Em que fase o projeto está

**E2 — especificação da linguagem e analisador léxico.** O lexer reconhece
identificadores, números, texto literal, palavras-chave (categorias plurais
do CLDR), operadores/símbolos e comentários, e localiza erros léxicos com
linha e coluna. As próximas fases (E3 — analisador sintático, E4 — análise
semântica) ainda não foram implementadas.

## Como rodar os testes

Não há suíte automatizada nesta fase; a validação é manual, rodando o
analisador sobre os exemplos válidos e inválidos:

```bash
# devem tokenizar sem erro
python src/lexico.py exemplos/ola.loca
python src/lexico.py exemplos/dano.loca
python src/lexico.py exemplos/pluralizacao.loca

# devem reportar erro léxico com linha/coluna
python src/lexico.py exemplos/invalidos/caractere_invalido.loca
python src/lexico.py exemplos/invalidos/numero_malformado.loca
python src/lexico.py exemplos/invalidos/tag_sem_fechar.loca
```
