import fsspec
import json
import re

def _get_swift_conn(config):
    try:
        from keystoneauth1.identity import v3
        from keystoneauth1 import session
        from swiftclient import Connection as SwiftConnection
    except ImportError:
        raise Exception(
            "Swift dependencies not installed. Install python-swiftclient, "
            "python-keystoneclient, and keystoneauth1"
        )

    is_app_cred = bool(re.match(r'^[a-f0-9]{32}$', config.OS_USERNAME or ''))

    if is_app_cred:
        auth = v3.ApplicationCredential(
            auth_url=config.OS_AUTH_URL,
            application_credential_id=config.OS_USERNAME,
            application_credential_secret=config.OS_PASSWORD
        )
        sess = session.Session(auth=auth)
        conn = SwiftConnection(
            session=sess,
            os_options={
                'object_storage_url': config.OS_STORAGE_URL
            }
        )
    else:
        conn = SwiftConnection(
            authurl=config.OS_AUTH_URL,
            user=config.OS_USERNAME,
            key=config.OS_PASSWORD,
            os_options={
                'user_domain_name': config.OS_USER_DOMAIN_NAME,
                'project_domain_name': config.OS_PROJECT_DOMAIN_NAME,
                'project_name': config.OS_PROJECT_NAME,
            },
            auth_version='3'
        )

    return conn


def _get_fs(source, config):
    try:
        if source == 's3':
            return fsspec.filesystem("s3", key=config.AWS_ACCESS_KEY_ID, secret=config.AWS_SECRET_ACCESS_KEY)
        if source == 'abfs':
            return fsspec.filesystem("abfs", account_name=config.AZURE_ACCOUNT_NAME, account_key=config.AZURE_ACCOUNT_KEY)
    except:  # noqa: E722
        raise Exception(f"Error in creating {source} filesystem")


def download_gwtm_file(filename, source='s3', config=None, decode=True):
    if source == "swift":
        conn = _get_swift_conn(config)
        headers, content = conn.get_object(config.OS_CONTAINER_NAME, filename)
        if decode:
            return content.decode("utf-8")
        return content

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
    if source == "swift":
        conn = _get_swift_conn(config)
        if isinstance(content, str):
            content = content.encode('utf-8')
        conn.put_object(config.OS_CONTAINER_NAME, filename, content)
        return True

    fs = _get_fs(source=source, config=config)

    if source=="s3" and f"{config.AWS_BUCKET}/" not in filename:
        filename = f"{config.AWS_BUCKET}/{filename}"

    if isinstance(content, bytes):
        open_file = fs.open(filename, "wb")
    else:
        open_file = fs.open(filename, "w")

    with open_file as of:
        of.write(content)
    of.close()
    return True


def list_gwtm_bucket(container, source="s3", config=None):
    if source == "swift":
        conn = _get_swift_conn(config)
        headers, objects = conn.get_container(
            config.OS_CONTAINER_NAME,
            prefix=f"{container}/"
        )
        ret = []
        for obj in objects:
            name = obj.get('name', '')
            if name != f"{container}/":
                ret.append(name)
        return sorted(ret)

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
    if source == "swift":
        conn = _get_swift_conn(config)
        if isinstance(keys, str):
            keys = [keys]
        for k in keys:
            conn.delete_object(config.OS_CONTAINER_NAME, k)
        return True

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
    try:
        return download_gwtm_file(key, source, config)
    except Exception:
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
    abfs_content = list_gwtm_bucket("test", "abfs", config)
    # for a in alerts:
    #     filtered_content = [x for x in abfs_content if a in x and 'alert.json' in x]
    #     for f in filtered_content:
    #         json_file = download_gwtm_file(f, source="abfs", config=config)
    #         test = json.loads(json_file)
    #         print(f, test['event']['duration'], test['event']['central_frequency'])
    #         requests.post(url= base_url + '/fixdata', json = {"alert_name":f, "duration":test['event']['duration'], "central_freq":test['event']['central_frequency']})