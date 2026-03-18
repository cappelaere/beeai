# PAR-015: intermediateCatchEvent timer/message wait statuses

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("agent_app", "0029_workflow"),
    ]

    operations = [
        migrations.AlterField(
            model_name="workflowrun",
            name="status",
            field=models.CharField(
                choices=[
                    ("pending", "Pending"),
                    ("running", "Running"),
                    ("completed", "Completed"),
                    ("failed", "Failed"),
                    ("cancelled", "Cancelled"),
                    ("waiting_for_task", "Waiting for Task"),
                    ("waiting_for_bpmn_timer", "Waiting for BPMN timer"),
                    ("waiting_for_bpmn_message", "Waiting for BPMN message"),
                ],
                db_index=True,
                default="pending",
                max_length=32,
            ),
        ),
    ]
