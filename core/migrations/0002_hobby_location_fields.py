from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='hobby',
            name='province',
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name='hobby',
            name='city',
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name='hobby',
            name='neighbourhood',
            field=models.CharField(blank=True, max_length=150),
        ),
    ]
