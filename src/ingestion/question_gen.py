import os
from openai import AzureOpenAI
from src.utils.prompts import QUESTION_GEN_SYSTEM_PROMPT

def generate_initial_questions(cv_text):
    """
    Generates a list of initial technical questions based on the CV text using Azure OpenAI.
    """
    api_key = os.getenv("AZURE_OPENAI_API_KEY")
    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    deployment_name = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-audio-AI-Assessment")
    api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-08-01-preview")

    if not api_key or not endpoint:
        return ["Error: Azure OpenAI credentials not found."]

    client = AzureOpenAI(
        api_key=api_key,
        api_version=api_version,
        azure_endpoint=endpoint
    )
    model_name = deployment_name

    try:
        prompt = f"Analyze the following CV and generate a list of 3-5 technical interview topics/questions. Return them as a simple listone per line.\nCV Text:\n{cv_text}"
        
        messages = [
            {"role": "system", "content": QUESTION_GEN_SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ]

        try:
             completion = client.chat.completions.create(
                model=model_name,
                messages=messages,
                temperature=0.5,
                max_tokens=512,
            )
        except Exception as e:
            error_str = str(e).lower()
            if "audio" in error_str and ("modality" in error_str or "required" in error_str):
                print(f"[QuestionGen] Metadata-Only Model detected. Retrying with dummy audio output...")
                completion = client.chat.completions.create(
                    model=model_name,
                    messages=messages,
                    temperature=0.5,
                    max_tokens=512,
                    modalities=["text", "audio"],
                    audio={"voice": "alloy", "format": "wav"}
                )
            else:
                raise e
        
        response_text = completion.choices[0].message.content
        # Fallback for audio models
        if not response_text and hasattr(completion.choices[0].message, 'audio'):
             response_text = completion.choices[0].message.audio.transcript

        if not response_text:
             response_text = "Could not generate questions. Please introduce yourself."
        
        # Simple extraction assumes the model follows instructions to list items
        questions = [line.strip().lstrip('- ').strip() for line in response_text.split('\n') if line.strip()]
        
        if not questions:
             return ["Could not generate specific questions. Please introduce yourself."]
             
        return questions
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"Error generating questions: {e}")
        return ["Could not generate questions. Please introduce yourself."]
