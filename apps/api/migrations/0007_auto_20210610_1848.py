# Generated by Django 3.2 on 2021-06-10 17:48

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0006_auto_20210610_1842'),
    ]

    operations = [
        migrations.AlterField(
            model_name='timeslot',
            name='ClassGroup',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='api.classgroup'),
        ),
        migrations.AlterField(
            model_name='timeslot',
            name='Room',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='api.room'),
        ),
        migrations.AlterField(
            model_name='timeslot',
            name='Subject',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='api.subject'),
        ),
        migrations.AlterField(
            model_name='timeslot',
            name='Teacher',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='api.teacher'),
        ),
    ]
