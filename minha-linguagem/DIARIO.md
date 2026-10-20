# Diário do projeto — LocaScript

## 09/09
- Escolhido tema e escopo do projeto, elaboração inicial das especificações

## 11/09
- Gerados os primeiros arquivos do analisador lexico, gramática.

## 14/09
- Criado o repositório no Github, com todos os arquivos do projeto; README ajustado.

## 17/09
- Tentativas de resolver problemas da instalação do ANTLR4, tanto no Windows quanto no Pop!OS. No Pop!OS foi necessário criar um .venv com a ajuda do Copilot

## 14/10
- Adicionados arquivos para implementação do analisador sintático e seus testes

# 16/10
- Gramática atualizada com correções para garantir bom funcionamento do analisador lexico e portanto do sintático; .gitignore adicionado para não versionar pasta gerado/

# 17/10
- Adicionado parser.g4 e primeiros testes de sintaxe feitos
- Melhorada a visualização dos analisadores: o léxico agora exibe tokens em uma tabela, e o sintático mostra a árvore indentada.

# 20/10
- Pequenos ajustes na gramática do léxico, no README e na especificação; 
- Adição de testes para verificar se a linguagem segue a especificação atual