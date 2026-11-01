# =========================================================
# AI-BASED SKILL GAP ANALYZER - BACKEND
# =========================================================

from flask import Flask, request
from flask_cors import CORS

from db import get_db_connection
from skill_extractor import extract_skills
from ai_recommender import generate_recommendation

from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

from functools import wraps
from dotenv import load_dotenv

import jwt
import os

from datetime import datetime, timedelta, timezone

from pypdf import PdfReader
from docx import Document


# =========================================================
# LOAD ENVIRONMENT VARIABLES
# =========================================================

load_dotenv()

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")

if not JWT_SECRET_KEY:
    raise ValueError("JWT_SECRET_KEY is not set in .env file")


# =========================================================
# FLASK APP
# =========================================================

app = Flask(__name__)

CORS(app)


# =========================================================
# FILE UPLOAD SECURITY
# =========================================================

# Maximum request size = 5 MB
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024

ALLOWED_EXTENSIONS = {"pdf", "docx"}


def allowed_file(filename):

    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower()
        in ALLOWED_EXTENSIONS
    )


# =========================================================
# HANDLE FILE TOO LARGE
# =========================================================

@app.errorhandler(413)
def file_too_large(error):

    return {
        "success": False,
        "message": "File size must be less than or equal to 5 MB"
    }, 413


# =========================================================
# JWT TOKEN DECORATOR
# =========================================================

def token_required(f):

    @wraps(f)
    def decorated(*args, **kwargs):

        token = None

        # Get Authorization header
        auth_header = request.headers.get("Authorization")

        if auth_header:

            parts = auth_header.split()

            if len(parts) == 2 and parts[0].lower() == "bearer":

                token = parts[1]

        # Token missing
        if not token:

            return {
                "success": False,
                "message": "Authorization token is required"
            }, 401

        try:

            # Decode JWT token
            decoded_token = jwt.decode(
                token,
                JWT_SECRET_KEY,
                algorithms=["HS256"]
            )

            current_user_id = decoded_token.get("user_id")

            if not current_user_id:

                return {
                    "success": False,
                    "message": "Invalid token"
                }, 401

        except jwt.ExpiredSignatureError:

            return {
                "success": False,
                "message": "Token has expired"
            }, 401

        except jwt.InvalidTokenError:

            return {
                "success": False,
                "message": "Invalid token"
            }, 401

        return f(current_user_id, *args, **kwargs)

    return decorated


# =========================================================
# HOME API
# =========================================================

@app.route("/")
def home():

    return {
        "message": "AI Skill Gap Analyzer Backend is Running",
        "success": True
    }


# =========================================================
# TEST API
# =========================================================

@app.route("/api/test")
def test():

    return {
        "message": "Backend API is working successfully",
        "success": True
    }


# =========================================================
# DATABASE TEST API
# =========================================================

@app.route("/api/db-test")
def db_test():

    try:

        connection = get_db_connection()

        cursor = connection.cursor()

        cursor.execute("SELECT 1")

        result = cursor.fetchone()

        cursor.close()
        connection.close()

        return {
            "success": True,
            "message": "Database connected successfully",
            "result": result[0]
        }

    except Exception as e:

        return {
            "success": False,
            "message": str(e)
        }, 500


# =========================================================
# REGISTER API
# =========================================================

@app.route("/api/register", methods=["POST"])
def register():

    connection = None
    cursor = None

    try:

        data = request.get_json()

        if not data:

            return {
                "success": False,
                "message": "Request body is required"
            }, 400

        name = data.get("name")
        email = data.get("email")
        password = data.get("password")
        education = data.get("education")
        branch = data.get("branch")
        target_role = data.get("target_role")

        if not name or not email or not password:

            return {
                "success": False,
                "message": "Name, email and password are required"
            }, 400

        # =================================================
        # HASH PASSWORD
        # =================================================

        hashed_password = generate_password_hash(password)

        connection = get_db_connection()

        cursor = connection.cursor()

        query = """
            INSERT INTO users
            (name, email, password, education, branch, target_role)
            VALUES (%s, %s, %s, %s, %s, %s)
        """

        values = (
            name,
            email,
            hashed_password,
            education,
            branch,
            target_role
        )

        cursor.execute(query, values)

        connection.commit()

        user_id = cursor.lastrowid

        return {
            "success": True,
            "message": "User registered successfully",
            "user_id": user_id
        }, 201

    except Exception as e:

        if connection:
            connection.rollback()

        return {
            "success": False,
            "message": str(e)
        }, 500

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


