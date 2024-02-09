"""Functions for the Notion Assistant."""
import logging
import os
from copy import deepcopy
from typing import List, Optional

from dotenv import load_dotenv
from notion_client import Client
from notion_client.helpers import iterate_paginated_api
from pydantic import BaseModel
from thefuzz import fuzz

logging.basicConfig(level=logging.INFO)

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
        tweet_type = (
            page.get("properties", {})
            .get("Tweet type ", {})
            .get("select", {})
            .get("name")
        )
        if tweet_type:
            tweet_types.add(tweet_type)
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
    return get_pages_for_database("72f1b016-535b-4ba4-b10b-9c11143c0f52", 1)[0]


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