import os
import json
import time
from typing import Dict, Any, Optional
from openai import AzureOpenAI

class Brain:
    """
    The AI's intelligence layer - handles all reasoning and response generation.
    Refactored v3.0 - Separate Speech and Analysis pipelines.
    """
    
    def __init__(self, expert_profile: Optional[Dict] = None):
        self.api_key = os.getenv("AZURE_OPENAI_API_KEY")
        self.endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        self.api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-10-01-preview")
        self.deployment_name = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4o")
        self.analysis_model = "gpt-4o-mini"
        
        if not self.api_key or not self.endpoint:
            raise ValueError("AZURE_OPENAI_API_KEY or AZURE_OPENAI_ENDPOINT not found in env")
            
        self.client = AzureOpenAI(
            api_key=self.api_key,
            api_version=self.api_version,
            azure_endpoint=self.endpoint
        )
        
        self.expert_profile = expert_profile
        self.conversation_history = []
        self.interview_phase = "OPENING"
        self.strike_count = 0
        self.question_count = 0
        
        if expert_profile:
            from src.utils.question_strategy import build_question_strategy
            self.interview_strategy = build_question_strategy(expert_profile)
        else:
            self.interview_strategy = ""
            
        print("[Brain] Initialized (Refactored v3.0 - AI_REBUILD)")

    def handle_user_input(self, user_input: str, elapsed_time: float) -> Dict[str, Any]:
        """
        Main entry point for processing user input.
        """
        if self.detect_abuse(user_input):
            self.strike_count += 1
            print(f"[Brain] Abuse Detected. Strike {self.strike_count}/2")
            if self.strike_count == 1:
                return {
                    "spoken_response": "I need to keep this conversation professional. Please refrain from using inappropriate language. This is your first warning.",
                    "analysis": {"overall_score": 0, "red_flags": ["Inappropriate language"], "depth_score": 1, "thinking_score": 1, "fit_score": 1},
                    "terminate": False, "warning_issued": True, "phase": "WARNING"
                }
            else:
                return {
                    "spoken_response": "I'm ending this interview due to continued unprofessional behavior. Thank you.",
                    "analysis": {"overall_score": 0, "red_flags": ["Terminated for conduct"], "depth_score": 1, "thinking_score": 1, "fit_score": 1},
                    "terminate": True, "warning_issued": False, "phase": "TERMINATED"
                }
        
        if elapsed_time > 890: 
            return {
                "spoken_response": "We've reached our time limit. Thank you for your time today. You'll hear back from us soon.",
                "analysis": {"overall_score": 0, "note": "Interview completed on time", "depth_score": 3, "thinking_score": 3, "fit_score": 3},
                "terminate": True, "warning_issued": False, "phase": "TERMINATED"
            }
        
        spoken_response = self.generate_spoken_response(user_input, elapsed_time)
        
        try:
            analysis = self.analyze_answer(user_input)
        except Exception:
            analysis = self._get_empty_analysis()

        if self.question_count == 1:
            self.interview_phase = "OPENING"
        elif self.question_count < 5:
            self.interview_phase = "QUESTIONS"
        else:
            self.interview_phase = "CLOSING"
        
        return {
            "spoken_response": spoken_response,
            "analysis": analysis,
            "terminate": False,
            "warning_issued": False,
            "phase": self.interview_phase
        }
    
    def generate_spoken_response(self, user_input: str, elapsed_time: float) -> str:
        messages = self._build_conversation_messages(user_input, elapsed_time)
        try:
            response = self.client.chat.completions.create(
                model=self.deployment_name,
                messages=messages,
                temperature=0.7,
                max_tokens=300
            )
            spoken_text = response.choices[0].message.content.strip()
            if spoken_text.lstrip().startswith("{") and "response_text" in spoken_text:
                try:
                    data = json.loads(spoken_text)
                    spoken_text = data.get("response_text", spoken_text)
                except:
                    pass
            
            self.conversation_history.append({"role": "user", "content": user_input})
            self.conversation_history.append({"role": "assistant", "content": spoken_text})
            self.question_count += 1
            return spoken_text
        except Exception as e:
            print(f"[Brain Error] Failed to generate response: {e}")
            return "I apologize, I'm having a technical issue. Could you please repeat that?"
    
    def _build_conversation_messages(self, user_input: str, elapsed_time: float) -> list:
        messages = []
        messages.append({"role": "system", "content": self._get_static_system_prompt()})
        if self.interview_strategy:
            messages.append({"role": "system", "content": f"[EXPERT PROFILE & STRATEGY]\n{self.interview_strategy}"})
        if elapsed_time > 780:
            messages.append({"role": "system", "content": "[TIME WARNING] You have 2 minutes left. Ask ONE final question to wrap up."})
        elif elapsed_time > 600:
            messages.append({"role": "system", "content": "[TIME CHECK] You have 5 minutes left. Start moving toward conclusion."})
        messages.extend(self.conversation_history)
        messages.append({"role": "user", "content": user_input})
        return messages
    
    def _get_static_system_prompt(self) -> str:
        return """You are a professional expert interviewer conducting a capability assessment.

YOUR ROLE:
You are evaluating whether this expert has the depth of knowledge, structured thinking, 
and communication skills to advise clients on complex projects.

INTERVIEW STYLE:
- Professional and respectful at all times
- Ask thoughtful questions that explore real experience
- Listen actively - let them talk 80% of the time
- Ask follow-up questions to get specific examples
- Encourage concrete details: metrics, outcomes, before/after comparisons

CONDUCT RULES:
- If someone is rude or abusive, politely end the interview
- Never ask them to write code - this is a verbal discussion only

IMPORTANT: Respond in plain English. Do NOT output JSON. This is a natural conversation."""

    def analyze_answer(self, user_input: str) -> Dict[str, Any]:
        analysis_prompt = f"""Analyze this interview answer and provide a structured assessment.

CANDIDATE'S ANSWER:
{user_input}

Evaluate on these dimensions (1-5):
1. DEPTH: Quality of evidence and domain expertise
2. THINKING: Structure and reasoning quality
3. FIT: Communication and professionalism
4. RED FLAGS: Any concerns

Return ONLY valid JSON:
{{
  "depth_score": 1-5,
  "thinking_score": 1-5,
  "fit_score": 1-5,
  "overall_score": 0-100,
  "depth_reasoning": "...",
  "thinking_reasoning": "...",
  "fit_reasoning": "...",
  "red_flags": [],
  "key_strengths": [],
  "suggested_follow_up": "..."
}}"""
        try:
            analysis_model = os.getenv("AZURE_OPENAI_ANALYSIS_MODEL", self.deployment_name)
            response = self.client.chat.completions.create(
                model=analysis_model,
                messages=[{"role": "user", "content": analysis_prompt}],
                response_format={"type": "json_object"},
                temperature=0.3
            )
            content = response.choices[0].message.content
            if content: return json.loads(content)
            else: return self._get_empty_analysis()
        except Exception:
            return self._get_empty_analysis()
            
    def _get_empty_analysis(self):
        return {
            "depth_score": 3, "thinking_score": 3, "fit_score": 3, "overall_score": 60,
            "depth_reasoning": "N/A", "thinking_reasoning": "N/A", "fit_reasoning": "N/A",
            "red_flags": [], "key_strengths": [], "suggested_follow_up": "Continue"
        }

    def detect_abuse(self, user_input: str) -> bool:
        if not user_input: return False
        abuse_keywords = ["stupid", "idiot", "fuck", "shit", "asshole", "dumb", "moron", "retard", "bitch", "shut up"]
        input_lower = user_input.lower()
        return any(keyword in input_lower for keyword in abuse_keywords)
    
    def get_opening_message(self) -> str:
        if not self.expert_profile:
            return "Hello! Thank you for joining this interview. Shall we begin?"
        name = self.expert_profile.get("name", "there")
        project = self.expert_profile.get("key_project")
        if project:
            title = project.get("title", str(project)) if isinstance(project, dict) else str(project)
            return f"Hi {name}, thanks for joining! I saw you worked on {title}. Can you walk me through that experience?"
        return f"Hi {name}, thanks for joining. Tell me about a recent project you're proud of."
