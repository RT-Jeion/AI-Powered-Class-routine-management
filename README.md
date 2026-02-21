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

## Agentic Class Routine Management

An AI-powered agent that uses LangChain + Groq to manage class routines through natural language instructions.

### Install

```bash
pip install -r requirements.txt
```

### Environment Variable

Set your Groq API key before running the agent:

```bash
export GROQ_API_KEY=your_groq_api_key_here
```

### Usage

```bash
# Schedule a slot via natural language
python run_agent.py --prompt "Schedule Bangla 1st paper (subject_id=1) for section 11A on Monday period 1, teacher_id=1, room_id=1, shift_log_id=1"

# Specify custom paths
python run_agent.py \
  --prompt "Move 11A Monday period 2 to Wednesday period 2" \
  --routine output/routine_table.csv \
  --output-md output/class_routine_generated.md
```

### Output Files

| File | Description |
|------|-------------|
| `output/routine_table.csv` | The routine data (section_code, day, period, subject_id, teacher_id, room_id, shift_log_id) |
| `output/class_routine_generated.md` | Markdown timetable visualization generated from the routine CSV |

### Package Structure

```
routine_agent/
  data_context.py       # Load all CSV files into DataFrames
  routine_store.py      # Load/save/upsert/move/swap routine slots
  validator.py          # Teacher conflict, room conflict, period/day validation
  markdown_renderer.py  # Generate Markdown from routine CSV + context
  agent.py              # LangChain tool-calling agent wired to Groq
run_agent.py            # CLI entrypoint
```
