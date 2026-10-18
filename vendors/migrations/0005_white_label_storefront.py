from django.db import migrations, models


def populate_subdomains(apps, schema_editor):
    """Set subdomain = slug for all existing vendors before adding unique constraint."""
    Vendor = apps.get_model('vendors', 'Vendor')
    for v in Vendor.objects.all():
        v.subdomain = v.slug
        v.save(update_fields=['subdomain'])


class Migration(migrations.Migration):

    dependencies = [
        ('vendors', '0004_inventory_full'),
    ]

    operations = [
        # Add non-unique subdomain first (blank allowed so existing rows get '')
        migrations.AddField(
            model_name='vendor',
            name='subdomain',
            field=models.CharField(blank=True, max_length=100, default='',
                                   help_text='Subdomain e.g. "alex" → alex.qenagebeya.com'),
        ),
        # Populate from slug before adding unique constraint
        migrations.RunPython(populate_subdomains, migrations.RunPython.noop),
        # Now make it unique
        migrations.AlterField(
            model_name='vendor',
            name='subdomain',
            field=models.CharField(blank=True, unique=True, max_length=100,
                                   help_text='Subdomain e.g. "alex" → alex.qenagebeya.com'),
        ),
        migrations.AddField(model_name='vendor', name='brand_font',
            field=models.CharField(blank=True, default='Inter', max_length=100)),
        migrations.AddField(model_name='vendor', name='brand_primary',
            field=models.CharField(default='#0b2b4a', max_length=7)),
        migrations.AddField(model_name='vendor', name='brand_secondary',
            field=models.CharField(default='#d42e2e', max_length=7)),
        migrations.AddField(model_name='vendor', name='custom_domain',
            field=models.CharField(blank=True, max_length=253)),
        migrations.AddField(model_name='vendor', name='storefront_enabled',
            field=models.BooleanField(default=True)),
        migrations.AddField(model_name='vendor', name='store_tagline',
            field=models.CharField(blank=True, max_length=200)),
        migrations.AddField(model_name='vendor', name='store_keywords',
            field=models.CharField(blank=True, max_length=300)),
        migrations.AddField(model_name='vendor', name='whatsapp',
            field=models.CharField(blank=True, max_length=30)),
        migrations.AddField(model_name='vendor', name='telegram',
            field=models.CharField(blank=True, max_length=100)),
        migrations.AddField(model_name='vendor', name='instagram',
            field=models.CharField(blank=True, max_length=100)),
        migrations.AddField(model_name='vendor', name='facebook',
            field=models.CharField(blank=True, max_length=100)),
        migrations.AddField(model_name='vendor', name='twitter',
            field=models.CharField(blank=True, max_length=100)),
        migrations.AddField(model_name='vendor', name='tiktok',
            field=models.CharField(blank=True, max_length=100)),
    ]
