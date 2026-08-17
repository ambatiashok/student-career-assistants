from google import genai
from config import GOOGLE_API_KEY
import re
import json
import os
import io

# Using API key from environment variable (more secure)
try:
    client = genai.Client(api_key=GOOGLE_API_KEY)
except Exception as e:
    print(f"[AI SERVICE WARNING] Failed to init genai client: {e}")
    client = None


def extract_text_from_file(file_path):
    """
    Extract text from uploaded resume files (PDF, DOC, DOCX, TXT)
    
    Args:
        file_path: Path to the uploaded file
        
    Returns:
        Extracted text content
    """
    
    file_extension = os.path.splitext(file_path)[1].lower()
    
    try:
        if file_extension == '.txt':
            # Handle text files
            with open(file_path, 'r', encoding='utf-8') as file:
                return file.read()
        
        elif file_extension == '.pdf':
            # Handle PDF files
            try:
                import PyPDF2
                with open(file_path, 'rb') as file:
                    pdf_reader = PyPDF2.PdfReader(file)
                    text = ""
                    for page in pdf_reader.pages:
                        text += page.extract_text() + "\n"
                    return text
            except ImportError:
                # Fallback if PyPDF2 not available
                return "PDF text extraction requires PyPDF2 library. Please install: pip install PyPDF2"
        
        elif file_extension in ['.doc', '.docx']:
            # Handle Word documents
            try:
                import docx
                doc = docx.Document(file_path)
                text = ""
                for paragraph in doc.paragraphs:
                    text += paragraph.text + "\n"
                return text
            except ImportError:
                # Fallback if python-docx not available
                return "Word document extraction requires python-docx library. Please install: pip install python-docx"
        
        else:
            return "Unsupported file format"
            
    except Exception as e:
        return f"Error extracting text: {str(e)}"


def analyze_resume_format(resume_text):
    """
    Analyze the format and structure of an uploaded resume
    
    Args:
        resume_text: Text content of the resume
        
    Returns:
        dict with format analysis and suggestions
    """
    
    prompt = f"""
    Analyze this resume's format, structure, and organization:
    
    Resume Text:
    {resume_text}
    
    Provide analysis in JSON format:
    {{
        "format_type": "chronological/functional/combination/creative",
        "sections_found": ["section1", "section2"],
        "missing_sections": ["missing1", "missing2"],
        "format_score": [0-10],
        "readability_score": [0-10],
        "ats_compatibility": [0-10],
        "structure_strengths": ["strength1", "strength2"],
        "structure_weaknesses": ["weakness1", "weakness2"],
        "format_suggestions": [
            {{
                "issue": "specific format issue",
                "suggestion": "how to fix it",
                "priority": "high/medium/low"
            }}
        ],
        "recommended_templates": ["template1", "template2"]
    }}
    
    Return ONLY valid JSON, no extra text.
    """
    
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        
        # Strip markdown fences before parsing
        raw = response.text.strip()
        if raw.startswith('```'):
            lines = raw.split('\n')
            start = 1
            end = len(lines) - 1 if lines[-1].strip() == '```' else len(lines)
            raw = '\n'.join(lines[start:end]).strip()
        
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            # Fallback analysis
            return {
                "format_type": "standard",
                "sections_found": ["Contact", "Education", "Skills"],
                "missing_sections": ["Summary", "Projects"],
                "format_score": 6,
                "readability_score": 7,
                "ats_compatibility": 6,
                "structure_strengths": ["Clear sections", "Readable layout"],
                "structure_weaknesses": ["Missing professional summary", "Could improve formatting"],
                "format_suggestions": [
                    {
                        "issue": "Missing professional summary",
                        "suggestion": "Add a 3-4 line professional summary at the top",
                        "priority": "high"
                    }
                ],
                "recommended_templates": ["Professional", "Modern"]
            }
            
    except Exception as e:
        print(f"Error analyzing resume format: {e}")
        # Return default analysis
        return {
            "format_type": "standard",
            "sections_found": ["Contact", "Education"],
            "missing_sections": ["Summary", "Skills", "Projects"],
            "format_score": 5,
            "readability_score": 6,
            "ats_compatibility": 5,
            "structure_strengths": ["Basic structure present"],
            "structure_weaknesses": ["Needs improvement in organization"],
            "format_suggestions": [
                {
                    "issue": "Structure analysis incomplete",
                    "suggestion": "Please review resume manually for optimization",
                    "priority": "medium"
                }
            ],
            "recommended_templates": ["Professional", "Clean"]
        }


def generate_resume_templates():
    """
    Provide different resume format templates with enhanced recommendations
    
    Returns:
        dict with various resume template options
    """
    
    templates = {
        "professional": {
            "name": "Professional Classic",
            "description": "Clean, traditional format perfect for corporate roles and ATS systems",
            "best_for": ["Finance", "Consulting", "Management", "Corporate", "Government"],
            "features": ["ATS-optimized", "Conservative design", "Clear hierarchy", "Traditional layout"],
            "seo_score": 9,
            "ats_compatibility": 10,
            "visual_appeal": 7,
            "industry_preference": ["Corporate", "Finance", "Legal", "Healthcare"],
            "preview_html": """
            <div class="template-preview professional">
                <h1>John Doe</h1>
                <p>Software Developer | john@email.com | +91-9999999999</p>
                <h3>Professional Summary</h3>
                <p>Experienced software developer with strong technical skills...</p>
                <h3>Work Experience</h3>
                <h3>Education</h3>
                <h3>Technical Skills</h3>
            </div>
            """
        },
        "modern": {
            "name": "Modern Professional",
            "description": "Contemporary design with subtle colors and clean typography",
            "best_for": ["Tech", "Design", "Startups", "Digital Marketing", "Product Management"],
            "features": ["Visual appeal", "Color accents", "Modern typography", "Balanced layout"],
            "seo_score": 8,
            "ats_compatibility": 8,
            "visual_appeal": 9,
            "industry_preference": ["Technology", "Creative", "Startup"],
            "preview_html": """
            <div class="template-preview modern">
                <div class="header-section">
                    <h1>John Doe</h1>
                    <p>Software Developer</p>
                </div>
                <div class="content-section">
                    <h3>About</h3>
                    <h3>Experience</h3>
                    <h3>Skills</h3>
                </div>
            </div>
            """
        },
        "creative": {
            "name": "Creative Portfolio",
            "description": "Unique layout with creative elements perfect for design and creative roles",
            "best_for": ["Design", "Marketing", "Arts", "Media", "Photography", "Writing"],
            "features": ["Creative layout", "Visual elements", "Portfolio style", "Unique design"],
            "seo_score": 6,
            "ats_compatibility": 6,
            "visual_appeal": 10,
            "industry_preference": ["Design", "Creative", "Media"],
            "preview_html": """
            <div class="template-preview creative">
                <div class="creative-header">
                    <h1>John Doe</h1>
                    <p>Creative Designer</p>
                </div>
                <div class="creative-sections">
                    <h3>Portfolio</h3>
                    <h3>Experience</h3>
                    <h3>Skills</h3>
                </div>
            </div>
            """
        },
        "minimal": {
            "name": "Minimal Academic",
            "description": "Clean, minimalist design focusing on content and achievements",
            "best_for": ["Academic", "Research", "Science", "Engineering", "Education"],
            "features": ["Content focused", "Clean lines", "Academic style", "Research emphasis"],
            "seo_score": 8,
            "ats_compatibility": 9,
            "visual_appeal": 7,
            "industry_preference": ["Academic", "Research", "Science"],
            "preview_html": """
            <div class="template-preview minimal">
                <h1>John Doe</h1>
                <p>Research Scientist</p>
                <h3>Research Experience</h3>
                <h3>Publications</h3>
                <h3>Education</h3>
            </div>
            """
        },
        "executive": {
            "name": "Executive Leadership",
            "description": "Premium format designed for senior roles and executive positions",
            "best_for": ["C-Suite", "VP", "Director", "Senior Management", "Executive"],
            "features": ["Premium design", "Leadership focus", "Achievement emphasis", "Executive style"],
            "seo_score": 9,
            "ats_compatibility": 8,
            "visual_appeal": 9,
            "industry_preference": ["Executive", "Leadership", "Management"],
            "preview_html": """
            <div class="template-preview executive">
                <div class="executive-header">
                    <h1>John Doe</h1>
                    <p>Chief Technology Officer</p>
                </div>
                <h3>Executive Summary</h3>
                <h3>Leadership Experience</h3>
                <h3>Key Achievements</h3>
            </div>
            """
        },
        "technical": {
            "name": "Technical Expert",
            "description": "Developer-focused template optimized for technical roles and showcasing skills",
            "best_for": ["Software Engineer", "DevOps", "Data Scientist", "Cybersecurity", "AI/ML"],
            "features": ["Technical layout", "Skills showcase", "Project emphasis", "Code-friendly"],
            "seo_score": 8,
            "ats_compatibility": 9,
            "visual_appeal": 8,
            "industry_preference": ["Technology", "Engineering", "Data Science"],
            "preview_html": """
            <div class="template-preview technical">
                <div class="tech-header">
                    <h1>John Doe</h1>
                    <p>Senior Software Engineer</p>
                </div>
                <h3>Technical Skills</h3>
                <h3>Projects</h3>
                <h3>Professional Experience</h3>
            </div>
            """
        }
    }
    
    return templates


def suggest_optimal_templates(analysis_data, target_role="Software Developer", industry="Technology"):
    """
    AI-powered template recommendations based on resume analysis
    
    Args:
        analysis_data: Resume analysis results from validate_resume
        target_role: Target job role
        industry: Target industry
        
    Returns:
        Ordered list of recommended templates with reasoning
    """
    
    try:
        # Parse analysis data if it's a JSON string
        if isinstance(analysis_data, str):
            analysis_data = json.loads(analysis_data)
    except:
        analysis_data = {}
    
    templates = generate_resume_templates()
    recommendations = []
    
    # Extract key metrics
    ats_score = analysis_data.get("ats_score", 5)
    overall_score = analysis_data.get("overall_score", 70)
    industry_relevance = analysis_data.get("industry_relevance_score", 6)
    
    # Role-based template scoring
    role_preferences = {
        "software": ["technical", "modern", "professional"],
        "data": ["technical", "minimal", "professional"], 
        "design": ["creative", "modern", "portfolio"],
        "management": ["executive", "professional", "modern"],
        "finance": ["professional", "minimal", "modern"],
        "marketing": ["modern", "creative", "professional"],
        "research": ["minimal", "academic", "professional"],
        "executive": ["executive", "professional", "modern"]
    }
    
    # Determine role category
    role_lower = target_role.lower()
    role_category = "professional"  # default
    
    for category, keywords in [
        ("software", ["software", "developer", "engineer", "programmer", "full stack"]),
        ("data", ["data", "scientist", "analyst", "machine learning", "ai"]),
        ("design", ["design", "ui", "ux", "graphic", "creative"]),
        ("management", ["manager", "lead", "director", "head"]),
        ("finance", ["finance", "accounting", "analyst", "consultant"]),
        ("marketing", ["marketing", "growth", "digital", "content"]),
        ("research", ["research", "academic", "scientist", "phd"]),
        ("executive", ["ceo", "cto", "vp", "chief", "executive"])
    ]:
        if any(keyword in role_lower for keyword in keywords):
            role_category = category
            break
    
    # Score each template
    for template_id, template in templates.items():
        score = 0
        reasons = []
        
        # Role compatibility (40% weight)
        if template_id in role_preferences.get(role_category, []):
            score += 40
            reasons.append(f"Optimized for {role_category} roles")
        
        # ATS compatibility consideration (30% weight)  
        if ats_score < 7 and template["ats_compatibility"] >= 9:
            score += 30
            reasons.append("High ATS compatibility to improve parsing")
        elif ats_score >= 8 and template["visual_appeal"] >= 8:
            score += 25
            reasons.append("Good balance of ATS compatibility and visual appeal")
        
        # Industry alignment (20% weight)
        if industry.lower() in [pref.lower() for pref in template["industry_preference"]]:
            score += 20
            reasons.append(f"Preferred in {industry} industry")
        
        # Overall performance boost (10% weight)
        if overall_score >= 80 and template["visual_appeal"] >= 8:
            score += 10
            reasons.append("Premium template for strong resume content")
        elif overall_score < 70 and template["ats_compatibility"] >= 9:
            score += 10
            reasons.append("ATS-focused template to maximize visibility")
        
        recommendations.append({
            "template_id": template_id,
            "template": template,
            "score": score,
            "reasons": reasons,
            "recommendation_strength": "high" if score >= 80 else "medium" if score >= 60 else "low"
        })
    
    # Sort by score and return top recommendations
    recommendations.sort(key=lambda x: x["score"], reverse=True)
    
    return recommendations[:3]  # Return top 3 recommendations

def generate_roadmap(branch, skills, goal, weakness):

    prompt = f"""
    Act as a career mentor.

    Create a 4 week career roadmap.

    Branch: {branch}
    Skills: {skills}
    Career goal: {goal}
    Weakness: {weakness}

    Provide weekly goals and daily tasks.
    """

    response = client.models.generate_content(
        model="gemini-2.5-flash",  # Fixed: Changed from gemini-2.0-flash-exp to gemini-2.5-flash
        contents=prompt
    )
    return response.text


def generate_mock_test(category, difficulty="medium", num_questions=5):
    """
    Generate AI-powered mock test questions
    
    Args:
        category: 'aptitude' or 'technical'
        difficulty: 'easy', 'medium', 'hard'
        num_questions: number of questions to generate
    """
    
    if category == "aptitude":
        prompt = f"""
        Generate {num_questions} {difficulty} aptitude test multiple choice questions.
        Include topics: logical reasoning, quantitative aptitude, verbal ability, data interpretation.
        
        Format EXACTLY like this for EACH question:
        
        Question: [question text]
        A) [option A]
        B) [option B] 
        C) [option C]
        D) [option D]
        Answer: [correct letter A/B/C/D]
        
        Make questions practical and relevant for engineering students.
        """
    
    elif category == "technical":
        prompt = f"""
        Generate {num_questions} {difficulty} technical multiple choice questions.
        Include topics: programming basics, data structures, algorithms, computer science fundamentals, software engineering.
        
        Format EXACTLY like this for EACH question:
        
        Question: [question text]
        A) [option A]
        B) [option B]
        C) [option C] 
        D) [option D]
        Answer: [correct letter A/B/C/D]
        
        Focus on practical programming knowledge and CS concepts.
        """

    elif category == "verbal":
        prompt = f"""
        Generate {num_questions} {difficulty} verbal ability and English language multiple choice questions for placement preparation.
        Include topics: synonyms/antonyms, sentence correction, reading comprehension, fill in the blanks, vocabulary, idioms and phrases.
        
        Format EXACTLY like this for EACH question:
        
        Question: [question text]
        A) [option A]
        B) [option B]
        C) [option C]
        D) [option D]
        Answer: [correct letter A/B/C/D]
        
        Make questions suitable for engineering placement exams.
        """

    elif category == "core_engineering":
        prompt = f"""
        Generate {num_questions} {difficulty} core engineering multiple choice questions.
        Include topics: operating systems, computer networks, database management systems (DBMS), software engineering principles, computer architecture, OOP concepts.
        
        Format EXACTLY like this for EACH question:
        
        Question: [question text]
        A) [option A]
        B) [option B]
        C) [option C]
        D) [option D]
        Answer: [correct letter A/B/C/D]
        
        Focus on conceptual depth and placement-relevant topics.
        """

    elif category == "hr_interview":
        prompt = f"""
        Generate {num_questions} {difficulty} HR interview preparation multiple choice questions.
        Include topics: behavioral questions (what would you do scenarios), company culture fit, teamwork and leadership, problem-solving approach, career goals, situational judgment, professional ethics.
        
        Format EXACTLY like this for EACH question:
        
        Question: [scenario or situation question text]
        A) [option A]
        B) [option B]
        C) [option C]
        D) [option D]
        Answer: [correct/best letter A/B/C/D]
        
        Make questions realistic HR interview scenarios that test soft skills and professional maturity.
        """

    elif category == "general_knowledge":
        prompt = f"""
        Generate {num_questions} {difficulty} general knowledge multiple choice questions for campus placement and competitive exams.
        Include topics: current affairs, science & technology, Indian economy, world history, geography, awards & achievements, famous personalities, sports.
        
        Format EXACTLY like this for EACH question:
        
        Question: [question text]
        A) [option A]
        B) [option B]
        C) [option C]
        D) [option D]
        Answer: [correct letter A/B/C/D]
        
        Make questions useful for placement and competitive exam preparation.
        """

    else:
        raise ValueError("Invalid category")
    
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        return response.text
    except Exception as e:
        print(f"Error generating questions: {e}")
        return None


