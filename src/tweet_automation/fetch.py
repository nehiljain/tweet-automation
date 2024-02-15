# Create a function to reads all the files on a arg directory with extension .md
# use Pathlib
# return a collection of filepath and content

import re
from pathlib import Path


def read_md_files(directory):
    p = Path(directory)
    # get all the md files in the directory and subdirectories

    # filter out the files that are not in the TIL directory
    # filter out files with no content or empty content
    files = list(p.glob("**/*.md"))
    files = [
        file
        for file in files
        # if "TILs" in str(file) or "Posts" in str(file)
        if "Tweet Raw Material" in str(file)
    ]
    files = [file for file in files if file.stat().st_size > 0]
    # return a collection of filepath, filename and content
    return [
        {"filepath": str(file), "filename": file.name, "content": file.read_text()}
        for file in files
    ]


def parse_result_from_llm_response(llm_response):
    # parse the result and return a dictionary
    # with the initial tweet, the rewritten tweet and the critiques
    # Regex to extract the last rewritten tweet
    last_tweet_regex = r"#### Rewritten Tweet\n\n(.+?)\n\n#### Critique"
    match = re.findall(last_tweet_regex, llm_response, re.DOTALL)

    last_tweet = match[-1] if match else "No match found"
    return last_tweet.replace(">", "").strip()