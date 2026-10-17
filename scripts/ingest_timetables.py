"""
Vignan's University — Department of Computer Science & Engineering
Official Master Timetable & Faculty Registry Ingestion Pipeline.

Parses official department timetables across Year II, III, and IV:
- data/2nd yt TT (1) (3). 9TH JULY)(3).xlsx
- data/3rd yr UPDATED TT (1) (2) 9TH JULY..xlsx
- data/4th yr TT 17TH JULY(1).xlsx

Outputs:
- public/data/timetables.json (Full multi-year section timetables & allocations)
- public/data/faculties.json (Aggregated faculty directory with phone numbers & course allocations)
- Syncs to MongoDB Atlas collection 'timetables' and 'faculties'
"""

import os
import sys
import re
import json
import logging
from typing import Dict, Any, List

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("timetable_ingestion")

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
PUBLIC_DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "public", "data")

TT_FILES = [
    (2, "2nd yt TT (1) (3). 9TH JULY)(3).xlsx", "2024–2028 Batch"),
    (3, "3rd yr UPDATED TT (1) (2) 9TH JULY..xlsx", "2023–2027 Batch"),
    (4, "4th yr TT 17TH JULY(1).xlsx", "2022–2026 Batch"),
]

DAYS = ["MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY", "FRIDAY", "SATURDAY"]


def split_faculties(fac_str: str) -> List[Dict[str, str]]:
    """Splits comma-separated faculty string into clean list of name and phone."""
    parts = fac_str.split(",")
    res = []
    for p in parts:
        p = p.strip()
        if not p:
            continue
        phone_match = re.search(r"[\(\[](\d{10})[\)\]]", p)
        phone = phone_match.group(1) if phone_match else ""
        clean_name = re.sub(r"[\(\[\{].*?[\)\]\}]", "", p).strip()
        clean_name = re.sub(r"\s+", " ", clean_name)
        # ignore weekday annotations like 'tue-Ch.Naga Gopi' or short tags
        clean_name = re.sub(r"^(mon|tue|wed|thu|fri|sat)\s*-\s*", "", clean_name, flags=re.IGNORECASE).strip()
        if len(clean_name) >= 3 and not any(k in clean_name.lower() for k in ["break", "library", "counsel"]):
            res.append({"name": clean_name, "phone": phone})
    return res


