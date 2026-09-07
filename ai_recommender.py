import os
from dotenv import load_dotenv
from google import genai

# Load environment variables
load_dotenv()

# Get Gemini API key
API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    raise ValueError("GEMINI_API_KEY is not set in .env file")

# Create Gemini client
client = genai.Client(api_key=API_KEY)


def generate_recommendation(target_role, matched_skills, missing_skills):
    """
    Generate personalized career recommendations using Gemini AI.
    """

    matched_text = ", ".join(matched_skills) if matched_skills else "None"
    missing_text = ", ".join(missing_skills) if missing_skills else "None"

    prompt = f"""
You are an AI Career Recommendation Assistant.

Target Job Role:
{target_role}

Student's Existing Skills:
{matched_text}

Student's Missing Skills:
{missing_text}

Create a personalized learning recommendation for this student.

Provide the response in the following format:

1. Skill Priority
- List the missing skills in learning priority order.

2. Learning Roadmap
- Give a step-by-step roadmap from beginner to advanced.
- Mention what the student should learn first, second, third, etc.

3. Learning Topics
- Mention important topics for each missing skill.

4. Project Recommendations
- Suggest practical projects that the student can build.

5. Career Advice
- Give short advice on how the student can prepare for the target role.

Keep the response practical, clear and suitable for a college student.
"""

    interaction = client.interactions.create(
        model="gemini-3.6-flash",
        input=prompt
    )

    return interaction.output_text


if __name__ == "__main__":

    target_role = "AI/ML Engineer"

    matched_skills = [
        "Python",
        "Machine Learning",
        "Git",
        "Docker"
    ]

    missing_skills = [
        "Deep Learning",
        "Pandas",
        "NumPy",
        "Scikit-learn",
        "TensorFlow",
        "PyTorch"
    ]

    recommendation = generate_recommendation(
        target_role,
        matched_skills,
        missing_skills
    )

    print("\n===== AI PERSONALIZED RECOMMENDATION =====\n")
    print(recommendation)