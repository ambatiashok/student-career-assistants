from flask import Flask, render_template, request, redirect, session, flash, jsonify
from models import db, User, RoadmapHistory, AIQuestion, TestResult, GDTopic, Resume, ResumeValidation, GDRoom, GDRoomParticipant, GDMessage, GDRoomEvaluation, Schedule, InterviewSession, InterviewMessage, AIAssistantChat
from ai_service import generate_roadmap, generate_mock_test, parse_questions, evaluate_answers, evaluate_gd_response, generate_resume, validate_resume, simulate_recruiter_review, suggest_resume_improvements, generate_resume_summary, extract_text_from_file, analyze_resume_format, generate_resume_templates, analyze_skill_gaps, generate_gd_topic_for_room, generate_individual_participant_evaluation, evaluate_message_realtime, ai_moderator_intervention, analyze_room_session_comprehensive, start_interview, interview_next_turn, generate_interview_report, generate_custom_topic_test, generate_ai_gd_participant_response, generate_job_suggestions, intelligent_assistant_chat, generate_smart_suggestions, generate_performance_insight, detect_intent_and_mode
import bcrypt
from datetime import datetime
from sqlalchemy import func
import json
import time
import base64
import io
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "secret123")

# Vercel/serverless: only /tmp is writable; detect by checking VERCEL or VERCEL_ENV env vars
IS_VERCEL = bool(os.environ.get("VERCEL") or os.environ.get("VERCEL_ENV") or os.environ.get("VERCEL_URL"))
if IS_VERCEL:
    DB_PATH = "/tmp/career.db"
    UPLOAD_DIR = "/tmp/uploads"
else:
    DB_PATH = None  # use default instance/ folder
    UPLOAD_DIR = "uploads"

if DB_PATH:
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:////tmp/career.db"
else:
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///career.db"

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["UPLOAD_FOLDER"] = UPLOAD_DIR
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16MB max file size

# Allowed file extensions
ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'txt'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

db.init_app(app)

# Custom template filter
@app.template_filter('from_json')
def from_json_filter(value):
    if value:
        try:
            return json.loads(value)
        except:
            return {}
    return {}

def clean_json_response(text):
    """Strip markdown code fences from AI JSON responses before parsing."""
    if not text:
        return text
    text = text.strip()
    # Remove ```json ... ``` or ``` ... ``` wrappers
    if text.startswith('```'):
        lines = text.split('\n')
        # Drop first line (```json or ```) and last if it's ```
        start = 1
        end = len(lines)
        if lines[-1].strip() == '```':
            end -= 1
        text = '\n'.join(lines[start:end]).strip()
    return text

# Create upload directory if it doesn't exist (safe on read-only FS)
try:
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
except OSError:
    pass

# Initialise DB lazily so a failing create_all() doesn't crash the import
_db_initialised = False

def _init_db():
    global _db_initialised
    if _db_initialised:
        return
    try:
        with app.app_context():
            db.create_all()
        _db_initialised = True
    except Exception as e:
        print(f"[DB INIT WARNING] {e}")

@app.before_request
def before_request():
    _init_db()

# ---------- HOME ----------
@app.route("/")
def home():
    return redirect("/login")

# ---------- REGISTER ----------
@app.route("/register", methods=["GET","POST"])
def register():
    if request.method == "POST":

        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]
        branch = request.form["branch"]

        hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt())

        user = User(
            name=name,
            email=email,
            password=hashed.decode(),
            branch=branch
        )

        db.session.add(user)
        db.session.commit()

        return redirect("/login")

    return render_template("register.html")

# ---------- LOGIN ----------
@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        user = User.query.filter_by(email=email).first()

        if user and bcrypt.checkpw(password.encode(), user.password.encode()):
            session["user"] = user.id
            return redirect("/dashboard")

    return render_template("login.html")

# ---------- DASHBOARD (hub – no roadmap form) ----------
@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect("/login")

    user = User.query.get(session["user"])

    # Stats
    total_roadmaps = RoadmapHistory.query.filter_by(user_id=user.id).count()

    profile_completion = 0
    if user.name: profile_completion += 20
    if user.skills: profile_completion += 25
    if user.career_goal: profile_completion += 25
    if user.branch: profile_completion += 15
    if user.year: profile_completion += 15

    readiness_level = min(100, profile_completion + (total_roadmaps * 5))

    total_tests = TestResult.query.filter_by(user_id=user.id).count()
    avg_test_score = db.session.query(
        func.avg(TestResult.score * 100.0 / TestResult.total_questions)
    ).filter_by(user_id=user.id).scalar() or 0

    return render_template("dashboard.html",
                           user=user,
                           total_roadmaps=total_roadmaps,
                           readiness_level=readiness_level,
                           profile_completion=profile_completion,
                           total_tests=total_tests,
                           avg_test_score=round(avg_test_score, 1))


# ---------- GENERATE ROADMAP (separate screen) ----------
@app.route("/generate-roadmap", methods=["GET", "POST"])
def generate_roadmap_page():
    if "user" not in session:
        return redirect("/login")

    user = User.query.get(session["user"])
    roadmap = None
    saved = False

    if request.method == "POST":
        skills   = request.form["skills"]
        goal     = request.form["goal"]
        weakness = request.form["weakness"]
        branch   = request.form["branch"]

        roadmap = generate_roadmap(branch, skills, goal, weakness)

        if roadmap:
            history = RoadmapHistory(
                user_id=user.id,
                skills=skills,
                goal=goal,
                weakness=weakness,
                branch=branch,
                roadmap_text=roadmap
            )
            db.session.add(history)
            db.session.commit()
            return redirect(f"/roadmap/{history.id}")

    return render_template("generate_roadmap.html", user=user)

# ---------- PROFILE ----------
@app.route("/profile", methods=["GET", "POST"])
def profile():
    if "user" not in session:
        return redirect("/login")
    
    user = User.query.get(session["user"])
    success = False
    
    if request.method == "POST":
        user.name = request.form.get("name", user.name)
        user.branch = request.form.get("branch", user.branch)
        user.year = request.form.get("year", user.year)
        user.skills = request.form.get("skills", user.skills)
        user.career_goal = request.form.get("career_goal", user.career_goal)
        user.weakness = request.form.get("weakness", user.weakness)
        
        db.session.commit()
        success = True
    
    # Get statistics
    total_roadmaps = RoadmapHistory.query.filter_by(user_id=user.id).count()
    
    return render_template("profile.html", user=user, success=success, total_roadmaps=total_roadmaps)

# ---------- ROADMAP HISTORY ----------
@app.route("/history")
def history():
    if "user" not in session:
        return redirect("/login")
    
    user = User.query.get(session["user"])
    roadmaps = RoadmapHistory.query.filter_by(user_id=user.id).order_by(RoadmapHistory.created_at.desc()).all()
    
    return render_template("history.html", user=user, roadmaps=roadmaps)

# ---------- VIEW SINGLE ROADMAP ----------
@app.route("/roadmap/<int:roadmap_id>")
def view_roadmap(roadmap_id):
    if "user" not in session:
        return redirect("/login")
    
    user = User.query.get(session["user"])
    roadmap = RoadmapHistory.query.filter_by(id=roadmap_id, user_id=user.id).first()
    
    if not roadmap:
        return redirect("/history")
    
    return render_template("view_roadmap.html", user=user, roadmap=roadmap)

# ---------- DELETE ROADMAP ----------
@app.route("/roadmap/delete/<int:roadmap_id>", methods=["POST"])
def delete_roadmap(roadmap_id):
    if "user" not in session:
        return redirect("/login")
    
    roadmap = RoadmapHistory.query.filter_by(id=roadmap_id, user_id=session["user"]).first()
    
    if roadmap:
        db.session.delete(roadmap)
        db.session.commit()
    
    return redirect("/history")

