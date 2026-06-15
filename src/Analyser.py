import math
import pandas as pd


class DeepAnalyzer:
    def __init__(self):
        # Constante de Graham (P/L máx 15 * P/VP máx 1.5)
        self.GRAHAM_CONSTANT = 22.5

    def calcular_cagr(self, inital_value: float, final_value: float, anos: int) -> float:
        """Calcula a Taxa de Crescimento Anual Composta."""
        if inital_value <= 0 or final_value <= 0 or anos <= 0:
            return 0.0
        return ((final_value / inital_value) ** (1 / anos)) - 1

    def analyze(self, ticker: str, df_history: pd.DataFrame, price: float) -> dict:
        """
        Recebe o DataFrame histórico (index=indicator, columns=anos) e o preço atual.
        """
        # Garante que o índice é o nome do indicador
        if 'indicator' in df_history.columns:
            df = df_history.set_index('indicator')
        else:
            df = df_history

        analysis = {
            "ticker": ticker,
            "valor_intrinseco": 0.0,
            "margem_seguranca": 0.0,
            "cagr_lucro_5a": 0.0,
            "tendencia_roe": "Estável",
            "score": 0
        }

        # 1. VALUATION DE GRAHAM
        # Nota: Certifique-se que sua API/DataFrame usa os nomes 'lpa' e 'vpa'
        if 'lpa' in df.index and 'vpa' in df.index:
            lpa_atual = df.loc['lpa'].iloc[-1]
            vpa_atual = df.loc['vpa'].iloc[-1]

            if lpa_atual > 0 and vpa_atual > 0:
                vi = math.sqrt(self.GRAHAM_CONSTANT * lpa_atual * vpa_atual)
                analysis["valor_intrinseco"] = round(vi, 2)
                if vi > 0:
                    analysis["margem_seguranca"] = round(((vi - price) / vi) * 100, 2)

        # 2. CRESCIMENTO (CAGR 5 anos)
        if 'lpa' in df.index and len(df.columns) >= 5:
            lpa_inicio = df.loc['lpa'].iloc[-5]
            lpa_fim = df.loc['lpa'].iloc[-1]
            cagr = self.calcular_cagr(lpa_inicio, lpa_fim, 5)
            analysis["cagr_lucro_5a"] = round(cagr * 100, 2)

        # 3. TENDÊNCIA DE ROE
        if 'roe' in df.index and len(df.columns) >= 3:
            roe_antigo = df.loc['roe'].iloc[-3]
            roe_atual = df.loc['roe'].iloc[-1]
            if roe_atual > roe_antigo * 1.05: analysis["tendencia_roe"] = "Crescente"
            elif roe_atual < roe_antigo * 0.95: analysis["tendencia_roe"] = "Decrescente"

        # 4. SCORE DE QUALIDADE (0 a 10)
        score = 0
        if 'roe' in df.index and df.loc['roe'].iloc[-1] > 15: score += 3
        if 'dividaliquida_ebitda' in df.index and df.loc['dividaliquida_ebitda'].iloc[-1] < 2.0: score += 3
        if analysis["cagr_lucro_5a"] > 5: score += 2
        if analysis["margem_seguranca"] > 20: score += 2
        
        analysis["score"] = score
        return analysis
