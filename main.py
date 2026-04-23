import pandas as pd
import unicodedata
import re
import subprocess
import argparse

# =========================
# HELPERS
# =========================

parser = argparse.ArgumentParser(description='SuS Verteiler.')
args = parser.parse_args()

def clean_vorname(v):
    """Extract first given name"""
    return str(v).strip().split()[0]


def normalize(text):
    """Normalize text (lowercase, remove accents)"""
    text = str(text).lower().strip()
    text = unicodedata.normalize('NFKD', text)
    return "".join(c for c in text if not unicodedata.combining(c))


# =========================
# DYNAMIC RULES CONFIGURATION
# =========================
# Edit this dict to add, remove, or tweak rules without touching model.lp.
# Each key maps to a fact type that model.lp reacts to.
#
# Rule 1 – min_per_company:   soft minimum students per company (~n_students / n_companies)
# Rule 2 – exact_count:       exact headcount for specific companies (hard)
# Rule 3 – max_prio:          only students with pref rank <= N may go to this company (hard)
# Rule 4 – (automatic in model.lp, no config needed)
# Rule 5 – fill_first:        fill these companies first; higher weight = stronger preference
#
RULES = {
    # Global fallback minimum per company.
    # Overridden per-company by the `min` column in company_list.csv.
    # Companies with `genau` > 0 are exempt (exact count controls them instead).
    "min_per_company": 7,

    # exact_count is now auto-extracted from the `genau` column in company_list.csv.
    # No need to list companies here anymore.

    "max_prio": {
        "Caritas": 2,          # only rank-1 and rank-2 students accepted
    },
    "fill_first": {
        "Gesobau": 20,         # fill Gesobag first  (higher weight = stronger pull)
        "ABB":     10,         # fill ABB second
    },
}


# =========================
# 1. LOAD DATA
# =========================
students = pd.read_csv('./data/students_list.csv')
prefs = pd.read_csv('./data/students_elections.csv')
companies = pd.read_csv('./data/company_list.csv')


# =========================
# 2. CLEAN STUDENTS
# =========================
students = students[students['Name'].notna()].reset_index(drop=True)

students_df = (
    students[["Vorname", "Name"]]
    .rename(columns={"Name": "Nachname"})
    .sort_values(by="Nachname")
    .reset_index(drop=True)
)

students_df["vor_clean"] = students_df["Vorname"].apply(clean_vorname)
students_df["id"] = (
    students_df["vor_clean"] + "_" + students_df["Nachname"]
).apply(normalize)


# =========================
# 3. CLEAN PREFERENCES
# =========================
prefs_df = prefs.iloc[:, 1:].copy()

prefs_df = prefs_df.sort_values(by="Nachname").reset_index(drop=True)

prefs_df["vor_clean"] = prefs_df["Vorname"].apply(clean_vorname)
prefs_df["id"] = (
    prefs_df["vor_clean"] + "_" + prefs_df["Nachname"]
).apply(normalize)


# =========================
# 4. MERGE
# =========================
merged = students_df.merge(
    prefs_df,
    on="id",
    how="left",
    indicator=True
)


# =========================
# 5. BUILD FINAL TABLE
# =========================
company_cols = [
    col for col in prefs_df.columns
    if col not in ["Vorname", "Nachname", "vor_clean", "id"]
]

final_df = merged[
    ["id", "Vorname_x", "Nachname_x"] + company_cols
].copy()

final_df = final_df.rename(columns={
    "Vorname_x": "Vorname",
    "Nachname_x": "Nachname"
})

final_df = final_df.fillna(0)


# =========================
# 6. DEBUG
# =========================
print("Final dataset shape:", final_df.shape)
print(final_df.head())

unmatched = merged[merged["_merge"] == "left_only"]
print("Unmatched students:", len(unmatched))
print("Total students:", len(final_df))

# =========================
# 7. EXPORT STUDENT/COMPANY FACTS TO ASP
# =========================
asp_lines = []

# Students
for sid in final_df["id"]:
    asp_lines.append(f'student("{sid}").')

# Companies
for _, row in companies.iterrows():
    asp_lines.append(f'company("{row["name"]}").')
    asp_lines.append(f'capacity("{row["name"]}",{int(row["max"])}).')

# Preferences
company_cols = [c for c in final_df.columns if c not in ["id", "Vorname", "Nachname"]]

for _, row in final_df.iterrows():
    sid = row["id"]
    for c in company_cols:
        val = row[c]
        if isinstance(val, (int, float)) and val > 0:
            asp_lines.append(f'pref("{sid}","{c}",{int(val)}).')

with open("data.lp", "w") as f:
    f.write("\n".join(asp_lines))

print("ASP data written to data.lp")


# =========================
# 7b. GENERATE config.lp FROM RULES DICT
# =========================
# model.lp contains general rules that react to these facts.
# To add a new rule: add a key here + one general rule in model.lp.

# --- Fuzzy company name resolver ---
# RULES keys like "Caritas" are matched against the real company names
# (e.g. "Caritas Krankenhaus") so config.lp always uses the exact string
# that appears in data.lp. Raises an error early if a key is ambiguous
# or has no match, rather than silently generating a fact that never fires.
real_company_names = companies["name"].tolist()

def resolve_company(key):
    """Return the real company name that contains `key` (case-insensitive).
    Raises ValueError if there is no match or more than one match."""
    key_lower = key.lower()
    matches = [n for n in real_company_names if key_lower in n.lower()]
    if len(matches) == 1:
        return matches[0]
    if len(matches) == 0:
        raise ValueError(
            f"RULES key '{key}' matched no company in company_list.csv.\n"
            f"Available companies: {real_company_names}"
        )
    raise ValueError(
        f"RULES key '{key}' is ambiguous — matched {matches}.\n"
        f"Use a more specific name."
    )

