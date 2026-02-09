import pickle
import openai
import os
import json
from Code.base.openai_prompts import PROMPTS

# ✅ masked: avoid KeyError at import time; keep behavior otherwise
client = openai.OpenAI(api_key=os.environ.get("OPENAI_API_KEY", ""))

def analyze_claims(claims_text, model, role, api_base, api_key, temperature, top_p, max_tokens, retries = 5): 
    """
    Run all prompts from openai_prompts.py on the extracted claims text.

    Args:
        claims_text (str): Extracted claims text from PDF.

    Returns:
        dict: {prompt_name: response_text}
    """
    # Define Llama client
    client = openai.OpenAI(
        api_key  = api_key,
        base_url = api_base
    )
    

    # Build dictionary of prompt responses
    results = {}

    for prompt_name, prompt_template in PROMPTS.items():
        # Combine the base prompt with the patent text
        user_prompt = f"{prompt_template}\n\nPatent text:\n{claims_text}"
        print(f'attempting prompt {prompt_name}')

        try:
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": role, "content": user_prompt}],
                temperature=temperature,
                top_p=top_p,
                max_tokens=max_tokens,
            )
            results[prompt_name] = response.choices[0].message.content

        except Exception as e:
            results[prompt_name] = f"Error: {e}"
        
        print(f'done with prompt {prompt_name}')

    return results
