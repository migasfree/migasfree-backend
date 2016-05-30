# -*- coding: utf-8 -*-

# Copyright (c) 2015-2016 Jose Antonio Chavarría <jachavar@gmail.com>
# Copyright (c) 2015-2016 Alberto Gacías <alberto@migasfree.org>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

from django.core.exceptions import ValidationError
from django import forms
from django.utils.translation import ugettext_lazy as _

from .widgets import MultiFileInput


class MultiFileField(forms.FileField):
    # http://koensblog.eu/blog/7/multiple-file-upload-django

    widget = MultiFileInput
    default_error_messages = {
        'min_num': _("Ensure at least %(min_num)s files are uploaded (received %(num_files)s)."),
        'max_num': _("Ensure at most %(max_num)s files are uploaded (received %(num_files)s)."),
        'file_size': _("File: %(uploaded_file_name)s, exceeded maximum upload size.")
    }

    def __init__(self, *args, **kwargs):
        self.min_num = kwargs.pop('min_num', 0)
        self.max_num = kwargs.pop('max_num', None)
        self.maximum_file_size = kwargs.pop('maximum_file_size', None)
        super(MultiFileField, self).__init__(*args, **kwargs)

    def to_python(self, data):
        ret = []
        for item in data:
            ret.append(super(MultiFileField, self).to_python(item))
        return ret

    def validate(self, data):
        super(MultiFileField, self).validate(data)

        num_files = len(data)
        if len(data) and not data[0]:
            num_files = 0

        if num_files < self.min_num:
            raise ValidationError(
                self.error_messages['min_num'] % {
                    'min_num': self.min_num,
                    'num_files': num_files
                }
            )
        elif self.max_num and  num_files > self.max_num:
            raise ValidationError(
                self.error_messages['max_num'] % {
                    'max_num': self.max_num,
                    'num_files': num_files
                }
            )

        for uploaded_file in data:
            if uploaded_file.size > self.maximum_file_size:
                raise ValidationError(
                    self.error_messages['file_size'] % {
                        'uploaded_file_name': uploaded_file.name
                    }
                )
