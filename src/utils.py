"""This module contains functions that are used by other modules."""

import json
import os

from typing import Any

import polars as pl
import requests

from dotenv import load_dotenv
from requests import Response
from youtube_transcript_api import YouTubeTranscriptApi

from src.config import Paths, params_config
from src.logger import logger

load_dotenv(Paths.ENV)


def process_videos(
    youtube_channel_id: str,
    max_results: int = params_config.max_results
) -> pl.DataFrame:
    """Returns a pl.DataFrame that contains the ID, creation date, title, and transcript
    for a YouTube channel's videos.

    NOTE: the following link, https://www.youtube.com/watch?v=qPKmPaNaCmE&t=1s,
    shows how to find the YouTube channel ID for a given YouTube channel.

    Args:
        youtube_channel_id (str): ID of the YouTube channel whose videos will be processed.
        max_results (int, optional): Maximum number of YouTube videos that will be processed.
        Defaults to params_config.max_results.

    Returns:
        pl.DataFrame: Dataset containing the ID, creation date, title, and transcript
        for a YouTube channel's videos.
    
    """
    try:
        params: dict[str, int | list[str] | str] = {
            "key": os.getenv("YOUTUBE_API_KEY"),
            "channelId": youtube_channel_id,
            "part": ["snippet", "id"],
            "order": "date",
            "maxResults": max_results,
        }
        response: Response = requests.get(Paths.YOUTUBE_DATA_API, params=params)
        if response.status_code == 200:
            items: list[dict[str, Any]] = json.loads(response.text).get("items")
            data: pl.DataFrame = (
                pl.LazyFrame({
                    "video_id": [item.get("id").get("videoId") for item in items],
                    "creation_date": [item.get("snippet").get("publishedAt") for item in items],
                    "title": [item.get("snippet").get("title").strip() for item in items]
                })
                .collect()
            )

            # iterate over each video ID and ...
            records: list[dict[str, str]] = []
            for record in data.to_dicts():
                video_id: str = record.get("video_id")
                title: str = record.get("title")
                try:
                    # extract its transcript, if it's available ...
                    transcript: str = " ".join(
                        d.get("text").strip()
                        for d in (
                            YouTubeTranscriptApi
                            .get_transcript(video_id=video_id, proxies={"http": os.getenv("PROXY")})
                        )
                        if d.get("text")
                    )
                    record = record | {"transcript": transcript.strip()}
                    logger.info(f"SUCCESS: '{title}' has been transcribed.")
                    records.append(record)
                except Exception as e:
                    # otherwise, log an error and assign its transcript to 'unavailable'
                    # NOTE: 'TranscriptsDisabled' would've been returned from this except block ...
                    # had the error been raised instead of being logged
                    error: str = str(e).split("https", maxsplit=1)[0].strip()
                    logger.info(f"ERROR: {error}, '{title}'. It will be removed.")
                    record = record | {"transcript": "unavailable"}
                    records.append(record)
            bad: list[str] = ["&#39;", "&quot;", "&amp;", "  "]
            good: list[str] = ["'", "'", "&", " "]
            return (
                pl.DataFrame(records)
                .with_columns(
                    pl.col("title").str.replace_many(bad, good),
                    pl.col("creation_date").str.to_datetime().dt.replace_time_zone(None),
                    pl.col("transcript").str.replace_many(bad, good).cast(pl.String)
                )
                .filter(pl.col("transcript").ne("unavailable"))
            )
        logger.info(
            f"Invalid request. Unable to access videos from the YouTube channel ID, \
'{youtube_channel_id}'."
        )
        return pl.DataFrame(schema=["video_id", "creation_date", "title", "transcript"])
    except Exception as e:
        raise e
