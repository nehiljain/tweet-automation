from typing import Dict, List

import pandas as pd
from notion.databases import (
    get_all_tweets,
    get_pages_for_database,
    get_tweet_examples_block,
)
from tweet_automation.ai import generate_tweet_from_inspiration_prompt
from tweet_automation.fetch import parse_result_from_llm_response, read_md_files


def get_notion_tweet_df(pages: List[Dict[str, str]]) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "tweet_type": [
                page["properties"]["Title"]["title"][0]["text"]["content"].split(":")[0]
                for page in pages
            ],
            "tweet_filename": [
                page["properties"]["Title"]["title"][0]["text"]["content"]
                .replace(
                    f'{page["properties"]["Title"]["title"][0]["text"]["content"].split(":")[0]}:',
                    "",
                )
                .strip()
                .replace("- Tweet", "")
                .strip()
                for page in pages
            ],
        }
    )


def process_tweet_type(
    tweet_type: str,
    notion_tweet_df: pd.DataFrame,
    tweet_example_block: str,
    notes_contents: List[Dict[str, str]],
) -> None:
    for file_data in notes_contents:
        # Check if tweet_type and filename already exists in the notion_tweet_df
        if (
            tweet_type in notion_tweet_df["tweet_type"].values
            and file_data["filename"] in notion_tweet_df["tweet_filename"].values
        ):
            print(f'{file_data["filename"]} -- "{tweet_type}" Already Tweeted.')
            continue
        print(f"Processing {file_data['filename']} -- {tweet_type}...")
        tweet_response = generate_tweet_from_inspiration_prompt(
            tweet_type=tweet_type,
            tweet_example_blocks=tweet_example_block,
            til_content=file_data["content"],
        )
        tweet = parse_result_from_llm_response(tweet_response)
        print(f"Tweet: {tweet}\n\n\n")
        # create_new_tweet_db_page(
        #     title=f'{tweet_type}: {file_data["filename"]} - Tweet',
        #     tweet_type=tweet_type,
        #     source_title=file_data["filename"],
        #     tweet_text=tweet,
        # )


def main() -> None:
    NOTES_DIR = "/Users/nehiljain/Library/Mobile Documents/iCloud~md~obsidian/Documents"
    notes_contents = read_md_files(NOTES_DIR)
    # print(notes_contents)
    tweets_df = get_all_tweets()
    pages = get_pages_for_database("72f1b016-535b-4ba4-b10b-9c11143c0f52")
    notion_tweet_df = get_notion_tweet_df(pages)
    for tweet_type in tweets_df["tweet_type"].unique():
        try:
            tweet_example_block = get_tweet_examples_block(
                tweets_df, tweet_type=tweet_type
            )
        except ValueError:
            print(f"No tweet examples found for {tweet_type}. Skipping...")
            continue
        process_tweet_type(
            tweet_type,
            notion_tweet_df,
            tweet_example_block,
            notes_contents,
        )


if __name__ == "__main__":
    main()