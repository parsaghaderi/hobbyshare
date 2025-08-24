from django.db import migrations, models
import django.db.models.deletion
import core.models


class Migration(migrations.Migration):
    dependencies = [
        ('core', '0002_hobby_location_fields'),
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='Supplier',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('province', models.CharField(blank=True, max_length=100)),
                ('city', models.CharField(blank=True, max_length=100)),
                ('neighbourhood', models.CharField(blank=True, max_length=150)),
                ('active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='supplier', to='auth.user')),
            ],
        ),
        migrations.CreateModel(
            name='SupplierItem',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('quantity', models.PositiveIntegerField(default=1)),
                ('is_rental', models.BooleanField(default=True)),
                ('price', models.DecimalField(decimal_places=2, max_digits=10)),
                ('image', models.ImageField(blank=True, null=True, upload_to=core.models.supplier_item_image_upload)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('category', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='supplier_items', to='core.category')),
                ('supplier', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='items', to='core.supplier')),
                ('tag', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='supplier_items', to='core.tag')),
            ],
        ),
        migrations.AddField(
            model_name='requirement',
            name='category',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='requirements', to='core.category'),
        ),
        migrations.AddField(
            model_name='requirement',
            name='tag',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='requirements', to='core.tag'),
        ),
    ]