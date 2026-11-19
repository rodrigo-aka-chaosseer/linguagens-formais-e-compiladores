# Especificação da linguagem — LocaScript

## 1.1 Introdução

LocaScript é uma linguagem de marcação para interpolar variáveis, pluralizar
números e flexionar gênero/gramática em textos de jogos e software, tudo
resolvido em tempo de execução. Ela existe para que um único arquivo de
tradução sirva a várias variações linguísticas (gênero do personagem,
quantidade de itens) sem precisar de lógica extra no código do jogo.


### 1.2 Codificação e Texto Literal

* **Codificação de Entrada:** Todos os arquivos LocaScript **devem** ser estritamente codificados em **UTF-8**.
* **Payload de Texto:** Aceita qualquer ponto de código Unicode válido, garantindo suporte nativo a scripts globais (Latino, Cirílico, CJK, Árabe, Devanagari) e símbolos gráficos (Emojis).

### 1.3 Categorias de Caracteres no Analisador Léxico

| Categoria | Alfabeto / Intervalo Válido | Regras de Parsing |
| --- | --- | --- |
| **Identificadores** | `[a-zA-Z_][a-zA-Z0-9_]*` | Nomes de variáveis (ex: `$jogador`) e chaves de casos (ex: `[masculino]`). Não aceitam acentos ou espaços. |
| **Símbolos Reservados** | `{`, `}`, `$`, `->`, `[`, `]`, `\|`, `#`, `*`, `<`, `>`, `/`, `=` | Caracteres ASCII com função estrutural de controle. |
| **Texto Literal** | Qualquer caractere UTF-8 fora dos reservados. | Mantido intacto no payload de exibição. |
| **Espaços em Branco** | `\u0020` (Espaço), `\t` (Tab), `\n` (LF), `\r` (CR) | **Significativos** em texto literal; **insensíveis** em expressões de controle (`{ $var }` equivale a `{$var}`). |

### 1.4 Sequências de Escape

Para utilizar um símbolo reservado como caractere literal, precede-se o símbolo com a barra invertida `\`:

* `\{` e `\}` → Renderizam chaves literais sem abrir um bloco de código.
* `\$` e `\#` → Renderizam o cifrão e o sustenido literais.
* `\\` → Renderiza a barra invertida literal.



## 2. Tipos de dado

- **Variável de texto** (`$nome`, `$atacante_nome`): string simples injetada
  pelo sistema hospedeiro.
- **Variável numérica** (`$dano`, `$pocoes`): número inteiro ou real, usado
  tanto para exibição quanto para decidir a categoria plural.
- **Texto literal**: qualquer trecho de caractere fora dos símbolos
  reservados, mantido intacto no payload de exibição.
- **Categoria plural** (`zero`, `one`, `two`, `few`, `many`, `other`): ...
  O ramo padrão é sempre `[*]`; `[other]` é aceito como chave comum e não
  substitui o `[*]` obrigatório.

## 3. Comandos (construções da linguagem)

- **Interpolação** — `{ $var }`: insere o valor de uma variável.
- **Formatador** — `{ $var | formatador(args) }`: aplica uma transformação
  (ex: `moeda(BRL)`) sobre o valor antes de exibir.
- **Seleção contextual** — `{ $var -> [caso] ... [*] ... }`: escolhe um ramo
  de texto de acordo com o valor de `$var` (gênero, pessoa, categoria
  plural), com `[*]` como ramo obrigatório de fallback.
- **Tag de UI** — `<nome>texto</>` ou `<nome=valor>texto</>`, onde `valor` é
  um identificador (`yellow`) ou uma cor hexadecimal (`#FF0000`). `</>` fecha
  a tag mais recente; `</nome>` também é aceito.
- **Escape** — `\{`, `\}`, `\$`, `\#`, `\\`, `\<`; dentro de ramos de seleção
  também `\[` e `\]`: insere o símbolo como caractere literal.

## 4. Operadores e precedência

Dentro de `{ ... }` existem duas formas, e elas não se misturam:

- **Interpolação** `{ $var | f1 | f2(args) }`: o `|` encadeia formatadores,
  aplicados da esquerda para a direita; cada um recebe o resultado do anterior.
- **Seleção** `{ $var -> [caso] ... [*] ... }`: o `->` escolhe um ramo.
  Não aceita `|` depois da variável. Dentro de um ramo, `|` é texto literal.

Como as duas formas são exclusivas no mesmo bloco, não há ambiguidade entre
`|` e `->`. Para formatar um valor dentro de uma seleção, aninhe uma
interpolação no ramo: `{ $x -> [*] { $y | moeda(BRL) } }`.

Ordem de resolução (do que liga primeiro ao que liga por último):
1. Escape `\` — resolvido no léxico.
2. Prefixo `$` — liga o identificador à variável injetada.
3. `|` — encadeia formatadores sobre o valor da variável.
4. `->` — escolhe o ramo; o texto do ramo pode conter `#`, `{ }` e tags.

## 5. Comentários

`##` inicia um comentário que vai até o fim da linha e é descartado pelo
analisador léxico. Vale em texto fora de blocos `{ }`; dentro de blocos e de
ramos de seleção, `#` mantém seu significado próprio. A quebra de linha ao
final do comentário continua no texto. Para escrever `##` literal, use `\#\#`.

## 6. Três coisas que a linguagem deliberadamente não faz

1. **Não tem laços de repetição.** Cada arquivo LocaScript descreve uma
   mensagem, não um programa; repetição de itens fica a cargo do sistema
   hospedeiro, que chama o mesmo trecho várias vezes se precisar.
2. **Não faz aritmética entre variáveis.** Não existe `$a + $b`; cálculos
   ficam fora da linguagem, que só formata e seleciona texto.
3. **Não permite lógica booleana composta nas condições.** Uma seleção
   contextual só compara a variável a chaves de caso (`[masculino]`,
   `[one]`); não há `&&`, `||` ou comparações como `$dano > 10`.

---
## 7. Análise semântica

Depois que o analisador sintático aceita uma mensagem, a análise semântica
percorre a árvore (AST) e verifica o que a gramática não consegue expressar:
ramos de seleção, pareamento de tags, valores de tags, formatadores e tipos de
variáveis. Todo problema é um **erro** (a linguagem não tem avisos). Os erros
são coletados em uma única passada e reportados juntos, ordenados por posição,
no formato `linha L, coluna C: mensagem`.

### 7.1 Regras

| Regra | Descrição |
| --- | --- |
| **R1** | Toda seleção tem **exatamente um** ramo `[*]`, em qualquer posição. |
| **R2** | Toda tag é aberta com `<nome>` e fechada com `</nome>`; não existe `</>`. A tag aberta por último deve ser fechada primeiro, e o nome do fechamento deve ser o da tag aberta. |
| **R3** | O marcador `#` só pode aparecer em seleção de pluralização e se refere à seleção **mais interna** que o contém. |
| **R4** | Uma chave não pode se repetir na mesma seleção (`[one]` duas vezes). |
| **R5** | Uma seleção não mistura categorias plurais (`zero`, `one`, `two`, `few`, `many`, `other`) com chaves de gênero/papel (`masculino`, `fem`...). |
| **R6** | `[other]` é uma categoria comum e **não** substitui `[*]`, que continua obrigatório. |
| **R7** | Ramos vazios são aceitos: `{ $x -> [one] [*] texto }`. |
| **R8** | Uma seleção só com `[*]` é aceita. |
| **R9** | Os nomes de tag são livres, exceto `color`, que exige valor (ver 8.3). |
| **R11** | As chaves de gênero/papel são livres: o contrato é com o código do jogo. |
| **R13** | A existência de uma variável **não** é verificada: o conjunto de variáveis só é conhecido em tempo de execução. |
| **R14** | Uma variável tem um único tipo (número ou texto) em toda a mensagem (ver 8.2). |
| **R15** | Só existem os formatadores da tabela de 8.4, com a quantidade e o tipo de argumentos indicados. |
| **R16** | Em `{ $v \| f1 \| f2 }`, a saída de `f1` precisa ser do tipo que `f2` espera. |
| **R17** | As categorias plurais não são validadas por idioma (por exemplo, `few` é aceito mesmo em português). |

