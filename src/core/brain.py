import os
from openai import AzureOpenAI
from src.utils.prompts import INTERVIEWER_SYSTEM_PROMPT, DOMAIN_PERSONAS
from src.utils.question_strategy import build_question_strategy
from src.utils.question_strategy import build_question_strategy
from src.utils.sanitizer import clean_ai_response # Phase 23: External Sanitizer

# Phase 35: Semantic Caching Imports
try:
    from gptcache import cache
    from gptcache.manager import get_data_manager, CacheBase, VectorBase
    from gptcache.embedding import Onnx
    from gptcache.similarity_evaluation.distance import SearchDistanceEvaluation
    HAS_CACHE = True
except ImportError:
    HAS_CACHE = False
    print("DEBUG: GPTCache not found. Caching disabled.")

class InterviewBrain:
    def __init__(self, expert_profile=None):
        print("DEBUG: InterviewBrain Initialized (v2.2)") # Proof of life
        self.api_key = os.getenv("AZURE_OPENAI_API_KEY")
        self.endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        self.deployment_name = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-audio-AI-Assessment")
        self.api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-10-01-preview")

        if not self.api_key or not self.endpoint:
            raise ValueError("AZURE_OPENAI_API_KEY or AZURE_OPENAI_ENDPOINT not found in env")
        
        self.client = AzureOpenAI(
            api_key=self.api_key,
            api_version=self.api_version,
            azure_endpoint=self.endpoint
        )
            
        self.model_name = self.deployment_name
        self.history = []
        self.warning_count = 0 # Feature 6: Conduct Tracking
        
        # Phase 17: Personalization
        self.expert_profile = expert_profile
        self.question_strategy = ""
        if self.expert_profile:
             self.question_strategy = build_question_strategy(self.expert_profile)
             
             self.question_strategy = build_question_strategy(self.expert_profile)
             
        self.model_name = self.deployment_name
        self.history = []

        # Phase 35: Initialize Semantic Cache
        self.cache_enabled = False
        if HAS_CACHE:
            self._init_setup_cache()
    
    def _init_setup_cache(self):
        """
        Initializes the Semantic Cache using SQLite (Metadata) and Onnx (Embeddings).
        """
        try:
            print("DEBUG: Initializing Semantic Cache...")
            # Use Onnx for lightweight local embedding generation (no API cost)
            onnx = Onnx()
            
            # Use SQLite for reliable local storage
            # VectorBase 'faiss' is standard, but 'simple' might be safer if faiss fails. 
            # We'll try standard config, GPTCache handles numpy fallback usually.
            data_manager = get_data_manager(
                CacheBase("sqlite", sql_url="sqlite:///./brain_cache.db"), 
                VectorBase("faiss", dimension=onnx.dimension)
            )
            
            cache.init(
                embedding_func=onnx.to_embeddings,
                data_manager=data_manager,
                similarity_evaluation=SearchDistanceEvaluation(),
            )
            self.cache_enabled = True
            print("DEBUG: Semantic Cache Activated.")
        except Exception as e:
            print(f"WARN: Failed to init Semantic Cache: {e}")
            self.cache_enabled = False
    
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

