import pandas as pd
import plotly.graph_objects as go
from dash import Dash, dcc, html, Input, Output, State, callback_context
from dash.exceptions import PreventUpdate

app = Dash(__name__)
server = app.server

df = pd.DataFrame({
    'GESTOR': ['Juan'] * 3,
    'FECHA_GESTION': pd.to_datetime(['2024-06-01'] * 3),
    'LATITUD': [25.6866, 25.6870, 25.6875],
    'LONGITUD': [-100.3161, -100.3170, -100.3180],
    'HORA_GESTION': ['10:00AM', '11:00AM', '12:00PM'],
    'ID_CLIENTE': ['C001', 'C002', 'C003'],
    'RESULTADO': ['PP', 'DP', 'ND'],
    'AP_VAP': [100, 200, 150]
})
df["HORA_ORDEN"] = pd.to_datetime(df["HORA_GESTION"], format="%I:%M%p").dt.time

app.layout = html.Div([
    html.H2("Mapa de Gestiones - Modo Pantalla Completa", style={"textAlign": "center"}),
    html.Button("Pantalla Completa", id="btn-fullscreen"),
    html.Div([
        dcc.Graph(id="mapa-gestiones", style={'height': '90vh', 'width': '100%'})
    ], id="mapa-container")
])

@app.callback(
    Output("mapa-gestiones", "figure"),
    Input("btn-fullscreen", "n_clicks")
)
def mostrar_mapa(n):
    fig = go.Figure()
    fig.add_trace(go.Scattermapbox(
        lat=df["LATITUD"],
        lon=df["LONGITUD"],
        mode='markers+lines',
        marker=dict(size=10, color='blue'),
        hovertext=df["ID_CLIENTE"]
    ))
    fig.update_layout(
        mapbox=dict(
            style="open-street-map",
            zoom=14,
            center=dict(lat=df["LATITUD"].mean(), lon=df["LONGITUD"].mean())
        ),
        margin=dict(l=0, r=0, t=0, b=0)
    )
    return fig

from dash import ClientsideFunction
app.clientside_callback(
    ClientsideFunction(namespace='fullscreen', function_name='activarPantallaCompleta'),
    Output('btn-fullscreen', 'n_clicks'),
    Input('btn-fullscreen', 'n_clicks')
)

if __name__ == '__main__':
    app.run_server(debug=False, port=8080)
