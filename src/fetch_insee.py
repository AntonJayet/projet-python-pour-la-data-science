import requests
import os

def download_insee_comparateur():
    """
    Télécharge automatiquement le fichier des résultats législatives 2022 (2nd tour)
    par commune/subcom depuis DataGouv et le place dans data/raw/
    """
    # URL directe vers le fichier correct
    download_url = "https://www.insee.fr/fr/statistiques/fichier/2521169/base_cc_comparateur_xlsx.zip"
    # Chemin de sauvegarde fixe
    save_path = "data/raw/insee_comparateur.zip"
    os.makedirs(os.path.dirname(save_path), exist_ok=True)

    print("Téléchargement en cours :", download_url)
    r = requests.get(download_url)
    r.raise_for_status()  # Vérifie que le téléchargement a fonctionné

    with open(save_path, "wb") as f:
        f.write(r.content)

    print("✔️ Fichier téléchargé avec succès :", save_path)


if __name__ == "__main__":
    download_insee_comparateur()