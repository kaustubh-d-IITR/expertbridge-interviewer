from typing import Dict, Any, List
import json
import os
from openai import AzureOpenAI, OpenAI

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
        elif os.getenv("OPENAI_API_KEY"):
             self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
             self.deployment_name = "gpt-4o-mini"
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
        
        # Feature: Auto-fallback for Analysis
        # UPDATED: Added user's specific deployments
        fallback_models = [
            "gpt4-extract-updated", 
            "gpt4-extract-1", 
            "gpt-4o-mini-query-generation", 
            "gpt5-mini-core",
            "gpt-4o-mini", 
            "gpt-4o", 
            "gpt-35-turbo", 
            "gpt-4"
        ]
        check_models = [self.deployment_name] + [m for m in fallback_models if m != self.deployment_name]
        
        response = None
        last_exception = None
        
        for model_to_use in check_models:
            try:
                 # Standard Call
                 try:
                     response = self.client.chat.completions.create(
                        model=model_to_use,
                        messages=[{"role": "user", "content": prompt}],
                        response_format={"type": "json_object"},
                        temperature=0.3
                    )
                 except Exception as std_err:
                     # O1 Fallback
                     err_str = str(std_err).lower()
                     if "unsupported" in err_str or "parameter" in err_str:
                         print(f"[Analyzer] Retrying '{model_to_use}' with O1 params...")
                         response = self.client.chat.completions.create(
                            model=model_to_use,
                            messages=[{"role": "user", "content": prompt}],
                            response_format={"type": "json_object"}
                            # No temperature
                        )
                     else:
                         raise std_err

                 if response: break
            except Exception as e:
                last_exception = e
                continue
                
        if not response:
            print(f"[Analyzer] Error: {last_exception}")
            return {"error": str(last_exception)}
            
        return json.loads(response.choices[0].message.content)
