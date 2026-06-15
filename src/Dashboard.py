import pandas as pd
import streamlit as st
import plotly.express as px # Usamos 'px' por convenção

class DashBoardCompany:
    def __init__(self):
        # A configuração da página deve ser o primeiro comando do Streamlit
        st.set_page_config(page_title="Dashboard Fundamentalista", layout='wide', page_icon="📈")
        
    def construct_data(self, dataset: list[pd.DataFrame]) -> None:        
        if not dataset:
            st.warning("Nenhum dado disponível.")
            return

        # 1. Preparação dos Dados
        df = pd.concat(dataset)
        df.reset_index(inplace=True)
        df.columns = [column.upper() for column in df.columns]
        df['TICKER'] = [ticker.upper() for ticker in df['TICKER']]
        
        if 'RANK' in df.columns:
            df.rename(columns={'RANK': 'ANO'}, inplace=True)
            
        # Converte ANO para string para evitar números decimais no eixo X do gráfico
        if 'ANO' in df.columns:
            df['ANO'] = df['ANO'].astype(str)
        
        # Ordena cronologicamente
        df = df.sort_values(by='ANO')
        
        # 2. Sidebar e Filtros
        st.sidebar.title("Filtros 🔎")
        tickers_disponiveis = sorted(df['TICKER'].unique())
        ticker_selecionado = st.sidebar.selectbox(label='Selecione o Ativo', options=tickers_disponiveis)

        # Filtra o dataframe para exibir apenas a empresa escolhida
        df_filtered = df[df['TICKER'] == ticker_selecionado].copy()

        # 3. Cabeçalho Principal
        st.title(f"📊 Análise Fundamentalista: {ticker_selecionado}")
        
        # 4. Cards de Resumo (Pegando os dados do ano mais recente)
        if not df_filtered.empty:
            ultimo_ano = df_filtered.iloc[-1] # Pega a última linha (ano mais recente)
            
            st.subheader(f"Indicadores Recentes ({ultimo_ano.get('ANO', 'Atual')})")
            c1, c2, c3, c4 = st.columns(4)
            c1.metric(label="Dividend Yield (DY)", value=f"{ultimo_ano.get('DY', 0):.2f}%")
            c2.metric(label="Preço / Lucro (P/L)", value=f"{ultimo_ano.get('P_L', 0):.2f}")
            c3.metric(label="Rentabilidade (ROE)", value=f"{ultimo_ano.get('ROE', 0):.2f}%")
            c4.metric(label="Preço / Valor Patrimonial", value=f"{ultimo_ano.get('P_VP', 0):.2f}")
            
        st.markdown("---")

        # 5. Organização em Abas para manter a interface limpa
        tab1, tab2, tab3 = st.tabs(["💰 Valuation & Dividendos", "📈 Rentabilidade & Crescimento", "🛡️ Saúde Financeira"])

        # Função auxiliar para não repetir o mesmo código de formatação 10 vezes
        def plot_indicador(indicador, title, chart_type='bar', color='#1f77b4'):
            # Cria a figura baseada no tipo escolhido
            if chart_type == 'bar':
                fig = px.bar(df_filtered, x="ANO", y=indicador, title=title, text_auto='.2s')
                fig.update_traces(marker_color=color, textposition="outside", cliponaxis=False)
            else:
                fig = px.line(df_filtered, x="ANO", y=indicador, title=title, markers=True)
                fig.update_traces(line_color=color, line_width=3, marker_size=8)
            
            # Limpa o visual do gráfico
            fig.update_layout(xaxis_title="", yaxis_title="", margin=dict(t=40, b=10, l=10, r=10))
            return fig

        # Populando a Aba 1
        with tab1:
            col1, col2 = st.columns(2)
            col1.plotly_chart(plot_indicador("P_L", "Histórico de P/L", 'line', color='#FF9F36'), width='stretch')
            col2.plotly_chart(plot_indicador("P_VP", "Histórico de P/VP", 'line', color='#00C2A8'), width='stretch')
            
            col3, col4 = st.columns(2)
            col3.plotly_chart(plot_indicador("DY", "Histórico de DY (%)", 'bar', color='#4285F4'), width='stretch')
            col4.plotly_chart(plot_indicador("LPA", "Lucro Por Ação (LPA)", 'bar', color='#0F9D58'), width='stretch')

        # Populando a Aba 2
        with tab2:
            col1, col2 = st.columns(2)
            col1.plotly_chart(plot_indicador("ROE", "Evolução do ROE (%)", 'line', color='#DB4437'), width='stretch')
            col2.plotly_chart(plot_indicador("ROIC", "Evolução do ROIC (%)", 'line', color='#F4B400'), width='stretch')
            
            col3, col4 = st.columns(2)
            col3.plotly_chart(plot_indicador("RECEITAS_CAGR5", "CAGR Receitas 5 Anos (%)", 'bar', color='#673AB7'), width='stretch')
            col4.plotly_chart(plot_indicador("LUCROS_CAGR5", "CAGR Lucros 5 Anos (%)", 'bar', color='#3F51B5'), width='stretch')

        # Populando a Aba 3
        with tab3:
            col1, col2 = st.columns(2)
            col1.plotly_chart(plot_indicador("DIVIDALIQUIDA_EBITDA", "Dívida Líquida / EBITDA", 'line', color='#E91E63'), width='stretch')
            col2.plotly_chart(plot_indicador("DIVIDALIQUIDA_PATRIMONIOLIQUIDO", "Dívida Líquida / Patr. Líquido", 'line', color='#9C27B0'), width='stretch')
            
            col3, col4 = st.columns(2)
            col3.plotly_chart(plot_indicador("MARGEMLIQUIDA", "Margem Líquida (%)", 'bar', color='#009688'), width='stretch')
            col4.plotly_chart(plot_indicador("LIQUIDEZCORRENTE", "Liquidez Corrente", 'bar', color='#795548'), width='stretch')
    