import re

SKILLS = [
    "Python",
    "Java",
    "C++",
    "SQL",
    "HTML",
    "CSS",
    "JavaScript",
    "React",
    "Node.js",
    "Flask",
    "Django",
    "Machine Learning",
    "Deep Learning",
    "Data Analysis",
    "Pandas",
    "NumPy",
    "Matplotlib",
    "Scikit-learn",
    "TensorFlow",
    "PyTorch",
    "Git",
    "GitHub",
    "Docker",
    "Kubernetes",
    "AWS"
]


def extract_skills(text):
    """Extract skills from resume text."""

    if not text:
        return []

    found_skills = []
    text_lower = text.lower()

    for skill in SKILLS:

        skill_lower = skill.lower()

        pattern = r"(?<!\w)" + re.escape(skill_lower) + r"(?!\w)"

        if re.search(pattern, text_lower):
            found_skills.append(skill)

    return found_skills


if __name__ == "__main__":

    sample_text = """
    I have knowledge of Python, Java, SQL, Git,
    GitHub, Docker, AWS and Machine Learning.
    """

    print("Detected Skills:")

    for skill in extract_skills(sample_text):
        print("-", skill)