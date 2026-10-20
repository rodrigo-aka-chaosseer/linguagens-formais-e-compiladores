"""Testes baseados em propriedades (Hypothesis) para o parser."""
from hypothesis import HealthCheck, given, settings, strategies as st

from api_parser import ErroSintatico, parse
from ast_nos import Mensagem, No, TextoLiteral

CONFIG = settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow],
)

RESERVADOS = "{}<#\\"  # fora de blocos, o léxico rejeita ou trata estes

# Fragmentos da linguagem: chegam mais fundo no parser que texto aleatório.
FRAGMENTOS = [
    "{", "}", "[", "]", "<", ">", "$", "#", "*", "|", "(", ")", ",", "=", "/",
    "\\", "->", " ", "\n", "x", "one", "fem", "BRL", "3", "3.", "1.5", "##",
    "\\{", "\\#", "</>", "<b>", "é", "日本",
]
fonte_estruturada = st.lists(st.sampled_from(FRAGMENTOS), max_size=25).map("".join)


def todos_os_nos(no: No):
    yield no
    for filho in no.filhos():
        yield from todos_os_nos(filho)


# 1. Nunca quebra: ou devolve AST, ou ErroSintatico.
@CONFIG
@given(st.text(max_size=200))
def test_texto_qualquer_nao_quebra(fonte):
    try:
        parse(fonte)
    except ErroSintatico:
        pass


@CONFIG
@given(fonte_estruturada)
def test_fragmentos_nao_quebram(fonte):
    try:
        parse(fonte)
    except ErroSintatico:
        pass


# 2. Determinismo: mesma entrada, mesmo resultado.
@CONFIG
@given(fonte_estruturada)
def test_parse_e_deterministico(fonte):
    def tentar():
        try:
            return parse(fonte).para_dict()
        except ErroSintatico as e:
            return [str(d) for d in e.diagnosticos]

    assert tentar() == tentar()


# 3. Texto sem símbolos reservados vira exatamente um TextoLiteral.
@CONFIG
@given(st.text(max_size=100).filter(lambda s: not any(c in s for c in RESERVADOS)))
def test_texto_sem_reservados_e_preservado(fonte):
    esperado = [TextoLiteral(valor=fonte)] if fonte else []
    assert parse(fonte) == Mensagem(itens=esperado)


# 4. Se aceitou, a AST é coerente: posições válidas e Mensagem na raiz.
@CONFIG
@given(fonte_estruturada)
def test_ast_aceita_tem_posicoes_validas(fonte):
    try:
        arvore = parse(fonte)
    except ErroSintatico:
        return
    assert isinstance(arvore, Mensagem)
    for no in todos_os_nos(arvore):
        assert no.linha >= 1 and no.coluna >= 0


# 5. Todo erro traz ao menos um diagnóstico com posição.
@CONFIG
@given(fonte_estruturada)
def test_erros_trazem_posicao(fonte):
    try:
        parse(fonte)
    except ErroSintatico as e:
        assert e.diagnosticos
        assert all(d.linha >= 1 and d.coluna >= 0 for d in e.diagnosticos)