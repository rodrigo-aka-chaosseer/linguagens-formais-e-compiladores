parser grammar LocaScriptParser;

// Parser da LocaScript (E3). Usa os tokens do lexer LocaScript.g4.
options { tokenVocab = LocaScript; }

// Uma mensagem é uma sequência de itens até o fim do arquivo.
mensagem : item* EOF ;

// Item: texto literal (modo padrão: TEXTO; corpo de ramo: TEXTO_B),
// escape, '#' (valor numérico), interpolação, seleção ou tag de UI.
item
    : TEXTO
    | TEXTO_B
    | ESCAPE
    | VALOR_NUMERICO
    | interpolacao
    | selecao
    | tag
    ;

// { $nome }   ou   { $valor | moeda(BRL, 2) }
interpolacao
    : ABRE_BLOCO PREFIXO_VAR IDENT (PIPE formatador)* FECHA_BLOCO
    ;

formatador : IDENT (ABRE_PAREN argumentos? FECHA_PAREN)? ;
argumentos : argumento (VIRGULA argumento)* ;
argumento  : IDENT | NUMERO ;

// { $genero -> [fem] Ela [*] Ele }
selecao
    : ABRE_BLOCO PREFIXO_VAR IDENT OPERADOR_SELECAO ramo+ FECHA_BLOCO
    ;

ramo  : ABRE_CASO chave FECHA_CASO item* ;

chave
    : CASO_PADRAO
    | CLDR_ZERO | CLDR_ONE | CLDR_TWO | CLDR_FEW | CLDR_MANY | CLDR_OTHER
    | IDENT
    ;

// <color=yellow> ... </>
tag       : tagAbre item* tagFecha ;
tagAbre   : TAG_UI_ABRE TAG_IDENT (IGUAL valorTag)? TAG_UI_FECHA ;
valorTag  : TAG_IDENT | VALOR_HEX ;
tagFecha  : TAG_UI_ABRE BARRA TAG_IDENT? TAG_UI_FECHA ;
