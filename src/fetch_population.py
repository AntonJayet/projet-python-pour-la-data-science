import requests
import os

def download_population():
    """
    Télécharge automatiquement le fichier principal du dataset population municipale
    depuis DataGouv et le place dans data/raw/ sous un nom fixe.
    """
    dataset_id = "65b1a75854fb88f787f72944"
    api_url = f"https://www.data.gouv.fr/api/1/datasets/{dataset_id}/"

    # Récupère les métadonnées du dataset
    response = requests.get(api_url)
    if response.status_code != 200:
        raise ValueError(f"Erreur lors de l'accès à l'API : {response.status_code}")

    dataset = response.json()
    resources = dataset.get("resources", [])

    if not resources:
        raise ValueError("Aucune ressource trouvée dans le dataset !")

    # Liste toutes les URLs disponibles (debug)
    print("Ressources disponibles :")
    for i, res in enumerate(resources):
        url = res.get("url")
        if url:
            print(f"{i}: {url}")

    # Prend la première ressource avec une URL valide
    download_url = next((res.get("url") for res in resources if res.get("url")), None)

    if download_url is None:
        raise ValueError("Aucune URL valide trouvée dans le dataset !")

    # 🔴 NOM FIXE DU FICHIER (IMPORTANT)
    save_path = "data/raw/population_communes.xlsx"
    os.makedirs("data/raw", exist_ok=True)

    print("Téléchargement en cours :", download_url)
    r = requests.get(download_url)
    r.raise_for_status()

    with open(save_path, "wb") as f:
        f.write(r.content)

    print("✔️ Fichier téléchargé sous le nom :", save_path)

if __name__ == "__main__":
    download_population()







