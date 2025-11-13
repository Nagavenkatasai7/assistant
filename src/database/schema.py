"""
Database schema for storing job descriptions and generated resumes
"""
import sqlite3
import json
from pathlib import Path
from datetime import datetime

class Database:
    def __init__(self, db_path="resume_generator.db"):
        self.db_path = db_path
        self.init_database()
        self._migrate_scoring_fields()

    def get_connection(self):
        """Get database connection"""
        return sqlite3.connect(self.db_path)

    def init_database(self):
        """Initialize database schema"""
        conn = self.get_connection()
        cursor = conn.cursor()

        # Job descriptions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS job_descriptions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                company_name TEXT NOT NULL,
                job_title TEXT,
                job_description TEXT NOT NULL,
                job_url TEXT,
                keywords TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(company_name, job_description)
            )
        """)

        # Generated resumes table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS generated_resumes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_description_id INTEGER NOT NULL,
                resume_content TEXT NOT NULL,
                ats_score INTEGER,
                file_path TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (job_description_id) REFERENCES job_descriptions(id),
                UNIQUE(job_description_id)
            )
        """)

        # Company research cache (from Perplexity)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS company_research (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                company_name TEXT UNIQUE NOT NULL,
                research_data TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Generated cover letters table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS generated_cover_letters (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_description_id INTEGER NOT NULL,
                resume_id INTEGER,
                cover_letter_content TEXT NOT NULL,
                file_path TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (job_description_id) REFERENCES job_descriptions(id),
                FOREIGN KEY (resume_id) REFERENCES generated_resumes(id),
                UNIQUE(job_description_id)
            )
        """)

        # Resume versions table for tracking edit history
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS resume_versions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                resume_id INTEGER NOT NULL,
                content TEXT NOT NULL,
                version_notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (resume_id) REFERENCES generated_resumes(id) ON DELETE CASCADE
            )
        """)

        # Create index for faster version queries
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_version_resume
            ON resume_versions(resume_id, created_at DESC)
        """)

        conn.commit()
        conn.close()

    def insert_job_description(self, company_name, job_description, job_title=None, job_url=None, keywords=None):
        """Insert or get existing job description"""
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                INSERT INTO job_descriptions (company_name, job_title, job_description, job_url, keywords)
                VALUES (?, ?, ?, ?, ?)
            """, (company_name, job_title, job_description, job_url, keywords))
            conn.commit()
            job_id = cursor.lastrowid
        except sqlite3.IntegrityError:
            # Job description already exists
            cursor.execute("""
                SELECT id FROM job_descriptions
                WHERE company_name = ? AND job_description = ?
            """, (company_name, job_description))
            job_id = cursor.fetchone()[0]

        conn.close()
        return job_id

    def check_resume_exists(self, job_description_id):
        """Check if resume already generated for this job"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, file_path, created_at FROM generated_resumes
            WHERE job_description_id = ?
        """, (job_description_id,))

        result = cursor.fetchone()
        conn.close()

        if result:
            return {
                "id": result[0],
                "file_path": result[1],
                "created_at": result[2]
            }
        return None

    def insert_generated_resume(self, job_description_id, resume_content, file_path, ats_score=None):
        """Insert generated resume"""
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                INSERT INTO generated_resumes (job_description_id, resume_content, file_path, ats_score)
                VALUES (?, ?, ?, ?)
            """, (job_description_id, resume_content, file_path, ats_score))
            conn.commit()
            resume_id = cursor.lastrowid
        except sqlite3.IntegrityError:
            # Resume already exists, update it
            cursor.execute("""
                UPDATE generated_resumes
                SET resume_content = ?, file_path = ?, ats_score = ?
                WHERE job_description_id = ?
            """, (resume_content, file_path, ats_score, job_description_id))
            conn.commit()
            cursor.execute("""
                SELECT id FROM generated_resumes WHERE job_description_id = ?
            """, (job_description_id,))
            resume_id = cursor.fetchone()[0]

        conn.close()
        return resume_id

    def get_company_research(self, company_name):
        """Get cached company research"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT research_data FROM company_research
            WHERE company_name = ?
        """, (company_name,))

        result = cursor.fetchone()
        conn.close()

        return result[0] if result else None

    def save_company_research(self, company_name, research_data):
        """Save company research to cache"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT OR REPLACE INTO company_research (company_name, research_data)
            VALUES (?, ?)
        """, (company_name, research_data))

        conn.commit()
        conn.close()

    def get_all_resumes(self):
        """Get all generated resumes with job info"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                r.id,
                j.company_name,
                j.job_title,
                r.file_path,
                r.ats_score,
                r.created_at
            FROM generated_resumes r
            JOIN job_descriptions j ON r.job_description_id = j.id
            ORDER BY r.created_at DESC
        """)

        results = cursor.fetchall()
        conn.close()

        return [{
            "id": row[0],
            "company_name": row[1],
            "job_title": row[2],
            "file_path": row[3],
            "ats_score": row[4],
            "created_at": row[5]
        } for row in results]

    def check_cover_letter_exists(self, job_description_id):
        """Check if cover letter already generated for this job"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, file_path, created_at FROM generated_cover_letters
            WHERE job_description_id = ?
        """, (job_description_id,))

        result = cursor.fetchone()
        conn.close()

        if result:
            return {
                "id": result[0],
                "file_path": result[1],
                "created_at": result[2]
            }
        return None

    def insert_generated_cover_letter(self, job_description_id, cover_letter_content, file_path, resume_id=None):
        """Insert generated cover letter"""
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                INSERT INTO generated_cover_letters (job_description_id, resume_id, cover_letter_content, file_path)
                VALUES (?, ?, ?, ?)
            """, (job_description_id, resume_id, cover_letter_content, file_path))
            conn.commit()
            cover_letter_id = cursor.lastrowid
        except sqlite3.IntegrityError:
            # Cover letter already exists, update it
            cursor.execute("""
                UPDATE generated_cover_letters
                SET cover_letter_content = ?, file_path = ?, resume_id = ?
                WHERE job_description_id = ?
            """, (cover_letter_content, file_path, resume_id, job_description_id))
            conn.commit()
            cursor.execute("""
                SELECT id FROM generated_cover_letters WHERE job_description_id = ?
            """, (job_description_id,))
            cover_letter_id = cursor.fetchone()[0]

        conn.close()
        return cover_letter_id

    def update_resume_content(self, resume_id, new_content):
        """Update resume content after editing"""
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            # TRANSACTION FIX: Use single transaction for both operations
            # First, get the current content to save as a version
            cursor.execute("""
                SELECT resume_content FROM generated_resumes WHERE id = ?
            """, (resume_id,))
            result = cursor.fetchone()

            if result:
                old_content = result[0]
                # Save the old version to history (in same transaction)
                cursor.execute("""
                    INSERT INTO resume_versions (resume_id, content, version_notes)
                    VALUES (?, ?, ?)
                """, (resume_id, old_content, "Auto-saved before edit"))

            # Update the resume content
            cursor.execute("""
                UPDATE generated_resumes
                SET resume_content = ?,
                    created_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (new_content, resume_id))

            conn.commit()
        except Exception as e:
            conn.rollback()
            raise  # Re-raise to notify caller
        finally:
            conn.close()

    def create_resume_version(self, resume_id, content, version_notes=""):
        """Create a new version of a resume for history tracking"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO resume_versions (resume_id, content, version_notes)
            VALUES (?, ?, ?)
        """, (resume_id, content, version_notes))

        conn.commit()
        version_id = cursor.lastrowid
        conn.close()

        return version_id

    def get_resume_versions(self, resume_id, limit=10):
        """Get version history for a resume"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, content, version_notes, created_at
            FROM resume_versions
            WHERE resume_id = ?
            ORDER BY created_at DESC
            LIMIT ?
        """, (resume_id, limit))

        results = cursor.fetchall()
        conn.close()

        return [{
            "id": row[0],
            "content": row[1],
            "version_notes": row[2],
            "created_at": row[3]
        } for row in results]

    def get_resume_by_id(self, resume_id):
        """Get resume by ID"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                r.id,
                r.job_description_id,
                r.resume_content,
                r.ats_score,
                r.file_path,
                r.created_at,
                j.company_name,
                j.job_title
            FROM generated_resumes r
            JOIN job_descriptions j ON r.job_description_id = j.id
            WHERE r.id = ?
        """, (resume_id,))

        result = cursor.fetchone()
        conn.close()

        if result:
            return {
                "id": result[0],
                "job_description_id": result[1],
                "resume_content": result[2],
                "ats_score": result[3],
                "file_path": result[4],
                "created_at": result[5],
                "company_name": result[6],
                "job_title": result[7]
            }
        return None

    def update_resume_score(self, resume_id, new_score):
        """Update ATS score after editing"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE generated_resumes
            SET ats_score = ?
            WHERE id = ?
        """, (new_score, resume_id))

        conn.commit()
        conn.close()

    def _migrate_scoring_fields(self):
        """
        Migrate database to add new scoring fields.
        Safe to run multiple times - only adds columns if they don't exist.
        """
        conn = self.get_connection()
        cursor = conn.cursor()

        # Check if new columns exist
        cursor.execute("PRAGMA table_info(generated_resumes)")
        columns = [col[1] for col in cursor.fetchall()]

        # Add new scoring columns if they don't exist
        new_columns = {
            'ats_grade': 'TEXT',
            'ats_color': 'TEXT',
            'score_breakdown': 'TEXT',  # JSON field
            'pass_probability': 'REAL'
        }

        for col_name, col_type in new_columns.items():
            if col_name not in columns:
                try:
                    cursor.execute(f"""
                        ALTER TABLE generated_resumes
                        ADD COLUMN {col_name} {col_type}
                    """)
                    conn.commit()
                except sqlite3.OperationalError:
                    # Column might already exist in another process
                    pass

        conn.close()

    def insert_generated_resume_with_score(
        self,
        job_description_id,
        resume_content,
        file_path,
        score_data=None
    ):
        """
        Insert generated resume with comprehensive ATS score data.

        Args:
            job_description_id: ID of the job description
            resume_content: Full text of the resume
            file_path: Path to saved resume file
            score_data: Dict from ATSScorer.score_resume() containing:
                - score: Overall score (0-100)
                - grade: Letter grade (A+, A, B+, etc.)
                - color: Color coding (green, yellow, red)
                - category_scores: Detailed breakdown
                - pass_probability: Estimated pass rate
        """
        conn = self.get_connection()
        cursor = conn.cursor()

        # Extract score data
        if score_data:
            ats_score = int(score_data.get('score', 0))
            ats_grade = score_data.get('grade', 'N/A')
            ats_color = score_data.get('color', 'red')
            pass_probability = score_data.get('pass_probability', 0.0)
            score_breakdown = json.dumps(score_data.get('category_scores', {}))
        else:
            ats_score = None
            ats_grade = None
            ats_color = None
            pass_probability = None
            score_breakdown = None

        try:
            cursor.execute("""
                INSERT INTO generated_resumes (
                    job_description_id,
                    resume_content,
                    file_path,
                    ats_score,
                    ats_grade,
                    ats_color,
                    score_breakdown,
                    pass_probability
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                job_description_id,
                resume_content,
                file_path,
                ats_score,
                ats_grade,
                ats_color,
                score_breakdown,
                pass_probability
            ))
            conn.commit()
            resume_id = cursor.lastrowid
        except sqlite3.IntegrityError:
            # Resume already exists, update it
            cursor.execute("""
                UPDATE generated_resumes
                SET resume_content = ?,
                    file_path = ?,
                    ats_score = ?,
                    ats_grade = ?,
                    ats_color = ?,
                    score_breakdown = ?,
                    pass_probability = ?
                WHERE job_description_id = ?
            """, (
                resume_content,
                file_path,
                ats_score,
                ats_grade,
                ats_color,
                score_breakdown,
                pass_probability,
                job_description_id
            ))
            conn.commit()
            cursor.execute("""
                SELECT id FROM generated_resumes WHERE job_description_id = ?
            """, (job_description_id,))
            resume_id = cursor.fetchone()[0]

        conn.close()
        return resume_id

    def get_resume_score_details(self, resume_id):
        """
        Get detailed ATS score information for a resume.

        Returns:
            Dict with score, grade, color, breakdown, and pass probability
        """
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                ats_score,
                ats_grade,
                ats_color,
                score_breakdown,
                pass_probability
            FROM generated_resumes
            WHERE id = ?
        """, (resume_id,))

        result = cursor.fetchone()
        conn.close()

        if result:
            score_breakdown = None
            if result[3]:
                try:
                    score_breakdown = json.loads(result[3])
                except json.JSONDecodeError:
                    score_breakdown = None

            return {
                'ats_score': result[0],
                'ats_grade': result[1],
                'ats_color': result[2],
                'score_breakdown': score_breakdown,
                'pass_probability': result[4]
            }
        return None

    def get_score_history(self, job_description_id=None, limit=10):
        """
        Get ATS score history, optionally filtered by job description.

        Returns:
            List of score records with trend analysis
        """
        conn = self.get_connection()
        cursor = conn.cursor()

        if job_description_id:
            cursor.execute("""
                SELECT
                    r.id,
                    r.ats_score,
                    r.ats_grade,
                    r.ats_color,
                    r.pass_probability,
                    r.created_at,
                    j.company_name,
                    j.job_title
                FROM generated_resumes r
                JOIN job_descriptions j ON r.job_description_id = j.id
                WHERE r.job_description_id = ?
                ORDER BY r.created_at DESC
                LIMIT ?
            """, (job_description_id, limit))
        else:
            cursor.execute("""
                SELECT
                    r.id,
                    r.ats_score,
                    r.ats_grade,
                    r.ats_color,
                    r.pass_probability,
                    r.created_at,
                    j.company_name,
                    j.job_title
                FROM generated_resumes r
                JOIN job_descriptions j ON r.job_description_id = j.id
                ORDER BY r.created_at DESC
                LIMIT ?
            """, (limit,))

        results = cursor.fetchall()
        conn.close()

        return [{
            'id': row[0],
            'ats_score': row[1],
            'ats_grade': row[2],
            'ats_color': row[3],
            'pass_probability': row[4],
            'created_at': row[5],
            'company_name': row[6],
            'job_title': row[7]
        } for row in results]
