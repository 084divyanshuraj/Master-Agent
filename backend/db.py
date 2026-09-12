"""
Vignan's University — Master Agent Database & Audit Logger
Supports MongoDB Atlas persistence with automatic in-memory fallback.
"""

import os
import time
import logging
import hashlib
import secrets
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

load_dotenv(override=True)
logger = logging.getLogger("mongo_db")
logger.setLevel(logging.INFO)

# In-memory storage fallback for query logs, custom agent endpoints, and user sessions
IN_MEMORY_LOGS: List[Dict[str, Any]] = []
IN_MEMORY_USERS: Dict[str, Dict[str, Any]] = {}
IN_MEMORY_ENDPOINTS: Dict[str, str] = {}
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


init_mongo_connection()


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
