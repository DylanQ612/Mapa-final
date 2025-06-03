import dash
from dash import dcc, html, Input, Output
import pandas as pd
import plotly.graph_objects as go
from sqlalchemy import create_engine, URL
import toml

# Leer credenciales desde secrets.toml
secrets = toml.load("secrets.toml")
server = secrets["server"]
database = secrets["database"]
username = secrets["username"]
password = secrets["password"]

connection_url = URL.create(
    "mssql+pyodbc",
    username=username,
    password=password,
    host=server,
    database=database,
    query={"driver": "ODBC Driver 17 for SQL Server"}
)
engine = create_engine(connection_url)

def cargar_datos():
    query = """SELECT * FROM GESTIONES_APVAP
               WHERE CONVERT(date, FECHAVISITA) = DATEADD(day, -14, CONVERT(date, GETDATE()))"""
    df = pd.read_sql(query, engine)
    df.columns = df.columns.str.strip().str.upper()
    df = df.rename(columns={
        'NOMBREVENDEDOR': 'GESTOR',
        'FECHAVISITA': 'FECHA_GESTION',
        'HORADEGESTION': 'HORA_GESTION',
        'IDCLIENTE': 'ID_CLIENTE',
        'NOMBREDECLIENTE': 'CLIENTE',
        'POSTURA': 'RESULTADO'
    })
    df = df.dropna(subset=["LATITUD", "LONGITUD", "GESTOR", "HORA_GESTION", "FECHA_GESTION"])
    df = df[(df["LATITUD"] != 0) & (df["LONGITUD"] != 0)]
    df["LATITUD"] = pd.to_numeric(df["LATITUD"], errors='coerce')
    df["LONGITUD"] = pd.to_numeric(df["LONGITUD"], errors='coerce')
    df = df.dropna(subset=["LATITUD", "LONGITUD"])
    df["FECHA_GESTION"] = pd.to_datetime(df["FECHA_GESTION"])
    df["HORA_ORDEN"] = pd.to_datetime(df["HORA_GESTION"], format="%I:%M%p", errors='coerce').dt.time
    df["EFECTIVA"] = df["RESULTADO"].apply(lambda x: "Efectiva" if x in ["PP", "DP"] else "No Efectiva")
    df["COLOR"] = df["EFECTIVA"].map({"Efectiva": "green", "No Efectiva": "red"})
    return df

app = dash.Dash(__name__)
server = app.server

app.layout = html.Div([
    html.H1("Seguimiento de Gestiones de Cobranza"),
    dcc.Dropdown(id="gestor-dropdown"),
    dcc.Dropdown(id="fecha-dropdown"),
    dcc.Graph(id="mapa")
])

@app.callback(
    Output("gestor-dropdown", "options"),
    Output("gestor-dropdown", "value"),
    Input("mapa", "id")
)
def actualizar_gestores(_):
    df = cargar_datos()
    opciones = [{"label": g, "value": g} for g in sorted(df["GESTOR"].unique())]
    return opciones, opciones[0]["value"] if opciones else None

@app.callback(
    Output("fecha-dropdown", "options"),
    Output("fecha-dropdown", "value"),
    Input("gestor-dropdown", "value")
)
def actualizar_fechas(gestor):
    if gestor:
        df = cargar_datos()
        fechas = df[df["GESTOR"] == gestor]["FECHA_GESTION"].dt.strftime("%Y-%m-%d").unique()
        return [{"label": f, "value": f} for f in fechas], fechas[0] if len(fechas) else None
    return [], None

@app.callback(
    Output("mapa", "figure"),
    Input("gestor-dropdown", "value"),
    Input("fecha-dropdown", "value")
)
def actualizar_mapa(gestor, fecha):
    df = cargar_datos()
    if gestor and fecha:
        datos = df[(df["GESTOR"] == gestor) & (df["FECHA_GESTION"].dt.strftime("%Y-%m-%d") == fecha)]
        datos = datos.sort_values("HORA_ORDEN").reset_index(drop=True)
        datos["hover"] = datos.apply(lambda row: f"ID: {row['ID_CLIENTE']}<br>Resultado: {row['RESULTADO']}", axis=1)
        fig = go.Figure(go.Scattermapbox(
            lat=datos["LATITUD"],
            lon=datos["LONGITUD"],
            mode='markers+lines',
            marker=dict(size=10, color=datos["COLOR"]),
            text=datos["hover"],
            hoverinfo='text'
        ))
        fig.update_layout(
            mapbox=dict(style="open-street-map", zoom=12,
                        center=dict(lat=datos["LATITUD"].mean(), lon=datos["LONGITUD"].mean())),
            margin=dict(l=0, r=0, t=0, b=0)
        )
        return fig
    return go.Figure()

if __name__ == "__main__":
    app.run_server(debug=True)