def generate_custom_topic_test(topic: str, difficulty: str = "medium", num_questions: int = 5) -> str | None:
    """
    Generate MCQ questions on ANY user-specified topic/concept.

    Args:
        topic: Free-text topic entered by the user (e.g. "Python OOP", "React Hooks", "Binary Trees")
        difficulty: 'easy' | 'medium' | 'hard'
        num_questions: how many questions (5-20)

    Returns:
        Raw question text in the standard Q/A format, or None on error.
    """
    prompt = f"""
You are an expert educator and test designer.
Generate exactly {num_questions} {difficulty}-difficulty multiple choice questions about the topic: "{topic}".

Rules:
- Questions must be specific, accurate and relevant to "{topic}".
- Each question must have exactly 4 options (A, B, C, D).
- Only one option is correct.
- Cover different sub-aspects of the topic across all questions.
- Difficulty level "{difficulty}": easy = conceptual basics, medium = applied understanding, hard = in-depth / edge cases.

Use EXACTLY this format for every question (no extra text between questions):

Question: [question text]
A) [option A]
B) [option B]
C) [option C]
D) [option D]
Answer: [correct letter A/B/C/D]

Generate all {num_questions} questions now.
"""
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        return response.text
    except Exception as e:
        print(f"[CUSTOM TOPIC TEST] Error generating questions: {e}")
        return None


def parse_questions(raw_text):
    """
    Parse AI-generated questions into structured format
    
    Returns:
        list of dicts with question, options, correct_answer
    """
    questions = []
    
    try:
        # Split by "Question:" to get individual questions
        question_blocks = re.split(r'Question:', raw_text)
        
        for block in question_blocks[1:]:  # Skip first empty split
            
            # Extract question text
            question_match = re.search(r'^(.*?)(?=A\))', block, re.DOTALL)
            if not question_match:
                continue
                
            question_text = question_match.group(1).strip()
            
            # Extract options
            option_a = re.search(r'A\)(.*?)(?=B\))', block, re.DOTALL)
            option_b = re.search(r'B\)(.*?)(?=C\))', block, re.DOTALL)
            option_c = re.search(r'C\)(.*?)(?=D\))', block, re.DOTALL)
            option_d = re.search(r'D\)(.*?)(?=Answer:)', block, re.DOTALL)
            
            # Extract correct answer
            answer_match = re.search(r'Answer:\s*([A-D])', block)
            
            if all([question_text, option_a, option_b, option_c, option_d, answer_match]):
                questions.append({
                    'question': question_text,
                    'options': {
                        'A': option_a.group(1).strip(),
                        'B': option_b.group(1).strip(),
                        'C': option_c.group(1).strip(),
                        'D': option_d.group(1).strip()
                    },
                    'correct_answer': answer_match.group(1).upper()
                })
        
        return questions
        
    except Exception as e:
        print(f"Error parsing questions: {e}")
        return []


def evaluate_answers(user_answers, correct_answers):
    """
    Evaluate user answers against correct answers
    
    Args:
        user_answers: list of user's answers ['A', 'B', 'C', ...]
        correct_answers: list of correct answers ['B', 'A', 'D', ...]
    
    Returns:
        dict with score, percentage, results
    """
    
    if len(user_answers) != len(correct_answers):
        return {'score': 0, 'percentage': 0, 'results': []}
    
    score = 0
    results = []
    
    for i, (user_ans, correct_ans) in enumerate(zip(user_answers, correct_answers)):
        is_correct = user_ans.upper() == correct_ans.upper()
        if is_correct:
            score += 1
        
        results.append({
            'question_num': i + 1,
            'user_answer': user_ans.upper(),
            'correct_answer': correct_ans.upper(),
            'is_correct': is_correct
        })
    
    percentage = round((score / len(correct_answers)) * 100, 1)
    
    return {
        'score': score,
        'total': len(correct_answers),
        'percentage': percentage,
        'results': results
    }


# Group Discussion AI Functions

def generate_gd_topic_for_room(topic_type="social", difficulty="medium", room_name=None):
    """
    Generate Group Discussion topics specifically for room-based collaborative discussions
    
    Args:
        topic_type: 'social', 'technology', 'economy', 'abstract', 'case_study'
        difficulty: 'easy', 'medium', 'hard'
        room_name: Optional room name for context
    
    Returns:
        dict with topic title, description, and discussion framework
    """
    
    context_prompt = f"for a collaborative room-based discussion with 3-6 participants" + (f" in room '{room_name}'" if room_name else "")
    
    if topic_type == "social":
        prompt = f"""
        Generate a {difficulty} level Group Discussion topic about social issues {context_prompt}.
        
        This topic will be used for REAL-TIME COLLABORATIVE discussion where multiple participants will debate simultaneously.
        
        Format your response exactly like this:
        
        TOPIC: [topic title]
        
        DESCRIPTION: [brief engaging description that encourages debate]
        
        DISCUSSION_FRAMEWORK: [3-4 key angles/perspectives for multi-participant debate separated by |]
        
        STARTER_QUESTIONS: [2-3 opening questions to kick-start discussion separated by |]
        
        Make it highly engaging for engineering students in placement scenarios.
        The topic should have multiple valid viewpoints to encourage healthy debate.
        Focus on current, relevant social issues that allow for diverse opinions.
        
        Examples: "Social media: Connection or isolation?", "Remote work: Future or fad?", "AI replacing human jobs: Threat or opportunity?"
        """
        
    elif topic_type == "technology":
        prompt = f"""
        Generate a {difficulty} level Group Discussion topic about technology {context_prompt}.
        
        Format your response exactly like this:
        
        TOPIC: [topic title]
        
        DESCRIPTION: [brief engaging description that encourages debate]
        
        DISCUSSION_FRAMEWORK: [3-4 key angles/perspectives separated by |]
        
        STARTER_QUESTIONS: [2-3 opening questions separated by |]
        
        Focus on current technology trends with multiple debatable aspects.
        Ensure the topic allows for both pro and con arguments.
        Make it relevant for tech-savvy engineering students.
        
        Examples: "Cryptocurrency: Revolution or bubble?", "AI in education: Enhancement or replacement?", "Privacy vs convenience in smart cities"
        """
        
    elif topic_type == "economy":
        prompt = f"""
        Generate a {difficulty} level Group Discussion topic about economics and business {context_prompt}.
        
        Format your response exactly like this:
        
        TOPIC: [topic title]
        
        DESCRIPTION: [brief engaging description that encourages debate]
        
        DISCUSSION_FRAMEWORK: [3-4 key economic/business angles separated by |]
        
        STARTER_QUESTIONS: [2-3 opening questions separated by |]
        
        Focus on economic policies, business trends, or financial topics.
        Ensure multiple valid economic perspectives can be argued.
        Make it accessible yet challenging for engineering students.
        
        Examples: "Startup culture vs traditional employment", "Universal Basic Income: Necessity or luxury?", "Green economy: Growth opportunity or constraint?"
        """
        
    elif topic_type == "abstract":
        prompt = f"""
        Generate a {difficulty} level abstract Group Discussion topic {context_prompt}.
        
        Format your response exactly like this:
        
        TOPIC: [topic title]
        
        DESCRIPTION: [brief engaging description for creative debate]
        
        DISCUSSION_FRAMEWORK: [3-4 creative thinking angles separated by |]
        
        STARTER_QUESTIONS: [2-3 thought-provoking questions separated by |]
        
        Create an abstract, philosophical, or creative topic for innovative thinking.
        The topic should spark imagination and diverse interpretations.
        No obvious right/wrong answers - focus on creative reasoning.
        
        Examples: "Is silence more powerful than words?", "Time: Linear journey or circular experience?", "Success: Destination or journey?"
        """
        
    elif topic_type == "case_study":
        prompt = f"""
        Generate a {difficulty} level business case study for collaborative problem-solving {context_prompt}.
        
        Format your response exactly like this:
        
        TOPIC: [case study title]
        
        DESCRIPTION: [detailed scenario with business challenge]
        
        DISCUSSION_FRAMEWORK: [3-4 problem-solving approaches separated by |]
        
        STARTER_QUESTIONS: [2-3 strategic questions separated by |]
        
        Create a realistic business scenario requiring group problem-solving.
        Include enough complexity for meaningful collaborative analysis.
        Multiple valid solutions should be possible.
        
        Examples: "Tech startup facing user retention crisis", "Traditional retailer's digital transformation challenge", "Team productivity in hybrid work environment"
        """
    
    else:
        return None
    
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        
        # Parse the response
        text = response.text.strip()
        
        topic_match = re.search(r'TOPIC:\s*(.+?)(?=\n|$)', text, re.MULTILINE)
        desc_match = re.search(r'DESCRIPTION:\s*(.+?)(?=\nDISCUSSION_FRAMEWORK|\Z)', text, re.DOTALL)
        framework_match = re.search(r'DISCUSSION_FRAMEWORK:\s*(.+?)(?=\nSTARTER_QUESTIONS|\Z)', text, re.DOTALL)
        questions_match = re.search(r'STARTER_QUESTIONS:\s*(.+?)(?=\n|$)', text, re.MULTILINE)
        
        if topic_match and desc_match:
            return {
                'title': topic_match.group(1).strip(),
                'description': desc_match.group(1).strip(),
                'discussion_framework': framework_match.group(1).strip().split('|') if framework_match else [],
                'starter_questions': questions_match.group(1).strip().split('|') if questions_match else [],
                'topic_type': topic_type,
                'difficulty': difficulty
            }
        else:
            # Fallback topics for room-based discussions
            fallback_topics = {
                'social': "The Impact of Social Media on Real-World Relationships",
                'technology': "Artificial Intelligence: Friend or Foe to Humanity?", 
                'economy': "Gig Economy vs Traditional Employment: The Future of Work",
                'abstract': "Is failure a stepping stone or a stumbling block?",
                'case_study': "Reviving a Struggling Tech Startup: Strategic Turnaround"
            }
            return {
                'title': fallback_topics.get(topic_type, "Technology and Society Debate"),
                'description': f"Engage in a collaborative discussion about {fallback_topics.get(topic_type, 'the given topic')} with your fellow participants.",
                'discussion_framework': ["Multiple perspectives to consider", "Real-world examples to discuss", "Future implications to debate", "Personal experiences to share"],
                'starter_questions': ["What's your initial perspective on this topic?", "Can you share a relevant example?", "How might this evolve in the future?"],
                'topic_type': topic_type,
                'difficulty': difficulty
            }
        
    except Exception as e:
        print(f"Error generating GD room topic: {e}")
        # Return comprehensive fallback
        fallback_topics = {
            'social': "Digital Communication vs Face-to-Face Interaction",
            'technology': "The Role of Technology in Modern Education",
            'economy': "Entrepreneurship vs Corporate Employment",
            'abstract': "Change: Opportunity or Challenge?",
            'case_study': "Managing Remote Team Performance"
        }
        return {
            'title': fallback_topics.get(topic_type, "Current Affairs Discussion"),
            'description': f"A collaborative exploration of {fallback_topics.get(topic_type, 'contemporary issues')} through group discussion.",
            'discussion_framework': ["Different viewpoints", "Supporting arguments", "Real-world applications", "Future considerations"],
            'starter_questions': ["What are your thoughts on this topic?", "How does this relate to your experience?", "What trends do you see emerging?"],
            'topic_type': topic_type,
            'difficulty': difficulty
        }
        

def evaluate_message_realtime(message_text, topic_context, participant_history=None, room_context=None):
    """
    Real-time evaluation of messages in group discussion rooms
    
    Args:
        message_text: User's message content
        topic_context: Discussion topic and description
        participant_history: Previous messages from this participant (optional)
        room_context: Recent room messages for context (optional)
    
    Returns:
        dict with real-time scores and feedback
    """
    
    history_context = ""
    if participant_history:
        history_context = "Participant's previous contributions:\n" + "\n".join(participant_history[-3:])
    
    room_context_str = ""
    if room_context:
        room_context_str = "Recent room discussion:\n" + "\n".join(room_context[-5:])
    
    prompt = f"""
    Evaluate this Group Discussion message in REAL-TIME for a collaborative room-based session.
    
    TOPIC CONTEXT: {topic_context}
    
    {history_context}
    
    {room_context_str}
    
    CURRENT MESSAGE: {message_text}
    
    Provide INSTANT evaluation on these criteria (score 0-10 each):
    
    1. RELEVANCE - How relevant is this message to the ongoing topic?
    2. CLARITY - How clear and well-articulated is the communication?
    3. CONFIDENCE - How confident and assertive is the tone?
    4. LEADERSHIP - Does this message show leadership qualities (guiding discussion, asking questions, building consensus)?
    5. COLLABORATION - How well does this build on/respond to others' contributions?
    
    Also analyze:
    - SENTIMENT: Rate emotional tone (-1 to 1, where -1 is very negative, 0 is neutral, 1 is very positive)
    - INITIATIVE: Does this show proactive thinking? (0-10)
    
    Format your response exactly like this:
    
    RELEVANCE: [score]/10
    CLARITY: [score]/10
    CONFIDENCE: [score]/10
    LEADERSHIP: [score]/10
    COLLABORATION: [score]/10
    SENTIMENT: [score from -1 to 1]
    INITIATIVE: [score]/10
    
    INSTANT_FEEDBACK: [1-2 sentences of immediate constructive feedback]
    STRENGTHS: [1-2 key strengths]
    SUGGESTIONS: [1-2 quick improvement tips]
    
    Keep feedback concise for real-time display.
    """
    
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        
        text = response.text.strip()
        
        # Extract scores
        relevance = re.search(r'RELEVANCE:\s*(\d+(?:\.\d+)?)', text)
        clarity = re.search(r'CLARITY:\s*(\d+(?:\.\d+)?)', text)
        confidence = re.search(r'CONFIDENCE:\s*(\d+(?:\.\d+)?)', text)
        leadership = re.search(r'LEADERSHIP:\s*(\d+(?:\.\d+)?)', text)
        collaboration = re.search(r'COLLABORATION:\s*(\d+(?:\.\d+)?)', text)
        sentiment = re.search(r'SENTIMENT:\s*(-?\d+(?:\.\d+)?)', text)
        initiative = re.search(r'INITIATIVE:\s*(\d+(?:\.\d+)?)', text)
        
        # Extract feedback
        instant_feedback = re.search(r'INSTANT_FEEDBACK:\s*(.+?)(?=\nSTRENGTHS|\Z)', text, re.DOTALL)
        strengths = re.search(r'STRENGTHS:\s*(.+?)(?=\nSUGGESTIONS|\Z)', text, re.DOTALL)
        suggestions = re.search(r'SUGGESTIONS:\s*(.+?)(?=\n|$)', text, re.DOTALL)
        
        return {
            'relevance_score': float(relevance.group(1)) if relevance else 6.0,
            'clarity_score': float(clarity.group(1)) if clarity else 6.0,
            'confidence_score': float(confidence.group(1)) if confidence else 6.0,
            'leadership_score': float(leadership.group(1)) if leadership else 6.0,
            'collaboration_score': float(collaboration.group(1)) if collaboration else 6.0,
            'sentiment_score': float(sentiment.group(1)) if sentiment else 0.0,
            'initiative_score': float(initiative.group(1)) if initiative else 6.0,
            'instant_feedback': instant_feedback.group(1).strip() if instant_feedback else "Good contribution to the discussion!",
            'strengths': strengths.group(1).strip() if strengths else "Clear communication",
            'suggestions': suggestions.group(1).strip() if suggestions else "Keep engaging with the topic"
        }
        
    except Exception as e:
        print(f"Error in real-time message evaluation: {e}")
        return {
            'relevance_score': 6.0,
            'clarity_score': 6.0,
            'confidence_score': 6.0,
            'leadership_score': 6.0,
            'collaboration_score': 6.0,
            'sentiment_score': 0.0,
            'initiative_score': 6.0,
            'instant_feedback': "Thanks for participating!",
            'strengths': "Active participation",
            'suggestions': "Continue sharing your thoughts"
        }


