"""Fontes de insumo do rateio AutoTruck (conector SGA).

Abstrai DE ONDE vêm os veículos/eventos para o fechamento. Hoje a fonte
real é o export FECHAMENTO.xlsx do SGA; amanhã será um endpoint do SGA —
ambos implementam o mesmo `Protocol`, então o motor não muda.

Requisitos de interface (do levantamento): Placa, Valor FIPE, Status de
Pagamento (D+0), Data de Aviso do Sinistro, Status de Liquidação do
Salvado, Tipo/Envolvimento do evento.
"""

from typing import Protocol, runtime_checkable

from .domain import EventoAT, VeiculoAT
from .ingestao import ler_fechamento


@runtime_checkable
class FonteRateio(Protocol):
    """Contrato único de ingestão. `carregar()` devolve a base do mês."""

    nome: str

    def carregar(self) -> tuple[list[VeiculoAT], list[EventoAT], dict]:
        """(veiculos, eventos, meta). `meta` traz ao menos
        {'mes_ano_ref', 'origem'} e o que mais a fonte souber."""
        ...


class FonteFechamentoXlsx:
    """Fonte REAL atual: o export FECHAMENTO.xlsx do SGA.

    Eventos = os sinistros reais da aba RATEIO. A planilha não traz a
    base de veículos; a base de cotas ativas é informada (parâmetro do
    fechamento), espelhando como a AutoTruck opera hoje.
    """

    def __init__(self, path: str, mes_ano_ref: str = "FECHAMENTO") -> None:
        self.path = path
        self.mes_ano_ref = mes_ano_ref
        self.nome = f"FECHAMENTO.xlsx ({path.split('/')[-1]})"

    def carregar(self) -> tuple[list[VeiculoAT], list[EventoAT], dict]:
        f = ler_fechamento(self.path)
        meta = {
            "mes_ano_ref": self.mes_ano_ref,
            "origem": "FECHAMENTO_XLSX",
            "arquivo": self.path,
            "secoes": f.secoes_com_dados,
            "analitico_declarado": {
                "rateio_leves": f.analitico.rateio_leves,
                "rateio_motos": f.analitico.rateio_motos,
            },
        }
        return [], f.eventos, meta


class FonteSGAHttp:
    """Conector do SGA via relatório/endpoint (fase de produção).

    Quando o endpoint do SGA estiver disponível, implementar `carregar()`
    com o GET autenticado e o mapeamento de colunas para VeiculoAT/EventoAT
    (mesmo contrato do FonteFechamentoXlsx). Mantido como adaptador
    explícito para ser um drop-in — não inventa dados.
    """

    def __init__(self, base_url: str, token: str, mes_ano_ref: str) -> None:
        self.base_url = base_url
        self.token = token
        self.mes_ano_ref = mes_ano_ref
        self.nome = f"SGA HTTP ({base_url})"

    def carregar(self) -> tuple[list[VeiculoAT], list[EventoAT], dict]:
        raise NotImplementedError(
            "Conector SGA HTTP: configurar endpoint/credenciais do SGA. "
            "O contrato e o pipeline D+0..D+5 já estão prontos (ver "
            "FonteFechamentoXlsx, mesmo Protocol)."
        )


class FonteMemoria:
    """Fonte em memória — para testes e simulações controladas."""

    def __init__(self, veiculos, eventos, mes_ano_ref: str) -> None:
        self._v = list(veiculos)
        self._e = list(eventos)
        self.mes_ano_ref = mes_ano_ref
        self.nome = "memória (teste)"

    def carregar(self) -> tuple[list[VeiculoAT], list[EventoAT], dict]:
        return self._v, self._e, {"mes_ano_ref": self.mes_ano_ref,
                                  "origem": "MEMORIA"}