# ---------- PERFORMANCE DASHBOARD ----------
@app.route("/performance")
def performance():
    if "user" not in session:
        return redirect("/login")

    user = User.query.get(session["user"])
    if not user:
        return redirect("/login")

    try:
        import json as _json

        # ── 1. ROADMAPS ──────────────────────────────────────────────
        roadmaps = RoadmapHistory.query.filter_by(user_id=user.id).order_by(RoadmapHistory.created_at.asc()).all() or []
        total_roadmaps = len(roadmaps)

        unique_skills   = set()
        unique_goals    = set()
        branches_explored = set()
        for rm in roadmaps:
            try:
                if rm.skills:
                    for s in str(rm.skills).split(','):
                        s = s.strip().lower()
                        if s: unique_skills.add(s)
                if rm.goal:
                    unique_goals.add(str(rm.goal).strip().lower())
                if rm.branch:
                    branches_explored.add(str(rm.branch).strip())
            except Exception:
                continue

        # ── 2. MOCK TESTS ─────────────────────────────────────────────
        test_results = TestResult.query.filter_by(user_id=user.id).order_by(TestResult.created_at.asc()).all() or []
        total_tests = len(test_results)
        avg_test_score = 0.0
        best_test_score = 0
        test_category_scores = {}   # {category: [pct, ...]}
        for tr in test_results:
            try:
                pct = round((tr.score / tr.total_questions) * 100, 1) if tr.total_questions else 0
                avg_test_score += pct
                if pct > best_test_score:
                    best_test_score = pct
                cat = tr.category or 'other'
                test_category_scores.setdefault(cat, []).append(pct)
            except Exception:
                continue
        avg_test_score = round(avg_test_score / total_tests, 1) if total_tests else 0.0
        # Per-category averages
        category_avg = {cat: round(sum(v)/len(v), 1) for cat, v in test_category_scores.items()}

        # ── 3. INTERVIEWS ─────────────────────────────────────────────
        interview_sessions = InterviewSession.query.filter_by(user_id=user.id).order_by(InterviewSession.created_at.asc()).all() or []
        total_interviews = len(interview_sessions)
        completed_interviews = [s for s in interview_sessions if s.status == 'completed']
        avg_interview_score = 0.0
        best_interview_score = 0.0
        avg_comm_score = 0.0
        avg_tech_score = 0.0
        avg_conf_score = 0.0
        if completed_interviews:
            avg_interview_score = round(sum(s.overall_score for s in completed_interviews) / len(completed_interviews), 1)
            best_interview_score = round(max(s.overall_score for s in completed_interviews), 1)
            avg_comm_score = round(sum(s.communication_score for s in completed_interviews) / len(completed_interviews), 1)
            avg_tech_score = round(sum(s.technical_score for s in completed_interviews) / len(completed_interviews), 1)
            avg_conf_score = round(sum(s.confidence_score for s in completed_interviews) / len(completed_interviews), 1)

        # ── 4. GROUP DISCUSSIONS ──────────────────────────────────────
        gd_evals = GDRoomEvaluation.query.filter_by(user_id=user.id).order_by(GDRoomEvaluation.created_at.asc()).all() or []
        total_gd_sessions = len(gd_evals)
        avg_gd_score = 0.0
        avg_leadership = 0.0
        avg_communication_gd = 0.0
        if gd_evals:
            avg_gd_score = round(sum(e.overall_score for e in gd_evals) / len(gd_evals) * 10, 1)
            avg_leadership = round(sum(e.leadership_shown for e in gd_evals) / len(gd_evals) * 10, 1)
            avg_communication_gd = round(sum(e.communication_score for e in gd_evals) / len(gd_evals) * 10, 1)

        # ── 5. RESUMES ────────────────────────────────────────────────
        resumes = Resume.query.filter_by(user_id=user.id).all() or []
        total_resumes = len(resumes)
        resume_validations = ResumeValidation.query.filter_by(user_id=user.id).order_by(ResumeValidation.created_at.desc()).all() or []
        avg_resume_score = 0
        best_resume_score = 0
        avg_ats_score = 0
        if resume_validations:
            avg_resume_score = round(sum(rv.overall_score for rv in resume_validations) / len(resume_validations))
            best_resume_score = max(rv.overall_score for rv in resume_validations)
            avg_ats_score = round(sum(rv.ats_score for rv in resume_validations) / len(resume_validations))

        # ── 6. PROFILE COMPLETION ─────────────────────────────────────
        profile_completion = 0
        if user.name and str(user.name).strip():        profile_completion += 20
        if user.skills and str(user.skills).strip():    profile_completion += 25
        if user.career_goal and str(user.career_goal).strip(): profile_completion += 25
        if user.branch and str(user.branch).strip():    profile_completion += 15
        if user.year and str(user.year).strip():        profile_completion += 15
        profile_completion = max(0, min(100, profile_completion))

        # ── 7. SKILL SCORES (0-100) ───────────────────────────────────
        # Problem Solving → aptitude/technical test avg
        ps_scores = test_category_scores.get('aptitude', []) + test_category_scores.get('technical', [])
        problem_solving_score = round(sum(ps_scores)/len(ps_scores)) if ps_scores else 0

        # Communication → interview comm avg (0-100) and GD comm avg (0-100)
        comm_parts = []
        if completed_interviews: comm_parts.append(avg_comm_score)
        if gd_evals: comm_parts.append(avg_communication_gd)
        communication_score = round(sum(comm_parts)/len(comm_parts)) if comm_parts else 0

        # Technical Knowledge → technical test avg
        tech_parts = test_category_scores.get('technical', test_category_scores.get('core_engineering', []))
        technical_knowledge_score = round(sum(tech_parts)/len(tech_parts)) if tech_parts else 0

        # Leadership → GD leadership avg (0-100)
        leadership_score = round(avg_leadership) if gd_evals else 0

        # Resume Strength → avg resume validation score
        resume_strength_score = avg_resume_score

        # Verbal/GK → verbal/general_knowledge test avg
        verbal_scores = test_category_scores.get('verbal', []) + test_category_scores.get('general_knowledge', [])
        verbal_score = round(sum(verbal_scores)/len(verbal_scores)) if verbal_scores else 0

        skill_scores = {
            'Problem Solving':    problem_solving_score,
            'Communication':      communication_score,
            'Technical':          technical_knowledge_score,
            'Leadership':         leadership_score,
            'Resume Strength':    resume_strength_score,
            'Verbal & GK':        verbal_score,
        }

        # ── 8. OVERALL CAREER READINESS ───────────────────────────────
        score_parts = [profile_completion]
        if total_roadmaps:   score_parts.append(min(100, total_roadmaps * 8))
        if total_tests:      score_parts.append(avg_test_score)
        if completed_interviews: score_parts.append(avg_interview_score)
        if total_gd_sessions: score_parts.append(avg_gd_score)
        if total_resumes:     score_parts.append(avg_resume_score)
        readiness_level = max(0, min(100, round(sum(score_parts) / len(score_parts))))

        # ── 9. MONTHLY ACTIVITY ───────────────────────────────────────
        monthly_activity = []
        current_date = datetime.now()
        for i in range(6):
            year  = current_date.year
            month = current_date.month - i
            while month <= 0:
                month += 12; year -= 1
            ms = datetime(year, month, 1)
            me = datetime(year + 1, 1, 1) if month == 12 else datetime(year, month + 1, 1)
            rm_cnt  = RoadmapHistory.query.filter(RoadmapHistory.user_id==user.id,  RoadmapHistory.created_at>=ms,  RoadmapHistory.created_at<me).count()
            tst_cnt = TestResult.query.filter(TestResult.user_id==user.id,           TestResult.created_at>=ms,       TestResult.created_at<me).count()
            int_cnt = InterviewSession.query.filter(InterviewSession.user_id==user.id, InterviewSession.created_at>=ms, InterviewSession.created_at<me).count()
            monthly_activity.insert(0, {
                'month': ms.strftime('%b %Y'),
                'roadmaps': int(rm_cnt),
                'tests':    int(tst_cnt),
                'interviews': int(int_cnt),
            })

        # ── 10. RECENT ACTIVITIES (all modules) ───────────────────────
        recent_activities = []
        for rm in roadmaps[-3:]:
            recent_activities.append({'type':'roadmap','icon':'fa-map-marked-alt','color':'#3b82f6','title':rm.goal or 'Roadmap','time':rm.created_at,'link':f'/roadmap/{rm.id}'})
        for tr in test_results[-3:]:
            pct = round((tr.score/tr.total_questions)*100) if tr.total_questions else 0
            recent_activities.append({'type':'test','icon':'fa-pencil-alt','color':'#22c55e','title':f'{tr.category.replace("_"," ").title()} Test – {pct}%','time':tr.created_at,'link':'/test-history'})
        for iv in completed_interviews[-3:]:
            recent_activities.append({'type':'interview','icon':'fa-user-tie','color':'#a855f7','title':f'{iv.job_role} Interview – {iv.overall_score:.0f}%','time':iv.created_at,'link':f'/interview/result/{iv.id}'})
        for gd in gd_evals[-3:]:
            recent_activities.append({'type':'gd','icon':'fa-comments','color':'#f97316','title':f'Group Discussion – {gd.overall_score*10:.0f}%','time':gd.created_at,'link':'/gd-history'})
        recent_activities.sort(key=lambda x: x['time'], reverse=True)
        recent_activities = recent_activities[:8]

        # ── 11. BADGES ────────────────────────────────────────────────
        def badge(icon, label, tier, condition, desc=''):
            return {'icon':icon,'label':label,'tier':tier,'earned':condition,'desc':desc}

        badges = [
            # Roadmap badges
            badge('🚀','First Step',       'bronze', total_roadmaps >= 1,   'Generated your first roadmap'),
            badge('🗺️','Explorer',          'silver', total_roadmaps >= 5,   '5 roadmaps generated'),
            badge('🧭','Navigator',         'gold',   total_roadmaps >= 10,  '10 roadmaps generated'),
            badge('🌍','Pathfinder Master','platinum',total_roadmaps >= 20,  '20 roadmaps generated'),
            # Test badges
            badge('📝','Test Taker',        'bronze', total_tests >= 1,      'Attempted first test'),
            badge('🎯','Sharp Shooter',     'silver', avg_test_score >= 70,  'Avg test score ≥ 70%'),
            badge('🏅','High Achiever',     'gold',   avg_test_score >= 85,  'Avg test score ≥ 85%'),
            badge('💯','Perfect Score',     'platinum',best_test_score >= 100,'Scored 100% in a test'),
            badge('📚','Test Veteran',      'silver', total_tests >= 10,     'Completed 10+ tests'),
            # Interview badges
            badge('🎤','Interview Ready',   'bronze', total_interviews >= 1,  'Completed first interview'),
            badge('💼','Interview Pro',     'silver', len(completed_interviews) >= 5,'5 interviews done'),
            badge('⭐','Top Performer',     'gold',   avg_interview_score >= 80,'Interview avg score ≥ 80%'),
            badge('🌟','Interview Star',    'platinum',best_interview_score >= 90,'Interview score ≥ 90%'),
            # GD badges
            badge('💬','Discussion Starter','bronze', total_gd_sessions >= 1, 'Participated in first GD'),
            badge('🤝','Team Player',       'silver', total_gd_sessions >= 5,  '5 GD sessions done'),
            badge('👑','GD Leader',         'gold',   avg_leadership >= 75,    'Avg leadership score ≥ 75%'),
            # Resume badges
            badge('📄','Resume Creator',   'bronze', total_resumes >= 1,      'Created first resume'),
            badge('✏️','Resume Expert',    'silver', avg_resume_score >= 70,  'Resume score ≥ 70'),
            badge('🎖️','ATS Champion',    'gold',   avg_ats_score >= 8,      'Avg ATS score ≥ 8/10'),
            # Profile & overall
            badge('👤','Profile Complete', 'gold',   profile_completion == 100,'100% profile filled'),
            badge('💻','Skill Collector',  'silver', len(unique_skills) >= 5,  '5+ unique skills'),
            badge('🌐','All-Rounder',      'platinum', total_roadmaps >= 1 and total_tests >= 1 and total_interviews >= 1 and total_resumes >= 1, 'Used all major modules'),
        ]

        # ── 12. TEST SCORE BY CATEGORY (for chart) ───────────────────
        test_chart_labels = list(category_avg.keys())
        test_chart_values = list(category_avg.values())

        template_data = {
            'user': user,
            # Roadmaps
            'total_roadmaps': total_roadmaps,
            'unique_skills': len(unique_skills),
            'unique_goals': len(unique_goals),
            'branches_explored': len(branches_explored),
            'unique_skills_list': sorted(list(unique_skills)),
            # Tests
            'total_tests': total_tests,
            'avg_test_score': avg_test_score,
            'best_test_score': best_test_score,
            'test_chart_labels': test_chart_labels,
            'test_chart_values': test_chart_values,
            # Interviews
            'total_interviews': total_interviews,
            'completed_interviews': len(completed_interviews),
            'avg_interview_score': avg_interview_score,
            'best_interview_score': best_interview_score,
            'avg_comm_score': avg_comm_score,
            'avg_tech_score': avg_tech_score,
            'avg_conf_score': avg_conf_score,
            # GD
            'total_gd_sessions': total_gd_sessions,
            'avg_gd_score': avg_gd_score,
            'avg_leadership': avg_leadership,
            # Resumes
            'total_resumes': total_resumes,
            'avg_resume_score': avg_resume_score,
            'best_resume_score': best_resume_score,
            'avg_ats_score': avg_ats_score,
            # Derived
            'profile_completion': profile_completion,
            'readiness_level': readiness_level,
            'skill_scores': skill_scores,
            'badges': badges,
            'monthly_activity': monthly_activity,
            'recent_activities': recent_activities,
        }
        return render_template("performance.html", **template_data)

    except Exception as e:
        print(f"Critical error in performance route: {e}")
        import traceback; traceback.print_exc()
        safe = {
            'user': user,
            'total_roadmaps': 0, 'unique_skills': 0, 'unique_goals': 0, 'branches_explored': 0,
            'unique_skills_list': [],
            'total_tests': 0, 'avg_test_score': 0, 'best_test_score': 0,
            'test_chart_labels': [], 'test_chart_values': [],
            'total_interviews': 0, 'completed_interviews': 0,
            'avg_interview_score': 0, 'best_interview_score': 0,
            'avg_comm_score': 0, 'avg_tech_score': 0, 'avg_conf_score': 0,
            'total_gd_sessions': 0, 'avg_gd_score': 0, 'avg_leadership': 0,
            'total_resumes': 0, 'avg_resume_score': 0, 'best_resume_score': 0, 'avg_ats_score': 0,
            'profile_completion': 0, 'readiness_level': 0,
            'skill_scores': {'Problem Solving':0,'Communication':0,'Technical':0,'Leadership':0,'Resume Strength':0,'Verbal & GK':0},
            'badges': [],
            'monthly_activity': [{'month':f'Month-{i}','roadmaps':0,'tests':0,'interviews':0} for i in range(6)],
            'recent_activities': [],
        }
        return render_template("performance.html", **safe)

# ---------- LOGOUT ----------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

# ---------- AI MOCK TEST MODULE ----------
@app.route("/mock-test")
def mock_test_home():
    """Mock test landing page with category selection"""
    if "user" not in session:
        return redirect("/login")
    
    user = User.query.get(session["user"])
    
    # Get user statistics
    aptitude_tests      = TestResult.query.filter_by(user_id=user.id, category='aptitude').count()
    technical_tests     = TestResult.query.filter_by(user_id=user.id, category='technical').count()
    verbal_tests        = TestResult.query.filter_by(user_id=user.id, category='verbal').count()
    core_tests          = TestResult.query.filter_by(user_id=user.id, category='core_engineering').count()
    hr_tests            = TestResult.query.filter_by(user_id=user.id, category='hr_interview').count()
    gk_tests            = TestResult.query.filter_by(user_id=user.id, category='general_knowledge').count()
    custom_tests        = TestResult.query.filter_by(user_id=user.id, category='custom').count()

    # Get recent test results
    recent_results = TestResult.query.filter_by(user_id=user.id).order_by(TestResult.created_at.desc()).limit(6).all()

    # Calculate average scores
    def avg_score(cat):
        v = db.session.query(func.avg(TestResult.score * 100.0 / TestResult.total_questions)).filter_by(user_id=user.id, category=cat).scalar() or 0
        return round(v, 1)

    return render_template("mock_test_home.html",
                         user=user,
                         aptitude_tests=aptitude_tests,
                         technical_tests=technical_tests,
                         verbal_tests=verbal_tests,
                         core_tests=core_tests,
                         hr_tests=hr_tests,
                         gk_tests=gk_tests,
                         custom_tests=custom_tests,
                         recent_results=recent_results,
                         aptitude_avg=avg_score('aptitude'),
                         technical_avg=avg_score('technical'),
                         verbal_avg=avg_score('verbal'),
                         core_avg=avg_score('core_engineering'),
                         hr_avg=avg_score('hr_interview'),
                         gk_avg=avg_score('general_knowledge'))

@app.route("/start-custom-test", methods=["POST"])
def start_custom_test():
    """Generate a test on a user-specified topic."""
    if "user" not in session:
        return redirect("/login")

    user = User.query.get(session["user"])
    topic = request.form.get("topic", "").strip()
    difficulty = request.form.get("difficulty", "medium")
    num_questions = min(max(int(request.form.get("num_questions", 5)), 5), 20)

    if not topic:
        flash("Please enter a topic.", "error")
        return redirect("/mock-test")

    raw_questions = generate_custom_topic_test(topic, difficulty, num_questions)
    if not raw_questions:
        flash("Could not generate questions. Please try a different topic.", "error")
        return redirect("/mock-test")

    questions = parse_questions(raw_questions)
    if not questions:
        flash("Error parsing questions. Please try again.", "error")
        return redirect("/mock-test")

    session['current_test'] = {
        'category': 'custom',
        'custom_topic': topic,
        'questions': questions,
        'start_time': time.time(),
        'raw_questions': raw_questions
    }

    return render_template("ai_test.html",
                           user=user,
                           category='custom',
                           custom_topic=topic,
                           questions=questions)


