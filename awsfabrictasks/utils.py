from fabric.api import put, sudo
from os import walk, remove
from os.path import relpath, join
from tempfile import NamedTemporaryFile


def sudo_chown(remote_path, owner):
    """
    Run ``sudo chown <owner> remote_path``.
    """
    sudo('chown {owner} {remote_path}'.format(**vars()))

def sudo_chmod(remote_path, mode):
    """
    Run ``sudo chmod <mode> remote_path``.
    """
    sudo('chmod {mode} {remote_path}'.format(**vars()))

def sudo_chattr(remote_path, owner=None, mode=None):
    """
    Run :func:`sudo_chown` and :func:`sudo_chmod` on ``remote_path``.
    If owner or mode is None, their corresponding function is not called.
    """
    if owner:
        sudo_chown(remote_path, owner)
    if mode:
        sudo_chmod(remote_path, mode)

def sudo_upload_file(local_path, remote_path, **chattr_kw):
    """
    Use sudo to upload a file from ``local_path`` to ``remote_path`` and run
    :func:`sudo_chattr` with the given ``chattr_kw`` as arguments.
    """
    put(local_path, remote_path, use_sudo=True)
    sudo_chattr(remote_path, **chattr_kw)

def sudo_upload_string_to_file(string_to_upload, remote_path, **chattr_kw):
    """
    Create a tempfile containing ``string_to_upload``, and use
    :func:`sudo_upload_file` to upload the tempfile. Removes the tempfile
    when the upload is complete or if it fails.

    :param string_to_upload: The string to write to the tempfile.
    :param remote_path: See :func:`sudo_upload_file`.
    :param chattr_kw: See :func:`sudo_upload_file`.
    """
    tmpfile = NamedTemporaryFile(delete=False)
    try:
        tmpfile.write(string_to_upload)
        tmpfile.close()
        sudo_upload_file(tmpfile.name, remote_path, **chattr_kw)
    finally:
        remove(tmpfile.name)


def sudo_mkdir_p(remote_path, **chattr_kw):
    """
    ``sudo mkdir -p <remote_path>`` followed by :func:`sudo_chattr`(remote_path, **chattr_kw).
    """
    sudo('mkdir -p {remote_path}'.format(**vars()))
    sudo_chattr(remote_path, **chattr_kw)


def sudo_upload_dir(local_dir, remote_dir, **chattr_kw):
    """
    Upload all files and directories in ``local_dir`` to ``remote_dir``.
    Directories are created with :func:`sudo_mkdir_p` and files are uploaded
    with :func:`sudo_upload_file`. ``chattr_kw`` is forwarded in both cases.
    """
    for local_dirpath, dirnames, filenames in walk(local_dir):
        remote_dirpath = remote_dir
        rel = relpath(local_dirpath, local_dir)
        if rel != '.':
            remote_dirpath = join(remote_dir, rel)
        #print local_dirpath, '-->', remote_dirpath
        sudo_mkdir_p(remote_dirpath, **chattr_kw)
        for filename in filenames:
            local_filepath = join(local_dirpath, filename)
            remote_filepath = join(remote_dirpath, filename)
            #print local_filepath, '-->', remote_filepath
            sudo_upload_file(local_filepath, remote_filepath, **chattr_kw)


def parse_bool(data):
    """
    Return ``True`` if data is one of:: ``'true', 'True', True``. Otherwise,
    return ``False``.
    """
    return data in ('true', 'True', True)

def force_slashend(path):
    """
    Return ``path`` suffixed with ``/`` (path is unchanged if it is already
    suffixed with ``/``).
    """
    if not path.endswith('/'):
        path = path + '/'
    return path

def force_noslashend(path):
    """
    Return ``path`` with any trailing ``/`` removed.
    """
    if path.endswith('/'):
        path = path.rstrip('/')
    return path

def rsyncformat_path(source_path, sync_content=False):
    """
    rsync uses ``/`` in the source directory to determine if we should
    sync a directory or the contents of a directory. How rsync works:

    Sync contents:
        Source path ending with ``/`` means sync the contents (just as if we
        used ``/*`` except that ``*`` does not include hidden files).
    Sync the directory:
        Source path NOT ending with ``/`` means sync the directory. I.e.: If
        the source is ``/etc/init.d``,  and the destination is ``/tmp``, the contents
        of ``/etc/init.d`` is copied into ``/tmp/init.d/``.

    This is error-prone, and the consequences can be severe if combined with
    ``--delete``. Therefore, we use a boolean to distinguish between these two
    methods of specifying source directory, and reformat the path using
    :func:`force_slashend` and :func:`force_noslashend`.
    """
    if sync_content:
        return force_slashend(source_path)
    else:
        return force_noslashend(source_path)
