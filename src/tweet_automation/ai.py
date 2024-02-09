
import logging
from functools import partial

from llama_index.llms import CompletionResponse, Ollama

from tweet_automation.templates import generate_contrarian_tweet_from_inspiration_prompt

logging.basicConfig(level=logging.DEBUG)

# TODO: Convert to async
def generate_tweet_from_inspiration_prompt(
    prompt: str, tweet_content
) -> CompletionResponse:
    """
    Generate a tweet from an inspiration prompt.
    """
    llm = Ollama(model="mistral", request_timeout=300.0)
    prompt_str = prompt.format(til_content=tweet_content)
    print(f"Prompt: {prompt_str}")
    resp = llm.complete(prompt_str)
    return resp


# write a new function to generate a tweet from an inspiration prompt using generate_contratian_tweet_from_inspiration_prompt
generate_contrarian_tweet_from_inspiration_prompt = partial(
    generate_tweet_from_inspiration_prompt,
    generate_contrarian_tweet_from_inspiration_prompt,
)

# TODO: write a func with story style tweets
# TODO: write a func with ['Story', 'Listicle', 'CTA', 'Questioning community', 'Joke or meme', 'Lessons', 'Resources', 'Contrarian Take', 'Recipe', 'Past vs Present'] style tweets