@app.route("/start-test/<category>")
def start_test(category):
    """Generate and start a new test"""
    if "user" not in session:
        return redirect("/login")
    
    VALID_CATEGORIES = ['aptitude', 'technical', 'verbal', 'core_engineering', 'hr_interview', 'general_knowledge']
    if category not in VALID_CATEGORIES:
        return redirect("/mock-test")
    
    user = User.query.get(session["user"])
    
    # Generate questions using AI
    raw_questions = generate_mock_test(category)
    if not raw_questions:
        flash("Error generating questions. Please try again.", "error")
        return redirect("/mock-test")
    
    # Parse questions
    questions = parse_questions(raw_questions)
    if not questions:
        flash("Error parsing questions. Please try again.", "error")
        return redirect("/mock-test")
    
    # Store in session for the test
    session['current_test'] = {
        'category': category,
        'questions': questions,
        'start_time': time.time(),
        'raw_questions': raw_questions
    }
    
    return render_template("ai_test.html", 
                         user=user,
                         category=category,
                         custom_topic='',
                         questions=questions)

@app.route("/submit-test", methods=["POST"])
def submit_test():
    """Process test submission and calculate results"""
    if "user" not in session or "current_test" not in session:
        return redirect("/mock-test")
    
    user = User.query.get(session["user"])
    test_data = session["current_test"]
    
    # Calculate time taken
    time_taken = int(time.time() - test_data['start_time'])
    
    # Get user answers
    user_answers = []
    questions = test_data['questions']
    
    for i in range(len(questions)):
        answer = request.form.get(f'q{i}', '').upper()
        user_answers.append(answer)
    
    # Get correct answers
    correct_answers = [q['correct_answer'] for q in questions]
    
    # Evaluate
    evaluation = evaluate_answers(user_answers, correct_answers)
    
    # Save result to database
    test_result = TestResult(
        user_id=user.id,
        category=test_data['category'],
        score=evaluation['score'],
        total_questions=evaluation['total'],
        time_taken=time_taken,
        questions_data=json.dumps(questions),
        user_answers=json.dumps(user_answers),
        correct_answers=json.dumps(correct_answers)
    )
    
    db.session.add(test_result)
    db.session.commit()
    
    # Store results in session for display
    session['test_result'] = {
        'result_id': test_result.id,
        'category': test_data['category'],
        'custom_topic': test_data.get('custom_topic', ''),
        'score': evaluation['score'],
        'total': evaluation['total'],
        'percentage': evaluation['percentage'],
        'time_taken': time_taken,
        'results': evaluation['results'],
        'questions': questions,
        'user_answers': user_answers
    }
    
    # Clear current test
    session.pop('current_test', None)
    
    return redirect("/test-result")

@app.route("/test-result")
def test_result():
    """Display test results"""
    if "user" not in session or "test_result" not in session:
        return redirect("/mock-test")
    
    user = User.query.get(session["user"])
    result_data = session["test_result"]
    
    return render_template("test_result.html", 
                         user=user,
                         result=result_data)

@app.route("/test-history")
def test_history():
    """Display user's test history"""
    if "user" not in session:
        return redirect("/login")
    
    user = User.query.get(session["user"])
    test_results = TestResult.query.filter_by(user_id=user.id).order_by(TestResult.created_at.desc()).all()
    
    return render_template("test_history.html", 
                         user=user,
                         test_results=test_results)

@app.route("/test-review/<int:result_id>")
def test_review(result_id):
    """Review a specific test result"""
    if "user" not in session:
        return redirect("/login")
    
    user = User.query.get(session["user"])
    test_result = TestResult.query.filter_by(id=result_id, user_id=user.id).first()
    
    if not test_result:
        return redirect("/test-history")
    
    # Parse stored data
    questions = json.loads(test_result.questions_data)
    user_answers = json.loads(test_result.user_answers)
    correct_answers = json.loads(test_result.correct_answers)
    
    # Prepare review data
    review_data = []
    for i, question in enumerate(questions):
        review_data.append({
            'question': question,
            'user_answer': user_answers[i] if i < len(user_answers) else '',
            'correct_answer': correct_answers[i] if i < len(correct_answers) else '',
            'is_correct': (user_answers[i] if i < len(user_answers) else '') == (correct_answers[i] if i < len(correct_answers) else '')
        })
    
    return render_template("test_review.html", 
                         user=user,
                         test_result=test_result,
                         review_data=review_data)

# ---------- ADVANCED AI GROUP DISCUSSION MODULE - ROOM-BASED ----------
@app.route("/group-discussion")
def group_discussion_home():
    """Room-based Group Discussion landing page - Like Ludo Game Room System"""
    if "user" not in session:
        return redirect("/login")
    
    user = User.query.get(session["user"])
    
    # Get available rooms (waiting or active)
    available_rooms = GDRoom.query.filter(
        GDRoom.status.in_(['waiting', 'active'])
    ).order_by(GDRoom.created_at.desc()).limit(10).all()
    
    # Get user's room history and statistics
    completed_rooms = GDRoom.query.join(
        GDRoomParticipant, GDRoom.room_id == GDRoomParticipant.room_id
    ).filter(
        GDRoomParticipant.user_id == user.id,
        GDRoom.status == 'completed'
    ).count()
    
    # Get user's recent evaluations
    recent_evaluations = GDRoomEvaluation.query.filter_by(
        user_id=user.id
    ).order_by(GDRoomEvaluation.created_at.desc()).limit(5).all()
    
    # Calculate average score
    avg_score = sum(eval.overall_score for eval in recent_evaluations) / len(recent_evaluations) if recent_evaluations else 0
    
    # Get topic category statistics
    category_stats = {}
    for topic_type in ['social', 'technology', 'economy', 'abstract', 'case_study']:
        topic_rooms = GDRoom.query.join(GDTopic).filter(
            GDTopic.topic_type == topic_type
        ).join(GDRoomParticipant).filter(
            GDRoomParticipant.user_id == user.id,
            GDRoom.status == 'completed'
        ).count()
        category_stats[topic_type] = topic_rooms
    
    # Check if user is currently in any active room
    current_room = GDRoom.query.join(
        GDRoomParticipant, GDRoom.room_id == GDRoomParticipant.room_id
    ).filter(
        GDRoomParticipant.user_id == user.id,
        GDRoomParticipant.status == 'active',
        GDRoom.status.in_(['waiting', 'active'])
    ).first()
    
    return render_template("gd_room_lobby.html", 
                         user=user,
                         available_rooms=available_rooms,
                         completed_rooms=completed_rooms,
                         recent_evaluations=recent_evaluations,
                         avg_score=round(avg_score, 1),
                         category_stats=category_stats,
                         current_room=current_room)

@app.route("/create-gd-room", methods=["GET", "POST"])
def create_gd_room():
    """Create a new Group Discussion room"""
    if "user" not in session:
        return redirect("/login")
    
    user = User.query.get(session["user"])
    
    # Check if user is already in an active room
    current_room = GDRoomParticipant.query.filter_by(
        user_id=user.id, status='active'
    ).first()
    
    if current_room:
        return redirect(f"/gd-room/{current_room.room_id}")
    
    if request.method == "POST":
        room_name = request.form.get('room_name', '').strip()
        topic_type = request.form.get('topic_type')
        difficulty = request.form.get('difficulty', 'medium')
        max_participants = int(request.form.get('max_participants', 6))
        discussion_mode = request.form.get('discussion_mode', 'turn_based')
        total_duration = int(request.form.get('total_duration', 1200))
        with_ai = request.form.get('with_ai') == 'on'  # AI participant toggle
        
        if not room_name or len(room_name) < 3:
            flash("Room name must be at least 3 characters long.", "error")
            return render_template("create_gd_room.html", user=user)
        
        if topic_type not in ['social', 'technology', 'economy', 'abstract', 'case_study']:
            flash("Invalid topic type selected.", "error")
            return render_template("create_gd_room.html", user=user)
        
        # Generate room ID
        import random
        import string
        room_id = ''.join(random.choices(string.digits, k=6))
        
        # Ensure room ID is unique
        while GDRoom.query.filter_by(room_id=room_id).first():
            room_id = ''.join(random.choices(string.digits, k=6))
        
        # Generate topic for room
        topic_data = generate_gd_topic_for_room(topic_type, difficulty, room_name)
        if not topic_data:
            flash("Error generating topic. Please try again.", "error")
            return render_template("create_gd_room.html", user=user)
        
        # Create topic
        gd_topic = GDTopic(
            topic_type=topic_data['topic_type'],
            title=topic_data['title'],
            description=topic_data['description'],
            difficulty_level=topic_data['difficulty']
        )
        db.session.add(gd_topic)
        db.session.flush()  # Get topic ID
        
        # Create room
        gd_room = GDRoom(
            room_id=room_id,
            room_name=room_name,
            topic_id=gd_topic.id,
            host_id=user.id,
            max_participants=max_participants,
            min_participants=1 if with_ai else 2,
            with_ai=with_ai,
            discussion_mode=discussion_mode,
            total_duration=total_duration,
            status="waiting"
        )
        db.session.add(gd_room)
        
        # Add creator as first participant
        participant = GDRoomParticipant(
            room_id=room_id,
            user_id=user.id,
            role="host",
            status="active"
        )
        db.session.add(participant)
        
        db.session.commit()
        
        flash(f"Room '{room_name}' created successfully! Room ID: {room_id}", "success")
        return redirect(f"/gd-room/{room_id}")
    
    return render_template("create_gd_room.html", user=user)

@app.route("/join-gd-room", methods=["POST"])
def join_gd_room():
    """Join an existing GD room by room ID"""
    if "user" not in session:
        return jsonify({"success": False, "error": "Not authenticated"})
    
    user = User.query.get(session["user"])
    room_id = request.json.get('room_id', '').strip()
    
    if not room_id:
        return jsonify({"success": False, "error": "Room ID is required"})
    
    # Check if user is already in an active room
    current_participation = GDRoomParticipant.query.filter_by(
        user_id=user.id, status='active'
    ).first()
    
    if current_participation:
        return jsonify({
            "success": False, 
            "error": "You are already in an active room",
            "current_room": current_participation.room_id
        })
    
    # Find the room
    room = GDRoom.query.filter_by(room_id=room_id).first()
    if not room:
        return jsonify({"success": False, "error": "Room not found"})
    
    # Check room status
    if room.status not in ['waiting', 'active']:
        return jsonify({"success": False, "error": "Room is not available for joining"})
    
    # Check if room is full
    current_participants = room.get_participant_count()
    if current_participants >= room.max_participants:
        return jsonify({"success": False, "error": "Room is full"})
    
    # Check if user was previously in this room
    existing_participation = GDRoomParticipant.query.filter_by(
        room_id=room_id, user_id=user.id
    ).first()
    
    if existing_participation:
        # Rejoin the room
        existing_participation.status = 'active'
        existing_participation.joined_at = datetime.utcnow()
    else:
        # Add new participant
        participant = GDRoomParticipant(
            room_id=room_id,
            user_id=user.id,
            role="participant",
            status="active"
        )
        db.session.add(participant)
    
    db.session.commit()
    
    return jsonify({
        "success": True,
        "room_id": room_id,
        "redirect_url": f"/gd-room/{room_id}"
    })

@app.route("/gd-room/<room_id>")
def gd_room(room_id):
    """Group Discussion room interface - waiting lobby or active discussion"""
    if "user" not in session:
        return redirect("/login")
    
    user = User.query.get(session["user"])
    
    # Find the room
    room = GDRoom.query.filter_by(room_id=room_id).first()
    if not room:
        flash("Room not found.", "error")
        return redirect("/group-discussion")
    
    # Check if user is participant in this room
    participant = GDRoomParticipant.query.filter_by(
        room_id=room_id, user_id=user.id, status='active'
    ).first()
    
    if not participant:
        flash("You are not a participant in this room.", "error")
        return redirect("/group-discussion")
    
    # Get room topic
    topic = GDTopic.query.get(room.topic_id)
    
    # Get all active participants
    participants = GDRoomParticipant.query.filter_by(
        room_id=room_id, status='active'
    ).all()
    
    # Get room messages
    messages = GDMessage.query.filter_by(
        room_id=room_id
    ).order_by(GDMessage.created_at.asc()).all()
    
    # Check room status and render appropriate template
    if room.status == 'waiting':
        return render_template("gd_waiting_lobby.html", 
                             user=user,
                             room=room,
                             topic=topic,
                             participants=participants,
                             participant=participant)
    
    elif room.status == 'active':
        return render_template("gd_active_room.html", 
                             user=user,
                             room=room,
                             topic=topic,
                             participants=participants,
                             participant=participant,
                             messages=messages)
    
    elif room.status == 'completed':
        return redirect(f"/gd-room-results/{room_id}")
    
    else:
        flash("Room is not available.", "error")
        return redirect("/group-discussion")

