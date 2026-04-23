import pandas as pd
import unicodedata
import logging

def load_data(): 
    # TODO: Connect Google Sheets
    logging.info("Loading CSV files")
    students = pd.read_csv('./data/students_list.csv')
    prefs = pd.read_csv('./data/students_elections.csv')
    companies = pd.read_csv('./data/company_list.csv')
    return students, prefs, companies

def clean_first_name(v: str) -> str:
    return str(v).strip().split()[0]

def normalize(text: str) -> str:
    text = str(text).lower().strip()
    text = unicodedata.normalize('NFKD', text)
    return "".join(c for c in text if not unicodedata.combining(c))

def prepare_data(students, prefs):
    # --- students ---
    logging.info("Preparing student data")
    students = students[students['Name'].notna()].reset_index(drop=True)

    students_df = (
        students[["Vorname", "Name"]]
        .rename(columns={"Name": "Nachname"})
        .sort_values(by="Nachname")
        .reset_index(drop=True)
    )

    students_df["vor_clean"] = students_df["Vorname"].apply(clean_first_name)
    students_df["id"] = (
        students_df["vor_clean"] + "_" + students_df["Nachname"]
    ).apply(normalize)

    logging.info("Total students after cleaning: %d", len(students_df))
    # --- prefs ---
    prefs_df = prefs.iloc[:, 1:].copy()
    prefs_df = prefs_df.sort_values(by="Nachname").reset_index(drop=True)

    prefs_df["vor_clean"] = prefs_df["Vorname"].apply(clean_first_name)
    prefs_df["id"] = (
        prefs_df["vor_clean"] + "_" + prefs_df["Nachname"]
    ).apply(normalize)

    # --- merge ---
    logging.info("Merging student and preference data")
    merged = students_df.merge(prefs_df, on="id", how="left")
    missing = merged["id"].isna().sum()
    if missing > 0:
        logging.warning("Missing preference matches: %d", missing)

    meta_cols = {"Vorname", "Nachname", "vor_clean", "id"}
    company_cols = [c for c in prefs_df.columns if c not in meta_cols]

    final_df = merged[
        ["id", "Vorname_x", "Nachname_x"] + company_cols
    ].copy()

    final_df = final_df.rename(columns={
        "Vorname_x": "Vorname",
        "Nachname_x": "Nachname"
    })

    final_df = final_df.fillna(0)

    return final_df, students_df