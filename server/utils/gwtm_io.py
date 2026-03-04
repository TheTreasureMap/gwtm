import fsspec
import json
import os
import re
import tempfile


def _get_swift_conn(config):
    """
    Get Swift connection with appropriate authentication method.

    Supports both application credentials and username/password authentication.
    Application credential IDs are detected as 32-character hex strings.

    Args:
        config: Configuration object with Swift credentials

    Returns:
        Swift Connection object
    """
    try:
        from keystoneauth1.identity import v3
        from keystoneauth1 import session
        from swiftclient import Connection as SwiftConnection
    except ImportError:
        raise Exception(
            "Swift dependencies not installed. Install python-swiftclient, "
            "python-keystoneclient, and keystoneauth1"
        )

    # Detect if using application credentials (32-character hex string)
    is_app_cred = bool(re.match(r"^[a-f0-9]{32}$", config.OS_USERNAME or ""))

    if is_app_cred:
        # Use application credential authentication
        auth = v3.ApplicationCredential(
            auth_url=config.OS_AUTH_URL,
            application_credential_id=config.OS_USERNAME,
            application_credential_secret=config.OS_PASSWORD,
        )

        # Create authenticated session
        sess = session.Session(auth=auth)

        # Create Swift connection with session
        conn = SwiftConnection(
            session=sess, os_options={"object_storage_url": config.OS_STORAGE_URL}
        )
    else:
        # Use username/password authentication
        conn = SwiftConnection(
            authurl=config.OS_AUTH_URL,
            user=config.OS_USERNAME,
            key=config.OS_PASSWORD,
            os_options={
                "user_domain_name": config.OS_USER_DOMAIN_NAME,
                "project_domain_name": config.OS_PROJECT_DOMAIN_NAME,
                "project_name": config.OS_PROJECT_NAME,
            },
            auth_version="3",
        )

    return conn


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


def _is_local(source, config):
    """Check if we should use local filesystem storage."""
    if source == "local":
        return True
    return hasattr(config, "DEVELOPMENT_MODE") and config.DEVELOPMENT_MODE


def _get_local_dir(config):
    """Return the local storage directory path."""
    return getattr(config, "DEVELOPMENT_STORAGE_DIR", "./dev_storage")


def _local_path(local_dir, filename):
    """Build the local file path, preserving subdirectory structure."""
    return os.path.join(local_dir, filename)


def download_gwtm_file(filename, source="s3", config=None, decode=True):
    """
    Download a file from the GWTM storage.

    Args:
        filename: File path/name to download
        source: Storage source ('s3', 'abfs', 'swift', or 'local')
        config: Configuration object with credentials
        decode: Whether to decode the file content to UTF-8

    Returns:
        File content (string if decode=True, bytes if decode=False)
    """
    # If filename is a full HTTP/HTTPS URL (e.g. a GraceDB skymap URL),
    # download it directly rather than routing through the storage backend.
    if filename and filename.startswith(("http://", "https://")):
        import requests
        response = requests.get(filename, timeout=60)
        response.raise_for_status()
        content = response.content
        return content.decode("utf-8") if decode else content

    # Local filesystem storage
    if source == "local":
        local_dir = _get_local_dir(config)
        path = _local_path(local_dir, filename)
        if os.path.exists(path):
            with open(path, "rb") as f:
                content = f.read()
                return content.decode("utf-8") if decode else content
        raise FileNotFoundError(f"Local file not found: {path}")

    # Handle Swift separately (doesn't use fsspec)
    if source == "swift":
        try:
            conn = _get_swift_conn(config)
            headers, content = conn.get_object(config.OS_CONTAINER_NAME, filename)
            if decode:
                return content.decode("utf-8")
            else:
                return content
        except Exception as e:
            raise Exception(f"Error reading Swift file {filename}: {str(e)}")

    # Handle S3 and Azure with fsspec
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
        # Fall back to local storage in development mode
        if _is_local(source, config):
            local_dir = _get_local_dir(config)
            path = _local_path(local_dir, filename.split("/")[-1])
            if os.path.exists(path):
                with open(path, "rb") as f:
                    content = f.read()
                    return content.decode("utf-8") if decode else content

        raise Exception(f"Error reading {source} file {filename}: {str(e)}")


