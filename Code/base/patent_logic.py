import openai
import time
from Code.base.openai_prompts import PROMPTS

def analyze_claims(claims_text, model, role, api_base, api_key, temperature, top_p, max_tokens, retries=5):
    """
    Run all prompts from openai_prompts.py on the extracted claims text.

    Args:
        claims_text (str): Extracted claims text from PDF.

    Returns:
        dict: {prompt_name: response_text}
    """
    client = openai.OpenAI(
        api_key  = api_key,
        base_url = api_base
    )

    results = {}

    for prompt_name, prompt_template in PROMPTS.items():
        user_prompt = f"{prompt_template}\n\nPatent text:\n{claims_text}"

        try:
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": role, "content": user_prompt}],
                temperature=temperature,
                top_p=top_p,
                max_tokens=max_tokens,
            )
            results[prompt_name] = response.choices[0].message.content
            time.sleep(1)

        except openai.APIStatusError as e:
            results[prompt_name] = f"API error ({e.status_code}): {e.message}"
        except openai.APIConnectionError:
            results[prompt_name] = "Connection error: could not reach the API"
        except Exception as e:
            results[prompt_name] = f"Unexpected error during analysis"

    return results