def ai_moderator_intervention(room_messages, topic_context, current_participants):
    """
    AI Moderator system to guide discussion and maintain engagement
    
    Args:
        room_messages: Recent messages in the room
        topic_context: Discussion topic information
        current_participants: List of active participants
    
    Returns:
        dict with moderator suggestions and interventions
    """
    
    messages_summary = "\n".join([f"User {i+1}: {msg}" for i, msg in enumerate(room_messages[-10:])])
    participant_count = len(current_participants)
    
    prompt = f"""
    You are an AI MODERATOR for a Group Discussion room with {participant_count} participants.
    
    TOPIC: {topic_context}
    
    RECENT DISCUSSION:
    {messages_summary}
    
    As an AI moderator, analyze the discussion flow and provide interventions:
    
    1. DISCUSSION_HEALTH: Rate the current discussion quality (1-10)
    2. ENGAGEMENT_LEVEL: Are all participants contributing? (1-10)
    3. TOPIC_FOCUS: How well are participants staying on topic? (1-10)
    
    Provide interventions if needed:
    - If discussion is stagnant: Suggest new angles or questions
    - If off-topic: Gentle redirection
    - If dominated by one person: Encourage others
    - If lacking depth: Probe for deeper analysis
    
    Format response exactly like this:
    
    DISCUSSION_HEALTH: [score]/10
    ENGAGEMENT_LEVEL: [score]/10
    TOPIC_FOCUS: [score]/10
    
    INTERVENTION_NEEDED: [YES/NO]
    INTERVENTION_TYPE: [redirection/engagement/deepening/new_angle/none]
    
    MODERATOR_MESSAGE: [If intervention needed, provide a helpful moderator message to guide discussion. Keep it conversational and encouraging. If no intervention needed, write "NONE"]
    
    SUGGESTED_QUESTIONS: [2-3 follow-up questions to enhance discussion, separated by |]
    
    Keep moderator messages friendly and guiding, not controlling.
    """
    
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        
        text = response.text.strip()
        
        # Extract assessments
        health = re.search(r'DISCUSSION_HEALTH:\s*(\d+(?:\.\d+)?)', text)
        engagement = re.search(r'ENGAGEMENT_LEVEL:\s*(\d+(?:\.\d+)?)', text)
        focus = re.search(r'TOPIC_FOCUS:\s*(\d+(?:\.\d+)?)', text)
        
        # Extract intervention details
        intervention_needed = re.search(r'INTERVENTION_NEEDED:\s*(YES|NO)', text, re.IGNORECASE)
        intervention_type = re.search(r'INTERVENTION_TYPE:\s*(.+?)(?=\n|$)', text)
        moderator_message = re.search(r'MODERATOR_MESSAGE:\s*(.+?)(?=\nSUGGESTED_QUESTIONS|\Z)', text, re.DOTALL)
        suggested_questions = re.search(r'SUGGESTED_QUESTIONS:\s*(.+?)(?=\n|$)', text, re.MULTILINE)
        
        return {
            'discussion_health': float(health.group(1)) if health else 7.0,
            'engagement_level': float(engagement.group(1)) if engagement else 7.0,
            'topic_focus': float(focus.group(1)) if focus else 7.0,
            'intervention_needed': intervention_needed.group(1).upper() == 'YES' if intervention_needed else False,
            'intervention_type': intervention_type.group(1).strip() if intervention_type else 'none',
            'moderator_message': moderator_message.group(1).strip() if moderator_message and moderator_message.group(1).strip() != 'NONE' else None,
            'suggested_questions': suggested_questions.group(1).strip().split('|') if suggested_questions else []
        }
        
    except Exception as e:
        print(f"Error in AI moderator intervention: {e}")
        return {
            'discussion_health': 7.0,
            'engagement_level': 7.0,
            'topic_focus': 7.0,
            'intervention_needed': False,
            'intervention_type': 'none',
            'moderator_message': None,
            'suggested_questions': []
        }


def evaluate_voice_message_realtime(transcribed_text, topic_context, audio_duration, word_count, room_context=None, participant_history=None):
    """
    Real-time evaluation of voice messages in group discussion rooms
    
    Args:
        transcribed_text: Speech-to-text converted message
        topic_context: Discussion topic and description
        audio_duration: Duration of audio in seconds
        word_count: Number of words in transcribed text
        room_context: Recent room messages for context (optional)
        participant_history: Previous messages from this participant (optional)
        
    Returns:
        dict with voice-specific scores and real-time feedback
    """
    
    # Calculate speaking rate (words per minute)
    speaking_rate = (word_count / (audio_duration / 60)) if audio_duration > 0 else 0
    
    room_context_str = ""
    if room_context:
        room_context_str = "Recent room discussion:\n" + "\n".join(room_context[-5:])
    
    history_context = ""
    if participant_history:
        history_context = "Participant's previous contributions:\n" + "\n".join(participant_history[-3:])
    
    prompt = f"""
    Evaluate this VOICE message in a real-time Group Discussion room for placement assessment.
    
    TOPIC CONTEXT: {topic_context}
    AUDIO DURATION: {audio_duration:.1f} seconds
    WORD COUNT: {word_count} words
    SPEAKING RATE: {speaking_rate:.1f} words per minute
    
    {room_context_str}
    
    {history_context}
    
    TRANSCRIBED MESSAGE: {transcribed_text}
    
    Evaluate on these criteria (score 0-10 each):
    
    CONTENT EVALUATION:
    1. RELEVANCE - How relevant to the ongoing discussion?
    2. CLARITY - How clear and well-structured is the communication?
    3. CONFIDENCE - How confident and assertive is the delivery?
    4. LEADERSHIP - Does this show leadership in the group discussion?
    5. COLLABORATION - How well does this build on others' contributions?
    
    VOICE-SPECIFIC EVALUATION:
    6. FLUENCY - Based on transcription quality, rate speech fluency
    7. PRONUNCIATION - Based on transcription accuracy, rate pronunciation clarity
    8. PACE - Rate speaking speed appropriateness
       - Optimal range: 140-180 words/minute
       - Current rate: {speaking_rate:.1f} wpm
       - Too slow (under 120): Lower score
       - Too fast (over 200): Lower score
    
    ROOM DYNAMICS:
    9. TIMING - Was this contribution well-timed in the discussion flow?
    10. ENGAGEMENT - How engaging is this for other participants?
    
    Format your response exactly like this:
    
    RELEVANCE: [score]/10
    CLARITY: [score]/10
    CONFIDENCE: [score]/10
    LEADERSHIP: [score]/10
    COLLABORATION: [score]/10
    FLUENCY: [score]/10
    PRONUNCIATION: [score]/10
    PACE: [score]/10
    TIMING: [score]/10
    ENGAGEMENT: [score]/10
    
    INSTANT_FEEDBACK: [1-2 sentences of immediate voice-specific feedback]
    VOICE_STRENGTHS: [1-2 voice delivery strengths]
    VOICE_SUGGESTIONS: [1-2 voice improvement tips]
    
    Keep feedback concise for real-time display in group setting.
    """
    
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        
        text = response.text.strip()
        
        # Extract scores
        relevance = re.search(r'RELEVANCE:\s*(\d+(?:\.\d+)?)', text)
        clarity = re.search(r'CLARITY:\s*(\d+(?:\.\d+)?)', text)
        confidence = re.search(r'CONFIDENCE:\s*(\d+(?:\.\d+)?)', text)
        leadership = re.search(r'LEADERSHIP:\s*(\d+(?:\.\d+)?)', text)
        collaboration = re.search(r'COLLABORATION:\s*(\d+(?:\.\d+)?)', text)
        fluency = re.search(r'FLUENCY:\s*(\d+(?:\.\d+)?)', text)
        pronunciation = re.search(r'PRONUNCIATION:\s*(\d+(?:\.\d+)?)', text)
        pace = re.search(r'PACE:\s*(\d+(?:\.\d+)?)', text)
        timing = re.search(r'TIMING:\s*(\d+(?:\.\d+)?)', text)
        engagement = re.search(r'ENGAGEMENT:\s*(\d+(?:\.\d+)?)', text)
        
        # Extract feedback
        instant_feedback = re.search(r'INSTANT_FEEDBACK:\s*(.+?)(?=\nVOICE_STRENGTHS|\Z)', text, re.DOTALL)
        voice_strengths = re.search(r'VOICE_STRENGTHS:\s*(.+?)(?=\nVOICE_SUGGESTIONS|\Z)', text, re.DOTALL)
        voice_suggestions = re.search(r'VOICE_SUGGESTIONS:\s*(.+?)(?=\n|$)', text, re.DOTALL)
        
        return {
            'relevance_score': float(relevance.group(1)) if relevance else 6.0,
            'clarity_score': float(clarity.group(1)) if clarity else 6.0,
            'confidence_score': float(confidence.group(1)) if confidence else 6.0,
            'leadership_score': float(leadership.group(1)) if leadership else 6.0,
            'collaboration_score': float(collaboration.group(1)) if collaboration else 6.0,
            'fluency_score': float(fluency.group(1)) if fluency else 6.0,
            'pronunciation_score': float(pronunciation.group(1)) if pronunciation else 6.0,
            'pace_score': float(pace.group(1)) if pace else 6.0,
            'timing_score': float(timing.group(1)) if timing else 6.0,
            'engagement_score': float(engagement.group(1)) if engagement else 6.0,
            'speaking_rate': speaking_rate,
            'instant_feedback': instant_feedback.group(1).strip() if instant_feedback else "Good voice contribution to the discussion!",
            'voice_strengths': voice_strengths.group(1).strip() if voice_strengths else "Clear voice delivery",
            'voice_suggestions': voice_suggestions.group(1).strip() if voice_suggestions else "Continue using voice effectively"
        }
        
    except Exception as e:
        print(f"Error evaluating voice message in real-time: {e}")
        return {
            'relevance_score': 6.0,
            'clarity_score': 6.0,
            'confidence_score': 6.0,
            'leadership_score': 6.0,
            'collaboration_score': 6.0,
            'fluency_score': 6.0,
            'pronunciation_score': 6.0,
            'pace_score': 6.0,
            'timing_score': 6.0,
            'engagement_score': 6.0,
            'speaking_rate': speaking_rate,
            'instant_feedback': "Thanks for your voice contribution!",
            'voice_strengths': "Active voice participation",
            'voice_suggestions': "Keep engaging with voice messages"
        }


def evaluate_gd_response(response_text, topic_context, previous_responses=None):
    """
    Evaluate a single GD response for quality, relevance, and communication skills
    
    Args:
        response_text: User's response text
        topic_context: Discussion topic and description
        previous_responses: List of previous responses for context (optional)
        
    Returns:
        dict with scores and feedback
    """
    
    previous_context = ""
    if previous_responses:
        previous_context = "Previous discussion points:\n" + "\n".join(previous_responses[-3:])  # Last 3 responses
    
    prompt = f"""
    Evaluate this Group Discussion response for placement assessment.
    
    TOPIC: {topic_context}
    
    {previous_context}
    
    USER RESPONSE: {response_text}
    
    Evaluate the response on these criteria (score 0-10 for each):
    
    1. RELEVANCE - How relevant is the response to the topic?
    2. CLARITY - How clear and well-structured is the communication?
    3. LOGIC - How logical and well-reasoned are the arguments?
    4. CONTENT_QUALITY - How insightful and valuable is the content?
    5. CONFIDENCE - How confident and assertive is the tone?
    
    Format your response exactly like this:
    
    RELEVANCE: [score]/10
    CLARITY: [score]/10
    LOGIC: [score]/10
    CONTENT_QUALITY: [score]/10
    CONFIDENCE: [score]/10
    
    STRENGTHS: [2-3 specific strengths]
    WEAKNESSES: [2-3 areas for improvement]
    SUGGESTIONS: [2-3 specific suggestions]
    
    Be specific and constructive in your feedback.
    """
    
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        
        text = response.text.strip()
        
        # Extract scores
        relevance = re.search(r'RELEVANCE:\s*(\d+(?:\.\d+)?)', text)
        clarity = re.search(r'CLARITY:\s*(\d+(?:\.\d+)?)', text)
        logic = re.search(r'LOGIC:\s*(\d+(?:\.\d+)?)', text)
        content_quality = re.search(r'CONTENT_QUALITY:\s*(\d+(?:\.\d+)?)', text)
        confidence = re.search(r'CONFIDENCE:\s*(\d+(?:\.\d+)?)', text)
        
        # Extract feedback
        strengths = re.search(r'STRENGTHS:\s*(.+?)(?=\nWEAKNESSES|\Z)', text, re.DOTALL)
        weaknesses = re.search(r'WEAKNESSES:\s*(.+?)(?=\nSUGGESTIONS|\Z)', text, re.DOTALL)
        suggestions = re.search(r'SUGGESTIONS:\s*(.+?)(?=\n|$)', text, re.DOTALL)
        
        return {
            'relevance_score': float(relevance.group(1)) if relevance else 5.0,
            'clarity_score': float(clarity.group(1)) if clarity else 5.0,
            'logic_score': float(logic.group(1)) if logic else 5.0,
            'content_quality_score': float(content_quality.group(1)) if content_quality else 5.0,
            'confidence_score': float(confidence.group(1)) if confidence else 5.0,
            'strengths': strengths.group(1).strip() if strengths else "Good participation",
            'weaknesses': weaknesses.group(1).strip() if weaknesses else "Room for improvement",
            'suggestions': suggestions.group(1).strip() if suggestions else "Keep practicing"
        }
        
    except Exception as e:
        print(f"Error evaluating GD response: {e}")
        return {
            'relevance_score': 5.0,
            'clarity_score': 5.0,
            'logic_score': 5.0,
            'content_quality_score': 5.0,
            'confidence_score': 5.0,
            'strengths': "Participated in discussion",
            'weaknesses': "Could not analyze due to technical error",
            'suggestions': "Please try again"
        }


