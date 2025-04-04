import os

import openai

OPENAI_MODEL = "gpt-4o"
PROMPT_PREFIX = "Use young slangs and speak like you're chill. Be sarcastic."


def initialize():
    """Initialize OpenAI client."""
    openai.api_key = os.getenv("OPENAI_API_KEY")


async def ask_chatgpt(prompt, logger):
    """Ask OpenAI ChatGPT a question."""
    completion = openai.ChatCompletion.create(
        model=OPENAI_MODEL,
        messages=[
            {
                "role": "user",
                "content": f"{PROMPT_PREFIX} {prompt}"
            }
        ]
    )

    logger.info({
        "name": "Ask ChatGPT interaction",
        "prompt": prompt,
        "response": completion.to_dict_recursive()
    })

    try:
        resp = completion["choices"][0]["message"]["content"]
    except (IndexError, KeyError) as exc:
        resp = f"ChatGPT response format changed: {repr(exc)}"
        logger.error(resp)

    return resp