# =========================================================
# LOGIN API
# =========================================================

@app.route("/api/login", methods=["POST"])
def login():

    connection = None
    cursor = None

    try:

        data = request.get_json()

        if not data:

            return {
                "success": False,
                "message": "Request body is required"
            }, 400

        email = data.get("email")
        password = data.get("password")

        if not email or not password:

            return {
                "success": False,
                "message": "Email and password are required"
            }, 400

        connection = get_db_connection()

        cursor = connection.cursor(dictionary=True)

        query = """
            SELECT *
            FROM users
            WHERE email = %s
        """

        cursor.execute(
            query,
            (email,)
        )

        user = cursor.fetchone()

        if not user:

            return {
                "success": False,
                "message": "Invalid email or password"
            }, 401

        # =================================================
        # CHECK HASHED PASSWORD
        # =================================================

        password_correct = check_password_hash(
            user["password"],
            password
        )

        if not password_correct:

            return {
                "success": False,
                "message": "Invalid email or password"
            }, 401

        # =================================================
        # GENERATE JWT TOKEN
        # =================================================

        token_payload = {

            "user_id": user["id"],

            "exp":
                datetime.now(timezone.utc)
                + timedelta(hours=24)

        }

        access_token = jwt.encode(
            token_payload,
            JWT_SECRET_KEY,
            algorithm="HS256"
        )

        # =================================================
        # REMOVE PASSWORD
        # =================================================

        user.pop("password", None)

        return {

            "success": True,

            "message": "Login successful",

            "access_token":
                access_token,

            "token_type":
                "Bearer",

            "expires_in":
                "24 hours",

            "user":
                user

        }, 200

    except Exception as e:

        return {

            "success": False,

            "message":
                str(e)

        }, 500

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


# =========================================================
# GET USER PROFILE
# =========================================================

@app.route("/api/profile/<int:user_id>", methods=["GET"])
@token_required
def get_profile(current_user_id, user_id):

    connection = None
    cursor = None

    try:

        # User can access only their own profile

        if current_user_id != user_id:

            return {
                "success": False,
                "message":
                    "You are not authorized to access this profile"
            }, 403

        connection = get_db_connection()

        cursor = connection.cursor(dictionary=True)

        query = """
            SELECT
                id,
                name,
                email,
                education,
                branch,
                target_role,
                created_at
            FROM users
            WHERE id = %s
        """

        cursor.execute(
            query,
            (user_id,)
        )

        user = cursor.fetchone()

        if not user:

            return {
                "success": False,
                "message": "User not found"
            }, 404

        return {
            "success": True,
            "user": user
        }, 200

    except Exception as e:

        return {
            "success": False,
            "message": str(e)
        }, 500

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


# =========================================================
# GET ALL SKILLS
# =========================================================

@app.route("/api/skills", methods=["GET"])
def get_skills():

    connection = None
    cursor = None

    try:

        connection = get_db_connection()

        cursor = connection.cursor(dictionary=True)

        query = """
            SELECT
                id,
                skill_name
            FROM skills
            ORDER BY id
        """

        cursor.execute(query)

        skills = cursor.fetchall()

        return {
            "success": True,
            "total_skills": len(skills),
            "skills": skills
        }, 200

    except Exception as e:

        return {
            "success": False,
            "message": str(e)
        }, 500

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


# =========================================================
# ADD USER SKILLS
# =========================================================

