# El contenido ya fue generado antes; se vuelve a guardar tras el reset.
import pandas as pd
import plotly.graph_objects as go
from dash import Dash, dcc, html, Input, Output, State, callback_context
from dash.exceptions import PreventUpdate
import numpy as np
import pyodbc
from sqlalchemy import create_engine, URL

server = '52.167.231.145,51433'
database = 'CreditoYCobranza'
username = 'credito'
password = 'Cr3d$.23xme'

connection_url = URL.create(
    "mssql+pyodbc",
    username=username,
    password=password,
    host=server,
    database=database,
    query={"driver": "ODBC Driver 17 for SQL Server"}
)
engine = create_engine(connection_url)

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
df["EFECTIVA"] = np.where(df["RESULTADO"].isin(["PP", "DP"]), "Efectiva", "No Efectiva")
df["COLOR"] = np.where(df["EFECTIVA"] == "Efectiva", "green", "red")
df = df.sort_values(by=["GESTOR", "FECHA_GESTION", "HORA_ORDEN"])

app = Dash(__name__)
server = app.server
app.title = "Rutas de Gestores"

app.layout = html.Div([
    html.H1("Seguimiento de Gestiones de Cobranza", style={'textAlign': 'center'}),
    html.Div([
        html.Div([
            html.Label("Seleccione el Gestor:"),
            dcc.Dropdown(
                id="gestor-dropdown",
                options=[{"label": g, "value": g} for g in sorted(df["GESTOR"].unique())],
                placeholder="Seleccione un gestor..."
            )
        ], style={'width': '30%', 'display': 'inline-block', 'padding': '10px'}),
        html.Div([
            html.Label("Seleccione la Fecha:"),
            dcc.Dropdown(id="fecha-dropdown")
        ], style={'width': '30%', 'display': 'inline-block', 'padding': '10px'}),
    ], style={'padding': '20px', 'backgroundColor': '#f9f9f9'}),
    html.Div([
        html.Button("Anterior", id="btn-anterior", n_clicks=0),
        html.Button("Siguiente", id="btn-siguiente", n_clicks=0),
        html.Div(id="contador-puntos", style={'display': 'inline-block', 'marginLeft': '20px', 'fontWeight': 'bold'})
    ], style={'textAlign': 'center', 'margin': '20px 0'}),
    dcc.Store(id="store-datos"),
    dcc.Store(id="store-indice", data=1),
    dcc.Graph(id="mapa-gestiones", style={'height': '75vh'})
])

@app.callback(
    Output("fecha-dropdown", "options"),
    Output("fecha-dropdown", "value"),
    Input("gestor-dropdown", "value")
)
def actualizar_fechas(gestor):
    if not gestor:
        return [], None
    filtro = df[df["GESTOR"] == gestor]
    fechas = filtro["FECHA_GESTION"].dt.strftime("%Y-%m-%d").unique()
    opciones = [{"label": f, "value": f} for f in sorted(fechas)]
    return opciones, opciones[-1]["value"] if opciones else None

@app.callback(
    Output("store-datos", "data"),
    Output("store-indice", "data"),
    Output("contador-puntos", "children"),
    Input("gestor-dropdown", "value"),
    Input("fecha-dropdown", "value"),
    Input("btn-anterior", "n_clicks"),
    Input("btn-siguiente", "n_clicks"),
    State("store-indice", "data")
)
def manejar_datos_y_indice(gestor, fecha, n_ant, n_sig, indice_actual):
    ctx = callback_context
    triggered_id = ctx.triggered[0]["prop_id"].split(".")[0] if ctx.triggered else None
    if not gestor or not fecha:
        raise PreventUpdate

    datos_filtrados = df[(df["GESTOR"] == gestor) & 
                         (df["FECHA_GESTION"].dt.strftime("%Y-%m-%d") == fecha)]
    datos_ordenados = datos_filtrados.sort_values("HORA_ORDEN").reset_index(drop=True).to_dict("records")
    total = len(datos_ordenados)
    if total == 0:
        return [], 0, "Sin datos"

    if triggered_id in ["gestor-dropdown", "fecha-dropdown"]:
        nuevo_indice = 1
    elif triggered_id == "btn-siguiente":
        nuevo_indice = min(indice_actual + 1, total)
    elif triggered_id == "btn-anterior":
        nuevo_indice = max(1, indice_actual - 1)
    else:
        nuevo_indice = indice_actual

    return datos_ordenados, nuevo_indice, f"Punto {nuevo_indice} de {total}"

