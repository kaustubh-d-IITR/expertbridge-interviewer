import os
from openai import AzureOpenAI
from src.utils.prompts import INTERVIEWER_SYSTEM_PROMPT, DOMAIN_PERSONAS

class InterviewBrain:
    # ... (init methods unchanged) ...

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
        else:
            # Fallback to generic prompt if no job selected
            system_instruction = INTERVIEWER_SYSTEM_PROMPT + "\n\nWe are starting the interview. Ask distinct technical questions relevant to their CV."

        # Reset history
        self.history = [
            {"role": "system", "content": system_instruction}
        ]
        
        initial_message = f"Candidate Name: {candidate_name}\nCV Text:\n{cv_text}\n\nPlease start the interview by introducing yourself as the interviewer for the {job_context.get('job_title', 'role') if job_context else 'role'} and asking the first question (Phase 1: Resume Skills)."
        
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