@app.route("/api/user-skills", methods=["POST"])
@token_required
def add_user_skills(current_user_id):

    connection = None
    cursor = None

    try:

        data = request.get_json()

        if not data:

            return {
                "success": False,
                "message": "Request body is required"
            }, 400

        user_id = data.get("user_id")
        skill_ids = data.get("skill_ids")

        if not user_id or not skill_ids:

            return {
                "success": False,
                "message":
                    "user_id and skill_ids are required"
            }, 400

        if not isinstance(skill_ids, list):

            return {
                "success": False,
                "message": "skill_ids must be a list"
            }, 400

        if current_user_id != user_id:

            return {
                "success": False,
                "message":
                    "You are not authorized to modify these skills"
            }, 403

        connection = get_db_connection()

        cursor = connection.cursor()

        query = """
            INSERT IGNORE INTO user_skills
            (user_id, skill_id)
            VALUES (%s, %s)
        """

        for skill_id in skill_ids:

            cursor.execute(
                query,
                (user_id, skill_id)
            )

        connection.commit()

        return {

            "success": True,

            "message":
                "User skills saved successfully",

            "user_id":
                user_id,

            "skill_ids":
                skill_ids

        }, 200

    except Exception as e:

        if connection:
            connection.rollback()

        return {

            "success": False,

            "message":
                str(e)

        }, 500

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


# =========================================================
# GET USER SKILLS
# =========================================================

@app.route("/api/user-skills/<int:user_id>", methods=["GET"])
@token_required
def get_user_skills(current_user_id, user_id):

    connection = None
    cursor = None

    try:

        if current_user_id != user_id:

            return {
                "success": False,
                "message":
                    "You are not authorized to access these skills"
            }, 403

        connection = get_db_connection()

        cursor = connection.cursor(dictionary=True)

        query = """
            SELECT
                s.id,
                s.skill_name
            FROM user_skills us
            JOIN skills s
                ON us.skill_id = s.id
            WHERE us.user_id = %s
            ORDER BY s.id
        """

        cursor.execute(
            query,
            (user_id,)
        )

        skills = cursor.fetchall()

        return {

            "success": True,

            "user_id":
                user_id,

            "total_skills":
                len(skills),

            "skills":
                skills

        }, 200

    except Exception as e:

        return {

            "success": False,

            "message":
                str(e)

        }, 500

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


# =========================================================
# GET ALL JOB ROLES
# =========================================================

@app.route("/api/job-roles", methods=["GET"])
def get_job_roles():

    connection = None
    cursor = None

    try:

        connection = get_db_connection()

        cursor = connection.cursor(dictionary=True)

        query = """
            SELECT
                id,
                role_name,
                description
            FROM job_roles
            ORDER BY id
        """

        cursor.execute(query)

        roles = cursor.fetchall()

        return {

            "success": True,

            "total_roles":
                len(roles),

            "job_roles":
                roles

        }, 200

    except Exception as e:

        return {

            "success": False,

            "message":
                str(e)

        }, 500

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


# =========================================================
# GET REQUIRED SKILLS FOR ROLE
# =========================================================

@app.route("/api/role-skills/<int:role_id>", methods=["GET"])
def get_role_skills(role_id):

    connection = None
    cursor = None

    try:

        connection = get_db_connection()

        cursor = connection.cursor(dictionary=True)

        query = """
            SELECT
                s.id,
                s.skill_name
            FROM role_skills rs
            JOIN skills s
                ON rs.skill_id = s.id
            WHERE rs.role_id = %s
            ORDER BY s.id
        """

        cursor.execute(
            query,
            (role_id,)
        )

        skills = cursor.fetchall()

        return {

            "success": True,

            "role_id":
                role_id,

            "total_required_skills":
                len(skills),

            "required_skills":
                skills

        }, 200

    except Exception as e:

        return {

            "success": False,

            "message":
                str(e)

        }, 500

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


# =========================================================
# SKILL GAP API
# =========================================================

