# AI-Powered Class Routine Management

A CLI-first, agentic class routine management system powered by the Groq LLM API (via LangChain/LangGraph). It understands natural-language prompts, generates conflict-free timetables from existing CSV data, and validates scheduling constraints automatically.

---

## Quick Start

### 1. Clone and install dependencies

```bash
git clone https://github.com/RT-Jeion/AI-Powered-Class-routine-management.git
cd AI-Powered-Class-routine-management
pip install -r requirements.txt
```

### 2. Configure the Groq API key (optional)

The system works without a Groq API key using its built-in keyword parser. To enable LLM-powered natural-language understanding:

1. Get a free key at <https://console.groq.com/keys>
2. Copy `.env.example` to `.env` and add your key:

```bash
cp .env.example .env
# Then edit .env:
# GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxxxxxx
```

### 3. Run the CLI

**Interactive mode** (prompts you for input):

```bash
python cli.py
```

**Single-prompt mode**:

```bash
python cli.py "Create a routine for Class 11 Science"
python cli.py "Create a routine for Class 12"
python cli.py "Reschedule all Math classes to avoid Friday"
python cli.py "Show routine for 11A"
```

### Example session

```
>>> Create a routine for Class 11 Science
✅ Generated routine for 11A (24 entries).
✅ No constraint violations.

── Routine Preview ──
[11A]
  Mon P1: Bangla 1st paper | Mr Bangla1 | Room 101
  Mon P2: Bangla 2nd paper | Mr Bangla1 | Room 101
  ...

>>> Reschedule all Math classes to avoid Friday
✅ 11A: 'Math' classes moved away from Fri.
✅ No constraint violations after rescheduling.
```

---

## Project Structure

```
.
├── cli.py                  # CLI entrypoint (interactive + single-prompt)
├── core/
│   ├── __init__.py
│   ├── data_loader.py      # Load CSV files into pandas DataFrames
│   ├── constraints.py      # Teacher/room double-booking & timeslot collision checks
│   ├── scheduler.py        # Heuristic routine generation and rescheduling
│   ├── intent_parser.py    # Groq LLM intent parsing with keyword fallback
│   └── agent.py            # Agentic loop: parse → load → plan → apply → validate → respond
├── csv_files/              # Source data (classes, sections, teachers, subjects, …)
├── requirements.txt
├── .env.example
├── class1.py               # Original data-loading scripts (unchanged)
├── main.py
└── README.md
```

---

## Agentic Loop

```
User prompt
    │
    ▼
intent_parser  ──(Groq LLM or keyword fallback)──▶  intent dict
    │
    ▼
agent.run()
    ├─ create_routine  ──▶ scheduler.generate_routine()  ──▶ constraints.validate()
    ├─ reschedule      ──▶ scheduler.reschedule_subject() ──▶ constraints.validate()
    └─ show_routine    ──▶ format in-memory routines
```

### Supported intents

| Natural-language example | Intent |
|---|---|
| "Create a routine for Class 11 Science" | `create_routine` |
| "Generate schedule for 11A" | `create_routine` |
| "Reschedule all Math classes to avoid Friday" | `reschedule` |
| "Move English away from Monday" | `reschedule` |
| "Show routine for 11A" | `show_routine` |
| "Display all routines" | `show_routine` |

### Constraint checks

- **Teacher double-booking** — same teacher in two sections at the same time
- **Room double-booking** — same room used by two sections simultaneously
- **Timeslot collision** — a section scheduled for two subjects in the same slot

---

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

## Requirements

- Python 3.8+
- See `requirements.txt` for all dependencies

```bash
pip install -r requirements.txt
```

---

## Legacy Scripts

- `class1.py` — original data-loading demo
- `main.py` — section–subject merge and shift duration calculation

These are preserved for reference; the `core/` engine supersedes them.
