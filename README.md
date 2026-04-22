# Student Internship Assignment (ASP + Clingo)

This project assigns students to internship companies based on their preferences using **Answer Set Programming (ASP)** with **Clingo**.

---

## 📌 Overview

We are given:

* A list of students
* A list of student preferences (not all students responded)
* A list of companies with capacity limits

The goal is to:

> Assign **every student** to a company while maximizing overall satisfaction and respecting company capacities.

---

## ⚙️ Pipeline

The process is fully automated in `main.py`:

### 1. Data Loading

* Reads CSV files from `/data`:

  * `students_list.csv`
  * `students_elections.csv`
  * `company_list.csv`

---

### 2. Data Cleaning

* Removes invalid rows
* Normalizes names (lowercase, removes accents)
* Extracts first given name (handles multiple first names)

---

### 3. Matching Students ↔ Preferences

* Builds a unique **ID**:

  ```
  vorname_nachname
  ```
* Merges student list with preference data

---

### 4. ASP Encoding

Creates `data.lp` with facts:

* Students:

  ```
  student("florian_abraham").
  ```

* Companies:

  ```
  company("ABB").
  capacity("ABB",20).
  ```

* Preferences:

  ```
  pref("florian_abraham","ABB",5).
  ```

---

### 5. Optimization (Clingo)

Clingo assigns students such that:

* ✅ Every student is assigned
* ✅ Company capacities are respected
* ✅ Preferences are maximized

Run with:

```
clingo data.lp model.lp --opt-mode=optN --time-limit=60
```

---

### 6. Result Parsing

* Extracts final optimal assignment
* Maps IDs back to real names

---

### 7. Output

Final result is saved as:

```
assignments.csv
```

Format:

```
Vorname,Nachname,company
Florian,Abraham,ABB
Zahra,Afshar,Sparkasse
...
```

---

## 🚀 How to Run

### 1. Install dependencies

```
pip install pandas
```

Install Clingo:

👉 https://potassco.org/clingo/

---

### 2. Run the script

```
python main.py
```

---

## ⚠️ Notes

* Students without preferences are still assigned (required by task)
* Missing preferences are treated as neutral (0)
* Name normalization is critical for matching consistency

---

## 📊 Possible Extensions

* Compute average satisfaction score
* Detect worst assignments
* Balance company load
* Add fairness constraints

---

## 🧠 Technologies Used

* Python (data processing)
* Pandas (data manipulation)
* Clingo (ASP solver)

---

## ✅ Status

✔ End-to-end pipeline working
✔ Optimal assignment generation
✔ Clean CSV output

---

## 👨‍💻 Author

Project for internship assignment optimization using ASP.
