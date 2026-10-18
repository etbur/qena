from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


def clear_supplier(apps, schema_editor):
    schema_editor.connection.cursor().execute(
        "UPDATE vendors_vendorinventoryitem SET supplier = \'\'")


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("vendors", "0003_vendorinventoryitem"),
    ]

    operations = [
        migrations.RunPython(clear_supplier, migrations.RunPython.noop),
        migrations.RemoveField(model_name="vendorinventoryitem", name="supplier"),
        migrations.AddField(model_name="vendorinventoryitem", name="barcode", field=models.CharField(blank=True, db_index=True, max_length=100)),
        migrations.AddField(model_name="vendorinventoryitem", name="expiry_date", field=models.DateField(blank=True, null=True)),
        migrations.AddField(model_name="vendorinventoryitem", name="image", field=models.ImageField(blank=True, null=True, upload_to="inventory/")),
        migrations.AddField(model_name="vendorinventoryitem", name="unit", field=models.CharField(blank=True, default="pcs", max_length=30)),
        migrations.AlterField(model_name="vendorinventoryitem", name="sku", field=models.CharField(blank=True, db_index=True, max_length=100)),
        migrations.CreateModel(
            name="VendorWarehouse",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=150)),
                ("address", models.TextField(blank=True)),
                ("city", models.CharField(blank=True, max_length=100)),
                ("phone", models.CharField(blank=True, max_length=30)),
                ("is_default", models.BooleanField(default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("vendor", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="warehouses", to="vendors.vendor")),
            ],
            options={"ordering": ["-is_default", "name"]},
        ),
        migrations.CreateModel(
            name="VendorSupplier",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=200)),
                ("contact_person", models.CharField(blank=True, max_length=150)),
                ("email", models.EmailField(blank=True, max_length=254)),
                ("phone", models.CharField(blank=True, max_length=30)),
                ("address", models.TextField(blank=True)),
                ("notes", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("vendor", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="suppliers", to="vendors.vendor")),
            ],
            options={"ordering": ["name"]},
        ),
        migrations.AddField(model_name="vendorinventoryitem", name="warehouse", field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="items", to="vendors.vendorwarehouse")),
        migrations.AddField(model_name="vendorinventoryitem", name="supplier", field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="items", to="vendors.vendorsupplier")),
        migrations.CreateModel(
            name="StockMovement",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("move_type", models.CharField(choices=[("in","Stock In"),("out","Stock Out"),("transfer","Transfer"),("adjust","Adjustment"),("return","Customer Return")], max_length=12)),
                ("quantity", models.IntegerField()),
                ("before_qty", models.IntegerField(default=0)),
                ("after_qty", models.IntegerField(default=0)),
                ("reference", models.CharField(blank=True, max_length=200)),
                ("note", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("created_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
                ("item", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="movements", to="vendors.vendorinventoryitem")),
            ],
            options={"ordering": ["-created_at"]},
        ),
        migrations.CreateModel(
            name="PurchaseOrder",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("po_number", models.CharField(blank=True, max_length=50, unique=True)),
                ("status", models.CharField(choices=[("draft","Draft"),("ordered","Ordered"),("received","Received"),("cancelled","Cancelled")], default="draft", max_length=12)),
                ("total_cost", models.DecimalField(decimal_places=2, default=0, max_digits=14)),
                ("note", models.TextField(blank=True)),
                ("expected_date", models.DateField(blank=True, null=True)),
                ("received_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("supplier", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to="vendors.vendorsupplier")),
                ("vendor", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="purchase_orders", to="vendors.vendor")),
            ],
            options={"ordering": ["-created_at"]},
        ),
        migrations.CreateModel(
            name="PurchaseOrderItem",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("item_name", models.CharField(max_length=250)),
                ("quantity", models.PositiveIntegerField(default=1)),
                ("unit_cost", models.DecimalField(decimal_places=2, max_digits=10)),
                ("inventory_item", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to="vendors.vendorinventoryitem")),
                ("po", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="items", to="vendors.purchaseorder")),
            ],
        ),
    ]
