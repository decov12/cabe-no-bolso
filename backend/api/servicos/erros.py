"""Exceções dos serviços de busca e IA.

A view do Henrique pode tratar as duas assim:
- ErroEntrada        -> 400 (a pessoa mandou algo errado ou não há voo/hotel para os dados)
- ErroServicoExterno -> 502/503 (SerpApi ou Gemini falharam mesmo depois de 1 nova tentativa)

A mensagem (str(erro) ou erro.mensagem) já está em português e pode ir para a tela.
Ela nunca contém chave de API nem URL com a chave.
"""


class ErroServico(Exception):
    """Base das exceções dos serviços."""

    def __init__(self, mensagem):
        super().__init__(mensagem)
        self.mensagem = mensagem


class ErroEntrada(ErroServico):
    """Dados de entrada inválidos (datas, orçamento, pessoas, códigos...)."""


class ErroServicoExterno(ErroServico):
    """A SerpApi ou o Gemini falharam depois de 1 nova tentativa."""
