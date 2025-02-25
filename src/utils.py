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
) -> pl.LazyFrame:
    """Returns a pl.DataFrame that contains the ID, creation date, title, and transcript
    for a YouTube channel's videos.

    NOTE: the following link, https://www.youtube.com/watch?v=qPKmPaNaCmE&t=1s,
    shows how to find the YouTube channel ID for a given YouTube channel.

    Args:
        youtube_channel_id (str): ID of the YouTube channel whose videos will be processed.
        max_results (int, optional): Maximum number of YouTube videos that will be processed.
        Defaults to params_config.max_results.

    Returns:
        pl.LazyFrame: Dataset containing the ID, creation date, title, and transcript
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
            logger.info(
                f"Extracting video transcripts from the \
'{items[0].get('snippet').get('channelTitle')}' YouTube channel."
            )
            records: list[dict[str, str]] = []
            for item in items:
                try:
                    record: dict[str, None | str] = {
                        "video_id": item.get("id").get("videoId"),
                        "creation_date": item.get("snippet").get("publishedAt"),
                        "title": item.get("snippet").get("title").strip(),
                        "transcript": " ".join(
                            transcript_dict.get("text").strip()
                            for transcript_dict in YouTubeTranscriptApi.get_transcript(
                                item.get("id").get("videoId")
                            )
                            if transcript_dict.get("text")
                        ),
                    }
                except Exception:
                    logger.info(
                        f"Transcript unavailable. '{item.get('snippet').get('title')}' will be \
removed."
                    )
                    record = {
                        "video_id": item.get("id").get("videoId"),
                        "creation_date": item.get("snippet").get("publishedAt"),
                        "title": item.get("snippet").get("title").strip(),
                        "transcript": None,
                    }
                records.append(record)
            incorrect_strings: list[str] = ["&#39;", "&quot;", "&amp;", "  "]
            correct_strings: list[str] = ["'", "'", "&", " "]
            return (
                pl.LazyFrame(records)
                .with_columns(
                    pl.col("creation_date").str.to_datetime(),
                    pl.col("title").str.replace_many(incorrect_strings, correct_strings),
                    pl.col("transcript").str.replace_many(incorrect_strings, correct_strings),
                )
                .drop_nulls(subset="transcript")
            )
        logger.info(
            f"Invalid request. Unable to access videos from the YouTube channel ID, \
'{youtube_channel_id}'."
        )
        return pl.LazyFrame(schema=["video_id", "creation_date", "title", "transcript"])
    except Exception as e:
        raise e
