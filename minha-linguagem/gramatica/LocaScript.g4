lexer grammar LocaScript;

// ---- LEXER: MAIUSCULAS ----
// Gramática de lexer da LocaScript v1.1
// Linguagem de marcação para interpolação, pluralização (CLDR) e
// flexão de gênero/gramática em textos de jogos.
//
// Usa MODOS porque espaço em branco é significativo em texto literal,
// mas insensível dentro de expressões de controle "{ ... }" e de tags
// de UI "< ... >" .
//
// Pilha de modos (de fora para dentro):
//
//   DEFAULT_MODE   texto literal solto
//     '{'  -> DENTRO_BLOCO     cabeçalho: { $var | formatador(args) ...
//       '->' troca para DENTRO_SELECAO (mode, sem empilhar)
//     DENTRO_SELECAO           corpo da seleção: [caso] texto ... }
//       '['  -> DENTRO_CASO    chave do caso: [one] [fem] [*]
//       '{'  -> DENTRO_BLOCO   interpolação aninhada dentro de um ramo
//       '<'  -> DENTRO_TAG     tag de UI dentro de um ramo
//     '<'  -> DENTRO_TAG       tag de UI: <color=#FF0000> </>
//


// =====================================================================
// MODO PADRAO: texto literal solto (fora de blocos e tags)
// =====================================================================

// Comentários: '##' até o fim da linha (em qualquer ponto da linha).
// Dois caracteres, e não um só, porque um único '#' já é o token
// VALOR_NUMERICO usado dentro dos ramos de pluralização.
// Para escrever "##" literal, use "\#\#".
COMENT : '##' ~[\r\n]* -> skip ;

// Escapes: transformam um símbolo reservado em texto literal.
ESCAPE : '\\' ('{' | '}' | '$' | '#' | '\\' | '<') ;

ABRE_BLOCO  : '{' -> pushMode(DENTRO_BLOCO) ;
TAG_UI_ABRE : '<' -> pushMode(DENTRO_TAG) ;

// Texto literal: tudo que NÃO seja '{', '}', '<', '#' ou '\'.
// Espaço em branco é mantido.
// Novo: '}' saiu daqui; um '}' solto agora é erro léxico (antes passava
// em silêncio como texto). Para um '}' literal, use '\}'.
TEXTO : ~[{}<#\\]+ ;

// =====================================================================
// MODO DENTRO_BLOCO: cabeçalho de "{ ... }" (variável, formatador, '->')
// Espaço em branco é insensível aqui: { $var } == {$var}
// =====================================================================
mode DENTRO_BLOCO;

FECHA_BLOCO      : '}' -> popMode ;
PREFIXO_VAR      : '$' ;
PIPE             : '|' ;
ABRE_PAREN : '(' -> pushMode(DENTRO_ARGS) ;

// '->' troca o modo (não empilha): o '}' que fecha a seleção então
// desempilha o bloco inteiro de uma vez.
OPERADOR_SELECAO : '->' -> mode(DENTRO_SELECAO) ;



IDENT : [a-zA-Z_][a-zA-Z0-9_]* ;

// NUMERO exige dígito depois do ponto; "3." sozinho é malformado.
// Números só aparecem como argumento de formatador. Em texto de ramo,
// "Você tem 5." é texto comum e não gera mais erro.
NUMERO_MALFORMADO : [0-9]+ '.' ;
NUMERO            : [0-9]+ ('.' [0-9]+)? ;

ESPACO_B : [ \t\r\n]+ -> skip ;

// =====================================================================
// MODO DENTRO_ARGS: argumentos de formatador, "( ... )"
// =====================================================================
mode DENTRO_ARGS;

FECHA_PAREN : ')' -> popMode ;
VIRGULA     : ',' ;

IDENT_ARG             : [a-zA-Z_][a-zA-Z0-9_]* -> type(IDENT) ;
NUMERO_MALFORMADO_ARG : [0-9]+ '.' -> type(NUMERO_MALFORMADO) ;
NUMERO_ARG            : [0-9]+ ('.' [0-9]+)? -> type(NUMERO) ;

ESPACO_A : [ \t\r\n]+ -> skip ;


// =====================================================================
// MODO DENTRO_SELECAO: corpo de "{ $var -> [caso] texto ... }"
// Espaço em branco é SIGNIFICATIVO no texto dos ramos: vai para o canal
// HIDDEN (o parser ignora, mas o texto original pode ser reconstruído).
// =====================================================================
mode DENTRO_SELECAO;

ABRE_CASO : '[' -> pushMode(DENTRO_CASO) ;

// Fecha o bloco inteiro (corpo da seleção + cabeçalho que ficou abaixo).
// O token continua se chamando FECHA_BLOCO para o parser.
FECHA_BLOCO_SEL : '}' -> type(FECHA_BLOCO), popMode ;

// Interpolação e tag de UI aninhadas dentro de um ramo.
ABRE_BLOCO_SEL  : '{' -> type(ABRE_BLOCO), pushMode(DENTRO_BLOCO) ;
TAG_UI_ABRE_SEL : '<' -> type(TAG_UI_ABRE), pushMode(DENTRO_TAG) ;

// Escapes dentro de ramos (inclui '[' e ']' além dos do modo padrão).
ESCAPE_SEL : '\\' ('{' | '}' | '$' | '#' | '\\' | '<' | '[' | ']')
             -> type(ESCAPE) ;

// Marcador do valor numérico em pluralização: "# moedas".
VALOR_NUMERICO : '#' ;

// Texto do ramo: qualquer sequência fora dos símbolos de controle.
// '(' ')' ',' '.' etc. fazem parte do texto aqui ("O(a) jogador(a)").
TEXTO_B : ~[{}\u005B\u005D<#\\ \t\r\n]+ ;

ESPACO_SEL : [ \t\r\n]+ -> channel(HIDDEN) ;

// =====================================================================
// MODO DENTRO_CASO: chave de um caso, "[ ... ]"
// =====================================================================
mode DENTRO_CASO;

FECHA_CASO  : ']' -> popMode ;
CASO_PADRAO : '*' ;

// Palavras-chave: categorias plurais do padrão Unicode CLDR.
// Só são palavras-chave aqui; "one" como nome de variável ($one) ou
// como palavra solta de um ramo continua sendo identificador/texto.
CLDR_ZERO  : 'zero' ;
CLDR_ONE   : 'one' ;
CLDR_TWO   : 'two' ;
CLDR_FEW   : 'few' ;
CLDR_MANY  : 'many' ;
CLDR_OTHER : 'other' ;

// Chaves de gênero/papel: [masculino] [fem]
IDENT_CASO : [a-zA-Z_][a-zA-Z0-9_]* -> type(IDENT) ;

ESPACO_C : [ \t\r\n]+ -> skip ;

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

//