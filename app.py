import warnings
warnings.filterwarnings("ignore")

import streamlit as st
import pandas as pd
from statsbombpy import sb
import matplotlib.pyplot as plt
from mplsoccer import Pitch

st.set_page_config(page_title="Europa vs América do Sul", layout="wide")

# --- IDs confirmados ---
Torneios = {
    "Copa América 2024": {"competition_id": 223, "season_id": 282, "continente":"América do Sul"},
    "UEFA Euro 2024": {"competition_id": 55, "season_id": 282, "continente":"Europa"},
}

# ---Carregamento com Cache ---
@st.cache_data(show_spinner=False)
def carregar_partidas(cid,sid):
    return sb.matches(competition_id=cid, season_id=sid)

@st.cache_data(show_spinner=False)
def carregar_eventos(match_id):
    return sb.events(match_id=match_id)

def por_partida(t, chave):
    return t[chave] / t["partidas"] if t["partidas"] else 0

@st.cache_data
def carregar_agregados():
    torneios = pd.read_csv("dados_torneios.csv").set_index("torneio")
    jogadores = pd.read_csv("dados_jogadores.csv")
    chutes = pd.read_csv("dados_chutes.csv")
    return torneios, jogadores, chutes

# =====INTERFACE=====
st.title("Futebol: Europa vs América do Sul")
st.caption("Comparativo entre torneios de seleções da Europa e América do Sul em 2024 (Dados StatsBomb)")

df_torneios, df_jogadores, df_chutes = carregar_agregados()

nomes = list(Torneios.keys()) # [Copa America, Euro]

aba1, aba2, aba3, aba4 = st.tabs(
    ["Visao geral", "Estilo de jogo", "Intensidade fisica", "Finalizacao"]
)

# Visão geral
with aba1:
    st.subheader("Media por partida")
    for nome in nomes:
        t = df_torneios.loc[nome]        
        st.markdown(f"### {nome} — {Torneios[nome]['continente']}")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Gols/jogo", f"{por_partida(t, 'gols'):.2f}")
        c2.metric("Chutes/jogo", f"{por_partida(t, 'chutes'):.1f}")
        c3.metric("Passes/jogo", f"{por_partida(t, 'passes'):.0f}")
        c4.metric("Faltas/jogo", f"{por_partida(t, 'faltas'):.1f}")

# Estilo de jogo
with aba2:
    st.subheader("Volume e precisão de passes")
    tabela = []
    for nome in nomes:
        t = df_torneios.loc[nome]
        precisao = 100 * t["passes_certos"] / t["passes"] if t["passes"] else 0
        tabela.append({
            "Torneio": nome,
            "Passes/jogo": round(por_partida(t, "passes")),
            "Precisão (%)": round(precisao, 1),
        })
    df_estilo = pd.DataFrame(tabela).set_index("Torneio")
    st.dataframe(df_estilo)
    st.bar_chart(df_estilo["Passes/jogo"])

#Intensidade física
with aba3:
    st.subheader("Faltas e cartões")
    tabela = []
    for nome in nomes:
        t = df_torneios.loc[nome]
        tabela.append({
            "Torneio": nome,
            "Faltas/jogo": round(por_partida(t, "faltas"), 1),
            "Amarelos/jogo": round(por_partida(t, "amarelos"), 2),
            "Vermelhos (total)": int(t["vermelhos"]),
        })
    df_intensidade = pd.DataFrame(tabela).set_index("Torneio")
    st.dataframe(df_intensidade)

# Finalização
with aba4:
    st.subheader("Mapa de chutes agregado")
    col_a, col_b = st.columns(2)
    for coluna, nome in zip([col_a, col_b], nomes):
        with coluna:
            st.markdown(f"**{nome}**")
            chutes = df_chutes[df_chutes["torneio"] == nome]
            pitch = Pitch(pitch_type="statsbomb", half=True, line_color="black")
            fig, ax = pitch.draw(figsize=(6, 4))
            if not chutes.empty:
                gols = chutes[chutes["gol"]]
                nao = chutes[~chutes["gol"]]
                pitch.scatter(nao["x"], nao["y"], ax=ax, color="gray", s=15, alpha=0.4)
                pitch.scatter(gols["x"], gols["y"], ax=ax, color="red", s=40)
            st.pyplot(fig)
            conv = 100 * len(chutes[chutes["gol"]]) / len(chutes) if len(chutes) else 0
            st.metric("Conversão de chutes (%)", f"{conv:.1f}")
