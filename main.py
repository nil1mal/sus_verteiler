import pandas as pd
import unicodedata
import re
import subprocess


# =========================
# HELPERS
# =========================
def clean_vorname(v):
    """Extract first given name"""
    return str(v).strip().split()[0]


def normalize(text):
    """Normalize text (lowercase, remove accents)"""
    text = str(text).lower().strip()
    text = unicodedata.normalize('NFKD', text)
    return "".join(c for c in text if not unicodedata.combining(c))


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


# =========================
# 7. EXPORT TO ASP
# =========================
asp_lines = []

# Students
for sid in final_df["id"]:
    asp_lines.append(f'student("{sid}").')

# Companies
for _, row in companies.iterrows():
    asp_lines.append(f'company("{row["name"]}").')
    asp_lines.append(f'capacity("{row["name"]}",{int(row["capacity"])}).')

# Preferences
company_cols = [c for c in final_df.columns if c not in ["id", "Vorname", "Nachname"]]

for _, row in final_df.iterrows():
    sid = row["id"]
    for c in company_cols:
        val = row[c]
        if isinstance(val, (int, float)) and val > 0:
            asp_lines.append(f'pref("{sid}","{c}",{int(val)}).')

# Save ASP file
with open("data.lp", "w") as f:
    f.write("\n".join(asp_lines))

print("ASP data written to data.lp")


# =========================
# 8. RUN CLINGO
# =========================
result = subprocess.run(
    ["clingo", "data.lp", "model.lp", "--opt-mode=optN", "--time-limit=60"],
    capture_output=True,
    text=True
)

output = result.stdout


# =========================
# 9. PARSE RESULT
# =========================
lines = output.splitlines()
answer_lines = [line for line in lines if "assign(" in line]

if not answer_lines:
    raise ValueError("No solution found by clingo")

last_answer = answer_lines[-1]

matches = re.findall(r'assign\("([^"]+)","([^"]+)"\)', last_answer)
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