config_lines = [
    "% Auto-generated by main.py — do not edit by hand.",
    "% Edit the RULES dict at the top of main.py instead.",
    "",
]

# Rule 1: global fallback minimum — used for companies with no CSV override
#         and no exact count
if "min_per_company" in RULES:
    config_lines.append(f'min_per_company({RULES["min_per_company"]}).')

# Rule 1 (per-company): auto-extracted from `min` column in company_list.csv.
# These override the global default for their company.
for _, row in companies.iterrows():
    if int(row["min"]) > 0:
        config_lines.append(f'company_min("{row["name"]}",{int(row["min"])}).')

# Rule 2: auto-extracted from `genau` column in company_list.csv.
# Companies with genau > 0 get an exact_count fact (and are exempt from min).
for _, row in companies.iterrows():
    if int(row["genau"]) > 0:
        config_lines.append(f'exact_count("{row["name"]}",{int(row["genau"])}).')

# Rule 3: max allowed preference rank per company
for key, p in RULES.get("max_prio", {}).items():
    company = resolve_company(key)
    config_lines.append(f'max_prio("{company}",{p}).')

# Rule 5: fill-first companies (rule 4 is automatic — no config fact needed)
for key, w in RULES.get("fill_first", {}).items():
    company = resolve_company(key)
    config_lines.append(f'fill_first("{company}",{w}).')

with open("config.lp", "w") as f:
    f.write("\n".join(config_lines))

print("Config written to config.lp")
print("\n".join(config_lines))


# =========================
# 8. RUN CLINGO
# =========================
result = subprocess.run(
    ["clingo", "data.lp", "config.lp", "model.lp",
     "--opt-mode=optN", "--time-limit=1200", "-t 4"],
    capture_output=True,
    text=True
)

output = result.stdout

# =========================
# 9. PARSE RESULT
# =========================
# Clingo output with --opt-mode=optN looks like:
#
#   Answer: 1
#   assign("a","X") assign("b","Y") ...
#   Optimization: 500 200 100 50        ← penalties at @4 @3 @2 @1
#   Answer: 2
#   assign("a","X") assign("b","Z") ...
#   Optimization: 400 200 100 48        ← better solution
#   ...
#   Progression : [400;400] (Error: 0)  ← proven optimal (NOT a program error)
#
# We pair each answer line with its following Optimization line and keep
# the answer set with the lexicographically smallest optimization vector
# (Clingo already minimizes left-to-right by priority level, so the last
# complete pair is always the best — but we verify explicitly to be safe
# even when the time limit cuts things short).

lines = output.splitlines()

best_answer_str   = None
best_opt_vector   = None   # list of ints, compared lexicographically

i = 0
while i < len(lines):
    line = lines[i].strip()
    if line.startswith("Answer:"):
        answer_body = lines[i + 1].strip() if i + 1 < len(lines) else ""
        opt_line    = lines[i + 2].strip() if i + 2 < len(lines) else ""

        if "assign(" in answer_body:
            opt_vector = []
            if opt_line.startswith("Optimization:"):
                opt_vector = [int(x) for x in opt_line.split(":")[1].split()]

            if best_opt_vector is None or opt_vector < best_opt_vector:
                best_answer_str = answer_body
                best_opt_vector = opt_vector
        i += 3
    else:
        i += 1

if not best_answer_str:
    print("--- Clingo stdout ---")
    print(output)
    print("--- Clingo stderr ---")
    print(result.stderr)
    raise ValueError("No solution found by Clingo. See output above.")

# Report optimization quality (these are NOT errors — "Progression/Error"
# is Clingo's term for the convergence gap; Error=0 means proven optimal)
print("\n=== Clingo optimization summary ===")
if best_opt_vector:
    labels = ["@4 preference scores + company min shortfall (balanced)",
              "@3 sole-top violations",
              "@2 fill-first / misc penalties"]
    for label, val in zip(labels, best_opt_vector):
        print(f"  {label}: {val}")

proved_optimal = "Progression" not in output or "(Error: 0)" in output
print(f"  Proven optimal: {'YES' if proved_optimal else 'NO (time limit reached — best found)'}")

# Warn if sole-top violations are high (5 * 500 or more)
if best_opt_vector and best_opt_vector[0] >= 2500:
    sole_top_count = best_opt_vector[0] // 500
    print(f"\n  ⚠ Warning: {sole_top_count} sole-top-choice students could not get "
          f"their unique rank-1 company. Consider raising company capacities "
          f"or relaxing the min_per_company rule.")
print()

matches = re.findall(r'assign\("([^"]+)","([^"]+)"\)', best_answer_str)
assignments = pd.DataFrame(matches, columns=["id", "company"])

print("Assignments:", assignments.shape)

# =========================
# 10. MAP BACK TO NAMES
# =========================
students_ids = students_df[["id", "Vorname", "Nachname"]].copy()

final_assignments = assignments.merge(
    students_ids,
    on="id",
    how="left"
)

final_assignments = final_assignments[
    ["Vorname", "Nachname", "company"]
]


# =========================
# 11. SAVE OUTPUT
# =========================
final_assignments.to_csv("assignments.csv", index=False)
print("Saved to assignments.csv")


# =========================
# 12. CHECK ERRORS
# =========================
missing = final_assignments[final_assignments["Vorname"].isna()]

print("Missing matches:", len(missing))
if len(missing) > 0:
    print(missing.head())