import requests
import os
from urllib.parse import urlparse

def download_population():
    """
    Télécharge automatiquement le fichier principal du dataset population municipale
    depuis DataGouv et le place dans data/raw/.
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

    # Liste toutes les URLs disponibles
    print("Ressources disponibles :")
    for i, res in enumerate(resources):
        url = res.get('url')
        if url:
            print(f"{i}: {url}")

    # Prend la première ressource avec URL
    download_url = next((res.get('url') for res in resources if res.get('url')), None)

    if download_url is None:
        raise ValueError("Aucune URL trouvée dans le dataset !")

    # Détermine le nom du fichier depuis l'URL
    filename = os.path.basename(urlparse(download_url).path)
    save_path = os.path.join("data/raw", filename)
    os.makedirs(os.path.dirname(save_path), exist_ok=True)

    print("Téléchargement en cours :", download_url)
    r = requests.get(download_url)
    if r.status_code != 200:
        raise ValueError(f"Erreur pendant le téléchargement : {r.status_code}")

    with open(save_path, "wb") as f:
        f.write(r.content)

    print("✔️ Fichier téléchargé dans :", save_path)

if __name__ == "__main__":
    download_population()







