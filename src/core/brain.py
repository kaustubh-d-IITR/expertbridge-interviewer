import os
from openai import AzureOpenAI
from src.utils.prompts import INTERVIEWER_SYSTEM_PROMPT

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

    def set_context(self, candidate_name, cv_text, job_context=None):
        """
        Initializes the chat history with system prompt and context.
        Returns the initial greeting from the AI.
        """
        if not self.client:
            return "Error: Azure OpenAI API Key not configured."
            
        # Dynamic System Prompt Construction
        if job_context:
            role_title = job_context.get('job_title', 'Expert')
            domain = job_context.get('industry_domain', 'General')
            requirements = job_context.get('killer_requirements', [])
            topics = job_context.get('question_topics', [])
            
            system_instruction = f"""
            You are an expert interviewer for the role of {role_title} in the {domain} domain.
            Your goal is to assess the candidate's fit based on the Job Description provided below.
            
            JOB REQUIREMENTS:
            - Focus Topics: {', '.join(topics)}
            - Key Requirements: {', '.join(requirements)}
            
            INTERVIEW STRATEGY (Total 6 Questions):
            1.  **Questions 1 & 2 (Job Fit)**: Ask questions strictly about the Role Objectives and Challenges. Verify if they understand the job's core mission.
            2.  **Questions 3 & 4 (Skill Fit)**: Ask technical questions strictly based on the skills found in their CV. Verify their claimed expertise.
            3.  **Questions 5 & 6 (Synergy)**: Ask questions about how their specific skills (CV) can solve the specific problems (Job Description). Test their strategic thinking.
            
            Process:
            - Ask ONE question at a time.
            - Keep responses concise and conversational.
            - Do not explicitly state "Question 1" or "Question 2". Just ask naturally.
            - After Question 6, conclude the interview.
            """
        else:
            # Fallback to generic prompt if no job selected
            system_instruction = INTERVIEWER_SYSTEM_PROMPT + "\n\nWe are starting the interview. Ask distinct technical questions relevant to their CV."

        # Reset history
        self.history = [
            {"role": "system", "content": system_instruction}
        ]
        
        initial_message = f"Candidate Name: {candidate_name}\nCV Text:\n{cv_text}\n\nPlease start the interview by introducing yourself as the interviewer for the {job_context.get('job_title', 'role') if job_context else 'role'} and asking the first question (Phase 1: Job Fit)."
        
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

    def generate_response(self, user_text):
        """
        Generates a response to the user's input.
        """
        try:
            if not self.client:
                return "Brain not initialized. Please upload a CV first."
            
            # Add user message
            self.history.append({"role": "user", "content": user_text})
            
            completion = self._safe_completion(
                messages=self.history,
                temperature=0.7,
                max_tokens=1024
            )
            
            ai_text = self._extract_content(completion)
            
            # Add assistant response
            self.history.append({"role": "assistant", "content": ai_text})
            
            return ai_text
            
        except Exception as e:
            # Crucial: print the exact error so it shows up in Streamlit Cloud logs
            print(f"!!! AZURE BRAIN ERROR !!!: {type(e).__name__}: {str(e)}")
            import traceback
            traceback.print_exc()
            return "I'm having trouble thinking right now. Could you repeat that?"