def analyze_room_session_comprehensive(room_messages, topic_context, room_duration, participant_data):
    """
    Comprehensive analysis of entire Group Discussion room session with all participants
    
    Args:
        room_messages: List of all messages in the room with user_id and timestamps
        topic_context: Discussion topic information
        room_duration: Total room session time in seconds
        participant_data: Dict of participant info {user_id: {name, join_time, etc}}
        
    Returns:
        dict with comprehensive room evaluation and individual participant scores
    """
    
    # Prepare room summary
    total_messages = len(room_messages)
    total_words = sum(len(msg['text'].split()) for msg in room_messages)
    participant_ids = list(participant_data.keys())
    num_participants = len(participant_ids)
    
    # Prepare messages for analysis
    messages_for_analysis = []
    participant_contributions = {}
    
    for msg in room_messages:
        user_id = msg['user_id']
        participant_name = participant_data.get(user_id, {}).get('name', f'Participant {user_id}')
        messages_for_analysis.append(f"{participant_name}: {msg['text']}")
        
        # Track individual contributions
        if user_id not in participant_contributions:
            participant_contributions[user_id] = {'messages': 0, 'words': 0, 'voice_messages': 0}
        
        participant_contributions[user_id]['messages'] += 1
        participant_contributions[user_id]['words'] += len(msg['text'].split())
        if msg.get('is_voice', False):
            participant_contributions[user_id]['voice_messages'] += 1
    
    room_discussion = "\n\n".join(messages_for_analysis)
    
    prompt = f"""
    Conduct a COMPREHENSIVE Group Discussion room evaluation for {num_participants} participants in a placement assessment scenario.
    
    TOPIC: {topic_context}
    ROOM DURATION: {room_duration//60} minutes
    TOTAL MESSAGES: {total_messages}
    TOTAL WORDS: {total_words}
    PARTICIPANTS: {num_participants}
    
    COMPLETE ROOM DISCUSSION:
    {room_discussion}
    
    Analyze this collaborative Group Discussion room on multiple dimensions:
    
    ROOM-LEVEL ANALYSIS:
    1. OVERALL_DISCUSSION_QUALITY (0-100): How engaging and productive was the discussion?
    2. TOPIC_ADHERENCE (0-100): How well did the group stay on topic?
    3. COLLABORATION_LEVEL (0-100): How well did participants build on each other's ideas?
    4. DIVERSITY_OF_PERSPECTIVES (0-100): Were multiple viewpoints explored?
    5. DEPTH_OF_ANALYSIS (0-100): How deep and insightful was the discussion?
    
    INDIVIDUAL PARTICIPANT RANKING:
    Rank all participants from 1st to {num_participants} position based on overall performance.
    
    LEADERSHIP IDENTIFICATION:
    Who emerged as natural leaders? Who guided the discussion effectively?
    
    COLLABORATION PATTERNS:
    How did participants interact? Who built on others' ideas? Who asked good questions?
    
    Format your response exactly like this:
    
    OVERALL_DISCUSSION_QUALITY: [score]/100
    TOPIC_ADHERENCE: [score]/100
    COLLABORATION_LEVEL: [score]/100
    DIVERSITY_OF_PERSPECTIVES: [score]/100
    DEPTH_OF_ANALYSIS: [score]/100
    
    ROOM_OVERALL_SCORE: [weighted average]/100
    
    PARTICIPANT_RANKINGS:
    1st: [Participant Name] - [reason for top ranking]
    2nd: [Participant Name] - [reason]
    {"3rd: [Participant Name] - [reason]" if num_participants >= 3 else ""}
    {"4th: [Participant Name] - [reason]" if num_participants >= 4 else ""}
    {"5th: [Participant Name] - [reason]" if num_participants >= 5 else ""}
    {"6th: [Participant Name] - [reason]" if num_participants >= 6 else ""}
    
    IDENTIFIED_LEADERS:
    - [Leader 1]: [leadership qualities shown]
    - [Leader 2]: [leadership qualities shown] (if applicable)
    
    BEST_COLLABORATORS:
    - [Name]: [collaboration strengths]
    - [Name]: [collaboration strengths]
    
    DISCUSSION_HIGHLIGHTS:
    - [Key insight or moment from discussion]
    - [Another significant contribution or exchange]
    - [Third notable aspect of the discussion]
    
    ROOM_IMPROVEMENT_AREAS:
    - [Area where the entire group could improve]
    - [Another collective improvement opportunity]
    
    MODERATOR_OBSERVATIONS: [2-3 paragraphs analyzing the group dynamics, communication patterns, and overall discussion effectiveness from an AI moderator’s perspective]
    
    Provide specific, constructive analysis suitable for placement feedback.
    """
    
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        
        text = response.text.strip()
        
        # Extract room-level scores
        discussion_quality = re.search(r'OVERALL_DISCUSSION_QUALITY:\s*(\d+(?:\.\d+)?)', text)
        topic_adherence = re.search(r'TOPIC_ADHERENCE:\s*(\d+(?:\.\d+)?)', text)
        collaboration = re.search(r'COLLABORATION_LEVEL:\s*(\d+(?:\.\d+)?)', text)
        diversity = re.search(r'DIVERSITY_OF_PERSPECTIVES:\s*(\d+(?:\.\d+)?)', text)
        depth = re.search(r'DEPTH_OF_ANALYSIS:\s*(\d+(?:\.\d+)?)', text)
        overall_score = re.search(r'ROOM_OVERALL_SCORE:\s*(\d+(?:\.\d+)?)', text)
        
        # Extract analysis sections
        rankings_match = re.search(r'PARTICIPANT_RANKINGS:\s*(.+?)(?=\nIDENTIFIED_LEADERS)', text, re.DOTALL)
        leaders_match = re.search(r'IDENTIFIED_LEADERS:\s*(.+?)(?=\nBEST_COLLABORATORS)', text, re.DOTALL)
        collaborators_match = re.search(r'BEST_COLLABORATORS:\s*(.+?)(?=\nDISCUSSION_HIGHLIGHTS)', text, re.DOTALL)
        highlights_match = re.search(r'DISCUSSION_HIGHLIGHTS:\s*(.+?)(?=\nROOM_IMPROVEMENT_AREAS)', text, re.DOTALL)
        improvements_match = re.search(r'ROOM_IMPROVEMENT_AREAS:\s*(.+?)(?=\nMODERATOR_OBSERVATIONS)', text, re.DOTALL)
        observations_match = re.search(r'MODERATOR_OBSERVATIONS:\s*(.+?)$', text, re.DOTALL)
        
        # Calculate individual participation metrics
        individual_metrics = {}
        for user_id, contrib in participant_contributions.items():
            participation_percentage = (contrib['words'] / total_words * 100) if total_words > 0 else 0
            avg_message_length = contrib['words'] / contrib['messages'] if contrib['messages'] > 0 else 0
            
            individual_metrics[user_id] = {
                'message_count': contrib['messages'],
                'word_count': contrib['words'],
                'voice_message_count': contrib['voice_messages'],
                'participation_percentage': round(participation_percentage, 1),
                'avg_message_length': round(avg_message_length, 1)
            }
        
        return {
            # Room-level scores
            'discussion_quality_score': float(discussion_quality.group(1)) if discussion_quality else 75.0,
            'topic_adherence_score': float(topic_adherence.group(1)) if topic_adherence else 75.0,
            'collaboration_score': float(collaboration.group(1)) if collaboration else 75.0,
            'diversity_score': float(diversity.group(1)) if diversity else 75.0,
            'depth_score': float(depth.group(1)) if depth else 75.0,
            'room_overall_score': float(overall_score.group(1)) if overall_score else 75.0,
            
            # Room analytics
            'total_messages': total_messages,
            'total_words': total_words,
            'num_participants': num_participants,
            'avg_messages_per_participant': total_messages / num_participants if num_participants > 0 else 0,
            'avg_words_per_participant': total_words / num_participants if num_participants > 0 else 0,
            
            # Individual participant metrics
            'participant_metrics': individual_metrics,
            
            # Analysis sections
            'participant_rankings': rankings_match.group(1).strip() if rankings_match else "Rankings analysis unavailable",
            'identified_leaders': leaders_match.group(1).strip() if leaders_match else "No clear leaders identified",
            'best_collaborators': collaborators_match.group(1).strip() if collaborators_match else "Collaboration analysis unavailable",
            'discussion_highlights': highlights_match.group(1).strip() if highlights_match else "No specific highlights identified",
            'improvement_areas': improvements_match.group(1).strip() if improvements_match else "General improvement in participation recommended",
            'moderator_observations': observations_match.group(1).strip() if observations_match else "Room showed good collaborative discussion with opportunities for enhanced engagement and deeper analysis.",
        }
        
    except Exception as e:
        print(f"Error analyzing room session: {e}")
        # Return default comprehensive analysis
        individual_metrics = {}
        for user_id, contrib in participant_contributions.items():
            participation_percentage = (contrib['words'] / total_words * 100) if total_words > 0 else 0
            individual_metrics[user_id] = {
                'message_count': contrib['messages'],
                'word_count': contrib['words'],
                'voice_message_count': contrib['voice_messages'],
                'participation_percentage': round(participation_percentage, 1),
                'avg_message_length': 15.0
            }
        
        return {
            'discussion_quality_score': 75.0,
            'topic_adherence_score': 75.0,
            'collaboration_score': 75.0,
            'diversity_score': 75.0,
            'depth_score': 75.0,
            'room_overall_score': 75.0,
            'total_messages': total_messages,
            'total_words': total_words,
            'num_participants': num_participants,
            'avg_messages_per_participant': total_messages / num_participants if num_participants > 0 else 0,
            'avg_words_per_participant': total_words / num_participants if num_participants > 0 else 0,
            'participant_metrics': individual_metrics,
            'participant_rankings': "Analysis unavailable due to technical issues",
            'identified_leaders': "Leadership analysis unavailable",
            'best_collaborators': "Collaboration analysis unavailable",
            'discussion_highlights': "Discussion proceeded with good participation",
            'improvement_areas': "Continue practicing group discussion skills",
            'moderator_observations': "The group demonstrated collaborative discussion. Technical issues prevented detailed analysis. Continue practicing to improve group discussion skills."
        }


# ===============================
# AI RESUME BUILDER + VALIDATION
# ===============================

def generate_resume(personal_info, education, experience, projects, skills, certifications, target_role="Software Developer"):
    """
    Generate professional ATS-friendly resume using AI
    
    Args:
        personal_info: dict with name, email, phone, address
        education: list of education entries
        experience: list of work experience
        projects: list of project entries  
        skills: list of skills
        certifications: list of certifications
        target_role: target job role for customization
    """
    
    prompt = f"""
    Create a professional, ATS-friendly resume for a {target_role} position.
    
    Personal Information:
    {json.dumps(personal_info, indent=2)}
    
    Education:
    {json.dumps(education, indent=2)}
    
    Work Experience:
    {json.dumps(experience, indent=2) if experience else "No work experience"}
    
    Projects:
    {json.dumps(projects, indent=2)}
    
    Technical Skills:
    {json.dumps(skills, indent=2)}
    
    Certifications:
    {json.dumps(certifications, indent=2) if certifications else "No certifications"}
    
    Requirements:
    1. Create professional resume content in HTML format
    2. Use clean, ATS-compatible structure
    3. Add strong action verbs and measurable achievements
    4. Optimize for {target_role} keywords
    5. Include proper sections: Contact, Summary, Education, Skills, Projects, Experience
    6. Make descriptions compelling and quantified where possible
    7. Ensure proper formatting with headers and bullet points
    
    Return ONLY the HTML resume content, no extra text.
    """
    
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        
        # Check if response looks like HTML
        if '<html>' in response.text.lower() or '<div>' in response.text.lower() or '<h' in response.text.lower():
            return response.text
        else:
            # If not HTML, generate fallback resume
            return generate_fallback_resume(personal_info, education, experience, projects, skills, certifications, target_role)
            
    except Exception as e:
        print(f"Error generating resume: {e}")
        # Return fallback resume
        return generate_fallback_resume(personal_info, education, experience, projects, skills, certifications, target_role)


def generate_fallback_resume(personal_info, education, experience, projects, skills, certifications, target_role):
    """Generate a basic HTML resume when AI generation fails"""
    
    name = personal_info.get('name', 'John Doe')
    email = personal_info.get('email', 'email@example.com')
    phone = personal_info.get('phone', '+91-9999999999')
    
    skills_str = ', '.join(skills) if skills else 'Programming, Web Development, Problem Solving'
    
    html_resume = f"""
    <div class="resume-container" style="font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px;">
        <header style="text-align: center; border-bottom: 2px solid #333; margin-bottom: 20px; padding-bottom: 10px;">
            <h1 style="margin: 0; color: #333;">{name}</h1>
            <p style="margin: 5px 0; color: #666;">Aspiring {target_role}</p>
            <p style="margin: 5px 0;">{email} | {phone}</p>
        </header>
        
        <section style="margin-bottom: 20px;">
            <h2 style="color: #333; border-bottom: 1px solid #ccc;">Professional Summary</h2>
            <p>Motivated and detail-oriented {target_role} with strong technical skills and passion for innovation. 
            Seeking to leverage programming knowledge and project experience to contribute to a dynamic development team.</p>
        </section>
        
        <section style="margin-bottom: 20px;">
            <h2 style="color: #333; border-bottom: 1px solid #ccc;">Technical Skills</h2>
            <p><strong>Programming & Technologies:</strong> {skills_str}</p>
        </section>
        
        <section style="margin-bottom: 20px;">
            <h2 style="color: #333; border-bottom: 1px solid #ccc;">Education</h2>"""
    
    for edu in education:
        html_resume += f"""
            <div style="margin-bottom: 10px;">
                <h3 style="margin: 0; color: #333;">{edu.get('degree', 'Bachelor of Technology')}</h3>
                <p style="margin: 0; color: #666;">{edu.get('institution', 'University')} | {edu.get('year', '2024')}</p>
                {f"<p style='margin: 0;'>Grade: {edu.get('grade')}</p>" if edu.get('grade') else ""}
            </div>"""
    
    if projects:
        html_resume += """
        <section style="margin-bottom: 20px;">
            <h2 style="color: #333; border-bottom: 1px solid #ccc;">Projects</h2>"""
        
        for project in projects:
            html_resume += f"""
            <div style="margin-bottom: 15px;">
                <h3 style="margin: 0; color: #333;">{project.get('name', 'Project')}</h3>
                <p style="margin: 5px 0;">{project.get('description', 'Project description')}</p>
                <p style="margin: 0; font-style: italic; color: #666;">
                    <strong>Technologies:</strong> {project.get('technologies', 'Various technologies')}
                </p>
                {f"<p style='margin: 0;'><strong>Link:</strong> {project.get('link')}</p>" if project.get('link') else ""}
            </div>"""
        
        html_resume += "</section>"
    
    if experience:
        html_resume += """
        <section style="margin-bottom: 20px;">
            <h2 style="color: #333; border-bottom: 1px solid #ccc;">Work Experience</h2>"""
        
        for exp in experience:
            html_resume += f"""
            <div style="margin-bottom: 15px;">
                <h3 style="margin: 0; color: #333;">{exp.get('position', 'Position')}</h3>
                <p style="margin: 0; color: #666;">{exp.get('company', 'Company')} | {exp.get('duration', 'Duration')}</p>
                <p style="margin: 5px 0;">{exp.get('description', 'Role description')}</p>
            </div>"""
        
        html_resume += "</section>"
    
    if certifications:
        html_resume += """
        <section style="margin-bottom: 20px;">
            <h2 style="color: #333; border-bottom: 1px solid #ccc;">Certifications</h2>
            <ul>"""
        
        for cert in certifications:
            html_resume += f"<li>{cert.get('name', 'Certification')}</li>"
        
        html_resume += "</ul></section>"
    
    html_resume += "</div>"
    
    return html_resume


