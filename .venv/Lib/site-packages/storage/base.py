import os
import mimetypes
from abc import ABC, abstractmethod

from storage.files import File




class Storage(ABC):

    def save(self, name, content, content_type=None, encoding='utf-8'):
        """
        Save new content to the file specified by name. The content should be
        a proper File object or any Python file-like object, ready to be read
        from the beginning.
        """
        if isinstance(content, str):
            content = content.encode(encoding)
        name = self._save(
            name,
            content,
            content_type=content_type,
            encoding=encoding,
        )
        return name


    def open(self, name, mode='rb'):
        return self._open(name, mode)


    @abstractmethod
    def _save(self, name):
        pass


    @abstractmethod
    def _open(self, name):
        pass


    @abstractmethod
    def delete(self, name):
        pass


    @abstractmethod
    def exists(self, name):
        pass


    @abstractmethod
    def size(self, name):
        pass


    @abstractmethod
    def url(self, name):
        """
        Return an absolute URL where the file's contents can be accessed
        directly by a web browser.
        """
        pass
