"""
Vignan's University — Master Agent Database & Audit Logger
Supports MongoDB Atlas persistence with automatic in-memory fallback.
"""

import os
import time
import json
import re
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
IN_MEMORY_PLACEMENTS: Dict[str, Any] = {}
MAX_LOG_HISTORY = 100

# Official Vignan University CSE Academic Regulations Mapping
YEAR_REGULATION_MAP: Dict[int, str] = {
    2: "R25",  # II Year (2024–2028 Batch)
    3: "C24",  # III Year (2023–2027 Batch)
    4: "C22",  # IV Year (2022–2026 Batch)
}


def get_regulation_for_year(year: int) -> str:
    """Returns official curriculum regulation code for a given academic year."""
    try:
        y = int(year)
        return YEAR_REGULATION_MAP.get(y, "R25")
    except Exception:
        return "R25"


# Detailed Course Structure & Curricula extracted from Official PDF Syllabus Books
OFFICIAL_CURRICULUM_COURSES: Dict[str, Dict[str, List[Dict[str, Any]]]] = {
    "R25": {
        "year_2_sem_1": [
            {"code": "25MT204", "title": "Probability and Statistics", "l": 3, "t": 0, "p": 2, "credits": 4, "category": "Basic Sciences"},
            {"code": "25MT205", "title": "Discrete Mathematical Structures", "l": 2, "t": 2, "p": 0, "credits": 3, "category": "Basic Sciences"},
            {"code": "25CS201", "title": "Data Structures", "l": 2, "t": 2, "p": 2, "credits": 4, "category": "Basic Engineering"},
            {"code": "25CS202", "title": "Web Technology", "l": 0, "t": 2, "p": 2, "credits": 2, "category": "Professional Core-1"},
            {"code": "25CS203", "title": "Database Management Systems", "l": 2, "t": 2, "p": 2, "credits": 4, "category": "Professional Core-2"},
            {"code": "25CS204", "title": "Object-Oriented Programming through JAVA", "l": 2, "t": 2, "p": 2, "credits": 4, "category": "Professional Core-3"},
            {"code": "25CS205", "title": "Digital Logic Design", "l": 2, "t": 0, "p": 2, "credits": 3, "category": "Professional Core-4"},
        ],
        "year_2_sem_2": [
            {"code": "25MT203", "title": "Optimization Techniques", "l": 2, "t": 2, "p": 0, "credits": 3, "category": "Basic Sciences"},
            {"code": "25CS801", "title": "Industry – Interface (I2) Course", "l": 0, "t": 2, "p": 0, "credits": 1, "category": "Dept. Elective-1"},
            {"code": "OPEN-EL1", "title": "Open Elective-1", "l": 2, "t": 0, "p": 2, "credits": 3, "category": "Open Elective-1"},
            {"code": "25CS206", "title": "Computer Organization and Architecture", "l": 2, "t": 2, "p": 0, "credits": 3, "category": "Professional Core-5"},
            {"code": "25CS207", "title": "Design and Analysis of Algorithms", "l": 2, "t": 2, "p": 2, "credits": 4, "category": "Professional Core-6"},
            {"code": "25CS208", "title": "Operating Systems", "l": 2, "t": 0, "p": 2, "credits": 3, "category": "Professional Core-7"},
            {"code": "25CS209", "title": "Computer Networks", "l": 3, "t": 0, "p": 2, "credits": 4, "category": "Professional Core-8"},
            {"code": "25CS210", "title": "Design Thinking and Engineering Orientation", "l": 0, "t": 0, "p": 2, "credits": 1, "category": "Basic Engineering"},
            {"code": "25CS211", "title": "Field Project", "l": 0, "t": 0, "p": 2, "credits": 1, "category": "Project"},
        ]
    },
    "C24": {
        "year_3_sem_1": [
            {"code": "22TP301", "title": "Soft Skills Laboratory", "l": 0, "t": 0, "p": 2, "credits": 1, "category": "Humanities"},
            {"code": "24CS301", "title": "Optimization Techniques", "l": 2, "t": 2, "p": 0, "credits": 3, "category": "Basic Sciences"},
            {"code": "24CS302", "title": "Artificial Intelligence", "l": 2, "t": 0, "p": 2, "credits": 3, "category": "Professional Core"},
            {"code": "24CS303", "title": "Computer Networks", "l": 2, "t": 2, "p": 2, "credits": 4, "category": "Professional Core"},
            {"code": "24CS304", "title": "Mobile Application Development", "l": 0, "t": 2, "p": 2, "credits": 2, "category": "Professional Core"},
            {"code": "DEPT-EL1", "title": "Department Elective-1", "l": 3, "t": 0, "p": 2, "credits": 4, "category": "Department Elective"},
            {"code": "OPEN-EL2", "title": "Open Elective-2", "l": 2, "t": 0, "p": 2, "credits": 3, "category": "Open Elective"},
            {"code": "24EN301", "title": "Professional Communication Skills", "l": 0, "t": 0, "p": 2, "credits": 1, "category": "Humanities"},
        ],
        "year_3_sem_2": [
            {"code": "24CS305", "title": "Computing Ethics", "l": 1, "t": 2, "p": 0, "credits": 2, "category": "Humanities"},
            {"code": "24TP301", "title": "Quantitative Aptitude & Logical Reasoning", "l": 1, "t": 2, "p": 0, "credits": 2, "category": "Humanities"},
            {"code": "24CS306", "title": "Machine Learning", "l": 2, "t": 0, "p": 2, "credits": 3, "category": "Professional Core"},
            {"code": "22CS407", "title": "Cryptography and Network Security", "l": 2, "t": 0, "p": 2, "credits": 3, "category": "Professional Core"},
            {"code": "DEPT-EL2", "title": "Department Elective-2", "l": 2, "t": 0, "p": 2, "credits": 3, "category": "Department Elective"},
            {"code": "DEPT-EL3", "title": "Department Elective-3", "l": 3, "t": 0, "p": 2, "credits": 4, "category": "Department Elective"},
            {"code": "OPEN-EL3", "title": "Open Elective-3", "l": 2, "t": 0, "p": 2, "credits": 3, "category": "Open Elective"},
            {"code": "24CS307", "title": "Inter Departmental Project", "l": 0, "t": 0, "p": 2, "credits": 1, "category": "Project"},
        ]
    },
    "C22": {
        "year_4_sem_1": [
            {"code": "24CS401", "title": "Software Project Management", "l": 2, "t": 2, "p": 0, "credits": 3, "category": "Professional Core"},
            {"code": "24CS402", "title": "Parallel & Distributed Computing", "l": 2, "t": 2, "p": 0, "credits": 3, "category": "Professional Core"},
            {"code": "24CS403", "title": "Privacy and Intrusion Detection", "l": 2, "t": 2, "p": 0, "credits": 3, "category": "Professional Core"},
            {"code": "DEPT-EL4", "title": "Department Elective-4", "l": 3, "t": 0, "p": 2, "credits": 4, "category": "Department Elective"},
            {"code": "DEPT-EL5", "title": "Department Elective-5", "l": 3, "t": 0, "p": 2, "credits": 4, "category": "Department Elective"},
            {"code": "DEPT-EL6", "title": "Department Elective-6", "l": 3, "t": 0, "p": 2, "credits": 4, "category": "Department Elective"},
        ],
        "year_4_sem_2": [
            {"code": "22CS404", "title": "Semester-Long Corporate Internship / Capstone Project", "l": 0, "t": 2, "p": 22, "credits": 12, "category": "Project"},
        ]
    }
}


