import fsspec
import json
import os
import tempfile


def _get_fs(source, config):
    """
    Get the appropriate filesystem based on source.

    Args:
        source: Storage source ('s3' or 'abfs')
        config: Configuration object with credentials

    Returns:
        Filesystem object
    """
    try:
        if source == "s3":
            return fsspec.filesystem(
                "s3", key=config.AWS_ACCESS_KEY_ID, secret=config.AWS_SECRET_ACCESS_KEY
            )
        if source == "abfs":
            return fsspec.filesystem(
                "abfs",
                account_name=config.AZURE_ACCOUNT_NAME,
                account_key=config.AZURE_ACCOUNT_KEY,
            )
    except Exception as e:
        raise Exception(f"Error in creating {source} filesystem: {str(e)}")


def download_gwtm_file(filename, source="s3", config=None, decode=True):
    """
    Download a file from the GWTM storage.

    Args:
        filename: File path/name to download
        source: Storage source ('s3' or 'abfs')
        config: Configuration object with credentials
        decode: Whether to decode the file content to UTF-8

    Returns:
        File content (string if decode=True, bytes if decode=False)
    """
    fs = _get_fs(source=source, config=config)

    if source == "s3" and f"{config.AWS_BUCKET}/" not in filename:
        filename = f"{config.AWS_BUCKET}/{filename}"

    try:
        s3file = fs.open(filename, "rb")

        with s3file as _file:
            if decode:
                return _file.read().decode("utf-8")
            else:
                return _file.read()
    except Exception as e:
        # In development mode, we might want to simulate file access
        # This would allow the system to function without actual cloud storage
        if hasattr(config, "DEVELOPMENT_MODE") and config.DEVELOPMENT_MODE:
            # Check if we have a local development directory
            dev_dir = getattr(config, "DEVELOPMENT_STORAGE_DIR", "./dev_storage")
            local_path = os.path.join(dev_dir, filename.split("/")[-1])

            # If the file exists locally, return its contents
            if os.path.exists(local_path):
                with open(local_path, "rb") as f:
                    content = f.read()
                    return content.decode("utf-8") if decode else content

        # If we're not in development mode or couldn't find a local file
        raise Exception(f"Error reading {source} file {filename}: {str(e)}")


def upload_gwtm_file(content, filename, source="s3", config=None):
    """
    Upload a file to GWTM storage.

    Args:
        content: File content to upload
        filename: Destination file path/name
        source: Storage source ('s3' or 'abfs')
        config: Configuration object with credentials

    Returns:
        True if upload successful
    """
    # In development mode, we might want to simulate file upload
    if hasattr(config, "DEVELOPMENT_MODE") and config.DEVELOPMENT_MODE:
        dev_dir = getattr(config, "DEVELOPMENT_STORAGE_DIR", "./dev_storage")
        os.makedirs(dev_dir, exist_ok=True)
        local_path = os.path.join(dev_dir, filename.split("/")[-1])

        # Write to local file
        mode = "wb" if isinstance(content, bytes) else "w"
        with open(local_path, mode) as f:
            f.write(content)
        return True

    # Normal cloud storage upload
    fs = _get_fs(source=source, config=config)

    if source == "s3" and f"{config.AWS_BUCKET}/" not in filename:
        filename = f"{config.AWS_BUCKET}/{filename}"

    try:
        mode = "wb" if isinstance(content, bytes) else "w"
        with fs.open(filename, mode) as f:
            f.write(content)
        return True
    except Exception as e:
        raise Exception(f"Error uploading to {source} file {filename}: {str(e)}")


def list_gwtm_bucket(container, source="s3", config=None):
    """
    List contents of a bucket/container.

    Args:
        container: Container/folder to list
        source: Storage source ('s3' or 'abfs')
        config: Configuration object with credentials

    Returns:
        List of files in the container
    """
    # In development mode, we might want to simulate bucket listing
    if hasattr(config, "DEVELOPMENT_MODE") and config.DEVELOPMENT_MODE:
        dev_dir = getattr(config, "DEVELOPMENT_STORAGE_DIR", "./dev_storage")
        container_dir = os.path.join(dev_dir, container)

        if os.path.exists(container_dir) and os.path.isdir(container_dir):
            return sorted(
                [os.path.join(container, f) for f in os.listdir(container_dir)]
            )
        elif os.path.exists(dev_dir):
            # If the specific container doesn't exist, list all files that match the prefix
            return sorted([f for f in os.listdir(dev_dir) if f.startswith(container)])
        return []

    # Normal cloud storage listing
    fs = _get_fs(source=source, config=config)

    try:
        if source == "s3":
            bucket_content = fs.ls(f"{config.AWS_BUCKET}/{container}")
            ret = []
            for b in bucket_content:
                split_b = b.split(f"{config.AWS_BUCKET}/")[1]
                if split_b != f"{container}/":
                    ret.append(split_b)
            return sorted(ret)

        ret = fs.ls(container)
        return sorted(ret)
    except Exception as e:
        # If listing fails (e.g., container doesn't exist), return empty list
        return []


