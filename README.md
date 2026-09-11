# Student Internship Assignment (ASP + Clingo)

Assigns students to internship companies based on preferences using **Clingo** and **Python**.

---

## 📌 Overview

**Input:**
- One student list  
- Student preferences (optional)  
- Companies with capacities  

**Goal:**
Assign every student while maximizing preference satisfaction and respecting constraints.

---

## 🧱 Structure

```
project/
├── main.py
├── data/
│   ├── folder_with_csvs/ (manual input)
│   └── rules.json        (manual input)
├── logs/
├── results/
├── src/
│   └── utils/
└── README.md
```

---

## ⚙️ Pipeline

1. Load data from `/data`  
2. Clean & normalize names, generate IDs (`vorname_nachname`)  
3. Merge students with preferences  
4. Generate ASP files (`data.lp`, `config.lp`)  
5. Run Clingo to compute optimal assignment  
6. Parse results and map back to names  
7. Export `assignments.csv`  

---

## 🧩 Rules (`rules.json`)

Configure assignment behavior without changing code:

```json
{
  "min_per_company": 7,
  "max_prio": { "Caritas": 2 },
  "fill_first": { "Gesobau": 20, "ABB": 10 }
}
```

---

## 🚀 Usage

### Install
```
pip install pandas
```

Install Clingo: https://potassco.org/clingo/

### Run
```
python main.py
```

### Options
```
python main.py --timeout 120 --debug
```

- `--timeout` → solver time limit (seconds)  
- `--threads` → number of Clingo solver threads  
- `--debug` → verbose logging  

---

## 📅 Multi-Day Mode

Multi-day mode assigns the same students across multiple available days.

There is **one shared student list**. Each day has its own company and preference file.
```
python main.py --mode multi \
  --companies companies_day1.csv companies_day2.csv \
  --prefs prefs_day1.csv prefs_day2.csv
```

The files are matched by their order:
```
Student list (shared)
        │
        ├── Day 1 → companies_day1.csv + prefs_day1.csv
        │
        └── Day 2 → companies_day2.csv + prefs_day2.csv
```
The number of company files and preference files must be identical.

The solver assigns **each student to exactly one day and one company**, while respecting the capacities and preferences available on that day.

---

## 📄 Output

`assignments.csv`

```
Vorname,Nachname,company
Florian,Abraham,ABB
...
```

---

## ⚠️ Notes

- All students are assigned (even without preferences)  
- Missing preferences = `0`  
- Rules use fuzzy company name matching  
- In multi-day mode, the student list is shared across all days

---

## 🧠 Tech

- Python + Pandas  
- Clingo (ASP solver)  

---

## ✅ Status

✔ Modular structure
✔ Configurable rules
✔ Single- and multi-day assignment
✔ Logging & CLI support
✔ Optimal assignment generation