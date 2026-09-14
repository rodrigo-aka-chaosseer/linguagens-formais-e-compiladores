lexer grammar LocaScript;

// ---- LEXER: MAIUSCULAS ----
// Gramática de lexer da LocaScript v1.0
// Linguagem de marcação para interpolação, pluralização (CLDR) e
// flexão de gênero/gramática em textos de jogos.
//
// Usa MODOS porque espaço em branco é significativo em texto literal,
// mas insensível dentro de expressões de controle "{ ... }" e de tags
// de UI "< ... >" (ver README, seção 1.2). Ver DIARIO.md 12/09.

// =====================================================================
// MODO PADRAO: texto literal solto (fora de blocos e tags)
// =====================================================================

// Comentários: linha iniciada por '##'. Escolhemos dois caracteres, e
// não um só, porque um único '#' já é o token VALOR_NUMERICO usado
// dentro de blocos de pluralização ("# moedas de ouro"). A regra de
// maior correspondência do ANTLR garante que "##..." vire COMENT.
COMENT : '##' ~[\r\n]* -> skip ;

ESCAPE : '\\' ('{' | '}' | '$' | '#' | '\\') ;

ABRE_BLOCO  : '{' -> pushMode(DENTRO_BLOCO) ;
TAG_UI_ABRE : '<' -> pushMode(DENTRO_TAG) ;

// Texto literal: qualquer sequência de caracteres que NÃO seja um dos
// símbolos reservados que abrem um modo de controle ('{', '<'), o
// escape ('\') ou o marcador de comentário ('#', que precisa de \# para
// virar texto). Espaço em branco aqui é mantido (não é ESPACO/skip).
TEXTO : ~[{<#\\]+ ;

// =====================================================================
// MODO DENTRO_BLOCO: dentro de "{ ... }" (interpolação/seleção)
// =====================================================================
mode DENTRO_BLOCO;

FECHA_BLOCO      : '}' -> popMode ;
PREFIXO_VAR      : '$' ;
OPERADOR_SELECAO : '->' ;
ABRE_CASO        : '[' ;
FECHA_CASO       : ']' ;
CASO_PADRAO      : '*' ;
PIPE             : '|' ;
VALOR_NUMERICO   : '#' ;

// Palavras-chave: categorias plurais do padrão Unicode CLDR, usadas
// como chave de caso dentro de uma seleção plural: { $qtd -> [one] ... }
CLDR_ZERO  : 'zero' ;
CLDR_ONE   : 'one' ;
CLDR_TWO   : 'two' ;
CLDR_FEW   : 'few' ;
CLDR_MANY  : 'many' ;
CLDR_OTHER : 'other' ;

IDENT  : [a-zA-Z_][a-zA-Z0-9_]* ;
NUMERO_MALFORMADO : [0-9]+ '.' ;
NUMERO : [0-9]+ ('.' [0-9]+)? ;

// Texto dos ramos de selecao. Fica depois das regras estruturais para que
// chaves, colchetes, '$' e '#' continuem sendo tokens de controle.
TEXTO_B : ~[{}\u005B\u005D#$@\\ \t\r\n]+ ;

ESPACO_B : [ \t\r\n]+ -> skip ;

// =====================================================================
// MODO DENTRO_TAG: dentro de "< ... >" (estilização de interface)
// =====================================================================
mode DENTRO_TAG;

TAG_UI_FECHA : '>' -> popMode ;
BARRA        : '/' ;
IGUAL        : '=' ;
VALOR_HEX    : '#' [0-9a-fA-F]+ ;

TAG_IDENT : [a-zA-Z_][a-zA-Z0-9_]* ;

ESPACO_T : [ \t\r\n]+ -> skip ;