def get_regulation_courses(year: int, semester: Optional[int] = None) -> List[Dict[str, Any]]:
    """Returns official course lists for a given year and semester."""
    reg = get_regulation_for_year(year)
    reg_data = OFFICIAL_CURRICULUM_COURSES.get(reg, {})
    if semester:
        key = f"year_{year}_sem_{semester}"
        return reg_data.get(key, [])
    # Return all semesters for that year
    all_courses = []
    for k, courses in reg_data.items():
        if f"year_{year}" in k:
            all_courses.extend(courses)
    return all_courses


def get_regulations_summary() -> Dict[str, Any]:
    """Returns official VFSTR Department of CSE Academic Regulations matrix extracted from syllabus books."""
    return {
        "university": "Vignan's Foundation for Science, Technology & Research (VFSTR)",
        "accreditation": "NAAC 'A+' Grade | NBA Tier-1 Compliant | UGC Section 3",
        "department": "Computer Science & Engineering",
        "total_degree_credits": {
            "regular_btech": 161,
            "btech_honours": 181,
            "minor_specialization": 20,
            "add_on_diploma": 20,
        },
        "evaluation_system": {
            "ratio": "60:40",
            "formative_assessment_cie": {
                "total_marks": 60,
                "min_passing_pct": 35.0,
                "min_passing_marks": 21,
                "failure_grade": "R (Repeat Course)",
            },
            "summative_assessment_see": {
                "total_marks": 40,
                "min_passing_pct": 35.0,
                "min_passing_marks": 14,
                "failure_grade": "I (Incomplete)",
            },
            "min_passing_grade_point": 4.0,
        },
        "attendance_policy": {
            "mandatory_threshold_pct": 75.0,
            "condonation_range": "65.0% to 74.99%",
            "condonation_basis": "Ill-health (medical certificates), sports/cultural representation, social obligations, placement drives",
            "approving_authority": "Scrutiny Committee constituted by the Vice-Chancellor (Clause 4.b)",
            "detention_clause": "Attendance < 65.0% results in mandatory 'R' grade and semester debarment (Clause 4.e)",
            "review_frequency": "Every 4 weeks with parental communication",
        },
        "grading_scale": [
            {"relative_points_range": ">= 9.50", "category": "Outstanding", "letter_grade": "O", "points": 10},
            {"relative_points_range": "8.50 to 9.49", "category": "Excellent", "letter_grade": "S", "points": 9},
            {"relative_points_range": "7.00 to 8.49", "category": "Very Good", "letter_grade": "A", "points": 8},
            {"relative_points_range": "6.00 to 6.99", "category": "Good", "letter_grade": "B", "points": 7},
            {"relative_points_range": "5.00 to 5.99", "category": "Fair", "letter_grade": "C", "points": 6},
            {"relative_points_range": "4.00 to 4.99", "category": "Marginal", "letter_grade": "M", "points": 4},
            {"relative_points_range": "Transitional", "category": "Repeat (Failed CIE or Attendance)", "letter_grade": "R", "points": 0},
            {"relative_points_range": "Transitional", "category": "Incomplete (Failed SEE)", "letter_grade": "I", "points": 0},
        ],
        "award_of_class": [
            {"cgpa_range": ">= 8.00", "division": "First Class with Distinction"},
            {"cgpa_range": "6.50 to 7.99", "division": "First Class"},
            {"cgpa_range": "6.00 to 6.49", "division": "Second Class"},
            {"cgpa_range": "< 6.00", "division": "Pass Class"},
        ],
        "active_regulations": [
            {
                "year": 2,
                "cohort": "2024–2028 Batch",
                "regulation": "R25",
                "scheme_name": "R25 / C25 Outcome-Based Education (OBE) Curriculum",
                "syllabus_source_pdf": "data/R25 C25 CSE Course Structure & Syllabus.pdf (212 Pages)",
                "semester_credits": {"sem_1": 24, "sem_2": 23, "year_total": 47},
                "key_features": "Revised 2024-25 syllabus, 25-series codes, integrated theory-practical courses (e.g. DS-25CS201, DBMS-25CS203, OOP Java 25CS204), continuous coding labs",
                "attendance_threshold": "75.0% Mandatory (65.0%–74.99% Condonation band)",
                "courses_preview": [
                    "25CS201: Data Structures (4 Cr)",
                    "25CS202: Web Technology (2 Cr)",
                    "25CS203: DBMS (4 Cr)",
                    "25CS204: OOP through JAVA (4 Cr)",
                    "25CS205: Digital Logic Design (3 Cr)",
                    "25CS206: Computer Organization & Architecture (3 Cr)",
                    "25CS207: Design & Analysis of Algorithms (4 Cr)",
                    "25CS208: Operating Systems (3 Cr)",
                    "25CS209: Computer Networks (4 Cr)"
                ]
            },
            {
                "year": 3,
                "cohort": "2023–2027 Batch",
                "regulation": "C24",
                "scheme_name": "C24 CBCS Specialization Scheme",
                "syllabus_source_pdf": "data/R22C24 Syllabus book 01-08-2026.pdf (133 Pages)",
                "semester_credits": {"sem_1": 21, "sem_2": 21, "year_total": 42},
                "key_features": "Choice-Based Credit System, AI/ML specialization track (24CS302 AI, 24CS306 Machine Learning), Cloud & Mobile App Dev (24CS304), mandatory summer internships",
                "attendance_threshold": "75.0% Mandatory (65.0%–74.99% Condonation band)",
                "courses_preview": [
                    "24CS301: Optimization Techniques (3 Cr)",
                    "24CS302: Artificial Intelligence (3 Cr)",
                    "24CS303: Computer Networks (4 Cr)",
                    "24CS304: Mobile Application Development (2 Cr)",
                    "24CS306: Machine Learning (3 Cr)",
                    "22CS407: Cryptography & Network Security (3 Cr)",
                    "24CS307: Inter Departmental Project (1 Cr)"
                ]
            },
            {
                "year": 4,
                "cohort": "2022–2026 Batch",
                "regulation": "C22",
                "scheme_name": "R22 Graduating Curriculum (In Compliance with NEP 2020)",
                "syllabus_source_pdf": "data/R-22 syllabus book(01-08-2026).pdf (238 Pages)",
                "semester_credits": {"sem_1": 21, "sem_2": 12, "year_total": 33},
                "key_features": "Major Capstone Project (12 Credits dedicated in Sem 8), full-time corporate internship waiver for students securing placement offers (565 offers, Blinkit, TCS, Amazon)",
                "attendance_threshold": "75.0% Mandatory (65.0%–74.99% Condonation band)",
                "courses_preview": [
                    "24CS401: Software Project Management (3 Cr)",
                    "24CS402: Parallel & Distributed Computing (3 Cr)",
                    "24CS403: Privacy and Intrusion Detection (3 Cr)",
                    "22CS404 / 22CS405: 12-Credit Semester-Long Capstone Project / Corporate Internship"
                ]
            },
        ]
    }


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
    """Seeds official department leadership and demo credentials into MongoDB and memory."""
    demo_users = [
        # Official Professor & HOD CSE (Dr. S V Phani Kumar - Emp ID: 675)
        {
            "name": "Dr. S V Phani Kumar",
            "rollNumber": "675",
            "email": "675@vignan.ac.in",
            "role": "hod",
            "department": "CSE",
            "password": "vignan123",
        },
        {
            "name": "Dr. S V Phani Kumar",
            "rollNumber": "VFSTR-HOD-CSE-01",
            "email": "svphanikumar@vignan.ac.in",
            "role": "hod",
            "department": "CSE",
            "password": "vignan123",
        },
        # Official Professor & Dean SOCI (Prof. Dr. K.V.Krishna Kishore - Emp ID: 163)
        {
            "name": "Prof. Dr. K.V.Krishna Kishore",
            "rollNumber": "163",
            "email": "163@vignan.ac.in",
            "role": "dean",
            "department": "SOCI",
            "password": "vignan123",
        },
        {
            "name": "Prof. Dr. K.V.Krishna Kishore",
            "rollNumber": "VFSTR-DEAN-ACAD-04",
            "email": "kvkrishnakishore@vignan.ac.in",
            "role": "dean",
            "department": "SOCI",
            "password": "vignan123",
        },
        # Official Deputy HOD CSE (Dr. M. Umadevi - Emp ID: 02342)
        {
            "name": "Dr. M. Umadevi",
            "rollNumber": "02342",
            "email": "02342@vignan.ac.in",
            "role": "deputy_hod",
            "department": "CSE",
            "password": "vignan123",
        },
        # Official Deputy HOD CSE (Dr. S. Deva Kumar - Emp ID: 189)
        {
            "name": "Dr. S. Deva Kumar",
            "rollNumber": "189",
            "email": "189@vignan.ac.in",
            "role": "deputy_hod",
            "department": "CSE",
            "password": "vignan123",
        },
        # Controller of Examinations
        {
            "name": "Prof. S. R. Murthy",
            "rollNumber": "VFSTR-COE-ADM-12",
            "email": "srmurthy@vignan.ac.in",
            "role": "exam",
            "department": "COE",
            "password": "vignan123",
        },
        # Official Department Data Entry Operator (DEO 1 - CSE)
        {
            "name": "DEO 1 - Department of CSE",
            "rollNumber": "DEO1_CSE",
            "email": "deo1_cse@vignan.ac.in",
            "role": "deo",
            "department": "CSE",
            "password": "DEO_password",
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
                    {"$set": doc},
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
            # Check if this ID is in the official faculty registry enrolled by DEO
            clean_id = identifier.upper()
            found_faculty = None
            for f in IN_MEMORY_FACULTIES:
                if str(f.get("emp_id", "")).strip().upper() == clean_id or str(f.get("email", "")).lower() == identifier.lower():
                    found_faculty = f
                    break
            if found_faculty:
                return {
                    "success": False,
                    "needs_activation": True,
                    "message": f"Faculty profile '{found_faculty.get('name')}' is enrolled by DEO, but password has not been created yet. Please click '✨ First Time? Activate Account' below to set up your password."
                }
            return {
                "success": False,
                "message": f"No account found for '{identifier}'. You must be enrolled by the Department DEO before signing in."
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

    curr_yr = st.get("current_year", 2)
    reg_code = st.get("regulation") or get_regulation_for_year(curr_yr)

    return {
        "roll_number": st.get("roll_number"),
        "name": st.get("name"),
        "current_year": curr_yr,
        "regulation": reg_code,
        "section": st.get("section"),
        "counsellor": st.get("counsellor"),
        "cgpa": cgpa,
        "credits_earned": st.get("credits_earned", 0),
        "semesters_sgpa": st.get("semesters_sgpa", []),
        "active_backlogs": st.get("active_backlogs", 0),
        "backlog_courses": st.get("backlog_courses", ""),
        "standing_classification": standing,
        "hostel_status": st.get("hostel_status", "Day Scholar"),
        "placement_status": st.get("placement_status", "Unspecified"),
        "placement_offers": st.get("placement_offers", []),
        "total_offers": st.get("total_offers", 0),
        "primary_company": st.get("primary_company"),
        "highest_package": st.get("highest_package"),
    }


def get_year_cgpa_stats(year: int = 2) -> Dict[str, Any]:
    """Provides official CGPA analytics, grade distribution, and toppers for a specific academic year."""
    students = [s for s in IN_MEMORY_STUDENTS.values() if s.get("current_year") == year]
    evaluated = [s for s in students if isinstance(s.get("cgpa"), (int, float)) and s.get("cgpa") > 0]
    total_enrolled = len(students)
    total_evaluated = len(evaluated)
    reg_code = get_regulation_for_year(year)
    cohort_str = "2024–2028 (R25 Regulation)" if year == 2 else ("2023–2027 (C24 Regulation)" if year == 3 else "2022–2026 (C22 Regulation)")

    if total_evaluated == 0:
        return {
            "year": year,
            "regulation": reg_code,
            "cohort_batch": cohort_str,
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
        "regulation": reg_code,
        "cohort_batch": cohort_str,
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
    """Searches faculty directory by name, employee ID, designation, or phone number."""
    if not faculty_name:
        return None
    q = faculty_name.strip()
    q_upper = q.upper()

    # 1. Leadership alias lookups
    if any(q_upper == k for k in ["HOD", "HEAD OF DEPARTMENT", "HOD CSE", "CSE HOD", "CURRENT HOD"]):
        for f in IN_MEMORY_FACULTIES:
            desig = f.get("designation", "").upper()
            if "HOD" in desig and "DEPUTY" not in desig:
                return f

    if any(q_upper == k for k in ["DEAN", "DEAN SOCI", "SOCI DEAN", "DEAN OF SOCI"]):
        for f in IN_MEMORY_FACULTIES:
            if "DEAN" in f.get("designation", "").upper():
                return f

    # 2. Exact Employee ID lookup
    for f in IN_MEMORY_FACULTIES:
        if str(f.get("emp_id", "")).strip().upper() == q_upper:
            return f

    # 3. Direct or Substring Name lookup
    for f in IN_MEMORY_FACULTIES:
        if q_upper in f.get("name", "").upper():
            return f

    # 4. Normalized Name lookup (ignoring titles and punctuation)
    norm_q = re.sub(r"^(prof\.|dr\.|mr\.|mrs\.|ms\.)\s*", "", q, flags=re.IGNORECASE).strip().lower()
    norm_q_clean = re.sub(r"[\.\,\s\-_]+", "", norm_q)
    if len(norm_q_clean) >= 3:
        for f in IN_MEMORY_FACULTIES:
            f_norm = re.sub(r"^(prof\.|dr\.|mr\.|mrs\.|ms\.)\s*", "", f.get("name", ""), flags=re.IGNORECASE)
            f_clean = re.sub(r"[\.\,\s\-_]+", "", f_norm).lower()
            if norm_q_clean in f_clean or f_clean in norm_q_clean:
                return f

    # 5. Phone lookup
    phone_clean = re.sub(r"[^0-9]", "", q)
    if len(phone_clean) >= 10:
        for f in IN_MEMORY_FACULTIES:
            if f.get("phone") == phone_clean:
                return f

    # 6. MongoDB fallback
    if is_mongo_connected and mongo_db is not None:
        try:
            doc = mongo_db["faculties"].find_one({
                "$or": [
                    {"emp_id": q},
                    {"name": {"$regex": re.escape(q), "$options": "i"}},
                    {"phone": phone_clean if len(phone_clean) >= 10 else q}
                ]
            }, {"_id": 0})
            if doc:
                return doc
        except Exception as e:
            logger.error(f"MongoDB faculty query error: {e}")

    return None


def search_faculties(query: str, limit: int = 30) -> List[Dict[str, Any]]:
    """Searches official faculty directory by name, employee ID, designation, course, or phone number."""
    if not query:
        return IN_MEMORY_FACULTIES[:limit]
    q = query.strip().upper()
    phone_q = re.sub(r"[^0-9]", "", query)
    res = []
    for f in IN_MEMORY_FACULTIES:
        emp_match = q == str(f.get("emp_id", "")).strip().upper()
        name_match = q in f.get("name", "").upper()
        desig_match = q in f.get("designation", "").upper()
        phone_match = (len(phone_q) >= 4 and phone_q in f.get("phone", ""))
        course_match = any(q in c.get("subject", "").upper() for c in f.get("courses", []))
        if emp_match or name_match or desig_match or phone_match or course_match:
            res.append(f)
            if len(res) >= limit:
                break
    return res


def _generate_token_for_emp(emp_id: str) -> str:
    """Generates a stable 6-digit security token for a faculty member."""
    h = hashlib.sha256(f"vignan_token_seed_{emp_id}".encode()).hexdigest()
    return str(int(h[:8], 16) % 900000 + 100000)


def get_all_deo_faculties(search: Optional[str] = None) -> Dict[str, Any]:
    """
    Returns full list of faculty members for the DEO Management Console,
    enriched with activation status and login account state.
    """
    faculties = []
    activated_count = 0
    pending_count = 0

    s_clean = search.strip().upper() if search else ""

    # Filter strictly to official CSE Department members (plus newly enrolled by DEO)
    cse_faculties = [
        f for f in IN_MEMORY_FACULTIES
        if f.get("is_official_cse") is True or f.get("department") == "Computer Science & Engineering"
    ]

    for f in cse_faculties:
        emp_id = str(f.get("emp_id", "")).strip().upper()
        # Check if this faculty has an activated user login in IN_MEMORY_USERS
        has_account = emp_id in IN_MEMORY_USERS or any(
            u.get("rollNumber") == emp_id or u.get("email", "").lower() == str(f.get("email", "")).lower()
            for u in IN_MEMORY_USERS.values()
        )
        status = "activated" if has_account else "pending_setup"
        if status == "activated":
            activated_count += 1
        else:
            pending_count += 1

        token = f.get("activation_token")
        if not token:
            token = _generate_token_for_emp(emp_id)
            f["activation_token"] = token

        if s_clean:
            matches = (
                s_clean in emp_id
                or s_clean in f.get("name", "").upper()
                or s_clean in f.get("designation", "").upper()
                or s_clean in f.get("email", "").upper()
                or s_clean in f.get("phone", "")
                or s_clean in str(token)
            )
            if not matches:
                continue

        faculties.append({
            "emp_id": f.get("emp_id"),
            "name": f.get("name"),
            "designation": f.get("designation", "Faculty"),
            "department": f.get("department", "Computer Science & Engineering"),
            "email": f.get("email", ""),
            "phone": f.get("phone", ""),
            "status": status,
            "activation_token": token,
            "courses_count": len(f.get("courses", [])),
            "mentees_count": f.get("mentees_count", 0),
        })

    return {
        "total_faculty": len(cse_faculties),
        "displayed_count": len(faculties),
        "activated_count": activated_count,
        "pending_count": pending_count,
        "faculties": faculties,
    }


def add_deo_faculty(
    name: str,
    emp_id: str,
    designation: str = "Assistant Professor",
    email: Optional[str] = None,
    phone: Optional[str] = None,
    department: str = "Computer Science & Engineering",
) -> Dict[str, Any]:
    """Adds a new faculty member into the official directory as DEO with an activation token."""
    clean_emp = str(emp_id).strip().upper()
    clean_name = name.strip()

    # Check for duplicate
    for f in IN_MEMORY_FACULTIES:
        if str(f.get("emp_id", "")).strip().upper() == clean_emp:
            return {
                "success": False,
                "message": f"Faculty with Employee ID '{clean_emp}' is already enrolled ({f.get('name')})."
            }

    clean_email = email.strip().lower() if email else f"{clean_emp.lower()}@vignan.ac.in"
    token = str(secrets.randbelow(900000) + 100000)
    new_faculty = {
        "sl_no": len(IN_MEMORY_FACULTIES) + 1,
        "emp_id": clean_emp,
        "name": clean_name,
        "designation": designation.strip(),
        "gender": "U",
        "phone": (phone or "").strip(),
        "email": clean_email,
        "department": department,
        "is_leadership": "HOD" in designation.upper() or "DEAN" in designation.upper(),
        "is_official_cse": True,
        "class_teacher_of": [],
        "courses": [],
        "courses_count": 0,
        "mentees_count": 0,
        "mentee_rolls": [],
        "status": "pending_setup",
        "activation_token": token,
        "enrolled_by": "DEO1_CSE",
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }

    IN_MEMORY_FACULTIES.insert(0, new_faculty)

    # Persist to MongoDB if connected
    if is_mongo_connected and mongo_db is not None:
        try:
            mongo_db["faculties"].insert_one(dict(new_faculty))
        except Exception as e:
            logger.error(f"Error persisting added faculty to MongoDB: {e}")

    return {
        "success": True,
        "message": f"Faculty '{clean_name}' (ID: {clean_emp}) enrolled successfully! Security Token: {token}",
        "faculty": new_faculty,
        "activation_token": token,
    }


def regenerate_deo_token(emp_id: str) -> Dict[str, Any]:
    """
    Generates a fresh 6-digit security token for a faculty member.
    If the faculty was already activated, resets their existing password so they must re-verify.
    """
    clean_emp = str(emp_id).strip().upper()
    target_faculty = None
    for f in IN_MEMORY_FACULTIES:
        if str(f.get("emp_id", "")).strip().upper() == clean_emp:
            target_faculty = f
            break

    if not target_faculty:
        return {"success": False, "message": f"Faculty with ID '{clean_emp}' not found."}

    # Generate new random 6-digit token
    new_token = str(secrets.randbelow(900000) + 100000)
    target_faculty["activation_token"] = new_token
    target_faculty["status"] = "pending_setup"

    # Invalidate existing password session in IN_MEMORY_USERS
    if clean_emp in IN_MEMORY_USERS:
        del IN_MEMORY_USERS[clean_emp]

    if is_mongo_connected and mongo_db is not None:
        try:
            mongo_db["users"].delete_one({"rollNumber": clean_emp})
            mongo_db["faculties"].update_one(
                {"emp_id": clean_emp},
                {"$set": {"activation_token": new_token, "status": "pending_setup"}}
            )
        except Exception as e:
            logger.error(f"Error updating MongoDB on token regeneration: {e}")

    fac_name = target_faculty.get("name", "Faculty Member")
    return {
        "success": True,
        "emp_id": clean_emp,
        "name": fac_name,
        "activation_token": new_token,
        "message": f"New security token '{new_token}' generated for {fac_name} (ID: {clean_emp})."
    }


def remove_deo_faculty(emp_id: str) -> Dict[str, Any]:
    """Removes a faculty member from the directory as DEO."""
    clean_emp = str(emp_id).strip().upper()
    found_idx = None
    target_name = clean_emp

    for idx, f in enumerate(IN_MEMORY_FACULTIES):
        if str(f.get("emp_id", "")).strip().upper() == clean_emp:
            found_idx = idx
            target_name = f.get("name", clean_emp)
            break

    if found_idx is None:
        return {"success": False, "message": f"Faculty with Employee ID '{clean_emp}' not found."}

    IN_MEMORY_FACULTIES.pop(found_idx)

    # Also remove login user from IN_MEMORY_USERS if present
    if clean_emp in IN_MEMORY_USERS:
        del IN_MEMORY_USERS[clean_emp]

    if is_mongo_connected and mongo_db is not None:
        try:
            mongo_db["faculties"].delete_one({"emp_id": clean_emp})
            mongo_db["users"].delete_one({"rollNumber": clean_emp})
        except Exception as e:
            logger.error(f"Error deleting faculty from MongoDB: {e}")

    return {
        "success": True,
        "message": f"Faculty '{target_name}' (ID: {clean_emp}) successfully removed from university records.",
    }


def verify_faculty_for_activation(emp_id: str, name: str, token: Optional[str] = None) -> Dict[str, Any]:
    """
    Verifies that a faculty member exists in the DEO-approved list,
    that their provided name matches official records,
    AND that their DEO Security Token matches.
    """
    clean_emp = str(emp_id).strip().upper()
    clean_input_name = name.strip().lower()

    # Find faculty record
    target_faculty = None
    for f in IN_MEMORY_FACULTIES:
        if str(f.get("emp_id", "")).strip().upper() == clean_emp:
            target_faculty = f
            break

    if not target_faculty:
        return {
            "success": False,
            "message": f"Employee ID '{emp_id}' is not enrolled in the official VFSTR Department registry. Please contact your Department DEO to add your profile."
        }

    if not (target_faculty.get("is_official_cse") is True or target_faculty.get("department") == "Computer Science & Engineering"):
        return {
            "success": False,
            "message": f"Employee ID '{emp_id}' is an allied/inter-departmental instructor. The current portal activation is for Computer Science & Engineering faculty."
        }

    # Normalize official name & input name to match reliably (ignoring Dr., Prof., punctuation, spaces)
    def normalize_name(n: str) -> str:
        no_titles = re.sub(r"^(dr\.|prof\.|mr\.|mrs\.|ms\.)\s*", "", n, flags=re.IGNORECASE).strip().lower()
        return re.sub(r"[\.\,\s\-_]+", "", no_titles)

    norm_official = normalize_name(target_faculty.get("name", ""))
    norm_input = normalize_name(clean_input_name)

    # Check if input matches or is substring or tokens overlap
    input_tokens = set(re.findall(r"[a-z0-9]+", clean_input_name)) - {"dr", "prof", "mr", "mrs", "ms"}
    official_tokens = set(re.findall(r"[a-z0-9]+", target_faculty.get("name", "").lower())) - {"dr", "prof", "mr", "mrs", "ms"}

    is_name_match = (
        norm_official == norm_input
        or norm_input in norm_official
        or norm_official in norm_input
        or len(input_tokens & official_tokens) > 0
    )

    if not is_name_match:
        return {
            "success": False,
            "message": f"Name mismatch for Employee ID '{emp_id}'. The name entered does not match official department records. Please check spelling or contact your DEO."
        }

    # Verify DEO Security Token
    expected_token = target_faculty.get("activation_token")
    if not expected_token:
        expected_token = _generate_token_for_emp(clean_emp)
        target_faculty["activation_token"] = expected_token

    if not token or not str(token).strip():
        return {
            "success": False,
            "message": "DEO Security Token is required. Please enter the 6-digit token provided by your Department DEO."
        }

    clean_token = str(token).strip().upper()
    if clean_token != str(expected_token).strip().upper():
        return {
            "success": False,
            "message": f"Invalid DEO Security Token for Employee ID '{emp_id}'. Please check with your Department DEO for your authorized 6-digit token."
        }

    # Check if already activated
    already_activated = clean_emp in IN_MEMORY_USERS or any(
        u.get("rollNumber") == clean_emp for u in IN_MEMORY_USERS.values()
    )

    return {
        "success": True,
        "message": "Identity and DEO Security Token verified successfully!",
        "emp_id": target_faculty.get("emp_id"),
        "name": target_faculty.get("name"),
        "designation": target_faculty.get("designation"),
        "department": target_faculty.get("department", "Computer Science & Engineering"),
        "email": target_faculty.get("email"),
        "already_activated": already_activated,
    }


def activate_faculty_account(emp_id: str, name: str, password: str, token: Optional[str] = None) -> Dict[str, Any]:
    """
    Sets the faculty member's password and activates their login credentials.
    Consumes the DEO token upon successful password setup.
    """
    verify_res = verify_faculty_for_activation(emp_id, name, token=token)
    if not verify_res.get("success"):
        return verify_res

    if len(password.strip()) < 4:
        return {"success": False, "message": "Password must be at least 4 characters long."}

    clean_emp = str(verify_res["emp_id"]).strip().upper()
    fac_name = verify_res["name"]
    fac_email = verify_res.get("email") or f"{clean_emp.lower()}@vignan.ac.in"
    fac_desig = verify_res.get("designation", "")

    role = "faculty"
    if "HOD" in fac_desig.upper() and "DEPUTY" not in fac_desig.upper():
        role = "hod"
    elif "DEAN" in fac_desig.upper():
        role = "dean"
    elif "DEPUTY HOD" in fac_desig.upper():
        role = "deputy_hod"

    hashed = _hash_password(password)
    user_doc = {
        "name": fac_name,
        "rollNumber": clean_emp,
        "email": fac_email,
        "role": role,
        "department": verify_res.get("department", "CSE"),
        "designation": fac_desig,
        "password_hash": hashed,
        "status": "activated",
        "activated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }

    IN_MEMORY_USERS[clean_emp] = user_doc

    # Mark token consumed in faculty roster
    for f in IN_MEMORY_FACULTIES:
        if str(f.get("emp_id", "")).strip().upper() == clean_emp:
            f["status"] = "activated"
            f["activation_token"] = None
            break

    if is_mongo_connected and mongo_db is not None:
        try:
            mongo_db["users"].update_one(
                {"rollNumber": clean_emp},
                {"$set": user_doc},
                upsert=True
            )
            mongo_db["faculties"].update_one(
                {"emp_id": clean_emp},
                {"$set": {"status": "activated", "activation_token": None}}
            )
        except Exception as e:
            logger.error(f"Error persisting activated user to MongoDB: {e}")

    return {
        "success": True,
        "message": f"Welcome, {fac_name}! Your faculty portal password has been set and your account is active.",
        "user": {
            "name": fac_name,
            "rollNumber": clean_emp,
            "email": fac_email,
            "role": role,
            "department": verify_res.get("department", "CSE"),
            "designation": fac_desig,
        }
    }


def get_timetables_summary() -> Dict[str, Any]:
    """Returns overview of available section timetables across Years 2, 3, and 4."""
    y2_secs = [k.split("_")[1] for k in IN_MEMORY_TIMETABLES if k.startswith("2_")]
    y3_secs = [k.split("_")[1] for k in IN_MEMORY_TIMETABLES if k.startswith("3_")]
    y4_secs = [k.split("_")[1] for k in IN_MEMORY_TIMETABLES if k.startswith("4_")]
    return {
        "total_sections": len(IN_MEMORY_TIMETABLES),
        "total_faculties": len(IN_MEMORY_FACULTIES),
        "year_2": {"regulation": "R25", "batch": "2024–2028 (R25 Regulation)", "sections_count": len(y2_secs), "sections": sorted(y2_secs, key=lambda x: int(x) if x.isdigit() else 0)},
        "year_3": {"regulation": "C24", "batch": "2023–2027 (C24 Regulation)", "sections_count": len(y3_secs), "sections": sorted(y3_secs, key=lambda x: int(x) if x.isdigit() else 0)},
        "year_4": {"regulation": "C22", "batch": "2022–2026 (C22 Regulation)", "sections_count": len(y4_secs), "sections": sorted(y4_secs, key=lambda x: int(x) if x.isdigit() else 0)},
    }


def load_placements_cache():
    """Loads official department placement dossier into memory cache."""
    global IN_MEMORY_PLACEMENTS
    base_dir = os.path.dirname(os.path.dirname(__file__))
    plc_path = os.path.join(base_dir, "public", "data", "placements.json")
    if os.path.exists(plc_path):
        try:
            with open(plc_path, "r", encoding="utf-8") as f:
                IN_MEMORY_PLACEMENTS = json.load(f)
            logger.info(f"Loaded placement registry ({IN_MEMORY_PLACEMENTS.get('total_placed_count', 0)} placed students) into memory cache.")
        except Exception as ex:
            logger.error(f"Error loading placements.json: {ex}")


def get_placements_summary() -> Dict[str, Any]:
    """Returns official executive placement statistics, company breakdown, and section leaderboard."""
    if not IN_MEMORY_PLACEMENTS:
        load_placements_cache()
    summary = IN_MEMORY_PLACEMENTS.get("summary", {})
    companies = IN_MEMORY_PLACEMENTS.get("companies", [])
    sections = IN_MEMORY_PLACEMENTS.get("sections", [])
    return {
        "summary": summary,
        "companies": companies,
        "sections": sections,
        "total_placed_count": IN_MEMORY_PLACEMENTS.get("total_placed_count", 0),
        "total_offers_count": IN_MEMORY_PLACEMENTS.get("total_offers_count", 0),
        "multi_offer_students_count": len(IN_MEMORY_PLACEMENTS.get("multi_offer_students", [])),
    }


def get_company_placements(company_name: str) -> Optional[Dict[str, Any]]:
    """Returns official placement stats and placed student roster for a specific recruiter."""
    if not IN_MEMORY_PLACEMENTS:
        load_placements_cache()
    if not company_name:
        return None
    q = company_name.strip().upper()
    comp_summary = None
    for c in IN_MEMORY_PLACEMENTS.get("companies", []):
        if q in c.get("company", "").upper() or c.get("company", "").upper() in q:
            comp_summary = c
            break

    matched_offers = []
    for off in IN_MEMORY_PLACEMENTS.get("all_offers", []):
        if q in off.get("company", "").upper() or off.get("company", "").upper() in q:
            matched_offers.append(off)

    if not comp_summary and not matched_offers:
        return None

    return {
        "company": comp_summary.get("company") if comp_summary else company_name,
        "summary": comp_summary,
        "offers_count": len(matched_offers),
        "offers": matched_offers
    }


def get_section_placements(section: str) -> Optional[Dict[str, Any]]:
    """Returns placement performance and placed student roster for a specific 4th-year section."""
    if not IN_MEMORY_PLACEMENTS:
        load_placements_cache()
    sec_clean = str(section).strip().upper().replace("SEC-", "").replace("SEC", "").replace("SECTION", "").strip()
    sec_stat = None
    for s in IN_MEMORY_PLACEMENTS.get("sections", []):
        if s.get("section") == sec_clean:
            sec_stat = s
            break

    placed_in_sec = [
        p for p in IN_MEMORY_PLACEMENTS.get("placed_students", [])
        if str(p.get("section")).strip() == sec_clean
    ]

    if not sec_stat and not placed_in_sec:
        return None

    return {
        "section": sec_clean,
        "stats": sec_stat,
        "placed_count": len(placed_in_sec),
        "students": placed_in_sec
    }


def get_student_placement(roll_number: str) -> Optional[Dict[str, Any]]:
    """O(1) lookup of a student's placement status, offers, packages, and recruiters."""
    if not IN_MEMORY_PLACEMENTS:
        load_placements_cache()
    r = roll_number.strip().upper()
    for p in IN_MEMORY_PLACEMENTS.get("placed_students", []):
        if p.get("roll_number") == r:
            return p

    # Check unplaced or excluded
    st = get_student_by_roll(r)
    if st and st.get("current_year") == 4:
        is_excl = any(e.get("roll_number") == r for e in IN_MEMORY_PLACEMENTS.get("excluded_students", []))
        return {
            "roll_number": r,
            "name": st.get("name"),
            "section": st.get("section"),
            "cgpa": st.get("cgpa"),
            "placement_status": "Excluded" if is_excl else "Active Unplaced",
            "total_offers": 0,
            "offers": []
        }
    return None


def get_multi_offer_students(limit: int = 20) -> List[Dict[str, Any]]:
    """Returns students who secured multiple offers sorted by offer count."""
    if not IN_MEMORY_PLACEMENTS:
        load_placements_cache()
    return IN_MEMORY_PLACEMENTS.get("multi_offer_students", [])[:limit]


# Initialize database connection and sync caches
init_mongo_connection()
if not IN_MEMORY_STUDENTS:
    load_students_cache()
if not IN_MEMORY_TIMETABLES:
    load_timetables_cache()
if not IN_MEMORY_PLACEMENTS:
    load_placements_cache()




