import requests
import os

def download_elections():
    dataset_id = "a3c524fd-eed6-4be2-99ca-bc3920824953"  # à remplacer par l'ID réel
    api_url = f"https://www.data.gouv.fr/api/1/datasets/{dataset_id}/"

    # Récupérer les métadonnées
    response = requests.get(api_url)
    response.raise_for_status()
    dataset = response.json()
    resources = dataset.get("resources", [])

    if not resources:
        raise ValueError("Aucune ressource trouvée !")

    # On prend la première ressource CSV disponible
    download_url = next((res.get("url") for res in resources if res.get("url") and "csv" in res.get("format","").lower()), None)

    if download_url is None:
        raise ValueError("Aucune ressource CSV trouvée !")

    # Nom fixe
    save_path = "data/raw/elections_legislatives.csv"
    os.makedirs("data/raw", exist_ok=True)

    print("Téléchargement en cours :", download_url)
    r = requests.get(download_url)
    r.raise_for_status()

    with open(save_path, "wb") as f:
        f.write(r.content)

    print("✔️ Fichier téléchargé :", save_path)

if __name__ == "__main__":
    download_elections()