# Removed internal _clean_json_response to use external module


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
            # Phase 19: Split Context to avoid Azure Content Filter "Jailbreak" detection
            # System prompt stays pure. Context goes to User message.
            # Phase 25: Jailbreak Evasion - Move Instructions to User Message
            # System prompt is now benign. We inject the "persona" here.
            # Phase 27: Emergency De-JSON-ification (User Request)
            # Abolish JSON. We want clean text only.
            RECRUITER_INSTRUCTIONS = """
            Goal: Conduct a professional technical interview.
            Guidelines:
            1. Be polite and focused.
            2. Evaluate depth of knowledge (internally).
            3. Speak English.
            4. If rude, warn once, then end call.
            5. VERBAL discussion only. No coding.
            
            OUTPUT FORMAT:
            Plain text conversation only. Do NOT output JSON. Do NOT include any scores or metadata. Just reply to the candidate.
            """
            
            # Fix UnboundLocalError: Initialize system_instruction with the benign prompt
            system_instruction = RECRUITER_SYSTEM_PROMPT 
            
            context_block = f"\n\nCONTEXT:\nCandidate: {candidate_name}\nCV Summary: {cv_text[:500]}..."
            
            # Phase 17: Inject Personalized Strategy (into User Context, not System)
            if self.question_strategy:
                context_block += f"\n\n{self.question_strategy}\n\nPlease ask specific questions based on the above."
            
            initial_message = f"{RECRUITER_INSTRUCTIONS}\n\n{context_block}\n\nPlease start immediately with Question 1."
            
            print(f"DEBUG: Brain Context Set. Mode: Recruiter. Instruction Length: {len(RECRUITER_INSTRUCTIONS)}")
        
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
        import streamlit as st # Ensure st is available throughout the scope
        import re # For robust JSON extraction
        if "debug_logs" not in st.session_state:
            st.session_state.debug_logs = ""
            
        try:
            if not self.client:
                return {"text": "Brain not initialized. Please upload a CV first.", "score": 0}
            
            # Feature 4 & 5: Strict Output Language Logic
            target_lang = response_language if response_language else detected_language
            
            lang_instruction = ""
            
            # Case A: Explicit Target Language (Non-English)
            if target_lang and target_lang.lower() not in ["en", "english"]:
                 lang_instruction = f"[SYSTEM NOTE: Please reply in {target_lang}. Use the native script for {target_lang}.]\n\n"
            
             # Case B: Strict English Enforcement (User speaks non-English, but Target is English)
            elif (target_lang and target_lang.lower() in ["en", "english"]) and (detected_language and detected_language.lower() not in ["en", "english"]):
                 lang_instruction = f"[SYSTEM NOTE: The user is speaking in language '{detected_language}'. Please reply in ENGLISH only.]\n\n"

            # Case C: Auto-Detect
            elif not response_language and detected_language and detected_language != "en":
                 lang_instruction = f"[SYSTEM NOTE: The user is speaking in language code '{detected_language}'. Reply in this language.]\n\n"
            
            # Add user message
            full_content = lang_instruction + user_text
            self.history.append({"role": "user", "content": full_content})
            
            # Request JSON Mode (implicit via prompt, but we set response_format if using newer models, 
            # but to be safe with all models we just parse the text).
            raw_content = None # Initialize scope
            ai_text = "I'm having trouble thinking right now. Could you repeat that?" 
            
            # Phase 35: Semantic Cache Lookup
            # We use the user's last message as the key.
            # Note: We do NOT cache the whole history, just the QA pair, since audio interviews 
            # often have atomic Q&A structure (Greeting -> Greeting, Define X -> Definition).
            if self.cache_enabled:
                try:
                    cached_res = cache.get(user_text)
                    if cached_res:
                         import streamlit as st
                         st.session_state.debug_logs += f"\\n[Brain Info]: CACHE HIT! Served from Memory."
                         print(f"[Brain] Cache Hit for: '{user_text}'")
                         
                         self.history.append({"role": "assistant", "content": cached_res})
                         return {
                            "text": cached_res,
                            "score": 0,
                            "terminate": False
                        }
                except Exception as cache_e:
                    print(f"[Brain] Cache Lookup Failed: {cache_e}")

            try:
                # Phase 32: Robust Modality Handling
                # We construct the request parameters dynamically.
                # If it's an audio model (or if we suspect it is), we add audio params.
                
                req_params = {
                    "model": self.model_name,
                    "messages": self.history,
                    "temperature": 0.7,
                    "max_tokens": 1024
                }
                
                # Broader check for audio models
                # User's model: 'gpt-audio-AI-Assessment'
                model_lower = self.model_name.lower()
                if "audio" in model_lower or "gpt-4o-audio" in model_lower:
                    print(f"[Brain] Detected Audio Model '{self.model_name}'. Forcing audio modality.")
                    req_params["modalities"] = ["text", "audio"]
                    req_params["audio"] = {"voice": "alloy", "format": "wav"}
                
                try:
                    response = self.client.chat.completions.create(**req_params)
                except Exception as e:
                    # Retry Logic for Modality Errors
                    error_str = str(e).lower()
                    if "modality" in error_str or "audio" in error_str:
                        print(f"[Brain Warning] Modality Error: {e}. Retrying with FORCED AUDIO...")
                        req_params["modalities"] = ["text", "audio"]
                        req_params["audio"] = {"voice": "alloy", "format": "wav"}
                        try:
                            response = self.client.chat.completions.create(**req_params)
                        except Exception as retry_e:
                            print(f"[Brain Error] Retry failed: {retry_e}")
                            raise retry_e # Rethrow to outer fallback
                    else:
                        print(f"[Brain Error] Primary model failed: {e}")
                        raise e # Rethrow to outer fallback
                        
                # Success Handling (for both initial and retry)
                if response:
                    # Check for Content Filter
                    if response.choices[0].finish_reason == 'content_filter':
                        st.session_state.debug_logs += f"\\n[Brain Alert]: Azure Content Filter Triggered."
                        return {
                            "text": "I cannot answer that because it triggered the safety filters. Please ask something else.",
                            "score": 0,
                            "terminate": False
                        }

                    raw_content = response.choices[0].message.content
                    # If content is null (sometimes happens with audio models), try transcript
                    if not raw_content and hasattr(response.choices[0].message, 'audio'):
                        raw_content = response.choices[0].message.audio.transcript
                    
                    if not raw_content:
                        st.session_state.debug_logs += f"\\n[Brain Alert]: Received empty response from model."
                        # If empty but no error, we might want to try fallback or just return specific error
                        # Proceeding to fallback if empty...
                        pass 
                    else:
                         # We have our response, no need to fallback
                         pass 
                            
                # 2. IF NO RESPONSE YET -> DEPLOYMENT FALLBACK LOOP
                if not raw_content:
                    import streamlit as st
                    st.session_state.debug_logs += f"\\n[Brain Critical]: Primary model returned no content. Initiating Deployment Fallback Sequence..."
                    
                    # Define Fallback Candidates
                    fallback_candidates = []
                    env_fallback = os.getenv("AZURE_OPENAI_FALLBACK_MODEL")
                    if env_fallback: 
                        fallback_candidates.append(env_fallback)
                        st.session_state.debug_logs += f"\\n[Brain Info]: Added configured fallback model: {env_fallback}"
                    
                    defaults = ["gpt-4o", "gpt-4", "gpt-4-turbo", "gpt-35-turbo"]
                    for d in defaults:
                        if d not in fallback_candidates:
                            fallback_candidates.append(d)
                            
                    success = False
                    last_error = None
                    
                    for candidate in fallback_candidates:
                        try:
                            print(f"[Brain] Trying fallback model: {candidate}")
                            # Phase 33: Ensure fallbacks are TEXT-ONLY (no audio params)
                            response = self.client.chat.completions.create(
                                model=candidate, 
                                messages=self.history, 
                                temperature=0.7,
                                max_tokens=1024 
                            )
                            
                            if response.choices[0].finish_reason == 'content_filter':
                                st.session_state.debug_logs += f"\\n[Brain Info]: Fallback '{candidate}' blocked by Content Filter."
                                continue 
                                
                            raw_content = response.choices[0].message.content
                            if raw_content:
                                st.session_state.debug_logs += f"\\n[Brain Info]: Fallback to '{candidate}' SUCCESSFUL."
                                success = True
                                break
                        except Exception as fb_e:
                            last_error = fb_e
                            st.session_state.debug_logs += f"\\n[Brain Info]: Fallback to '{candidate}' failed ({type(fb_e).__name__})."
                            continue
                    
                    if not success:
                        st.session_state.debug_logs += f"\\n[Brain Critical]: All fallbacks failed. Last error: {str(last_error)}"
                        # Return specific error
                        return {
                            "text": f"System Error: Unable to generate response. (Details: {str(last_error) if last_error else 'Empty Response'})", 
                            "score": 0, 
                            "terminate": False
                        }

                if raw_content:
                    # Phase 27: No JSON Parsing. Just return clean text.
                    # We still use clean_ai_response just in case, but expectation is plain text.
                    from src.utils.sanitizer import clean_ai_response
                    clean_data = clean_ai_response(raw_content)
                    
                    ai_text = clean_data["text"]
                    
                    # Mock scores since we disabled JSON
                    # This breaks the scoring feature but fixes the critical "Raw JSON" bug.
                    signal_score = 0 
                    terminate = False 
                    
                    self.history.append({"role": "assistant", "content": ai_text})
                    
                    # Phase 35: Save to Semantic Cache
                    if self.cache_enabled and ai_text:
                        try:
                            # Only cache reasonable length responses (avoid caching errors)
                            if len(ai_text) > 5 and "Error" not in ai_text:
                                cache.data_manager.save(user_text, ai_text, cache.embedding_func(user_text))
                                print(f"[Brain] Saved response to cache.")
                        except Exception as save_e:
                             print(f"[Brain Warning] Failed to save to cache: {save_e}")

                    return {
                        "text": ai_text,
                        "score": signal_score, # Mocked
                        "terminate": terminate # Mocked
                    }
                    
            except Exception as e:
                print(f"Brain Logic Error: {e}")
                # Return the specific error to the user
                return {
                    "text": f"Error: {type(e).__name__} - {str(e)}", 
                    "score": 0, 
                    "terminate": False
                }
            
            return {
                "text": ai_text, 
                "score": 0, 
                "terminate": False
            }
            
        except Exception as e:
            print(f"!!! AZURE BRAIN ERROR !!!: {type(e).__name__}: {str(e)}")
            import traceback
            traceback.print_exc()
            return {"text": f"Critical Error: {str(e)}", "score": 0, "terminate": False}
