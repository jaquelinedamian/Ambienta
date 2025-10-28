from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ml_models', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='mlmodel',
            name='model_data',
            field=models.BinaryField(blank=True, null=True),
        ),
        migrations.RunPython(
            code=lambda apps, schema_editor: None,  # Forward - handled by load_model
            reverse_code=lambda apps, schema_editor: None,  # Backward
            elidable=True,
        ),
        migrations.RemoveField(
            model_name='mlmodel',
            name='model_file_path',
        ),
    ]