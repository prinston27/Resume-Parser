import os

from storage.files import File

from storage.base import Storage




class FileSystemStorage(Storage):

    def __init__(self, base_path=None, file_permissions=None):
        if not base_path:
            base_path = 'media/'
        if not file_permissions:
            file_permissions = 0o644
        self.base_path = base_path
        self.file_permissions = file_permissions


    def _get_full_path(self, name):
        return os.path.join(self.base_path, name)


    def _save(self, name, content, content_type=None, encoding='utf-8'):
        full_path = self._get_full_path(name)
        with open(full_path, 'wb') as f:
            f.write(content)
        os.chmod(full_path, self.file_permissions)


    def _open(self, name, mode='rb'):
        full_path = self._get_full_path(name)
        return File(open(full_path, mode))


    def delete(self, name):
        full_path = self._get_full_path(name)

        if not name:
            raise ValueError('The name must be given to delete().')
        try:
            if os.path.exists(full_path):
                os.remove(full_path)
        except FileNotFoundError:
            # FileNotFoundError is raised if the file
            # or directory was removed concurrently.
            pass


    def listdir(self, path):
        path = self.path(path)
        directories, files = [], []
        with os.scandir(path) as entries:
            for entry in entries:
                if entry.is_dir():
                    directories.append(entry.name)
                else:
                    files.append(entry.name)
        return directories, files


    def exists(self, name):
        return os.path.exists(self._get_full_path(name))


    def size(self, name):
        return os.path.getsize(self._get_full_path(name))


    def url(self, name):
        return f'/media/{name}'
