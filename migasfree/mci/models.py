from django.db import models
from django.utils.translation import gettext_lazy as _

from migasfree.core.models import Project, ServerAttribute


class Config(models.Model):
    project = models.OneToOneField(
        Project,
        on_delete=models.CASCADE,
        related_name='mci_config',
        verbose_name=_('Project'),
        db_comment='related project for this MCI configuration',
    )
    template_id = models.CharField(
        max_length=100,
        verbose_name=_('Template ID'),
        db_comment='identifier of the MCI template used (e.g. debian-12-desktop)',
    )
    base_os = models.CharField(
        max_length=255,
        verbose_name=_('Base OS'),
        blank=True,
        db_comment='base operating system name (e.g. debian, ubuntu)',
    )
    dockerfile = models.TextField(
        verbose_name=_('Dockerfile'),
        blank=True,
        db_comment='jinja2 template for the dockerfile used to build the image',
    )
    partition = models.TextField(
        verbose_name=_('Partition'),
        blank=True,
        db_comment='yaml partition schema definition for the image creation',
    )

    class Meta:
        app_label = 'mci'
        verbose_name = _('MCI Config')
        verbose_name_plural = _('MCI Configs')
        db_table_comment = (
            'stores the general MCI configuration template, base operating system and partition schema for a project'
        )

    def __str__(self):
        return f'MCI Config for {self.project.name}'


class Flavour(models.Model):
    config = models.ForeignKey(
        Config,
        on_delete=models.CASCADE,
        related_name='flavours',
        verbose_name=_('MCI Config'),
        db_comment='related MCI configuration',
    )
    name = models.CharField(
        max_length=255,
        verbose_name=_('Name'),
        db_comment='name of the flavour (e.g. Desktop, Server, Minimal)',
    )
    description = models.TextField(
        verbose_name=_('Description'),
        blank=True,
        db_comment='detailed description of the flavour purpose and packages',
    )
    tags = models.ManyToManyField(
        ServerAttribute,
        blank=True,
        verbose_name=_('Tags'),
        related_name='flavours',
    )
    enabled = models.BooleanField(
        default=True,
        verbose_name=_('Enabled'),
        db_comment='indicates if this flavour is active and can be built',
    )
    user = models.CharField(
        max_length=255,
        verbose_name=_('User'),
        db_comment='default user name created in the system',
    )
    password = models.CharField(
        max_length=255,
        verbose_name=_('Password'),
        db_comment='default user password or hash created in the system',
    )
    keymap = models.CharField(
        max_length=50,
        verbose_name=_('Keymap'),
        default='us',
        db_comment='keyboard layout code (e.g. us, es)',
    )
    keyboard_model = models.CharField(
        max_length=50,
        verbose_name=_('Keyboard Model'),
        default='pc105',
        db_comment='keyboard hardware model (e.g. pc105)',
    )
    charmap = models.CharField(
        max_length=50,
        verbose_name=_('Charmap'),
        default='UTF-8',
        db_comment='character set encoding (e.g. UTF-8)',
    )
    codeset = models.CharField(
        max_length=50,
        verbose_name=_('Codeset'),
        default='guess',
        db_comment='console keyboard code set (e.g. guess, Lat15)',
    )
    timezone = models.CharField(
        max_length=100,
        verbose_name=_('Timezone'),
        default='Europe/Madrid',
        db_comment='system timezone name (e.g. Europe/Madrid, UTC)',
    )
    hostname = models.CharField(
        max_length=255,
        verbose_name=_('Hostname'),
        db_comment='hostname assigned to the built system',
    )

    class Meta:
        app_label = 'mci'
        verbose_name = _('MCI Flavour')
        verbose_name_plural = _('MCI Flavours')
        db_table_comment = 'defines specific system environments or variants (flavours) with customized hostnames, credentials, timezones, and packages'

    def __str__(self):
        return f'{self.config.project.name} - {self.name}'


class Release(models.Model):
    config = models.ForeignKey(
        Config,
        on_delete=models.CASCADE,
        related_name='releases',
        verbose_name=_('MCI Config'),
        db_comment='related MCI configuration',
    )
    name = models.CharField(
        max_length=255,
        verbose_name=_('Name'),
        db_comment='name of the release (e.g. v1.0, 2026-05)',
    )
    description = models.TextField(
        verbose_name=_('Description'),
        blank=True,
        db_comment='detailed release notes and changelog',
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Created At'),
        db_comment='timestamp when the release was registered',
    )

    class Meta:
        app_label = 'mci'
        verbose_name = _('MCI Release')
        verbose_name_plural = _('MCI Releases')
        db_table_comment = 'represents a versioned build release of a specific MCI configuration'

    def __str__(self):
        return f'{self.config.project.name} - {self.name}'


class Build(models.Model):
    STATUS_CHOICES = [
        ('queued', _('Queued')),
        ('running', _('Running')),
        ('completed', _('Completed')),
        ('failed', _('Failed')),
    ]

    release = models.ForeignKey(
        Release,
        on_delete=models.CASCADE,
        related_name='builds',
        verbose_name=_('Release'),
        db_comment='related release associated with this build',
    )
    flavour = models.ForeignKey(
        Flavour,
        on_delete=models.CASCADE,
        related_name='builds',
        verbose_name=_('Flavour'),
        db_comment='related flavour built in this task',
    )
    task_id = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_('Task ID'),
        db_comment='Redis/Celery task identifier associated with the build process',
    )
    status = models.CharField(
        max_length=50,
        choices=STATUS_CHOICES,
        default='queued',
        verbose_name=_('Status'),
        db_comment='current status of the build task (queued, running, completed, failed)',
    )
    started_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Started At'),
        db_comment='timestamp when the build process started',
    )
    finished_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Finished At'),
        db_comment='timestamp when the build process ended',
    )
    uri = models.TextField(
        blank=True,
        verbose_name=_('URI'),
        db_comment='download URI of the generated system image files',
    )
    size = models.BigIntegerField(
        null=True,
        blank=True,
        verbose_name=_('Size'),
        db_comment='total size in bytes of the generated system image',
    )
    log = models.TextField(
        blank=True,
        verbose_name=_('Log'),
        db_comment='stdout and stderr compilation logs from the build task',
    )

    class Meta:
        app_label = 'mci'
        verbose_name = _('MCI Build')
        verbose_name_plural = _('MCI Builds')
        db_table_comment = 'tracks individual build tasks of a release and flavour, including status, compilation logs, image size and download URL'

    def __str__(self):
        return f'Build {self.release.name} ({self.flavour.name}) - {self.status}'
