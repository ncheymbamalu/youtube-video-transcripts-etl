"""This module sets up the project's configurations."""

from pathlib import Path, PosixPath

from omegaconf import DictConfig, OmegaConf


class Paths:
    """Configuration for the project's primary directories and filepaths.

    Attributes:
        PROJECT_DIR (PosixPath): Project's root directory.
        DATA_DIR (PosixPath): Project's data directory, ~/data/.
        LOGS_DIR (PosixPath): Project's logs directory, ~/logs/.
        ENV (PosixPath): Project's .env file path, ~/.env.
        CONFIG (PosixPath): Project's configuration file path, ~/config.yaml.
        PROCESSED_DATA (PosixPath): Project's processed data file path,
        ~/data/youtube_transcripts.parquet.
        YOUTUBE_DATA_API (str): YouTube Data API.
    """
    PROJECT_DIR: PosixPath = Path(__file__).parent.parent.absolute()
    DATA_DIR: PosixPath = PROJECT_DIR / "data"
    LOGS_DIR: PosixPath = PROJECT_DIR / "logs"
    ENV: PosixPath = PROJECT_DIR / ".env"
    CONFIG: PosixPath = PROJECT_DIR / "config.yaml"
    PROCESSED_DATA: PosixPath = DATA_DIR / "youtube_transcripts.parquet"
    YOUTUBE_DATA_API: str = "https://www.googleapis.com/youtube/v3/search"


def load_config() -> DictConfig:
    """Loads Paths.CONFIG as a DictConfig object.

    Returns:
        DictConfig: Dictionary-like object with user-defined key-values pairs.
    """
    try:
        return OmegaConf.load(Paths.CONFIG)
    except Exception as e:
        raise e


params_config: DictConfig = load_config().params
