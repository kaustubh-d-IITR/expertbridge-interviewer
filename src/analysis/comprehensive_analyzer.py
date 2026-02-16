from typing import Dict, Any, List
import json
import os
from openai import AzureOpenAI

class ComprehensiveAnalyzer:
    """
    Performs deep post-interview analysis.
    """
    def __init__(self):
        self.api_key = os.getenv("AZURE_OPENAI_API_KEY")
        self.endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        self.api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-10-01-preview")
        self.deployment_name = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4o")
        
        if self.api_key and self.endpoint:
            self.client = AzureOpenAI(api_key=self.api_key, api_version=self.api_version, azure_endpoint=self.endpoint)
        else:
            self.client = None

    def analyze_interview(self, transcript: List[Dict], expert_profile: Dict) -> Dict[str, Any]:
        if not self.client or not transcript: return {}

        full_text = ""
        for turn in transcript:
            role = turn.get("role", "unknown")
            text = turn.get("text", "")
            full_text += f"{role.upper()}: {text}\n"

        prompt = f"""
        You are a hiring committee. Review this technical interview transcript.
        
        CANDIDATE: {expert_profile.get('name', 'Candidate')}
        ROLE: {expert_profile.get('current_role', 'Expert')}
        
        TRANSCRIPT:
        {full_text[:15000]}
        
        Return JSON:
        {{
            "summary": "...",
            "strengths": ["...", "...", "..."],
            "weaknesses": ["...", "...", "..."],
            "rating": "Strong Hire/Hire/No Hire"
        }}
        """
        
        try:
             response = self.client.chat.completions.create(
                model=self.deployment_name,
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
                temperature=0.3
            )
             return json.loads(response.choices[0].message.content)
        except Exception as e:
            print(f"[Analyzer] Error: {e}")
            return {"error": str(e)}