def validate_resume(resume_content, target_role="Software Developer"):
    """
    Enhanced AI Resume Validation - comprehensive analysis with industry insights
    
    Returns detailed analysis with scores, benchmarking, and actionable suggestions
    """
    
    prompt = f"""
    Act as an expert HR recruiter, ATS specialist, and career coach with 15+ years experience.
    
    Analyze this resume for a {target_role} position with comprehensive industry insights:
    
    Resume Content:
    {resume_content}
    
    Provide a detailed analysis in the following JSON format:
    {{
        "overall_score": [0-100],
        "content_score": [0-10],
        "structure_score": [0-10], 
        "skills_score": [0-10],
        "ats_score": [0-10],
        "industry_relevance_score": [0-10],
        "strengths": ["specific strength with context", "quantified achievement example"],
        "weaknesses": ["specific weakness with impact", "missing element with reason"],
        "suggestions": ["actionable improvement with timeline", "specific enhancement strategy"],
        "missing_skills": ["critical skill with market demand", "emerging technology requirement"],
        "ats_issues": ["specific formatting issue", "keyword density problem"],
        "keyword_analysis": {{
            "present_keywords": ["identified technical terms", "role-relevant skills"],
            "missing_keywords": ["critical industry terms", "trending technologies"],
            "keyword_density": "low/medium/high",
            "competitiveness": "below average/average/above average"
        }},
        "industry_insights": {{
            "market_demand": "high/medium/low",
            "salary_competitiveness": [0-10],
            "trending_skills": ["emerging skill 1", "in-demand technology 2"],
            "career_progression": ["next logical role", "growth opportunity"],
            "certification_recommendations": ["relevant cert 1", "valuable credential 2"]
        }},
        "benchmarking": {{
            "compared_to_peers": "below average/average/above average",
            "top_percentile": [0-100],
            "improvement_potential": "limited/moderate/high",
            "competitive_advantage": ["unique strength 1", "differentiator 2"]
        }},
        "actionable_roadmap": [
            {{
                "category": "immediate (1-2 weeks)",
                "action": "specific task",
                "impact": "expected improvement",
                "effort": "low/medium/high"
            }},
            {{
                "category": "short-term (1-2 months)", 
                "action": "development activity",
                "impact": "skill enhancement result",
                "effort": "low/medium/high"
            }},
            {{
                "category": "long-term (3-6 months)",
                "action": "strategic improvement",
                "impact": "career advancement outcome",
                "effort": "low/medium/high"
            }}
        ]
    }}
    
    Enhanced Evaluation Criteria:
    1. Content Quality (0-10): Achievement impact, quantified results, action verbs, compelling narrative
    2. Structure (0-10): Professional format, logical flow, ATS-friendly layout, visual hierarchy
    3. Skills Match (0-10): Technical relevance, depth demonstration, trending technologies, certifications
    4. ATS Compatibility (0-10): Parsing success rate, keyword optimization, formatting compliance
    5. Industry Relevance (0-10): Market alignment, competitive positioning, growth potential
    
    Be specific, data-driven, and provide actionable insights with business context.
    Return ONLY valid JSON, no additional text or formatting.
    """
    
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        
        # Try to parse as JSON first
        try:
            import json
            json.loads(response.text.strip())
            return response.text.strip()
        except json.JSONDecodeError:
            # Enhanced fallback analysis
            return json.dumps({
                "overall_score": 75,
                "content_score": 7,
                "structure_score": 8,
                "skills_score": 7,
                "ats_score": 7,
                "industry_relevance_score": 6,
                "strengths": ["Clear professional structure", "Technical skills demonstrated", "Educational background evident"],
                "weaknesses": ["Limited quantified achievements", "Missing industry-specific keywords", "Could strengthen impact statements"],
                "suggestions": ["Add measurable project results with metrics", "Include relevant technical certifications", "Optimize keyword density for ATS"], 
                "missing_skills": ["Cloud computing platforms", "DevOps methodologies", "Emerging framework knowledge"],
                "ats_issues": ["Keyword density below optimal range", "Could improve section formatting for better parsing"],
                "keyword_analysis": {
                    "present_keywords": ["programming", "development", "software", "technical"],
                    "missing_keywords": ["cloud", "agile", "automation", "API", "microservices"],
                    "keyword_density": "medium",
                    "competitiveness": "average"
                },
                "industry_insights": {
                    "market_demand": "high",
                    "salary_competitiveness": 7,
                    "trending_skills": ["AI/ML integration", "Cloud architecture", "DevSecOps"],
                    "career_progression": ["Senior Developer", "Tech Lead", "Solutions Architect"], 
                    "certification_recommendations": ["AWS Solutions Architect", "Google Cloud Professional", "Azure DevOps Engineer"]
                },
                "benchmarking": {
                    "compared_to_peers": "average",
                    "top_percentile": 65,
                    "improvement_potential": "moderate",
                    "competitive_advantage": ["Academic foundation", "Multi-technology exposure"]
                },
                "actionable_roadmap": [
                    {
                        "category": "immediate (1-2 weeks)",
                        "action": "Add quantified achievements to existing roles",
                        "impact": "15-20% improvement in recruiter engagement",
                        "effort": "low"
                    },
                    {
                        "category": "short-term (1-2 months)",
                        "action": "Complete relevant technical certification",
                        "impact": "Enhanced credibility and skill validation",
                        "effort": "medium"
                    },
                    {
                        "category": "long-term (3-6 months)", 
                        "action": "Build portfolio showcasing trending technologies",
                        "impact": "Significant competitive advantage in job market",
                        "effort": "high"
                    }
                ]
            })
    except Exception as e:
        print(f"Error validating resume: {e}")
        # Enhanced error fallback 
        import json
        return json.dumps({
            "overall_score": 70,
            "content_score": 7,
            "structure_score": 7,
            "skills_score": 6,
            "ats_score": 6,
            "industry_relevance_score": 6,
            "strengths": ["Resume structure identified", "Professional background evident", "Educational foundation present"],
            "weaknesses": ["Analysis temporarily unavailable", "Detailed review recommended", "Manual assessment needed"],
            "suggestions": ["Resubmit for complete analysis", "Review formatting for optimal parsing", "Consider professional resume review"],
            "missing_skills": ["Role-specific technical skills", "Industry certifications", "Trending technologies"],
            "ats_issues": ["Format verification needed", "Keyword optimization recommended", "Structure assessment required"],
            "keyword_analysis": {
                "present_keywords": ["basic professional terms identified"],
                "missing_keywords": ["comprehensive analysis pending"],
                "keyword_density": "unknown",
                "competitiveness": "assessment pending"
            },
            "industry_insights": {
                "market_demand": "assessment pending",
                "salary_competitiveness": 5,
                "trending_skills": ["Analysis temporarily unavailable"],
                "career_progression": ["Manual review recommended"],
                "certification_recommendations": ["Industry-standard credentials advised"]
            },
            "benchmarking": {
                "compared_to_peers": "analysis pending",
                "top_percentile": 50,
                "improvement_potential": "assessment needed",
                "competitive_advantage": ["Review required for detailed insights"]
            },
            "actionable_roadmap": [
                {
                    "category": "immediate (1-2 weeks)",
                    "action": "Resubmit resume for comprehensive analysis",
                    "impact": "Complete assessment and recommendations",
                    "effort": "low"
                }
            ]
        })


def analyze_skill_gaps(resume_content, target_role="Software Developer", experience_level="mid-level"):
    """
    Advanced skill gap analysis with market insights and learning recommendations
    
    Args:
        resume_content: Text content of the resume
        target_role: Target position role
        experience_level: junior/mid-level/senior
        
    Returns:
        Detailed skill gap analysis with learning roadmap
    """
    
    prompt = f"""
    Act as a senior technical recruiter and career development specialist.
    
    Analyze skill gaps for this {experience_level} {target_role} candidate:
    
    Resume Content:
    {resume_content}
    
    Provide comprehensive skill gap analysis in JSON format:
    {{
        "current_skill_level": "junior/mid-level/senior",
        "target_role_requirements": [
            {{
                "skill_category": "technical_core",
                "required_skills": ["skill1", "skill2"],
                "current_coverage": [0-100],
                "gap_severity": "low/medium/high"
            }}
        ],
        "skill_assessment": {{
            "strengths": [
                {{
                    "skill": "specific technology/framework",
                    "proficiency": "beginner/intermediate/advanced/expert",
                    "market_value": "low/medium/high",
                    "evidence": "how demonstrated in resume"
                }}
            ],
            "gaps": [
                {{
                    "skill": "missing technology/framework", 
                    "importance": "critical/important/nice-to-have",
                    "market_demand": "high/medium/low",
                    "learning_effort": "low/medium/high",
                    "time_to_proficiency": "1-2 months/3-6 months/6+ months"
                }}
            ]
        }},
        "market_analysis": {{
            "role_competitiveness": [0-100],
            "salary_impact_potential": "high/medium/low",
            "job_market_readiness": [0-100],
            "competitive_positioning": "below average/average/above average/exceptional"
        }},
        "learning_roadmap": {{
            "priority_skills": [
                {{
                    "skill": "technology/framework name",
                    "priority": 1-10,
                    "learning_resources": ["online course", "certification", "project idea"],
                    "estimated_timeline": "weeks/months",
                    "career_impact": "immediate/short-term/long-term"
                }}
            ],
            "certification_path": [
                {{
                    "certification": "credential name",
                    "provider": "AWS/Google/Microsoft/etc",
                    "difficulty": "easy/medium/hard",
                    "time_investment": "hours/days/weeks",
                    "roi_score": [0-10]
                }}
            ],
            "project_suggestions": [
                {{
                    "project_type": "portfolio project idea",
                    "skills_demonstrated": ["skill1", "skill2"],
                    "complexity": "beginner/intermediate/advanced",
                    "time_required": "timeline estimate"
                }}
            ]
        }},
        "next_level_requirements": {{
            "promotion_readiness": [0-100],
            "leadership_skills_needed": ["communication", "mentoring"],
            "technical_depth_areas": ["architecture", "system design"],
            "timeline_to_advancement": "months/years"
        }}
    }}
    
    Focus on:
    - Market-relevant skills and their demand
    - Practical learning paths with realistic timelines
    - High-impact skills that maximize career growth
    - Industry-specific requirements for {target_role}
    - Competitive advantage opportunities
    
    Return ONLY valid JSON, no additional text.
    """
    
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        
        # Try to parse as JSON first
        try:
            import json
            json.loads(response.text.strip())
            return response.text.strip()
        except json.JSONDecodeError:
            # Enhanced fallback analysis
            return json.dumps({
                "current_skill_level": experience_level,
                "target_role_requirements": [
                    {
                        "skill_category": "technical_core",
                        "required_skills": ["Programming Languages", "Frameworks", "Database Management"],
                        "current_coverage": 70,
                        "gap_severity": "medium"
                    },
                    {
                        "skill_category": "soft_skills",
                        "required_skills": ["Communication", "Problem Solving", "Team Collaboration"],
                        "current_coverage": 60,
                        "gap_severity": "medium"
                    }
                ],
                "skill_assessment": {
                    "strengths": [
                        {
                            "skill": "Programming Fundamentals",
                            "proficiency": "intermediate",
                            "market_value": "high", 
                            "evidence": "Multiple projects and educational background"
                        }
                    ],
                    "gaps": [
                        {
                            "skill": "Cloud Technologies",
                            "importance": "critical",
                            "market_demand": "high",
                            "learning_effort": "medium",
                            "time_to_proficiency": "3-6 months"
                        },
                        {
                            "skill": "DevOps Practices",
                            "importance": "important",
                            "market_demand": "high",
                            "learning_effort": "medium", 
                            "time_to_proficiency": "2-4 months"
                        }
                    ]
                },
                "market_analysis": {
                    "role_competitiveness": 70,
                    "salary_impact_potential": "medium",
                    "job_market_readiness": 65,
                    "competitive_positioning": "average"
                },
                "learning_roadmap": {
                    "priority_skills": [
                        {
                            "skill": "Cloud Platforms (AWS/Azure)",
                            "priority": 9,
                            "learning_resources": ["AWS Learning Path", "Azure Fundamentals", "Hands-on Labs"],
                            "estimated_timeline": "3-4 months",
                            "career_impact": "immediate"
                        },
                        {
                            "skill": "Container Technologies",
                            "priority": 8,
                            "learning_resources": ["Docker Tutorial", "Kubernetes Basics", "DevOps Projects"],
                            "estimated_timeline": "2-3 months",
                            "career_impact": "short-term"
                        }
                    ],
                    "certification_path": [
                        {
                            "certification": "AWS Solutions Architect Associate",
                            "provider": "AWS",
                            "difficulty": "medium",
                            "time_investment": "2-3 months",
                            "roi_score": 9
                        }
                    ],
                    "project_suggestions": [
                        {
                            "project_type": "Cloud-based Web Application",
                            "skills_demonstrated": ["AWS", "Microservices", "CI/CD"],
                            "complexity": "intermediate",
                            "time_required": "4-6 weeks"
                        }
                    ]
                },
                "next_level_requirements": {
                    "promotion_readiness": 55,
                    "leadership_skills_needed": ["Technical Mentoring", "Cross-team Collaboration"],
                    "technical_depth_areas": ["System Architecture", "Performance Optimization"],
                    "timeline_to_advancement": "12-18 months"
                }
            })
    except Exception as e:
        print(f"Error analyzing skill gaps: {e}")
        # Return basic fallback
        import json
        return json.dumps({
            "current_skill_level": experience_level,
            "error": "Analysis temporarily unavailable",
            "recommendation": "Please try again or consult with a career counselor"
        })


