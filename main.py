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
    def __init__(self) -> None:
        try:
            with open(file='config/settings.json', mode='r') as f:
                self._settings = json.load(fp=f)
        
        except FileNotFoundError:
            raise FileNotFoundError('Arquivo "settings.json" não foi encontrado.')
        
        self._console = Console()
        self._fetcher = Fetcher(settings=self._settings)
        self._filter_data = FilterData(settings=self._settings)
        self._deep_analyzer = DeepAnalyzer()
        self._dashboard_company = DashBoardCompany()
        
    def _save_file(self, final_data: pd.DataFrame) -> None:
        period = datetime.now().strftime(format='%m-%Y')
        try:
            os.makedirs(name=f'output/{period}')
            
        except FileExistsError:
            pass
        
        final_data.to_excel(excel_writer=os.path.join(f'output/{period}', f'Ativos com potêncial de investimento ({period}).xlsx'), index=True)
        
    def run(self):
        with self._console.status(status='Coletando os principais ativos listados...') as status:
            response = self._fetcher.colect_all_symbols_from_api()
            status.update(status='Ativos coletados')
            df_base = pd.DataFrame(data=response)
            df_base['ticker'] = df_base['ticker'].str.lower()
            df_base.set_index(keys='ticker', inplace=True)
            df_base = self._filter_data.pre_filter(df=df_base)
            tickers = df_base.index.to_list()
            
            status.update(status='Realizando a coleta de dados por ativos...')
            data_dash = []
            final_company = []
            for ticker in tickers:
                present_line_indicators, history_lines = self._fetcher.colect_indicators_from_symbol(ticker=ticker)  
                df_unique = pd.DataFrame(data=present_line_indicators)
                df_unique.set_index(keys='indicator', inplace=True)
                result = self._filter_data.Filter_current_dataframe(df=df_unique)
                if result:
                    df_history = pd.DataFrame(data=history_lines).pivot(columns='rank', index='indicator', values='value')
                    df_history.fillna(value=0, inplace=True)
                    
                    # Separando para o dashboard
                    df_to_dash = df_history.T
                    df_to_dash['ticker'] = ticker
                    data_dash.append(df_to_dash)
                    
                    df_history.reset_index(inplace=True)
                    status.update(status=f'Realizando análise do ativo >> {ticker}')
                    result_analysis = self._deep_analyzer.analyze(ticker=ticker, df_history=df_history, price=df_base.loc[ticker, 'price'])
                    final_company.append(result_analysis)
            
            df_analyzed = pd.DataFrame(data=final_company)
            df_analyzed.set_index(keys='ticker', inplace=True)
            df_merge = df_base.merge(df_analyzed, left_index=True, right_index=True, how='left')
            df_merge.index = df_merge.index.str.upper()
            df_merge.sort_values(by='score', ascending=False, inplace=True)
            df_merge.dropna(inplace=True, axis=0)
            self._save_file(final_data=df_merge)
            self._console.log('[[bold green]Arquivo com os resultados salvo na pasta output[/]]')
            
            status.update(status='Iniciando o Web DashBoard...')
            self._dashboard_company.construct_data(dataset=data_dash)
            self._console.log('[[bold green]DashBoard pronto[/]]')

        
if __name__ == "__main__":
    app = Main()
    app.run()
    