import os
import json
import pandas as pd
from datetime import datetime
from src.Fetcher import Fetcher
from src.FilterData import FilterData
from src.Analyser import DeepAnalyzer
from src.Dashboard import DashBoardCompany
from rich.console import Console


class Main:
    """
    Orquestrador principal do ValuationEngine.

    Responsável por inicializar todos os componentes do pipeline,
    coordenar a coleta, filtragem, análise e visualização dos dados
    de ações listadas na B3.

    Attributes:
        _settings (dict): Configurações carregadas do arquivo ``config/settings.json``.
        _console (Console): Instância do console Rich para saída formatada no terminal.
        _fetcher (Fetcher): Componente de coleta de dados via API.
        _filter_data (FilterData): Componente de triagem e filtragem de ativos.
        _deep_analyzer (DeepAnalyzer): Componente de análise quantitativa e de valuation.
        _dashboard_company (DashBoardCompany): Componente de construção do dashboard Streamlit.
    """

    def __init__(self) -> None:
        """
        Inicializa o orquestrador carregando as configurações e instanciando todos os componentes.

        Lê o arquivo ``config/settings.json`` e repassa as configurações a cada
        componente do pipeline. Caso o arquivo não exista, encerra a execução
        com uma mensagem de erro clara.

        Raises:
            FileNotFoundError: Se o arquivo ``config/settings.json`` não for encontrado
                no diretório de trabalho atual.
        """
        try:
            with open(file='config/settings.json', mode='r') as f:
                self._settings = json.load(fp=f)
        except FileNotFoundError:
            raise FileNotFoundError('Arquivo "settings.json" não foi encontrado.')

        self._console           = Console()
        self._fetcher           = Fetcher(settings=self._settings)
        self._filter_data       = FilterData(settings=self._settings)
        self._deep_analyzer     = DeepAnalyzer()
        self._dashboard_company = DashBoardCompany()

    def _save_file(self, final_data: pd.DataFrame) -> None:
        """
        Persiste o ranking final de ativos em uma planilha Excel.

        Cria automaticamente o diretório ``output/<MM-YYYY>/`` se ainda não
        existir e salva o DataFrame com o ranking completo no formato ``.xlsx``.
        O nome do arquivo inclui o período (mês e ano) de geração.

        Args:
            final_data (pd.DataFrame): DataFrame com os ativos aprovados,
                ordenados por score decrescente, contendo indicadores
                fundamentalistas e o valor intrínseco calculado.

        Returns:
            None

        Example:
            O arquivo gerado terá o caminho::

                output/06-2025/Ativos com potêncial de investimento (06-2025).xlsx
        """
        periodo = datetime.now().strftime(format='%m-%Y')
        try:
            os.makedirs(name=f'output/{periodo}')
        except FileExistsError:
            pass

        final_data.to_excel(
            excel_writer=os.path.join(
                f'output/{periodo}',
                f'Ativos com potêncial de investimento ({periodo}).xlsx'
            ),
            index=True
        )

    def run(self) -> None:
        """
        Executa o pipeline completo de coleta, filtragem, análise e exportação.

        O fluxo segue as etapas abaixo em sequência:

        1. **Coleta de tickers** — busca todos os ativos listados na B3 via API.
        2. **Pré-filtragem** — remove ativos que falham em critérios básicos de preço.
        3. **Coleta de indicadores por ativo** — busca indicadores atuais e histórico
           de 5 anos para cada ticker aprovado.
        4. **Filtros rígidos** — descarta ativos com dívida abusiva, lucros
           inconsistentes ou prejuízos recorrentes.
        5. **Análise profunda** — calcula valor intrínseco (Graham), CAGR,
           tendência de ROE e score de qualidade (0–10).
        6. **Consolidação** — mescla os dados de base com os resultados da análise,
           ordena por score decrescente e remove linhas incompletas.
        7. **Exportação** — salva a planilha Excel em ``output/``.
        8. **Dashboard** — inicializa o ambiente web Streamlit com os históricos
           de indicadores das empresas aprovadas.

        Returns:
            None

        Note:
            Todo o progresso é exibido no terminal via spinner do Rich.
            O arquivo Excel é salvo antes da inicialização do dashboard,
            garantindo a persistência dos resultados mesmo que o servidor
            web não seja iniciado corretamente.
        """
        with self._console.status(status='Coletando os principais ativos listados...') as status:
            resposta_api = self._fetcher.colect_all_symbols_from_api()
            status.update(status='Ativos coletados')

            df_base = pd.DataFrame(data=resposta_api)
            df_base['ticker'] = df_base['ticker'].str.lower()
            df_base.set_index(keys='ticker', inplace=True)
            df_base = self._filter_data.pre_filter(df=df_base)
            tickers = df_base.index.to_list()

            status.update(status='Realizando a coleta de dados por ativos...')

            historicos_dashboard = []
            resultados_analise   = []

            for ticker in tickers:
                indicadores_atuais, dados_historicos = self._fetcher.colect_indicators_from_symbol(ticker=ticker)

                df_indicadores_atuais = pd.DataFrame(data=indicadores_atuais)
                df_indicadores_atuais.set_index(keys='indicator', inplace=True)

                aprovado = self._filter_data.filter_current_dataframe(df=df_indicadores_atuais)

                if aprovado:
                    df_historico = pd.DataFrame(data=dados_historicos).pivot(
                        columns='rank', index='indicator', values='value'
                    )
                    df_historico.fillna(value=0, inplace=True)

                    df_historico_dashboard = df_historico.T
                    df_historico_dashboard['ticker'] = ticker
                    historicos_dashboard.append(df_historico_dashboard)

                    df_historico.reset_index(inplace=True)

                    status.update(status=f'Realizando análise do ativo >> {ticker}')
                    resultado = self._deep_analyzer.analyze(
                        ticker=ticker,
                        df_historico=df_historico,
                        preco_atual=df_base.loc[ticker, 'price']
                    )
                    resultados_analise.append(resultado)

            df_analisado = pd.DataFrame(data=resultados_analise)
            df_analisado.set_index(keys='ticker', inplace=True)

            df_ranking = df_base.merge(df_analisado, left_index=True, right_index=True, how='left')
            df_ranking.index = df_ranking.index.str.upper()
            df_ranking.sort_values(by='score', ascending=False, inplace=True)
            df_ranking.dropna(inplace=True, axis=0)

            self._save_file(final_data=df_ranking)
            self._console.log('[[bold green]Arquivo com os resultados salvo na pasta output[/]]')

            status.update(status='Iniciando o Web DashBoard...')
            self._dashboard_company.construct_data(dataset=historicos_dashboard)
            self._console.log('[[bold green]DashBoard pronto[/]]')


if __name__ == "__main__":
    app = Main()
    app.run()
