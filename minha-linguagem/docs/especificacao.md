# Especificação da linguagem — LocaScript

## 1. Para que serve

LocaScript é uma linguagem de marcação para interpolar variáveis, pluralizar
números e flexionar gênero/gramática em textos de jogos e software, tudo
resolvido em tempo de execução. Ela existe para que um único arquivo de
tradução sirva a várias variações linguísticas (gênero do personagem,
quantidade de itens) sem precisar de lógica extra no código do jogo.

## 2. Programa de exemplo completo, comentado linha a linha

```locascript
## Mensagem exibida quando um jogador causa dano em combate.
<color=yellow>{ $atacante_nome }</> causou { $dano } de dano!
{ $vitima_genero ->
    [fem] Ela perdeu
    [*]   Ele perdeu
} { $pocoes ->
    [one]  # poção de vida.
    [*]    # poções de vida.
}
```

- Linha 1 — comentário (`##`), ignorado pelo analisador; serve de nota para
  quem traduz.
- Linha 2 — abre uma tag de UI (`<color=yellow>`), interpola a variável
  `$atacante_nome`, fecha a tag (`</>`), e segue com texto literal
  (`causou`), outra interpolação (`$dano`), e mais texto literal.
- Linhas 3–6 — bloco de seleção contextual: consulta `$vitima_genero`; se for
  `fem` usa "Ela perdeu", senão (`*`, ramo padrão) usa "Ele perdeu".
- Linhas 6–9 — segundo bloco, agora de pluralização: consulta `$pocoes`; se a
  categoria CLDR for `one` usa singular, senão (`*`) usa plural, substituindo
  `#` pelo valor numérico formatado.

## 3. Tipos de dado

- **Variável de texto** (`$nome`, `$atacante_nome`): string simples injetada
  pelo sistema hospedeiro.
- **Variável numérica** (`$dano`, `$pocoes`): número inteiro ou real, usado
  tanto para exibição quanto para decidir a categoria plural.
- **Texto literal**: qualquer trecho de caractere fora dos símbolos
  reservados, mantido intacto no payload de exibição.
- **Categoria plural** (`zero`, `one`, `two`, `few`, `many`, `other`): valor
  derivado automaticamente de uma variável numérica segundo o padrão CLDR,
  não é digitado pelo autor do texto.

## 4. Comandos (construções da linguagem)

- **Interpolação** — `{ $var }`: insere o valor de uma variável.
- **Formatador** — `{ $var | formatador(args) }`: aplica uma transformação
  (ex: `moeda(BRL)`) sobre o valor antes de exibir.
- **Seleção contextual** — `{ $var -> [caso] ... [*] ... }`: escolhe um ramo
  de texto de acordo com o valor de `$var` (gênero, pessoa, categoria
  plural), com `[*]` como ramo obrigatório de fallback.
- **Tag de UI** — `<nome>texto</>` ou `<nome=valor>texto</>`: aplica
  estilização (cor, negrito) a um trecho de texto.
- **Escape** — `\{`, `\}`, `\$`, `\#`, `\\`: insere um símbolo reservado como
  caractere literal.

## 5. Operadores e precedência

Da resolução mais interna para a mais externa:

1. **Escape (`\`)** — resolvido primeiro, no próprio léxico; transforma um
   símbolo reservado em caractere literal antes de qualquer outra regra
   se aplicar.
2. **Prefixo de variável (`$`)** — liga o identificador seguinte ao valor
   injetado pelo sistema.
3. **Seleção (`->`)** — consome o valor da variável e decide qual ramo
   `[caso]`/`[*]` será avaliado; readequação da CLDR acontece aqui quando o
   valor é numérico.
4. **Pipe / formatador (`|`)** — aplicado por último, sobre o valor já
   resolvido (variável ou resultado da seleção), formatando a saída final.

## 6. Comentários

Uma linha iniciada por `##` é um comentário e é totalmente descartada pelo
analisador léxico. Escolhemos dois caracteres (`##`) e não um só porque um
único `#` já é o token `VALOR_NUMERICO`, usado dentro de blocos de
pluralização (`# moedas de ouro`). Ver `DIARIO.md`, entrada de 12/09, para o
motivo da mudança.

## 7. Três coisas que a linguagem deliberadamente não faz

1. **Não tem laços de repetição.** Cada arquivo LocaScript descreve uma
   mensagem, não um programa; repetição de itens fica a cargo do sistema
   hospedeiro, que chama o mesmo trecho várias vezes se precisar.
2. **Não faz aritmética entre variáveis.** Não existe `$a + $b`; cálculos
   ficam fora da linguagem, que só formata e seleciona texto.
3. **Não permite lógica booleana composta nas condições.** Uma seleção
   contextual só compara a variável a chaves de caso (`[masculino]`,
   `[one]`); não há `&&`, `||` ou comparações como `$dano > 10`.
