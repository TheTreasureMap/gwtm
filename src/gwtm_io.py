import fsspec
import json
import requests

def _get_fs(source, config):
    try:
        if source == 's3':
            return fsspec.filesystem(f"s3", key=config.AWS_ACCESS_KEY_ID, secret=config.AWS_SECRET_ACCESS_KEY)
        if source == 'abfs':
            return fsspec.filesystem(f"abfs", account_name=config.AZURE_ACCOUNT_NAME, account_key=config.AZURE_ACCOUNT_KEY)
    except:
        raise Exception(f"Error in creating {source} filesystem")


def download_gwtm_file(filename, source='s3', config=None, decode=True):
    fs = _get_fs(source=source, config=config)

    if source=="s3" and f"{config.AWS_BUCKET}/" not in filename:
        filename = f"{config.AWS_BUCKET}/{filename}"

    s3file = fs.open(filename, 'rb')

    with s3file as _file:
        if decode:
            return _file.read().decode('utf-8')
        else:
            return _file.read()


#def download_gwtm_file(filename, source='s3', config=None, decode=True):
#
#    try:
#        if source == 's3':
#            s3file = fsspec.open(f"s3://{config.AWS_BUCKET}/{filename}", key=config.AWS_ACCESS_KEY_ID, secret=config.AWS_SECRET_ACCESS_KEY)
#
#        if source == 'abfs':
#            s3file = fsspec.open(f"abfs://{filename}", "rb", account_name=config.AZURE_ACCOUNT_NAME, account_key=config.AZURE_ACCOUNT_KEY)
#
#        with s3file as _file:
#            if decode:
#                return _file.read().decode('utf-8')
#            else:
#                return _file.read()
#
#    except:
#        raise Exception(f"Error reading {source} file: {filename}")


def upload_gwtm_file(content, filename, source="s3", config=None):
    fs = _get_fs(source=source, config=config)

    if source=="s3" and f"{config.AWS_BUCKET}/" not in filename:
        filename = f"{config.AWS_BUCKET}/{filename}"

    if type(content) == bytes:
        open_file = fs.open(filename, "wb")
    else:
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
    for k in keys:
        fs.rm(k)
    return True

def get_cached_file(key, config):
    source = config.STORAGE_BUCKET_SOURCE
    cached_files = list_gwtm_bucket('cache', source, config)

    if key in cached_files:
        print(f"found cached file {key}")
        return download_gwtm_file(key, source, config)
    else:
        return None

def set_cached_file(key, contents, config):
    source = config.STORAGE_BUCKET_SOURCE

    upload_gwtm_file(json.dumps(contents), key, source, config)


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
    # for source in bucket_sources:

    #     content = "line1\line2"
    #     filename = "test/vv.text"
    #     print("uploading test file", source)
    #     test1 = upload_gwtm_file(content, filename, source=source, config=config)
    #     assert test1, "error upload"

    #     print("downloading test file", source)
    #     test2 = download_gwtm_file(filename, source=source, config=config)
    #     assert test2==content, "error download"

    #     print("deleting test tile", source)
    #     test3 = delete_gwtm_files([filename], source=source, config=config)
    #     assert test3, "error delete"

    # s3_content = list_gwtm_bucket("fit", "s3", config)[0:10]
    # abfs_content = list_gwtm_bucket("fit", "abfs", config)[0:10]
    # assert s3_content==abfs_content
    alerts = ['S230621ad', 'S230620z']
    base_url = 'https://treasuremap.space'
    abfs_content = list_gwtm_bucket("fit", "abfs", config)
    for a in alerts:
        filtered_content = [x for x in abfs_content if a in x and 'alert.json' in x]
        for f in filtered_content:
            json_file = download_gwtm_file(f, source="abfs", config=config)
            test = json.loads(json_file)
            print(f, test['event']['duration'], test['event']['central_frequency'])
            requests.post(url= base_url + '/fixdata', json = {"alert_name":f, "duration":test['event']['duration'], "central_freq":test['event']['central_frequency']})