import pandas as pd

# Chemin relatif vers ton fichier Excel
file_path = "data/raw/resultats-par-niveau-subcom-t2-france-entiere.xlsx"

# Lire le fichier Excel
df = pd.read_excel(file_path)

# Afficher les premières lignes pour vérifier
print(df.head())
print(df.info())


