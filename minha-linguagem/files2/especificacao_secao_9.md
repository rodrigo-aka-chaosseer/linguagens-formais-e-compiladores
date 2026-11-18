## 9. Execução (renderização)

O interpretador recebe uma mensagem **já validada** (seções 7 e 8), um conjunto
de **valores** para as variáveis e um **idioma**, e produz o texto final. A
saída é uma lista de **trechos** (texto mais as tags de UI ativas naquele
ponto) e uma lista de **avisos**. Problemas de execução nunca interrompem a
renderização: viram avisos.

### 9.1 Entradas

- **Valores:** cada variável recebe um texto, um número ou nada. Valores
  booleanos e estruturas (listas, objetos) não são aceitos.
- **Idioma:** um código como `pt`, `pt-BR`, `pt_PT`, `en` ou `ru`. Ele decide as
  categorias plurais e o formato dos números. `pt` equivale a `pt_BR`. Um código
  desconhecido é um erro (a renderização não começa).
- Um valor numérico pode vir como número ou como texto numérico (`"5"`).
  O valor absoluto não pode passar de 10^15.

### 9.2 Seleção por pluralização

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

### 9.3 Seleção por gênero ou papel

O valor, que deve ser texto, é comparado com as chaves, **diferenciando
maiúsculas de minúsculas**: `[fem]` casa com `"fem"` e não com `"FEM"`. Sem
correspondência, usa `[*]`.

### 9.4 Formatadores

| Formatador | Resultado |
| --- | --- |
| `moeda(BRL)` | Valor com o símbolo e as casas da moeda, no formato do idioma: `R$ 1.234,50` em `pt`, `R$1,234.50` em `en`. `moeda(JPY)` não tem casas. |
| `moeda(BRL, n)` | Igual, com `n` casas decimais. |
| `arredondar(n)` | Arredonda para `n` casas, **metade para cima** (2,5 vira 3), e fixa as casas: `arredondar(2)` mostra `3,10` para 3,1. |
| `maiusculo`, `minusculo` | Converte o texto. |

Em uma cadeia, cada formatador recebe a saída do anterior.
Exemplo: `{ $v | arredondar(1) | moeda(BRL) }` com 1,26 produz `R$ 1,30`.

### 9.5 Tags de UI

As tags não aparecem no texto: cada trecho carrega a lista de tags ativas
(`color=#FF0000`, `b`...). Um ramo de seleção herda as tags abertas em volta
da seleção, e as tags abertas dentro de um ramo terminam com ele.

```locascript
<color=#FF0000>{ $nome }</color> venceu
```

Com `nome = "Aria"`, os trechos são `Aria` (com `color=#FF0000`) e ` venceu` (sem tags).

### 9.6 Avisos

| Situação | Resultado |
| --- | --- |
| Variável sem valor (ou `null`) | Marcador `{$nome}`, destacado como ausente, e aviso |
| Valor de tipo inválido (booleano, estrutura) | Igual ao caso anterior |
| Valor não numérico em seleção de pluralização | Usa `[*]` e avisa |
| Valor não numérico em `moeda` ou `arredondar` | Marcador `{$nome}` e aviso |
| Seleção de gênero sem valor, ou com valor que não é texto | Usa `[*]` e avisa |
| `#` sem valor numérico | `#` destacado como ausente e aviso |
| Número fora do limite (9.1) | Tratado como valor não numérico |

### 9.7 Fora do escopo

O interpretador não traduz entre idiomas: quem traduz é a pessoa que escreve
cada arquivo. Ele só resolve, para um conjunto de valores, qual texto de um
arquivo já escrito deve aparecer.
