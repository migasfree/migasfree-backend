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

from migasfree.client.models import Computer

from .models import Package, Deployment, ClientProperty, Attribute
from .validators import MimetypeValidator
from .pms import get_available_mimetypes
from .fields import MultiFileField

# TODO https://github.com/Chive/django-multiupload
# TODO https://github.com/blueimp/jQuery-File-Upload/wiki
# TODO https://github.com/sigurdga/django-jquery-file-upload
# TODO https://github.com/digi604/django-smart-selects (project -> store)


class PackageForm(forms.ModelForm):
    package_file = MultiFileField(
        maximum_file_size=1024*1024*50,  # FIXME to settings.py
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
        fields = '__all__'


class DeploymentForm(forms.ModelForm):
    def _validate_active_computers(self, att_list):
        for att_id in att_list:
            attribute = Attribute.objects.get(pk=att_id)
            if attribute.property_att.prefix == 'CID':
                computer = Computer.objects.get(pk=int(attribute.value))
                if computer.status not in Computer.ACTIVE_STATUS:
                    raise ValidationError(
                        _('It is not possible to assign an inactive computer (%s) as an attribute')
                        % computer.__str__()
                    )

    def clean(self):
        # http://stackoverflow.com/questions/7986510/django-manytomany-model-validation
        cleaned_data = super(DeploymentForm, self).clean()

        for item in cleaned_data.get('available_packages', []):
            if item.project.id != cleaned_data['project'].id:
                raise ValidationError(
                    _('Package %s must belong to the project %s') % (
                        item, cleaned_data['project']
                    )
                )

        self._validate_active_computers(cleaned_data.get('included_attributes', []))
        self._validate_active_computers(cleaned_data.get('excluded_attributes', []))

    class Meta:
        model = Deployment
        fields = '__all__'


class ClientPropertyForm(forms.ModelForm):
    class Meta:
        model = ClientProperty
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super(ClientPropertyForm, self).__init__(*args, **kwargs)
        self.fields['code'].required = True
