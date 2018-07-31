# -*- coding: utf-8 -*-

# Copyright (c) 2015-2018 Jose Antonio Chavarría <jachavar@gmail.com>
# Copyright (c) 2015-2018 Alberto Gacías <alberto@migasfree.org>
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

import datetime

from django import forms
from django.conf import settings
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
from django.urls import reverse
from django.utils.text import slugify
from django.utils.translation import ugettext_lazy as _

from migasfree.client.models import Computer

from .models import (
    Package, Deployment, ClientProperty, Attribute,
    UserProfile, Scope, Domain, Project, Store,
)
from .validators import MimetypeValidator
from .pms import get_available_mimetypes

# TODO https://github.com/blueimp/jQuery-File-Upload/wiki
# TODO https://github.com/sigurdga/django-jquery-file-upload
# TODO https://github.com/digi604/django-smart-selects (project -> store)


class PackageForm(forms.ModelForm):
    package_file = forms.FileField(
        required=False,
        validators=[MimetypeValidator(get_available_mimetypes())],
        max_length=settings.MAX_FILE_SIZE,
        allow_empty_file=True,
    )

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop("request", None)
        super(PackageForm, self).__init__(*args, **kwargs)

        self.fields['fullname'].required = False
        self.fields['name'].required = False
        self.fields['version'].required = False
        self.fields['architecture'].required = False
        self.fields['store'].required = False

        user = self.request.user.userprofile

        try:
            if Project.objects.scope(user).count() == 1:
                self.fields['project'].initial = Project.objects.scope(user).first().id

            self.fields['project'].empty_label = None
            self.fields['project'].queryset = Project.objects.scope(user)
        except AttributeError:
            pass

    def clean(self):
        if self['package_file'].value() is not None and not self['store'].value():
            raise ValidationError(_('Store is required with package file'))

        cleaned_data = super(PackageForm, self).clean()
        if self['fullname'].value() == '':
            cleaned_data['fullname'] = self['package_file'].value().name
        else:
            cleaned_data['fullname'] = slugify(cleaned_data['fullname'])

        if not cleaned_data['fullname']:
            raise ValidationError(_('Fullname is required'))

        cleaned_data['name'], cleaned_data['version'], cleaned_data['architecture'] = Package.normalized_name(
            cleaned_data['fullname']
        )

        if not cleaned_data['version']:
            raise ValidationError(_('Version is required'))

        if not cleaned_data['architecture']:
            raise ValidationError(_('Architecture is required'))

        self.data = cleaned_data
        return cleaned_data

    def save(self, commit=True):
        instance = super(PackageForm, self).save(commit=False)
        if instance.fullname is None:
            instance.fullname = self['package_file'].value().name
        if commit:
            instance.save()

        return instance

    class Meta:
        model = Package
        fields = '__all__'


class StoreForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop("request", None)
        super(StoreForm, self).__init__(*args, **kwargs)

        user = self.request.user.userprofile

        try:
            if Project.objects.scope(user).count() == 1:
                self.fields['project'].initial = Project.objects.scope(user).first().id

            self.fields['project'].empty_label = None
            self.fields['project'].queryset = Project.objects.scope(user)
        except AttributeError:
            pass

    class Meta:
        model = Store
        fields = '__all__'


class DeploymentForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop("request", None)
        super(DeploymentForm, self).__init__(*args, **kwargs)
        user = self.request.user.userprofile
        self.fields['start_date'].initial = datetime.date.today()

        try:
            if Project.objects.scope(user).count() == 1:
                self.fields['project'].initial = Project.objects.scope(user).first().id

            self.fields['project'].queryset = Project.objects.scope(user)
        except AttributeError:
            pass

        if not self.instance.id and user.domain_preference:
            self.fields['domain'].initial = user.domain_preference
            self.fields['domain'].widget.attrs['readonly'] = True

        domains = user.domains.all()
        if domains.count() == 0:
            self.fields['domain'].queryset = Domain.objects.all()
        else:
            self.fields['domain'].queryset = domains

    def _validate_active_computers(self, att_list):
        for att_id in att_list:
            attribute = Attribute.objects.get(pk=att_id)
            if attribute.property_att.prefix == 'CID':
                computer = Computer.objects.get(pk=int(attribute.value))
                if computer.status not in Computer.ACTIVE_STATUS:
                    raise ValidationError(
                        _('It is not possible to assign an inactive computer (%s) as an attribute')
                        % computer
                    )

    def clean(self):
        # http://stackoverflow.com/questions/7986510/django-manytomany-model-validation
        cleaned_data = super(DeploymentForm, self).clean()

        if 'project' not in cleaned_data:
            raise ValidationError(_('Project is required'))

        for item in cleaned_data.get('available_packages', []):
            if item.project.id != cleaned_data['project'].id:
                raise ValidationError(
                    _('Package %s must belong to the project %s') % (
                        item, cleaned_data['project']
                    )
                )

        self._validate_active_computers(cleaned_data.get('included_attributes', []))
        self._validate_active_computers(cleaned_data.get('excluded_attributes', []))

        if not cleaned_data['domain']:
            admin_domain_group = Group.objects.filter(name=_('Admin Domain'))
            if admin_domain_group:
                admin_domain_group = admin_domain_group[0]
                if admin_domain_group.id in list(
                    self.request.user.userprofile.groups.values_list('id', flat=True)
                ):
                    raise ValidationError(_('Domain can not be empty'))

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


class ScopeForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop("request", None)
        super(ScopeForm, self).__init__(*args, **kwargs)

        try:
            self.fields['user'].initial = self.request.user.userprofile
            self.fields['domain'].initial = self.request.user.userprofile.domain_preference
        except AttributeError:
            pass

    class Meta:
        model = Scope
        fields = ('name', 'user')


class DomainForm(forms.ModelForm):
    class Meta:
        model = Domain
        fields = ('name',)


class UserProfileForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(UserProfileForm, self).__init__(*args, **kwargs)
        self.fields['groups'].help_text = ''
        if self.instance.id:
            self.fields['username'].help_text += u'<p><a href="{}">{}</a></p>'.format(
                reverse('admin:auth_user_password_change', args=(self.instance.id,)),
                _('Change Password')
            )

    def clean(self):
        cleaned_data = super(UserProfileForm, self).clean()

        if not cleaned_data['is_superuser'] and len(cleaned_data['domains']) == 0:
            admin_domain_group = Group.objects.filter(name=_('Admin Domain'))
            if admin_domain_group:
                admin_domain_group = admin_domain_group[0]
                if admin_domain_group.id in list(cleaned_data['groups'].values_list('id', flat=True)):
                    raise ValidationError(_('This user must be one domain at least'))

        if cleaned_data['domain_preference'] \
                and cleaned_data['domain_preference'] not in list(cleaned_data['domains']):
            raise ValidationError(_('Domain preference not in selected Domains'))

        return cleaned_data

    class Meta:
        model = UserProfile
        fields = (
            'username', 'first_name', 'last_name',
            'email', 'date_joined', 'last_login',
            'is_active', 'is_superuser', 'is_staff',
            'groups', 'user_permissions', 'domains',
        )
