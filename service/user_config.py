import io
import logging
import os
import re
import shutil
import tempfile
import uuid
import zipfile
from dataclasses import dataclass

import boto3
from botocore.exceptions import BotoCoreError, ClientError, NoCredentialsError, PartialCredentialsError

DEFAULT_S3_BUCKET_NAME = "metatrader5-config-dev-824597117854-ap-southeast-1-an"
DEFAULT_AWS_REGION = "ap-southeast-1"
DEFAULT_USER_CONFIG_USER_ID = "0"
DEFAULT_USER_CONFIG_SERVER = "EBCFinancialGroupKY-Demo"
DEFAULT_USER_CONFIG_ACCOUNT = "51236"
DEFAULT_USER_CONFIG_OBJECT_NAME = "Config.zip"
DEFAULT_MT5_CONFIG_DIR = r"C:\Program Files\MetaTrader 5\Config"

logger = logging.getLogger("MetaTrader5-service.user_config")


class UserConfigError(Exception):
    pass


class UserConfigNotFoundError(UserConfigError):
    pass


class AwsCredentialsUnavailableError(UserConfigError):
    pass


class UserConfigDownloadError(UserConfigError):
    pass


class UserConfigApplyError(UserConfigError):
    pass


@dataclass(frozen=True)
class UserConfigSettings:
    s3_bucket_name: str
    aws_region: str
    user_id: str
    server: str
    account: str
    server_slug: str
    object_key: str
    target_config_dir: str


def _env_or_default(name: str, default: str) -> str:
    value = os.getenv(name)
    if value is None:
        return default
    normalized = value.strip()
    return normalized if normalized else default


def to_server_slug(server: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", server.strip().lower())
    slug = re.sub(r"_+", "_", slug)
    return slug.strip("_")


def build_user_config_key(user_id: str, server: str, account: str) -> str:
    return f"{user_id}/{to_server_slug(server)}/{account}/{DEFAULT_USER_CONFIG_OBJECT_NAME}"


def get_user_config_settings() -> UserConfigSettings:
    s3_bucket_name = _env_or_default("S3_BUCKET_NAME", DEFAULT_S3_BUCKET_NAME)
    aws_region = _env_or_default("AWS_REGION", DEFAULT_AWS_REGION)
    user_id = _env_or_default("USER_CONFIG_USER_ID", DEFAULT_USER_CONFIG_USER_ID)
    server = _env_or_default("USER_CONFIG_SERVER", DEFAULT_USER_CONFIG_SERVER)
    account = _env_or_default("USER_CONFIG_ACCOUNT", DEFAULT_USER_CONFIG_ACCOUNT)
    server_slug = to_server_slug(server)

    return UserConfigSettings(
        s3_bucket_name=s3_bucket_name,
        aws_region=aws_region,
        user_id=user_id,
        server=server,
        account=account,
        server_slug=server_slug,
        object_key=build_user_config_key(user_id, server, account),
        target_config_dir=DEFAULT_MT5_CONFIG_DIR,
    )


def _create_s3_client(settings: UserConfigSettings):
    return boto3.client("s3", region_name=settings.aws_region)


def _download_user_config_zip(settings: UserConfigSettings) -> bytes:
    try:
        logger.info(
            "downloading user config from S3: bucket=%s key=%s",
            settings.s3_bucket_name,
            settings.object_key,
        )
        response = _create_s3_client(settings).get_object(
            Bucket=settings.s3_bucket_name,
            Key=settings.object_key,
        )
        zip_bytes = response["Body"].read()
        logger.info("downloaded user config from S3: bytes=%s", len(zip_bytes))
        return zip_bytes
    except (NoCredentialsError, PartialCredentialsError) as exc:
        raise AwsCredentialsUnavailableError("AWS credentials are not available.") from exc
    except ClientError as exc:
        error = exc.response.get("Error", {})
        error_code = str(error.get("Code", ""))
        error_message = str(error.get("Message", ""))
        if error_code in ("404", "NoSuchKey", "NotFound"):
            raise UserConfigNotFoundError("User config not found in S3.") from exc
        raise UserConfigDownloadError(
            f"Failed to download user config from S3: {error_code or 'ClientError'} {error_message}".strip()
        ) from exc
    except BotoCoreError as exc:
        raise UserConfigDownloadError(f"Failed to download user config from S3: {str(exc)}") from exc


def _safe_extract_zip(zip_bytes: bytes, extract_dir: str) -> None:
    extract_root = os.path.abspath(extract_dir)
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as archive:
        for member in archive.infolist():
            member_path = os.path.abspath(os.path.join(extract_root, member.filename))
            if member_path != extract_root and not member_path.startswith(extract_root + os.sep):
                raise UserConfigApplyError("Config.zip contains invalid paths.")
        archive.extractall(extract_root)


def _replace_config_directory(extracted_config_dir: str, target_config_dir: str) -> None:
    target_parent_dir = os.path.dirname(target_config_dir)
    if not os.path.isdir(target_parent_dir):
        raise UserConfigApplyError(f"MetaTrader 5 directory not found: {target_parent_dir}")

    backup_dir = None
    try:
        logger.info("applying user config to target directory: target=%s", target_config_dir)
        if os.path.exists(target_config_dir):
            backup_dir = os.path.join(target_parent_dir, f"Config.backup.{uuid.uuid4().hex}")
            logger.info("backing up existing Config directory: backup=%s", backup_dir)
            shutil.move(target_config_dir, backup_dir)
        shutil.move(extracted_config_dir, target_config_dir)
    except Exception as exc:
        try:
            if backup_dir and os.path.exists(backup_dir) and not os.path.exists(target_config_dir):
                shutil.move(backup_dir, target_config_dir)
        except Exception:
            pass
        raise UserConfigApplyError(f"Failed to replace Config directory: {str(exc)}") from exc

    if backup_dir and os.path.exists(backup_dir):
        try:
            shutil.rmtree(backup_dir)
        except Exception:
            pass
    logger.info("user config applied successfully: target=%s", target_config_dir)


def _apply_user_config_zip(zip_bytes: bytes, target_config_dir: str) -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        _safe_extract_zip(zip_bytes, temp_dir)
        extracted_config_dir = os.path.join(temp_dir, "Config")
        if not os.path.isdir(extracted_config_dir):
            raise UserConfigApplyError("Config.zip root directory must contain Config/.")
        _replace_config_directory(extracted_config_dir, target_config_dir)


def download_and_apply_user_config() -> UserConfigSettings:
    settings = get_user_config_settings()
    logger.info(
        "resolved user config settings: bucket=%s region=%s key=%s target=%s",
        settings.s3_bucket_name,
        settings.aws_region,
        settings.object_key,
        settings.target_config_dir,
    )
    zip_bytes = _download_user_config_zip(settings)
    _apply_user_config_zip(zip_bytes, settings.target_config_dir)
    return settings
