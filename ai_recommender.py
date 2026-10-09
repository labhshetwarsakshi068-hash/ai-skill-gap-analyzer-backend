import os
from dotenv import load_dotenv
from google import genai

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=API_KEY) if API_KEY else None


def generate_recommendation(target_role, matched_skills, missing_skills):
    matched_text = ", ".join(matched_skills) if matched_skills else "None"
    missing_text = ", ".join(missing_skills) if missing_skills else "None"

    prompt = f"""
You are an AI Career Recommendation Assistant.

Target Role: {target_role}
Existing Skills: {matched_text}
Missing Skills: {missing_text}

Write a personalized recommendation using these separate headings:
1. Skill Priority
2. Learning Roadmap
3. Learning Topics
4. Project Recommendations
5. Career Advice

Use clear numbered lists under each heading.
Keep the response practical and suitable for a college student.
"""

    if client:
        try:
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt
            )
            if response.text:
                return response.text.strip()
        except Exception as error:
            print(f"Gemini API unavailable: {error}")

    # Fallback recommendation when Gemini is unavailable
    if missing_skills:
        priority_items = "\n".join(
            f"{i}. {skill}" for i, skill in enumerate(missing_skills, 1)
        )
        roadmap_items = "\n".join(
            f"{i}. Learn {skill}: study the basics, practise with examples, "
            f"and build a small project."
            for i, skill in enumerate(missing_skills, 1)
        )
        topic_items = "\n".join(
            f"- {skill}: fundamentals, practical exercises, and real-world use."
            for skill in missing_skills
        )
    else:
        priority_items = "No missing skills identified."
        roadmap_items = "Practise advanced concepts and build portfolio projects."
        topic_items = "Explore advanced topics related to your target role."

    return f"""## 🎯 Personalized Career Recommendation

**Target Role:** {target_role}

### 1. 🎯 Skill Priority
{priority_items}

### 2. 🗺️ Learning Roadmap
{roadmap_items}

### 3. 📚 Learning Topics
{topic_items}

### 4. 💻 Project Recommendations
1. Build a project related to {target_role} using your existing skills.
2. Gradually integrate the missing skills into the project.
3. Upload your project and documentation to GitHub.

### 5. 🚀 Career Advice
1. Practise coding and problem-solving regularly.
2. Build practical projects and maintain a GitHub portfolio.
3. Prepare for technical interviews related to {target_role}.

*Note: This is a fallback recommendation, not a Gemini-generated response.*
"""


if __name__ == "__main__":
    target_role = "AI/ML Engineer"
    matched_skills = ["Python", "Machine Learning", "Git", "Docker"]
    missing_skills = [
        "Deep Learning",
        "Pandas",
        "NumPy",
        "Scikit-learn",
        "TensorFlow",
        "PyTorch"
    ]

    print(generate_recommendation(
        target_role,
        matched_skills,
        missing_skills
    ))
