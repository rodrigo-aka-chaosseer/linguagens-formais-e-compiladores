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

## Dicionário de contexto
Contexto utilizado: jogos de RPG *high-fantasy*.

**Magia, Entidades e Artefatos**

* **Arcano:** Qualidade mística, pouco compreendida pela sociedade; mágico, misterioso.
* **Grimório:** Tomo ou livro de feitiços contendo rituais, encantamentos e fórmulas mágicas.
* **Lich:** Necromante poderoso que renunciou à vida mortal por meio de artes das trevas para se tornar um morto-vivo consciente.
* **Mana / Éter:** O recurso ou substância vital consumida durante a conjuração de habilidades mágicas.
* **Runa:** Símbolo místico esculpido em armas, armaduras ou monumentos para conceder propriedades mágicas ou elementais.
* **Mitril (Mithril):** Metal mítico extremamente leve e reluzente, mas incomparavelmente mais resistente que o aço comum.

**Locais e Organizações**

* **Masmorra (Dungeon):** Complexo subterrâneo, cripta ou ruína infestada por monstros, armadilhas e tesouros.
* **Santuário:** Local sagrado canalizador de bênçãos, curas ou pactos com divindades e patronos.
* **Guilda:** Associação de aventureiros ou artesãos que distribui missões (*quests*), recursos e contratos.

**Mecânicas de Combate e Papéis**

* **Aggro (Ameaça):** Nível de hostilidade que faz um monstro focar seus ataques em um jogador específico.
* **Tank (Tanque):** Classe focada em absorver dano de grande porte e manter o *aggro* dos inimigos longe dos aliados.
* **DPS (Dano por Segundo):** Papel focado em causar a maior quantidade de dano possível no menor tempo.
* **Healer (Curandeiro):** Personagem focado em suporte, purificação de maldições e restauração de pontos de vida (HP).
* **Buff / Debuff:** Efeito temporário que melhora (*buff*) ou enfraquece (*debuff*) os atributos de um personagem.
* **Cooldown (Recarga):** Intervalo de tempo necessário até que uma habilidade possa ser usada novamente.
* **Loot (Saque):** Recompensas, itens e moedas obtidos ao derrotar inimigos ou abrir baús.

**Atributos de Personagem**

* **Força (FOR):** Poder físico brutal, bônus de dano corpo a corpo e capacidade de carga.
* **Destreza (DES):** Agilidade, precisão com armas à distância, reflexos e taxa de esquiva.
* **Inteligência (INT):** Capacidade de raciocínio e potência para magias de origem arcana.
* **Sabedoria (SAB):** Intuição, percepção do ambiente e eficácia para magias de origem divina ou de cura.
* **Carisma (CAR):** Força de personalidade, persuasão e facilidade de negociação com NPCs.
