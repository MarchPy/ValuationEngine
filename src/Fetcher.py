import json
import requests
from src.FilterData import FilterData


class Fetcher:
    """
    Camada de extração de dados via API do Status Invest.

    Responsável por coletar a lista completa de ativos listados na B3
    e os históricos de indicadores fundamentalistas de cada ativo,
    conforme os parâmetros definidos em ``config/settings.json``.

    Attributes:
        _settings (dict): Configurações globais da aplicação.
        _filterData (FilterData): Instância de filtragem reservada para
            uso interno em futuras implementações.
    """

    def __init__(self, settings: dict) -> None:
        """
        Inicializa o Fetcher com as configurações da aplicação.

        Args:
            settings (dict): Dicionário de configurações carregado de
                ``config/settings.json``, contendo URLs base, headers HTTP
                e parâmetros de paginação da API do Status Invest.
        """
        self._settings  = settings
        self._filterData = FilterData(settings=self._settings)
        self._driver    = None

    def colect_all_symbols_from_api(self) -> list[dict]:
        """
        Busca todos os ativos listados na B3 via API do Status Invest.

        Envia uma requisição GET com os parâmetros de busca, ordenação
        e paginação definidos em ``settings['statusInvest']`` e retorna
        a lista de ativos disponíveis no endpoint configurado.

        Returns:
            list[dict]: Lista de dicionários, cada um representando um ativo
                com pelo menos as chaves ``ticker`` e ``price``.
                Retorna uma lista vazia se a API retornar código diferente de 200.

        Raises:
            requests.exceptions.ConnectionError: Se não houver conexão com a
                internet ou o endpoint estiver indisponível.
        """
        config_si = self._settings['statusInvest']

        parametros_requisicao = {
            "search":       json.dumps(config_si["search"], separators=(",", ":")),
            "orderColumn":  config_si["orderColumn"],
            "isAsc":        config_si["isAsc"],
            "page":         config_si["pagination"]["page"],
            "take":         config_si["pagination"]["take"],
            "CategoryType": config_si["categoryType"],
        }

        resposta = requests.get(
            config_si["baseUrlAPI"],
            params=parametros_requisicao,
            headers=config_si['headers']
        )

        if resposta.status_code != 200:
            return []

        return resposta.json()['list']

    def colect_indicators_from_symbol(self, ticker: str) -> tuple[list[dict], list[dict]]:
        """
        Coleta os indicadores atuais e o histórico de 5 anos de um ativo.

        Envia uma requisição POST à API de histórico e processa a resposta,
        separando os dados em dois grupos:

        - **Indicadores atuais** — valores do período mais recente com estatísticas
          comparativas (média, mínimo, máximo e diferença em relação à média);
        - **Histórico anual** — todos os valores anuais de cada indicador,
          usados para análise de tendência e CAGR.

        Args:
            ticker (str): Código do ativo em qualquer capitalização
                (ex.: ``"PETR4"`` ou ``"petr4"``).
                É normalizado para minúsculas internamente.

        Returns:
            tuple[list[dict], list[dict]]: Par contendo:

            - ``indicadores_atuais`` — lista de dicionários com os dados do
              período corrente para cada indicador. Cada dicionário possui as
              chaves: ``indicator``, ``actual``, ``avg``, ``avgDifference``,
              ``minValue``, ``minValueRank``, ``maxValue``, ``maxValueRank``.
            - ``dados_historicos`` — lista de dicionários com os valores anuais
              de cada indicador. Cada dicionário contém a chave ``indicator``
              e os campos retornados pela API (ex.: ``rank``, ``value``).

            Retorna uma lista vazia se a API retornar código diferente de 200.

        Raises:
            requests.exceptions.ConnectionError: Se não houver conexão com a
                internet ou o endpoint estiver indisponível.
            KeyError: Se o ticker não for encontrado na resposta da API.
        """
        ticker = ticker.lower()
        url_historico = self._settings['statusInvest']['historyIndicatorsAPI']

        payload = {
            "codes[]":    ticker,
            "time":       "5",
            "byQuarter":  "false",
            "futureData": "false"
        }

        resposta = requests.post(
            url=url_historico,
            headers=self._settings['statusInvest']['headers'],
            data=payload
        )

        if resposta.status_code != 200:
            return []

        dados_api          = resposta.json()['data'][ticker]
        dados_historicos   = []
        indicadores_atuais = []

        for dado_indicador in dados_api:
            indicador_atual = {
                "indicator":     dado_indicador['key'],
                "actual":        dado_indicador['actual'],
                "avg":           dado_indicador['avg'],
                "avgDifference": dado_indicador['avgDifference'],
                "minValue":      dado_indicador['minValue'],
                "minValueRank":  dado_indicador['minValueRank'],
                "maxValue":      dado_indicador['maxValue'],
                "maxValueRank":  dado_indicador['maxValueRank'],
            }
            indicadores_atuais.append(indicador_atual)

            for dado_historico in dado_indicador['ranks']:
                dado_historico.update({'indicator': dado_indicador['key']})
                dados_historicos.append(dado_historico)

        return indicadores_atuais, dados_historicos