# ---------- MISSING GD ROOM CONTROL ROUTES ----------

@app.route("/start-gd-room", methods=["POST"])
def start_gd_room():
    """Start a discussion room (host only)"""
    if "user" not in session:
        return jsonify({"success": False, "error": "Not authenticated"})
    
    user = User.query.get(session["user"])
    room_id = request.json.get('room_id')
    
    if not room_id:
        return jsonify({"success": False, "error": "Room ID is required"})
    
    room = GDRoom.query.filter_by(room_id=room_id).first()
    if not room:
        return jsonify({"success": False, "error": "Room not found"})
    
    if room.host_id != user.id:
        return jsonify({"success": False, "error": "Only the host can start the room"})
    
    if room.status != 'waiting':
        return jsonify({"success": False, "error": "Room is not in waiting state"})
    
    if not room.is_ready_to_start():
        return jsonify({"success": False, "error": f"Need at least {room.min_participants} participants to start"})
    
    # Start the room
    room.status = 'active'
    room.started_at = datetime.utcnow()
    room.current_turn = 1
    
    # Set first speaker for turn-based mode
    if room.discussion_mode == 'turn_based':
        first_speaker = room.get_next_speaker()
        if first_speaker:
            room.current_speaker = first_speaker
            room.turn_start_time = datetime.utcnow()
    
    db.session.commit()
    
    return jsonify({
        "success": True,
        "message": "Discussion started successfully!",
        "redirect_url": f"/gd-room/{room_id}"
    })

@app.route("/cancel-gd-room", methods=["POST"])
def cancel_gd_room():
    """Cancel a room (host only)"""
    if "user" not in session:
        return jsonify({"success": False, "error": "Not authenticated"})
    
    user = User.query.get(session["user"])
    room_id = request.json.get('room_id')
    
    if not room_id:
        return jsonify({"success": False, "error": "Room ID is required"})
    
    room = GDRoom.query.filter_by(room_id=room_id).first()
    if not room:
        return jsonify({"success": False, "error": "Room not found"})
    
    if room.host_id != user.id:
        return jsonify({"success": False, "error": "Only the host can cancel the room"})
    
    if room.status not in ['waiting', 'active']:
        return jsonify({"success": False, "error": "Cannot cancel this room"})
    
    # Cancel the room
    room.status = 'cancelled'
    room.ended_at = datetime.utcnow()
    
    # Mark all participants as left
    participants = GDRoomParticipant.query.filter_by(
        room_id=room_id, status='active'
    ).all()
    
    for participant in participants:
        participant.status = 'left'
        participant.left_at = datetime.utcnow()
    
    db.session.commit()
    
    return jsonify({
        "success": True,
        "message": "Room cancelled successfully!",
        "redirect_url": "/group-discussion"
    })

