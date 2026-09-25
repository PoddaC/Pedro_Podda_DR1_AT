from statsbombpy import sb
import warnings
warnings.filterwarnings("ignore")

comps = sb.competitions()

#Filtrar torneios de 2024 - Masculino
filtro = comps[(comps['competition_gender'] == 'male') & (comps['season_name'] == '2024')]

print(filtro[['competition_id', 'competition_name', 'season_name']].to_string())

for _, linha in filtro.iterrows():
    cid = int(linha['competition_id'])
    sid = int(linha['season_id'])
    nome = linha['competition_name']
    season = linha['season_name']
    try:
        qtd = len(sb.matches(competition_id=cid, season_id=sid))
    except Exception:
        qtd = "-"
    print(f"{nome:35} | {season:10} | comp={cid:4} | season={sid:4} | {qtd} partidas")


# carrega as partidas da Euro 2024 (comp=55, season=282)
partidas = sb.matches(competition_id=55, season_id=282)

# pega o primeiro match_id e baixa os eventos
primeiro_id = partidas["match_id"].iloc[0]
ev = sb.events(match_id=primeiro_id)

# inspeciona as colunas reais
print("Tipos de evento:", ev["type"].unique())
print("Existe 'type_name'?:", "type_name" in ev.columns)
print("Colunas de cartão:", [c for c in ev.columns if "card" in c])
print("Existe 'shot_outcome'?:", "shot_outcome" in ev.columns)