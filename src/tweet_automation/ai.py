
from llama_index.llms import Ollama

from .templates import (
    analyses_of_styles,
    generate_template_style_tweet_from_inspiration_prompt,
)


# TODO: Convert to async
def generate_tweet_from_inspiration_prompt(
    tweet_type: str, tweet_example_blocks: str, til_content: str
) -> str:
    """
    Generate a tweet from an inspiration prompt.
    """
    llm = Ollama(model="mistral", request_timeout=300.0)

    if tweet_type in analyses_of_styles:
        prompt_str = generate_template_style_tweet_from_inspiration_prompt.format(
            analysis_of_style=analyses_of_styles[tweet_type],
            tweet_example_blocks=tweet_example_blocks,
            til_content=til_content,
        )
        # print(f"Prompt: {prompt_str}")
        resp = llm.complete(prompt_str)
        print(f"Response AI:\n\n {resp.text}")

        return resp.text
    return ""
