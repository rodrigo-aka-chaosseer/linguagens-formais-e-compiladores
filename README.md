# Especificação Formal da Linguagem LocaScript v1.0

A **LocaScript** é uma linguagem de marcação leve projetada para interpolação de dados, pluralização e condicionalidade gramatical em tempo de execução para jogos e softwares.

---

## 1. Conjunto de Caracteres e Alfabeto Válido

### 1.1 Codificação e Texto Literal

* **Codificação de Entrada:** Todos os arquivos LocaScript **devem** ser estritamente codificados em **UTF-8**.
* **Payload de Texto:** Aceita qualquer ponto de código Unicode válido, garantindo suporte nativo a scripts globais (Latino, Cirílico, CJK, Árabe, Devanagari) e símbolos gráficos (Emojis).

### 1.2 Categorias de Caracteres no Analisador Léxico

| Categoria | Alfabeto / Intervalo Válido | Regras de Parsing |
| --- | --- | --- |
| **Identificadores** | `[a-zA-Z_][a-zA-Z0-9_]*` | Nomes de variáveis (ex: `$jogador`) e chaves de casos (ex: `[masculino]`). Não aceitam acentos ou espaços. |
| **Símbolos Reservados** | `{`, `}`, `$`, `->`, `[`, `]`, `\|`, `#`, `*`, `<`, `>`, `/`, `=` | Caracteres ASCII com função estrutural de controle. |
| **Texto Literal** | Qualquer caractere UTF-8 fora dos reservados. | Mantido intacto no payload de exibição. |
| **Espaços em Branco** | `\u0020` (Espaço), `\t` (Tab), `\n` (LF), `\r` (CR) | **Significativos** em texto literal; **insensíveis** em expressões de controle (`{ $var }` equivale a `{$var}`). |

### 1.3 Sequências de Escape

Para utilizar um símbolo reservado como caractere literal, precede-se o símbolo com a barra invertida `\`:

* `\{` e `\}` → Renderizam chaves literais sem abrir um bloco de código.
* `\$` e `\#` → Renderizam o cifrão e o sustenido literais.
* `\\` → Renderiza a barra invertida literal.

---

## 2. Sintaxe e Operadores

### 2.1 Interpolação Simples e Formatadores

* **Variáveis:** Declaradas com o prefixo `$` dentro de chaves: `{ $nome_variavel }`.
* **Formatadores de Tipo:** Invocados via operador pipe `|`: `{ $valor | moeda(BRL) }`.

### 2.2 Condicionais e Seleção Contextual

Gerencia flexões de gênero, papéis ou estado gramatical usando o operador `->`. O caractere `*` define o ramo padrão (*fallback*).

```locascript
{ $genero ->
    [masculino] O jogador
    [feminino]  A jogadora
    [*]         O(a) jogador(a)
} { $nome } subiu de nível!

```

### 2.3 Pluralização Gramatical

Processa valores numéricos baseando-se nas categorias do padrão Unicode CLDR (`zero`, `one`, `few`, `other`). O símbolo `#` é o marcador de posição para o valor numérico formatado.

```locascript
Você encontrou { $quantidade ->
    [zero]  nenhuma moeda.
    [one]   1 moeda de ouro.
    [*]     # moedas de ouro.
}

```

---

## 3. Tabela de Tokens da Gramática

| Símbolo | Nome do Token | Função no Parser |
| --- | --- | --- |
| `{` / `}` | `ABRE_BLOCO` / `FECHA_BLOCO` | Delimita expressões processadas pela AST. |
| `$` | `PREFIXO_VAR` | Identifica uma variável injetada pelo sistema. |
| `->` | `OPERADOR_SELECAO` | Inicia uma estrutura de decisão condicional. |
| `[` / `]` | `ABRE_CASO` / `FECHA_CASO` | Delimita a chave de correspondência do seletor. |
| `*` | `CASO_PADRAO` | Marca o ramo de *fallback* obrigatório na análise semântica. |
| `#` | `VALOR_NUMERICO` | Substituído dinamicamente pelo número no contexto plural. |
| `<` / `>` | `TAG_UI_ABRE` / `TAG_UI_FECHA` | Delimita estilização de interface (ex: `<bold>`, `<color=#FF0000>`). |

---

## 4. Exemplo Completo

```locascript
<color=yellow>{ $atacante_nome }</> causou { $dano } de dano!
{ $vitima_genero ->
    [fem] Ela perdeu
    [*]   Ele perdeu
} { $pocoes ->
    [one]  # poção de vida.
    [*]    # poções de vida.
}

```
## 5.Dicionário de contexto
Contexto utilizado: jogos de RPG *high-fantasy*.

**Magia, Entidades e Artefatos**

* **Arcano:** A energia mágica primordial que permeia a realidade e pode ser manipulada por conjuradores.
* **Grimório:** Tomo ou livro de feitiços contendo rituais, encantamentos e fórmulas mágicas.
* **Filactério:** Receptáculo mágico onde um *Lich* preserva sua alma para garantir a imortalidade.
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
* **Tank:** Classe focada em absorver dano de grande porte e manter o *aggro* dos inimigos longe dos aliados.
* **DPS (Dano por Segundo):** Papel focado em causar a maior quantidade de dano possível no menor tempo.
* **Healer (Curandeiro):** Personagem focado em suporte, purificação de maldições e restauração de pontos de vida (HP).
* **Buff / Debuff:** Efeito temporário que melhora (*buff*) ou enfraquece (*debuff*) os atributos de um personagem.
* **Cooldown (Tempo de Recarga):** Intervalo de tempo necessário até que uma habilidade possa ser usada novamente.
* **Loot (Saque):** Recompensas, itens e moedas obtidos ao derrotar inimigos ou abrir baús.

**Atributos de Personagem**

* **Força (FOR):** Poder físico brutal, bônus de dano corpo a corpo e capacidade de carga.
* **Destreza (DES):** Agilidade, precisão com armas à distância, reflexos e taxa de esquiva.
* **Inteligência (INT):** Capacidade de raciocínio e potência para magias de origem arcana.
* **Sabedoria (SAB):** Intuição, percepção do ambiente e eficácia para magias de origem divina ou de cura.
* **Carisma (CAR):** Força de personalidade, persuasão e facilidade de negociação com NPCs.