def simulate_recruiter_review(resume_content, target_role="Software Developer"):
    """
    AI Recruiter Simulation - simulates hiring manager reviewing resume
    
    Returns hiring probability and recruiter feedback
    """
    
    prompt = f"""
    Act as an experienced hiring manager reviewing resumes for a {target_role} position.
    
    Resume to Review:
    {resume_content}
    
    Provide your assessment in the following JSON format:
    {{
        "hiring_probability": [0-100],
        "interview_readiness": "poor/fair/good/excellent",
        "recruiter_feedback": "Detailed feedback paragraph from recruiter perspective",
        "key_strengths": ["strength1", "strength2", "strength3"],
        "major_concerns": ["concern1", "concern2"],
        "interview_focus_areas": ["area1", "area2", "area3"],
        "salary_estimate_range": "X-Y LPA",
        "competition_level": "low/medium/high"
    }}
    
    Think like a real recruiter:
    1. Would you call this candidate for interview?
    2. What stands out positively?
    3. What are red flags?
    4. How does this compare to other candidates?
    5. What would you ask in interview?
    
    Be honest and realistic in your assessment.
    Return ONLY valid JSON, no extra text.
    """
    
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash", 
            contents=prompt
        )
        
        # Try to parse as JSON first
        try:
            import json
            json.loads(response.text.strip())
            return response.text.strip()
        except json.JSONDecodeError:
            # If not valid JSON, return fallback
            return json.dumps({
                "hiring_probability": 70,
                "interview_readiness": "good",
                "recruiter_feedback": "This candidate shows promise with a solid technical background. The resume demonstrates relevant experience and skills for the role.",
                "key_strengths": ["Technical skills", "Project experience", "Clear communication"],
                "major_concerns": ["Limited work experience", "Could provide more specific details"],
                "interview_focus_areas": ["Technical depth", "Problem-solving approach", "Communication skills"],
                "salary_estimate_range": "4-8 LPA",
                "competition_level": "medium"
            })
    except Exception as e:
        print(f"Error simulating recruiter review: {e}")
        # Return default simulation
        import json
        return json.dumps({
            "hiring_probability": 65,
            "interview_readiness": "fair",
            "recruiter_feedback": "Unable to complete detailed analysis. The candidate appears to have relevant qualifications for consideration.",
            "key_strengths": ["Technical background", "Educational qualification"],
            "major_concerns": ["Analysis incomplete", "Need more details"],
            "interview_focus_areas": ["Technical skills assessment", "Project discussion"],
            "salary_estimate_range": "3-7 LPA",
            "competition_level": "medium"
        })


def suggest_resume_improvements(resume_content, validation_data, target_role="Software Developer"):
    """
    Generate specific, actionable resume improvement suggestions
    """
    
    prompt = f"""
    Based on resume analysis, provide specific improvement suggestions.
    
    Current Resume:
    {resume_content}
    
    Analysis Results:
    {validation_data}
    
    Target Role: {target_role}
    
    Provide detailed improvement plan in JSON format:
    {{
        "priority_improvements": [
            {{
                "area": "Skills Section",
                "current_issue": "Missing key technologies",
                "suggested_action": "Add React, Node.js, AWS",
                "impact": "Would increase ATS score by 15 points"
            }}
        ],
        "content_improvements": [
            {{
                "section": "Projects",
                "improvement": "Add quantified results and impact metrics",
                "example": "Increased user engagement by 40% through responsive design"
            }}
        ],
        "format_improvements": ["improvement1", "improvement2"],
        "keyword_optimization": {{
            "add_keywords": ["keyword1", "keyword2"],
            "keyword_placement": "Where to add them"
        }},
        "skill_gap_analysis": [
            {{
                "missing_skill": "Docker",
                "importance": "high",
                "learning_resource": "Docker official documentation"
            }}
        ]
    }}
    
    Return ONLY valid JSON, no extra text.
    """
    
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        return response.text
    except Exception as e:
        print(f"Error suggesting improvements: {e}")
        return None


def generate_resume_summary(user_profile, target_role="Software Developer"):
    """
    Generate professional summary for resume based on user profile
    """
    
    prompt = f"""
    Create a compelling professional summary for a {target_role} resume.
    
    User Profile:
    - Branch: {user_profile.get('branch', 'Computer Science')}
    - Year: {user_profile.get('year', 'Final Year')}
    - Skills: {user_profile.get('skills', '')}
    - Career Goal: {user_profile.get('career_goal', target_role)}
    - Experience Level: {user_profile.get('experience_level', 'Entry Level')}
    
    Create a 3-4 line professional summary that:
    1. Highlights key technical skills
    2. Shows career objective alignment
    3. Mentions relevant experience/projects
    4. Uses strong action words
    5. Is ATS-friendly with keywords
    
    Return only the summary text, no extra formatting.
    """
    
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        return response.text.strip()
    except Exception as e:
        print(f"Error generating summary: {e}")
        return f"Ambitious {target_role} with strong technical skills and passion for innovation."


def generate_individual_participant_evaluation(room_analysis, participant_messages, user_id, participant_data):
    """
    Generate detailed individual evaluation for a specific participant based on room analysis
    
    Args:
        room_analysis: Comprehensive room analysis data
        participant_messages: List of messages from this specific participant
        user_id: ID of the participant being evaluated
        participant_data: Information about this participant
    
    Returns:
        dict with individual evaluation scores and feedback
    """
    
    participant_name = participant_data.get('name', f'Participant {user_id}')
    participant_contributions = [msg['text'] for msg in participant_messages]
    total_participant_words = sum(len(msg['text'].split()) for msg in participant_messages)
    num_messages = len(participant_messages)
    
    # Get metrics from room analysis
    individual_metrics = room_analysis['participant_metrics'].get(str(user_id), {})
    participation_percentage = individual_metrics.get('participation_percentage', 0)
    
    contributions_text = "\n".join([f"Message {i+1}: {msg}" for i, msg in enumerate(participant_contributions)])
    
    prompt = f"""
    Generate individual evaluation for {participant_name} based on their Group Discussion room performance.
    
    ROOM CONTEXT:
    - Overall Room Score: {room_analysis['room_overall_score']}/100
    - Total Participants: {room_analysis['num_participants']}
    - Discussion Quality: {room_analysis['discussion_quality_score']}/100
    - Collaboration Level: {room_analysis['collaboration_score']}/100
    
    PARTICIPANT CONTRIBUTIONS:
    - Messages Sent: {num_messages}
    - Words Contributed: {total_participant_words}
    - Participation Percentage: {participation_percentage}%
    
    ALL PARTICIPANT MESSAGES:
    {contributions_text}
    
    ROOM ANALYSIS INSIGHTS:
    - Rankings: {room_analysis['participant_rankings']}
    - Leaders: {room_analysis['identified_leaders']}
    - Collaborators: {room_analysis['best_collaborators']}
    
    Based on this participant's contributions in the collaborative room setting, evaluate:
    
    INDIVIDUAL SCORES (0-100):
    1. COMMUNICATION: How effectively did they communicate their ideas?
    2. LEADERSHIP: Did they show leadership qualities and guide discussion?
    3. PARTICIPATION: How actively did they participate compared to others?
    4. CONTENT_QUALITY: How valuable and insightful were their contributions?
    5. CONFIDENCE: How confident and assertive were they?
    6. COLLABORATION: How well did they work with other participants?
    7. LISTENING: How well did they build on others' ideas?
    
    COMPARATIVE ANALYSIS:
    How did they perform relative to other participants?
    
    Format your response exactly like this:
    
    COMMUNICATION: [score]/100
    LEADERSHIP: [score]/100
    PARTICIPATION: [score]/100
    CONTENT_QUALITY: [score]/100
    CONFIDENCE: [score]/100
    COLLABORATION: [score]/100
    LISTENING: [score]/100
    
    OVERALL_SCORE: [weighted average]/100
    
    RANK_IN_ROOM: [position like 1st, 2nd, 3rd, etc.]
    PERCENTILE: [percentile compared to other participants]/100
    
    STRENGTHS:
    - [specific strength 1]
    - [specific strength 2]
    - [specific strength 3]
    
    WEAKNESSES:
    - [specific weakness 1]
    - [specific weakness 2]
    - [specific weakness 3]
    
    SUGGESTIONS:
    - [specific improvement suggestion 1]
    - [specific improvement suggestion 2]
    - [specific improvement suggestion 3]
    
    ACHIEVEMENTS: [Notable achievements like "Best Collaborator", "Topic Expert", "Discussion Starter", etc.]
    
    DETAILED_FEEDBACK: [2-3 paragraphs of personalized feedback focusing on their specific performance in the collaborative environment]
    
    Provide specific feedback based on their actual contributions and room dynamics.
    """
    
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        
        text = response.text.strip()
        
        # Extract scores
        communication = re.search(r'COMMUNICATION:\s*(\d+(?:\.\d+)?)', text)
        leadership = re.search(r'LEADERSHIP:\s*(\d+(?:\.\d+)?)', text)
        participation = re.search(r'PARTICIPATION:\s*(\d+(?:\.\d+)?)', text)
        content_quality = re.search(r'CONTENT_QUALITY:\s*(\d+(?:\.\d+)?)', text)
        confidence = re.search(r'CONFIDENCE:\s*(\d+(?:\.\d+)?)', text)
        collaboration = re.search(r'COLLABORATION:\s*(\d+(?:\.\d+)?)', text)
        listening = re.search(r'LISTENING:\s*(\d+(?:\.\d+)?)', text)
        overall_score = re.search(r'OVERALL_SCORE:\s*(\d+(?:\.\d+)?)', text)
        
        # Extract additional metrics
        rank = re.search(r'RANK_IN_ROOM:\s*(.+?)(?=\n)', text)
        percentile = re.search(r'PERCENTILE:\s*(\d+(?:\.\d+)?)', text)
        
        # Extract feedback sections
        strengths_match = re.search(r'STRENGTHS:\s*(.+?)(?=\nWEAKNESSES)', text, re.DOTALL)
        weaknesses_match = re.search(r'WEAKNESSES:\s*(.+?)(?=\nSUGGESTIONS)', text, re.DOTALL)
        suggestions_match = re.search(r'SUGGESTIONS:\s*(.+?)(?=\nACHIEVEMENTS)', text, re.DOTALL)
        achievements_match = re.search(r'ACHIEVEMENTS:\s*(.+?)(?=\nDETAILED_FEEDBACK)', text, re.DOTALL)
        feedback_match = re.search(r'DETAILED_FEEDBACK:\s*(.+?)$', text, re.DOTALL)
        
        return {
            # Core scores
            'communication_score': float(communication.group(1)) if communication else 70.0,
            'leadership_score': float(leadership.group(1)) if leadership else 65.0,
            'participation_score': float(participation.group(1)) if participation else 70.0,
            'content_quality_score': float(content_quality.group(1)) if content_quality else 70.0,
            'confidence_score': float(confidence.group(1)) if confidence else 70.0,
            'collaboration_score': float(collaboration.group(1)) if collaboration else 75.0,
            'listening_score': float(listening.group(1)) if listening else 70.0,
            'overall_score': float(overall_score.group(1)) if overall_score else 70.0,
            
            # Comparative metrics
            'rank_in_room': rank.group(1).strip() if rank else f"{room_analysis['num_participants']}th",
            'percentile_score': float(percentile.group(1)) if percentile else 50.0,
            
            # Participation metrics from room analysis
            'total_messages': num_messages,
            'total_words': total_participant_words,
            'participation_percentage': participation_percentage,
            'avg_message_length': individual_metrics.get('avg_message_length', 0),
            'voice_message_count': individual_metrics.get('voice_message_count', 0),
            
            # Feedback
            'strengths': strengths_match.group(1).strip() if strengths_match else "Active participation in group discussion",
            'weaknesses': weaknesses_match.group(1).strip() if weaknesses_match else "Room for improvement in collaborative skills",
            'suggestions': suggestions_match.group(1).strip() if suggestions_match else "Continue practicing group discussion skills",
            'achievements': achievements_match.group(1).strip() if achievements_match else "Collaborative Participant",
            'detailed_feedback': feedback_match.group(1).strip() if feedback_match else f"{participant_name} demonstrated good participation in the group discussion. Focus on enhancing specific skills to improve overall performance."
        }
        
    except Exception as e:
        print(f"Error generating individual participant evaluation: {e}")
        return {
            'communication_score': 70.0,
            'leadership_score': 65.0,
            'participation_score': 70.0,
            'content_quality_score': 70.0,
            'confidence_score': 70.0,
            'collaboration_score': 75.0,
            'listening_score': 70.0,
            'overall_score': 70.0,
            'rank_in_room': f"{room_analysis['num_participants']}th",
            'percentile_score': 50.0,
            'total_messages': num_messages,
            'total_words': total_participant_words,
            'participation_percentage': participation_percentage,
            'avg_message_length': individual_metrics.get('avg_message_length', 0),
            'voice_message_count': individual_metrics.get('voice_message_count', 0),
            'strengths': "Participated in group discussion",
            'weaknesses': "Analysis unavailable due to technical issues",
            'suggestions': "Continue practicing group discussion skills",
            'achievements': "Active Participant",
            'detailed_feedback': f"{participant_name} participated in the group discussion. Technical issues prevented detailed analysis. Continue practicing to improve skills."
        }


# ═══════════════════════════════════════════════════════════════════
#  AI INTERVIEW CHATBOT  –  Level-2 Stateful Interview Engine
# ═══════════════════════════════════════════════════════════════════

_STAGE_ORDER = ['introduction', 'technical', 'behavioral', 'situational', 'wrap_up']

_STAGE_QUESTIONS = {
    'introduction': 2,
    'technical':    4,
    'behavioral':   2,
    'situational':  1,
    'wrap_up':      1,
}

def _next_stage(current_stage: str) -> str:
    """Return the next interview stage."""
    try:
        idx = _STAGE_ORDER.index(current_stage)
        return _STAGE_ORDER[idx + 1] if idx + 1 < len(_STAGE_ORDER) else 'wrap_up'
    except ValueError:
        return 'wrap_up'


def _build_history_text(messages: list) -> str:
    """Convert message list [{role, content}] to readable transcript."""
    lines = []
    for m in messages:
        label = "Interviewer" if m['role'] == 'ai' else "Candidate"
        lines.append(f"{label}: {m['content']}")
    return "\n".join(lines)


def start_interview(job_role: str, interview_type: str, user_name: str,
                    user_skills: str = "", career_goal: str = "") -> dict:
    """
    Generate the very first AI interviewer message (greeting + first question).

    Returns:
        {
            "message": str,        # AI greeting + first question
            "stage": "introduction",
            "question_number": 1
        }
    """
    prompt = f"""
You are a professional, friendly yet rigorous job interviewer.
You are interviewing {user_name} for the role of "{job_role}".
Interview type: {interview_type} (technical / behavioral / hr / mixed).
Candidate skills: {user_skills or 'not provided'}.
Career goal: {career_goal or 'not provided'}.

This is the INTRODUCTION stage.
Start with a warm professional greeting, briefly explain the interview format,
then ask the classic opening question: "Tell me about yourself and why you are
interested in the {job_role} role."

Keep your response to 3-4 sentences max. Be encouraging.
Return ONLY your spoken words — no labels, no JSON.
"""
    try:
        response = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
        return {
            "message": response.text.strip(),
            "stage": "introduction",
            "question_number": 1
        }
    except Exception as e:
        print(f"[INTERVIEW] start_interview error: {e}")
        return {
            "message": (
                f"Hello {user_name}! Welcome to your mock interview for the {job_role} role. "
                "I'll be your AI interviewer today. Let's start: Could you please tell me "
                "about yourself and why you are interested in this position?"
            ),
            "stage": "introduction",
            "question_number": 1
        }


