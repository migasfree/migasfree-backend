from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _

from ..core.models import MigasLink, Project, ServerAttribute


class Config(models.Model, MigasLink):
    BUILD_TYPE_CHOICES = [
        ('docker', _('Docker (Linux)')),
        ('qemu_win', _('QEMU Unattended (Windows)')),
        ('qemu_lnx', _('QEMU Preseed/Kickstart (Linux)')),
    ]

    IMAGE_FORMAT_CHOICES = [
        ('raw', _('RAW (.raw)')),
        ('wim', _('WIM (.wim)')),
        ('squashfs', _('SquashFS (.squashfs)')),
    ]

    project = models.OneToOneField(
        Project,
        on_delete=models.CASCADE,
        related_name='mgi_config',
        verbose_name=_('Project'),
        db_comment='related project for this MGI configuration',
    )
    template_id = models.CharField(
        max_length=100,
        verbose_name=_('Template ID'),
        db_comment='identifier of the MGI template used (e.g. debian-12-desktop)',
    )
    build_type = models.CharField(
        max_length=20,
        choices=BUILD_TYPE_CHOICES,
        default='docker',
        verbose_name=_('Build Type'),
        db_comment='engine used to build the Golden Image',
    )
    base_os = models.CharField(
        max_length=255,
        verbose_name=_('Base OS'),
        blank=True,
        db_comment='base operating system name (e.g. debian, ubuntu)',
    )
    partition = models.TextField(
        verbose_name=_('Partition'),
        blank=True,
        db_comment='yaml partition schema definition for the image creation',
    )
    provision_script = models.TextField(
        blank=True,
        verbose_name=_('Provision Script'),
        db_comment='jinja2 provisioning script (Bash for Linux / PowerShell for Windows)',
    )
    image_format = models.CharField(
        max_length=10,
        choices=IMAGE_FORMAT_CHOICES,
        default='raw',
        verbose_name=_('Image Format'),
        db_comment='output compression or image format (raw, wim, squashfs)',
    )
    config = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_('Extended Configuration'),
        db_comment='polymorphic storage for build-engine specific parameters',
    )

    class Meta:
        app_label = 'mgi'
        verbose_name = _('Config')
        verbose_name_plural = _('Configs')
        db_table_comment = (
            'stores the general MGI configuration template, base operating system and partition schema for a project'
        )

    @property
    def dockerfile(self):
        if isinstance(self.config, dict):
            return self.config.get('dockerfile', '')
        return ''

    @dockerfile.setter
    def dockerfile(self, value):
        if not isinstance(self.config, dict):
            self.config = {}
        self.config['dockerfile'] = value

    def clean(self):
        super().clean()
        if not isinstance(self.config, dict):
            raise ValidationError({'config': _('Extended Configuration must be a dictionary.')})

        if self.build_type == 'docker':
            df = self.config.get('dockerfile', '').strip()
            if not df:
                raise ValidationError(
                    {'config': _('Extended Configuration must contain a "dockerfile" key for Docker build type.')}
                )
        elif self.build_type == 'qemu_win':
            required_keys = ['autounattend_template', 'setupcomplete_template']
            missing = [k for k in required_keys if k not in self.config]
            if missing:
                raise ValidationError({'config': _(f'Missing required keys for Windows build: {", ".join(missing)}')})

            disk_size = self.config.get('disk_size_gb', 40)
            if not isinstance(disk_size, (int, float)) or disk_size < 20:
                raise ValidationError({'config': _('disk_size_gb must be a number and at least 20 GB.')})

    def __str__(self):
        return f'MGI Config for {self.project.name}'


class Flavour(models.Model, MigasLink):
    config = models.ForeignKey(
        Config,
        on_delete=models.CASCADE,
        related_name='flavours',
        verbose_name=_('MGI Config'),
        db_comment='related MGI configuration',
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
        app_label = 'mgi'
        verbose_name = _('Flavour')
        verbose_name_plural = _('Flavours')
        db_table_comment = 'defines specific system environments or variants (flavours) with customized hostnames, credentials, timezones, and packages'

    def __str__(self):
        return f'{self.config.project.name} - {self.name}'


class Release(models.Model, MigasLink):
    config = models.ForeignKey(
        Config,
        on_delete=models.CASCADE,
        related_name='releases',
        verbose_name=_('MGI Config'),
        db_comment='related MGI configuration',
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
        app_label = 'mgi'
        verbose_name = _('Release')
        verbose_name_plural = _('Releases')
        db_table_comment = 'represents a versioned build release of a specific MGI configuration'

    def __str__(self):
        return f'{self.config.project.name} - {self.name}'


class Build(models.Model, MigasLink):
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
        app_label = 'mgi'
        verbose_name = _('Build')
        verbose_name_plural = _('Builds')
        db_table_comment = 'tracks individual build tasks of a release and flavour, including status, compilation logs, image size and download URL'

    def __str__(self):
        return f'Build {self.release.name} ({self.flavour.name}) - {self.status}'
