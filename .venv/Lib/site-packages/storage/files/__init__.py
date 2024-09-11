"""
The entire ``storage.files`` subpackage is almost a complete replica of
Django's ``django.core.files`` subpackage -- apart from
``django.core.files.storage``. Currently from Django 4.2. This is so that we
don't create the additional dependency to Django.
"""

from storage.files.base import File, ContentFile

__all__ = ['File', 'ContentFile']
