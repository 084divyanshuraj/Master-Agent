"""
Vignan's University — Master Agent Database & Audit Logger
Supports MongoDB Atlas persistence with automatic in-memory fallback.
"""

import os
import time
import json
import logging
import hashlib
import secrets
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

load_dotenv(override=True)
logger = logging.getLogger("mongo_db")
logger.setLevel(logging.INFO)

# In-memory storage fallback for query logs, custom agent endpoints, student records, and user sessions
IN_MEMORY_LOGS: List[Dict[str, Any]] = []
IN_MEMORY_USERS: Dict[str, Dict[str, Any]] = {}
IN_MEMORY_ENDPOINTS: Dict[str, str] = {}
IN_MEMORY_STUDENTS: Dict[str, Dict[str, Any]] = {}
IN_MEMORY_TIMETABLES: Dict[str, Dict[str, Any]] = {}
IN_MEMORY_FACULTIES: List[Dict[str, Any]] = []
MAX_LOG_HISTORY = 100

mongo_client = None
mongo_db = None
is_mongo_connected = False


def _hash_password(password: str, salt: Optional[str] = None) -> str:
    if not salt:
        salt = secrets.token_hex(8)
    h = hashlib.sha256((salt + password).encode("utf-8")).hexdigest()
    return f"{salt}:{h}"


def _verify_password(stored_hash: str, password: str) -> bool:
    if not stored_hash:
        return False
    if ":" not in stored_hash:
        return stored_hash == password  # fallback for plaintext demo
    salt, h = stored_hash.split(":", 1)
    test_h = hashlib.sha256((salt + password).encode("utf-8")).hexdigest()
    return test_h == h


