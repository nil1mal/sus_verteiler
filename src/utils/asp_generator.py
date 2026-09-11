import json
import logging

def load_rules(path="./data/rules.json"):
    logging.info("Loading rules from %s", path)

    try:
        with open(path, "r") as f:
            rules = json.load(f)
    except FileNotFoundError:
        logging.error("rules.json not found")
        raise
    except json.JSONDecodeError as e:
        logging.error("Invalid JSON format in rules.json")
        raise ValueError(f"Invalid JSON: {e}")

    return rules


def generate_asp(final_df, companies, mode: str = "single"):
    logging.info("Generating ASP facts (src/data.lp)")
    logging.info(f"Companies: {len(companies)} | Max capacity: {int(companies['max'].max())} | Total spots: {int(companies['max'].sum())}")

    lines = []

    # mode fact
    lines.append(f'mode("{mode}").')
    lines.append("")

    # days
    for day in sorted(companies["day"].unique()):
        lines.append(f'day({int(day)}).')
    lines.append("")

    # students
    for sid in final_df["id"]:
        lines.append(f'student("{sid}").')
    lines.append("")

    # companies
    for _, row in companies.iterrows():
        lines.append(f'company("{row["name"]}").')
        lines.append(f'capacity("{row["name"]}",{int(row["max"])}).')
        lines.append(f'company_day("{row["name"]}",{int(row["day"])}).')
    lines.append("")

    # preferences
    meta_cols = {"id", "Vorname", "Nachname"}
    company_cols = [c for c in final_df.columns if c not in meta_cols]

    for _, row in final_df.iterrows():
        for c in company_cols:
            val = row[c]
            if val > 0:
                lines.append(f'pref("{row["id"]}","{c}",{int(val)}).')

    with open("src/data.lp", "w") as f:
        f.write("\n".join(lines))


def generate_config(companies, rules):
    real_names = companies["name"].tolist()

    def resolve(key):
        matches = [n for n in real_names if key.lower() in n.lower()]
        if len(matches) == 1:
            return matches[0]
        if len(matches) == 0:
            raise ValueError(f"No company match for '{key}'")
        raise ValueError(f"Ambiguous company key '{key}': {matches}")

    lines = [
        "% auto-generated",
        "% edit rules.json instead of this file",
        ""
    ]

    # --- Rule 1: global min ---
    if "min_per_company" in rules:
        lines.append(f'min_per_company({rules["min_per_company"]}).')

    # --- CSV-based rules ---
    for _, row in companies.iterrows():
        if int(row["min"]) > 0:
            lines.append(f'company_min("{row["name"]}",{int(row["min"])}).')

        if int(row["genau"]) > 0:
            lines.append(f'exact_count("{row["name"]}",{int(row["genau"])}).')

    # --- Rule 3: max_prio ---
    for key, val in rules.get("max_prio", {}).items():
        company = resolve(key)
        lines.append(f'max_prio("{company}",{val}).')

    # --- Rule 5: fill_first ---
    for key, val in rules.get("fill_first", {}).items():
        company = resolve(key)
        lines.append(f'fill_first("{company}",{val}).')

    with open("src/config.lp", "w") as f:
        f.write("\n".join(lines))

    logging.info("src/config.lp generated")