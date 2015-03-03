# -*- coding: utf-8 -*-

# Copyright (c) 2015 Jose Antonio Chavarría <jachavar@gmail.com>
# Copyright (c) 2015 Alberto Gacías <alberto@migasfree.org>
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

import magic

from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _
from rest_framework import serializers

from .pms import get_available_pms


class MimetypeValidator(object):
    def __init__(self, mimetypes):
        self.mimetypes = mimetypes

    def __call__(self, value):
        if type(value) is not list:
            value = [value]
        try:
            for item in value:
                mime = magic.from_buffer(item.read(1024), mime=True)
                if not mime in self.mimetypes:
                    raise ValidationError(
                        _('%s is not an acceptable file type') % item
                    )
        except AttributeError as e:
            raise ValidationError(
                _('This value could not be validated for file type') % item
            )


def validate_package_name(name, file_list):
    if name == '' and len(file_list) > 1:
        raise serializers.ValidationError(
            _('When more than one file is uploaded, name is required')
        )


def validate_project_pms(pms):
    available_pms = dict(get_available_pms()).keys()
    if pms not in available_pms:
        raise ValidationError(
            _('PMS must be one of %s' % str(available_pms))
        )