@app.route("/api/skill-gap", methods=["GET"])
@token_required
def skill_gap(current_user_id):

    connection = None
    cursor = None

    try:

        user_id = request.args.get(
            "user_id",
            type=int
        )

        role_id = request.args.get(
            "role_id",
            type=int
        )

        if not user_id or not role_id:

            return {

                "success": False,

                "message":
                    "user_id and role_id are required"

            }, 400

        if current_user_id != user_id:

            return {

                "success": False,

                "message":
                    "You are not authorized to access this skill gap"

            }, 403

        connection = get_db_connection()

        cursor = connection.cursor(dictionary=True)

        # =================================================
        # GET USER SKILLS
        # =================================================

        user_skill_query = """

            SELECT
                s.id,
                s.skill_name

            FROM user_skills us

            JOIN skills s
                ON us.skill_id = s.id

            WHERE us.user_id = %s

        """

        cursor.execute(
            user_skill_query,
            (user_id,)
        )

        user_skills = cursor.fetchall()

        # =================================================
        # GET REQUIRED ROLE SKILLS
        # =================================================

        role_skill_query = """

            SELECT
                s.id,
                s.skill_name

            FROM role_skills rs

            JOIN skills s
                ON rs.skill_id = s.id

            WHERE rs.role_id = %s

        """

        cursor.execute(
            role_skill_query,
            (role_id,)
        )

        required_skills = cursor.fetchall()

        if not required_skills:

            return {

                "success": False,

                "message":
                    "No required skills found for this role"

            }, 404

        # =================================================
        # COMPARE SKILLS
        # =================================================

        user_skill_names = {

            skill["skill_name"].lower()

            for skill in user_skills

        }

        matched_skills = [

            skill["skill_name"]

            for skill in required_skills

            if skill["skill_name"].lower()
            in user_skill_names

        ]

        missing_skills = [

            skill["skill_name"]

            for skill in required_skills

            if skill["skill_name"].lower()
            not in user_skill_names

        ]

        total_required = len(required_skills)

        total_matched = len(matched_skills)

        match_percentage = round(
            (total_matched / total_required) * 100,
            2
        )

        return {

            "success":
                True,

            "user_id":
                user_id,

            "role_id":
                role_id,

            "total_required_skills":
                total_required,

            "total_matched_skills":
                total_matched,

            "match_percentage":
                match_percentage,

            "matched_skills":
                matched_skills,

            "missing_skills":
                missing_skills

        }, 200

    except Exception as e:

        return {

            "success":
                False,

            "message":
                str(e)

        }, 500

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


# =========================================================
# RESUME UPLOAD API
# =========================================================

