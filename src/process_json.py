import json
import os

import utils

project_root_directory = utils.find_root_directory()
DATA_DIR = os.path.join(project_root_directory, "data", "recipes")

data = []

for recipe_category in os.listdir(DATA_DIR):
    with open(os.path.join(DATA_DIR, recipe_category), "r") as f:
        recipes = json.load(f)

    for recipe_name in recipes.keys():
        recipe_data = {}
        recipe_data["url"] = recipes[recipe_name]["url"]
        recipe_data["text"] = f"{recipe_name}\n" + "\n".join(
            [
                (f"{k}\n" + recipes[recipe_name][k])
                for k in recipes[recipe_name].keys()
                if k != "url"
            ]
        )
        data.append(recipe_data)

with open(os.path.join(project_root_directory, "data", "all-recipes.json"), "w") as f:
    json.dump(data, f, indent=4)
