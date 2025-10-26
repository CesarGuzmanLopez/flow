# Migration to add 'role' and 'step_number' to MoleculeFlow (assistant-created)
from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("chemistry", "0002_moleculeflow_add_role_step_number"),
    ]

    # No-op: fields added in 0002_moleculeflow_add_role_step_number
    operations = []