@app.route("/api/upload-resume", methods=["POST"])
@token_required
def upload_resume(current_user_id):

    saved_filepath = None
    connection = None
    cursor = None

    try:

        # =================================================
        # GET USER ID
        # =================================================

        user_id = request.form.get(
            "user_id",
            type=int
        )

        if not user_id:

            return {

                "success":
                    False,

                "message":
                    "user_id is required"

            }, 400

        # =================================================
        # AUTHORIZATION CHECK
        # =================================================

        if current_user_id != user_id:

            return {

                "success":
                    False,

                "message":
                    "You are not authorized to upload resume for this user"

            }, 403

        # =================================================
        # CHECK FILE
        # =================================================

        if "resume" not in request.files:

            return {

                "success":
                    False,

                "message":
                    "Resume file is required"

            }, 400

        resume = request.files["resume"]

        if resume.filename == "":

            return {

                "success":
                    False,

                "message":
                    "No resume file selected"

            }, 400

        # =================================================
        # ORIGINAL FILENAME
        # =================================================

        original_filename = resume.filename

        # =================================================
        # CHECK EXTENSION
        # =================================================

        if not allowed_file(original_filename):

            return {

                "success":
                    False,

                "message":
                    "Only PDF and DOCX files are allowed"

            }, 400

        # =================================================
        # SECURE FILENAME
        # =================================================

        safe_filename = secure_filename(
            original_filename
        )

        if not safe_filename:

            return {

                "success":
                    False,

                "message":
                    "Invalid filename"

            }, 400

        # =================================================
        # CHECK FILE SIZE
        # =================================================

        resume.stream.seek(
            0,
            os.SEEK_END
        )

        file_size = resume.stream.tell()

        resume.stream.seek(0)

        MAX_FILE_SIZE = 5 * 1024 * 1024

        if file_size > MAX_FILE_SIZE:

            return {

                "success":
                    False,

                "message":
                    "File size must be less than or equal to 5 MB"

            }, 400

        # =================================================
        # CREATE UPLOAD FOLDER
        # =================================================

        upload_folder = os.path.join(
            os.path.dirname(
                os.path.abspath(__file__)
            ),
            "uploads"
        )

        os.makedirs(
            upload_folder,
            exist_ok=True
        )

        # =================================================
        # CREATE UNIQUE FILENAME
        # =================================================

        timestamp = datetime.now().strftime(
            "%Y%m%d_%H%M%S_%f"
        )

        file_extension = safe_filename.rsplit(
            ".",
            1
        )[1].lower()

        saved_filename = (
            f"user_{user_id}_"
            f"{timestamp}."
            f"{file_extension}"
        )

        saved_filepath = os.path.join(
            upload_folder,
            saved_filename
        )

        # =================================================
        # SAVE FILE
        # =================================================

        resume.save(saved_filepath)

        # =================================================
        # EXTRACT TEXT
        # =================================================

        extracted_text = ""

        if file_extension == "pdf":

            reader = PdfReader(
                saved_filepath
            )

            for page in reader.pages:

                page_text = page.extract_text()

                if page_text:

                    extracted_text += (
                        page_text + "\n"
                    )

        elif file_extension == "docx":

            document = Document(
                saved_filepath
            )

            for paragraph in document.paragraphs:

                if paragraph.text:

                    extracted_text += (
                        paragraph.text + "\n"
                    )

        # =================================================
        # CHECK EXTRACTED TEXT
        # =================================================

        if not extracted_text.strip():

            return {

                "success":
                    False,

                "message":
                    "Could not extract text from resume"

            }, 400

        # =================================================
        # EXTRACT SKILLS
        # =================================================

        detected_skills = extract_skills(
            extracted_text
        )

        # =================================================
        # SAVE SKILLS INTO DATABASE
        # =================================================

        connection = get_db_connection()

        cursor = connection.cursor()

        saved_skills = []

        not_found_skills = []

        for skill_name in detected_skills:

            cursor.execute(
                """
                SELECT id
                FROM skills
                WHERE skill_name = %s
                """,
                (skill_name,)
            )

            skill = cursor.fetchone()

            if skill:

                skill_id = skill[0]

                cursor.execute(
                    """
                    INSERT IGNORE INTO user_skills
                    (user_id, skill_id)
                    VALUES (%s, %s)
                    """,
                    (
                        user_id,
                        skill_id
                    )
                )

                saved_skills.append(
                    skill_name
                )

            else:

                not_found_skills.append(
                    skill_name
                )

        connection.commit()

        return {

            "success":
                True,

            "message":
                "Resume uploaded, skills detected and saved successfully",

            "user_id":
                user_id,

            "filename":
                original_filename,

            "saved_filename":
                saved_filename,

            "total_detected_skills":
                len(detected_skills),

            "total_saved_skills":
                len(saved_skills),

            "detected_skills":
                detected_skills,

            "saved_skills":
                saved_skills,

            "not_found_skills":
                not_found_skills

        }, 200

    except Exception as e:

        if connection:

            connection.rollback()

        # =================================================
        # DELETE FILE IF ERROR OCCURS
        # =================================================

        if saved_filepath and os.path.exists(
            saved_filepath
        ):

            try:

                os.remove(
                    saved_filepath
                )

            except Exception:

                pass

        return {

            "success":
                False,

            "message":
                str(e)

        }, 500

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


# =========================================================
# PERSONALIZED ROADMAP API
# =========================================================