@app.callback(
    Output("mapa-gestiones", "figure"),
    Input("store-datos", "data"),
    Input("store-indice", "data")
)
def actualizar_mapa(datos_filtrados, indice_actual):
    if not datos_filtrados or indice_actual is None:
        return go.Figure()

    datos = pd.DataFrame.from_records(datos_filtrados).reset_index(drop=True)
    total = len(datos)
    if total == 0 or indice_actual < 1 or indice_actual > total:
        return go.Figure()

    lat_centro = datos["LATITUD"].mean()
    lon_centro = datos["LONGITUD"].mean()

    datos["HOVER_TEXT"] = datos.apply(
        lambda row: (
            f"<b>Gestión #{int(row.name) + 1}</b><br>"
            f"<b>Gestor:</b> {row.get('GESTOR', '')}<br>"
            f"<b>ID:</b> {row.get('ID_CLIENTE', '')}<br>"
            f"<b>Hora:</b> {row.get('HORA_GESTION', '')}<br>"
            f"<b>Tipo:</b> {'Presencial' if str(row.get('ACCION', '')).strip().upper() in ['VISITA A CASA', 'VISITA REFERENCIA'] else 'Virtual'}<br>"
            f"<b>Resultado:</b> {row.get('RESULTADO', '')}<br>"
        ), axis=1
    )

    fig = go.Figure()

    fig.add_trace(go.Scattermapbox(
        lat=datos["LATITUD"],
        lon=datos["LONGITUD"],
        mode='markers',
        marker=dict(size=10, color='lightgray', opacity=0.4),
        hoverinfo='skip'
    ))

    fig.add_trace(go.Scattermapbox(
        lat=datos["LATITUD"],
        lon=datos["LONGITUD"],
        mode='lines',
        line=dict(width=1, color='gray'),
        hoverinfo='skip'
    ))

    if indice_actual > 1:
        fig.add_trace(go.Scattermapbox(
            lat=datos["LATITUD"].iloc[:indice_actual],
            lon=datos["LONGITUD"].iloc[:indice_actual],
            mode='lines',
            line=dict(width=2, color='blue'),
            hoverinfo='skip'
        ))

        anteriores = datos.iloc[:indice_actual - 1]
        fig.add_trace(go.Scattermapbox(
            lat=anteriores["LATITUD"],
            lon=anteriores["LONGITUD"],
            mode='markers',
            marker=dict(size=12, color='blue'),
            hovertext=anteriores["HOVER_TEXT"],
            hoverinfo='text',
            opacity=0.8
        ))

    actual = datos.iloc[indice_actual - 1]
    fig.add_trace(go.Scattermapbox(
        lat=[actual["LATITUD"]],
        lon=[actual["LONGITUD"]],
        mode='markers+text',
        marker=dict(size=14, color='purple'),
        text=[str(indice_actual)],
        textposition="top center",
        textfont=dict(color='black', size=14),
        hovertext=[actual["HOVER_TEXT"]],
        hoverinfo='text',
        opacity=1
    ))

    fig.update_layout(
        mapbox=dict(
            style="open-street-map",
            zoom=12,
            center=dict(lat=lat_centro, lon=lon_centro)
        ),
        margin=dict(r=0, t=0, l=0, b=0),
        hovermode='closest',
        uirevision="persistente"
    )

    return fig

if __name__ == '__main__':
    app.run(debug=False, port=8080)
