# AI-Powered Class Routine Management

## Data Organization Overview

This project uses Pandas to organize and manage class routine data from various CSV files.

---

## Data Files and Structure

### FILE: class1.py

#### 1. **classes.csv** → `class_dt`
**Columns:**
- `id`
- `name`
- `code`

#### 2. **sections.csv** → `section_dt`
**Columns:**
- `id`
- `name`
- `code`
- `grp_code` *(added)*
- `classes_id`

**Modifications:**
- **Added:** `grp_code` → Values: `hsc-sci`, `hsc-commerce`, `hsc-arts`
- **Converted:** `class_id` → `1, 2` → `11, 12`

#### 3. **class_rooms.csv** → `class_room_dt`
**Columns:**
- `id`
- `room_no`
- `number_of_row`
- `number_of_columns`
- `each_bench_capacity`

#### 4. **shift_management_logs.csv** → `shift_dt`
**Columns:**
- `id`
- `weekends`
- `start`
- `end`

#### 5. **subjects.csv** → `sub_dt`
**Columns:**
- `id`
- `name`
- `code`
- `department` *(added)*

**Modifications:**
- **Added:** `department` → Values: Bangla, English, Math, etc.

#### 6. **subjects_groups.csv** → `sub_grp_dt`
**Columns:**
- `id`
- `name`
- `grp_code`
- `has_subjects`

#### 7. **teachers.csv** → `teacher_dt`
**Columns:**
- `id`
- `name`
- `code`
- `department`
- `designation`

---

### FILE: main.py

#### 1. **Section and Group Subject Mapping** → `sec_sub_dt`
- Merged `section_dt` and `sub_grp_dt`
- Joined on `grp_code`
- Based on `sub_grp_dt` structure

#### 2. **Shift Duration Calculation**
- Added new column to `shift_dt`: `duration`
- Calculation: Time duration between `end - start`

---

## Getting Started

1. Ensure all CSV files are in the appropriate directory
2. Run `class1.py` to load and organize the data
3. Run `main.py` to perform data merging and calculations

## Requirements

- Python 3.x
- Pandas library

```bash
pip install pandas
```

---

## Notes

- All data transformations are handled using Pandas DataFrames
- Ensure CSV files follow the specified column structure for proper data loading

---

## Agentic Class Routine Management (LangChain + Groq)

This project now includes an AI-powered routine management agent built with
[LangChain](https://python.langchain.com/) and the
[Groq](https://groq.com/) inference platform (model `openai/gpt-oss-120b`).

### Package Layout

```
routine_agent/
  config.py            # RoutineRules (days, periods, break position)
  data_context.py      # Load reference DataFrames from csv_files/
  routine_store.py     # load / save / upsert / move / swap routine slots
  validator.py         # Teacher conflict, room conflict, day/period bounds
  markdown_renderer.py # Generate output/class_routine_generated.md
  agent.py             # LangChain tool-calling agent (Groq)

run_agent.py           # CLI entrypoint

output/
  routine_table.csv            # Generated routine (section_code, day, period, …)
  class_routine_generated.md   # Human-readable Markdown timetable
```

### Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Set your Groq API key
export GROQ_API_KEY="your_groq_api_key_here"
```

### Usage

```bash
# Schedule a full routine from a natural-language prompt
python run_agent.py --prompt "Create a weekly routine for section 11A with Math on Sunday period 1 (teacher 6, room 1, shift log 6) and Bangla 1st on Monday period 2 (teacher 2, room 1, shift log 6)."

# Ask the agent to validate the existing routine
python run_agent.py --prompt "Validate the current routine and report any conflicts."

# Move a slot
python run_agent.py --prompt "Move section 11A Monday period 3 to Wednesday period 3."
```

After each run the agent:
1. Validates the routine for teacher/room conflicts and bounds errors.
2. Saves `output/routine_table.csv` (columns: `section_code`, `day`, `period`, `subject_id`, `teacher_id`, `room_id`, `shift_log_id`).
3. Regenerates `output/class_routine_generated.md` with per-section Markdown timetables (periods 1–6 with a break row after period 3).

### Output Format

`output/routine_table.csv` columns:

| Column | Description |
|---|---|
| `section_code` | Section code (e.g. `11A`) |
| `day` | Day abbreviation (`Sun` … `Thu`) |
| `period` | Period number (1–6) |
| `subject_id` | ID from `csv_files/subjects.csv` |
| `teacher_id` | ID from `csv_files/teachers.csv` |
| `room_id` | ID from `csv_files/class_rooms.csv` |
| `shift_log_id` | ID from `csv_files/shift_management_logs.csv` |
