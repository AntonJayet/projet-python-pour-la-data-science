import requests
import os

def download_population():
    dataset_id = "65b1a75854fb88f787f72944"
    api_url = f"https://www.data.gouv.fr/api/1/datasets/{dataset_id}/"

    # Récupère les métadonnées du dataset
    dataset = requests.get(api_url).json()
    resources = dataset.get("resources", [])

    if not resources:
        raise ValueError("Aucune ressource trouvée dans le dataset !")

    # Affiche les ressources pour debug
    print("Ressources disponibles :")
    for i, res in enumerate(resources):
        print(f"{i}: {res['name']} ({res['format']}) -> {res['url']}")

    # Cherche XLS ou XLSX
    resource = next(
        (res for res in resources if res['format'].lower() in ['xls', 'xlsx']),
        None
    )

    if resource is None:
        raise ValueError("Aucun fichier XLS/XLSX trouvé dans le dataset !")

    download_url = resource["url"]
    save_path = "data/raw/population_communes.xlsx"  # change extension XLS/XLSX
    os.makedirs(os.path.dirname(save_path), exist_ok=True)

    # Télécharger le fichier
    print("Téléchargement en cours :", download_url)
    r = requests.get(download_url)
    if r.status_code != 200:
        raise ValueError(f"Erreur pendant le téléchargement : {r.status_code}")

    with open(save_path, "wb") as f:
        f.write(r.content)

    print("✔️ Fichier téléchargé dans :", save_path)

if __name__ == "__main__":
    download_population()


