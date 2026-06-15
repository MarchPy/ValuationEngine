import pandas as pd


class FilterData:
    def __init__(self, settings: dict) -> None:
        self._settings = settings
    
    def pre_filter(self, df: pd.DataFrame) -> pd.DataFrame:
        filters = self._settings['preFilter']
        for key, values in filters.items():
            df = df[(df[key] >= values['min'])] if values['min'] is not None else df
            df = df[(df[key] <= values['max'])] if values['max'] is not None else df
        
        if df.empty:
            return df
        
        return df
  
    def Filter_current_dataframe(self, df: pd.DataFrame):
        filters = self._settings['hardFilter']
        
        verify = []
        for indicator, metrics in filters.items():
            if indicator not in df.index:
                verify.append(False)
                continue
            
            for metrics_column, limits in metrics.items():
                value  = df.loc[indicator, metrics_column]
                if limits.get('min') is not None:
                    if value >= limits['min']:
                        verify.append(True)
                    else:
                        verify.append(False)
                        
                if limits.get('max') is not None:
                    if value <= limits['max']:
                        verify.append(True)
                    else:
                        verify.append(False)
        
        return all(verify)
                                