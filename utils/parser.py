import re
import pandas as pd
import logging
from datetime import datetime

def parse_clingo_output(output: str) -> pd.DataFrame:
    logging.info("Parsing Clingo output")
    lines = output.splitlines()

    best_answer = None
    best_vector = None

    i = 0
    while i < len(lines):
        if lines[i].startswith("Answer:"):
            answer = lines[i + 1]
            opt = lines[i + 2] if i + 2 < len(lines) else ""

            vector = []
            if "Optimization:" in opt:
                vector = [int(x) for x in opt.split(":")[1].split()]

            if best_vector is None or vector < best_vector:
                best_answer = answer
                best_vector = vector

            i += 3
        else:
            i += 1

    if not best_answer:
        logging.error("No valid solution found in Clingo output")
        raise ValueError("No solution found")

    matches = re.findall(r'assign\("([^"]+)","([^"]+)"\)', best_answer)
    logging.info("Assignments extracted: %d", len(matches))
    # TODO: Change order before saving
    return pd.DataFrame(matches, columns=["id", "company"])


def map_ids_to_names(assignments, students_df):
    return assignments.merge(
        students_df[["id", "Vorname", "Nachname"]],
        on="id",
        how="left"
    )[["Vorname", "Nachname", "company"]]


def save_output(df, exp_name: str):
    date_str = datetime.now().strftime("%Y-%m-%d")
    if exp_name:
        filename = f"./results/assignments_{exp_name}_{date_str}.csv"
        df.to_csv(filename, index=False)
    else:
        df.to_csv(f"./results/assignments_{date_str}.csv", index=False)