def upload_gwtm_file(content, filename, source="s3", config=None):
    """
    Upload a file to GWTM storage.

    Args:
        content: File content to upload
        filename: Destination file path/name
        source: Storage source ('s3', 'abfs', 'swift', or 'local')
        config: Configuration object with credentials

    Returns:
        True if upload successful
    """
    # Local filesystem storage
    if _is_local(source, config):
        local_dir = _get_local_dir(config)
        path = _local_path(local_dir, filename)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        mode = "wb" if isinstance(content, bytes) else "w"
        with open(path, mode) as f:
            f.write(content)
        return True

    # Handle Swift separately (doesn't use fsspec)
    if source == "swift":
        try:
            conn = _get_swift_conn(config)
            # Swift expects bytes, convert if string
            if isinstance(content, str):
                content = content.encode("utf-8")
            conn.put_object(config.OS_CONTAINER_NAME, filename, content)
            return True
        except Exception as e:
            raise Exception(f"Error uploading to Swift file {filename}: {str(e)}")

    # Normal cloud storage upload (S3, Azure)
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
        source: Storage source ('s3', 'abfs', 'swift', or 'local')
        config: Configuration object with credentials

    Returns:
        List of files in the container
    """
    # Local filesystem storage
    if _is_local(source, config):
        local_dir = _get_local_dir(config)
        container_dir = os.path.join(local_dir, container)

        if os.path.exists(container_dir) and os.path.isdir(container_dir):
            return sorted(
                [os.path.join(container, f) for f in os.listdir(container_dir)]
            )
        elif os.path.exists(local_dir):
            # If the specific container doesn't exist, list files matching the prefix
            return sorted([f for f in os.listdir(local_dir) if f.startswith(container)])
        return []

    # Handle Swift separately (doesn't use fsspec)
    if source == "swift":
        try:
            conn = _get_swift_conn(config)
            # List objects with the specified prefix
            headers, objects = conn.get_container(
                config.OS_CONTAINER_NAME, prefix=f"{container}/"
            )
            ret = []
            for obj in objects:
                # obj is a dict with 'name', 'bytes', 'content_type', etc.
                name = obj.get("name", "")
                if name != f"{container}/":  # Exclude the directory itself
                    ret.append(name)
            return sorted(ret)
        except Exception:
            # If listing fails (e.g., container doesn't exist), return empty list
            return []

    # Normal cloud storage listing (S3, Azure)
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
    except Exception:
        # If listing fails (e.g., container doesn't exist), return empty list
        return []


def delete_gwtm_files(keys, source="s3", config=None):
    """
    Delete files from GWTM storage.

    Args:
        keys: Single key or list of keys to delete
        source: Storage source ('s3', 'abfs', 'swift', or 'local')
        config: Configuration object with credentials

    Returns:
        True if delete successful
    """
    # Convert single key to list
    if isinstance(keys, str):
        keys = [keys]

    # Local filesystem storage
    if _is_local(source, config):
        local_dir = _get_local_dir(config)
        for key in keys:
            path = _local_path(local_dir, key)
            if os.path.exists(path):
                os.remove(path)
        return True

    # Handle Swift separately (doesn't use fsspec)
    if source == "swift":
        try:
            conn = _get_swift_conn(config)
            for k in keys:
                conn.delete_object(config.OS_CONTAINER_NAME, k)
            return True
        except Exception as e:
            raise Exception(f"Error deleting from Swift: {str(e)}")

    # Normal cloud storage deletion (S3, Azure)
    if source == "s3":
        # Add bucket prefix if not present
        for i, k in enumerate(keys):
            if f"{config.AWS_BUCKET}/" not in k:
                keys[i] = f"{config.AWS_BUCKET}/{k}"

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
    source = config.STORAGE_BUCKET_SOURCE

    # Local filesystem cache
    if _is_local(source, config):
        local_dir = _get_local_dir(config)
        cache_dir = os.path.join(local_dir, "cache")
        cache_file = os.path.join(cache_dir, key.split("/")[-1])

        if os.path.exists(cache_file):
            with open(cache_file, "r") as f:
                return f.read()
        return None

    # Normal cloud storage cache access
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
    source = config.STORAGE_BUCKET_SOURCE

    # Local filesystem cache
    if _is_local(source, config):
        local_dir = _get_local_dir(config)
        cache_dir = os.path.join(local_dir, "cache")
        os.makedirs(cache_dir, exist_ok=True)

        cache_file = os.path.join(cache_dir, key.split("/")[-1])

        with open(cache_file, "w") as f:
            json.dump(contents, f)
        return True

    # Normal cloud storage cache setting
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
        source: Storage source ('s3', 'abfs', 'swift', or 'local')
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