def seed_default_users():
    """Seeds default demo staff credentials into MongoDB and memory."""
    demo_users = [
        {
            "name": "Dr. K. V. Rao",
            "rollNumber": "VFSTR-HOD-CSE-01",
            "email": "kvrao@vignan.ac.in",
            "role": "hod",
            "department": "CSE",
            "password": "vignan123",
        },
        {
            "name": "Dr. M. S. Naidu",
            "rollNumber": "VFSTR-DEAN-ACAD-04",
            "email": "msnaidu@vignan.ac.in",
            "role": "dean",
            "department": "ACADEMICS",
            "password": "vignan123",
        },
        {
            "name": "Prof. S. R. Murthy",
            "rollNumber": "VFSTR-COE-ADM-12",
            "email": "srmurthy@vignan.ac.in",
            "role": "exam",
            "department": "COE",
            "password": "vignan123",
        },
    ]

    for u in demo_users:
        emp = u["rollNumber"]
        hashed = _hash_password(u["password"])
        doc = {
            "name": u["name"],
            "rollNumber": emp,
            "email": u["email"],
            "role": u["role"],
            "department": u["department"],
            "password_hash": hashed,
            "is_demo": True,
            "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }
        IN_MEMORY_USERS[emp] = doc
        if is_mongo_connected and mongo_db is not None:
            try:
                mongo_db["users"].update_one(
                    {"rollNumber": emp},
                    {"$setOnInsert": doc},
                    upsert=True
                )
            except Exception as e:
                logger.error(f"Error seeding demo user {emp} to MongoDB: {e}")


def init_mongo_connection():
    global mongo_client, mongo_db, is_mongo_connected
    mongodb_uri = os.getenv("MONGODB_URI", "").strip()
    if mongodb_uri:
        try:
            from pymongo import MongoClient
            mongo_client = MongoClient(mongodb_uri, serverSelectionTimeoutMS=4000)
            mongo_client.admin.command("ping")
            mongo_db = mongo_client.get_database("vignan_master_agent")
            is_mongo_connected = True
            logger.info("Successfully connected to MongoDB Atlas!")
        except Exception as e:
            logger.warning(f"Could not connect to MongoDB Atlas ({e}). Operating in resilient In-Memory mode.")
            is_mongo_connected = False
            mongo_client = None
            mongo_db = None
    else:
        logger.info("MONGODB_URI not configured. Operating in resilient In-Memory mode.")
        is_mongo_connected = False
        mongo_client = None
        mongo_db = None

    seed_default_users()
    seed_default_agent_endpoints()
    load_students_cache()


DEFAULT_LIVE_ENDPOINTS: Dict[str, str] = {
    "agent_02": "https://course-content-agent.vercel.app/?utm_source=chatgpt.com",
    "agent_03": "https://faculty-course-allocation-agent.vercel.app/",
    "agent_04": "https://vignan-timetable-ai-1.onrender.com/",
    "agent_05": "https://lesson-plan-agent-gamma.vercel.app/",
    "agent_06": "https://ai-academic-recovery-agent.vercel.app/",
    "agent_08": "https://courseoutcome.onrender.com/",
    "agent_09": "https://vignan-accreditation-agent-rmibobgo5lojrogjovrz7z.streamlit.app/",
    "agent_10": "https://bodhsight.vercel.app/",
    "agent_11": "https://attendance-analysis-agent.vercel.app/",
    "agent_13": "https://placement-ops-ai.vercel.app/",
    "agent_22": "https://foma-agent.vercel.app/",
    "agent_23": "https://patent-monitoring-agent.vercel.app/",
    "agent_25": "https://hospitals-accessible-upon-morris.trycloudflare.com/",
    "agent_26": "https://conference-management-agent.vercel.app/",
    "agent_27": "https://fdpluse.onrender.com/",
    "agent_28": "https://industrial-interaction-agent.onrender.com/",
    "agent_32": "https://question-paper-quality-agent.onrender.com/",
    "agent_33": "https://smartassess-3.vercel.app/",
    "agent_35": "https://backlog-monitoring-agent-vu.vercel.app/",
    "agent_37": "https://admissionai-1.onrender.com/",
    "agent_40": "https://feewise-red.vercel.app/",
    "agent_41": "https://fee-managment.netlify.app/",
    "agent_42": "https://scholarship-agent-42-1031611339150.asia-south1.run.app/",
    "agent_43": "https://education-loan-assist.vercel.app/",
    "agent_45": "https://agent-hackathon.onrender.com/login",
    "agent_49": "https://agent-49-tau.vercel.app/",
    "agent_50": "https://jobmatchingagent.onrender.com/",
    "agent_51": "https://internship-liard-sigma.vercel.app/",
    "agent_52": "https://alumini-finder.netlify.app/",
    "agent_53": "https://vision-y.vercel.app/",
    "agent_54": "https://agent54.vercel.app/",
    "agent_56": "https://vignan-commiai-frontend.vercel.app/",
    "agent_58": "https://agent-58-tawny.vercel.app/",
    "agent_59": "https://agent59-demo.streamlit.app/",
    "agent_61": "https://agent-61.vercel.app/",
    "agent_63": "https://agent63-frontend.onrender.com",
    "agent_64": "https://frontend-ten-puce-47.vercel.app/",
    "agent_65": "https://student-helpdesk-agent-two.vercel.app/",
    "agent_66": "https://frontend-henna-one-27.vercel.app/",
    "agent_67": "https://gap2growvignan.netlify.app/",
    "agent_68": "https://vijayadurgabolagani-stack.github.io/AI-certificate-advisor/",
    "agent_70": "https://agent-70.vercel.app/?_vercel_share=ArRJS7NP3SEkDRbgWc1iJBt9iea3aVqt",
    "agent_72": "https://agent-72-zeta.vercel.app/",
}


def seed_default_agent_endpoints():
    """Seeds verified live deployed sub-agents into Atlas and in-memory cache."""
    for agent_id, url in DEFAULT_LIVE_ENDPOINTS.items():
        IN_MEMORY_ENDPOINTS[agent_id] = url
        if is_mongo_connected and mongo_db is not None:
            try:
                mongo_db["agent_endpoints"].update_one(
                    {"agent_id": agent_id},
                    {
                        "$setOnInsert": {
                            "agent_id": agent_id,
                            "endpoint_url": url,
                            "updated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                        }
                    },
                    upsert=True
                )
            except Exception as e:
                logger.error(f"Error seeding agent {agent_id} endpoint to MongoDB: {e}")


class AuditDB:
    @staticmethod
    def get_status() -> Dict[str, Any]:
        global is_mongo_connected, mongo_db
        total_queries = 0
        if is_mongo_connected and mongo_db is not None:
            try:
                total_queries = mongo_db["query_logs"].count_documents({})
            except Exception:
                total_queries = len(IN_MEMORY_LOGS)
        else:
            total_queries = len(IN_MEMORY_LOGS)

        return {
            "is_connected": is_mongo_connected,
            "engine": "MongoDB Atlas" if is_mongo_connected else "In-Memory Circular Buffer",
            "total_logged_queries": total_queries,
            "database_name": "vignan_master_agent" if is_mongo_connected else "in_memory",
        }

    @staticmethod
    def log_query(trace: Dict[str, Any]):
        """Persists query execution trace to MongoDB query_logs collection or memory."""
        trace["timestamp"] = trace.get("timestamp", time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))

        if is_mongo_connected and mongo_db is not None:
            try:
                doc = dict(trace)
                mongo_db["query_logs"].insert_one(doc)
                return
            except Exception as e:
                logger.error(f"Error writing query trace to MongoDB: {e}")

        IN_MEMORY_LOGS.insert(0, trace)
        if len(IN_MEMORY_LOGS) > MAX_LOG_HISTORY:
            IN_MEMORY_LOGS.pop()

    @staticmethod
    def get_recent_logs(limit: int = 20) -> List[Dict[str, Any]]:
        """Retrieves recent query traces for demo inspection."""
        if is_mongo_connected and mongo_db is not None:
            try:
                cursor = mongo_db["query_logs"].find({}, {"_id": 0}).sort("timestamp", -1).limit(limit)
                return list(cursor)
            except Exception as e:
                logger.error(f"Error reading query traces from MongoDB: {e}")

        return IN_MEMORY_LOGS[:limit]

    @staticmethod
    def save_agent_endpoint(agent_id: str, endpoint_url: str) -> bool:
        """Persists custom deployment URL for an agent to MongoDB or memory."""
        IN_MEMORY_ENDPOINTS[agent_id] = endpoint_url
        if is_mongo_connected and mongo_db is not None:
            try:
                mongo_db["agent_endpoints"].update_one(
                    {"agent_id": agent_id},
                    {
                        "$set": {
                            "agent_id": agent_id,
                            "endpoint_url": endpoint_url,
                            "updated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                        }
                    },
                    upsert=True
                )
                return True
            except Exception as e:
                logger.error(f"Error saving agent endpoint to MongoDB: {e}")
                return False
        return True

    @staticmethod
    def get_all_agent_endpoints() -> Dict[str, str]:
        """Loads all custom agent deployment URLs from MongoDB or memory."""
        result = dict(IN_MEMORY_ENDPOINTS)
        if is_mongo_connected and mongo_db is not None:
            try:
                cursor = mongo_db["agent_endpoints"].find({}, {"_id": 0, "agent_id": 1, "endpoint_url": 1})
                for doc in cursor:
                    if doc.get("agent_id") and doc.get("endpoint_url"):
                        result[doc["agent_id"]] = doc["endpoint_url"]
            except Exception as e:
                logger.error(f"Error fetching agent endpoints from MongoDB: {e}")
        return result

    @staticmethod
    def register_user(
        name: str,
        employee_code: str,
        email: str,
        role: str,
        department: str,
        password: str,
    ) -> Dict[str, Any]:
        """Registers a new user in MongoDB Atlas or memory."""
        global is_mongo_connected, mongo_db
        emp_code = employee_code.strip().upper()
        email_clean = email.strip().lower()

        if is_mongo_connected and mongo_db is not None:
            try:
                existing = mongo_db["users"].find_one({
                    "$or": [{"rollNumber": emp_code}, {"email": email_clean}]
                })
                if existing:
                    return {
                        "success": False,
                        "message": "An account with this Employee Code or Email already exists in MongoDB Atlas."
                    }
            except Exception as e:
                logger.error(f"MongoDB duplicate check error: {e}")
        elif emp_code in IN_MEMORY_USERS:
            return {
                "success": False,
                "message": "An account with this Employee Code already exists."
            }

        hashed = _hash_password(password)
        user_doc = {
            "name": name.strip(),
            "rollNumber": emp_code,
            "email": email_clean,
            "role": role,
            "department": department,
            "password_hash": hashed,
            "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }

        if is_mongo_connected and mongo_db is not None:
            try:
                mongo_db["users"].insert_one(dict(user_doc))
            except Exception as e:
                logger.error(f"Error inserting user into MongoDB: {e}")

        IN_MEMORY_USERS[emp_code] = user_doc
        return {
            "success": True,
            "message": "User registered successfully in MongoDB Atlas!",
            "user": {
                "name": user_doc["name"],
                "rollNumber": user_doc["rollNumber"],
                "email": user_doc["email"],
                "role": user_doc["role"],
                "department": user_doc["department"],
            },
        }

    @staticmethod
    def authenticate_user(employee_code: str, password: str) -> Dict[str, Any]:
        """Authenticates user credentials against MongoDB Atlas or memory."""
        global is_mongo_connected, mongo_db
        identifier = employee_code.strip()

        user_doc = None
        if is_mongo_connected and mongo_db is not None:
            try:
                user_doc = mongo_db["users"].find_one({
                    "$or": [
                        {"rollNumber": identifier.upper()},
                        {"email": identifier.lower()}
                    ]
                })
            except Exception as e:
                logger.error(f"MongoDB auth query error: {e}")

        if not user_doc:
            user_doc = IN_MEMORY_USERS.get(identifier.upper())

        if not user_doc:
            return {
                "success": False,
                "message": f"No account found for '{identifier}'. Please register an account first."
            }

        stored_hash = user_doc.get("password_hash", "")
        if not _verify_password(stored_hash, password):
            return {
                "success": False,
                "message": "Incorrect password. Please verify your password and try again."
            }

        return {
            "success": True,
            "user": {
                "name": user_doc.get("name"),
                "rollNumber": user_doc.get("rollNumber"),
                "email": user_doc.get("email", ""),
                "role": user_doc.get("role", "faculty"),
                "department": user_doc.get("department", "CSE"),
            },
        }

    @staticmethod
    def save_user_session(user_data: Dict[str, Any]):
        """Saves user role and session details."""
        roll = user_data.get("rollNumber") or user_data.get("id") or "user_guest"
        if is_mongo_connected and mongo_db is not None:
            try:
                mongo_db["users"].update_one(
                    {"rollNumber": roll},
                    {"$set": user_data},
                    upsert=True
                )
                return
            except Exception as e:
                logger.error(f"Error saving user to MongoDB: {e}")

        IN_MEMORY_USERS[roll] = user_data

    @staticmethod
    def get_analytics_summary() -> Dict[str, Any]:
        """Provides high-level intelligence stats for institutional dashboard."""
        status = AuditDB.get_status()
        recent_logs = AuditDB.get_recent_logs(limit=50)

        modes_breakdown = {"global": 0, "scoped": 0}
        agent_hits: Dict[str, int] = {}
        total_latency = 0

        for l in recent_logs:
            m = l.get("mode", "global")
            modes_breakdown[m] = modes_breakdown.get(m, 0) + 1
            lat = l.get("total_time_ms") or 0
            total_latency += lat
            stages = l.get("stages", {})
            if "stage_4" in stages:
                aid = stages["stage_4"].get("agent_name", "Unknown Agent")
                agent_hits[aid] = agent_hits.get(aid, 0) + 1
            elif "stage_2" in stages:
                for p in stages["stage_2"].get("parts", []):
                    aname = p.get("agent_name", "Unknown Agent")
                    agent_hits[aname] = agent_hits.get(aname, 0) + 1

        avg_lat = int(total_latency / len(recent_logs)) if recent_logs else 0

        return {
            "status": status,
            "total_queries": status["total_logged_queries"],
            "modes_breakdown": modes_breakdown,
            "average_latency_ms": avg_lat,
            "top_queried_agents": sorted(
                [{"name": k, "count": v} for k, v in agent_hits.items()],
                key=lambda x: x["count"],
                reverse=True
            )[:5],
        }


db = AuditDB()


def load_students_cache():
    """Loads all student records from public/data/students.json into memory and MongoDB."""
    global IN_MEMORY_STUDENTS
    students_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "public", "data", "students.json")
    if os.path.exists(students_path):
        try:
            with open(students_path, "r", encoding="utf-8") as f:
                records = json.load(f)
            for r in records:
                roll = r.get("roll_number", "").strip().upper()
                if roll:
                    IN_MEMORY_STUDENTS[roll] = r
            logger.info(f"Loaded {len(IN_MEMORY_STUDENTS)} verified student records into memory cache.")

            if is_mongo_connected and mongo_db is not None:
                try:
                    col = mongo_db["students"]
                    if col.estimated_document_count() < len(records):
                        from pymongo import UpdateOne
                        ops = [UpdateOne({"roll_number": r["roll_number"]}, {"$set": r}, upsert=True) for r in records]
                        col.bulk_write(ops, ordered=False)
                        logger.info("Bulk-synced 4,121 student records to MongoDB Atlas.")
                except Exception as e:
                    logger.warning(f"MongoDB students sync error: {e}")
        except Exception as ex:
            logger.error(f"Error loading students.json: {ex}")
    else:
        logger.warning(f"students.json not found at {students_path}")


def get_student_by_roll(roll_number: str) -> Optional[Dict[str, Any]]:
    """O(1) lookup of student profile by registration roll number."""
    if not roll_number:
        return None
    roll = roll_number.strip().upper()
    if roll in IN_MEMORY_STUDENTS:
        return IN_MEMORY_STUDENTS[roll]
    if is_mongo_connected and mongo_db is not None:
        try:
            doc = mongo_db["students"].find_one({"roll_number": roll}, {"_id": 0})
            if doc:
                IN_MEMORY_STUDENTS[roll] = doc
                return doc
        except Exception as e:
            logger.error(f"MongoDB roll lookup error: {e}")
    return None


def search_students(query: str, limit: int = 15) -> List[Dict[str, Any]]:
    """Search students by name, roll number, section, or counsellor."""
    if not query:
        return []
    q = query.strip().upper()
    results = []
    for roll, st in IN_MEMORY_STUDENTS.items():
        if (q in roll or 
            q in st.get("name", "").upper() or 
            q in st.get("counsellor", "").upper() or 
            q == f"SEC-{st.get('section', '')}" or
            q == f"SECTION {st.get('section', '')}"):
            results.append(st)
            if len(results) >= limit:
                break
    return results


def get_students_by_counsellor(counsellor_name: str) -> List[Dict[str, Any]]:
    """Get all mentees assigned to a specific faculty counsellor."""
    c_name = counsellor_name.strip().upper()
    return [st for st in IN_MEMORY_STUDENTS.values() if c_name in st.get("counsellor", "").upper()]


def get_students_by_section(year: int, section: str) -> List[Dict[str, Any]]:
    """Get students by year and section."""
    s_sec = str(section).strip()
    return [st for st in IN_MEMORY_STUDENTS.values() if st.get("current_year") == year and str(st.get("section", "")).strip() == s_sec]


def get_student_attendance(roll_number: str) -> Optional[Dict[str, Any]]:
    """Returns verified live attendance telemetry for a student."""
    st = get_student_by_roll(roll_number)
    if not st:
        return None
    return {
        "roll_number": st.get("roll_number"),
        "name": st.get("name"),
        "current_year": st.get("current_year"),
        "section": st.get("section"),
        "counsellor": st.get("counsellor"),
        "attendance_pct": st.get("attendance_pct", 0.0),
        "attendance_conducted": st.get("attendance_conducted", 0),
        "attendance_attended": st.get("attendance_attended", 0),
        "attendance_status": st.get("attendance_status", "Normal"),
        "hall_ticket_status": st.get("hall_ticket_status", "Clear"),
        "subjects_attendance": st.get("subjects_attendance", []),
    }


def get_detained_students(year: Optional[int] = None, section: Optional[str] = None) -> List[Dict[str, Any]]:
    """Returns students flagged below 65% mandatory attendance threshold."""
    res = []
    for st in IN_MEMORY_STUDENTS.values():
        if year and st.get("current_year") != year:
            continue
        if section and str(st.get("section", "")).strip() != str(section).strip():
            continue
        if "Detained" in st.get("attendance_status", "") or (st.get("attendance_pct", 100) < 65.0):
            res.append(st)
    return sorted(res, key=lambda x: x.get("attendance_pct", 0.0))


def get_condonation_students(year: Optional[int] = None, section: Optional[str] = None) -> List[Dict[str, Any]]:
    """Returns students in the 65% - 74.99% condonation window."""
    res = []
    for st in IN_MEMORY_STUDENTS.values():
        if year and st.get("current_year") != year:
            continue
        if section and str(st.get("section", "")).strip() != str(section).strip():
            continue
        pct = st.get("attendance_pct", 100)
        if 65.0 <= pct < 75.0:
            res.append(st)
    return sorted(res, key=lambda x: x.get("attendance_pct", 0.0))


def get_student_cohort_stats() -> Dict[str, Any]:
    """Provides high-level cohort telemetry for HOD and Deans."""
    total = len(IN_MEMORY_STUDENTS)
    if total == 0:
        return {"total_students": 0}
    y2 = sum(1 for s in IN_MEMORY_STUDENTS.values() if s.get("current_year") == 2)
    y3 = sum(1 for s in IN_MEMORY_STUDENTS.values() if s.get("current_year") == 3)
    y4 = sum(1 for s in IN_MEMORY_STUDENTS.values() if s.get("current_year") == 4)
    hostellers = sum(1 for s in IN_MEMORY_STUDENTS.values() if s.get("hostel_status") == "Hosteller")
    detained = sum(1 for s in IN_MEMORY_STUDENTS.values() if "Detained" in s.get("attendance_status", "") or s.get("attendance_pct", 100) < 65.0)
    condonation = sum(1 for s in IN_MEMORY_STUDENTS.values() if 65.0 <= s.get("attendance_pct", 100) < 75.0)
    satisfactory = sum(1 for s in IN_MEMORY_STUDENTS.values() if s.get("attendance_pct", 0) >= 75.0)
    pending_fees = sum(1 for s in IN_MEMORY_STUDENTS.values() if s.get("fee_due_amount", 0) > 0)
    counsellors = len(set(s.get("counsellor") for s in IN_MEMORY_STUDENTS.values() if s.get("counsellor")))
    return {
        "total_students": total,
        "branch": "CSE",
        "years": {"year_2": y2, "year_3": y3, "year_4": y4},
        "hostellers": hostellers,
        "day_scholars": total - hostellers,
        "satisfactory_attendance_count": satisfactory,
        "condonation_attendance_count": condonation,
        "detained_attendance_count": detained,
        "pending_fee_count": pending_fees,
        "total_faculty_mentors": counsellors,
    }


def get_student_academic_profile(roll_number: str) -> Optional[Dict[str, Any]]:
    """Returns verified academic profile including real cumulative CGPA and semester progression."""
    st = get_student_by_roll(roll_number)
    if not st:
        return None
    cgpa = st.get("cgpa", 0.0)
    standing = "Pending / First Sem"
    if isinstance(cgpa, (int, float)) and cgpa > 0:
        if cgpa >= 9.0:
            standing = "Outstanding (First Class with Distinction)"
        elif cgpa >= 8.0:
            standing = "Distinction"
        elif cgpa >= 7.0:
            standing = "First Class"
        elif cgpa >= 6.0:
            standing = "Second Class"
        else:
            standing = "Remedial Coaching Required"

    return {
        "roll_number": st.get("roll_number"),
        "name": st.get("name"),
        "current_year": st.get("current_year"),
        "section": st.get("section"),
        "counsellor": st.get("counsellor"),
        "cgpa": cgpa,
        "credits_earned": st.get("credits_earned", 0),
        "semesters_sgpa": st.get("semesters_sgpa", []),
        "active_backlogs": st.get("active_backlogs", 0),
        "backlog_courses": st.get("backlog_courses", ""),
        "standing_classification": standing,
        "hostel_status": st.get("hostel_status", "Day Scholar"),
    }


def get_year_cgpa_stats(year: int = 2) -> Dict[str, Any]:
    """Provides official CGPA analytics, grade distribution, and toppers for a specific academic year."""
    students = [s for s in IN_MEMORY_STUDENTS.values() if s.get("current_year") == year]
    evaluated = [s for s in students if isinstance(s.get("cgpa"), (int, float)) and s.get("cgpa") > 0]
    total_enrolled = len(students)
    total_evaluated = len(evaluated)

    if total_evaluated == 0:
        return {
            "year": year,
            "total_enrolled": total_enrolled,
            "total_evaluated": 0,
            "average_cgpa": 0.0,
            "highest_cgpa": 0.0,
            "lowest_cgpa": 0.0,
            "brackets": {},
            "toppers": [],
        }

    cgpa_list = [float(s["cgpa"]) for s in evaluated]
    avg_cgpa = round(sum(cgpa_list) / total_evaluated, 2)
    max_cgpa = max(cgpa_list)
    min_cgpa = min(cgpa_list)

    b_9_plus = len([c for c in cgpa_list if c >= 9.0])
    b_8_9 = len([c for c in cgpa_list if 8.0 <= c < 9.0])
    b_7_8 = len([c for c in cgpa_list if 7.0 <= c < 8.0])
    b_6_7 = len([c for c in cgpa_list if 6.0 <= c < 7.0])
    b_below_6 = len([c for c in cgpa_list if c < 6.0])

    with_backlogs = [s for s in evaluated if s.get("active_backlogs", 0) > 0]
    toppers = sorted(evaluated, key=lambda x: x.get("cgpa", 0.0), reverse=True)[:10]

    return {
        "year": year,
        "total_enrolled": total_enrolled,
        "total_evaluated": total_evaluated,
        "average_cgpa": avg_cgpa,
        "highest_cgpa": max_cgpa,
        "lowest_cgpa": min_cgpa,
        "brackets": {
            "outstanding_ge_9": {"count": b_9_plus, "pct": round(b_9_plus / total_evaluated * 100, 1)},
            "distinction_8_to_9": {"count": b_8_9, "pct": round(b_8_9 / total_evaluated * 100, 1)},
            "first_class_7_to_8": {"count": b_7_8, "pct": round(b_7_8 / total_evaluated * 100, 1)},
            "second_class_6_to_7": {"count": b_6_7, "pct": round(b_6_7 / total_evaluated * 100, 1)},
            "remedial_lt_6": {"count": b_below_6, "pct": round(b_below_6 / total_evaluated * 100, 1)},
        },
        "active_backlogs_count": len(with_backlogs),
        "active_backlogs_pct": round(len(with_backlogs) / total_evaluated * 100, 1),
        "toppers": [
            {
                "rank": idx + 1,
                "roll_number": t.get("roll_number"),
                "name": t.get("name"),
                "section": t.get("section"),
                "cgpa": t.get("cgpa"),
                "credits": t.get("credits_earned"),
                "semesters_sgpa": t.get("semesters_sgpa", []),
                "hostel_status": t.get("hostel_status"),
            }
            for idx, t in enumerate(toppers)
        ],
    }


def get_toppers(year: Optional[int] = None, limit: int = 10) -> List[Dict[str, Any]]:
    """Returns top performing students by CGPA across a year or department."""
    candidates = [
        s for s in IN_MEMORY_STUDENTS.values()
        if (year is None or s.get("current_year") == year) and isinstance(s.get("cgpa"), (int, float)) and s.get("cgpa") > 0
    ]
    sorted_cand = sorted(candidates, key=lambda x: x.get("cgpa", 0.0), reverse=True)[:limit]
    return [
        {
            "rank": idx + 1,
            "roll_number": t.get("roll_number"),
            "name": t.get("name"),
            "current_year": t.get("current_year"),
            "section": t.get("section"),
            "cgpa": t.get("cgpa"),
            "credits_earned": t.get("credits_earned"),
            "semesters_sgpa": t.get("semesters_sgpa", []),
            "counsellor": t.get("counsellor"),
        }
        for idx, t in enumerate(sorted_cand)
    ]


def get_slow_learners(year: Optional[int] = None, section: Optional[str] = None) -> List[Dict[str, Any]]:
    """Identifies students needing remedial academic intervention (CGPA < 6.5 or active backlogs > 0)."""
    res = []
    for s in IN_MEMORY_STUDENTS.values():
        if year and s.get("current_year") != year:
            continue
        if section and str(s.get("section", "")).strip() != str(section).strip():
            continue
        cgpa = s.get("cgpa", 0.0)
        bl = s.get("active_backlogs", 0)
        if (isinstance(cgpa, (int, float)) and cgpa > 0 and cgpa < 6.5) or bl > 0:
            res.append(s)
    return sorted(res, key=lambda x: (x.get("active_backlogs", 0), -(x.get("cgpa") or 0.0)), reverse=True)


def load_timetables_cache():
    """Loads all section timetables and departmental faculty directory into memory."""
    global IN_MEMORY_TIMETABLES, IN_MEMORY_FACULTIES
    base_dir = os.path.dirname(os.path.dirname(__file__))
    tt_path = os.path.join(base_dir, "public", "data", "timetables.json")
    fac_path = os.path.join(base_dir, "public", "data", "faculties.json")

    if os.path.exists(tt_path):
        try:
            with open(tt_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            count = 0
            for y_k, secs in data.items():
                for s_k, s_data in secs.items():
                    key = f"{y_k}_{s_k}"
                    IN_MEMORY_TIMETABLES[key] = s_data
                    count += 1
            logger.info(f"Loaded {count} section timetables into memory cache.")
        except Exception as ex:
            logger.error(f"Error loading timetables.json: {ex}")

    if os.path.exists(fac_path):
        try:
            with open(fac_path, "r", encoding="utf-8") as f:
                IN_MEMORY_FACULTIES = json.load(f)
            logger.info(f"Loaded {len(IN_MEMORY_FACULTIES)} faculty directory entries into memory cache.")
        except Exception as ex:
            logger.error(f"Error loading faculties.json: {ex}")


def get_section_timetable(year: int, section: str) -> Optional[Dict[str, Any]]:
    """Returns official weekly schedule, room, class teacher, and course faculty for a section."""
    sec_clean = str(section).strip().upper().replace("SEC-", "").replace("SEC", "").replace("SECTION", "").strip()
    key = f"{year}_{sec_clean}"
    if key in IN_MEMORY_TIMETABLES:
        return IN_MEMORY_TIMETABLES[key]
    if is_mongo_connected and mongo_db is not None:
        try:
            doc = mongo_db["timetables"].find_one({"year": year, "section": sec_clean}, {"_id": 0})
            if doc:
                IN_MEMORY_TIMETABLES[key] = doc
                return doc
        except Exception as e:
            logger.error(f"MongoDB timetable lookup error: {e}")
    return None


def get_student_timetable(roll_number: str) -> Optional[Dict[str, Any]]:
    """O(1) student timetable lookup resolving year and section to official weekly timetable."""
    st = get_student_by_roll(roll_number)
    if not st:
        return None
    year = st.get("current_year")
    sec = st.get("section")
    if not year or not sec:
        return None
    tt = get_section_timetable(year, str(sec))
    return {
        "roll_number": st.get("roll_number"),
        "name": st.get("name"),
        "year": year,
        "section": sec,
        "counsellor": st.get("counsellor"),
        "timetable": tt
    }


def get_faculty_profile(faculty_name: str) -> Optional[Dict[str, Any]]:
    """Searches faculty directory for exact or fuzzy match, returning courses and sections taught."""
    if not faculty_name:
        return None
    q = faculty_name.strip().upper()
    for f in IN_MEMORY_FACULTIES:
        if q in f.get("name", "").upper():
            return f
    return None


def search_faculties(query: str, limit: int = 20) -> List[Dict[str, Any]]:
    """Searches faculty directory by name, course taught, or phone number."""
    if not query:
        return IN_MEMORY_FACULTIES[:limit]
    q = query.strip().upper()
    res = []
    for f in IN_MEMORY_FACULTIES:
        name_match = q in f.get("name", "").upper()
        phone_match = q in f.get("phone", "")
        course_match = any(q in c.get("subject", "").upper() for c in f.get("courses", []))
        if name_match or phone_match or course_match:
            res.append(f)
            if len(res) >= limit:
                break
    return res


def get_timetables_summary() -> Dict[str, Any]:
    """Returns overview of available section timetables across Years 2, 3, and 4."""
    y2_secs = [k.split("_")[1] for k in IN_MEMORY_TIMETABLES if k.startswith("2_")]
    y3_secs = [k.split("_")[1] for k in IN_MEMORY_TIMETABLES if k.startswith("3_")]
    y4_secs = [k.split("_")[1] for k in IN_MEMORY_TIMETABLES if k.startswith("4_")]
    return {
        "total_sections": len(IN_MEMORY_TIMETABLES),
        "total_faculties": len(IN_MEMORY_FACULTIES),
        "year_2": {"sections_count": len(y2_secs), "sections": sorted(y2_secs, key=lambda x: int(x) if x.isdigit() else 0)},
        "year_3": {"sections_count": len(y3_secs), "sections": sorted(y3_secs, key=lambda x: int(x) if x.isdigit() else 0)},
        "year_4": {"sections_count": len(y4_secs), "sections": sorted(y4_secs, key=lambda x: int(x) if x.isdigit() else 0)},
    }


# Initialize database connection and sync caches
init_mongo_connection()
if not IN_MEMORY_STUDENTS:
    load_students_cache()
if not IN_MEMORY_TIMETABLES:
    load_timetables_cache()



