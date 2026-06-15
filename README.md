# ValuationEngine

O ValuationEngine é um motor de análise quantitativa e fundamentalista desenvolvido em Python para automatizar a seleção de ativos na bolsa brasileira (B3). O sistema processa dados complexos e aplica uma rigorosa triagem matemática para identificar empresas sólidas, em crescimento e negociadas com desconto (Margem de Segurança).

<table>
  <tr>
    <td>
      <img src="https://github.com/user-attachments/assets/efffc09d-151c-4647-acad-f4890c945b4c">
    </td>
    <td>
      <img src="https://github.com/user-attachments/assets/c118f46d-4692-4b85-8456-8a45bc0960d2">
    </td>
  </tr>
  <tr>
    <td>
      <img src="https://github.com/user-attachments/assets/9480dd2d-2436-417e-bb1e-8a8506cc299e">
    </td>
    <td>
      <img src="https://github.com/user-attachments/assets/77b14fd4-d5db-45f1-83b8-0b751c30295f">
    </td>
  </tr>
</table>

## 🎯 O Objetivo

O investidor pessoa física frequentemente enfrenta a paralisia por análise ou decisões baseadas em ruídos. O ValuationEngine remove o fator emocional, aplicando uma metodologia Data-Driven baseada nos pilares do Value Investing (fórmula de Benjamin Graham), entregando um ranking objetivo de investimentos.

## ⚙️ Funcionalidades

- Triagem Automatizada: Executa filtros rígidos (Hard Filters) para eliminar empresas com dívidas abusivas, lucros inconsistentes ou prejuízos recorrentes.
- Cálculo de Valor Intrínseco: Utiliza modelos matemáticos para determinar o "preço justo" dos ativos.
- Análise de Eficiência: Processa indicadores como ROE, ROIC e tendências de longo prazo (CAGR de lucros e receitas).
- Ranking de Elite: Classifica as empresas aprovadas por um Score de qualidade (0 a 10).
- Dashboard Interativo: Interface web em tempo real (Streamlit) para visualização de históricos e indicadores.

## 🏗️ Arquitetura do Sistema

O projeto segue princípios de Clean Architecture, dividindo responsabilidades:

- Fetcher.py: Camada de extração e consumo de dados via API.
- FilterData.py: Motor de regras de negócio (filtros de exclusão).
- Analyser.py: Core matemático (cálculos de valuation e pontuação).
- Dashboard.py: Interface visual intuitiva com gráficos dinâmicos.
- main.py: Orquestrador central de todo o pipeline de dados.

## 🚀 Como Executar

### Pré-requisitos

Certifique-se de ter o Python 3.11+ instalado.

### Passos

1. Clone o repositório:

```bash
git clone https://github.com/MarchPy/ValuationEngine.git
```

2. Instale as dependências:

```bash
pip install -r requirements.txt
```

3. Execute o motor principal (gera o ranking em Excel na pasta output/):

```bash
streamlit run .\main.py
```

## 📊 Visualização

O sistema gera um arquivo Excel (.xlsx) mensal com o ranking completo e um ambiente web onde você pode filtrar cada empresa, visualizar o histórico de 5 anos de indicadores e conferir métricas cruciais como P/L, DY e dívida líquida.

## ⚠️ Disclaimer

Este projeto é uma ferramenta de estudo e análise de dados. Nenhuma informação aqui contida deve ser interpretada como uma recomendação oficial de compra ou venda de ativos financeiros. A responsabilidade por decisões de investimento é exclusivamente do usuário.
