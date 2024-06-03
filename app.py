from flask import Flask, render_template_string
import pandas as pd
import requests
from io import StringIO  
import plotly.express as px
import plotly.io as pio

app = Flask(__name__)

@app.route('/')
def display_table():
    # Wettquoten holen
    url1 = "https://www.wettbasis.com/em/em-wetten"
    r1 = requests.get(url1)
    df_list1 = pd.read_html(StringIO(r1.text))  
    df1 = df_list1[1]
    # Spalten umbenennen
    df1=df1.rename(columns={"Unnamed: 0": "Länder", "Unnamed: 1": "bet365", "Unnamed: 2":"Betano",
                      "Unnamed: 3":"Neobet","Unnamed: 4":"bwin","Unnamed: 5":"Oddset",
                      "Unnamed: 6":"Winamax","Unnamed: 7":"Happybet",
                     "Unnamed: 8":"sunmaker","Unnamed: 9":"Bet3000",
                     "Unnamed: 10":"bet-at-home"})
    # Durchschnitt der Wettquoten ermitteln
    df1["Durchschnitt Wettquoten"] = df1.select_dtypes(include="number").mean(axis=1).round(2)
    # FIFA Ranking holen
    url2 = "https://www.betinf.com/fifa_ranking.htm"
    r2 = requests.get(url2)
    df_list2 = pd.read_html(StringIO(r2.text))  
    df2 = df_list2[0]
    # Umbennen der Teams ins deutsche
    df2["Team"] = df2["Team"].replace({
        "France": "Frankreich", "Germany": "Deutschland", "Spain": "Spanien", "Italy": "Italien",
        "Belgium": "Belgien", "Netherlands": "Niederlande", "Denmark": "Dänemark", "Croatia": "Kroatien",
        "Turkiye": "Türkei", "Switzerland": "Schweiz", "Serbia": "Serbien", "Austria": "Österreich",
        "Hungary": "Ungarn", "Scotland": "Schottland", "Poland": "Polen", "Czechia": "Tschechien",
        "Romania": "Rumänien", "Slovenia": "Slowenien", "Albania": "Albanien", "Slovakia": "Slowakei",
        "Georgia": "Georgien"
    })
    # Filter
    teams = ["England", "Frankreich", "Deutschland", "Spanien", "Portugal", "Italien", "Belgien", "Niederlande",
             "Dänemark", "Kroatien", "Türkei", "Schweiz", "Serbien", "Österreich", "Ungarn", "Schottland",
             "Ukraine", "Polen", "Tschechien", "Rumänien", "Slowenien", "Albanien", "Slowakei", "Georgien"]
    df2 = df2[df2["Team"].isin(teams)].reset_index(drop=True)
    df2 = df2.rename(columns={"Team": "Länder"})
    # Zusammenführen beider Dataframes
    df_join = pd.merge(df1, df2, on="Länder", how="inner")
    # Modell
    df_join["Durchschnitt Wettquoten in %"] = round(1 / df_join["Durchschnitt Wettquoten"] * 100, 2)
    df_join["Rang in %"] = round(1 / df_join["Rank"] * 100, 2)
    gewichtung_wetten = 0.8
    gewichtung_fifa_ranking = 0.2
    df_join["Gewichtetes Ranking in %"] = (
        (df_join["Durchschnitt Wettquoten in %"] * gewichtung_wetten)+ (df_join["Rang in %"] * gewichtung_fifa_ranking)).round(2)
    # Ausgewählte Spalten selektieren und sortieren
    df_join =df_join.rename(columns={"Rank": "FIFA Rang"})
    df_final = df_join[["Länder", "Durchschnitt Wettquoten", "FIFA Rang", "Gewichtetes Ranking in %"]]
    df_final = df_final.sort_values(by="Gewichtetes Ranking in %", ascending=False).reset_index(drop=True)
    df_graph = df_final.sort_values(by="Gewichtetes Ranking in %", ascending=True).reset_index(drop=True)
    # Dataframe zu HTML
    df_final_html = df_final.to_html(classes="table table-striped", index=False)
    # Grafik
    fig = px.bar(
        df_graph, 
        x="Gewichtetes Ranking in %", 
        y="Länder", 
        orientation="h", 
        title="Ranking anhand der Wettquoten und des FIFA Rankings",
        color="Gewichtetes Ranking in %",  
        color_continuous_scale="Viridis")
    fig.update_layout(
        xaxis_title="Gewichtetes Ranking in %",
        yaxis_title="Länder",
        margin=dict(l=100, r=20, t=50, b=50),
        coloraxis_showscale=False) 
    config = {"displayModeBar": False} 
    fig_html = pio.to_html(fig, full_html=False, config=config)
    # Text
    additional_text = """
    <p style="margin-top: 12px;">Das Modell berechnet anhand der aktuelllen Wettqouten und des FIFA Rankings die Wahrscheinlichkeit, mit der ein Land Europameister wird.</p>
    <p>● Annahme Wettquoten sind dynamischer und Aussagekräftiger (Gewichtung 80%)</p>
    <p>● FIFA Ranking (Gewichtung 20%)</p>
    <p style="margin-bottom: 14px;">● Gewichtetes Ranking in % gibt die Wahrscheinlichkeit an, dass ein Land Europameister wird</p>
    """
    # Rendering
    return render_template_string('''
    <!doctype html>
    <html lang="en">
      <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">
        <title>EM 2024</title>
        <!-- Bootstrap CSS -->
        <link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.3.1/css/bootstrap.min.css">
        <style>
          th {text-align: left;}
          p {margin-bottom: 3px;}
        </style>
      </head>
      <body>
        <div class="container">
          <h1 class="mt-5">Welches Land wird Europameister 2024?</h1>
          {{ additional_text|safe }}                      
          {{ table|safe }}
          <div>{{ fig_html|safe }}</div>
          <div style="margin-top: 20px;">
          <a href="https://inside.fifa.com/fifa-world-ranking/men">FIFA Ranking</a>
           <br>                                               
        <i>Die Wettquoten stammen unter anderen von folgenden Anbietern: bet365, Betano, Neobet, bwin, Oddset, Winamax, Happybet, sunmaker, Bet3000, bet-at-home.</i>
    </div>
        </div>
      </body>
    </html>
    ''', additional_text=additional_text, table=df_final_html, fig_html=fig_html)

if __name__ == '__main__':
    app.run()
