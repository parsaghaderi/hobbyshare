from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):
    dependencies = [
        ('core', '0004_alter_supplier_id_alter_supplieritem_id'),
    ]

    operations = [
        migrations.AddField(
            model_name='requirement',
            name='supplier_item',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='requirements', to='core.supplieritem'),
        ),
        migrations.AddField(
            model_name='requirement',
            name='supplier_status',
            field=models.CharField(choices=[('pending', 'Pending'), ('accepted', 'Accepted'), ('declined', 'Declined')], default='pending', max_length=10),
        ),
        migrations.AddField(
            model_name='requirement',
            name='supplier_requested_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]