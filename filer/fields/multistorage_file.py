from django.core.files.base import File
from django.core.files.storage import Storage
from easy_thumbnails import fields as easy_thumbnails_fields, \
    files as easy_thumbnails_files
from filer import settings as filer_settings
from filer.utils.loader import load
import hashlib
import os

DEFAULT_STORAGES = {
    'public': load(filer_settings.FILER_PUBLICMEDIA_STORAGE, Storage),
    'private': load(filer_settings.FILER_PRIVATEMEDIA_STORAGE, Storage),
}

def generate_filename_multistorage(instance, filename):
    if instance.is_public:
        upload_to = filer_settings.FILER_PUBLICMEDIA_UPLOAD_TO
    else:
        upload_to = filer_settings.FILER_PRIVATEMEDIA_UPLOAD_TO
        
    if callable(upload_to):
        return upload_to(instance, filename)
    else:
        return upload_to

class ThumbnailNameMixin(easy_thumbnails_files.Thumbnailer):
    def get_thumbnail_name(self, thumbnail_options, transparent=False):
        path, source_filename = os.path.split(self.name)
        source_extension = os.path.splitext(source_filename)[1][1:]
        dst = super(ThumbnailNameMixin, self).get_thumbnail_name(thumbnail_options, transparent=transparent)
        dst_path, dst_filename = os.path.split(dst)
        dst_extension = os.path.splitext(dst_filename)[1][1:]
        m = hashlib.md5()
        m.update(dst)
        thumb_options_hash = m.hexdigest()
        return u"_/%s-%s.%s" % (self.name, thumb_options_hash, dst_extension)

class MultiStorageFieldFile(ThumbnailNameMixin, easy_thumbnails_files.ThumbnailerFieldFile):
    def __init__(self, instance, field, name):
        File.__init__(self, None, name)
        self.instance = instance
        self.field = field
        self._committed = True
        self.storages = self.field.storages
    @property
    def storage(self):
        if self.instance.is_public:
            return self.storages['public']
        else:
            return self.storages['private']
            
    @property
    def source_storage(self):
        if self.instance.is_public:
            return self.storages['public']
        else:
            return self.storages['private']
            
    @property
    def thumbnail_storage(self):
        if self.instance.is_public:
            return self.storages['public']
        else:
            return self.storages['private']

class MultiStorageFileField(easy_thumbnails_fields.ThumbnailerField):
    attr_class = MultiStorageFieldFile
    def __init__(self, verbose_name=None, name=None, upload_to_dict=None, storages=None, **kwargs):
        self.storages = storages or DEFAULT_STORAGES
        super(easy_thumbnails_fields.ThumbnailerField, self).__init__(verbose_name=verbose_name, name=name,
                                                                      upload_to=generate_filename_multistorage,
                                                                      storage=None, **kwargs)
