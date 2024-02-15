"""Functions for the Notion Assistant."""
import os
from copy import deepcopy
from typing import Generator, List, Optional

from dotenv import load_dotenv
import pandas as pd
import pendulum
from notion2md.exporter.block import StringExporter
from notion_client import Client
from notion_client.helpers import iterate_paginated_api
from pydantic import BaseModel
from thefuzz import fuzz

load_dotenv()
notion = Client(auth=os.environ["NOTION_TOKEN"])

# TODO: convert to async


class Database(BaseModel):
    """Database model."""

    id: str
    title: Optional[str]


def get_all_tweet_types() -> List:
    """Get all the pages that are not AI analyzed."""
    # ID of the Library database found at https://www.notion.so/nehiljain/de9aae36d17246a789560747061dfcf5?v=35f15763dd59473180c15dbc3d6c88c5
    database_id = "de9aae36d17246a789560747061dfcf5"
    tweet_types = set()
    for page in iterate_paginated_api(notion.databases.query, database_id=database_id):
        tweet_type = page.get("properties", {}).get("Tweet type ", {}).get("select", {})
        if tweet_type:
            tweet_types.add(tweet_type.get("name"))
    return list(tweet_types)


def get_pages_for_database(database_id: str, limit: int = None) -> List[dict]:
    """Get all pages for a database."""
    if limit:
        # use itertools to limit the number of pages returned
        return list(
            iterate_paginated_api(
                notion.databases.query, database_id=database_id, page_size=limit
            )
        )
    return list(iterate_paginated_api(notion.databases.query, database_id=database_id))


def get_first_tweet_db_page():
    """Get the first tweet database page."""
    # TODO:  Make it always get this page as template page
    get_id = "303210ad98a744378dfd1e5b94226cc6"
    return get_pages_for_database("72f1b016-535b-4ba4-b10b-9c11143c0f52", 1)[0]


def get_all_page_content_as_text(page_id: str) -> str:
    """Get all the content of a page as text by fetching the child blocks."""
    return StringExporter(block_id=page_id).export()


# Write a function to query database with a filter for Tweet type
def get_tweets_for_a_type(tweet_type) -> Generator[dict, None, None]:
    """Get all the pages that are not AI analyzed."""
    # ID of the Library database found at https://www.notion.so/nehiljain/de9aae36d17246a789560747061dfcf5?v=35f15763dd59473180c15dbc3d6c88c5
    database_id = "de9aae36d17246a789560747061dfcf5"
    for page in iterate_paginated_api(
        notion.databases.query,
        database_id=database_id,
        filter={
            "property": "Tweet type ",
            "select": {"equals": tweet_type},
        },
    ):
        yield get_all_page_content_as_text(page["id"])


def get_tweet_examples_block(tweet_examples: pd.DataFrame, tweet_type: str) -> str:
    """Get the tweet examples block."""
    tweet_blocks = """
----------
Example {num}
----------
{tweet_example}"""
    df = tweet_examples.copy()
    # write a function to sample 3 tweets from df given a tweet_type
    sample = df[df["tweet_type"] == tweet_type].sample(3)
    tweet_blocks = """
    ----------
    Example {num}
    ----------
    {tweet_example}"""
    return " \n".join(
        [
            tweet_blocks.format(tweet_example=val, num=num)
            for num, val in enumerate(sample["tweet"].tolist(), start=1)
        ]
    )


# write a function to get all the tweet types and then get all the 5 (page limit) tweets for each type and return a collection of tweet type and tweets
def get_all_tweets() -> pd.DataFrame:
    """Get all the pages that are not AI analyzed."""
    tweet_types = get_all_tweet_types()
    tweet_samples = {}
    for tweet_type in tweet_types:
        tweet_samples[tweet_type] = list(get_tweets_for_a_type(tweet_type))
    return pd.DataFrame(
        {
            "tweet_type": [
                key
                for key in tweet_samples.keys()
                for _ in range(len(tweet_samples[key]))
            ],
            "tweet": [
                tweet for key in tweet_samples.keys() for tweet in tweet_samples[key]
            ],
        }
    )


def create_new_tweet_db_page(title, tweet_type, source_title, tweet_text):
    original_page = get_first_tweet_db_page()
    database_id = original_page["parent"]["database_id"]
    new_properties = deepcopy(original_page.get("properties", {}))
    new_properties["Tweet Text"]["rich_text"][0]["text"]["content"] = tweet_text
    new_properties["Tweet Text"]["rich_text"][0]["plain_text"] = tweet_text
    new_properties["Source Title"]["rich_text"][0]["text"]["content"] = source_title
    new_properties["Source Title"]["rich_text"][0]["plain_text"] = source_title
    new_properties["Title"]["title"][0]["text"]["content"] = title
    new_properties["Title"]["title"][0]["plain_text"] = title
    new_properties.get("properties", {}).get("Should_Publish", {})["checkbox"] = False
    new_properties.get("properties", {}).get("Archive", {})["checkbox"] = False
    new_properties["created_at"] = pendulum.now().to_datetime_string()
    del new_properties["Created time"]
    del new_properties["Last edited time"]
    return notion.pages.create(
        **{"parent": {"database_id": database_id}, "properties": new_properties}
    )


def get_all_database_ids():
    """Get all database ids."""
    database_collection = []
    bad_database_collection = []
    for database in iterate_paginated_api(
        notion.search, payload={"filter": {"value": "database", "property": "object"}}
    ):
        print(f"Database: {database}")
        try:
            database_collection += [
                Database(id=database["id"], title=database["title"][0]["plain_text"])
            ]
        except (IndexError, KeyError) as error:
            print(
                f"Database is faulty: {database['id'].replace('-', '')} with error: {error}"
            )
            bad_database_collection += [
                Database(id=database["id"].replace("-", ""), title="Unknown")
            ]
    return database_collection, bad_database_collection


def filter_database_on_name(database_collection: list[Database], name: str):
    """Filter the database on name using fuzzy matching."""
    db_fuzz = [
        database
        for database in database_collection
        if fuzz.partial_ratio(database.title.lower(), name.lower()) > 90
    ]
    print(f"Total number of databases that are accurate: {len(db_fuzz)} {db_fuzz}")
    return db_fuzz[0]


if __name__ == "__main__":
    db, bdbs = get_all_database_ids()
    tweet_db = filter_database_on_name(db, "tweet")
    print(tweet_db)
    vault_db = filter_database_on_name(db, "library")
    print(get_pages_for_database(tweet_db.id, 1))