import json, os, glob

folder = r"C:\Users\Елена\Documents\projects\diplom_skypro_testing\postman_export"

def walk(items, depth=0):
    for it in items:
        tests = len(it.get("event", []))
        print("    " * depth + f"{it['name']} — тестов: {tests}")
        if "item" in it:
            walk(it["item"], depth + 1)

for path in glob.glob(os.path.join(folder, "*.json")):
    with open(path, encoding="utf-8") as f:
        d = json.load(f)
    if "info" in d:
        print(f"\n=== {d['info']['name']} ===")
        walk(d.get("item", []))
