# Merge migration to resolve conflicting moleculeflow migrations.
from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("chemistry", "0002_moleculeflow_add_role_step_number"),
        ("chemistry", "0003_moleculeflow_add_role_step_number"),
    ]

    operations = []
