import fsspec

def _get_fs(source, config):
    try:
        if source == 's3':
            return fsspec.filesystem(f"s3", key=config.AWS_ACCESS_KEY_ID, secret=config.AWS_SECRET_ACCESS_KEY)
        if source == 'abfs':
            return fsspec.filesystem(f"abfs", account_name=config.AZURE_ACCOUNT_NAME, account_key=config.AZURE_ACCOUNT_KEY)
    except:
        raise Exception(f"Error in creating {source} filesystem")


def download_gwtm_file(filename, source='s3', config=None, decode=True):

    try:
        if source == 's3':
            s3file = fsspec.open(f"s3://{config.AWS_BUCKET}/{filename}")

        if source == 'abfs':
            s3file = fsspec.open(f"abfs://{filename}", "rb", account_name=config.AZURE_ACCOUNT_NAME, account_key=config.AZURE_ACCOUNT_KEY)

        with s3file as _file:
            if decode:
                return _file.read().decode('utf-8')
            else:
                return _file.read()

    except:
        raise Exception(f"Error reading {source} file: {filename}")
            


def upload_gwtm_file(content, filename, source="s3", config=None):
    fs = _get_fs(source=source, config=config)

    if source=="s3" and f"{config.AWS_BUCKET}/" not in filename:
        filename = f"{config.AWS_BUCKET}/{filename}"

    open_file = fs.open(filename, "w") 
    with open_file as of:
        of.write(content)
    of.close()
    return True


def list_gwtm_bucket(container, source="s3", config=None):
    fs = _get_fs(source=source, config=config)
    if source == 's3':
        bucket_content = fs.ls(f"{config.AWS_BUCKET}/{container}")
        ret = []
        for b in bucket_content:
            split_b = b.split(f"{config.AWS_BUCKET}/")[1]
            if split_b != f"{container}/":
                ret.append(split_b)
        return sorted(ret)
    
    ret = fs.ls(container)
    return sorted(ret)


def delete_gwtm_files(keys, source="s3", config=None):
    if source=="s3":
        if isinstance(keys, list):
            for i,k in enumerate(keys):
                if f"{config.AWS_BUCKET}/" not in k:
                    keys[i] = f"{config.AWS_BUCKET}/{k}"
        if isinstance(keys, str) and f"{config.AWS_BUCKET}/" not in keys:
            keys = f"{config.AWS_BUCKET}/{keys}"
    
    fs = _get_fs(source=source, config=config)
    fs.rm(keys)
    return True


def get_fname(fullname):
    split = fullname.split('/')
    fname = split[len(split)-1]
    return fname

class test_config(object):
    pass

if __name__ == '__main__':
    import os
    config = test_config()

    config.AZURE_ACCOUNT_NAME = os.environ.get('AZURE_ACCOUNT_NAME', None)
    config.AZURE_ACCOUNT_KEY = os.environ.get("AZURE_ACCOUNT_KEY", None)
    config.AWS_BUCKET = os.environ.get("AWS_BUCKET", None)
    config.AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID', None)
    config.AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY', None)

    bucket_sources = ["s3", "abfs"]
    for source in bucket_sources:

        content = "line1\line2"
        filename = "test/vv.text"
        test1 = upload_gwtm_file(content, filename, source=source, config=config)
        assert test1, "error upload" 

        test2 = download_gwtm_file(filename, source=source, config=config)
        assert test2==content, "error download"

        test3 = delete_gwtm_files([filename], source=source, config=config)
        assert test3, "error delete"

    s3_content = list_gwtm_bucket("fit", "s3", config)[0:10]
    abfs_content = list_gwtm_bucket("fit", "abfs", config)[0:10]
    assert s3_content==abfs_content