@app.route("/send-gd-message", methods=["POST"])
def send_gd_message():
    """Send a message in a group discussion"""
    if "user" not in session:
        return jsonify({"success": False, "error": "Not authenticated"})
    
    user = User.query.get(session["user"])
    room_id = request.json.get('room_id')
    content = request.json.get('content', '').strip()
    
    if not room_id or not content:
        return jsonify({"success": False, "error": "Room ID and message content are required"})
    
    room = GDRoom.query.filter_by(room_id=room_id).first()
    if not room:
        return jsonify({"success": False, "error": "Room not found"})
    
    if room.status != 'active':
        return jsonify({"success": False, "error": "Room is not active"})
    
    # Check if user is participant
    participant = GDRoomParticipant.query.filter_by(
        room_id=room_id, user_id=user.id, status='active'
    ).first()
    
    if not participant:
        return jsonify({"success": False, "error": "You are not an active participant"})
    
    # For turn-based discussions, check if it's user's turn
    if room.discussion_mode == 'turn_based' and room.current_speaker != user.id:
        return jsonify({"success": False, "error": "Wait for your turn to speak"})
    
    try:
        # Create the message
        message = GDMessage(
            room_id=room_id,
            user_id=user.id,
            content=content,
            message_type='participant'
        )
        db.session.add(message)
        
        # Update participant stats
        participant.message_count += 1
        
        # For turn-based mode, advance to next speaker
        if room.discussion_mode == 'turn_based':
            participant.turn_count += 1
            next_speaker = room.get_next_speaker()
            room.current_speaker = next_speaker
            room.turn_start_time = datetime.utcnow()
            room.current_turn += 1
        
        db.session.commit()
        
        # Generate AI participant response if room is in AI mode
        if room.with_ai:
            try:
                topic = GDTopic.query.get(room.topic_id)
                recent_msgs = GDMessage.query.filter_by(room_id=room_id).order_by(GDMessage.created_at.asc()).limit(12).all()
                history = []
                for m in recent_msgs:
                    if m.message_type == 'participant' and m.user:
                        history.append(f"{m.user.name}: {m.content}")
                    elif m.message_type == 'ai_participant':
                        history.append(f"AI Participant: {m.content}")
                
                total_turns = GDMessage.query.filter_by(room_id=room_id, message_type='participant').count()
                ai_response = generate_ai_gd_participant_response(
                    topic.title if topic else "General Discussion",
                    topic.description if topic else "",
                    history,
                    turn_number=total_turns
                )
                if ai_response:
                    ai_msg = GDMessage(
                        room_id=room_id,
                        user_id=None,
                        content=ai_response,
                        message_type='ai_participant'
                    )
                    db.session.add(ai_msg)
                    db.session.commit()
            except Exception as e:
                print(f"AI participant response error: {e}")
        
        return jsonify({
            "success": True,
            "message": "Message sent successfully!",
            "next_speaker": room.current_speaker if room.discussion_mode == 'turn_based' else None
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": f"Error sending message: {str(e)}"})

@app.route("/end-gd-room", methods=["POST"])
def end_gd_room():
    """End a discussion room and generate evaluations"""
    if "user" not in session:
        return jsonify({"success": False, "error": "Not authenticated"})
    
    user = User.query.get(session["user"])
    room_id = request.json.get('room_id')
    
    if not room_id:
        return jsonify({"success": False, "error": "Room ID is required"})
    
    room = GDRoom.query.filter_by(room_id=room_id).first()
    if not room:
        return jsonify({"success": False, "error": "Room not found"})
    
    if room.host_id != user.id:
        return jsonify({"success": False, "error": "Only the host can end the room"})
    
    if room.status != 'active':
        return jsonify({"success": False, "error": "Room is not active"})
    
    try:
        # End the room
        room.status = 'completed'
        room.ended_at = datetime.utcnow()
        
        # Mark all participants as completed
        participants = GDRoomParticipant.query.filter_by(
            room_id=room_id, status='active'
        ).all()
        
        # Get room messages and topic
        room_messages = GDMessage.query.filter_by(room_id=room_id).all()
        topic = GDTopic.query.get(room.topic_id)
        
        # Calculate room duration
        if room.started_at and room.ended_at:
            room_duration = (room.ended_at - room.started_at).total_seconds()
        else:
            room_duration = room.total_duration
        
        # Prepare participant data
        participant_data = {}
        for p in participants:
            participant_data[p.user_id] = {
                'name': p.user.name,
                'join_time': p.joined_at,
                'message_count': p.message_count,
                'turn_count': p.turn_count,
                'role': p.role
            }
        
        # Generate comprehensive session analysis
        try:
            session_analysis = analyze_room_session_comprehensive(
                room_messages, 
                topic.title + ": " + topic.description,
                room_duration,
                participant_data
            )
        except Exception as e:
            print(f"Session analysis error: {e}")
            # Create fallback session analysis
            session_analysis = {
                'room_summary': 'Group discussion completed successfully',
                'topic_coverage': 'Good topic coverage',
                'participation_levels': {p.user_id: 7.0 for p in participants}
            }
        
        # Create individual evaluations for each participant
        for participant in participants:
            participant.status = 'completed'
            
            # Get participant messages
            participant_messages = [msg for msg in room_messages if msg.user_id == participant.user_id]
            
            # Generate individual evaluation
            try:
                evaluation_data = generate_individual_participant_evaluation(
                    session_analysis,
                    participant_messages,
                    participant.user_id,
                    participant_data[participant.user_id]
                )
            except Exception as e:
                print(f"AI evaluation error for user {participant.user_id}: {e}")
                # Create fallback evaluation
                evaluation_data = {
                    'overall_score': 7.0,
                    'communication_score': 7.0,
                    'content_quality': 7.0,
                    'participation_level': 7.0,
                    'leadership_shown': 7.0,
                    'feedback': 'Thank you for participating in the discussion!',
                    'strengths': 'Active participation in the discussion',
                    'areas_for_improvement': 'Continue practicing to improve further'
                }
            
            if evaluation_data:
                evaluation = GDRoomEvaluation(
                    room_id=room_id,
                    user_id=participant.user_id,
                    overall_score=evaluation_data.get('overall_score', 7.0),
                    communication_score=evaluation_data.get('communication_score', 7.0),
                    content_quality=evaluation_data.get('content_quality', 7.0),
                    participation_level=evaluation_data.get('participation_level', 7.0),
                    leadership_shown=evaluation_data.get('leadership_shown', 7.0),
                    feedback=evaluation_data.get('feedback', 'Good participation'),
                    strengths=evaluation_data.get('strengths', ''),
                    areas_for_improvement=evaluation_data.get('areas_for_improvement', ''),
                    detailed_analysis=json.dumps(evaluation_data)
                )
                db.session.add(evaluation)
        
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": "Discussion ended successfully!",
            "redirect_url": f"/gd-room-results/{room_id}"
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": f"Error ending discussion: {str(e)}"})


# ---------- EXISTING ROUTES CONTINUE ----------


# ===============================
# RESUME BUILDER ROUTES
# ===============================

@app.route("/resume-builder")
def resume_builder():
    if "user" not in session:
        return redirect("/login")
    
    user = User.query.get(session["user"])
    
    # Get user's existing resumes
    resumes = Resume.query.filter_by(user_id=user.id).order_by(Resume.created_at.desc()).all()
    
    return render_template("resume_builder.html", user=user, resumes=resumes)


@app.route("/create-resume", methods=["GET", "POST"])
def create_resume():
    if "user" not in session:
        return redirect("/login")
    
    user = User.query.get(session["user"])
    
    if request.method == "POST":
        try:
            # Collect form data
            personal_info = {
                "name": request.form.get("name"),
                "email": request.form.get("email"),
                "phone": request.form.get("phone"),
                "address": request.form.get("address"),
                "linkedin": request.form.get("linkedin", ""),
                "github": request.form.get("github", "")
            }
            
            # Education data
            education = []
            education_count = int(request.form.get("education_count", "1"))
            for i in range(education_count):
                edu_data = {
                    "degree": request.form.get(f"degree_{i}"),
                    "institution": request.form.get(f"institution_{i}"),
                    "year": request.form.get(f"graduation_year_{i}"),
                    "grade": request.form.get(f"grade_{i}", "")
                }
                if edu_data["degree"] and edu_data["institution"]:
                    education.append(edu_data)
            
            # Work Experience
            experience = []
            exp_count = int(request.form.get("experience_count", "0"))
            for i in range(exp_count):
                exp_data = {
                    "company": request.form.get(f"company_{i}"),
                    "position": request.form.get(f"position_{i}"),
                    "duration": request.form.get(f"duration_{i}"),
                    "description": request.form.get(f"exp_description_{i}")
                }
                if exp_data["company"] and exp_data["position"]:
                    experience.append(exp_data)
            
            # Projects
            projects = []
            project_count = int(request.form.get("project_count", "1"))
            for i in range(project_count):
                proj_data = {
                    "name": request.form.get(f"project_name_{i}"),
                    "description": request.form.get(f"project_description_{i}"),
                    "technologies": request.form.get(f"project_technologies_{i}"),
                    "link": request.form.get(f"project_link_{i}", "")
                }
                if proj_data["name"] and proj_data["description"]:
                    projects.append(proj_data)
            
            # Skills
            skills = [skill.strip() for skill in request.form.get("skills", "").split(",") if skill.strip()]
            
            # Certifications
            certifications = []
            cert_input = request.form.get("certifications", "")
            if cert_input:
                for cert in cert_input.split("\n"):
                    if cert.strip():
                        certifications.append({"name": cert.strip()})
            
            target_role = request.form.get("target_role", "Software Developer")
            
            # Generate resume using AI
            flash("🤖 Generating your professional resume...", "info")
            
            resume_content = generate_resume(
                personal_info=personal_info,
                education=education,
                experience=experience,
                projects=projects,
                skills=skills,
                certifications=certifications,
                target_role=target_role
            )
            
            if resume_content:
                # Save resume to database
                new_resume = Resume(
                    user_id=user.id,
                    personal_info=json.dumps(personal_info),
                    education=json.dumps(education),
                    experience=json.dumps(experience),
                    projects=json.dumps(projects),
                    skills=json.dumps(skills),
                    certifications=json.dumps(certifications),
                    resume_content=resume_content
                )
                
                db.session.add(new_resume)
                db.session.commit()
                
                flash("✅ Resume generated successfully!", "success")
                return redirect(f"/resume-view/{new_resume.id}")
            else:
                flash("❌ Error generating resume. Please try again.", "error")
                
        except Exception as e:
            flash(f"❌ Error: {str(e)}", "error")
            print(f"Resume creation error: {e}")
    
    return render_template("create_resume.html", user=user)


@app.route("/resume-view/<int:resume_id>")
def resume_view(resume_id):
    if "user" not in session:
        return redirect("/login")
    
    user = User.query.get(session["user"])
    resume = Resume.query.filter_by(id=resume_id, user_id=user.id).first()
    
    if not resume:
        flash("❌ Resume not found.", "error")
        return redirect("/resume-builder")
    
    # Get latest validation if exists
    validation = ResumeValidation.query.filter_by(
        resume_id=resume.id
    ).order_by(ResumeValidation.created_at.desc()).first()
    
    return render_template("resume_view.html", 
                         user=user, 
                         resume=resume, 
                         validation=validation)


@app.route("/validate-resume/<int:resume_id>")
def validate_resume_route(resume_id):
    if "user" not in session:
        return redirect("/login")
    
    user = User.query.get(session["user"])
    resume = Resume.query.filter_by(id=resume_id, user_id=user.id).first()
    
    if not resume:
        flash("❌ Resume not found.", "error")
        return redirect("/resume-builder")
    
    try:
        flash("🔍 AI is analyzing your resume...", "info")
        
        # Get target role from user profile
        target_role = user.career_goal or "Software Developer"
        
        # Validate resume using AI
        validation_result = validate_resume(resume.resume_content, target_role)
        recruiter_result = simulate_recruiter_review(resume.resume_content, target_role)
        
        if validation_result and recruiter_result:
            # Parse AI results
            try:
                validation_data = json.loads(validation_result.strip())
                recruiter_data = json.loads(recruiter_result.strip())
            except json.JSONDecodeError:
                # Fallback if JSON parsing fails
                validation_data = {
                    "overall_score": 75,
                    "content_score": 7,
                    "structure_score": 8, 
                    "skills_score": 7,
                    "ats_score": 8,
                    "strengths": ["Clear structure", "Good technical skills"],
                    "weaknesses": ["Could add more quantified achievements"],
                    "suggestions": ["Add measurable project results", "Include relevant certifications"],
                    "missing_skills": ["Cloud computing", "DevOps tools"],
                    "ats_issues": ["Missing keywords for target role"]
                }
                recruiter_data = {
                    "hiring_probability": 70,
                    "interview_readiness": "good",
                    "recruiter_feedback": "Strong technical background with good project experience."
                }
            
            # Save validation results
            validation = ResumeValidation(
                resume_id=resume.id,
                user_id=user.id,
                overall_score=validation_data.get("overall_score", 75),
                content_score=validation_data.get("content_score", 7),
                structure_score=validation_data.get("structure_score", 8),
                skills_score=validation_data.get("skills_score", 7),
                ats_score=validation_data.get("ats_score", 8),
                strengths=json.dumps(validation_data.get("strengths", [])),
                weaknesses=json.dumps(validation_data.get("weaknesses", [])),
                suggestions=json.dumps(validation_data.get("suggestions", [])),
                missing_skills=json.dumps(validation_data.get("missing_skills", [])),
                ats_issues=json.dumps(validation_data.get("ats_issues", [])),
                hiring_probability=recruiter_data.get("hiring_probability", 70),
                recruiter_feedback=recruiter_data.get("recruiter_feedback", ""),
                interview_readiness=recruiter_data.get("interview_readiness", "good")
            )
            
            db.session.add(validation)
            db.session.commit()
            
            flash("✅ Resume analysis completed!", "success")
            return redirect(f"/resume-analysis/{validation.id}")
        else:
            flash("❌ Error analyzing resume. Please try again.", "error")
    
    except Exception as e:
        flash(f"❌ Analysis error: {str(e)}", "error")
        print(f"Resume validation error: {e}")
    
    return redirect(f"/resume-view/{resume_id}")


@app.route("/resume-analysis/<int:validation_id>")
def resume_analysis(validation_id):
    if "user" not in session:
        return redirect("/login")
    
    user = User.query.get(session["user"])
    validation = ResumeValidation.query.filter_by(
        id=validation_id, 
        user_id=user.id
    ).first()
    
    if not validation:
        flash("❌ Analysis not found.", "error")
        return redirect("/resume-builder")
    
    # Parse JSON fields
    try:
        validation.strengths_list = json.loads(validation.strengths) if validation.strengths else []
        validation.weaknesses_list = json.loads(validation.weaknesses) if validation.weaknesses else []
        validation.suggestions_list = json.loads(validation.suggestions) if validation.suggestions else []
        validation.missing_skills_list = json.loads(validation.missing_skills) if validation.missing_skills else []
        validation.ats_issues_list = json.loads(validation.ats_issues) if validation.ats_issues else []
    except:
        validation.strengths_list = []
        validation.weaknesses_list = []
        validation.suggestions_list = []
        validation.missing_skills_list = []
        validation.ats_issues_list = []
    
    # Generate job suggestions based on resume skills
    try:
        resume_skills = ""
        if validation.resume and validation.resume.skills:
            try:
                skill_list = json.loads(validation.resume.skills)
                if isinstance(skill_list, list):
                    resume_skills = ", ".join(skill_list)
            except Exception:
                pass
        combined_skills = ", ".join(filter(None, [user.skills, resume_skills])) or "Programming"
        job_suggestions = generate_job_suggestions(
            skills=combined_skills,
            career_goal=user.career_goal or "",
            branch=user.branch or "",
            num_suggestions=4
        )
    except Exception as _je:
        print(f"[RESUME ANALYSIS] Job suggestions error: {_je}")
        job_suggestions = []

    return render_template("resume_analysis.html",
                         user=user,
                         validation=validation,
                         resume=validation.resume,
                         job_suggestions=job_suggestions)


@app.route("/resume-history")
def resume_history():
    if "user" not in session:
        return redirect("/login")
    
    user = User.query.get(session["user"])
    
    # Get all resumes with their latest validations
    resumes = db.session.query(Resume).filter_by(user_id=user.id)\
        .outerjoin(ResumeValidation)\
        .order_by(Resume.created_at.desc()).all()
    
    # Add latest validation to each resume
    for resume in resumes:
        resume.latest_validation = ResumeValidation.query.filter_by(
            resume_id=resume.id
        ).order_by(ResumeValidation.created_at.desc()).first()
    
    return render_template("resume_history.html", 
                         user=user, 
                         resumes=resumes)


@app.route("/resume-delete/<int:resume_id>", methods=["POST"])
def delete_resume(resume_id):
    if "user" not in session:
        return redirect("/login")
    
    user = User.query.get(session["user"])
    resume = Resume.query.filter_by(id=resume_id, user_id=user.id).first()
    
    if resume:
        # Delete associated validations
        ResumeValidation.query.filter_by(resume_id=resume.id).delete()
        # Delete resume
        db.session.delete(resume)
        db.session.commit()
        flash("✅ Resume deleted successfully.", "success")
    else:
        flash("❌ Resume not found.", "error")
    
    return redirect("/resume-history")


@app.route("/upload-resume", methods=["GET", "POST"])
def upload_resume():
    """Upload existing resume file for AI analysis"""
    if "user" not in session:
        return redirect("/login")
    
    user = User.query.get(session["user"])
    
    if request.method == "POST":
        try:
            # Check if file was uploaded
            if 'resume_file' not in request.files:
                flash("❌ No file selected.", "error")
                return redirect(request.url)
            
            file = request.files['resume_file']
            
            # Check if file was actually selected
            if file.filename == '':
                flash("❌ No file selected.", "error")
                return redirect(request.url)
            
            # Check if file type is allowed
            if not allowed_file(file.filename):
                flash("❌ Invalid file type. Please upload PDF, DOC, DOCX, or TXT files.", "error")
                return redirect(request.url)
            
            if file:
                # Secure filename and save
                filename = secure_filename(file.filename)
                timestamp = str(int(time.time()))
                filename = f"{user.id}_{timestamp}_{filename}"
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(file_path)
                
                flash("📄 Extracting text from your resume...", "info")
                
                # Extract text from uploaded file
                extracted_text = extract_text_from_file(file_path)
                
                if "Error" in extracted_text or "requires" in extracted_text:
                    flash(f"❌ {extracted_text}", "error")
                    os.remove(file_path)  # Clean up file
                    return redirect(request.url)
                
                flash("🤖 AI is analyzing your resume...", "info")
                
                # Get additional info from form
                target_role = request.form.get("target_role", "Software Developer")
                experience_level = request.form.get("experience_level", "mid-level")
                original_filename = file.filename
                
                # Create basic resume record
                uploaded_resume = Resume(
                    user_id=user.id,
                    personal_info=json.dumps({"name": user.name, "email": ""}),
                    education=json.dumps([]),
                    experience=json.dumps([]),
                    projects=json.dumps([]),
                    skills=json.dumps([]),
                    certifications=json.dumps([]),
                    resume_content=extracted_text  # Store extracted text
                )
                
                db.session.add(uploaded_resume)
                db.session.commit()
                
                # Perform Enhanced AI Analysis
                flash("🔍 Conducting comprehensive AI analysis...", "info")
                validation_result   = validate_resume(extracted_text, target_role)
                recruiter_result    = simulate_recruiter_review(extracted_text, target_role)
                format_analysis_raw = analyze_resume_format(extracted_text)   # returns dict
                skill_gap_raw       = analyze_skill_gaps(extracted_text, target_role, experience_level)

                # Parse skill_gap JSON
                try:
                    skill_gap_dict = json.loads(clean_json_response(skill_gap_raw)) if skill_gap_raw else {}
                except Exception:
                    skill_gap_dict = {}

                # Combine format_analysis + skill_gap into one JSON blob (persisted in DB)
                combined_analysis = json.dumps({
                    "format_analysis": format_analysis_raw if isinstance(format_analysis_raw, dict) else {},
                    "skill_gaps": skill_gap_dict
                })
                
                # Parse AI results (strip markdown fences if present)
                try:
                    validation_data = json.loads(clean_json_response(validation_result)) if validation_result else {}
                except Exception:
                    validation_data = {}

                try:
                    recruiter_data = json.loads(clean_json_response(recruiter_result)) if recruiter_result else {}
                except Exception:
                    recruiter_data = {}

                # Apply fallbacks for missing keys
                validation_data.setdefault("overall_score", 75)
                validation_data.setdefault("content_score", 7)
                validation_data.setdefault("structure_score", 8)
                validation_data.setdefault("skills_score", 7)
                validation_data.setdefault("ats_score", 8)
                validation_data.setdefault("industry_relevance_score", 6)
                validation_data.setdefault("strengths", ["Professional structure identified"])
                validation_data.setdefault("weaknesses", ["Limited quantified achievements"])
                validation_data.setdefault("suggestions", ["Add measurable results"])
                validation_data.setdefault("missing_skills", [])
                validation_data.setdefault("ats_issues", [])
                validation_data.setdefault("keyword_analysis", {"present_keywords": [], "missing_keywords": []})
                validation_data.setdefault("industry_insights", {"market_demand": "high", "trending_skills": []})
                validation_data.setdefault("benchmarking", {"compared_to_peers": "average", "top_percentile": 65})
                validation_data.setdefault("actionable_roadmap", [])
                recruiter_data.setdefault("hiring_probability", 70)
                recruiter_data.setdefault("interview_readiness", "good")
                recruiter_data.setdefault("recruiter_feedback", "Resume shows relevant background for the role.")
                
                # Save comprehensive validation with enhanced fields
                validation = ResumeValidation(
                    resume_id=uploaded_resume.id,
                    user_id=user.id,
                    overall_score=validation_data.get("overall_score", 75),
                    content_score=validation_data.get("content_score", 7),
                    structure_score=validation_data.get("structure_score", 8),
                    skills_score=validation_data.get("skills_score", 7),
                    ats_score=validation_data.get("ats_score", 8),
                    industry_relevance_score=validation_data.get("industry_relevance_score", 6),
                    strengths=json.dumps(validation_data.get("strengths", [])),
                    weaknesses=json.dumps(validation_data.get("weaknesses", [])),
                    suggestions=json.dumps(validation_data.get("suggestions", [])),
                    missing_skills=json.dumps(validation_data.get("missing_skills", [])),
                    ats_issues=json.dumps(validation_data.get("ats_issues", [])),
                    keyword_analysis=json.dumps(validation_data.get("keyword_analysis", {})),
                    industry_insights=json.dumps(validation_data.get("industry_insights", {})),
                    benchmarking=json.dumps(validation_data.get("benchmarking", {})),
                    actionable_roadmap=json.dumps(validation_data.get("actionable_roadmap", [])),
                    skill_gap_analysis=combined_analysis,   # format + skill gaps combined
                    hiring_probability=recruiter_data.get("hiring_probability", 70),
                    recruiter_feedback=recruiter_data.get("recruiter_feedback", ""),
                    interview_readiness=recruiter_data.get("interview_readiness", "good")
                )
                
                db.session.add(validation)
                db.session.commit()
                
                # Clean up uploaded file
                os.remove(file_path)

                session['uploaded_filename'] = original_filename
                
                flash("✅ Resume uploaded and analyzed successfully!", "success")
                return redirect(f"/resume-upload-analysis/{validation.id}")
                
        except Exception as e:
            flash(f"❌ Upload error: {str(e)}", "error")
            print(f"Upload error: {e}")
    
    return render_template("upload_resume.html", user=user)


@app.route("/resume-upload-analysis/<int:validation_id>")
def resume_upload_analysis(validation_id):
    """Display analysis results for uploaded resume"""
    if "user" not in session:
        return redirect("/login")
    
    user = User.query.get(session["user"])
    validation = ResumeValidation.query.filter_by(
        id=validation_id,
        user_id=user.id
    ).first()
    
    if not validation:
        flash("❌ Analysis not found.", "error")
        return redirect("/resume-builder")
    
    # Parse Enhanced JSON fields
    try:
        validation.strengths_list = json.loads(validation.strengths) if validation.strengths else []
        validation.weaknesses_list = json.loads(validation.weaknesses) if validation.weaknesses else []
        validation.suggestions_list = json.loads(validation.suggestions) if validation.suggestions else []
        validation.missing_skills_list = json.loads(validation.missing_skills) if validation.missing_skills else []
        validation.ats_issues_list = json.loads(validation.ats_issues) if validation.ats_issues else []
        validation.keyword_analysis_list = json.loads(validation.keyword_analysis) if validation.keyword_analysis else {}
        validation.industry_insights_list = json.loads(validation.industry_insights) if validation.industry_insights else {}
        validation.benchmarking_list = json.loads(validation.benchmarking) if validation.benchmarking else {}
        validation.actionable_roadmap_list = json.loads(validation.actionable_roadmap) if validation.actionable_roadmap else []
    except Exception as e:
        print(f"Error parsing JSON fields: {e}")
        validation.strengths_list = []
        validation.weaknesses_list = []
        validation.suggestions_list = []
        validation.missing_skills_list = []
        validation.ats_issues_list = []
        validation.keyword_analysis_list = {}
        validation.industry_insights_list = {}
        validation.benchmarking_list = {}
        validation.actionable_roadmap_list = []
    
    uploaded_filename = session.get('uploaded_filename', 'Resume')

    # Parse combined analysis blob (format_analysis + skill_gaps)
    format_analysis = {}
    skill_data = {}
    if validation.skill_gap_analysis:
        try:
            combined = json.loads(clean_json_response(validation.skill_gap_analysis))
            # Support both new combined format and old raw skill_gap string
            if 'format_analysis' in combined or 'skill_gaps' in combined:
                format_analysis = combined.get('format_analysis', {})
                skill_data      = combined.get('skill_gaps', {})
            else:
                skill_data = combined   # old format
        except Exception:
            skill_data = {}

    # Get resume templates
    templates = generate_resume_templates()
    recommended_templates = []
    if validation.industry_relevance_score and validation.industry_relevance_score >= 7:
        recommended_templates.append("professional")
    if validation.skills_score and validation.skills_score >= 8:
        recommended_templates.append("technical")
    if validation.overall_score < 70:
        recommended_templates.append("modern")

    # Generate job suggestions based on resume skills
    try:
        resume_skills = ""
        if validation.resume and validation.resume.skills:
            try:
                skill_list = json.loads(validation.resume.skills)
                if isinstance(skill_list, list):
                    resume_skills = ", ".join(skill_list)
            except Exception:
                pass
        # For uploaded resumes, also pull missing_skills as hints
        gap_hint = ", ".join(validation.missing_skills_list[:5]) if validation.missing_skills_list else ""
        combined_skills = ", ".join(filter(None, [user.skills, resume_skills, gap_hint])) or "Programming"
        upload_job_suggestions = generate_job_suggestions(
            skills=combined_skills,
            career_goal=user.career_goal or "",
            branch=user.branch or "",
            num_suggestions=4
        )
    except Exception as _je:
        print(f"[UPLOAD ANALYSIS] Job suggestions error: {_je}")
        upload_job_suggestions = []

    return render_template("resume_upload_analysis.html",
                         user=user,
                         validation=validation,
                         resume=validation.resume,
                         format_analysis=format_analysis,
                         uploaded_filename=uploaded_filename,
                         templates=templates,
                         recommended_templates=recommended_templates,
                         skill_data=skill_data,
                         job_suggestions=upload_job_suggestions)


@app.route("/resume-templates")
def resume_templates():
    """Display available resume templates"""
    if "user" not in session:
        return redirect("/login")
    
    user = User.query.get(session["user"])
    templates = generate_resume_templates()
    
    return render_template("resume_templates.html", 
                         user=user,
                         templates=templates)


@app.route("/generate-from-template/<template_name>")
def generate_from_template(template_name):
    """Generate resume using selected template"""
    if "user" not in session:
        return redirect("/login")
    
    user = User.query.get(session["user"])
    templates = generate_resume_templates()
    
    if template_name not in templates:
        flash("❌ Invalid template selected.", "error")
        return redirect("/resume-templates")
    
    # Redirect to create resume form with template pre-selected
    session['selected_template'] = template_name
    flash(f"✨ Using {templates[template_name]['name']} template. Fill in your details below.", "info")
    return redirect("/create-resume")


# ===============================
# GD POLL ENDPOINT (real-time updates)
# ===============================

@app.route("/gd-poll/<room_id>")
def gd_poll(room_id):
    """Lightweight polling endpoint for real-time room state (waiting lobby & active room)"""
    if "user" not in session:
        return jsonify({"error": "Not authenticated"}), 401

    room = GDRoom.query.filter_by(room_id=room_id).first()
    if not room:
        return jsonify({"error": "Room not found"}), 404

    # Active participants
    active_participants = GDRoomParticipant.query.filter_by(
        room_id=room_id, status='active'
    ).all()

    participants_data = [{
        "user_id": p.user_id,
        "name": p.user.name,
        "role": p.role,
        "message_count": p.message_count
    } for p in active_participants]

    # Messages since given id
    since_id = request.args.get('since_id', 0, type=int)
    new_messages = GDMessage.query.filter(
        GDMessage.room_id == room_id,
        GDMessage.id > since_id
    ).order_by(GDMessage.created_at.asc()).all()

    messages_data = [{
        "id": m.id,
        "user_id": m.user_id,
        "author": m.user.name if m.user else "AI Moderator",
        "content": m.content,
        "message_type": m.message_type,
        "ai_feedback": m.ai_feedback,
        "time": m.formatted_time()
    } for m in new_messages]

    return jsonify({
        "status": room.status,
        "participant_count": len(active_participants),
        "participants": participants_data,
        "current_speaker_id": room.current_speaker,
        "current_turn": room.current_turn,
        "messages": messages_data
    })


@app.route("/gd-room-results/<room_id>")
def gd_room_results(room_id):
    """Display comprehensive room results for all participants"""
    if "user" not in session:
        return redirect("/login")
    
    user = User.query.get(session["user"])
    room = GDRoom.query.filter_by(room_id=room_id).first()
    
    if not room or room.status != 'completed':
        flash("Room results not available.", "error")
        return redirect("/group-discussion")
    
    participant = GDRoomParticipant.query.filter_by(
        room_id=room_id, user_id=user.id
    ).first()
    
    if not participant:
        flash("You were not a participant in this room.", "error")
        return redirect("/group-discussion")
    
    evaluation = GDRoomEvaluation.query.filter_by(
        room_id=room_id, user_id=user.id
    ).first()
    
    topic = GDTopic.query.get(room.topic_id)
    all_participants = room.get_active_participants()
    messages = GDMessage.query.filter_by(
        room_id=room_id
    ).order_by(GDMessage.created_at.asc()).all()
    
    return render_template("gd_room_results.html", 
                         user=user,
                         room=room,
                         topic=topic,
                         evaluation=evaluation,
                         participant=participant,
                         all_participants=all_participants,
                         messages=messages)

@app.route("/leave-room", methods=["POST"])
def leave_room():
    """Leave a room (participants only, not host)"""
    if "user" not in session:
        return jsonify({"success": False, "error": "Not authenticated"})
    
    user = User.query.get(session["user"])
    room_id = request.json.get('room_id')
    
    room = GDRoom.query.filter_by(room_id=room_id).first()
    if not room:
        return jsonify({"success": False, "error": "Room not found"})
    
    if room.host_id == user.id:
        return jsonify({
            "success": False, 
            "error": "Host cannot leave room. End the session instead."
        })
    
    participant = GDRoomParticipant.query.filter_by(
        room_id=room_id, user_id=user.id
    ).first()
    
    if not participant:
        return jsonify({"success": False, "error": "You are not in this room"})
    
    participant.status = 'left'
    participant.left_at = datetime.utcnow()
    db.session.commit()
    
    return jsonify({
        "success": True,
        "message": "Left room successfully!",
        "redirect_url": "/group-discussion"
    })

@app.route("/gd-room-history")
def gd_room_history():
    """Display user's GD room history"""
    if "user" not in session:
        return redirect("/login")
    
    user = User.query.get(session["user"])
    
    # Get rooms where user was a participant
    participated_rooms = GDRoom.query.join(GDRoomParticipant).filter(
        GDRoomParticipant.user_id == user.id,
        GDRoom.status == 'completed'
    ).order_by(GDRoom.ended_at.desc()).all()
    
    # Get rooms where user was the host
    hosted_rooms = GDRoom.query.filter(
        GDRoom.host_id == user.id,
        GDRoom.status == 'completed'
    ).order_by(GDRoom.ended_at.desc()).all()
    
    return render_template("gd_history.html", 
                         user=user,
                         participated_rooms=participated_rooms,
                         hosted_rooms=hosted_rooms)


# ---------- GD ROOM POLLING API ----------
@app.route("/api/gd-room-poll/<room_id>")
def gd_room_poll(room_id):
    """Real-time polling endpoint for GD room updates"""
    if "user" not in session:
        return jsonify({"success": False, "error": "Not authenticated"})

    user = User.query.get(session["user"])
    room = GDRoom.query.filter_by(room_id=room_id).first()

    if not room:
        return jsonify({"success": False, "error": "Room not found"})

    # Check participant is in the room
    participant = GDRoomParticipant.query.filter_by(
        room_id=room_id, user_id=user.id
    ).first()

    if not participant:
        return jsonify({"success": False, "error": "Not a participant"})

    # Get the last known message id from the client
    last_msg_id = request.args.get("last_msg_id", 0, type=int)

    # New messages only
    new_messages = GDMessage.query.filter(
        GDMessage.room_id == room_id,
        GDMessage.id > last_msg_id
    ).order_by(GDMessage.created_at.asc()).all()

    messages_data = []
    for msg in new_messages:
        messages_data.append({
            "id": msg.id,
            "user_id": msg.user_id,
            "author": msg.user.name if msg.user else ("AI Participant" if msg.message_type == "ai_participant" else "AI Coach"),
            "content": msg.content,
            "message_type": msg.message_type,
            "time": msg.formatted_time(),
            "is_current_user": msg.user_id == user.id
        })

    # Get all active participants
    participants_data = []
    for p in room.participants:
        if p.status == 'active':
            participants_data.append({
                "user_id": p.user_id,
                "name": p.user.name,
                "role": p.role,
                "message_count": p.message_count,
                "turn_count": p.turn_count,
                "is_current_speaker": room.current_speaker == p.user_id
            })

    # Current user's own participant data
    my_participant = GDRoomParticipant.query.filter_by(
        room_id=room_id, user_id=user.id
    ).first()

    return jsonify({
        "success": True,
        "room_status": room.status,
        "current_speaker": room.current_speaker,
        "current_turn": room.current_turn,
        "is_my_turn": room.current_speaker == user.id,
        "turn_start_time": room.turn_start_time.isoformat() + "Z" if room.turn_start_time else None,
        "started_at": room.started_at.isoformat() + "Z" if room.started_at else None,
        "new_messages": messages_data,
        "participants": participants_data,
        "my_message_count": my_participant.message_count if my_participant else 0,
        "my_turn_count": my_participant.turn_count if my_participant else 0,
        "redirect_url": f"/gd-room-results/{room_id}" if room.status == 'completed' else None
    })




# ═══════════════════════════════════════════════════════════
#  SCHEDULING MODULE
# ═══════════════════════════════════════════════════════════

EVENT_TYPES = [
    ('mock_test',      'Mock Test',        'fa-pencil-alt',    '#3b82f6'),
    ('gd_session',     'GD Session',       'fa-comments',      '#8b5cf6'),
    ('interview',      'Interview Prep',   'fa-user-tie',      '#10b981'),
    ('resume_review',  'Resume Review',    'fa-file-alt',      '#f59e0b'),
    ('roadmap_task',   'Roadmap Task',     'fa-map-signs',     '#06b6d4'),
    ('custom',         'Custom Event',     'fa-calendar-check','#6b7280'),
]


@app.route("/schedule")
def schedule_page():
    if "user" not in session:
        return redirect("/login")

    user = User.query.get(session["user"])
    today = datetime.utcnow().date()
    today_str = today.strftime("%Y-%m-%d")

    # All schedules for this user
    all_schedules = Schedule.query.filter_by(user_id=user.id).order_by(Schedule.date, Schedule.time).all()

    # Auto-mark past 'scheduled' items as missed
    changed = False
    for s in all_schedules:
        if s.status == 'scheduled' and s.is_past():
            s.status = 'missed'
            changed = True
    if changed:
        db.session.commit()

    # Stats
    total   = len(all_schedules)
    upcoming_list = [s for s in all_schedules if s.status == 'scheduled']
    completed_count = sum(1 for s in all_schedules if s.status == 'completed')
    missed_count    = sum(1 for s in all_schedules if s.status == 'missed')
    today_list      = [s for s in all_schedules if s.date == today_str and s.status in ('scheduled', 'ongoing')]

    # Build calendar data: dict { "YYYY-MM-DD": [events] }
    calendar_data = {}
    for s in all_schedules:
        calendar_data.setdefault(s.date, []).append({
            "id": s.id,
            "title": s.title,
            "time": s.time,
            "event_type": s.event_type,
            "status": s.status,
            "color": s.event_color(),
            "icon": s.event_icon(),
            "priority": s.priority,
        })

    # Roadmaps for quick-link dropdown
    roadmaps = RoadmapHistory.query.filter_by(user_id=user.id).order_by(RoadmapHistory.created_at.desc()).limit(10).all()

    return render_template(
        "schedule.html",
        user=user,
        all_schedules=all_schedules,
        upcoming_list=upcoming_list,
        today_list=today_list,
        total=total,
        completed_count=completed_count,
        missed_count=missed_count,
        today_str=today_str,
        calendar_json=json.dumps(calendar_data),
        event_types=EVENT_TYPES,
        roadmaps=roadmaps,
    )


@app.route("/schedule/create", methods=["POST"])
def schedule_create():
    if "user" not in session:
        return jsonify({"success": False, "error": "Not logged in"}), 401

    data = request.get_json() or request.form.to_dict()
    title              = (data.get("title") or "").strip()
    event_type         = data.get("event_type", "custom")
    date_str           = data.get("date", "")
    time_str           = data.get("time", "")
    duration           = int(data.get("duration") or 60)
    priority           = data.get("priority", "medium")
    description        = (data.get("description") or "").strip()
    notes              = (data.get("notes") or "").strip()
    reminder_minutes   = int(data.get("reminder_minutes") or 30)
    linked_resource_id = data.get("linked_resource_id") or None
    if linked_resource_id:
        try:
            linked_resource_id = int(linked_resource_id)
        except Exception:
            linked_resource_id = None

    if not title or not date_str or not time_str:
        return jsonify({"success": False, "error": "Title, date and time are required"}), 400

    # Conflict detection: same user, same date+time
    conflict = Schedule.query.filter_by(
        user_id=session["user"], date=date_str, time=time_str
    ).filter(Schedule.status.notin_(['cancelled', 'missed'])).first()
    if conflict:
        return jsonify({"success": False, "error": f"You already have '{conflict.title}' at this time."}), 409

    sched = Schedule(
        user_id=session["user"],
        title=title,
        event_type=event_type,
        date=date_str,
        time=time_str,
        duration=duration,
        priority=priority,
        description=description,
        notes=notes,
        reminder_minutes=reminder_minutes,
        linked_resource_id=linked_resource_id,
    )
    db.session.add(sched)
    db.session.commit()

    return jsonify({"success": True, "id": sched.id, "message": "Event scheduled successfully!"})


@app.route("/schedule/update/<int:sched_id>", methods=["POST"])
def schedule_update(sched_id):
    if "user" not in session:
        return jsonify({"success": False, "error": "Not logged in"}), 401

    sched = Schedule.query.filter_by(id=sched_id, user_id=session["user"]).first()
    if not sched:
        return jsonify({"success": False, "error": "Event not found"}), 404

    data = request.get_json() or request.form.to_dict()
    if data.get("title"):        sched.title           = data["title"].strip()
    if data.get("event_type"):   sched.event_type      = data["event_type"]
    if data.get("date"):         sched.date            = data["date"]
    if data.get("time"):         sched.time            = data["time"]
    if data.get("duration"):     sched.duration        = int(data["duration"])
    if data.get("priority"):     sched.priority        = data["priority"]
    if data.get("description") is not None: sched.description = data["description"].strip()
    if data.get("notes") is not None:       sched.notes       = data["notes"].strip()
    if data.get("reminder_minutes"):        sched.reminder_minutes = int(data["reminder_minutes"])
    if data.get("status"):       sched.status          = data["status"]
    sched.updated_at = datetime.utcnow()

    db.session.commit()
    return jsonify({"success": True, "message": "Event updated successfully!"})


@app.route("/schedule/delete/<int:sched_id>", methods=["POST"])
def schedule_delete(sched_id):
    if "user" not in session:
        return jsonify({"success": False, "error": "Not logged in"}), 401

    sched = Schedule.query.filter_by(id=sched_id, user_id=session["user"]).first()
    if not sched:
        return jsonify({"success": False, "error": "Event not found"}), 404

    db.session.delete(sched)
    db.session.commit()
    return jsonify({"success": True, "message": "Event deleted."})


@app.route("/schedule/status/<int:sched_id>", methods=["POST"])
def schedule_status(sched_id):
    if "user" not in session:
        return jsonify({"success": False, "error": "Not logged in"}), 401

    sched = Schedule.query.filter_by(id=sched_id, user_id=session["user"]).first()
    if not sched:
        return jsonify({"success": False, "error": "Event not found"}), 404

    new_status = (request.get_json() or {}).get("status", "completed")
    sched.status = new_status
    sched.updated_at = datetime.utcnow()
    db.session.commit()
    return jsonify({"success": True, "status": new_status})


@app.route("/schedule/events")
def schedule_events():
    """JSON API for calendar JS to fetch events."""
    if "user" not in session:
        return jsonify([])

    schedules = Schedule.query.filter_by(user_id=session["user"]).all()
    events = []
    for s in schedules:
        events.append({
            "id": s.id,
            "title": s.title,
            "date": s.date,
            "time": s.time,
            "duration": s.duration,
            "event_type": s.event_type,
            "status": s.status,
            "priority": s.priority,
            "description": s.description,
            "notes": s.notes,
            "color": s.event_color(),
            "icon": s.event_icon(),
            "reminder_minutes": s.reminder_minutes,
        })
    return jsonify(events)


@app.route("/schedule/upcoming")
def schedule_upcoming():
    """Dashboard widget API: next 5 upcoming events."""
    if "user" not in session:
        return jsonify([])

    today_str = datetime.utcnow().strftime("%Y-%m-%d")
    schedules = Schedule.query.filter_by(
        user_id=session["user"], status='scheduled'
    ).filter(Schedule.date >= today_str).order_by(Schedule.date, Schedule.time).limit(5).all()

    return jsonify([{
        "id": s.id,
        "title": s.title,
        "date": s.formatted_date(),
        "time": s.time,
        "event_type": s.event_type,
        "icon": s.event_icon(),
        "color": s.event_color(),
        "priority": s.priority,
    } for s in schedules])


# ═══════════════════════════════════════════════════════════════════
#  AI INTERVIEW CHATBOT ROUTES
# ═══════════════════════════════════════════════════════════════════

@app.route("/interview")
def interview_home():
    """Interview setup page – choose role & type."""
    if "user" not in session:
        return redirect("/login")
    user = User.query.get(session["user"])
    return render_template("interview_home.html", user=user)


@app.route("/interview/start", methods=["POST"])
def interview_start():
    """Create a new session and send the first AI message."""
    if "user" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    user = User.query.get(session["user"])
    job_role = request.form.get("job_role", "").strip()
    interview_type = request.form.get("interview_type", "mixed")
    total_q = int(request.form.get("total_questions", 10))

    if not job_role:
        flash("Please enter a job role.", "error")
        return redirect("/interview")

    # Create session record
    iv_session = InterviewSession(
        user_id=user.id,
        job_role=job_role,
        interview_type=interview_type,
        total_questions=total_q,
        status="active",
        current_stage="introduction",
        question_count=0
    )
    db.session.add(iv_session)
    db.session.commit()

    # Generate opening message
    result = start_interview(
        job_role=job_role,
        interview_type=interview_type,
        user_name=user.name,
        user_skills=user.skills or "",
        career_goal=user.career_goal or ""
    )

    ai_msg = InterviewMessage(
        session_id=iv_session.id,
        role="ai",
        content=result["message"],
        stage="introduction",
        turn_number=1
    )
    db.session.add(ai_msg)
    iv_session.question_count = 1
    db.session.commit()

    return redirect(f"/interview/session/{iv_session.id}")


@app.route("/interview/session/<int:session_id>")
def interview_session(session_id):
    """Chat interface for an ongoing interview."""
    if "user" not in session:
        return redirect("/login")
    user = User.query.get(session["user"])
    iv_session = InterviewSession.query.get_or_404(session_id)
    if iv_session.user_id != user.id:
        return redirect("/interview")
    if iv_session.status == "completed":
        return redirect(f"/interview/result/{session_id}")
    messages = iv_session.messages
    return render_template("interview_chat.html",
                           user=user,
                           iv_session=iv_session,
                           messages=messages)


@app.route("/interview/message", methods=["POST"])
def interview_message():
    """AJAX endpoint: receive user answer, evaluate, return next AI turn."""
    if "user" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json(force=True) or {}
    session_id = data.get("session_id")
    user_text = (data.get("message") or "").strip()

    if not session_id or not user_text:
        return jsonify({"error": "Missing data"}), 400

    user = User.query.get(session["user"])
    iv_session = InterviewSession.query.get_or_404(session_id)
    if iv_session.user_id != user.id or iv_session.status != "active":
        return jsonify({"error": "Session not active"}), 400

    # Persist user message
    turn_no = len(iv_session.messages) + 1
    user_msg = InterviewMessage(
        session_id=iv_session.id,
        role="user",
        content=user_text,
        stage=iv_session.current_stage,
        turn_number=turn_no
    )
    db.session.add(user_msg)
    db.session.commit()

    # Build history list for AI
    history = [{"role": m.role, "content": m.content, "stage": m.stage}
               for m in iv_session.messages]

    # Get next AI turn
    result = interview_next_turn(
        job_role=iv_session.job_role,
        interview_type=iv_session.interview_type,
        messages=history,
        current_stage=iv_session.current_stage,
        question_count=iv_session.question_count,
        total_questions=iv_session.total_questions
    )

    # Update user message with evaluation scores
    user_msg.answer_score = float(result.get("answer_score", 6.0))
    user_msg.answer_feedback = result.get("answer_feedback", "")

    # Persist AI response message
    ai_msg = InterviewMessage(
        session_id=iv_session.id,
        role="ai",
        content=result["ai_message"],
        stage=result.get("new_stage", iv_session.current_stage),
        turn_number=turn_no + 1
    )
    db.session.add(ai_msg)

    # Advance session state
    iv_session.current_stage = result.get("new_stage", iv_session.current_stage)
    iv_session.question_count += 1

    is_final = result.get("is_final", False)
    if is_final:
        iv_session.status = "completed"
        iv_session.completed_at = datetime.utcnow()

    db.session.commit()

    # Generate comprehensive report when interview ends
    if is_final:
        full_history = [{"role": m.role, "content": m.content}
                        for m in iv_session.messages]
        report = generate_interview_report(
            job_role=iv_session.job_role,
            interview_type=iv_session.interview_type,
            messages=full_history,
            user_name=user.name
        )
        iv_session.overall_score = float(report.get("overall_score", 60))
        iv_session.technical_score = float(report.get("technical_score", 60))
        iv_session.communication_score = float(report.get("communication_score", 60))
        iv_session.confidence_score = float(report.get("confidence_score", 60))
        iv_session.final_report = json.dumps(report)
        db.session.commit()

    return jsonify({
        "ai_message": result["ai_message"],
        "answer_score": user_msg.answer_score,
        "answer_feedback": user_msg.answer_feedback,
        "is_final": is_final,
        "stage": iv_session.current_stage,
        "progress": iv_session.progress_pct()
    })


@app.route("/interview/result/<int:session_id>")
def interview_result(session_id):
    """Final performance report page."""
    if "user" not in session:
        return redirect("/login")
    user = User.query.get(session["user"])
    iv_session = InterviewSession.query.get_or_404(session_id)
    if iv_session.user_id != user.id:
        return redirect("/interview")

    report = {}
    if iv_session.final_report:
        try:
            report = json.loads(iv_session.final_report)
        except Exception:
            report = {}

    return render_template("interview_result.html",
                           user=user,
                           iv_session=iv_session,
                           report=report)


@app.route("/interview/history")
def interview_history():
    """List of past interview sessions."""
    if "user" not in session:
        return redirect("/login")
    user = User.query.get(session["user"])
    sessions = (InterviewSession.query
                .filter_by(user_id=user.id)
                .order_by(InterviewSession.created_at.desc())
                .all())
    return render_template("interview_history.html", user=user, sessions=sessions)


@app.route("/interview/abandon/<int:session_id>", methods=["POST"])
def interview_abandon(session_id):
    """Mark a session as abandoned."""
    if "user" not in session:
        return jsonify({"error": "Unauthorized"}), 401
    user = User.query.get(session["user"])
    iv_session = InterviewSession.query.get_or_404(session_id)
    if iv_session.user_id == user.id and iv_session.status == "active":
        iv_session.status = "abandoned"
        iv_session.completed_at = datetime.utcnow()
        db.session.commit()
    return jsonify({"success": True})


# ─────────────────────────────────────────────────────────────────
#  JOB SUGGESTIONS MODULE
# ─────────────────────────────────────────────────────────────────

@app.route("/job-suggestions")
def job_suggestions():
    """Main job suggestions page – shows AI-generated jobs based on profile & performance."""
    if "user" not in session:
        return redirect("/login")

    user = User.query.get(session["user"])
    if not user:
        return redirect("/login")

    # Pull performance stats
    total_tests = TestResult.query.filter_by(user_id=user.id).count()
    avg_test_score = db.session.query(
        func.avg(TestResult.score * 100.0 / TestResult.total_questions)
    ).filter_by(user_id=user.id).scalar() or 0.0
    total_roadmaps = RoadmapHistory.query.filter_by(user_id=user.id).count()

    search_query = request.args.get("q", "").strip()

    try:
        jobs = generate_job_suggestions(
            skills=user.skills or "",
            career_goal=user.career_goal or "",
            branch=user.branch or "",
            avg_test_score=round(float(avg_test_score), 1),
            total_tests=total_tests,
            total_roadmaps=total_roadmaps,
            search_query=search_query,
            num_suggestions=9
        )
    except Exception as e:
        print(f"[JOB SUGGESTIONS] Route error: {e}")
        jobs = []

    return render_template(
        "job_suggestions.html",
        user=user,
        jobs=jobs,
        search_query=search_query,
        avg_test_score=round(float(avg_test_score), 1),
        total_tests=total_tests
    )


@app.route("/job-suggestions/detail/<int:job_id>")
def job_detail(job_id):
    """
    Detail page for a single job.
    We regenerate the same job list and pick the matching id so we don't
    need a database table for ephemeral AI-generated suggestions.
    """
    if "user" not in session:
        return redirect("/login")

    user = User.query.get(session["user"])
    if not user:
        return redirect("/login")

    total_tests = TestResult.query.filter_by(user_id=user.id).count()
    avg_test_score = db.session.query(
        func.avg(TestResult.score * 100.0 / TestResult.total_questions)
    ).filter_by(user_id=user.id).scalar() or 0.0
    total_roadmaps = RoadmapHistory.query.filter_by(user_id=user.id).count()
    search_query = request.args.get("q", "").strip()

    try:
        jobs = generate_job_suggestions(
            skills=user.skills or "",
            career_goal=user.career_goal or "",
            branch=user.branch or "",
            avg_test_score=round(float(avg_test_score), 1),
            total_tests=total_tests,
            total_roadmaps=total_roadmaps,
            search_query=search_query,
            num_suggestions=9
        )
    except Exception as e:
        print(f"[JOB DETAIL] Error: {e}")
        jobs = []

    job = next((j for j in jobs if j.get("id") == job_id), None)
    if not job and jobs:
        job = jobs[0]
    if not job:
        return redirect("/job-suggestions")

    return render_template(
        "job_detail.html",
        user=user,
        job=job,
        all_jobs=jobs,
        search_query=search_query
    )


@app.route("/job-suggestions/refresh", methods=["POST"])
def job_suggestions_refresh():
    """AJAX endpoint – returns fresh job suggestions as JSON."""
    if "user" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    user = User.query.get(session["user"])
    total_tests = TestResult.query.filter_by(user_id=user.id).count()
    avg_test_score = db.session.query(
        func.avg(TestResult.score * 100.0 / TestResult.total_questions)
    ).filter_by(user_id=user.id).scalar() or 0.0
    total_roadmaps = RoadmapHistory.query.filter_by(user_id=user.id).count()
    search_query = request.json.get("q", "") if request.is_json else ""

    try:
        jobs = generate_job_suggestions(
            skills=user.skills or "",
            career_goal=user.career_goal or "",
            branch=user.branch or "",
            avg_test_score=round(float(avg_test_score), 1),
            total_tests=total_tests,
            total_roadmaps=total_roadmaps,
            search_query=search_query,
            num_suggestions=9
        )
        return jsonify({"jobs": jobs, "success": True})
    except Exception as e:
        return jsonify({"error": str(e), "success": False}), 500


# ============================
# AI ASSISTANT ROUTES
# ============================

def get_user_context_data(user_id):
    """Helper function to gather all user context data for AI Assistant"""
    user = User.query.get(user_id)
    if not user:
        return {}
    
    # Basic profile
    context = {
        'name': user.name or 'Student',
        'email': user.email,
        'branch': user.branch or 'Not specified',
        'year': user.year or 'Not specified',
        'skills': user.skills or 'Not specified',
        'career_goal': user.career_goal or 'Not specified',
        'weakness': user.weakness or ''
    }
    
    # Performance data
    total_tests = TestResult.query.filter_by(user_id=user_id).count()
    avg_test_score = db.session.query(
        func.avg(TestResult.score * 100.0 / TestResult.total_questions)
    ).filter_by(user_id=user_id).scalar() or 0
    
    completed_interviews = InterviewSession.query.filter_by(
        user_id=user_id, status='completed'
    ).count()
    avg_interview_score = db.session.query(
        func.avg(InterviewSession.overall_score)
    ).filter(
        InterviewSession.user_id == user_id,
        InterviewSession.status == 'completed'
    ).scalar() or 0
    
    total_gd = GDRoomParticipant.query.filter_by(user_id=user_id).count()
    avg_gd_score = db.session.query(
        func.avg(GDRoomEvaluation.overall_score)
    ).filter_by(user_id=user_id).scalar() or 0
    
    total_resumes = Resume.query.filter_by(user_id=user_id).count()
    avg_resume_score = db.session.query(
        func.avg(ResumeValidation.overall_score)
    ).filter_by(user_id=user_id).scalar() or 0
    
    total_roadmaps = RoadmapHistory.query.filter_by(user_id=user_id).count()
    
    context['performance'] = {
        'total_tests': total_tests,
        'avg_test_score': float(avg_test_score),
        'completed_interviews': completed_interviews,
        'avg_interview_score': float(avg_interview_score),
        'total_gd_sessions': total_gd,
        'avg_gd_score': float(avg_gd_score),
        'total_resumes': total_resumes,
        'avg_resume_score': float(avg_resume_score),
        'total_roadmaps': total_roadmaps
    }
    
    return context


@app.route("/assistant")
def assistant():
    """AI Assistant main page"""
    if "user" not in session:
        return redirect("/login")
    
    user_id = session["user"]
    user = User.query.get(user_id)
    
    # Get user context for suggestions
    user_context = get_user_context_data(user_id)
    
    # Generate smart suggestions
    suggestions = generate_smart_suggestions(user_context)
    
    # Generate performance insight
    insight = generate_performance_insight(user_context)
    
    # Get recent chat history (last 50 messages)
    recent_chats = AIAssistantChat.query.filter_by(
        user_id=user_id
    ).order_by(AIAssistantChat.created_at.desc()).limit(50).all()
    
    recent_chats.reverse()  # Chronological order
    
    return render_template(
        "ai_assistant.html",
        user=user,
        suggestions=suggestions,
        insight=insight,
        chat_history=recent_chats
    )


@app.route("/assistant/chat", methods=["POST"])
def assistant_chat():
    """Handle AI Assistant chat messages"""
    if "user" not in session:
        return jsonify({"error": "Unauthorized"}), 401
    
    user_id = session["user"]
    data = request.json
    user_message = data.get('message', '').strip()
    mode = data.get('mode', 'general')
    
    if not user_message:
        return jsonify({"error": "Empty message"}), 400
    
    try:
        # Get user context
        user_context = get_user_context_data(user_id)
        
        # Auto-detect mode if in general mode
        if mode == 'general':
            detected_mode = detect_intent_and_mode(user_message)
            mode = detected_mode
        
        # Get recent chat history for context
        recent_chats = AIAssistantChat.query.filter_by(
            user_id=user_id
        ).order_by(AIAssistantChat.created_at.desc()).limit(10).all()
        
        recent_chats.reverse()
        chat_history = [{'role': chat.role, 'message': chat.message} for chat in recent_chats]
        
        # Save user message
        user_chat = AIAssistantChat(
            user_id=user_id,
            role='user',
            message=user_message,
            mode=mode,
            context_data=json.dumps(user_context.get('performance', {}))
        )
        db.session.add(user_chat)
        db.session.commit()
        
        # Generate AI response
        ai_response = intelligent_assistant_chat(
            user_message=user_message,
            user_context=user_context,
            mode=mode,
            chat_history=chat_history
        )
        
        # Save AI response
        ai_chat = AIAssistantChat(
            user_id=user_id,
            role='assistant',
            message=ai_response,
            mode=mode
        )
        db.session.add(ai_chat)
        db.session.commit()
        
        return jsonify({
            "success": True,
            "response": ai_response,
            "mode": mode,
            "timestamp": ai_chat.created_at.isoformat()
        })
    
    except Exception as e:
        print(f"Assistant chat error: {e}")
        return jsonify({"error": "Failed to process message"}), 500


@app.route("/assistant/clear", methods=["POST"])
def assistant_clear():
    """Clear chat history"""
    if "user" not in session:
        return jsonify({"error": "Unauthorized"}), 401
    
    user_id = session["user"]
    
    try:
        AIAssistantChat.query.filter_by(user_id=user_id).delete()
        db.session.commit()
        return jsonify({"success": True})
    except Exception as e:
        print(f"Clear chat error: {e}")
        return jsonify({"error": "Failed to clear chat"}), 500


@app.route("/assistant/mode", methods=["POST"])
def assistant_change_mode():
    """Change assistant mode and get new suggestions"""
    if "user" not in session:
        return jsonify({"error": "Unauthorized"}), 401
    
    user_id = session["user"]
    data = request.json
    mode = data.get('mode', 'general')
    
    # Get user context
    user_context = get_user_context_data(user_id)
    
    # Generate mode-specific welcome message
    if mode == 'career':
        welcome = "🎯 Career Mode activated! Ask me about roadmaps, skill development, and career planning."
    elif mode == 'interview':
        welcome = "💼 Interview Mode activated! Let's prepare you for interviews and improve your performance."
    elif mode == 'resume':
        welcome = "📄 Resume Mode activated! I'll help you create and optimize your professional resume."
    elif mode == 'skill':
        welcome = "📚 Skill Mode activated! Let's identify gaps and create your learning path."
    elif mode == 'job':
        welcome = "🏢 Job Mode activated! I'll help you find and apply for suitable opportunities."
    else:
        welcome = "👋 General Mode activated! Ask me anything about your career development."
    
    return jsonify({
        "success": True,
        "mode": mode,
        "welcome": welcome
    })


if __name__ == "__main__":
    app.run(debug=True)

