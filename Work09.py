
import json
import operator
from google.colab import files

''' Parameters '''
FIELDS = {"length_mm": (int, float), "color": str, "mold": bool}
VALID_COLORS = ["green", "light", "brown", "dark"]
REQUIRED = ["mold"]
OPS = {"==": operator.eq, "!=": operator.ne, ">": operator.gt,
       ">=": operator.ge, "<": operator.lt, "<=": operator.le,
       "in": lambda a, b: a in b, "not in": lambda a, b: a not in b}

''' Uploading files function'''
def upload_json(label):
    print("Select the", label, "file")
    uploaded = files.upload()
    if not uploaded:
        print("No file selected.")
        return None
    name = list(uploaded.keys())[0]
    try:
        with open(name, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        print("The file is not valid JSON.")
        return None
    if not isinstance(data, list):
        print("The file must contain a list.")
        return None
    return data

''' Downloading files function '''
def download_json(data, name):
    with open(name, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
    files.download(name)

''' Rules checker '''
def check_rules(rules):
    valid = []
    for r in rules:
        try:
            ok = "then" in r and all(
                c["field"] in FIELDS and c["op"] in OPS for c in r["if"])
        except (KeyError, TypeError):
            ok = False
        if ok:
            valid.append(r)
        else:
            name = r.get("name", "?") if isinstance(r, dict) else "?"
            print("Ignored invalid rule:", name)
    return valid

''' Validation function '''
def validate(data):
    problems = []
    for f in FIELDS:
        data.setdefault(f, None)
    for f, value in data.items():
        if f in FIELDS and value is not None:
            if isinstance(value, bool) != (FIELDS[f] is bool):
                problems.append(f + " has the wrong type")
            elif not isinstance(value, FIELDS[f]):
                problems.append(f + " has the wrong type")
    if isinstance(data["length_mm"], (int, float)) and not isinstance(data["length_mm"], bool):
        if not 0 < data["length_mm"] <= 40:
            problems.append("length_mm out of range")
    if data["color"] is not None and data["color"] not in VALID_COLORS:
        problems.append("unknown color")
    for f in REQUIRED:
        if data[f] is None:
            problems.append(f + " is required")
    return problems

''' Condition Checker '''
def condition_true(data, cond):
    value = data.get(cond["field"])
    if value is None:
        return False  # unknown value: condition not satisfied
    return OPS[cond["op"]](value, cond["value"])

''' Rules for Specific Cases '''
def fired_rules(data, rules):
    fired = []
    for r in rules:
        results = [condition_true(data, c) for c in r["if"]]
        match = any(results) if r.get("logic", "and") == "or" else all(results)
        if match:
            fired.append((r["name"], r["then"]))
    return fired

''' Solve function that uses the fired list'''
def solve(data, rules):
    problems = validate(data)
    if problems:
        return {"status": "invalid", "conclusion": None, "info": problems}
    fired = fired_rules(data, rules)
    if not fired:
        missing = [f for f in FIELDS if data[f] is None]
        return {"status": "no_rule", "conclusion": None,
                "info": ["no rule matched", "missing: %s" % missing]}
    if len({c for _, c in fired}) > 1:
        return {"status": "rule_conflict", "conclusion": None,
                "info": [n + " -> " + c for n, c in fired]}
    return {"status": "ok", "conclusion": fired[0][1],
            "info": [n for n, _ in fired]}

''' Solve function for all the cases '''
def solve_all(cases, rules):
    results = []
    for i, case in enumerate(cases, start=1):
        try:
            case_id, data = case.get("id", i), dict(case["data"])
        except (KeyError, TypeError, AttributeError):
            results.append({"id": i, "status": "invalid", "conclusion": None,
                            "info": ["bad case format"]})
            continue
        r = solve(data, rules)
        results.append({"id": case_id, "input": data, **r})
        print(case_id, r["status"], r["conclusion"], r["info"])
    return results

''' Menu '''
def menu():
    rules, cases, results = [], [], []
    while True:
        print("\n1) Import rules  2) Import cases  3) Solve  "
              "4) Export conclusions  5) Export rules  6) Export cases  7) Exit")
        option = input("Option: ").strip()
        if option == "1":
            loaded = upload_json("rules")
            if loaded is not None:
                rules = check_rules(loaded)
                print(len(rules), "valid rules loaded.")
        elif option == "2":
            loaded = upload_json("cases")
            if loaded is not None:
                cases = loaded
                print(len(cases), "cases loaded.")
        elif option == "3":
            if not rules or not cases:
                print("Import rules and cases first.")
            else:
                results = solve_all(cases, rules)
        elif option == "4":
            if results:
                download_json(results, "conclusions.json")
            else:
                print("Nothing to export. Solve first.")
        elif option == "5":
            if rules:
                download_json(rules, "cacao_rules.json")
                break
            else:
                print("No rules loaded.")
        elif option == "6":
            if cases:
                download_json(cases, "cases.json")
                break
            else:
                print("No cases loaded.")

        elif option == "7":
            break
if __name__ == "__main__":
  menu()