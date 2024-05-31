from flask import Flask, render_template_string
import pandas as pd
import requests

app = Flask(__name__)

@app.route('/')
def display_table():
    # Wettquoten holen
    url1 = "https://www.wettbasis.com/em/em-wetten"
    r1 = requests.get(url1)
    df_list1 = pd.read_html(r1.text)
    df1 = df_list1[1]
    # Spalten umbenennen
    df1 = df1.rename(columns={"Unnamed: 0": "Länder", "Unnamed: 1": "bet365", "Unnamed: 2": "Oddset",
                              "Unnamed: 3": "bwin", "Unnamed: 4": "Betano", "Unnamed: 5": "bet-at-home",
                              "Unnamed: 6": "Interwetten"})
    # Durchschnitt der Wettquoten ermitteln
    df1["Durchschnitt Wettquoten"] = df1.select_dtypes(include="number").mean(axis=1).round(2)
    # FIFA Ranking holen
    url2 = "https://www.betinf.com/fifa_ranking.htm"
    r2 = requests.get(url2)
    df_list2 = pd.read_html(r2.text)
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
    df_final = df_join[["Länder", "bet365", "Oddset", "bwin", "Betano", "bet-at-home", "Interwetten",
                        "Durchschnitt Wettquoten", "FIFA Rang", "Gewichtetes Ranking in %"]]
    df_final = df_final.sort_values(by="Gewichtetes Ranking in %", ascending=False).reset_index(drop=True)
    # Dataframe zu HTML
    df_final_html = df_final.to_html(classes="table table-striped", index=False)
    #Text
    additional_text = """
    <p>- Annahme Wettquoten sind dynamischer und Aussagekräftiger (Gewichtung 80%)</p>
    <p>- FIFA Ranking (Gewichtung 20%)</p>
    <p>- Gewichtetes Ranking in % gibt die Wahrschleichkeit an, dass ein Land Europameister wird</p>
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
          th {
            text-align: left;
          }
        </style>
      </head>
      <body>
        <div class="container">
          <h1 class="mt-5">Europameisterschaft 2024</h1>
          {{ additional_text|safe }}                      
          {{ table|safe }}
        </div>
      </body>
    </html>
    ''', additional_text=additional_text, table=df_final_html)

if __name__ == '__main__':
    app.run(debug=True)

