from django.db import migrations

def create_groups(apps, schema_editor):
    Group = apps.get_model('auth', 'Group')
    group_names = ['Administrador', 'Vendedor', 'Almacén']
    for name in group_names:
        Group.objects.get_or_create(name=name)

def revert_groups(apps, schema_editor):
    # La migración inversa no debe eliminar grupos que puedan contener usuarios o permisos.
    pass

class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.RunPython(create_groups, revert_groups),
    ]
