import logging

from notion.databases import create_new_tweet_db_page
from tweet_automation.ai import generate_contrarian_tweet_from_inspiration_prompt
from tweet_automation.fetch import parse_result_from_llm_response, read_md_files

logging.basicConfig(level=logging.DEBUG)


def main():
    TIL_DIR = "/Users/nehiljain/Library/Mobile Documents/iCloud~md~obsidian/Documents"
    file_datas = read_md_files(TIL_DIR)
    print(file_datas)

    # TODO: find all the tweets already generated with a given type from notion and filter out the files that have already been tweeted
    for file_data in file_datas:
        tweet_response = generate_contrarian_tweet_from_inspiration_prompt(
            file_data["content"]
        )
        tweet = parse_result_from_llm_response(tweet_response.text)
        print(f"Tweet: {tweet}")
        create_new_tweet_db_page(
            title="Contrarian Take: " + file_data["filename"] + " - " + "Tweet",
            tweet_type="Contrarian Take",
            source_title=file_data["filename"],
            tweet_text=tweet,
        )


if __name__ == "__main__":
    main()