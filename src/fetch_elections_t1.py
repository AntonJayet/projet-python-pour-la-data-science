import requests
import os

def download_elections():
    """
    Télécharge automatiquement le fichier des résultats législatives 2022 (2nd tour)
    par commune/subcom depuis DataGouv et le place dans data/raw/
    """
    # URL directe vers le fichier correct
    download_url = "https://static.data.gouv.fr/resources/elections-legislatives-des-30-juin-et-7-juillet-2024-resultats-definitifs-du-1er-tour/20240711-075030/resultats-definitifs-par-communes.xlsx"
    # Chemin de sauvegarde fixe
    save_path = "data/raw/elections_t1_legislatives.xlsx"
    os.makedirs(os.path.dirname(save_path), exist_ok=True)

    print("Téléchargement en cours :", download_url)
    r = requests.get(download_url)
    r.raise_for_status()  # Vérifie que le téléchargement a fonctionné

    with open(save_path, "wb") as f:
        f.write(r.content)

    print("✔️ Fichier téléchargé avec succès :", save_path)


if __name__ == "__main__":
    download_elections()
