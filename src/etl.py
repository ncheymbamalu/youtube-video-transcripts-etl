"""This module provides functionality for executing the YouTube video transcripts ETL pipeline."""

import polars as pl

from dotenv import load_dotenv
from joblib import Parallel, delayed
from omegaconf import ListConfig
from tqdm import tqdm

from src.config import Paths, params_config
from src.utils import process_videos

load_dotenv(Paths.ENV)


def main(youtube_channel_ids: ListConfig | list[str]) -> None:
    """Processes a list of YouTube channels in parallel, that is, extracts the ID,
    creation date, title, and transcript from their videos, generates embeddings from
    their transcripts, and writes the resulting data to a local PostgreSQL database.

    Args:
        youtube_channel_ids (ListConfig | list[str]): YouTube channel IDs.
    """
    try:
        # load the processed data
        processed_data: pl.DataFrame = pl.read_parquet(
            Paths.DATA_DIR / "youtube_transcripts.parquet"
        )

        # a list of records (YouTube video IDs) that have already been processed
        processed_video_ids: list[str] = processed_data["video_id"].unique().to_list()

        # iterate over each YouTube channel and create a pl.LazyFrame that contains
        # the ID, creation date, title, and transcript of its 50 most recent videos
        lazyframes: list[pl.LazyFrame] = Parallel(n_jobs=-1)(
            delayed(process_videos)(youtube_channel_id)
            for youtube_channel_id in tqdm(youtube_channel_ids)
        )

        # vertically concatenate the pl.LazyFrames in the 'lazyframes' list, and ...
        # only keep the records that have not been processed
        data: pl.DataFrame = (
            pl.concat(lazyframes, how="vertical")
            .unique(subset="video_id", keep="first")
            .with_columns(pl.col("creation_date").dt.replace_time_zone(None))
            .filter(~pl.col("video_id").is_in(processed_video_ids))
            .collect()
        )

        # update the processed data
        processed_data = (
            processed_data if data.is_empty()
            else (
                pl.concat((processed_data, data), how="vertical")
                .sort(by=["creation_date", "video_id"], descending=[True, False])
            )
        )
        processed_data.write_parquet(Paths.DATA_DIR / "youtube_transcripts.parquet")
    except Exception as e:
        raise e


if __name__ == "__main__":
    channel_ids: ListConfig = params_config.youtube_channel_ids
    main(channel_ids)
