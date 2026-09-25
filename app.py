import warnings
warnings.filterwarnings("ignore")

import streamlit as st
import pandas as pd
from statsbombpy import sb
import matplotlib.pyplot as plt
from mplsoccer import Pitch
from statsbombpy import sb

st.set_page_config(page_title="Europa vs América do Sul", layout="wide")

# --- IDs confirmados ---
Torneios = {
    "UEFA Euro 2024": {"competition_id": 223, "season_id": 282, "continente":"América do Sul"},
    "Copa América 2024": {"competition_id": 55, "season_id": 282, "continente":"Europa"},
}

# ---Carregamento com Cache ---
@st.cache_data(show_spinner=False)
def carregar_partidas(cid,sid):
    return sb.matches(competition_id=cid, season_id=sid)

@st.cache_data(show_spinner=False)
def carregar_eventos(match_id):
    return sb.events(match_id=match_id)

@st.cache_data(show_spinner=False)
#Percorrer todas as partidas do torneio e soma as estatiscas
def agregar_torneio(cid,sid):
    partidas = carregar_partidas(cid,sid)
    match_ids = partidas['match_id'].tolist()

    tot={"gols": 0, "chutes": 0, "passes": 0, "passes_certos": 0,
        "faltas": 0, "amarelos": 0, "vermelhos": 0}

    for mid in match_ids:
        ev = carregar_eventos(mid)

        shots = ev[ev['type_name'] == 'Shot']
        passes = ev[ev['type_name'] == 'Pass']

        tot["chutes"] += len(shots)
        tot["gols"] += int((shots['shot_outcome'] == 'Goal').sum()) if 'shot_outcome' in ev.columns else 0
        tot["passes"] += len(passes)
        tot["passes_certos"] += int(passes["pass_outcome"].isna().sum()) if "pass_outcome" in ev.columns else len(passes)
        tot["faltas"] += int((ev["type"] == "Foul Committed").sum())

        if "foul_committed_card" in ev.columns:
            tot["amarelos"]  += int((ev["foul_committed_card"] == "Yellow Card").sum())
            tot["vermelhos"] += int(ev["foul_committed_card"].isin(["Red Card", "Second Yellow"]).sum())
    tot[partidas] = len(match_ids)
    return tot

@st.cache_data(show_spinner=False)
def coletar_chutes(cid,sid):
    partidas = carregar_partidas(cid,sid)
    linhas = []
    for mid in partidas['match_id'].tolist():
        ev = carregar_eventos(mid)
        chutes = ev[ev['type_name'] == 'Shot']
        if "location" not in chutes.columns:
            continue
        for _, r in chutes.iterrows():
            loc = r["location"]
            if isinstance(loc, list) and len(loc) == 2:
                linhas.append({
                    "x":loc[0],
                    "y":loc[1],
                    "gol":r.get("shot_outcome") == "Goal",
                    })
    return pd.DataFrame(linhas)

def por_partida(tot, chave):
    return tot[chave] / tot["partidas"] if tot["partidas"] else 0
