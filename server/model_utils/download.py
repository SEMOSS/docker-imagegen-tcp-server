import os
import json
import logging
import shutil
from huggingface_hub import snapshot_download
from model_utils.model_config import get_model_config
from globals.globals import ServerStatus, set_server_status

logger = logging.getLogger(__name__)


def check_and_download_model_files():
    """
    Check if the model files exist and are for the correct model type.
    If not, delete existing files and download the correct ones.
    """
    set_server_status(ServerStatus.DOWNLOADING_MODEL)

    LOCAL_MODEL_DIR = "./model_files"
    model_config = get_model_config()
    if not model_config:
        logger.error("Model configuration not found.")
        return

    model_repo_id = model_config.get("model_repo_id")
    expected_model_class = model_config.get("expected_model_class")

    model_index_path = os.path.join(LOCAL_MODEL_DIR, "model_index.json")

    # Check if directory exists and is not empty
    if not os.path.exists(LOCAL_MODEL_DIR) or not os.listdir(LOCAL_MODEL_DIR):
        logger.info("Model directory not found or empty. Downloading model files...")
        download_model_files(model_repo_id, LOCAL_MODEL_DIR)
        return

    # Check if model_index.json exists
    if not os.path.exists(model_index_path):
        logger.info(
            "model_index.json not found. Clearing directory and downloading model files..."
        )
        clear_directory(LOCAL_MODEL_DIR)
        download_model_files(model_repo_id, LOCAL_MODEL_DIR)
        return

    # Parse model_index.json and check _class_name
    try:
        with open(model_index_path, "r") as f:
            model_info = json.load(f)

        currently_downloaded_model = model_info.get("_class_name")
        if currently_downloaded_model != expected_model_class:
            logger.info(
                f"Existing model is listed as {currently_downloaded_model}, not {expected_model_class}. Clearing directory and downloading correct model files..."
            )
            clear_directory(LOCAL_MODEL_DIR)
            download_model_files(model_repo_id, LOCAL_MODEL_DIR)
        else:
            logger.info(f"Correct model files for {expected_model_class} found.")
            set_server_status(ServerStatus.READY)
    except json.JSONDecodeError:
        logger.error(
            "Error parsing model_index.json. Clearing directory and downloading model files..."
        )
        clear_directory(LOCAL_MODEL_DIR)
        download_model_files(model_repo_id, LOCAL_MODEL_DIR)


def clear_directory(directory):
    """
    Delete all contents of the specified directory.
    """
    for filename in os.listdir(directory):
        file_path = os.path.join(directory, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            logger.error(f"Failed to delete {file_path}. Reason: {e}")


def download_model_files(model_repo_id, LOCAL_MODEL_DIR):
    """
    Download the model files using snapshot_download.
    """
    snapshot_download(repo_id=model_repo_id, local_dir=LOCAL_MODEL_DIR)
    set_server_status(ServerStatus.READY)
    logger.info("Model files downloaded successfully.")
