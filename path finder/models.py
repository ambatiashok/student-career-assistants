from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(200))
    branch = db.Column(db.String(50))
    year = db.Column(db.String(20), default="1st Year")
    skills = db.Column(db.Text, default="")
    career_goal = db.Column(db.String(200), default="")
    weakness = db.Column(db.Text, default="")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    roadmaps = db.relationship('RoadmapHistory', backref='user', lazy=True)
    resumes = db.relationship('Resume', backref='user', lazy=True)
    resume_validations = db.relationship('ResumeValidation', backref='user', lazy=True)


class RoadmapHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    skills = db.Column(db.Text, nullable=False)
    goal = db.Column(db.String(200), nullable=False)
    weakness = db.Column(db.Text)
    branch = db.Column(db.String(50))
    roadmap_text = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def formatted_date(self):
        return self.created_at.strftime("%B %d, %Y at %I:%M %p")


class AIQuestion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    category = db.Column(db.String(50), nullable=False)  # 'aptitude' or 'technical'
    questions_data = db.Column(db.Text, nullable=False)  # JSON string of questions
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class TestResult(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    score = db.Column(db.Integer, nullable=False)
    total_questions = db.Column(db.Integer, nullable=False)
    time_taken = db.Column(db.Integer, nullable=False)  # seconds
    questions_data = db.Column(db.Text, nullable=False)  # Store questions for review
    user_answers = db.Column(db.Text, nullable=False)  # Store user answers
    correct_answers = db.Column(db.Text, nullable=False)  # Store correct answers
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def formatted_date(self):
        return self.created_at.strftime("%B %d, %Y at %I:%M %p")
    
    def percentage_score(self):
        return round((self.score / self.total_questions) * 100, 1) if self.total_questions > 0 else 0


# Advanced AI Group Discussion Models - Room-Based System
class GDTopic(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    topic_type = db.Column(db.String(50), nullable=False)  # 'social', 'technology', 'economy', 'abstract', 'case_study'
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    difficulty_level = db.Column(db.String(20), default="medium")  # 'easy', 'medium', 'hard'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    rooms = db.relationship('GDRoom', backref='topic', lazy=True)


class GDRoom(db.Model):
    """Room-based Group Discussion System - Like Ludo Game Rooms"""
    id = db.Column(db.Integer, primary_key=True)
    room_id = db.Column(db.String(10), unique=True, nullable=False)  # 6-digit room ID
    room_name = db.Column(db.String(100), nullable=False)
    topic_id = db.Column(db.Integer, db.ForeignKey('gd_topic.id'), nullable=False)
    host_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Room Settings
    max_participants = db.Column(db.Integer, default=6)  # Maximum participants
    min_participants = db.Column(db.Integer, default=2)  # Minimum to start
    with_ai = db.Column(db.Boolean, default=False)       # GD with AI participant
    discussion_mode = db.Column(db.String(20), default="turn_based")  # 'turn_based', 'open'
    turn_duration = db.Column(db.Integer, default=120)  # seconds per turn
    total_duration = db.Column(db.Integer, default=1200)  # 20 minutes total
    
    # Room Status
    status = db.Column(db.String(20), default="waiting")  # 'waiting', 'active', 'completed', 'cancelled'
    current_speaker = db.Column(db.Integer, db.ForeignKey('user.id'))  # Current turn
    current_turn = db.Column(db.Integer, default=1)
    turn_start_time = db.Column(db.DateTime)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    started_at = db.Column(db.DateTime)
    ended_at = db.Column(db.DateTime)
    
    # Relationships
    host = db.relationship('User', foreign_keys=[host_id], backref='hosted_rooms')
    speaker = db.relationship('User', foreign_keys=[current_speaker])
    participants = db.relationship('GDRoomParticipant', backref='room', lazy=True, cascade='all, delete-orphan')
    messages = db.relationship('GDMessage', backref='room', lazy=True, cascade='all, delete-orphan')
    evaluations = db.relationship('GDRoomEvaluation', backref='room', lazy=True, cascade='all, delete-orphan')
    
    def get_participant_count(self):
        return len([p for p in self.participants if p.status == 'active'])
    
    def is_ready_to_start(self):
        return self.get_participant_count() >= self.min_participants
    
    def get_active_participants(self):
        return [p for p in self.participants if p.status == 'active']
    
    def get_next_speaker(self):
        """Get next participant for turn-based discussion"""
        active_participants = self.get_active_participants()
        if not active_participants:
            return None
        
        if self.current_speaker:
            current_index = next((i for i, p in enumerate(active_participants) if p.user_id == self.current_speaker), -1)
            next_index = (current_index + 1) % len(active_participants)
        else:
            next_index = 0
        
        return active_participants[next_index].user_id
    
    def formatted_date(self):
        return self.created_at.strftime("%B %d, %Y at %I:%M %p")
    
    def duration_minutes(self):
        if self.started_at and self.ended_at:
            duration = (self.ended_at - self.started_at).total_seconds()
            return round(duration / 60, 1)
        return 0


class GDRoomParticipant(db.Model):
    """Track participants in each GD room"""
    id = db.Column(db.Integer, primary_key=True)
    room_id = db.Column(db.String(10), db.ForeignKey('gd_room.room_id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Participant Status
    status = db.Column(db.String(20), default="active")  # 'active', 'left', 'kicked'
    role = db.Column(db.String(20), default="participant")  # 'host', 'participant'
    
    # Participation Metrics
    message_count = db.Column(db.Integer, default=0)
    total_speaking_time = db.Column(db.Float, default=0.0)  # in seconds
    turn_count = db.Column(db.Integer, default=0)
    
    # Timestamps
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)
    left_at = db.Column(db.DateTime)
    
    # Relationships
    user = db.relationship('User', backref='gd_participations')
    
    def formatted_join_time(self):
        return self.joined_at.strftime("%I:%M %p")


# Resume Models
class Resume(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    personal_info = db.Column(db.Text, nullable=False)  # JSON: name, email, phone, address
    education = db.Column(db.Text, nullable=False)  # JSON array
    experience = db.Column(db.Text)  # JSON array
    projects = db.Column(db.Text)  # JSON array
    skills = db.Column(db.Text, nullable=False)  # JSON array
    certifications = db.Column(db.Text)  # JSON array
    resume_content = db.Column(db.Text, nullable=False)  # Generated resume HTML/text
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship
    validations = db.relationship('ResumeValidation', backref='resume', lazy=True)
    
    def formatted_date(self):
        return self.created_at.strftime("%B %d, %Y at %I:%M %p")


class ResumeValidation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    resume_id = db.Column(db.Integer, db.ForeignKey('resume.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Enhanced Scoring
    overall_score = db.Column(db.Integer, nullable=False)  # 0-100
    content_score = db.Column(db.Integer, default=0)  # 0-10
    structure_score = db.Column(db.Integer, default=0)  # 0-10
    skills_score = db.Column(db.Integer, default=0)  # 0-10
    ats_score = db.Column(db.Integer, default=0)  # 0-10
    industry_relevance_score = db.Column(db.Integer, default=0)  # 0-10
    
    # Feedback & Analysis
    strengths = db.Column(db.Text)  # JSON array
    weaknesses = db.Column(db.Text)  # JSON array
    suggestions = db.Column(db.Text)  # JSON array
    missing_skills = db.Column(db.Text)  # JSON array
    ats_issues = db.Column(db.Text)  # JSON array
    
    # Enhanced Analytics
    keyword_analysis = db.Column(db.Text)  # JSON object with keyword insights
    industry_insights = db.Column(db.Text)  # JSON object with market analysis
    benchmarking = db.Column(db.Text)  # JSON object with peer comparison
    actionable_roadmap = db.Column(db.Text)  # JSON array with improvement plan
    skill_gap_analysis = db.Column(db.Text)  # JSON object with detailed gap analysis
    
    # Recruiter Simulation
    hiring_probability = db.Column(db.Integer, default=0)  # 0-100
    recruiter_feedback = db.Column(db.Text)
    interview_readiness = db.Column(db.String(20))  # poor, fair, good, excellent
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def formatted_date(self):
        return self.created_at.strftime("%B %d, %Y at %I:%M %p")
    
    def get_grade(self):
        if self.overall_score >= 90:
            return "A+"
        elif self.overall_score >= 80:
            return "A"
        elif self.overall_score >= 70:
            return "B"
        elif self.overall_score >= 60:
            return "C"
        else:
            return "D"


class GDMessage(db.Model):
    """Store all messages/responses in GD rooms"""
    id = db.Column(db.Integer, primary_key=True)
    room_id = db.Column(db.String(10), db.ForeignKey('gd_room.room_id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)  # Null for AI messages
    
    # Message Content
    content = db.Column(db.Text, nullable=False)  # Changed from message_text to content
    message_type = db.Column(db.String(20), default="participant")  # 'participant', 'ai_feedback', 'moderator'
    
    # Turn Management
    turn_number = db.Column(db.Integer, default=0)
    
    # Message Metrics
    word_count = db.Column(db.Integer, default=0)
    character_count = db.Column(db.Integer, default=0)
    
    # AI Evaluation Scores (Real-time)
    relevance_score = db.Column(db.Float, default=0.0)  # 0-10
    clarity_score = db.Column(db.Float, default=0.0)    # 0-10
    confidence_score = db.Column(db.Float, default=0.0) # 0-10
    
    # AI Feedback
    ai_feedback = db.Column(db.Text)  # Real-time AI suggestions
    sentiment_score = db.Column(db.Float, default=0.0)  # -1 to 1 (negative to positive)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='gd_messages')
    
    def formatted_time(self):
        return self.created_at.strftime("%I:%M %p")
    
    def get_overall_message_score(self):
        """Calculate combined score for this message"""
        scores = [self.relevance_score, self.clarity_score, self.confidence_score]
        return round(sum(scores) / len(scores), 1) if scores else 0.0


class GDRoomEvaluation(db.Model):
    """Comprehensive evaluation for each participant after room session"""
    id = db.Column(db.Integer, primary_key=True)
    room_id = db.Column(db.String(10), db.ForeignKey('gd_room.room_id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Core Performance Scores (0-10)
    overall_score = db.Column(db.Float, nullable=False, default=0.0)
    communication_score = db.Column(db.Float, default=0.0)
    content_quality = db.Column(db.Float, default=0.0)
    participation_level = db.Column(db.Float, default=0.0)
    leadership_shown = db.Column(db.Float, default=0.0)
    
    # Participation Metrics
    total_messages = db.Column(db.Integer, default=0)
    total_words = db.Column(db.Integer, default=0)
    speaking_time_percentage = db.Column(db.Float, default=0.0)
    
    # Text Feedback
    feedback = db.Column(db.Text)
    strengths = db.Column(db.Text)
    areas_for_improvement = db.Column(db.Text)
    detailed_analysis = db.Column(db.Text)  # JSON string
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='gd_evaluations')
    
    def formatted_date(self):
        return self.created_at.strftime("%B %d, %Y at %I:%M %p")
    
    def grade_letter(self):
        if self.overall_score >= 9: return "A+"
        elif self.overall_score >= 8: return "A"
        elif self.overall_score >= 7: return "B+"
        elif self.overall_score >= 6: return "B"
        elif self.overall_score >= 5: return "C+"
        elif self.overall_score >= 4: return "C"
        elif self.overall_score >= 3: return "D"
        else: return "F"


# ─────────────────── SCHEDULING MODULE ───────────────────

class Schedule(db.Model):
    """Personal scheduling & event planning for placement preparation."""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    # Event Identity
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, default="")
    event_type = db.Column(db.String(50), nullable=False, default='custom')
    # event_type options: mock_test | gd_session | interview | resume_review | roadmap_task | custom

    # Time
    date = db.Column(db.String(20), nullable=False)   # "YYYY-MM-DD"
    time = db.Column(db.String(10), nullable=False)   # "HH:MM"
    duration = db.Column(db.Integer, default=60)      # minutes

    # Organisation
    priority = db.Column(db.String(10), default='medium')   # low | medium | high
    status = db.Column(db.String(20), default='scheduled')  # scheduled | ongoing | completed | missed | cancelled
    reminder_minutes = db.Column(db.Integer, default=30)    # reminder X mins before

    # Optional link to an existing resource (roadmap id, test id …)
    linked_resource_id = db.Column(db.Integer, nullable=True)
    notes = db.Column(db.Text, default="")

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = db.relationship('User', backref='schedules')

    def formatted_date(self):
        try:
            dt = datetime.strptime(self.date, "%Y-%m-%d")
            return dt.strftime("%B %d, %Y")
        except Exception:
            return self.date

    def formatted_datetime(self):
        try:
            dt = datetime.strptime(f"{self.date} {self.time}", "%Y-%m-%d %H:%M")
            return dt.strftime("%b %d, %Y at %I:%M %p")
        except Exception:
            return f"{self.date} {self.time}"

    def is_past(self):
        try:
            dt = datetime.strptime(f"{self.date} {self.time}", "%Y-%m-%d %H:%M")
            return dt < datetime.utcnow()
        except Exception:
            return False

    def event_icon(self):
        icons = {
            'mock_test': 'fa-pencil-alt',
            'gd_session': 'fa-comments',
            'interview': 'fa-user-tie',
            'resume_review': 'fa-file-alt',
            'roadmap_task': 'fa-map-signs',
            'custom': 'fa-calendar-check',
        }
        return icons.get(self.event_type, 'fa-calendar-check')

    def event_color(self):
        colors = {
            'mock_test': '#3b82f6',
            'gd_session': '#8b5cf6',
            'interview': '#10b981',
            'resume_review': '#f59e0b',
            'roadmap_task': '#06b6d4',
            'custom': '#6b7280',
        }
        return colors.get(self.event_type, '#6b7280')


# ─────────────────── AI INTERVIEW CHATBOT MODULE ───────────────────

class InterviewSession(db.Model):
    """Stores each AI-driven mock interview session."""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    # Setup
    job_role = db.Column(db.String(200), nullable=False)
    interview_type = db.Column(db.String(50), nullable=False, default='technical')
    # interview_type: technical | behavioral | hr | mixed

    # State
    status = db.Column(db.String(20), default='active')
    # status: active | completed | abandoned
    current_stage = db.Column(db.String(50), default='introduction')
    # stages: introduction → technical → behavioral → situational → wrap_up
    question_count = db.Column(db.Integer, default=0)
    total_questions = db.Column(db.Integer, default=10)

    # Final Report (JSON)
    overall_score = db.Column(db.Float, default=0.0)         # 0–100
    technical_score = db.Column(db.Float, default=0.0)
    communication_score = db.Column(db.Float, default=0.0)
    confidence_score = db.Column(db.Float, default=0.0)
    final_report = db.Column(db.Text)   # JSON: strengths, weaknesses, suggestions

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)

    # Relationships
    user = db.relationship('User', backref='interview_sessions')
    messages = db.relationship('InterviewMessage', backref='session',
                               lazy=True, cascade='all, delete-orphan',
                               order_by='InterviewMessage.created_at')

    def formatted_date(self):
        return self.created_at.strftime("%B %d, %Y at %I:%M %p")

    def duration_minutes(self):
        if self.completed_at:
            return round((self.completed_at - self.created_at).total_seconds() / 60, 1)
        return 0

    def grade(self):
        s = self.overall_score
        if s >= 85: return 'A+'
        elif s >= 75: return 'A'
        elif s >= 65: return 'B+'
        elif s >= 55: return 'B'
        elif s >= 45: return 'C'
        else: return 'D'

    def progress_pct(self):
        if self.total_questions == 0:
            return 0
        return min(100, round(self.question_count * 100 / self.total_questions))


class InterviewMessage(db.Model):
    """Stores every turn (AI question or user answer) in an interview session."""
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('interview_session.id'), nullable=False)

    role = db.Column(db.String(20), nullable=False)   # 'ai' | 'user'
    content = db.Column(db.Text, nullable=False)
    stage = db.Column(db.String(50), default='introduction')
    turn_number = db.Column(db.Integer, default=0)

    # Per-turn AI evaluation (only for user messages)
    answer_score = db.Column(db.Float, default=0.0)          # 0–10
    answer_feedback = db.Column(db.Text)                     # One-line AI comment
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def formatted_time(self):
        return self.created_at.strftime("%I:%M %p")


class AIAssistantChat(db.Model):
    """Stores AI Assistant conversation history with context awareness"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Message details
    role = db.Column(db.String(20), nullable=False)  # 'user' or 'assistant'
    message = db.Column(db.Text, nullable=False)
    
    # Context information
    mode = db.Column(db.String(50), default='general')  # 'career', 'interview', 'resume', 'skill', 'job', 'general'
    context_data = db.Column(db.Text)  # JSON string of user data used for this response
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    session_id = db.Column(db.String(50))  # To group conversations
    
    def formatted_time(self):
        return self.created_at.strftime("%I:%M %p")
    
    def formatted_date(self):
        return self.created_at.strftime("%B %d, %Y")
