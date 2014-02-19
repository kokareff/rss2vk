'''
@author: Kirill Python
@contact: http://vk.com/python273
@license Apache License, Version 2.0, see LICENSE file

Copyright (C) 2013
'''

# -*- coding: utf-8 -*-


class VkUpload():
    def __init__(self, vk):
        self.vk = vk
        # https://vk.com/dev/upload_files

    def photo(self, photos, album_id=None, group_id=None):


        if not (album_id and photos):
            return False

        if type(photos) == str:  # upload.photo('photo.jpg', ...)
            photos = [photos]

        values = {
            'album_id': album_id
        }
        if group_id:
            values.update({'group_id': group_id})

        url = self.vk.method('photos.getUploadServer', values)['upload_url']

        photos_files = openPhotos(photos)
        response = self.vk.http.post(url, files=photos_files).json()
        closePhotos(photos_files)


        if not 'album_id' in response:
            response['album_id'] = response['aid']

        response = self.vk.method('photos.save', response)

        return response

    def photoMessages(self, photos, group_id=None):

        if not photos:
            return False

        if type(photos) == str:  # upload.photo('photo.jpg', ...)
            photos = [photos]

        values = {}
        if group_id:
            values.update({'group_id': group_id})

        url = self.vk.method('photos.getMessagesUploadServer', values)['upload_url']

        photos_files = openPhotos(photos)
        response = self.vk.http.post(url, files=photos_files)
        closePhotos(photos_files)

        response = self.vk.method('photos.saveMessagesPhoto', response.json())

        return response


def openPhotos(photos_paths):
    photos = {}

    for x, filename in enumerate(photos_paths):
        photos.update(
            {'file%s' % x: open(filename, 'rb')}
        )

    return photos

def closePhotos(photos):
    for i in photos:
        photos[i].close()
