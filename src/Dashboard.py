import pandas as pd
import streamlit as st
import plotly.express as px


class DashBoardCompany:
    """
    Interface visual interativa do ValuationEngine via Streamlit.

    Consolida os históricos de indicadores de todas as empresas aprovadas
    pelo pipeline e renderiza um dashboard web com gráficos de valuation,
    rentabilidade e saúde financeira, organizados em abas temáticas.
    """

    def __init__(self) -> None:
        """
        Configura a página Streamlit antes de qualquer outro componente.

        Define o título da aba do navegador, o layout em largura total e
        o ícone da página. Deve ser instanciado antes de qualquer chamada
        a widgets Streamlit.

        Note:
            ``st.set_page_config`` só pode ser chamado uma vez por sessão
            Streamlit e precisa ser o primeiro comando executado.
        """
        st.set_page_config(
            page_title="Dashboard Fundamentalista",
            layout='wide',
            page_icon="📈"
        )

    def construct_data(self, dataset: list[pd.DataFrame]) -> None:
        """
        Constrói e renderiza o dashboard interativo com os indicadores das empresas.

        Concatena os DataFrames históricos de todas as empresas aprovadas,
        normaliza nomes de colunas para maiúsculas, aplica filtro por ticker
        via sidebar e distribui os gráficos em três abas temáticas.

        Args:
            dataset (list[pd.DataFrame]): Lista de DataFrames, um por empresa aprovada.
                Cada DataFrame deve conter uma coluna ``ticker`` e as colunas de
                indicadores (ex.: ``ROE``, ``LPA``, ``DY``, ``P_L``),
                indexadas pelo rank/ano retornado pela API.

        Returns:
            None

        Note:
            Exibe um aviso e encerra se ``dataset`` estiver vazio.
            Os gráficos são organizados em três abas:

            - **Valuation & Dividendos**: P/L, P/VP, DY, LPA;
            - **Rentabilidade & Crescimento**: ROE, ROIC, CAGR de receitas e lucros;
            - **Saúde Financeira**: Dívida/EBITDA, Dívida/PL, margem líquida, liquidez.
        """
        if not dataset:
            st.warning("Nenhum dado disponível.")
            return

        # 1. Consolidação e normalização dos dados de todas as empresas
        df_consolidado = pd.concat(dataset)
        df_consolidado.reset_index(inplace=True)
        df_consolidado.columns = [coluna.upper() for coluna in df_consolidado.columns]
        df_consolidado['TICKER'] = [ticker.upper() for ticker in df_consolidado['TICKER']]

        if 'RANK' in df_consolidado.columns:
            df_consolidado.rename(columns={'RANK': 'ANO'}, inplace=True)

        # Converte ANO para string para evitar notação decimal no eixo X
        if 'ANO' in df_consolidado.columns:
            df_consolidado['ANO'] = df_consolidado['ANO'].astype(str)

        df_consolidado = df_consolidado.sort_values(by='ANO')

        # 2. Sidebar com seleção do ativo
        st.sidebar.title("Filtros 🔎")
        tickers_disponiveis = sorted(df_consolidado['TICKER'].unique())
        ticker_selecionado  = st.sidebar.selectbox(
            label='Selecione o Ativo',
            options=tickers_disponiveis
        )

        df_empresa = df_consolidado[df_consolidado['TICKER'] == ticker_selecionado].copy()

        # 3. Cabeçalho da página
        st.title(f"📊 Análise Fundamentalista: {ticker_selecionado}")

        # 4. Cards de resumo com os indicadores mais recentes
        if not df_empresa.empty:
            indicadores_recentes = df_empresa.iloc[-1]

            st.subheader(f"Indicadores Recentes ({indicadores_recentes.get('ANO', 'Atual')})")
            col1, col2, col3, col4 = st.columns(4)
            col1.metric(label="Dividend Yield (DY)",       value=f"{indicadores_recentes.get('DY',   0):.2f}%")
            col2.metric(label="Preço / Lucro (P/L)",       value=f"{indicadores_recentes.get('P_L',  0):.2f}")
            col3.metric(label="Rentabilidade (ROE)",       value=f"{indicadores_recentes.get('ROE',  0):.2f}%")
            col4.metric(label="Preço / Valor Patrimonial", value=f"{indicadores_recentes.get('P_VP', 0):.2f}")

        st.markdown("---")

        # 5. Abas temáticas
        aba_valuation, aba_rentabilidade, aba_saude = st.tabs([
            "💰 Valuation & Dividendos",
            "📈 Rentabilidade & Crescimento",
            "🛡️ Saúde Financeira"
        ])

        def plot_indicador(nome_indicador: str, titulo: str, tipo_grafico: str = 'bar', cor: str = '#1f77b4'):
            """
            Gera um gráfico Plotly de barras ou linha para um indicador ao longo dos anos.

            Args:
                nome_indicador (str): Nome da coluna no DataFrame a ser plotada (ex.: ``'ROE'``).
                titulo (str): Título exibido no topo do gráfico.
                tipo_grafico (str): Tipo de visualização — ``'bar'`` para barras
                    ou qualquer outro valor para linha. Padrão: ``'bar'``.
                cor (str): Cor hexadecimal aplicada ao traçado. Padrão: ``'#1f77b4'``.

            Returns:
                plotly.graph_objs.Figure: Figura Plotly pronta para renderização
                    via ``st.plotly_chart()``.
            """
            if tipo_grafico == 'bar':
                figura = px.bar(df_empresa, x="ANO", y=nome_indicador, title=titulo, text_auto='.2s')
                figura.update_traces(marker_color=cor, textposition="outside", cliponaxis=False)
            else:
                figura = px.line(df_empresa, x="ANO", y=nome_indicador, title=titulo, markers=True)
                figura.update_traces(line_color=cor, line_width=3, marker_size=8)

            figura.update_layout(xaxis_title="", yaxis_title="", margin=dict(t=40, b=10, l=10, r=10))
            return figura

        with aba_valuation:
            col1, col2 = st.columns(2)
            col1.plotly_chart(plot_indicador("P_L",  "Histórico de P/L",    'line', cor='#FF9F36'), width='stretch')
            col2.plotly_chart(plot_indicador("P_VP", "Histórico de P/VP",   'line', cor='#00C2A8'), width='stretch')
            col3, col4 = st.columns(2)
            col3.plotly_chart(plot_indicador("DY",   "Histórico de DY (%)", 'bar',  cor='#4285F4'), width='stretch')
            col4.plotly_chart(plot_indicador("LPA",  "Lucro Por Ação (LPA)",'bar',  cor='#0F9D58'), width='stretch')

        with aba_rentabilidade:
            col1, col2 = st.columns(2)
            col1.plotly_chart(plot_indicador("ROE",            "Evolução do ROE (%)",      'line', cor='#DB4437'), width='stretch')
            col2.plotly_chart(plot_indicador("ROIC",           "Evolução do ROIC (%)",     'line', cor='#F4B400'), width='stretch')
            col3, col4 = st.columns(2)
            col3.plotly_chart(plot_indicador("RECEITAS_CAGR5", "CAGR Receitas 5 Anos (%)", 'bar',  cor='#673AB7'), width='stretch')
            col4.plotly_chart(plot_indicador("LUCROS_CAGR5",   "CAGR Lucros 5 Anos (%)",   'bar',  cor='#3F51B5'), width='stretch')

        with aba_saude:
            col1, col2 = st.columns(2)
            col1.plotly_chart(plot_indicador("DIVIDALIQUIDA_EBITDA",            "Dívida Líquida / EBITDA",        'line', cor='#E91E63'), width='stretch')
            col2.plotly_chart(plot_indicador("DIVIDALIQUIDA_PATRIMONIOLIQUIDO", "Dívida Líquida / Patr. Líquido", 'line', cor='#9C27B0'), width='stretch')
            col3, col4 = st.columns(2)
            col3.plotly_chart(plot_indicador("MARGEMLIQUIDA",    "Margem Líquida (%)", 'bar', cor='#009688'), width='stretch')
            col4.plotly_chart(plot_indicador("LIQUIDEZCORRENTE", "Liquidez Corrente",  'bar', cor='#795548'), width='stretch')
