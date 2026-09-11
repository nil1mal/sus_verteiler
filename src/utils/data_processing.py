import pandas as pd
import unicodedata
import logging
import os

def load_data(folder: str, mode: str = "single", companies_paths: list = None, prefs_paths: list = None):
    logging.info(f"Loading CSV files from {folder}")

    students = pd.read_csv(os.path.join(folder, "students_list.csv"))

    if mode == "multi":
        logging.info("Multi-day mode: loading companies and prefs from flags")

        companies_dfs = []
        for i, path in enumerate(companies_paths, start=1):
            df = pd.read_csv(path)
            df["day"] = i
            companies_dfs.append(df)
            logging.info(f"Day {i} companies: {len(df)} | path: {path}")
        companies = pd.concat(companies_dfs, ignore_index=True)

        prefs_dfs = []
        for i, path in enumerate(prefs_paths, start=1):
            df = pd.read_csv(path)
            df["day"] = i
            prefs_dfs.append(df)
            logging.info(f"Day {i} prefs: {len(df)} students | path: {path}")
        prefs = pd.concat(prefs_dfs, ignore_index=True)

    else:
        prefs = pd.read_csv(os.path.join(folder, "students_elections.csv"))
        companies = pd.read_csv(os.path.join(folder, "company_list.csv"))
        companies["day"] = 1

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

    meta_cols = {"Vorname", "Nachname", "vor_clean", "id", "day"}
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