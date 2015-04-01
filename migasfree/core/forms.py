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

from django import forms
from django.utils.translation import ugettext_lazy as _
from django.core.exceptions import ValidationError
from django.utils.text import slugify

from .models import Package, Release, ClientProperty
from .validators import MimetypeValidator
from .pms import get_available_mimetypes
from .fields import MultiFileField

#TODO https://github.com/Chive/django-multiupload
#TODO https://github.com/blueimp/jQuery-File-Upload/wiki
#TODO https://github.com/sigurdga/django-jquery-file-upload
#TODO https://github.com/digi604/django-smart-selects (project -> store)


class PackageForm(forms.ModelForm):
    package_file = MultiFileField(
        maximum_file_size = 1024*1024*50,  # FIXME to settings.py
        required=False,
        validators=[MimetypeValidator(get_available_mimetypes())]
    )

    def __init__(self, *args, **kwargs):
        super(PackageForm, self).__init__(*args, **kwargs)
        self.fields['name'].required = False

    def clean(self):
        cleaned_data = super(PackageForm, self).clean()
        if self['name'].value() == '':
            if len(self['package_file'].value()) == 1:
                cleaned_data['name'] = self['package_file'].value()[0]
            else:
                raise ValidationError(
                    _('When more than one file is uploaded, name is required')
                )
        else:
            cleaned_data['name'] = slugify(cleaned_data['name'])

    def save(self, commit=True):
        instance = super(PackageForm, self).save(commit=False)
        if instance.name is None:
            instance.name = str(self['package_file'].value())
        if commit:
            instance.save()

        return instance

    class Meta:
        model = Package


class ReleaseForm(forms.ModelForm):
    class Meta:
        model = Release

    def clean(self):
        # http://stackoverflow.com/questions/7986510/django-manytomany-model-validation
        cleaned_data = super(ReleaseForm, self).clean()

        for item in cleaned_data.get('available_packages', []):
            if item.project.id != cleaned_data['project'].id:
                raise ValidationError(
                    _('Package %s must belong to the project %s') % (
                        item, cleaned_data['project']
                    )
                )


class ClientPropertyForm(forms.ModelForm):
    class Meta:
        model = ClientProperty

    def __init__(self, *args, **kwargs):
        super(ClientPropertyForm, self).__init__(*args, **kwargs)
        self.fields['code'].required = True