def ingest_timetables():
    try:
        import openpyxl
    except ImportError:
        logger.error("openpyxl is required to parse timetables")
        return

    all_timetables = {}
    faculty_directory = {}
    all_courses = {}

    total_sections_count = 0

    for year, fname, batch_desc in TT_FILES:
        fpath = os.path.join(DATA_DIR, fname)
        if not os.path.exists(fpath):
            logger.warning(f"Timetable file not found: {fpath}")
            continue

        logger.info(f"Parsing Year {year} Timetable from {fname}...")
        wb = openpyxl.load_workbook(fpath, data_only=True)
        all_timetables[str(year)] = {}

        for sname in wb.sheetnames:
            sec_num = re.sub(r"[^0-9]", "", sname)
            if not sec_num:
                continue
            sec_key = str(int(sec_num))
            ws = wb[sname]

            section_info = {
                "year": year,
                "batch": batch_desc,
                "section": sec_key,
                "sheet": sname,
                "room": "",
                "class_teacher": "",
                "class_teacher_phone": "",
                "time_slots": [],
                "weekly_schedule": {},
                "course_allocations": [],
            }

            in_allocations = False

            for r in range(1, ws.max_row + 1):
                row_vals = [ws.cell(r, c).value for c in range(1, ws.max_column + 1)]
                non_empty = [(c, str(v).strip()) for c, v in enumerate(row_vals, 1) if v is not None and str(v).strip()]
                if not non_empty:
                    continue

                line_str = " ".join(v for c, v in non_empty)

                # Section title & Room detection
                if "SECTION" in line_str.upper() and not section_info["room"]:
                    r_match = re.search(r"\[([A-Za-z0-9\-]+)\]|-([0-9]{3})|\(([A-Za-z0-9\-]+)\)", line_str)
                    if r_match:
                        section_info["room"] = r_match.group(1) or r_match.group(2) or r_match.group(3)

                # Day header row with period slots
                for c, v in non_empty:
                    if v.upper() == "DAY" and not section_info["time_slots"]:
                        section_info["time_slots"] = [
                            v2 for c2, v2 in non_empty
                            if c2 > c and v2.upper() != "DAY" and not v2.upper().startswith("SEC")
                        ]
                        break

                # Day schedule rows
                for c, v in non_empty:
                    if v.upper() in DAYS:
                        day_name = v.capitalize()
                        periods = []
                        for c2, v2 in non_empty:
                            if c2 > c:
                                periods.append(v2)
                        section_info["weekly_schedule"][day_name] = periods
                        break

                # Class Teacher row
                if "CLASS TEACHER" in line_str.upper():
                    in_allocations = True
                    for c, v in non_empty:
                        if "CLASS TEACHER" not in v.upper():
                            section_info["class_teacher"] = v
                            p_match = re.search(r"[\(\[](\d{10})[\)\]]", v)
                            if p_match:
                                section_info["class_teacher_phone"] = p_match.group(1)
                            clean_ct = re.sub(r"[\(\[\{].*?[\)\]\}]", "", v).strip()
                            clean_ct = re.sub(r"\s+", " ", clean_ct)
                            if clean_ct:
                                if clean_ct not in faculty_directory:
                                    faculty_directory[clean_ct] = {
                                        "name": clean_ct,
                                        "phone": section_info["class_teacher_phone"],
                                        "class_teacher_of": [],
                                        "courses": []
                                    }
                                ct_entry = f"Year {year} Sec {sec_key}"
                                if ct_entry not in faculty_directory[clean_ct]["class_teacher_of"]:
                                    faculty_directory[clean_ct]["class_teacher_of"].append(ct_entry)
                            break
                    continue

                # Course & Faculty allocation rows (under Class Teacher)
                if in_allocations:
                    if len(non_empty) >= 2:
                        sub = non_empty[0][1]
                        fac = non_empty[1][1]
                        if sub and fac and not any(k in sub.upper() for k in ["NOTE:", "PRINCIPAL", "HOD", "DEAN"]):
                            section_info["course_allocations"].append({
                                "subject": sub,
                                "faculty": fac
                            })

                            # Index faculty members
                            fac_list = split_faculties(fac)
                            for f in fac_list:
                                f_name = f["name"]
                                f_phone = f["phone"]
                                if f_name not in faculty_directory:
                                    faculty_directory[f_name] = {
                                        "name": f_name,
                                        "phone": f_phone,
                                        "class_teacher_of": [],
                                        "courses": []
                                    }
                                elif f_phone and not faculty_directory[f_name].get("phone"):
                                    faculty_directory[f_name]["phone"] = f_phone

                                c_entry = {
                                    "year": year,
                                    "section": sec_key,
                                    "subject": sub
                                }
                                if c_entry not in faculty_directory[f_name]["courses"]:
                                    faculty_directory[f_name]["courses"].append(c_entry)

            all_timetables[str(year)][sec_key] = section_info
            total_sections_count += 1

        wb.close()

    # Save to public/data/timetables.json
    tt_out_path = os.path.join(PUBLIC_DATA_DIR, "timetables.json")
    with open(tt_out_path, "w", encoding="utf-8") as f:
        json.dump(all_timetables, f, indent=2, ensure_ascii=False)
    logger.info(f"Saved {total_sections_count} section timetables to {tt_out_path}")

    # Save to public/data/faculties.json
    fac_out_path = os.path.join(PUBLIC_DATA_DIR, "faculties.json")
    fac_list = sorted(list(faculty_directory.values()), key=lambda x: x["name"])
    with open(fac_out_path, "w", encoding="utf-8") as f:
        json.dump(fac_list, f, indent=2, ensure_ascii=False)
    logger.info(f"Saved {len(fac_list)} faculty profiles to {fac_out_path}")

    # MongoDB Atlas Sync
    try:
        from backend.db import mongo_db, is_mongo_connected
        if is_mongo_connected and mongo_db is not None:
            # Sync timetables
            col_tt = mongo_db["timetables"]
            from pymongo import UpdateOne
            tt_ops = []
            for y_k, secs in all_timetables.items():
                for s_k, s_data in secs.items():
                    tt_ops.append(UpdateOne({"year": int(y_k), "section": s_k}, {"$set": s_data}, upsert=True))
            if tt_ops:
                col_tt.bulk_write(tt_ops, ordered=False)
                logger.info(f"Synced {len(tt_ops)} timetables to MongoDB Atlas collection 'timetables'.")

            # Sync faculties
            col_fac = mongo_db["faculties"]
            fac_ops = [UpdateOne({"name": f["name"]}, {"$set": f}, upsert=True) for f in fac_list]
            if fac_ops:
                col_fac.bulk_write(fac_ops, ordered=False)
                logger.info(f"Synced {len(fac_ops)} faculties to MongoDB Atlas collection 'faculties'.")
    except Exception as e:
        logger.warning(f"MongoDB sync for timetables/faculties skipped or warning: {e}")

    print("\n" + "="*60)
    print("TIMETABLE & FACULTY INGESTION COMPLETE")
    print(f"Total Sections Processed: {total_sections_count}")
    print(f"Total Unique Faculty Members: {len(fac_list)}")
    print(f"Timetables JSON: {tt_out_path}")
    print(f"Faculties JSON: {fac_out_path}")
    print("="*60)


if __name__ == "__main__":
    ingest_timetables()
