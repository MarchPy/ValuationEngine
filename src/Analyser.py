import math
import pandas as pd


class DeepAnalyzer:
    """
    Motor de análise quantitativa e fundamentalista de ações.

    Responsável por calcular o valor intrínseco pelo modelo de Graham,
    mensurar o crescimento histórico dos lucros (CAGR), avaliar a tendência
    de rentabilidade (ROE) e atribuir um score de qualidade de 0 a 10
    a cada ativo aprovado pelos filtros rígidos.

    Attributes:
        GRAHAM_CONSTANT (float): Constante do modelo de Graham
            derivada da premissa P/L máx 15 × P/VP máx 1,5 = 22,5.
    """

    def __init__(self) -> None:
        """
        Inicializa o analisador com a constante de Graham.

        A constante 22,5 é derivada da premissa de Benjamin Graham de que
        nenhuma ação merece ser comprada com P/L acima de 15 e P/VP acima
        de 1,5 simultaneamente (15 × 1,5 = 22,5).
        """
        self.GRAHAM_CONSTANT = 22.5

    def calcular_cagr(self, valor_inicial: float, valor_final: float, anos: int) -> float:
        """
        Calcula a Taxa de Crescimento Anual Composta (CAGR).

        Fórmula aplicada::

            CAGR = (valor_final / valor_inicial) ^ (1 / anos) - 1

        Args:
            valor_inicial (float): Valor no início do período
                (ex.: LPA do primeiro ano da janela analisada).
            valor_final (float): Valor ao final do período
                (ex.: LPA do último ano da janela analisada).
            anos (int): Número de anos do intervalo de análise.

        Returns:
            float: Taxa de crescimento anual composta como decimal
                (ex.: 0.12 representa 12% a.a.).
                Retorna ``0.0`` se qualquer argumento for menor ou igual a zero.

        Example:
            >>> analisador = DeepAnalyzer()
            >>> analisador.calcular_cagr(valor_inicial=1.0, valor_final=1.61, anos=5)
            0.10  # ≈ 10% a.a.
        """
        if valor_inicial <= 0 or valor_final <= 0 or anos <= 0:
            return 0.0
        return ((valor_final / valor_inicial) ** (1 / anos)) - 1

    def analyze(self, ticker: str, df_historico: pd.DataFrame, preco_atual: float) -> dict:
        """
        Executa a análise fundamentalista completa de um ativo.

        Processa o histórico de indicadores para calcular o valor intrínseco
        pelo modelo de Graham, a margem de segurança, o CAGR do LPA em 5 anos,
        a tendência do ROE e um score de qualidade de 0 a 10.

        Args:
            ticker (str): Código do ativo na B3 (ex.: ``"petr4"``).
            df_historico (pd.DataFrame): DataFrame com o histórico de indicadores.
                Aceita tanto a coluna ``'indicator'`` presente quanto o índice já
                definido com os nomes dos indicadores (ex.: ``'lpa'``, ``'vpa'``, ``'roe'``).
            preco_atual (float): Cotação atual do ativo em reais (R$).

        Returns:
            dict: Dicionário com os resultados da análise:

            - ``ticker`` (str): Código do ativo.
            - ``valor_intrinseco`` (float): Preço justo calculado por Graham —
              ``√(22,5 × LPA × VPA)``.
            - ``margem_seguranca`` (float): Desconto do preço atual em relação
              ao valor intrínseco, em percentual (%).
            - ``cagr_lucro_5a`` (float): Crescimento anual composto do LPA
              nos últimos 5 anos (%).
            - ``tendencia_roe`` (str): Direção do ROE nos últimos 3 anos —
              ``"Crescente"``, ``"Decrescente"`` ou ``"Estável"``.
            - ``score`` (int): Pontuação de qualidade de 0 a 10, composta por:

              +3 pts se ROE > 15%;
              +3 pts se Dívida Líquida/EBITDA < 2,0;
              +2 pts se CAGR do LPA > 5% a.a.;
              +2 pts se margem de segurança > 20%.
        """
        if 'indicator' in df_historico.columns:
            df_indicadores = df_historico.set_index('indicator')
        else:
            df_indicadores = df_historico

        resultado = {
            "ticker":           ticker,
            "valor_intrinseco": 0.0,
            "margem_seguranca": 0.0,
            "cagr_lucro_5a":    0.0,
            "tendencia_roe":    "Estável",
            "score":            0
        }

        # 1. VALUATION DE GRAHAM: √(22,5 × LPA × VPA)
        if 'lpa' in df_indicadores.index and 'vpa' in df_indicadores.index:
            lpa_atual = df_indicadores.loc['lpa'].iloc[-1]
            vpa_atual = df_indicadores.loc['vpa'].iloc[-1]

            if lpa_atual > 0 and vpa_atual > 0:
                valor_intrinseco = math.sqrt(self.GRAHAM_CONSTANT * lpa_atual * vpa_atual)
                resultado["valor_intrinseco"] = round(valor_intrinseco, 2)
                if valor_intrinseco > 0:
                    resultado["margem_seguranca"] = round(
                        ((valor_intrinseco - preco_atual) / valor_intrinseco) * 100, 2
                    )

        # 2. CRESCIMENTO: CAGR do LPA nos últimos 5 anos
        if 'lpa' in df_indicadores.index and len(df_indicadores.columns) >= 5:
            lpa_cinco_anos_atras = df_indicadores.loc['lpa'].iloc[-5]
            lpa_atual            = df_indicadores.loc['lpa'].iloc[-1]
            cagr = self.calcular_cagr(lpa_cinco_anos_atras, lpa_atual, 5)
            resultado["cagr_lucro_5a"] = round(cagr * 100, 2)

        # 3. TENDÊNCIA DE ROE: comparação com 3 anos atrás (±5% de tolerância)
        if 'roe' in df_indicadores.index and len(df_indicadores.columns) >= 3:
            roe_tres_anos_atras = df_indicadores.loc['roe'].iloc[-3]
            roe_atual           = df_indicadores.loc['roe'].iloc[-1]

            if roe_atual > roe_tres_anos_atras * 1.05:
                resultado["tendencia_roe"] = "Crescente"
            elif roe_atual < roe_tres_anos_atras * 0.95:
                resultado["tendencia_roe"] = "Decrescente"

        # 4. SCORE DE QUALIDADE (0 a 10)
        score = 0
        if 'roe' in df_indicadores.index and df_indicadores.loc['roe'].iloc[-1] > 15:
            score += 3
        if 'dividaliquida_ebitda' in df_indicadores.index and df_indicadores.loc['dividaliquida_ebitda'].iloc[-1] < 2.0:
            score += 3
        if resultado["cagr_lucro_5a"] > 5:
            score += 2
        if resultado["margem_seguranca"] > 20:
            score += 2

        resultado["score"] = score
        return resultado
