import os
from openai import AzureOpenAI
from src.utils.prompts import INTERVIEWER_SYSTEM_PROMPT, DOMAIN_PERSONAS

class InterviewBrain:
    def __init__(self):
        self.api_key = os.getenv("AZURE_OPENAI_API_KEY")
        self.endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        self.deployment_name = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-audio-AI-Assessment")
        self.api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-08-01-preview")

        if not self.api_key or not self.endpoint:
            raise ValueError("AZURE_OPENAI_API_KEY or AZURE_OPENAI_ENDPOINT not found in env")
        
        self.client = AzureOpenAI(
            api_key=self.api_key,
            api_version=self.api_version,
            azure_endpoint=self.endpoint
        )
            
        self.model_name = self.deployment_name
        self.history = []
        self.warning_count = 0 # Feature 6: Conduct Tracking`,StartLine:21,TargetContent:`        self.model_name = self.deployment_name
        self.history = []
    
    def _safe_completion(self, messages, temperature=0.7, max_tokens=1024):
        """
        Attempts a standard completion. If it fails due to audio modality requirements,
        retries with audio output requested (discarding the audio).
        """
        try:
             # Try standard text-only request first
             return self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                top_p=1,
                stream=False
            )
        except Exception as e:
            error_str = str(e).lower()
            # Check for the specific Azure error about audio modality
            if "audio" in error_str and ("modality" in error_str or "required" in error_str):
                print(f"[Brain] Metadata-Only Model detected. Retrying with dummy audio output...")
                return self.client.chat.completions.create(
                    model=self.model_name,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    modalities=["text", "audio"],
                    audio={"voice": "alloy", "format": "wav"},
                    top_p=1,
                    stream=False
                )
            else:
                raise e # Re-raise real errors

    def _extract_content(self, completion):
        """
        Helper to extract text from either content or audio.transcript
        """
        msg = completion.choices[0].message
        if msg.content:
            return msg.content
        if hasattr(msg, 'audio') and msg.audio and msg.audio.transcript:
            return msg.audio.transcript
        return "I am having trouble speaking right now."

    def evaluate_code(self, code_snippet):
        """
        Evaluates the provided code snippet.
        """
        if not self.client:
             return "Error: Brain not active."
             
        prompt = f"""
        Evaluate the following Python code solution.
        Check for: 
        1. Correctness (Does it match the problem likely asked?)
        2. Efficiency (Big O)
        3. Code Style (Pythonic)
        
        Provide a concise feedback summary (2-3 sentences) and a Pass/Fail rating.
        
        CODE:
        {code_snippet}
        """
        
        try:
             completion = self._safe_completion(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2
            )
             return self._extract_content(completion)
        except Exception as e:
            return f"Error evaluating code: {e}"

    def set_context(self, candidate_name, cv_text, job_context=None, mode="standard"):
        """
        Initializes the chat history with system prompt and context.
        Returns the initial greeting from the AI.
        """
        if not self.client:
            return "Error: Azure OpenAI API Key not configured."
        
        # Feature 3: Recruiter Mode Override
        if mode == "recruiter":
            from src.utils.prompts import RECRUITER_SYSTEM_PROMPT
            system_instruction = RECRUITER_SYSTEM_PROMPT + f"\n\nCONTEXT:\nCandidate: {candidate_name}\nCV Summary: {cv_text[:500]}..."
            
            initial_message = f"Candidate Name: {candidate_name}\nCV Text:\n{cv_text}\n\nYou are in RECRUITER MODE. Start immediately with Question 1."
        
        # Standard Mode (with Job Context)
        elif job_context:
            role_title = job_context.get('job_title', 'Expert')
            domain = job_context.get('industry_domain', 'General')
            requirements = job_context.get('killer_requirements', [])
            topics = job_context.get('question_topics', [])
            
            # 1. Select the Base Persona from prompts.py
            # Try exact match, then partial match, then fallback
            base_persona = DOMAIN_PERSONAS.get(domain)
            if not base_persona:
                 # Fuzzy match attempt (e.g. "Healthcare IT" -> "Healthcare")
                 for key, persona in DOMAIN_PERSONAS.items():
                     if key.lower() in domain.lower():
                         base_persona = persona
                         break
            
            # Fallback if still None
            if not base_persona:
                base_persona = f"You are an expert interviewer for the role of {role_title} in the {domain} domain."

            system_instruction = f"""
            {base_persona}
            
            Your goal is to assess the candidate's fit based on the Job Description provided below.
            
            JOB REQUIREMENTS:
            - Focus Topics: {', '.join(topics)}
            - Key Requirements: {', '.join(requirements)}
            
            INTERVIEW STRATEGY (Total 6 Questions):
            1.  **Questions 1 & 2 (Skill Fit)**: Ask technical questions strictly based on the skills found in their RESUME/CV. Verify their claimed expertise first.
            2.  **Questions 3 & 4 (Company Vision)**: Ask questions strictly about the Role Objectives and Company Goals from the Job Description. Verify if they align with the vision.
            3.  **Questions 5 & 6 (Utility/Synergy)**: Ask questions about how their specific skills will be useful for this specific project. "How will you help us achieve X?"
            
            Process:
            - Ask ONE question at a time.
            - Keep responses concise and conversational.
            - Do not explicitly state "Question 1" or "Question 2". Just ask naturally.
            - After Question 6, conclude the interview.
            """
            
            initial_message = f"Candidate Name: {candidate_name}\nCV Text:\n{cv_text}\n\nPlease start the interview by introducing yourself as the interviewer for the {job_context.get('job_title', 'role') if job_context else 'role'} and asking the first question (Phase 1: Resume Skills)."

        else:
            # Fallback to generic prompt if no job selected
            system_instruction = INTERVIEWER_SYSTEM_PROMPT + "\n\nWe are starting the interview. Ask distinct technical questions relevant to their CV."
            initial_message = f"Candidate Name: {candidate_name}\nCV Text:\n{cv_text}\n\nPlease start the interview by introducing yourself as the interviewer and asking the first question."

        # Reset history
        self.history = [
            {"role": "system", "content": system_instruction}
        ]
        
        # Add the context as a user message to trigger the start
        self.history.append({"role": "user", "content": initial_message})
        
        try:
            completion = self._safe_completion(
                messages=self.history,
                temperature=0.7,
                max_tokens=1024
            )
            
            response_text = self._extract_content(completion)
            self.history.append({"role": "assistant", "content": response_text})
            return response_text
            
        except Exception as e:
            print(f"!!! AZURE BRAIN CONTEXT ERROR !!!: {type(e).__name__}: {str(e)}")
            import traceback
            traceback.print_exc()
            return "Hello! I am ready to interview you. Could you please introduce yourself?"

    def generate_response(self, user_text, detected_language="en", response_language=None):
        """
        Generates a response to the user's input.
        Parses JSON output for Smart Brain features (Scoring, Conduct).
        """
        try:
            if not self.client:
                return {"text": "Brain not initialized. Please upload a CV first.", "score": 0}
            
            # Feature 4 & 5: Strict Output Language Logic
            target_lang = response_language if response_language else detected_language
            
            lang_instruction = ""
            
            # Case A: Explicit Target Language (Non-English)
            if target_lang and target_lang.lower() not in ["en", "english"]:
                 lang_instruction = f"[SYSTEM INSTRUCTION: You MUST reply in {target_lang}. Use the native script for {target_lang}.]\n\n"
            
            # Case B: Strict English Enforcement (User speaks non-English, but Target is English)
            elif (target_lang and target_lang.lower() in ["en", "english"]) and (detected_language and detected_language.lower() not in ["en", "english"]):
                 lang_instruction = f"[SYSTEM INSTRUCTION: The user is speaking in language code '{detected_language}'. UNDERSTAND it, but you MUST reply in ENGLISH only.]\n\n"

            # Case C: Auto-Detect
            elif not response_language and detected_language and detected_language != "en":
                 lang_instruction = f"[SYSTEM NOTE: The user is speaking in language code '{detected_language}'. Reply in this language.]\n\n"
            
            # Add user message
            full_content = lang_instruction + user_text
            self.history.append({"role": "user", "content": full_content})
            
            # Request JSON Mode (implicit via prompt, but we set response_format if using newer models, 
            # but to be safe with all models we just parse the text).
            raw_content = None # Initialize scope
            
            try:
                try:
                    response = self.client.chat.completions.create(
                        model=self.model_name, 
                        messages=self.history, 
                        temperature=0.7,
                        max_tokens=1024 
                    )
                except Exception as e:
                    # Fallback Logic for Audio Models (e.g. gpt-4o-audio-preview) failing on text-only input
                    # Check if error is related to audio requirement
                    error_str = str(e).lower()
                    if "audio" in error_str and ("modality" in error_str or "input content" in error_str):
                        import streamlit as st
                        if "debug_logs" not in st.session_state: st.session_state.debug_logs = ""
                        st.session_state.debug_logs += f"\n[Brain Warning]: Model '{self.model_name}' rejected text-only input. Initiating fallback sequence...\n"
                        
                        # Define Fallback Candidates
                        # 1. User defined
                        # 2. Standard GPT-4o
                        # 3. GPT-4 Turbo
                        # 4. GPT-4 Classic
                        # 5. GPT-3.5 Turbo (Last resort)
                        fallback_candidates = []
                        env_fallback = os.getenv("AZURE_OPENAI_FALLBACK_MODEL")
                        if env_fallback: fallback_candidates.append(env_fallback)
                        
                        defaults = ["gpt-4o", "gpt-4", "gpt-4-turbo", "gpt-35-turbo"]
                        for d in defaults:
                            if d not in fallback_candidates:
                                fallback_candidates.append(d)
                                
                        success = False
                        last_error = None
                        
                        for candidate in fallback_candidates:
                            try:
                                print(f"[Brain] Trying fallback model: {candidate}")
                                response = self.client.chat.completions.create(
                                    model=candidate, 
                                    messages=self.history, 
                                    temperature=0.7,
                                    max_tokens=1024 
                                )
                                st.session_state.debug_logs += f"\n[Brain Info]: Fallback to '{candidate}' SUCCESSFUL."
                                success = True
                                break
                            except Exception as fb_e:
                                last_error = fb_e
                                st.session_state.debug_logs += f"\n[Brain Info]: Fallback to '{candidate}' failed ({type(fb_e).__name__})."
                                continue
                        
                        if not success:
                            st.session_state.debug_logs += f"\n[Brain Critical]: All fallbacks failed. Last error: {str(last_error)}"
                            # Return a friendly error message instead of crashing
                            return {"text": "System Error: No valid text-only AI model found. Please configure AZURE_OPENAI_FALLBACK_MODEL in your .env file.", "score": 0, "terminate": False}
                            
                    else:
                        raise e # Re-raise if not the expected error

                raw_content = response.choices[0].message.content
                
                # Debug: Log raw response
                import streamlit as st 
                if "debug_logs" not in st.session_state:
                    st.session_state.debug_logs = ""
                st.session_state.debug_logs += f"\n[Brain Raw]: {raw_content}"
                
                # Attempt to parse JSON
                import json
                try:
                    # remove markdown code fences if present
                    clean_content = raw_content.replace("```json", "").replace("```", "").strip()
                    data = json.loads(clean_content)
                    
                    # Extract fields
                    ai_response = data.get("response_text", "I'm not sure how to respond.")
                    signal_score = data.get("signal_score", 0)
                    warning_issued = data.get("warning_issued", False)
                    terminate = data.get("terminate_interview", False)
                    
                    # Update State
                    if warning_issued:
                        self.warning_count += 1
                    
                    if self.warning_count >= 2:
                        terminate = True
                        
                    # Add assistant response (TEXT only to history)
                    self.history.append({"role": "assistant", "content": ai_response})

                    # Return dict for Orchestrator
                    return {
                        "text": ai_response,
                        "score": signal_score,
                        "terminate": terminate
                    }
                    
                except json.JSONDecodeError:
                    st.session_state.debug_logs += f"\n[JSON Error]: Could not parse response."
                    # Fallback: Treat entire content as text (if not empty)
                    ai_text_fallback = raw_content if raw_content else "I encountered an error processing that."
                    self.history.append({"role": "assistant", "content": ai_text_fallback})
                    return {
                        "text": ai_text_fallback,
                        "score": 50, # Neutral score on error
                        "terminate": False
                    }
                    
            except Exception as e:
                ai_text = str(e) # Fallback to showing exception to UI if critical
                if raw_content: ai_text = raw_content
                
                import streamlit as st
                if "debug_logs" not in st.session_state:
                    st.session_state.debug_logs = ""
                st.session_state.debug_logs += f"\n[Brain Critical Error]: {str(e)}"
            
            # Add assistant response (TEXT only to history, so next turn doesn't get confused by JSON)
            # (Note: Already added inside try block if successful, but careful not to duplicate if error)
            # If we fall through here, history might be inconsistent. Let's fix that.
            
            return ai_text if 'ai_text' in locals() else "System Error (See Logs)"
            # Actually, keeping JSON in history might confuse the model if it expects conversation.
            # Best practice: Add the *text* response to history.
            self.history.append({"role": "assistant", "content": ai_text})
            
            return {
                "text": ai_text, 
                "score": signal_score, 
                "terminate": terminate
            }
            
        except Exception as e:
            print(f"!!! AZURE BRAIN ERROR !!!: {type(e).__name__}: {str(e)}")
            import traceback
            traceback.print_exc()
            return {"text": "I'm having trouble thinking right now. Could you repeat that?", "score": 0, "terminate": False}
