# src/compute_density_vote.py
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
import matplotlib.pyplot as plt
import seaborn as sns
import os

# ---- CONFIG ----
# chemins relatifs (modifie si besoin)
ELECTION_FILE = "data\raw\POPULATION_MUNICIPALE_COMMUNES_FRANCE (1).xlsx"   # fichier résultats (commune-level)
INSEE_POP_FILE = "data/raw/insee_population_commune.csv"     # population par commune (code_insee, population)
COMMUNES_GEO = "data/raw/communes_geo.geojson"               # geometry communes (geojson/shp)
CIRCOS_GEO = "data/raw/circonscriptions_geo.geojson"         # geometry circonscriptions (geojson/shp)

OUTPUT_PROCESSED = "data/processed/legislatives_density_by_circo.csv"

# Choix du parti / variable d'intérêt (modifie le label selon ton fichier)
# Si tu veux la part de RN par ex, mets la chaîne correspondante telle qu'elle apparait dans ton fichier.
PARTY_LABEL = "RN"   # <-- modifie selon ton fichier des résultats

# ---- 1) Lire les données ----
print("Lire données...")
# lire résultats électoraux (par commune). Ajuste la lecture si CSV
if ELECTION_FILE.endswith(".xlsx") or ELECTION_FILE.endswith(".xls"):
    df_el = pd.read_excel(ELECTION_FILE)
else:
    df_el = pd.read_csv(ELECTION_FILE)

# lire population INSEE (table simplifiée : code_insee, population)
df_pop = pd.read_csv(INSEE_POP_FILE, dtype={"code_insee": str})

# lire géométries
gdf_communes = gpd.read_file(COMMUNES_GEO)
gdf_circos = gpd.read_file(CIRCOS_GEO)

# ---- 2) Préparer / standardiser les clés ----
print("Préparer clés...")
# standardise les codes INSEE (colonnes peuvent s'appeler différemment)
# adapte les noms: communément 'code_insee' ou 'COM' / 'code' selon tes fichiers
if "code_insee" not in df_pop.columns:
    # essai commun
    possible = [c for c in df_pop.columns if c.lower().startswith("insee") or c.lower().startswith("com")]
    if possible:
        df_pop = df_pop.rename(columns={possible[0]: "code_insee"})
if "code_insee" not in gdf_communes.columns:
    possible = [c for c in gdf_communes.columns if c.lower().startswith("insee") or c.lower().startswith("com")]
    if possible:
        gdf_communes = gdf_communes.rename(columns={possible[0]: "code_insee"})

# forcer type str et zero-pad si nécessaire (5 chars)
df_pop["code_insee"] = df_pop["code_insee"].astype(str).str.zfill(5)
gdf_communes["code_insee"] = gdf_communes["code_insee"].astype(str).str.zfill(5)

# ---- 3) Calcul population par commune (si nécessaire) ----
# Si ton fichier INSEE a déjà la population municipale colonne 'population', adapte ici
if "population" not in df_pop.columns:
    # cherche une colonne candidate
    possible = [c for c in df_pop.columns if "pop" in c.lower()]
    if possible:
        df_pop = df_pop.rename(columns={possible[0]: "population"})
    else:
        raise ValueError("Impossible de trouver la colonne population dans le fichier INSEE.")

# ---- 4) Assigner chaque commune à une circonscription ----
print("Associer communes → circonscription (jointure spatiale)...")

# Vérifier CRS et uniformiser
if gdf_communes.crs != gdf_circos.crs:
    gdf_communes = gdf_communes.to_crs(gdf_circos.crs)

# Si gdf_communes n'a pas de géométrie (ex: seulement centroids), essayer créer à partir lat/lon:
if gdf_communes.geometry.isnull().all():
    if "longitude" in gdf_communes.columns and "latitude" in gdf_communes.columns:
        gdf_communes["geometry"] = gpd.points_from_xy(gdf_communes.longitude, gdf_communes.latitude)
        gdf_communes = gdf_communes.set_geometry("geometry")
    else:
        raise ValueError("Les géométries des communes sont manquantes.")

# join spatial: chaque commune prend l'id de la circonscription qui le contient
gdf_join = gpd.sjoin(gdf_communes, gdf_circos[["geometry", "code_circo"]], how="left", predicate="within")
# note: adapte 'code_circo' au nom réel de la colonne des circonscriptions

# Si la colonne code_circo a un autre nom, détecte et renomme:
if "code_circo" not in gdf_join.columns:
    possible = [c for c in gdf_circos.columns if "circ" in str(c).lower() or "circo" in str(c).lower() or "num" in str(c).lower()]
    if possible:
        gdf_circos = gdf_circos.rename(columns={possible[0]: "code_circo"})
        gdf_join = gpd.sjoin(gdf_communes, gdf_circos[["geometry", "code_circo"]], how="left", predicate="within")
    else:
        # si aucune colonne, on prend l'index comme identifiant
        gdf_circos = gdf_circos.reset_index().rename(columns={"index": "code_circo"})
        gdf_join = gpd.sjoin(gdf_communes, gdf_circos[["geometry", "code_circo"]], how="left", predicate="within")

