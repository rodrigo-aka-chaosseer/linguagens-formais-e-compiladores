# Diário do projeto — LocaScript

## 12/09
Definimos o alfabeto e os símbolos reservados a partir do README já escrito
para a linguagem. Ao tentar escolher o símbolo de comentário, percebemos que
`#` já era usado como marcador de posição para o valor numérico dentro de
blocos de pluralização (`# moedas de ouro`). Como o ANTLR resolve conflitos
por maior correspondência, optamos por `##` (dois caracteres) para
comentário — assim `##` sempre vence contra dois `#` isolados.

## 13/09
Ao escrever a regra de espaço em branco como um único `skip` global,
descobrimos que isso contradiz o próprio README: espaço é **significativo**
em texto literal, mas **insensível** dentro de blocos de controle. Corrigido
usando modos de lexer do ANTLR (`DENTRO_BLOCO`, `DENTRO_TAG`): fora deles o
espaço faz parte do token TEXTO; dentro deles, é descartado.

## 14/09
Testamos manualmente o exemplo de dano com gênero e pluralização (seção 4 do
README). Precisamos adicionar tokens específicos para as categorias
plurais do CLDR (`zero`, `one`, `two`, `few`, `many`, `other`) como
palavras-chave, já que o enunciado do trabalho exige que a gramática
reconheça pelo menos um conjunto de palavras-chave da linguagem.

## 15/09
Discutimos o que aconteceria com um arquivo em que uma tag `<...>` nunca é
fechada. O lexer sozinho não sabe balancear delimitadores (isso é trabalho
de análise sintática, fase E3), mas como usamos modos, dá para checar, ao
final da tokenização, se o lexer voltou ao modo padrão. Se não voltou, é
sinal de bloco/tag aberto e nunca fechado — adicionamos essa checagem em
`src/lexico.py`.