def delete_gwtm_files(keys, source="s3", config=None):
    """
    Delete files from GWTM storage.

    Args:
        keys: Single key or list of keys to delete
        source: Storage source ('s3' or 'abfs')
        config: Configuration object with credentials

    Returns:
        True if delete successful
    """
    # In development mode, we might want to simulate file deletion
    if hasattr(config, "DEVELOPMENT_MODE") and config.DEVELOPMENT_MODE:
        dev_dir = getattr(config, "DEVELOPMENT_STORAGE_DIR", "./dev_storage")

        # Convert single key to list
        if isinstance(keys, str):
            keys = [keys]

        # Delete local files
        for key in keys:
            local_path = os.path.join(dev_dir, key.split("/")[-1])
            if os.path.exists(local_path):
                os.remove(local_path)
        return True

    # Normal cloud storage deletion
    if source == "s3":
        if isinstance(keys, list):
            for i, k in enumerate(keys):
                if f"{config.AWS_BUCKET}/" not in k:
                    keys[i] = f"{config.AWS_BUCKET}/{k}"
        elif isinstance(keys, str) and f"{config.AWS_BUCKET}/" not in keys:
            keys = f"{config.AWS_BUCKET}/{keys}"
            keys = [keys]  # Convert to list for consistency

    fs = _get_fs(source=source, config=config)

    try:
        for k in keys:
            fs.rm(k)
        return True
    except Exception as e:
        raise Exception(f"Error deleting from {source}: {str(e)}")


def get_cached_file(key, config):
    """
    Get a cached file from storage.

    Args:
        key: Cache key
        config: Configuration object with credentials

    Returns:
        File content or None if not found
    """
    # In development mode, we might want to use a local cache
    if hasattr(config, "DEVELOPMENT_MODE") and config.DEVELOPMENT_MODE:
        dev_dir = getattr(config, "DEVELOPMENT_STORAGE_DIR", "./dev_storage")
        cache_dir = os.path.join(dev_dir, "cache")
        cache_file = os.path.join(cache_dir, key.split("/")[-1])

        if os.path.exists(cache_file):
            with open(cache_file, "r") as f:
                return f.read()
        return None

    # Normal cloud storage cache access
    source = config.STORAGE_BUCKET_SOURCE

    try:
        cached_files = list_gwtm_bucket("cache", source, config)

        if key in cached_files:
            return download_gwtm_file(key, source, config)
        else:
            return None
    except Exception:
        return None


def set_cached_file(key, contents, config):
    """
    Set a cached file in storage.

    Args:
        key: Cache key
        contents: Content to cache (will be JSON serialized)
        config: Configuration object with credentials

    Returns:
        True if successful
    """
    # In development mode, we might want to use a local cache
    if hasattr(config, "DEVELOPMENT_MODE") and config.DEVELOPMENT_MODE:
        dev_dir = getattr(config, "DEVELOPMENT_STORAGE_DIR", "./dev_storage")
        cache_dir = os.path.join(dev_dir, "cache")
        os.makedirs(cache_dir, exist_ok=True)

        cache_file = os.path.join(cache_dir, key.split("/")[-1])

        with open(cache_file, "w") as f:
            json.dump(contents, f)
        return True

    # Normal cloud storage cache setting
    source = config.STORAGE_BUCKET_SOURCE

    try:
        return upload_gwtm_file(json.dumps(contents), key, source, config)
    except Exception:
        return False


def download_to_temp_file(filename, source="s3", config=None):
    """
    Download a file to a temporary file and return the path.
    Useful for binary files like FITS files that need to be processed by external libraries.

    Args:
        filename: File to download
        source: Storage source ('s3' or 'abfs')
        config: Configuration object with credentials

    Returns:
        Path to temporary file
    """
    content = download_gwtm_file(filename, source, config, decode=False)

    # Create a temporary file
    temp_file = tempfile.NamedTemporaryFile(delete=False)
    temp_file.write(content)
    temp_file.close()

    return temp_file.name