### 7.2 Tipos das variáveis

O tipo de uma variável é **inferido** pelos seus usos; a linguagem não tem
declarações.

| Uso | Tipo da variável |
| --- | --- |
| Seleção com categorias plurais (`[one]`, `[zero]`, `[other]`...) | número |
| Marcador `#` em uma seleção | número |
| Entrada de `moeda` ou `arredondar` | número |
| Seleção com chaves de gênero/papel (`[masculino]`, `[fem]`...) | texto |
| Entrada de `maiusculo` ou `minusculo` | texto |
| `{ $x }` sem formatador; seleção só com `[*]` | nenhum (neutro) |

Se a mesma variável for usada com os dois tipos, o erro aponta para o **segundo**
uso e cita a linha do primeiro:

```locascript
{ $x | moeda(BRL) }
{ $x | maiusculo }
```

```
linha 2, coluna 7: $x é usada como texto (formatador 'maiusculo'), mas na linha 1
foi usada como número (formatador 'moeda')
```

### 7.3 Tags de UI

- Abertura e fechamento são sempre explícitos e aninhados:
  `<b><i>x</i></b>` é válido; `<b><i>x</b></i>` é erro (um erro para cada
  fechamento fora de ordem).
- `color` é a única tag com valor verificado: o valor é obrigatório e tem a
  forma `#` seguido de exatamente 6 dígitos hexadecimais, maiúsculos ou
  minúsculos (`<color=#FF0000>`). Nomes de cor (`yellow`) e formas abreviadas
  (`#FFF`) são erros.
- As demais tags (`bold`, `italic`, qualquer outro nome) e seus valores não são
  verificados; quem interpreta a tag é o sistema hospedeiro.

### 7.4 Formatadores

| Formatador | Argumentos | Entrada | Saída |
| --- | --- | --- | --- |
| `moeda` | 1 ou 2: código de 3 letras maiúsculas (`BRL`) e, opcional, casas decimais (inteiro de 0 a 10) | número | texto |
| `arredondar` | 1: casas decimais (inteiro de 0 a 10) | número | número |
| `maiusculo` | nenhum | texto | texto |
| `minusculo` | nenhum | texto | texto |

Exemplos:

```locascript
{ $preco | arredondar(2) | moeda(BRL) }     ## válido: número -> número -> texto
{ $preco | moeda(BRL) | arredondar(2) }     ## erro: arredondar espera número, recebe texto
{ $nome | moeda(BRL) }                      ## erro se $nome é usada como texto em outro ponto
{ $preco | moeda(brl) }                     ## erro: o código deve ter 3 letras maiúsculas
```

### 7.5 Exemplos de erro

```locascript
{ $genero -> [fem] # [one] x }              ## R1 e R5: sem [*] e mistura de chaves
<color=yellow>{ $nome }</color>             ## R9: color exige #RRGGBB
<b><i>texto</b></i>                         ## R2: fechamento fora de ordem
```

## 8. Execução (renderização)

O interpretador recebe uma mensagem **já validada** (seções 7 e 8), um conjunto
de **valores** para as variáveis e um **idioma**, e produz o texto final. A
saída é uma lista de **trechos** (texto mais as tags de UI ativas naquele
ponto) e uma lista de **avisos**. Problemas de execução nunca interrompem a
renderização: viram avisos.

### 8.1 Entradas

- **Valores:** cada variável recebe um texto, um número ou nada. Valores
  booleanos e estruturas (listas, objetos) não são aceitos.
- **Idioma:** um código como `pt`, `pt-BR`, `pt_PT`, `en` ou `ru`. Ele decide as
  categorias plurais e o formato dos números. `pt` equivale a `pt_BR`. Um código
  desconhecido é um erro (a renderização não começa).
