"""This module provides functionality for transcribing videos from a list of YouTube channels."""

import polars as pl

from dotenv import load_dotenv
from joblib import Parallel, delayed
from omegaconf import ListConfig
from tqdm import tqdm

from src.config import Paths, params_config
from src.utils import transcribe_videos

load_dotenv(Paths.ENV)


def main(youtube_channel_ids: ListConfig | list[str]) -> None:
    """Processes a list of YouTube channels in parallel, that is, extracts the ID,
    creation date, title, and transcript from their videos, adds them to the previously
    transcribed videos, and writes the data to Paths.PROCESSED_DATA.

    Args:
        youtube_channel_ids (ListConfig | list[str]): YouTube channel IDs.
    """
    try:
        # load the processed data
        processed_data: pl.DataFrame = pl.read_parquet(Paths.PROCESSED_DATA)

        # a list of video IDs that have already been transcribed
        transcribed_video_ids: list[str] = processed_data["video_id"].unique().to_list()

        # iterate over each YouTube channel and create a pl.DataFrame that contains
        # the ID, creation date, title, and transcript of its 50 most recent videos
        dfs: list[pl.DataFrame] = Parallel(n_jobs=-1)(
            delayed(transcribe_videos)(youtube_channel_id)
            for youtube_channel_id in tqdm(youtube_channel_ids)
        )

        # vertically concatenate the pl.DataFrames in the 'dfs' list, and ...
        # only keep records whose video has not been transcribed
        data: pl.DataFrame = (
            pl.concat(dfs, how="vertical")
            .unique(subset="video_id", keep="first")
            .filter(~pl.col("video_id").is_in(transcribed_video_ids))
        )

        # update the processed data and write it back to Paths.PROCESSED_DATA
        processed_data = (
            processed_data if data.is_empty()
            else (
                pl.concat((processed_data, data), how="vertical")
                .sort(by=["creation_date", "video_id"], descending=[True, False])
            )
        )
        processed_data.write_parquet(Paths.PROCESSED_DATA)
    except Exception as e:
        raise e


if __name__ == "__main__":
    channel_ids: ListConfig = params_config.youtube_channel_ids
    main(channel_ids)