# ---- 5) Agréger population et aire par circonscription ----
print("Agrégation population et calcul des surfaces...")
# merge population dans gdf_join
gdf_join = gdf_join.merge(df_pop[["code_insee", "population"]], on="code_insee", how="left")

# aire circonscription (km2) : calculer à partir du géodataframe des circonscriptions
# convertir en projection métrique si nécessaire (ex: EPSG:2154 pour France)
# si CRS géographique (deg) → projeter temporairement pour area en m2
gdf_circos_proj = gdf_circos.to_crs(epsg=2154)
gdf_circos_proj["area_km2"] = gdf_circos_proj.geometry.area / 1e6
# garder mapping code_circo -> area_km2
circo_area = gdf_circos_proj[["code_circo", "area_km2"]].copy()

# population par circo : sommer population des communes
pop_by_circo = gdf_join.groupby("code_circo", as_index=False)["population"].sum().rename(columns={"population": "pop_total"})

# joindre aire
pop_by_circo = pop_by_circo.merge(circo_area, on="code_circo", how="left")

# densité
pop_by_circo["density_hab_km2"] = pop_by_circo["pop_total"] / pop_by_circo["area_km2"]

# ---- 6) Agréger résultats électoraux par circonscription ----
print("Agrégation des résultats électoraux par circonscription...")
# df_el doit contenir au minimum : code_insee ou code_commune, et colonnes de voix par parti.
# Exemple: colonnes ['code_insee', 'parti', 'voix'] — si ton fichier est en format "long", on pivotera.
# On détecte le format et on calcule la part du PARTY_LABEL

# Standardiser code_insee dans df_el
if "code_insee" not in df_el.columns:
    poss = [c for c in df_el.columns if "insee" in c.lower() or "com" in c.lower()]
    if poss:
        df_el = df_el.rename(columns={poss[0]: "code_insee"})
df_el["code_insee"] = df_el["code_insee"].astype(str).str.zfill(5)

# Si df_el contient une colonne 'parti' et 'voix' (format long), on va pivot
if ("parti" in df_el.columns) and ("voix" in df_el.columns):
    pivot = df_el.pivot_table(index="code_insee", columns="parti", values="voix", aggfunc="sum", fill_value=0).reset_index()
    df_votes_commune = pivot
else:
    # sinon on suppose que le fichier a des colonnes "voix_PARTI" ou "parti_X" ; adapte ici si besoin
    df_votes_commune = df_el.copy()

# joindre votes (par commune) à gdf_join (commune->circo)
gdf_votes = gdf_join.merge(df_votes_commune, on="code_insee", how="left")

# sommer par circonscription : toutes colonnes numériques de votes sont sommées
vote_cols = [c for c in gdf_votes.columns if c not in ["index_right","geometry","code_insee","population","code_circo"] and pd.api.types.is_numeric_dtype(gdf_votes[c])]
# safer: detect columns that correspond to partis (strings) in df_votes_commune
if "code_insee" in df_votes_commune.columns:
    vote_cols = [c for c in df_votes_commune.columns if c != "code_insee"]

votes_by_circo = gdf_votes.groupby("code_circo")[vote_cols].sum().reset_index()

# calculer part de vote du PARTY_LABEL
if PARTY_LABEL not in votes_by_circo.columns:
    raise ValueError(f"Le label de parti '{PARTY_LABEL}' n'a pas été trouvé parmi les colonnes de votes : {votes_by_circo.columns.tolist()}")

# total voix par circo (somme sur toutes colonnes de partis détectées)
votes_by_circo["total_voix"] = votes_by_circo[vote_cols].sum(axis=1)
votes_by_circo["part_{}".format(PARTY_LABEL)] = votes_by_circo[PARTY_LABEL] / votes_by_circo["total_voix"]

# ---- 7) Joindre population/densité et votes ----
print("Joindre densité et part de vote...")
df_final = pop_by_circo.merge(votes_by_circo[["code_circo", "part_{}".format(PARTY_LABEL), "total_voix"]], on="code_circo", how="left")

# sauvegarder
os.makedirs(os.path.dirname(OUTPUT_PROCESSED), exist_ok=True)
df_final.to_csv(OUTPUT_PROCESSED, index=False)
print(f"Fichier sauvegardé : {OUTPUT_PROCESSED}")

# ---- 8) Tracer la courbe densité vs part de vote ----
print("Tracer graphique...")
plt.figure(figsize=(8,6))
sns.scatterplot(data=df_final, x="density_hab_km2", y="part_{}".format(PARTY_LABEL))
# ajouter un lissage / regression lineaire
sns.regplot(data=df_final, x="density_hab_km2", y="part_{}".format(PARTY_LABEL), scatter=False, lowess=True)
plt.xscale('log')  # souvent utile de loger la densité
plt.xlabel("Densité (hab / km²) [échelle log]")
plt.ylabel(f"Part du vote - {PARTY_LABEL}")
plt.title(f"Densité vs part de vote ({PARTY_LABEL}) par circonscription")
plt.tight_layout()
plt.savefig("reports/figures/density_vs_vote.png", dpi=300)
plt.show()