- Um valor numérico pode vir como número ou como texto numérico (`"5"`).
  O valor absoluto não pode passar de 10^15.

### 8.2 Seleção por pluralização

Para uma seleção com categorias plurais, o ramo é escolhido nesta ordem:

1. Se o valor é exatamente 0 e existe `[zero]`, usa `[zero]`.
2. Senão, calcula a categoria plural do valor no idioma (CLDR) e usa o ramo
   com essa chave, se existir.
3. Senão, usa `[*]`.

O passo 1 existe porque a categoria `zero` do CLDR só existe em alguns idiomas
(como o árabe); em português, por exemplo, o CLDR classifica o 0 como `one`
(`pt_BR`) ou `other` (`pt_PT`). Com a regra, `[zero]` funciona em qualquer
idioma. O passo 2 segue o CLDR: `1,5` e `1.0` podem cair em categorias
diferentes de `1`.

| Valor | `pt_BR` | `pt_PT` | `en` | `ru` |
| --- | --- | --- | --- | --- |
| 0 | one | other | other | many |
| 1 | one | one | one | one |
| 2 | other | other | other | few |
| 5 | other | other | other | many |
| 21 | other | other | other | one |

O marcador `#` é substituído pelo valor da seleção **mais interna** que o
contém, formatado segundo o idioma (`1.234,5` em `pt`, `1,234.5` em `en`). Sem
`arredondar`, números mostram até 3 casas decimais.

### 8.3 Seleção por gênero ou papel

O valor, que deve ser texto, é comparado com as chaves, **diferenciando
maiúsculas de minúsculas**: `[fem]` casa com `"fem"` e não com `"FEM"`. Sem
correspondência, usa `[*]`.

### 8.4 Formatadores

| Formatador | Resultado |
| --- | --- |
| `moeda(BRL)` | Valor com o símbolo e as casas da moeda, no formato do idioma: `R$ 1.234,50` em `pt`, `R$1,234.50` em `en`. `moeda(JPY)` não tem casas. |
| `moeda(BRL, n)` | Igual, com `n` casas decimais. |
| `arredondar(n)` | Arredonda para `n` casas, **metade para cima** (2,5 vira 3), e fixa as casas: `arredondar(2)` mostra `3,10` para 3,1. |
| `maiusculo`, `minusculo` | Converte o texto. |

Em uma cadeia, cada formatador recebe a saída do anterior.
Exemplo: `{ $v | arredondar(1) | moeda(BRL) }` com 1,26 produz `R$ 1,30`.

### 8.5 Tags de UI

As tags não aparecem no texto: cada trecho carrega a lista de tags ativas
(`color=#FF0000`, `b`...). Um ramo de seleção herda as tags abertas em volta
da seleção, e as tags abertas dentro de um ramo terminam com ele.

```locascript
<color=#FF0000>{ $nome }</color> venceu
```

Com `nome = "Aria"`, os trechos são `Aria` (com `color=#FF0000`) e ` venceu` (sem tags).

### 8.6 Avisos

| Situação | Resultado |
| --- | --- |
| Variável sem valor (ou `null`) | Marcador `{$nome}`, destacado como ausente, e aviso |
| Valor de tipo inválido (booleano, estrutura) | Igual ao caso anterior |
| Valor não numérico em seleção de pluralização | Usa `[*]` e avisa |
| Valor não numérico em `moeda` ou `arredondar` | Marcador `{$nome}` e aviso |
| Seleção de gênero sem valor, ou com valor que não é texto | Usa `[*]` e avisa |
| `#` sem valor numérico | `#` destacado como ausente e aviso |
| Número fora do limite (9.1) | Tratado como valor não numérico |

### 8.7 Fora do escopo

O interpretador não traduz entre idiomas: quem traduz é a pessoa que escreve
cada arquivo. Ele só resolve, para um conjunto de valores, qual texto de um
arquivo já escrito deve aparecer.
