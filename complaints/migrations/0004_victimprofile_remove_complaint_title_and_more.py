# Generated manually for the registration/profile and reporting-flow update.

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


def copy_existing_phone_numbers(apps, schema_editor):
    Complaint = apps.get_model('complaints', 'Complaint')
    VictimProfile = apps.get_model('complaints', 'VictimProfile')
    seen_user_ids = set()
    for complaint in Complaint.objects.exclude(victim_phone__isnull=True).exclude(victim_phone='').order_by('-created_at'):
        if complaint.victim_id not in seen_user_ids:
            VictimProfile.objects.get_or_create(
                user_id=complaint.victim_id,
                defaults={'phone_number': complaint.victim_phone},
            )
            seen_user_ids.add(complaint.victim_id)


def reverse_copy_existing_phone_numbers(apps, schema_editor):
    # Phone numbers remain on the profile when rolling back; report copies are not recreated.
    pass


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('complaints', '0003_complaint_investigator_remarks'),
    ]

    operations = [
        migrations.CreateModel(
            name='VictimProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('phone_number', models.CharField(max_length=255)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='victim_profile', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.RunPython(copy_existing_phone_numbers, reverse_copy_existing_phone_numbers),
        migrations.RemoveField(
            model_name='complaint',
            name='title',
        ),
        migrations.RemoveField(
            model_name='complaint',
            name='victim_phone',
        ),
        migrations.AlterField(
            model_name='complaint',
            name='amount_lost',
            field=models.DecimalField(decimal_places=2, default=0.0, max_digits=12, verbose_name='Amount lost (₦)'),
        ),
    ]
