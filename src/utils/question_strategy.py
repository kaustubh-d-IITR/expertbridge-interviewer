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
    
    # Start building the strategy text
    strategy = f"""
EXPERT CONTEXT - USE THIS TO PERSONALIZE YOUR QUESTIONS:

Name: {name}
Top Skills: {", ".join(skills)}
Industries: {", ".join(industries)}
Experience Level: {years} years
Current Role: {role}
"""
    
    # Add past companies if available
    if companies:
        strategy += f"Notable Companies: {', '.join(companies)}\n"
    
    # Add key project if available
    if project and isinstance(project, dict) and project.get("title"):
        strategy += f"\nKey Project: {project.get('title')} - {project.get('impact', '')}\n"
    elif isinstance(project, str) and project:
         strategy += f"\nKey Project: {project}\n"
    
    # Now add ADAPTIVE RULES based on their profile
    strategy += "\n--- PERSONALIZED QUESTION STRATEGY ---\n"
    
    # Rule 1: Adjust question depth based on experience
    if years >= 10:
        strategy += """
→ SENIOR LEVEL (10+ years):
  - Ask about LEADERSHIP: "Tell me about a time you built or managed a team"
  - Ask about STRATEGY: "How do you approach strategic decisions in your domain?"
  - Ask about MENTORSHIP: "How do you develop junior team members?"
  - Focus on: High-level thinking, business impact, scaling challenges
"""
    elif years >= 5:
        strategy += """
→ MID LEVEL (5-10 years):
  - Balance technical depth + collaboration
  - Ask: "Walk me through a complex problem you solved"
  - Ask: "How do you work with cross-functional teams?"
  - Focus on: Execution excellence, ownership, growing scope
"""
    else:
        strategy += """
→ JUNIOR LEVEL (0-5 years):
  - Ask about EXECUTION: "Describe a challenging task you completed"
  - Ask about LEARNING: "What's the hardest skill you've had to learn?"
  - Ask about GROWTH: "Where do you want to be in 2 years?"
  - Focus on: Learning mindset, execution, adaptability, work ethic
"""
    
    # Rule 2: Ask skill-specific deep-dive questions
    strategy += "\n→ SKILL-SPECIFIC QUESTIONS (Mix these in):\n"
    
    skill_questions = {
        "M&A": "- Deep dive: 'Walk me through your most complex M&A deal - what was the valuation approach?'",
        "Machine Learning": "- Deep dive: 'Tell me about a time your ML model failed in production - what happened?'",
        "Financial Modeling": "- Deep dive: 'How do you approach building a 3-statement financial model?'",
        "Fundraising": "- Deep dive: 'What's the hardest part of a fundraising process you've navigated?'",
        "Product Management": "- Deep dive: 'How do you prioritize features when everything is urgent?'",
        "Sales": "- Deep dive: 'Tell me about your largest deal - what made it close?'",
        "Marketing": "- Deep dive: 'Walk me through a campaign that didn't work - what did you learn?'",
        "Python": "- Deep dive: 'Describe a complex Python system you architected.'",
        "Java": "- Deep dive: 'How have you handled concurrency issues in Java?'",
        "AWS": "- Deep dive: 'What is your strategy for optimizing AWS costs?'",
    }
    
    found_skill_match = False
    for skill in skills:
        for key, question in skill_questions.items():
            if key.lower() in skill.lower():
                strategy += f"  {question}\n"
                found_skill_match = True
    
    if not found_skill_match:
         strategy += f"  - Ask deep technical questions specific to: {', '.join(skills)}\n"

    # Rule 3: Industry-specific questions
    strategy += "\n→ INDUSTRY-SPECIFIC CONTEXT:\n"
    
    industry_context = {
        "FinTech": "- Ask about: Regulatory challenges, compliance, payment systems, financial infrastructure",
        "SaaS": "- Ask about: Churn, customer retention, pricing strategy, scaling challenges",
        "Healthcare": "- Ask about: HIPAA compliance, patient data, regulatory approval processes",
        "E-commerce": "- Ask about: Logistics, conversion optimization, customer acquisition cost",
        "Crypto": "- Ask about: Security, decentralization trade-offs, tokenomics",
        "Web3": "- Ask about: Smart contract security, gas optimization",
    }
    
    for industry in industries:
        for key, context in industry_context.items():
            if key.lower() in industry.lower():
                strategy += f"  {context}\n"
    
    # Rule 4: Reference their key project as a conversation starter
    if project and ((isinstance(project, dict) and project.get("title")) or isinstance(project, str)):
        proj_title = project.get("title") if isinstance(project, dict) else project
        strategy += f"""
→ OPENING MOVE:
  Start with: "Hi {name}, I saw you worked on {proj_title} - that's impressive! 
  Can you walk me through that experience and what made it successful?"
  
  This makes them comfortable and gets a strong first answer.
"""
    else:
        # Fallback opening
        strategy += f"""
→ OPENING MOVE:
  Start with: "Hi {name}, thanks for joining! I see you have {years} years of experience. 
  What's been the most challenging project you've tackled in your career?"
"""
    
    # Rule 5: Follow-up strategy
    strategy += """
→ FOLLOW-UP RULES (Critical for depth):
  - If they mention metrics: Ask "What moved the needle most?"
  - If they're vague: Ask "Can you give me the before/after numbers?"
  - If they mention a decision: Ask "What alternatives did you consider? Why this one?"
  - If they mention a challenge: Ask "How did you overcome it specifically?"
  
  IMPORTANT: This is a VERBAL interview. Do NOT ask them to write code. Ask conceptual technical questions only.
"""
    
    return strategy