@app.route("/api/personalized-roadmap", methods=["GET"])
@token_required
def personalized_roadmap(current_user_id):

    connection = None
    cursor = None

    try:

        user_id = request.args.get(
            "user_id",
            type=int
        )

        role_id = request.args.get(
            "role_id",
            type=int
        )

        if not user_id or not role_id:

            return {

                "success":
                    False,

                "message":
                    "user_id and role_id are required"

            }, 400

        if current_user_id != user_id:

            return {

                "success":
                    False,

                "message":
                    "You are not authorized to access this roadmap"

            }, 403

        connection = get_db_connection()

        cursor = connection.cursor(
            dictionary=True
        )

        # =================================================
        # GET ROLE
        # =================================================

        cursor.execute(
            """
            SELECT
                id,
                role_name,
                description
            FROM job_roles
            WHERE id = %s
            """,
            (role_id,)
        )

        role = cursor.fetchone()

        if not role:

            return {

                "success":
                    False,

                "message":
                    "Job role not found"

            }, 404

        # =================================================
        # GET USER SKILLS
        # =================================================

        cursor.execute(
            """
            SELECT
                s.skill_name
            FROM user_skills us
            JOIN skills s
                ON us.skill_id = s.id
            WHERE us.user_id = %s
            """,
            (user_id,)
        )

        user_skills = cursor.fetchall()

        user_skill_names = {
            skill["skill_name"].lower()
            for skill in user_skills
        }

        # =================================================
        # GET REQUIRED ROLE SKILLS
        # =================================================

        cursor.execute(
            """
            SELECT
                s.id,
                s.skill_name
            FROM role_skills rs
            JOIN skills s
                ON rs.skill_id = s.id
            WHERE rs.role_id = %s
            ORDER BY s.id
            """,
            (role_id,)
        )

        required_skills = cursor.fetchall()

        if not required_skills:

            return {

                "success":
                    False,

                "message":
                    "No required skills found for this role"

            }, 404

        # =================================================
        # MATCHED / MISSING
        # =================================================

        matched_skills = [

            skill["skill_name"]

            for skill in required_skills

            if skill["skill_name"].lower()
            in user_skill_names

        ]

        missing_skills = [

            skill["skill_name"]

            for skill in required_skills

            if skill["skill_name"].lower()
            not in user_skill_names

        ]

        total_required = len(
            required_skills
        )

        total_matched = len(
            matched_skills
        )

        match_percentage = round(
            (
                total_matched
                / total_required
            ) * 100,
            2
        )

        # =================================================
        # GET LEARNING RESOURCES
        # =================================================

        roadmap = []

        for skill_name in missing_skills:

            cursor.execute(
                """
                SELECT
                    s.id AS skill_id,
                    s.skill_name,
                    lr.learning_topics,
                    lr.resources,
                    lr.project_ideas,
                    lr.difficulty
                FROM skills s
                LEFT JOIN learning_resources lr
                    ON s.id = lr.skill_id
                WHERE s.skill_name = %s
                """,
                (skill_name,)
            )

            resource = cursor.fetchone()

            if resource:

                roadmap.append({
                    "skill_id":
                        resource["skill_id"],

                    "skill_name":
                        resource["skill_name"],

                    "learning_topics":
                        resource["learning_topics"],

                    "resources":
                        resource["resources"],

                    "project_ideas":
                        resource["project_ideas"],

                    "difficulty":
                        resource["difficulty"]
                })

            else:

                roadmap.append({

                    "skill_name":
                        skill_name,

                    "learning_topics":
                        "Learning resources will be added soon.",

                    "resources":
                        "No resource available yet.",

                    "project_ideas":
                        "Build a small practical project using this skill.",

                    "difficulty":
                        "Not specified"
                })

        return {

            "success":
                True,

            "user_id":
                user_id,

            "role_id":
                role_id,

            "target_role":
                role["role_name"],

            "match_percentage":
                match_percentage,

            "matched_skills":
                matched_skills,

            "missing_skills":
                missing_skills,

            "personalized_roadmap":
                roadmap

        }, 200

    except Exception as e:

        return {

            "success":
                False,

            "message":
                str(e)

        }, 500

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


# =========================================================
# LEARNING RESOURCE API
# =========================================================

