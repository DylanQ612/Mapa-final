
import pandas as pd
import plotly.graph_objects as go
from dash import Dash, dcc, html, Input, Output, State, callback_context
from dash.exceptions import PreventUpdate
import numpy as np
import urllib
from sqlalchemy import create_engine
from dash import ClientsideFunction

# === CONEXIÓN A BASE SQL SERVER CON PYODBC ===
params = urllib.parse.quote_plus(
    "DRIVER={ODBC Driver 17 for SQL Server};"
    "SERVER=52.167.231.145,51433;"
    "DATABASE=CreditoYCobranza;"
    "UID=credito;"
    "PWD=Cr3d$.23xme"
)
engine = create_engine(f"mssql+pyodbc:///?odbc_connect={params}")

# === QUERY CON JOIN A TABLAS PERMANENTES ===
query = """
SELECT 
    GA.*, 
    TD.DIRECCION, 
    RG.OBSERVACIONES
FROM 
    GESTIONES_APVAP GA
LEFT JOIN 
    Tabla_Domicilios TD 
    ON GA.IDCLIENTE = TD.ID_CLIENTE
LEFT JOIN 
    RPGestiones RG 
    ON GA.IDCLIENTE = RG.IDCliente 
    AND CONVERT(date, GA.FECHAVISITA) = CONVERT(date, RG.FECHAVISITA)
WHERE 
    CONVERT(date, GA.FECHAVISITA) >= DATEADD(day, -7, CONVERT(date, GETDATE()))
    AND GA.CANAL = 'CAMPO'
"""
df = pd.read_sql(query, engine)

# === LIMPIEZA DE DATOS ===
df.columns = df.columns.str.strip().str.upper()
df = df.rename(columns={
    'NOMBREVENDEDOR': 'GESTOR',
    'FECHAVISITA': 'FECHA_GESTION',
    'HORADEGESTION': 'HORA_GESTION',
    'IDCLIENTE': 'ID_CLIENTE',
    'NOMBREDECLIENTE': 'CLIENTE',
    'AP_VAP_FACTURA': 'AP_VAP',
    'ACCION': 'RESULTADO'
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

# === APP DASH ===
app = Dash(__name__)
server = app.server
app.title = "Rutas de Gestores"

app.layout = html.Div(["Tu layout aquí..."])  # Placeholder simplificado

# Puedes pegar el resto del layout y callbacks aquí como ya los tienes definidos.
