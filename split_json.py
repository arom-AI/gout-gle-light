import os
import json

# Charger le fichier d'origine
with open("data/database.json", "r", encoding="utf-8") as f:
    full_data = json.load(f)

# Paramètres
chunk_size = 500  # nombre d’objets par fichier
output_dir = "data_split"
os.makedirs(output_dir, exist_ok=True)

# Découper
for i in range(0, len(full_data), chunk_size):
    chunk = full_data[i:i + chunk_size]
    part_name = f"part_{i//chunk_size:03}.json"
    with open(os.path.join(output_dir, part_name), "w", encoding="utf-8") as f:
        json.dump(chunk, f, ensure_ascii=False, indent=2)

print("✅ Fichiers JSON découpés enregistrés dans", output_dir)