@app.route(
    "/api/learning-resources/<int:skill_id>",
    methods=["GET"]
)
def get_learning_resource(skill_id):

    connection = None
    cursor = None

    try:

        connection = get_db_connection()

        cursor = connection.cursor(
            dictionary=True
        )

        query = """
            SELECT
                s.id AS skill_id,
                s.skill_name,
                lr.learning_topics,
                lr.resources,
                lr.project_ideas,
                lr.difficulty
            FROM skills s
            LEFT JOIN learning_resources lr
                ON s.id = lr.skill_id
            WHERE s.id = %s
        """

        cursor.execute(
            query,
            (skill_id,)
        )

        resource = cursor.fetchone()

        if not resource:

            return {

                "success":
                    False,

                "message":
                    "Skill not found"

            }, 404

        if not resource["learning_topics"]:

            return {

                "success":
                    False,

                "message":
                    "Learning resource not found for this skill"

            }, 404

        return {

            "success":
                True,

            "learning_resource":
                resource

        }, 200

    except Exception as e:

        return {

            "success":
                False,

            "message":
                str(e)

        }, 500

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()

# =========================================================
# PROGRESS TRACKING API - GET USER PROGRESS
# =========================================================

@app.route("/api/progress", methods=["GET"])
@token_required
def get_progress(current_user_id):

    connection = None
    cursor = None

    try:

        user_id = request.args.get("user_id", type=int)
        role_id = request.args.get("role_id", type=int)

        if not user_id or not role_id:
            return {
                "success": False,
                "message": "user_id and role_id are required"
            }, 400

        if current_user_id != user_id:
            return {
                "success": False,
                "message": "You are not authorized to access this progress"
            }, 403

        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT
                s.id AS skill_id,
                s.skill_name,
                COALESCE(pt.is_completed, 0) AS is_completed,
                pt.completed_at
            FROM role_skills rs
            JOIN skills s
                ON rs.skill_id = s.id
            LEFT JOIN progress_tracking pt
                ON pt.skill_id = s.id
                AND pt.user_id = %s
                AND pt.role_id = %s
            WHERE rs.role_id = %s
            ORDER BY s.id
            """,
            (user_id, role_id, role_id)
        )

        skills = cursor.fetchall()

        total_skills = len(skills)

        completed_skills = sum(
            1 for skill in skills
            if skill["is_completed"]
        )

        pending_skills = total_skills - completed_skills

        progress_percentage = (
            round((completed_skills / total_skills) * 100, 2)
            if total_skills else 0
        )

        return {
            "success": True,
            "user_id": user_id,
            "role_id": role_id,
            "total_skills": total_skills,
            "completed_skills": completed_skills,
            "pending_skills": pending_skills,
            "progress_percentage": progress_percentage,
            "skills": skills
        }, 200

    except Exception as e:

        return {
            "success": False,
            "message": str(e)
        }, 500

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


# =========================================================
# PROGRESS TRACKING API - UPDATE SKILL STATUS
# =========================================================

@app.route("/api/progress", methods=["POST"])
@token_required
def update_progress(current_user_id):

    connection = None
    cursor = None

    try:

        data = request.get_json()

        if not data:
            return {
                "success": False,
                "message": "Request body is required"
            }, 400

        user_id = data.get("user_id")
        role_id = data.get("role_id")
        skill_id = data.get("skill_id")
        is_completed = data.get("is_completed")

        if (
            not user_id
            or not role_id
            or not skill_id
            or not isinstance(is_completed, bool)
        ):
            return {
                "success": False,
                "message": "Valid user_id, role_id, skill_id and is_completed are required"
            }, 400

        if current_user_id != user_id:
            return {
                "success": False,
                "message": "You are not authorized to update this progress"
            }, 403

        connection = get_db_connection()
        cursor = connection.cursor()

        # Check whether skill belongs to the selected role

        cursor.execute(
            """
            SELECT skill_id
            FROM role_skills
            WHERE role_id = %s AND skill_id = %s
            """,
            (role_id, skill_id)
        )

        if not cursor.fetchone():
            return {
                "success": False,
                "message": "Skill does not belong to this job role"
            }, 404

        cursor.execute(
            """
            INSERT INTO progress_tracking
                (user_id, role_id, skill_id, is_completed, completed_at)
            VALUES (%s, %s, %s, %s,
                CASE WHEN %s = 1 THEN CURRENT_TIMESTAMP ELSE NULL END)
            ON DUPLICATE KEY UPDATE
                is_completed = VALUES(is_completed),
                completed_at = CASE
                    WHEN VALUES(is_completed) = 1
                    THEN CURRENT_TIMESTAMP
                    ELSE NULL
                END
            """,
            (
                user_id,
                role_id,
                skill_id,
                is_completed,
                is_completed
            )
        )

        connection.commit()

        return {
            "success": True,
            "message": "Progress updated successfully",
            "skill_id": skill_id,
            "is_completed": is_completed
        }, 200

    except Exception as e:

        if connection:
            connection.rollback()

        return {
            "success": False,
            "message": str(e)
        }, 500

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()
# =========================================================
# AI RECOMMENDATION API
# =========================================================

@app.route(
    "/api/ai-recommendation",
    methods=["GET"]
)
@token_required
def ai_recommendation(current_user_id):

    connection = None
    cursor = None

    try:

        user_id = request.args.get(
            "user_id",
            type=int
        )

        role_id = request.args.get(
            "role_id",
            type=int
        )

        if not user_id or not role_id:

            return {

                "success":
                    False,

                "message":
                    "user_id and role_id are required"

            }, 400

        if current_user_id != user_id:

            return {

                "success":
                    False,

                "message":
                    "You are not authorized to access this AI recommendation"

            }, 403

        connection = get_db_connection()

        cursor = connection.cursor(
            dictionary=True
        )

        # =================================================
        # GET TARGET ROLE
        # =================================================

        cursor.execute(
            """
            SELECT
                id,
                role_name,
                description
            FROM job_roles
            WHERE id = %s
            """,
            (role_id,)
        )

        role = cursor.fetchone()

        if not role:

            return {

                "success":
                    False,

                "message":
                    "Job role not found"

            }, 404

        # =================================================
        # GET USER SKILLS
        # =================================================

        cursor.execute(
            """
            SELECT
                s.skill_name
            FROM user_skills us
            JOIN skills s
                ON us.skill_id = s.id
            WHERE us.user_id = %s
            """,
            (user_id,)
        )

        user_skills = cursor.fetchall()

        user_skill_names = {

            skill["skill_name"].lower()

            for skill in user_skills

        }

        # =================================================
        # GET REQUIRED ROLE SKILLS
        # =================================================

        cursor.execute(
            """
            SELECT
                s.skill_name
            FROM role_skills rs
            JOIN skills s
                ON rs.skill_id = s.id
            WHERE rs.role_id = %s
            ORDER BY s.id
            """,
            (role_id,)
        )

        required_skills = cursor.fetchall()

        if not required_skills:

            return {

                "success":
                    False,

                "message":
                    "No required skills found for this role"

            }, 404

        # =================================================
        # MATCHED SKILLS
        # =================================================

        matched_skills = [

            skill["skill_name"]

            for skill in required_skills

            if skill["skill_name"].lower()
            in user_skill_names

        ]

        # =================================================
        # MISSING SKILLS
        # =================================================

        missing_skills = [

            skill["skill_name"]

            for skill in required_skills

            if skill["skill_name"].lower()
            not in user_skill_names

        ]

        # =================================================
        # MATCH PERCENTAGE
        # =================================================

        total_required = len(
            required_skills
        )

        total_matched = len(
            matched_skills
        )

        match_percentage = round(
            (
                total_matched
                / total_required
            ) * 100,
            2
        )

        # =================================================
        # GENERATE AI RECOMMENDATION
        # =================================================

        recommendation = generate_recommendation(

            role["role_name"],

            matched_skills,

            missing_skills

        )

        return {

            "success":
                True,

            "user_id":
                user_id,

            "role_id":
                role_id,

            "target_role":
                role["role_name"],

            "total_required_skills":
                total_required,

            "total_matched_skills":
                total_matched,

            "match_percentage":
                match_percentage,

            "matched_skills":
                matched_skills,

            "missing_skills":
                missing_skills,

            "ai_recommendation":
                recommendation

        }, 200

    except Exception as e:

        return {

            "success":
                False,

            "message":
                str(e)

        }, 500

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


# =========================================================
# RUN FLASK SERVER
# =========================================================

if __name__ == "__main__":

    app.run(
        debug=True,
        host="127.0.0.1",
        port=5000
    )
