# Como rodar o playground LocaScript

Este documento explica como iniciar o servidor do playground localmente no Windows/PowerShell e no Linux. Os comandos devem ser executados a partir da pasta `minha-linguagem/` (a pasta que contém `requirements.txt`, `gerar.ps1` e `gerar.sh`).

O servidor oferece a interface em `http://127.0.0.1:5000`, a rota de saúde em `/saude` e as APIs `/analisar` e `/renderizar`. Para uso local, o Flask serve a aplicação. No Render, o Dockerfile inicia o Gunicorn e escuta na porta indicada pela variável `PORT`.

## Requisitos

- Python 3.10 ou mais recente para execução local.
- Acesso à internet na primeira instalação dos pacotes.
- Java/JRE para gerar os arquivos ANTLR a partir das gramáticas. O `antlr4-tools` pode baixar um JRE quando necessário; também é possível instalar Java previamente.
- No Linux, Bash para executar `gerar.sh`.

Os arquivos Python gerados pelo ANTLR ficam em `gerado/` e são ignorados pelo Git. Portanto, em um clone novo, gere-os antes de iniciar o servidor. Não é necessário executar o gerador novamente a cada início, a menos que as gramáticas tenham mudado ou que os arquivos gerados não estejam presentes.

## Windows com PowerShell

Abra o PowerShell na raiz do repositório e entre na pasta do projeto:

```powershell
cd minha-linguagem
```

Crie e ative um ambiente virtual. Se já existir `.venv/`, pule a criação:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Instale as dependências da aplicação e a ferramenta de geração ANTLR:

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install antlr4-tools==0.2.2
```

Gere o lexer e o parser. Na primeira execução, a ferramenta pode pedir para baixar um JRE; permita o download ou instale Java e tente de novo:

```powershell
.\gerar.ps1
```

Se o PowerShell bloquear a ativação do ambiente por causa da política de execução, não é obrigatório ativá-lo. Use o caminho completo do Python do ambiente nos comandos, por exemplo `\.venv\Scripts\python.exe -m pip install -r requirements.txt` e `\.venv\Scripts\python.exe src\servidor.py`. O script `gerar.ps1` procura `antlr4.exe` no diretório Scripts do Python encontrado no PATH; ative o ambiente antes de gerar para que ele use a ferramenta instalada nele.

Inicie o servidor:

```powershell
python src\servidor.py
```

Quando aparecer `Running on http://127.0.0.1:5000`, abra esse endereço no navegador. Para parar o servidor, volte ao terminal e pressione `Ctrl+C`.

Se estiver usando o ambiente virtual já criado neste projeto, os mesmos passos essenciais são:

```powershell
cd minha-linguagem
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m pip install antlr4-tools==0.2.2
.\.venv\Scripts\python.exe src\servidor.py
```

O último comando é o que foi usado nesta máquina. A geração não foi necessária nessa execução porque os arquivos em `gerado/` já estavam presentes.

## Linux

Instale Python, pip, suporte a ambientes virtuais, Bash e Java. Em Debian/Ubuntu, por exemplo:

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip default-jre-headless
```

Na raiz do repositório, entre no projeto, crie/ative um ambiente virtual e instale as dependências:

```bash
cd minha-linguagem
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install antlr4-tools==0.2.2
```

Gere os arquivos do lexer e parser:

```bash
bash gerar.sh
```

Inicie o servidor de desenvolvimento:

```bash
python src/servidor.py
```

Abra `http://127.0.0.1:5000`. Para encerrar, pressione `Ctrl+C`. Para voltar a executar depois, basta ativar `.venv/` e rodar `python src/servidor.py`; reinstalação e geração não são necessárias enquanto o ambiente e os arquivos gerados forem mantidos.

## Verificação

Com o servidor ativo, a rota de saúde deve retornar um JSON com `status` igual a `ok`:

```powershell
Invoke-RestMethod http://127.0.0.1:5000/saude
```

```bash
curl http://127.0.0.1:5000/saude
```

Também é possível conferir a interface abrindo `http://127.0.0.1:5000` no navegador. As requisições do playground são feitas para o mesmo servidor; não é necessário iniciar um frontend separado.

## Dependências

`requirements.txt` contém as dependências Python do projeto:

| Pacote | Uso |
| --- | --- |
| `antlr4-python3-runtime==4.13.2` | Runtime usado pelos arquivos Python gerados pelo ANTLR. A versão deve corresponder à versão da ferramenta que gerou o parser. |
| `Babel==2.11.0` | Regras de idioma, pluralização e formatação de números/valores na renderização. |
| `Flask==3.1.3` | Servidor HTTP local, rotas e entrega da página estática. |
| `gunicorn==27.0.1` | Servidor WSGI de produção usado pelo container/Render; não é necessário para iniciar com `python src/servidor.py`. |
| `pytest==7.4.0` | Execução dos testes automatizados. |
| `hypothesis` | Geração de casos de teste usados pela suíte. |

`antlr4-tools==0.2.2` é uma ferramenta adicional de desenvolvimento, instalada separadamente porque não está em `requirements.txt`. Ela fornece o comando `antlr4` usado por `gerar.ps1`/`gerar.sh`. Java/JRE é necessário para a geração, não para executar o servidor quando os módulos já foram gerados.

### O que foi instalado no ambiente desta execução

O playground foi iniciado no Windows com Python 3.14.0 do ambiente virtual `minha-linguagem/.venv`. O primeiro início mostrou `ModuleNotFoundError: No module named 'flask'`. Em seguida, foram instalados nesse ambiente Flask 3.1.3, `antlr4-python3-runtime` 4.13.2 e Babel 2.11.0, e o servidor iniciou corretamente. O ambiente já continha `antlr4-tools` 0.2.2 e suas dependências. Não foi necessário instalar pacotes globalmente.

## Observação sobre o servidor local

`python src/servidor.py` inicia o servidor de desenvolvimento Flask ligado a `127.0.0.1`, apropriado para uso na própria máquina. No Render, use o container definido em `Dockerfile`: ele gera o parser durante a construção da imagem e inicia Gunicorn em `0.0.0.0:$PORT`. Não use o servidor de desenvolvimento Flask como comando de produção.
