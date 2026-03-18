# Generated migration for favorite workflows feature

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("agent_app", "0023_add_completed_by_user_id"),
    ]

    operations = [
        migrations.AddField(
            model_name="userpreference",
            name="favorite_workflows",
            field=models.TextField(
                blank=True,
                default="[]",
                help_text="JSON-encoded list of favorite workflow IDs",
                null=True,
            ),
        ),
    ]
