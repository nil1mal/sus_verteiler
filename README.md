# Student Internship Assignment (ASP + Clingo)

Assigns students to internship companies based on preferences using **Answer Set Programming (ASP)** with **Clingo**.

---

## 📌 Overview

**Input:**
- Students  
- Student preferences (optional)  
- Companies with capacities  

**Goal:**
Assign every student while maximizing preference satisfaction and respecting constraints.

---

## 🧱 Structure

```
project/
├── main.py
├── rules.json
├── utils/
├── data/
├── model.lp
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
- `--debug` → verbose logging  

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

---

## 🧠 Tech

- Python + Pandas  
- Clingo (ASP solver)  

---

## ✅ Status

✔ Modular structure  
✔ Configurable rules  
✔ Logging & CLI support  
✔ Optimal assignment generation  