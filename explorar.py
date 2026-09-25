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