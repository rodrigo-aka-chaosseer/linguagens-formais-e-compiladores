## 8. Análise semântica

Depois que o analisador sintático aceita uma mensagem, a análise semântica
percorre a árvore (AST) e verifica o que a gramática não consegue expressar:
ramos de seleção, pareamento de tags, valores de tags, formatadores e tipos de
variáveis. Todo problema é um **erro** (a linguagem não tem avisos). Os erros
são coletados em uma única passada e reportados juntos, ordenados por posição,
no formato `linha L, coluna C: mensagem`.

### 8.1 Regras

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

### 8.2 Tipos das variáveis

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

### 8.3 Tags de UI

- Abertura e fechamento são sempre explícitos e aninhados:
  `<b><i>x</i></b>` é válido; `<b><i>x</b></i>` é erro (um erro para cada
  fechamento fora de ordem).
- `color` é a única tag com valor verificado: o valor é obrigatório e tem a
  forma `#` seguido de exatamente 6 dígitos hexadecimais, maiúsculos ou
  minúsculos (`<color=#FF0000>`). Nomes de cor (`yellow`) e formas abreviadas
  (`#FFF`) são erros.
- As demais tags (`bold`, `italic`, qualquer outro nome) e seus valores não são
  verificados; quem interpreta a tag é o sistema hospedeiro.

### 8.4 Formatadores

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

### 8.5 Exemplos de erro

```locascript
{ $genero -> [fem] # [one] x }              ## R1 e R5: sem [*] e mistura de chaves
<color=yellow>{ $nome }</color>             ## R9: color exige #RRGGBB
<b><i>texto</b></i>                         ## R2: fechamento fora de ordem
```

### 8.6 O que a análise semântica não verifica

- Se as variáveis existem ou têm o valor esperado em tempo de execução (R13).
- Se o idioma de destino usa as categorias plurais escritas (R17).
- O conteúdo e a ortografia do texto literal.
