import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('core', '0005_alter_comments'),
        ('client', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelTableComment(
            name='computer',
            table_comment='computers that have registered in the migasfree system',
        ),
        migrations.AlterModelTableComment(
            name='error',
            table_comment='errors that occur on computers when synchronizing',
        ),
        migrations.AlterModelTableComment(
            name='fault',
            table_comment='faults detected in computers',
        ),
        migrations.AlterModelTableComment(
            name='faultdefinition',
            table_comment='code implementation for detecting faults or adverse events on computers',
        ),
        migrations.AlterModelTableComment(
            name='migration',
            table_comment='switching computer projects',
        ),
        migrations.AlterModelTableComment(
            name='notification',
            table_comment='relevant facts in the migasfree system',
        ),
        migrations.AlterModelTableComment(
            name='packagehistory',
            table_comment='history of changes to the computer packages',
        ),
        migrations.AlterModelTableComment(
            name='statuslog',
            table_comment='computer status changes',
        ),
        migrations.AlterModelTableComment(
            name='synchronization',
            table_comment='synchronization processes that have occurred on computers',
        ),
        migrations.AlterModelTableComment(
            name='user',
            table_comment='users logged into the graphical session at the time of computer synchronization',
        ),
        migrations.AlterField(
            model_name='computer',
            name='comment',
            field=models.TextField(
                blank=True, db_comment='additional computer comment or description', null=True, verbose_name='comment'
            ),
        ),
        migrations.AlterField(
            model_name='computer',
            name='cpu',
            field=models.CharField(
                blank=True, db_comment='processor description', max_length=50, null=True, verbose_name='CPU'
            ),
        ),
        migrations.AlterField(
            model_name='computer',
            name='created_at',
            field=models.DateTimeField(
                auto_now_add=True,
                db_comment='date of entry of the computer into the migasfree system',
                help_text='Date of entry into the migasfree system',
                verbose_name='entry date',
            ),
        ),
        migrations.AlterField(
            model_name='computer',
            name='disks',
            field=models.SmallIntegerField(
                blank=True, db_comment='number of disk drives', null=True, verbose_name='disks'
            ),
        ),
        migrations.AlterField(
            model_name='computer',
            name='forwarded_ip_address',
            field=models.GenericIPAddressField(
                blank=True, db_comment='forwarded IP address', null=True, verbose_name='forwarded ip address'
            ),
        ),
        migrations.AlterField(
            model_name='computer',
            name='fqdn',
            field=models.CharField(
                blank=True,
                db_comment='domain name that specifies its exact location in the tree hierarchy of the '
                'Domain Name System',
                max_length=255,
                null=True,
                verbose_name='full qualified domain name',
            ),
        ),
        migrations.AlterField(
            model_name='computer',
            name='ip_address',
            field=models.GenericIPAddressField(
                blank=True, db_comment='computer IP address', null=True, verbose_name='ip address'
            ),
        ),
        migrations.AlterField(
            model_name='computer',
            name='last_hardware_capture',
            field=models.DateTimeField(
                blank=True, db_comment='last hardware capture date', null=True, verbose_name='last hardware capture'
            ),
        ),
        migrations.AlterField(
            model_name='computer',
            name='mac_address',
            field=models.CharField(
                blank=True,
                db_comment='MAC addresses of network interfaces',
                max_length=60,
                null=True,
                verbose_name='MAC address',
            ),
        ),
        migrations.AlterField(
            model_name='computer',
            name='machine',
            field=models.CharField(
                choices=[('P', 'Physical'), ('V', 'Virtual')],
                db_comment='computer type (single-character string: use "P" for physical and "V" for virtual)',
                default='P',
                max_length=1,
                verbose_name='machine',
            ),
        ),
        migrations.AlterField(
            model_name='computer',
            name='name',
            field=models.CharField(
                blank=True, db_comment='computer name', max_length=50, null=True, verbose_name='name'
            ),
        ),
        migrations.AlterField(
            model_name='computer',
            name='product',
            field=models.CharField(
                blank=True,
                db_comment='description of the computer product',
                max_length=80,
                null=True,
                verbose_name='product',
            ),
        ),
        migrations.AlterField(
            model_name='computer',
            name='project',
            field=models.ForeignKey(
                db_comment='project to which the computer belongs',
                on_delete=django.db.models.deletion.CASCADE,
                to='core.project',
                verbose_name='project',
            ),
        ),
        migrations.AlterField(
            model_name='computer',
            name='ram',
            field=models.BigIntegerField(
                blank=True, db_comment='amount of installed RAM in bytes', null=True, verbose_name='RAM'
            ),
        ),
        migrations.AlterField(
            model_name='computer',
            name='status',
            field=models.CharField(
                choices=[
                    ('intended', 'Intended'),
                    ('reserved', 'Reserved'),
                    ('unknown', 'Unknown'),
                    ('in repair', 'In repair'),
                    ('available', 'Available'),
                    ('unsubscribed', 'Unsubscribed'),
                ],
                db_comment='computer status: intended, reserved, unknown, in repair, available or unsubscribed',
                default='intended',
                max_length=20,
                verbose_name='status',
            ),
        ),
        migrations.AlterField(
            model_name='computer',
            name='storage',
            field=models.BigIntegerField(
                blank=True, db_comment='total storage amount (bytes)', null=True, verbose_name='storage'
            ),
        ),
        migrations.AlterField(
            model_name='computer',
            name='sync_attributes',
            field=models.ManyToManyField(
                blank=True,
                help_text='computer attributes at the time of sync',
                to='core.attribute',
                verbose_name='sync attributes',
            ),
        ),
        migrations.AlterField(
            model_name='computer',
            name='sync_end_date',
            field=models.DateTimeField(db_comment='synchronization end date', null=True, verbose_name='sync end date'),
        ),
        migrations.AlterField(
            model_name='computer',
            name='sync_start_date',
            field=models.DateTimeField(
                db_comment='synchronization start date', null=True, verbose_name='sync start date'
            ),
        ),
        migrations.AlterField(
            model_name='computer',
            name='sync_user',
            field=models.ForeignKey(
                db_comment='user logged into the graphical session at the time of computer sync',
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to='client.user',
                verbose_name='sync user',
            ),
        ),
        migrations.AlterField(
            model_name='computer',
            name='updated_at',
            field=models.DateTimeField(auto_now=True, db_comment='computer update date on migasfree system'),
        ),
        migrations.AlterField(
            model_name='computer',
            name='uuid',
            field=models.CharField(
                blank=True,
                db_comment="Universally Unique IDentifier based on the computer's motherboard",
                default='',
                max_length=36,
                null=True,
                unique=True,
                verbose_name='uuid',
            ),
        ),
        migrations.AlterField(
            model_name='error',
            name='checked',
            field=models.BooleanField(
                db_comment='indicates whether the error has been verified or not', default=False, verbose_name='checked'
            ),
        ),
        migrations.AlterField(
            model_name='error',
            name='computer',
            field=models.ForeignKey(
                db_comment='computer to which the event corresponds',
                on_delete=django.db.models.deletion.CASCADE,
                to='client.computer',
                verbose_name='computer',
            ),
        ),
        migrations.AlterField(
            model_name='error',
            name='created_at',
            field=models.DateTimeField(
                auto_now_add=True, db_comment='date on which the event is created', verbose_name='date'
            ),
        ),
        migrations.AlterField(
            model_name='error',
            name='description',
            field=models.TextField(
                blank=True, db_comment='computer error description', null=True, verbose_name='description'
            ),
        ),
        migrations.AlterField(
            model_name='error',
            name='project',
            field=models.ForeignKey(
                db_comment='project to which the computer belongs',
                on_delete=django.db.models.deletion.CASCADE,
                to='core.project',
                verbose_name='project',
            ),
        ),
        migrations.AlterField(
            model_name='fault',
            name='checked',
            field=models.BooleanField(
                db_comment='indicates whether the fault has been verified by any user of the application',
                default=False,
                verbose_name='checked',
            ),
        ),
        migrations.AlterField(
            model_name='fault',
            name='computer',
            field=models.ForeignKey(
                db_comment='computer to which the event corresponds',
                on_delete=django.db.models.deletion.CASCADE,
                to='client.computer',
                verbose_name='computer',
            ),
        ),
        migrations.AlterField(
            model_name='fault',
            name='created_at',
            field=models.DateTimeField(
                auto_now_add=True, db_comment='date on which the event is created', verbose_name='date'
            ),
        ),
        migrations.AlterField(
            model_name='fault',
            name='fault_definition',
            field=models.ForeignKey(
                db_comment='related fault definition',
                on_delete=django.db.models.deletion.CASCADE,
                to='client.faultdefinition',
                verbose_name='fault definition',
            ),
        ),
        migrations.AlterField(
            model_name='fault',
            name='project',
            field=models.ForeignKey(
                db_comment='project to which the computer belongs',
                on_delete=django.db.models.deletion.CASCADE,
                to='core.project',
                verbose_name='project',
            ),
        ),
        migrations.AlterField(
            model_name='fault',
            name='result',
            field=models.TextField(
                blank=True,
                db_comment='fault result (if not empty indicates that fault has occurred)',
                null=True,
                verbose_name='result',
            ),
        ),
        migrations.AlterField(
            model_name='faultdefinition',
            name='code',
            field=models.TextField(blank=True, db_comment='fault programming code', verbose_name='code'),
        ),
        migrations.AlterField(
            model_name='faultdefinition',
            name='description',
            field=models.TextField(
                blank=True, db_comment='fault definition description', null=True, verbose_name='description'
            ),
        ),
        migrations.AlterField(
            model_name='faultdefinition',
            name='enabled',
            field=models.BooleanField(
                db_comment='indicates if the fault definition will execute', default=True, verbose_name='enabled'
            ),
        ),
        migrations.AlterField(
            model_name='faultdefinition',
            name='language',
            field=models.IntegerField(
                choices=[
                    (0, 'bash'),
                    (1, 'python'),
                    (2, 'perl'),
                    (3, 'php'),
                    (4, 'ruby'),
                    (5, 'cmd'),
                    (6, 'powershell'),
                ],
                db_comment='programming language used to implement the fault',
                default=0,
                verbose_name='programming language',
            ),
        ),
        migrations.AlterField(
            model_name='faultdefinition',
            name='name',
            field=models.CharField(db_comment='fault definition name', max_length=50, unique=True, verbose_name='name'),
        ),
        migrations.AlterField(
            model_name='migration',
            name='computer',
            field=models.ForeignKey(
                db_comment='computer to which the event corresponds',
                on_delete=django.db.models.deletion.CASCADE,
                to='client.computer',
                verbose_name='computer',
            ),
        ),
        migrations.AlterField(
            model_name='migration',
            name='created_at',
            field=models.DateTimeField(
                auto_now_add=True, db_comment='date on which the event is created', verbose_name='date'
            ),
        ),
        migrations.AlterField(
            model_name='migration',
            name='project',
            field=models.ForeignKey(
                db_comment='project to which the computer has been migrated',
                on_delete=django.db.models.deletion.CASCADE,
                to='core.project',
                verbose_name='project',
            ),
        ),
        migrations.AlterField(
            model_name='notification',
            name='checked',
            field=models.BooleanField(
                db_comment='indicates whether the notification has been verified', default=False, verbose_name='checked'
            ),
        ),
        migrations.AlterField(
            model_name='notification',
            name='created_at',
            field=models.DateTimeField(
                auto_now_add=True, db_comment='date on which the notification occurs', verbose_name='date'
            ),
        ),
        migrations.AlterField(
            model_name='notification',
            name='message',
            field=models.TextField(db_comment='notification message', verbose_name='message'),
        ),
        migrations.AlterField(
            model_name='packagehistory',
            name='computer',
            field=models.ForeignKey(
                db_comment='related computer',
                on_delete=django.db.models.deletion.CASCADE,
                to='client.computer',
                verbose_name='computer',
            ),
        ),
        migrations.AlterField(
            model_name='packagehistory',
            name='install_date',
            field=models.DateTimeField(
                auto_now_add=True,
                db_comment='date the package was installed on the computer',
                null=True,
                verbose_name='install date',
            ),
        ),
        migrations.AlterField(
            model_name='packagehistory',
            name='package',
            field=models.ForeignKey(
                db_comment='related package',
                on_delete=django.db.models.deletion.CASCADE,
                to='core.package',
                verbose_name='package',
            ),
        ),
        migrations.AlterField(
            model_name='packagehistory',
            name='uninstall_date',
            field=models.DateTimeField(
                db_comment='date of uninstallation of the package on the computer',
                null=True,
                verbose_name='uninstall date',
            ),
        ),
        migrations.AlterField(
            model_name='statuslog',
            name='computer',
            field=models.ForeignKey(
                db_comment='computer to which the event corresponds',
                on_delete=django.db.models.deletion.CASCADE,
                to='client.computer',
                verbose_name='computer',
            ),
        ),
        migrations.AlterField(
            model_name='statuslog',
            name='created_at',
            field=models.DateTimeField(
                auto_now_add=True, db_comment='date on which the event is created', verbose_name='date'
            ),
        ),
        migrations.AlterField(
            model_name='statuslog',
            name='status',
            field=models.CharField(
                choices=[
                    ('intended', 'Intended'),
                    ('reserved', 'Reserved'),
                    ('unknown', 'Unknown'),
                    ('in repair', 'In repair'),
                    ('available', 'Available'),
                    ('unsubscribed', 'Unsubscribed'),
                ],
                db_comment='computer status on a specific date',
                default='intended',
                max_length=20,
                verbose_name='status',
            ),
        ),
        migrations.AlterField(
            model_name='synchronization',
            name='computer',
            field=models.ForeignKey(
                db_comment='computer to which the event corresponds',
                on_delete=django.db.models.deletion.CASCADE,
                to='client.computer',
                verbose_name='computer',
            ),
        ),
        migrations.AlterField(
            model_name='synchronization',
            name='consumer',
            field=models.CharField(
                db_comment='application that has done the synchronization',
                max_length=50,
                null=True,
                verbose_name='consumer',
            ),
        ),
        migrations.AlterField(
            model_name='synchronization',
            name='created_at',
            field=models.DateTimeField(
                auto_now_add=True, db_comment='date on which the event is created', verbose_name='date'
            ),
        ),
        migrations.AlterField(
            model_name='synchronization',
            name='pms_status_ok',
            field=models.BooleanField(
                db_comment='indicates whether the packaging system completed successfully '
                '(true for no error, false for error)',
                default=False,
                help_text='indicates the status of transactions with PMS',
                verbose_name='PMS status OK',
            ),
        ),
        migrations.AlterField(
            model_name='synchronization',
            name='project',
            field=models.ForeignKey(
                db_comment='project to which the computer belongs',
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to='core.project',
                verbose_name='project',
            ),
        ),
        migrations.AlterField(
            model_name='synchronization',
            name='start_date',
            field=models.DateTimeField(
                blank=True, db_comment='start date connection', null=True, verbose_name='start date connection'
            ),
        ),
        migrations.AlterField(
            model_name='synchronization',
            name='user',
            field=models.ForeignKey(
                db_comment='user logged into the graphical session at the time of computer sync',
                on_delete=django.db.models.deletion.CASCADE,
                to='client.user',
                verbose_name='user',
            ),
        ),
        migrations.AlterField(
            model_name='user',
            name='fullname',
            field=models.CharField(blank=True, db_comment="user's fullname", max_length=100, verbose_name='fullname'),
        ),
        migrations.AlterField(
            model_name='user',
            name='name',
            field=models.CharField(db_comment="user's name", max_length=50, verbose_name='name'),
        ),
    ]
