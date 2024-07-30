# Generated by Django 5.0 on 2024-07-15 12:36

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bookstore', '0003_order_orderitem'),
    ]

    operations = [
        migrations.AlterField(
            model_name='cartitem',
            name='cart',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='items', to='bookstore.cart'),
        ),
    ]
