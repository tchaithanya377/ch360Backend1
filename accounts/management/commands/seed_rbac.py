import os
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction

from django.contrib.auth.models import Group, Permission as AuthPermission
from accounts.models import Permission as CustomPermission


class Command(BaseCommand):
    help = "Seed default roles, permissions, and an initial admin user (idempotent)."

    def add_arguments(self, parser):
        parser.add_argument('--admin-email', default=os.getenv('SEED_ADMIN_EMAIL', 'admin@campushub360.com'))
        parser.add_argument('--admin-password', default=os.getenv('SEED_ADMIN_PASSWORD', 'Admin@12345'))
        parser.add_argument('--admin-username', default=os.getenv('SEED_ADMIN_USERNAME', 'admin'))

    @transaction.atomic
    def handle(self, *args, **options):
        User = get_user_model()

        # Define baseline roles and permissions
        roles = ['Admin', 'Registrar', 'HOD', 'Faculty', 'Student', 'Accounts', 'Transport', 'Librarian']
        permissions = [
            'students.view', 'students.add', 'students.change', 'students.delete',
            'departments.view', 'departments.add', 'departments.change', 'departments.delete',
            'academics.view', 'academics.add', 'academics.change', 'academics.delete',
            'enrollment.manage', 'assignments.manage', 'attendance.manage',
        ]

        role_to_perms = {
            'Admin': permissions,
            'Registrar': [
                'students.view', 'students.add', 'students.change',
                'departments.view', 'academics.view', 'enrollment.manage'
            ],
            'HOD': [
                'students.view', 'students.change', 'departments.view',
                'academics.view', 'assignments.manage', 'attendance.manage'
            ],
            'Faculty': [
                'students.view', 'assignments.manage', 'attendance.manage'
            ],
            'Student': [
                'students.view', 'academics.view'
            ],
            'Accounts': ['students.view'],
            'Transport': ['students.view'],
            'Librarian': ['students.view'],
        }

        # Migrate: ensure our custom permission catalog exists (optional), but attach via Django Groups
        perm_objs = {}
        for code in permissions:
            # store in custom table for catalog/reference
            CustomPermission.objects.get_or_create(codename=code)
            # also create a django auth permission proxy via content_type None (or skip and rely on get_all_permissions custom codenames?)
            perm_objs[code], _ = AuthPermission.objects.get_or_create(codename=code, name=code, content_type_id=1)

        # Create groups as roles and attach auth permissions
        group_objs = {}
        for r in roles:
            group, _ = Group.objects.get_or_create(name=r)
            group_objs[r] = group
            pcodes = role_to_perms.get(r, [])
            group.permissions.set([perm_objs[p] for p in pcodes])

        # Ensure admin user
        admin_email = options['admin_email']
        admin_password = options['admin_password']
        admin_username = options['admin_username']

        user, created = User.objects.get_or_create(email=admin_email, defaults={
            'username': admin_username,
            'is_staff': True,
            'is_superuser': True,
            'is_active': True,
        })
        if created:
            user.set_password(admin_password)
            user.save(update_fields=['password'])
            self.stdout.write(self.style.SUCCESS(f"Created admin user {admin_email}"))
        else:
            self.stdout.write(f"Admin user {admin_email} already exists")

        # Assign Admin group to admin user
        if user:
            user.groups.add(group_objs['Admin'])

        self.stdout.write(self.style.SUCCESS('Roles, permissions, and admin user seeded successfully.'))