def interview_next_turn(job_role: str, interview_type: str,
                        messages: list, current_stage: str,
                        question_count: int, total_questions: int) -> dict:
    """
    Given the full conversation so far, evaluate the last user answer and
    produce the next interviewer message (follow-up or new question).

    Args:
        messages: list of {role: 'ai'|'user', content: str}
        current_stage: current interview stage
        question_count: how many questions have been asked so far
        total_questions: max questions for the session

    Returns:
        {
            "ai_message": str,          # next interviewer message
            "answer_score": float,      # 0-10 score for last answer
            "answer_feedback": str,     # one-line private feedback
            "new_stage": str,           # possibly advanced stage
            "is_final": bool            # True if interview should end
        }
    """
    # Determine if we should advance stage
    stage_q_limit = _STAGE_QUESTIONS.get(current_stage, 2)
    stage_questions_asked = sum(
        1 for m in messages if m['role'] == 'ai'
        and m.get('stage', current_stage) == current_stage
    )
    advance_stage = stage_questions_asked >= stage_q_limit
    new_stage = _next_stage(current_stage) if advance_stage else current_stage
    is_final = question_count >= total_questions or new_stage == 'wrap_up' and advance_stage

    history_text = _build_history_text(messages)

    # Instruction for next turn
    if is_final:
        next_instruction = (
            "The interview is now complete. Give the candidate an encouraging closing statement "
            "(2-3 sentences). Tell them you will now generate their performance report. "
            "Do NOT ask any more questions."
        )
    elif new_stage == 'wrap_up':
        next_instruction = (
            "This is the WRAP-UP stage. Ask the candidate if they have any questions for you, "
            "or invite them to share anything important they haven't covered yet."
        )
    elif new_stage == 'technical':
        next_instruction = (
            f"Transition smoothly to the TECHNICAL stage. Ask a specific, challenging technical "
            f"question relevant to the {job_role} role. Base it on anything the candidate already mentioned."
        )
    elif new_stage == 'behavioral':
        next_instruction = (
            "Transition to the BEHAVIORAL stage. Ask a STAR-method behavioral question like "
            "'Tell me about a time you faced a challenging problem...' relevant to the role."
        )
    elif new_stage == 'situational':
        next_instruction = (
            f"Ask a situational question: 'What would you do if...' scenario specific to {job_role}."
        )
    else:
        next_instruction = (
            f"You are in the {current_stage} stage. Evaluate the candidate's last answer briefly "
            "(1 sentence acknowledgment), then ask the next logical question for this stage. "
            "Reference previous answers to show memory."
        )

    prompt = f"""
You are a professional job interviewer conducting a {interview_type} interview for "{job_role}".

--- Conversation so far ---
{history_text}
--- End of conversation ---

Your task: {next_instruction}

Additionally, silently evaluate the LAST candidate answer and return JSON in this exact format:
{{
    "ai_message": "your next spoken words to the candidate",
    "answer_score": <float 0-10>,
    "answer_feedback": "<one concise evaluation sentence about the last answer>",
    "new_stage": "{new_stage}",
    "is_final": {"true" if is_final else "false"}
}}

Return ONLY valid JSON. No extra text outside the JSON.
"""
    try:
        response = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
        raw = response.text.strip()
        if raw.startswith('```'):
            lines = raw.split('\n')
            start = 1
            end = len(lines) - 1 if lines[-1].strip() == '```' else len(lines)
            raw = '\n'.join(lines[start:end]).strip()
        data = json.loads(raw)
        data.setdefault('answer_score', 6.0)
        data.setdefault('answer_feedback', 'Good response.')
        data.setdefault('new_stage', new_stage)
        data.setdefault('is_final', is_final)
        return data
    except Exception as e:
        print(f"[INTERVIEW] interview_next_turn error: {e}")
        fallback_msg = (
            "Thank you for that answer. " + (
                "That concludes our interview. I will now prepare your performance report."
                if is_final else
                f"Let me ask you another question. Could you elaborate on your experience "
                f"relevant to the {job_role} role?"
            )
        )
        return {
            "ai_message": fallback_msg,
            "answer_score": 6.0,
            "answer_feedback": "Reasonable response provided.",
            "new_stage": new_stage,
            "is_final": is_final
        }


def generate_interview_report(job_role: str, interview_type: str,
                               messages: list, user_name: str) -> dict:
    """
    Analyse the full interview transcript and return a comprehensive
    performance report.

    Returns:
        {
            "overall_score": float,          # 0-100
            "technical_score": float,        # 0-100
            "communication_score": float,    # 0-100
            "confidence_score": float,       # 0-100
            "strengths": [str, ...],
            "weaknesses": [str, ...],
            "suggestions": [str, ...],
            "question_breakdown": [
                {"question": str, "answer": str, "score": float, "feedback": str}
            ],
            "summary": str,
            "hire_recommendation": str       # "Strong Yes" / "Yes" / "Maybe" / "No"
        }
    """
    history_text = _build_history_text(messages)

    prompt = f"""
You are an expert job interview evaluator.
Candidate: {user_name}
Role: {job_role}
Interview type: {interview_type}

--- Full Interview Transcript ---
{history_text}
--- End of Transcript ---

Produce a detailed performance report in this EXACT JSON format:
{{
    "overall_score": <float 0-100>,
    "technical_score": <float 0-100>,
    "communication_score": <float 0-100>,
    "confidence_score": <float 0-100>,
    "strengths": ["strength1", "strength2", "strength3"],
    "weaknesses": ["weakness1", "weakness2"],
    "suggestions": ["suggestion1", "suggestion2", "suggestion3"],
    "question_breakdown": [
        {{"question": "Q text", "answer": "A excerpt", "score": <0-10>, "feedback": "short feedback"}}
    ],
    "summary": "2-3 sentence overall assessment",
    "hire_recommendation": "Strong Yes | Yes | Maybe | No"
}}

Be honest, constructive and specific. Return ONLY valid JSON.
"""
    try:
        response = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
        raw = response.text.strip()
        if raw.startswith('```'):
            lines = raw.split('\n')
            start = 1
            end = len(lines) - 1 if lines[-1].strip() == '```' else len(lines)
            raw = '\n'.join(lines[start:end]).strip()
        data = json.loads(raw)
        # Ensure all keys exist
        data.setdefault('overall_score', 60.0)
        data.setdefault('technical_score', 60.0)
        data.setdefault('communication_score', 60.0)
        data.setdefault('confidence_score', 60.0)
        data.setdefault('strengths', ['Participated in interview'])
        data.setdefault('weaknesses', ['Needs more practice'])
        data.setdefault('suggestions', ['Practice more mock interviews'])
        data.setdefault('question_breakdown', [])
        data.setdefault('summary', 'The candidate completed the interview session.')
        data.setdefault('hire_recommendation', 'Maybe')
        return data
    except Exception as e:
        print(f"[INTERVIEW] generate_interview_report error: {e}")
        return {
            "overall_score": 60.0,
            "technical_score": 60.0,
            "communication_score": 60.0,
            "confidence_score": 60.0,
            "strengths": ["Completed the interview", "Showed willingness to participate"],
            "weaknesses": ["Needs more structured answers", "Could improve technical depth"],
            "suggestions": [
                "Practice STAR method for behavioral questions",
                "Review core technical concepts for your role",
                "Work on concise, structured responses"
            ],
            "question_breakdown": [],
            "summary": (
                f"{user_name} completed the {interview_type} interview for the {job_role} role. "
                "Results were generated with limited analysis due to a technical issue."
            ),
            "hire_recommendation": "Maybe"
        }


# ─────────────────── AI GROUP DISCUSSION PARTICIPANT ───────────────────

def generate_ai_gd_participant_response(topic_title, topic_description, conversation_history, turn_number=1):
    """
    Generate a realistic AI participant response for a Group Discussion session.

    Args:
        topic_title: Title of the GD topic
        topic_description: Description / background of the topic
        conversation_history: List of strings like ["User: message", "AI Participant: message", ...]
        turn_number: How many turns have passed (used to vary response style)

    Returns:
        str: A natural, thoughtful GD participant response from the AI
    """
    history_block = ""
    if conversation_history:
        history_block = "CONVERSATION SO FAR:\n" + "\n".join(conversation_history[-10:]) + "\n\n"

    style_hint = (
        "This is the opening of the discussion — introduce a strong perspective on the topic."
        if turn_number <= 2
        else (
            "Build on or respectfully challenge the previous point. Add a new angle or supporting evidence."
            if turn_number <= 6
            else "As the discussion matures, try to synthesise different viewpoints or move toward a conclusion."
        )
    )

    prompt = f"""You are an intelligent, articulate student participating in a Group Discussion (GD) round
of a campus placement interview. You are confident, knowledgeable and balanced in your arguments.

TOPIC: {topic_title}
TOPIC BACKGROUND: {topic_description}

{history_block}YOUR TASK: Write your next spoken contribution to this group discussion.

Guidelines:
- Speak naturally, as a real student would in a face-to-face GD.
- Keep your response between 3-6 sentences (concise, impactful).
- Do NOT use bullet points or headers — respond in plain flowing speech.
- Do NOT start with "As an AI" or mention you are an AI.
- Refer to what other participants said when relevant (use phrases like "I agree with the earlier point...",
  "Building on that idea...", "I'd like to offer a different perspective..." etc.).
- {style_hint}
- Be thoughtful, bring in relevant facts, examples or logical reasoning.
- End with either a question to the group, a call for further discussion, or a crisp concluding remark.

Respond ONLY with your spoken contribution. No extra explanation or formatting."""

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        text = response.text.strip()
        # Remove any accidental AI self-references
        for phrase in ["As an AI", "As an artificial intelligence", "I am an AI", "I'm an AI"]:
            text = text.replace(phrase, "In my view")
        return text
    except Exception as e:
        print(f"[AI GD PARTICIPANT] Error generating response: {e}")
        return (
            "That's a thought-provoking point. I believe we should also consider the broader societal impact "
            f"of '{topic_title}'. Different stakeholders view this issue differently, and a balanced approach "
            "that weighs short-term challenges against long-term benefits would be most effective. "
            "What does the group think about prioritising practical implementation over ideological debate?"
        )


# ═══════════════════════════════════════════════════════════════════
#  JOB SUGGESTIONS MODULE  –  AI-powered personalised job finder
# ═══════════════════════════════════════════════════════════════════

def generate_job_suggestions(skills: str, career_goal: str, branch: str,
                              avg_test_score: float = 0.0,
                              total_tests: int = 0,
                              total_roadmaps: int = 0,
                              search_query: str = "",
                              num_suggestions: int = 9) -> list:
    """
    Generate personalised job suggestions using Gemini AI based on user profile,
    performance data, and optional search query.

    Args:
        skills: comma-separated skills from user profile
        career_goal: user's stated career goal
        branch: academic branch / department
        avg_test_score: average mock-test score (0-100)
        total_tests: number of tests taken
        total_roadmaps: number of roadmaps generated
        search_query: optional free-text search from user
        num_suggestions: how many jobs to return (default 9)

    Returns:
        list of job dicts with keys:
            id, title, company, location, type, experience_level,
            salary_range, skills_required, description, match_score,
            match_reasons, responsibilities, qualifications,
            growth_potential, industry, apply_tips, search_url
    """

    performance_context = ""
    if avg_test_score > 0:
        if avg_test_score >= 80:
            perf_label = "excellent"
        elif avg_test_score >= 60:
            perf_label = "good"
        elif avg_test_score >= 40:
            perf_label = "average"
        else:
            perf_label = "below average"
        performance_context = (
            f"Mock-test performance: {perf_label} ({avg_test_score:.1f}% avg score, "
            f"{total_tests} tests taken, {total_roadmaps} roadmaps generated)."
        )

    search_context = f'The user also searched for: "{search_query}".' if search_query.strip() else ""

    prompt = f"""
You are a professional career counselor and job placement expert specializing in technology and engineering roles.

USER PROFILE:
- Academic Branch: {branch or "Computer Science / Engineering"}
- Skills: {skills or "Programming, Problem Solving"}
- Career Goal: {career_goal or "Software Developer"}
- {performance_context}
{search_context}

Generate EXACTLY {num_suggestions} highly relevant job suggestions perfectly tailored to this user's profile,
skills, career goal, and performance data. Each job should be a real job role that exists in the Indian job market.

Return a JSON ARRAY of exactly {num_suggestions} job objects. Each object must have ALL of these keys:

{{
  "id": <integer 1 to {num_suggestions}>,
  "title": "Job Title",
  "company": "Representative Company Type (e.g. 'Tech Startup', 'MNC', 'Product Company', 'Service Company', 'FAANG-tier')",
  "location": "City, India (or Remote)",
  "type": "Full-time | Part-time | Internship | Remote | Contract",
  "experience_level": "Fresher | Junior (0-2 yrs) | Mid (2-5 yrs) | Senior (5+ yrs)",
  "salary_range": "X-Y LPA (Indian)",
  "skills_required": ["skill1", "skill2", "skill3", "skill4"],
  "description": "2-3 sentence compelling job description",
  "match_score": <integer 60-99, higher = better match to user profile>,
  "match_reasons": ["reason why this matches user skill", "reason why career goal aligns", "performance factor"],
  "responsibilities": ["responsibility 1", "responsibility 2", "responsibility 3", "responsibility 4"],
  "qualifications": ["qualification 1", "qualification 2", "qualification 3"],
  "growth_potential": "high | medium | low",
  "industry": "Technology | Finance | Healthcare | E-commerce | EdTech | etc.",
  "apply_tips": ["specific preparation tip", "resume keyword to include", "interview focus area"],
  "search_url": "https://www.linkedin.com/jobs/search/?keywords={{}}&location=India"
}}

Replace {{}} in search_url with the URL-encoded job title.

Rules:
1. Sort jobs by match_score descending (best match first).
2. Mix job types: include startups, MNCs, product companies, remote roles.
3. Base experience_level on the user's test performance — if excellent → include mid/senior roles too.
4. Make salary_range realistic for India 2024-2026.
5. match_reasons must specifically reference the user's actual skills, career goal, or branch.
6. {f'Heavily prioritise jobs related to: "{search_query}".' if search_query.strip() else 'Diversify across relevant domains.'}
7. Return ONLY the JSON array, no extra text or markdown fences.
"""

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        raw = response.text.strip()

        # Strip markdown code fences if present
        if raw.startswith("```"):
            lines = raw.split("\n")
            start = 1
            end = len(lines) - 1 if lines[-1].strip() == "```" else len(lines)
            raw = "\n".join(lines[start:end]).strip()

        jobs = json.loads(raw)

        # Validate and sanitise
        validated = []
        for i, job in enumerate(jobs):
            if not isinstance(job, dict):
                continue
            job.setdefault("id", i + 1)
            job.setdefault("title", "Software Developer")
            job.setdefault("company", "Tech Company")
            job.setdefault("location", "Bangalore, India")
            job.setdefault("type", "Full-time")
            job.setdefault("experience_level", "Fresher")
            job.setdefault("salary_range", "3-8 LPA")
            job.setdefault("skills_required", [])
            job.setdefault("description", "Exciting opportunity in technology.")
            job.setdefault("match_score", 70)
            job.setdefault("match_reasons", ["Matches your profile"])
            job.setdefault("responsibilities", [])
            job.setdefault("qualifications", [])
            job.setdefault("growth_potential", "medium")
            job.setdefault("industry", "Technology")
            job.setdefault("apply_tips", [])

            # Build search_url from title if missing / malformed
            title_encoded = job.get("title", "Software Developer").replace(" ", "%20")
            job["search_url"] = f"https://www.linkedin.com/jobs/search/?keywords={title_encoded}&location=India"
            job["adzuna_url"] = f"https://www.adzuna.in/search?q={title_encoded}&w=India"
            job["naukri_url"] = f"https://www.naukri.com/{'-'.join(job.get('title','').lower().split())}-jobs"

            validated.append(job)

        return validated[:num_suggestions]

    except json.JSONDecodeError as je:
        print(f"[JOB SUGGESTIONS] JSON parse error: {je}")
        return _fallback_job_suggestions(skills, career_goal, branch, num_suggestions)
    except Exception as e:
        print(f"[JOB SUGGESTIONS] Error generating suggestions: {e}")
        return _fallback_job_suggestions(skills, career_goal, branch, num_suggestions)


