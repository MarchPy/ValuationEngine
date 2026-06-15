import pandas as pd


class FilterData:
    """
    Motor de triagem e filtragem de ativos fundamentalistas.

    Aplica dois níveis de filtro sobre os dados coletados da API:

    1. **Pré-filtro** — elimina ativos que não atendem a critérios mínimos
       de preço ou liquidez antes da coleta de indicadores detalhados,
       reduzindo o volume de requisições à API.

    2. **Filtro rígido (Hard Filter)** — valida os indicadores fundamentalistas
       do período atual de cada ativo contra limites configurados em
       ``settings.json``, descartando empresas com endividamento excessivo,
       lucros inconsistentes ou outros fatores de risco elevado.

    Attributes:
        _settings (dict): Configurações globais da aplicação, incluindo
            as seções ``preFilter`` e ``hardFilter``.
    """

    def __init__(self, settings: dict) -> None:
        """
        Inicializa o FilterData com as configurações da aplicação.

        Args:
            settings (dict): Dicionário carregado de ``config/settings.json``.
                Deve conter as chaves ``preFilter`` e ``hardFilter``,
                cada uma mapeando nomes de colunas/indicadores para
                dicionários com os campos ``min`` e/ou ``max``.
        """
        self._settings = settings

    def pre_filter(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Aplica filtros iniciais ao DataFrame com todos os ativos listados.

        Itera sobre os critérios definidos em ``settings['preFilter']`` e
        descarta linhas cujos valores estejam fora do intervalo ``[min, max]``
        configurado para cada coluna. Limites com valor ``None`` são ignorados.

        Args:
            df (pd.DataFrame): DataFrame com todos os ativos retornados pela API,
                indexado por ``ticker``, contendo colunas como ``price`` e
                demais campos de triagem inicial.

        Returns:
            pd.DataFrame: Subconjunto do DataFrame original com apenas os ativos
                que passaram em todos os filtros configurados. Pode ser vazio
                se nenhum ativo atender aos critérios.

        Example:
            Com ``settings['preFilter'] = {"price": {"min": 5.0, "max": None}}``,
            todos os ativos com cotação abaixo de R$ 5,00 são removidos.
        """
        config_pre_filtro = self._settings['preFilter']

        for coluna, limites in config_pre_filtro.items():
            df = df[df[coluna] >= limites['min']] if limites['min'] is not None else df
            df = df[df[coluna] <= limites['max']] if limites['max'] is not None else df

        if df.empty:
            return df

        return df

    def filter_current_dataframe(self, df: pd.DataFrame) -> bool:
        """
        Avalia se um ativo passa em todos os critérios rígidos de qualidade.

        Itera sobre os filtros definidos em ``settings['hardFilter']``,
        verificando se cada indicador (linha do DataFrame) atende aos limites
        configurados por métrica e por coluna. Um ativo só é aprovado se
        **todas** as verificações forem satisfeitas.

        Args:
            df (pd.DataFrame): DataFrame do ativo com os indicadores do período
                atual como índice (ex.: ``'roe'``, ``'dividaliquida_ebitda'``)
                e colunas de métricas (ex.: ``'actual'``, ``'avg'``).

        Returns:
            bool: ``True`` se o ativo satisfaz todos os critérios de ``hardFilter``;
                ``False`` se qualquer critério falhar ou se um indicador
                esperado não estiver presente no DataFrame.

        Example:
            Com ``hardFilter = {"roe": {"actual": {"min": 10.0}}}`` e um ativo
            com ROE atual de 8%, retorna ``False`` e o ativo é descartado.
        """
        config_hard_filter = self._settings['hardFilter']
        resultados_filtros = []

        for nome_indicador, metricas in config_hard_filter.items():
            if nome_indicador not in df.index:
                resultados_filtros.append(False)
                continue

            for coluna_metrica, limites in metricas.items():
                valor_atual = df.loc[nome_indicador, coluna_metrica]

                if limites.get('min') is not None:
                    resultados_filtros.append(valor_atual >= limites['min'])

                if limites.get('max') is not None:
                    resultados_filtros.append(valor_atual <= limites['max'])

        return all(resultados_filtros)
