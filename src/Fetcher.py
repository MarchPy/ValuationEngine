import re
import os
import json
import requests
from src.FilterData import FilterData


class Fetcher:
    def __init__(self, settings: dict) -> None:
        self._settings = settings
        self._filterData = FilterData(settings=self._settings)
        self._driver = None
        
    def colect_all_symbols_from_api(self):
        statusInvest = self._settings['statusInvest']

        params = {
            "search": json.dumps(statusInvest["search"], separators=(",", ":")),
            "orderColumn": statusInvest["orderColumn"],
            "isAsc": statusInvest["isAsc"],
            "page": statusInvest["pagination"]["page"],
            "take": statusInvest["pagination"]["take"],
            "CategoryType": statusInvest["categoryType"],
        }
        response = requests.get(statusInvest["baseUrlAPI"], params=params, headers=statusInvest['headers'])
        if response.status_code != 200:
            return [], []
                
        return response.json()['list']
    
    def colect_indicators_from_symbol(self, ticker: str) -> list[dict]:
        ticker = ticker.lower()
        api = self._settings['statusInvest']['historyIndicatorsAPI']
        payload = {
            "codes[]": ticker.lower(),
            "time": "5",
            "byQuarter": "false",
            "futureData": "false"
        }

        response = requests.post(
            url=api,
            headers=self._settings['statusInvest']['headers'],
            data=payload
        )
        
        if response.status_code != 200:
            return []
        
        history_lines = []
        present_line_indicators = []
        data_json = response.json()['data'][ticker]
        for indicator in data_json:
            present_line = {
                "indicator": indicator['key'],
                "actual": indicator['actual'],
                "avg": indicator['avg'],
                "avgDifference": indicator['avgDifference'],
                "minValue": indicator['minValue'],
                "minValueRank": indicator['minValueRank'],
                "maxValue": indicator['maxValue'],
                "maxValueRank": indicator['maxValueRank'],
            }
            present_line_indicators.append(present_line)
              
              
            # valores históricos de um determinado ativo
            for year_ind in indicator['ranks']:
                year_ind.update({'indicator': indicator['key']})
                history_lines.append(year_ind)          

 
        return present_line_indicators, history_lines
             
   