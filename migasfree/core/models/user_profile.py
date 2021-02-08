# -*- coding: utf-8 -*-

# Copyright (c) 2018-2021 Jose Antonio Chavarría <jachavar@gmail.com>
# Copyright (c) 2018-2021 Alberto Gacías <alberto@migasfree.org>
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

from django.db import models, connection
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import (
    User as UserSystem,
    UserManager,
    Group,
)
from rest_framework.authtoken.models import Token

from .migas_link import MigasLink


class UserProfile(UserSystem, MigasLink):
    domains = models.ManyToManyField(
        'Domain',
        blank=True,
        verbose_name=_('domains'),
        related_name='domains'
    )

    domain_preference = models.ForeignKey(
        'Domain',
        blank=True,
        verbose_name=_('domain'),
        null=True,
        on_delete=models.SET_NULL
    )

    scope_preference = models.ForeignKey(
        'Scope',
        blank=True,
        verbose_name=_('scope'),
        null=True,
        on_delete=models.SET_NULL
    )

    objects = UserManager()

    def is_view_all(self):
        if str(self) == 'AnonymousUser':
            # TODO: only view current computer
            return True

        return not self.domain_preference and not self.scope_preference

    def get_computers(self):
        cursor = connection.cursor()
        ctx = {
            'domain': self.domain_preference_id,
            'scope': self.scope_preference_id,
            'status': "('intended', 'reserved', 'unknown')"
        }

        if self.domain_preference:
            sql_domain = """
(
    SELECT DISTINCT computer_id
    FROM client_computer_sync_attributes
    INNER JOIN client_computer ON client_computer.id=client_computer_sync_attributes.computer_id
    WHERE attribute_id IN (
        SELECT attribute_id
        FROM core_domain_included_attributes
        WHERE domain_id=%(domain)s
    ) AND client_computer.status in %(status)s
    EXCEPT
    SELECT DISTINCT computer_id
    FROM client_computer_sync_attributes
    WHERE attribute_id IN (
        SELECT attribute_id
        FROM core_domain_excluded_attributes
        WHERE domain_id=%(domain)s
    )
)
""" % ctx
        else:
            sql_domain = ""

        if self.scope_preference:
            sql_scope = """
(
    SELECT DISTINCT computer_id
    FROM client_computer_sync_attributes
    INNER JOIN client_computer ON client_computer.id=client_computer_sync_attributes.computer_id
    WHERE attribute_id IN (
        SELECT attribute_id
        FROM core_scope_included_attributes
        WHERE scope_id=%(scope)s
    ) AND client_computer.status in %(status)s
    EXCEPT
    SELECT DISTINCT computer_id
    FROM client_computer_sync_attributes
    WHERE attribute_id IN (
        SELECT attribute_id
        FROM core_scope_excluded_attributes
        WHERE scope_id=%(scope)s
    )
)
""" % ctx
        else:
            sql_scope = ""

        if not sql_domain and not sql_scope:
            return []

        sql = """
SELECT ARRAY(
%(sql_domain)s
%(operator)s
%(sql_scope)s
)
""" % {
            'sql_domain': sql_domain,
            'sql_scope': sql_scope,
            'operator': ' INTERSECT' if (self.domain_preference and self.scope_preference) else ''
        }

        cursor.execute(sql)
        computers = cursor.fetchall()[0][0]
        cursor.close()

        return computers

    def get_attributes(self):
        attributes = []
        computers = self.get_computers()
        if computers:
            cursor = connection.cursor()
            cursor.execute("""
                SELECT ARRAY(
                    SELECT DISTINCT attribute_id
                    FROM client_computer_sync_attributes
                    WHERE computer_id IN %s
                ) AS attributes""" % ("(" + ",".join(str(e) for e in computers) + ")"))
            attributes = cursor.fetchall()[0][0]
            cursor.close()

        return attributes

    def get_domain_tags(self):
        tags = []
        if self.domain_preference:

            cursor = connection.cursor()
            cursor.execute(
                """SELECT ARRAY(
                    SELECT serverattribute_id
                    FROM core_domain_tags
                    WHERE domain_id=%s
                ) AS attributes """ % self.domain_preference.id
            )
            tags = cursor.fetchall()[0][0]
            cursor.close()

        return tags

    def get_projects(self):
        projects = []
        cursor = connection.cursor()
        computers = self.get_computers()
        if computers:
            cursor.execute(
                """SELECT ARRAY(
                    SELECT DISTINCT project_id
                    FROM client_computer
                    WHERE id IN %s
                ) AS projects""" % ("(" + ",".join(str(e) for e in computers) + ")")
            )
            projects = cursor.fetchall()[0][0]
            cursor.close()

        return projects

    def check_scope(self, computer_id):
        computers = self.get_computers()
        if computers and int(computer_id) not in computers:
            raise PermissionDenied

    def update_scope(self, value):
        self.scope_preference = value if value > 0 else None
        self.save()

    def update_domain(self, value):
        self.domain_preference = value if value > 0 else None
        self.save()

    def is_domain_admin(self):
        if not self.is_superuser:
            domain_admin = Group.objects.get(name='Domain Admin')
            if domain_admin in self.groups.all():
                return True

        return False

    def update_password(self, new_password):
        # set_password also hashes the password that the user will get
        self.set_password(new_password)
        self.save()

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        if not (
            self.password.startswith('sha1$')
            or self.password.startswith('pbkdf2')
        ):
            super().set_password(self.password)

        super().save(force_insert, force_update, using, update_fields)

    class Meta:
        app_label = 'core'
        verbose_name = _('User Profile')
        verbose_name_plural = _('User Profiles')


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_auth_token(sender, instance=None, created=False, **kwargs):
    if created:
        Token.objects.create(user=instance)
