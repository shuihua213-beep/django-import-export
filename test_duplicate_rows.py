import os
import django
from django.conf import settings

settings.configure(
    INSTALLED_APPS=[
        'django.contrib.auth',
        'django.contrib.contenttypes',
        'core',
    ],
    DATABASES={
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': ':memory:',
        }
    },
)
django.setup()

from django.core.management import call_command
call_command('migrate', verbosity=0)

import tablib
from import_export import resources
from core.models import Book

class BookResource(resources.ModelResource):
    class Meta:
        model = Book
        use_bulk = True

class BookResourceNoBulk(resources.ModelResource):
    class Meta:
        model = Book
        use_bulk = False

dataset = tablib.Dataset(headers=['id', 'name'])
dataset.append(['1', 'Book 1'])
dataset.append(['1', 'Book 1 Updated'])

print("--- No Bulk, dry_run=True ---")
res1 = BookResourceNoBulk().import_data(dataset, dry_run=True)
print("Totals:", res1.totals)

print("--- No Bulk, dry_run=False ---")
res2 = BookResourceNoBulk().import_data(dataset, dry_run=False)
print("Totals:", res2.totals)

print("--- Bulk, dry_run=True ---")
res3 = BookResource().import_data(dataset, dry_run=True)
print("Totals:", res3.totals)

print("--- Bulk, dry_run=False ---")
try:
    res4 = BookResource().import_data(dataset, dry_run=False)
    print("Totals:", res4.totals)
except Exception as e:
    print("Exception:", e)