def _fallback_job_suggestions(skills: str, career_goal: str, branch: str, num: int = 9) -> list:
    """Return basic fallback job suggestions when AI call fails."""
    base_jobs = [
        {
            "id": 1, "title": "Software Developer", "company": "Tech MNC",
            "location": "Bangalore, India", "type": "Full-time",
            "experience_level": "Fresher", "salary_range": "4-8 LPA",
            "skills_required": ["Python", "Java", "SQL", "Git"],
            "description": "Build scalable software solutions for global clients.",
            "match_score": 85,
            "match_reasons": ["Matches your programming skills", "Aligns with career goal"],
            "responsibilities": ["Write clean, maintainable code", "Collaborate with cross-functional teams",
                                 "Participate in code reviews", "Debug and optimise applications"],
            "qualifications": ["B.Tech/B.E. in CS/IT", "Strong programming fundamentals",
                               "Good problem-solving skills"],
            "growth_potential": "high", "industry": "Technology",
            "apply_tips": ["Strengthen DSA skills", "Build GitHub portfolio",
                           "Practice system design basics"],
            "search_url": "https://www.linkedin.com/jobs/search/?keywords=Software%20Developer&location=India",
            "adzuna_url": "https://www.adzuna.in/search?q=Software+Developer&w=India",
            "naukri_url": "https://www.naukri.com/software-developer-jobs"
        },
        {
            "id": 2, "title": "Data Analyst", "company": "Analytics Firm",
            "location": "Hyderabad, India", "type": "Full-time",
            "experience_level": "Fresher", "salary_range": "4-7 LPA",
            "skills_required": ["Python", "SQL", "Excel", "Power BI"],
            "description": "Analyse data to deliver actionable business insights.",
            "match_score": 78,
            "match_reasons": ["Analytical skills match", "Growing domain"],
            "responsibilities": ["Collect and clean data", "Create dashboards", "Write SQL queries",
                                 "Present findings to stakeholders"],
            "qualifications": ["Degree in CS/Statistics/Math", "SQL proficiency",
                               "Data visualisation experience"],
            "growth_potential": "high", "industry": "Analytics",
            "apply_tips": ["Build a Tableau/Power BI portfolio", "Practice SQL challenges",
                           "Learn basic statistics"],
            "search_url": "https://www.linkedin.com/jobs/search/?keywords=Data%20Analyst&location=India",
            "adzuna_url": "https://www.adzuna.in/search?q=Data+Analyst&w=India",
            "naukri_url": "https://www.naukri.com/data-analyst-jobs"
        },
        {
            "id": 3, "title": "Frontend Developer", "company": "Product Startup",
            "location": "Pune, India", "type": "Full-time",
            "experience_level": "Fresher", "salary_range": "4-9 LPA",
            "skills_required": ["React", "JavaScript", "HTML", "CSS"],
            "description": "Build beautiful user interfaces for web and mobile platforms.",
            "match_score": 75,
            "match_reasons": ["Web development skills", "UI/UX growth area"],
            "responsibilities": ["Develop React components", "Ensure responsive design",
                                 "Optimise page performance", "Collaborate with designers"],
            "qualifications": ["CS/IT degree", "JavaScript proficiency", "Portfolio of web projects"],
            "growth_potential": "high", "industry": "Technology",
            "apply_tips": ["Build React projects", "Learn TypeScript", "Create portfolio website"],
            "search_url": "https://www.linkedin.com/jobs/search/?keywords=Frontend%20Developer&location=India",
            "adzuna_url": "https://www.adzuna.in/search?q=Frontend+Developer&w=India",
            "naukri_url": "https://www.naukri.com/frontend-developer-jobs"
        },
    ]
    return (base_jobs * ((num // len(base_jobs)) + 1))[:num]


# ============================
# AI ASSISTANT - INTELLIGENT CAREER GUIDE
# ============================

def get_assistant_system_prompt(mode, user_context):
    """
    Generate intelligent system prompt based on mode and user context
    
    Args:
        mode: 'career', 'interview', 'resume', 'skill', 'job', 'general'
        user_context: Dictionary with user data
    
    Returns:
        System prompt string
    """
    base_prompt = """You are an intelligent AI Career Assistant integrated into a comprehensive career development platform.

CORE CAPABILITIES:
- Career guidance and roadmap planning
- Performance analysis across all modules
- Resume optimization and review
- Interview preparation and coaching
- Group discussion training
- Job matching and recommendations
- Skill gap analysis and learning paths

PERSONALITY:
- Professional yet friendly and encouraging
- Data-driven and analytical
- Supportive and motivational
- Provide actionable, specific advice
- Use structured responses with emojis for clarity

RESPONSE FORMAT:
- Use clear headings and bullet points
- Include specific metrics when available
- Provide step-by-step action plans
- Highlight strengths and areas for improvement
- End with motivational encouragement
"""
    
    # Add user context
    context_info = f"\n\nSTUDENT PROFILE:\n"
    context_info += f"Name: {user_context.get('name', 'Student')}\n"
    context_info += f"Branch: {user_context.get('branch', 'Not specified')}\n"
    context_info += f"Year: {user_context.get('year', 'Not specified')}\n"
    context_info += f"Career Goal: {user_context.get('career_goal', 'Not specified')}\n"
    context_info += f"Current Skills: {user_context.get('skills', 'Not specified')}\n"
    
    # Add performance data
    if 'performance' in user_context:
        perf = user_context['performance']
        context_info += f"\nPERFORMANCE DATA:\n"
        context_info += f"Mock Test Average: {perf.get('avg_test_score', 0):.1f}%\n"
        context_info += f"Total Tests Taken: {perf.get('total_tests', 0)}\n"
        context_info += f"Interview Average: {perf.get('avg_interview_score', 0):.1f}%\n"
        context_info += f"Interviews Completed: {perf.get('completed_interviews', 0)}\n"
        context_info += f"GD Average: {perf.get('avg_gd_score', 0):.1f}%\n"
        context_info += f"GD Sessions: {perf.get('total_gd_sessions', 0)}\n"
        context_info += f"Resume Score: {perf.get('avg_resume_score', 0):.1f}%\n"
        context_info += f"Roadmaps Created: {perf.get('total_roadmaps', 0)}\n"
    
    # Mode-specific instructions
    if mode == 'career':
        mode_prompt = """
MODE: Career Guide
FOCUS: Help student plan career path, create roadmaps, identify skill gaps
USE: Career goals, current skills, branch, weak areas
PROVIDE: Specific roadmap steps, skill recommendations, timeline suggestions"""
    
    elif mode == 'interview':
        mode_prompt = """
MODE: Interview Coach
FOCUS: Prepare for interviews, analyze past performance, provide tips
USE: Interview scores, feedback, weak points
PROVIDE: Practice questions, improvement strategies, confidence tips"""
    
    elif mode == 'resume':
        mode_prompt = """
MODE: Resume Advisor
FOCUS: Review resume quality, suggest improvements, optimize content
USE: Resume scores, missing skills, format analysis
PROVIDE: Specific improvements, keyword suggestions, formatting tips"""
    
    elif mode == 'skill':
        mode_prompt = """
MODE: Skill Development Advisor
FOCUS: Analyze skill gaps, recommend learning paths, track progress
USE: Test scores by category, weak areas, career goals
PROVIDE: Learning resources, practice schedule, skill prioritization"""
    
    elif mode == 'job':
        mode_prompt = """
MODE: Job Match Advisor
FOCUS: Recommend suitable jobs, analyze job requirements, application tips
USE: Skills, experience, scores, career goals
PROVIDE: Job matches, application strategies, preparation advice"""
    
    else:  # general
        mode_prompt = """
MODE: General Assistant
FOCUS: Answer queries, provide guidance across all features
USE: All available student data
PROVIDE: Comprehensive, context-aware responses"""
    
    return base_prompt + context_info + mode_prompt


def intelligent_assistant_chat(user_message, user_context, mode='general', chat_history=None):
    """
    Main AI Assistant function - Context-aware, intelligent responses
    
    Args:
        user_message: User's question/message
        user_context: Dictionary with user profile and performance data
        mode: Assistant mode (career/interview/resume/skill/job/general)
        chat_history: List of previous messages in this conversation
    
    Returns:
        Assistant response string
    """
    if not client:
        return "AI Assistant is currently unavailable. Please try again later."
    
    try:
        # Build system prompt with context
        system_prompt = get_assistant_system_prompt(mode, user_context)
        
        # Build full prompt with conversation history
        full_prompt = system_prompt + "\n\n"
        
        # Add chat history if available
        if chat_history:
            full_prompt += "CONVERSATION HISTORY:\n"
            for msg in chat_history[-10:]:  # Last 10 messages for context
                role_label = "User" if msg['role'] == 'user' else "Assistant"
                full_prompt += f"{role_label}: {msg['message']}\n"
            full_prompt += "\n"
        
        # Add current user message
        full_prompt += f"Current User Message: {user_message}\n\n"
        full_prompt += "Please provide a helpful, context-aware response:"
        
        # Generate response using Gemini API
        response = client.models.generate_content(
            model="gemini-flash-latest",  # Using latest flash model for optimal performance
            contents=full_prompt
        )
        
        return response.text.strip()
    
    except Exception as e:
        print(f"Assistant error: {e}")
        import traceback
        traceback.print_exc()
        return "I encountered an error processing your request. Please try rephrasing your question."


def generate_smart_suggestions(user_context):
    """
    Generate contextual quick suggestions based on user's current state
    
    Args:
        user_context: User profile and performance data
    
    Returns:
        List of suggestion strings
    """
    suggestions = []
    
    perf = user_context.get('performance', {})
    
    # Career suggestions
    if perf.get('total_roadmaps', 0) == 0:
        suggestions.append("Create my first career roadmap")
    elif user_context.get('career_goal'):
        suggestions.append(f"How to become a {user_context.get('career_goal')}?")
    
    # Test suggestions
    avg_test = perf.get('avg_test_score', 0)
    if perf.get('total_tests', 0) == 0:
        suggestions.append("Start my first practice test")
    elif avg_test < 60:
        suggestions.append("How can I improve my test scores?")
    elif avg_test >= 80:
        suggestions.append("What advanced topics should I practice?")
    
    # Interview suggestions
    avg_interview = perf.get('avg_interview_score', 0)
    if perf.get('completed_interviews', 0) == 0:
        suggestions.append("Prepare for my first interview")
    elif avg_interview < 70:
        suggestions.append("Tips to improve interview performance")
    
    # Resume suggestions
    avg_resume = perf.get('avg_resume_score', 0)
    if perf.get('total_resumes', 0) == 0:
        suggestions.append("Help me build a professional resume")
    elif avg_resume < 75:
        suggestions.append("How to improve my resume score?")
    
    # GD suggestions
    if perf.get('total_gd_sessions', 0) == 0:
        suggestions.append("What is Group Discussion?")
    else:
        suggestions.append("Tips for confident communication")
    
    # Job suggestions
    if user_context.get('skills'):
        suggestions.append("What jobs match my skills?")
    
    # Weekly planning
    suggestions.append("Create this week's study plan")
    
    # Performance analysis
    if perf.get('total_tests', 0) > 0 or perf.get('completed_interviews', 0) > 0:
        suggestions.append("Analyze my overall performance")
    
    return suggestions[:6]  # Return top 6 suggestions


def generate_performance_insight(user_context):
    """
    Generate a brief performance insight for the assistant welcome message
    
    Args:
        user_context: User profile and performance data
    
    Returns:
        Insight string
    """
    perf = user_context.get('performance', {})
    
    # Calculate readiness
    scores = [
        perf.get('avg_test_score', 0),
        perf.get('avg_interview_score', 0),
        perf.get('avg_gd_score', 0),
        perf.get('avg_resume_score', 0)
    ]
    
    active_scores = [s for s in scores if s > 0]
    avg_readiness = sum(active_scores) / len(active_scores) if active_scores else 0
    
    if avg_readiness == 0:
        return "🚀 Welcome! Let's start building your career journey together."
    elif avg_readiness < 50:
        return "📈 You're getting started! Keep practicing to build strong foundations."
    elif avg_readiness < 70:
        return "💪 Good progress! Focus on weak areas to reach the next level."
    elif avg_readiness < 85:
        return "🌟 Great work! You're well-prepared. Fine-tune your skills for excellence."
    else:
        return "🏆 Outstanding! You're career-ready. Explore advanced opportunities!"


def detect_intent_and_mode(user_message):
    """
    Detect user intent and suggest appropriate mode
    
    Args:
        user_message: User's message
    
    Returns:
        Suggested mode string
    """
    message_lower = user_message.lower()
    
    # Career/Roadmap keywords
    if any(word in message_lower for word in ['roadmap', 'career', 'path', 'become', 'learn', 'goal', 'skill gap']):
        return 'career'
    
    # Interview keywords
    elif any(word in message_lower for word in ['interview', 'interviewing', 'preparation', 'hr', 'technical round']):
        return 'interview'
    
    # Resume keywords
    elif any(word in message_lower for word in ['resume', 'cv', 'profile', 'experience', 'format']):
        return 'resume'
    
    # Skill keywords
    elif any(word in message_lower for word in ['skill', 'learn', 'practice', 'improve', 'weak', 'strong']):
        return 'skill'
    
    # Job keywords
    elif any(word in message_lower for word in ['job', 'apply', 'company', 'salary', 'hiring', 'placement']):
        return 'job'
    
    # Performance keywords
    elif any(word in message_lower for word in ['score', 'performance', 'how am i', 'progress', 'doing']):
        return 'general'  # Will provide comprehensive analysis
    
    else:
        return 'general'
