# Generated by Django 2.2.7 on 2019-12-05 00:57

from django.conf import settings
import django.contrib.postgres.fields
from django.db import migrations, models
import django.db.models.deletion
import talents.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('categories', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Talent',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('phone_number', models.CharField(max_length=9)),
                ('area_code', models.CharField(max_length=2)),
                ('main_social_media', models.CharField(max_length=100)),
                ('social_media_username', models.CharField(max_length=80)),
                ('number_of_followers', models.PositiveIntegerField()),
                ('price', models.DecimalField(blank=True, decimal_places=2, max_digits=7, null=True)),
                ('description', models.TextField(blank=True)),
                ('available', models.BooleanField(default=False)),
                ('categories', models.ManyToManyField(related_name='talents', related_query_name='talent', to='categories.Category')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='PresentationVideo',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('file', models.FileField(max_length=140, upload_to=talents.models.upload_location)),
                ('talent', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='presentation_video', to='talents.Talent')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='DebtsPaymentLog',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('num_viggios', models.PositiveSmallIntegerField()),
                ('amount_paid', models.DecimalField(decimal_places=2, max_digits=7)),
                ('reference_month', models.DateField()),
                ('paid_debts_ids_array', django.contrib.postgres.fields.ArrayField(base_field=models.IntegerField(), size=None)),
                ('talent', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='talents.Talent')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='BankAccount',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('fullname', models.CharField(max_length=100)),
                ('tax_document', models.CharField(max_length=14)),
                ('bank', models.CharField(max_length=80)),
                ('bank_transit_number', models.CharField(max_length=10)),
                ('bank_branch_number', models.CharField(max_length=10)),
                ('account_number', models.CharField(max_length=10)),
                ('account_control_digit', models.CharField(blank=True, max_length=10)),
                ('talent', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='bank_account', to='talents.Talent')),
            ],
        ),
        migrations.AddConstraint(
            model_name='bankaccount',
            constraint=models.UniqueConstraint(fields=('account_number', 'bank_transit_number'), name='unique_bank_account'),
        ),
    ]