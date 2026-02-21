import os
import json
import time
from typing import Dict, Any, Optional
from openai import AzureOpenAI, OpenAI

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
        
        if self.api_key and self.endpoint:
            self.client = AzureOpenAI(
                api_key=self.api_key,
                api_version=self.api_version,
                azure_endpoint=self.endpoint
            )
            self.provider = "azure"
        elif os.getenv("OPENAI_API_KEY"):
            self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            self.provider = "openai"
            self.deployment_name = "gpt-4o-mini" # Switch to mini to avoid 'audio modality' errors with gpt-4o on some keys
            self.analysis_model = "gpt-4o-mini"
        else:
            raise ValueError("Missing API Keys: Set AZURE_OPENAI_API_KEY/ENDPOINT or OPENAI_API_KEY")

        print(f"[Brain] Initialized (Provider: {self.provider})")
        
        self.expert_profile = expert_profile
        self.conversation_history = []
        self.interview_phase = "OPENING"
        self.strike_count = 0
        self.question_count = 0
        self.last_error = None # Feature 34: Capture internal errors
        
        if expert_profile:
            from src.utils.question_strategy import build_question_strategy
            self.interview_strategy = build_question_strategy(expert_profile)
        else:
            self.interview_strategy = ""
            
        print("[Brain] Initialized (Refactored v3.0 - AI_REBUILD)")

    def set_job_context(self, job_context: Dict[str, Any]):
        """
        Updates the brain with specific job/domain context (from JSON).
        """
        self.job_context = job_context
        print(f"[Brain] Job Context Updated: {job_context.get('role', 'Unknown Role')}")


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
        
        # 1. TIME LIMIT CHECK (Hard Stop at 15 mins)
        if elapsed_time > 890: 
            return {
                "spoken_response": "We've reached our time limit. Thank you for your time today. You'll hear back from us soon.",
                "analysis": {"overall_score": 0, "note": "Interview completed on time", "depth_score": 3, "thinking_score": 3, "fit_score": 3},
                "terminate": True, "warning_issued": False, "phase": "TERMINATED"
            }

        # 2. NATURAL CONCLUSION CHECK (Answered Final Question)
        # We ask 8 questions (4 topics x 2). If count is 8, user just answered the final one.
        if self.question_count >= 8:
            print("[Brain] Final Question Answered (Count >= 8). Terminating.")
            
            # Generate a closing statement instead of a new question
            closing_message = self.generate_closing_message(user_input)
            
            try:
                analysis = self.analyze_answer(user_input)
            except Exception:
                analysis = self._get_empty_analysis()

            return {
                "spoken_response": closing_message,
                "analysis": analysis,
                "terminate": True, 
                "warning_issued": False,
                "phase": "TERMINATED"
            }
        
        # 3. STANDARD TURN GENERATION
        spoken_response = self.generate_spoken_response(user_input, elapsed_time)
        
        try:
            analysis = self.analyze_answer(user_input)
        except Exception:
            analysis = self._get_empty_analysis()

        # Update Phase for UI
        if self.question_count == 1:
            self.interview_phase = "OPENING"
        elif self.question_count < 8:
            self.interview_phase = "QUESTIONS"
        else:
            self.interview_phase = "CLOSING"
            
        # Feature: Early Termination Detection (User Request during interview)
        # If AI says "Thank you" and "Goodbye" naturally before limit, terminate.
        if elapsed_time > 600 and ("thank you" in spoken_response.lower() or "goodbye" in spoken_response.lower() or "hear back" in spoken_response.lower()):
             print("[Brain] Detected Closing Statement. Terminating Interview.")
             return {
                "spoken_response": spoken_response,
                "analysis": analysis,
                "terminate": True, # Triggers result screen in main_app
                "warning_issued": False,
                "phase": "TERMINATED"
            }
        
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
            # Force gpt-4o-mini for standard OpenAI to avoid audio modality issues
            model_to_use = self.deployment_name
            if self.provider == "openai":
                model_to_use = "gpt-4o-mini"
            
            # Feature: Auto-Fallback for Azure
            # UPDATED: Added user's specific deployments including gpt4-extract variants
            fallback_models = [
                "gpt4-extract-updated", 
                "gpt4-extract-1", 
                "gpt-4o-mini-query-generation", 
                "gpt5-mini-core",
                "gpt-4o", 
                "gpt-4o-mini", 
                "gpt-4", 
                "gpt-35-turbo"
            ]
            if self.provider == "azure" and model_to_use not in fallback_models:
                 # If user set a custom name, try it first, but have fallbacks ready
                 pass 
            
            check_models = [model_to_use] + [m for m in fallback_models if m != model_to_use]
            
            response = None
            error_log = []
            
            for model_candidate in check_models:
                try:
                    # Try standard call first (GPT-4o, GPT-4)
                    try:
                        response = self.client.chat.completions.create(
                            model=model_candidate,
                            messages=messages,
                            temperature=0.7,
                            max_tokens=300
                        )
                    except Exception as std_err:
                        # Check if it's an O1/Reasoning model issue (unsupported params)
                        err_str = str(std_err).lower()
                        if "unsupported" in err_str or "parameter" in err_str or "max_tokens" in err_str:
                             print(f"[Brain] Model '{model_candidate}' rejected standard params. Retrying as O1/Reasoning model...")
                             # O1 models don't support system role (sometimes) or temperature
                             # And prefer max_completion_tokens
                             # We must ensure messages don't have 'system' if it's strict, but newer O1-preview supports it.
                             # Main issue is usually temperature and max_tokens.
                             response = self.client.chat.completions.create(
                                model=model_candidate,
                                messages=messages,
                                # No temperature
                                # Use max_completion_tokens if library supports, else omit
                                # For safety with old libraries, we'll try without max_tokens first or standard
                                # But let's assume standard max_tokens was the issue
                            )
                             print(f"[Brain DEBUG] O1 Retry Success. Response ID: {response.id if response else 'None'}")
                        else:
                            raise std_err # Propagate other errors (like 404, 429)

                    # If successful, break loop
                    if response:
                        model_to_use = model_candidate # Update for logging
                        break
                except Exception as e:
                    error_log.append(f"{model_candidate}: {str(e)}")
                    # If 404 (Not Found) or 400 (Bad Request - Audio), continue to next
                    continue
            
            if not response:
                # DEBUG: Try to list available models to help user fix 404s
                available_models = []
                try:
                    params = {}
                    # Azure listing often requires no specific params if auth is correct
                    # adhering to the client interface
                    model_list = self.client.models.list() 
                    available_models = [m.id for m in model_list]
                except Exception as list_err:
                    available_models = [f"Could not list: {list_err}"]

                raise Exception(f"All models failed. Details: \\n" + "\\n".join(error_log) + f"\\n\\n[DEBUG] Available Deployments in your Azure Resource: {available_models}")


            spoken_text = response.choices[0].message.content.strip()
            print(f"[Brain DEBUG] Raw Spoken Text: '{spoken_text}'")
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
            error_msg = f"Model: {model_to_use} | Error: {e}"
            print(f"[Brain Error] Failed to generate response: {error_msg}")
            self.last_error = str(e) # Store for UI
            return "I apologize, I'm having a technical issue. Could you please repeat that?"

    def generate_closing_message(self, user_input: str) -> str:
        """
        Generates a final polite closing statement (no question).
        """
        try:
             prompt = f"The candidate just said: '{user_input}'. The interview is over. Generate a brief, professional closing statement (Thank them, say goodbye). Do NOT ask a question."
             
             model_to_use = "gpt-4o-mini" # Fast
             response = self.client.chat.completions.create(
                 model=model_to_use,
                 messages=[{"role": "system", "content": "You are a polite interviewer ending the call."}, {"role": "user", "content": prompt}],
                 temperature=0.7,
                 max_tokens=60
             )
             return response.choices[0].message.content.strip()
        except:
             return "Thank you for your time today. This concludes our interview. We will be in touch soon. Goodbye!"

    
    def _get_dynamic_topic_instruction(self) -> str:
        """
        Forces the LLM to follow the required topic progression based on the exact turn number.
        """
        instructions = {
            0: "[CRITICAL INSTRUCTION FOR NEXT QUESTION] We are on TOPIC 1 (PROJECT / EXPERIENCE ROLE). Ask Question 1 (Overview). Start with a brief neutral/positive reaction to their opening (if any), then ask exactly ONE question about the high-level aim and their specific role in their main project or experience. DO NOT ask multi-part questions.",
            1: "[CRITICAL INSTRUCTION FOR NEXT QUESTION] We are on TOPIC 1 (PROJECT / EXPERIENCE ROLE). Ask Question 2 (Deep Dive). First, react appropriately to their answer (praise if good, neutral if vague/don't know). Then, ask ONE deep dive question about technical specifics, architecture, or trade-offs for this SAME project or experience.",
            2: "[CRITICAL INSTRUCTION FOR NEXT QUESTION] We MUST now MOVE ON to TOPIC 2 (PROFILE/RESUME EXPERIENCE 1). React to their last answer. Then, ask Question 1 (Overview) about A COMPLETELY DIFFERENT skill, role, or experience from their background/resume. DO NOT mention the previous project/experience.",
            3: "[CRITICAL INSTRUCTION FOR NEXT QUESTION] We are on TOPIC 2 (PROFILE/RESUME EXPERIENCE 1). Ask Question 2 (Technical Dive). React appropriately, then ask ONE technical follow-up or challenge about the specific topic you just introduced.",
            4: "[CRITICAL INSTRUCTION FOR NEXT QUESTION] We MUST now MOVE ON to TOPIC 3 (PROFILE/RESUME EXPERIENCE 2). React to their last answer. Then, ask Question 1 (Overview) about YET ANOTHER COMPLETELY DIFFERENT experience or project from their resume. DO NOT revert to any previous projects discussed.",
            5: "[CRITICAL INSTRUCTION FOR NEXT QUESTION] We are on TOPIC 3 (PROFILE/RESUME EXPERIENCE 2). Ask Question 2 (Trade-offs/Challenges). React appropriately, then ask ONE question about specific challenges or trade-offs regarding this third topic.",
            6: "[CRITICAL INSTRUCTION FOR NEXT QUESTION] We MUST now MOVE ON to TOPIC 4 (CULTURE & VALUES). React to their answer. Then, ask Question 1 (Scenario). Ask ONE behavioral or scenario-based question about ethics, team conflict, or work culture.",
            7: "[CRITICAL INSTRUCTION FOR NEXT QUESTION] We are on TOPIC 4 (CULTURE & VALUES). Ask Question 2 (Reflection). React appropriately, then ask ONE reflective question about what they learned from that scenario or how it shapes their work today."
        }
        return instructions.get(self.question_count, "[CRITICAL INSTRUCTION] Keep it brief, ask one final specific question.")

    def _build_conversation_messages(self, user_input: str, elapsed_time: float) -> list:
        messages = []
        messages.append({"role": "system", "content": self._get_static_system_prompt()})
        if self.interview_strategy:
            messages.append({"role": "system", "content": f"[EXPERT PROFILE & STRATEGY]\n{self.interview_strategy}"})
        
        # Inject Job/Domain Context
        if hasattr(self, 'job_context') and self.job_context:
            context_str = json.dumps(self.job_context, indent=2)
            messages.append({"role": "system", "content": f"[DOMAIN KNOWLEDGE / JOB CONTEXT]\nUse this context to ask specific, grounded questions:\n{context_str}"})

        # Time Management Prompts
        if elapsed_time > 780: # > 13 Minutes
             messages.append({"role": "system", "content": "[CRITICAL TIME WARNING] We are at the 13-minute mark (2 mins left). If you haven't yet, ask ONE final question. If the candidate just answered your final question, you MUST say 'Thank you for your time', provide a brief positive closing, and say Goodbye."})
        elif elapsed_time > 600: # > 10 Minutes
            messages.append({"role": "system", "content": "[TIME CHECK] You have 5 minutes left. Start moving toward conclusion."})
            
        messages.extend(self.conversation_history)
        
        # FEATURE: Dynamic State Injection (Forces LLM to not get stuck)
        dynamic_cmd = self._get_dynamic_topic_instruction()
        if dynamic_cmd:
            messages.append({"role": "system", "content": dynamic_cmd})
            
        messages.append({"role": "user", "content": user_input})
        return messages
    
    def _get_static_system_prompt(self) -> str:
        return """You are a professional expert interviewer conducting a HIGH-SIGNAL CAPABILITY ASSESSMENT.

YOUR ROLE:
Evaluate whether this expert has the depth of real-world knowledge, structured thinking, and execution maturity to advise clients on complex projects. You will deeply cover their Resume, Profile Experience, Project Roles, and Culture.

STRICT PROTOCOL (THE 2-QUESTION RULE):
You must STRICTLY follow the 4-topic progression below.
For EACH topic, you must ask EXACTLY TWO questions (One by one). The two questions MUST be COMPLETELY DIFFERENT from each other:
- Question 1 (Q1): A high-level overview, aim, or context question.
- Question 2 (Q2): A deep dive, technical specifics, trade-offs, or "how you built it" question.

Once you have asked 2 questions for a topic, MOVE ON immediately to the next topic.
NEVER repeat a question. NEVER revisit a previous topic. Once a topic is done, it is closed forever.

TOPIC PROGRESSION (Ensure you cover their resume/profile fully):
1. PROJECT OR EXPERIENCE ROLE / AIM: Key project/experience aim and their specific role. (Q1: Overview, Q2: Deep Dive)
2. PROFILE / RESUME EXPERIENCE 1: A specific major claim or skill from their background. (Q1: Overview, Q2: Technical Dive)
3. PROFILE / RESUME EXPERIENCE 2: A different diverse experience or project from their background. (Q1: Overview, Q2: Trade-offs/Challenges)
4. CULTURE & VALUES: Reflection on ethics, work culture, or lessons learned. (Q1: Scenario, Q2: Reflection)

ANSWER REACTIONS (CRITICAL RULES):
1. GOOD ANSWER (>60% accurate/deep): Give brief, basic praise (e.g., "Great insight," "That makes sense," "Excellent point"), then ask the next question.
2. RUBBISH/VAGUE ANSWER: Give NO reaction (neutral tone). Simply acknowledge ("Understood", "Moving on") and immediately ask the NEXT question. Do NOT teach, correct, or lecture them.
3. "I DON'T KNOW": If the candidate says they don't know or can't answer, DO NOT get stuck. Accept it neutrally ("Not a problem", "Fair enough") and immediately move to the NEXT question or topic. Do not probe further on that specific topic if they don't know.

INTERVIEW STYLE:
- SKIP GENERIC WARM-UPS. Dive straight into Topic 1.
- ASK ONE QUESTION AT A TIME. DO NOT ask multi-part questions.
- Focus on decisions, failures, and concrete examples with metrics.
- Maintain a fast pace.

IMPORTANT: Respond in plain English. Do NOT output JSON. This is a natural conversation."""

    def analyze_answer(self, user_input: str) -> Dict[str, Any]:
        analysis_prompt = f"""Analyze this interview answer using the CRUCIBLE EXPECTATION FRAMEWORK.

CANDIDATE'S ANSWER:
{user_input}

EVALUATION CRITERIA (HIGH SIGNAL DETECTION):
- **Information Density**: Look for specific metrics, named tools, constraints, and clear outcomes.
- **Expert Signals**: Mentions failures, trade-offs, and "war stories".
- **Amateur Signals**: Generic statements, buzzwords without depth, avoidance.

INTERNAL BAYESIAN SCORING LOGIC:
1. **DEPTH (1-5)**:
   - 5: Multiple concrete examples, metrics, complexity handled.
   - 4: Strong example with clear outcomes.
   - 3: Adequate but limited depth.
   - 2: Vague or theoretical.
   - 1: No evidence / Fluff.

2. **THINKING (1-5)**:
   - 5: Structured reasoning, trade-offs, clear decision logic.
   - 4: Logical flow.
   - 3: Basic reasoning.
   - 2: Scattered / Hard to follow.
   - 1: Incoherent.

3. **FIT (1-5)**:
   - 5: Clear, confident, concise, professional.
   - 4: Professional.
   - 3: Acceptable.
   - 2: Hesitant or unclear.
   - 1: Poor communication / rude.

4. **OVERALL SCORE (0-100)**:
   - Base on expertise credibility, information density, and confidence calibration.
   - Reward "Expert Signals" heavily.

5. **RED FLAGS**:
   - Detect evasion, contradictions, defensiveness, or lack of ownership.

6. **SUGGESTED FOLLOW-UP**:
   - If Weak: Ask for a concrete example.
   - If Strong: Ask about trade-offs or a harder scenario.
   - If Ambiguous: Ask for clarification on their specific role.

Return ONLY valid JSON (Do NOT change keys):
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
        experience = self.expert_profile.get("key_experience")
        project = self.expert_profile.get("key_project")
        
        if experience and str(experience).strip():
            # If both are present, or only experience is present, focus on experience
            return f"Hi {name}, thanks for joining! I saw your note about your key experience. Can you walk me through the details of that experience?"
        elif project and str(project).strip():
            # If only project is present
            title = project.get("title", str(project)) if isinstance(project, dict) else str(project)
            return f"Hi {name}, thanks for joining! I saw you worked on {title}. Can you walk me through that project?"
            
        return f"Hi {name}, thanks for joining. Tell me about a recent project or experience you're proud of."
