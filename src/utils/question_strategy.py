def build_question_strategy(expert_profile):
    """
    Takes expert profile and returns personalized interview strategy.
    This tells the AI HOW to interview this specific person.
    """
    
    name = expert_profile.get("name", "Candidate")
    skills = expert_profile.get("top_skills", [])
    if isinstance(skills, str): skills = [s.strip() for s in skills.split(",")]
    
    industries = expert_profile.get("industries", [])
    if isinstance(industries, str): industries = [i.strip() for i in industries.split(",")]
    
    years = expert_profile.get("experience_years", 0)
    role = expert_profile.get("current_role", "Expert")
    companies = expert_profile.get("past_companies", [])
    if isinstance(companies, str): companies = [c.strip() for c in companies.split(",")]
    
    project = expert_profile.get("key_project", {})
    experience = expert_profile.get("key_experience", "")
    
    # Start building the strategy text
    strategy = f"""
EXPERT CONTEXT - USE THIS TO PERSONALIZE YOUR QUESTIONS:

Name: {name}
Top Skills: {", ".join(skills)}
Industries: {", ".join(industries)}
Experience Level: {years} years
Current Role: {role}
"""
    
    if companies:
        strategy += f"Notable Companies: {', '.join(companies)}\n"
    
    if project and isinstance(project, dict) and project.get("title"):
        strategy += f"\nKey Project: {project.get('title')} - {project.get('impact', '')}\n"
    elif isinstance(project, str) and str(project).strip():
         strategy += f"\nKey Project: {project}\n"
         
    if experience and str(experience).strip():
         strategy += f"\nKey Experience: {experience}\n"
    
    strategy += "\n--- PERSONALIZED QUESTION STRATEGY ---\n"
    
    if years >= 10:
        strategy += """
→ SENIOR LEVEL (10+ years):
  - Focus on LEADERSHIP: "Tell me about a time you had to align conflicting stakeholders."
  - Focus on STRATEGY: "How do you decide between building internal tools vs buying?"
  - Focus on MENTORSHIP: "How do you elevate standard engineers to senior levels?"
  - ASSESS: Strategic thinking, business impact, organizational influence.
"""
    elif years >= 5:
        strategy += """
→ MID LEVEL (5-10 years):
  - Focus on ARCHITECTURE: "Walk me through the system design of your last major project."
  - Focus on TRADE-OFFS: "Why did you choose that specific tech stack over alternatives?"
  - Focus on COLLABORATION: "How do you handle disagreements with product managers?"
  - ASSESS: Technical depth, system design, ownership.
"""
    else:
        strategy += """
→ JUNIOR LEVEL (0-5 years):
  - Focus on EXECUTION: "Describe a bug that was hard to track down."
  - Focus on LEARNING: "What is a new technology you learned recently and how?"
  - Focus on FUNDAMENTALS: "Explain a core concept in your primary language."
  - ASSESS: Coding capability, debugging, curiosity.
"""
    
    strategy += "\n→ SKILL-SPECIFIC PROBES (Select 1-2 relevant ones):\n"
    
    skill_questions = {
        "M&A": "- Probe: 'How do you validate synergies in the first 90 days of a deal?'",
        "Machine Learning": "- Probe: 'How do you handle data drift in production models?'",
        "Financial Modeling": "- Probe: 'What are the most common circular reference errors you encounter?'",
        "Fundraising": "- Probe: 'How do you structure the data room for Series B due diligence?'",
        "Product Management": "- Probe: 'Tell me about a feature you killed and why.'",
        "Sales": "- Probe: 'How do you revive a deal that has gone dark?'",
        "Marketing": "- Probe: 'What is your framework for attribution modeling?'",
        "Python": "- Probe: 'Explain how you manage memory in long-running Python processes.'",
        "Java": "- Probe: 'How do you tune the JVM for high-throughput applications?'",
        "AWS": "- Probe: 'How do you design for failure in a multi-region architecture?'",
        "React": "- Probe: 'How do you prevent unnecessary re-renders in large applications?'",
        "SQL": "- Probe: 'How do you optimize a query performing a full table scan on millions of rows?'",
    }
    
    found_skill_match = False
    for skill in skills:
        for key, question in skill_questions.items():
            if key.lower() in skill.lower():
                strategy += f"  {question}\n"
                found_skill_match = True
    
    if not found_skill_match:
         strategy += f"  - Ask 1 deep technical question specific to: {', '.join(skills)}\n"

    strategy += "\n→ INDUSTRY CONTEXT:\n"
    
    industry_context = {
        "FinTech": "- Context: High consistency, regulatory compliance, zero data loss.",
        "SaaS": "- Context: Scalability, multi-tenancy, churn reduction.",
        "Healthcare": "- Context: HIPAA compliance, data privacy, interoperability (HL7/FHIR).",
        "E-commerce": "- Context: High concurrency, conversion optimization, inventory management.",
        "Crypto": "- Context: Trustless systems, gas optimization, security audits.",
        "Web3": "- Context: Decentralization trade-offs, wallet integration.",
    }
    
    for industry in industries:
        for key, context in industry_context.items():
            if key.lower() in industry.lower():
                strategy += f"  {context}\n"
    
    return strategy
