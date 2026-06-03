import os
import sys

import django

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'tests')))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")
django.setup()

from core.models import Book
from import_export import resources

class BookResource(resources.ModelResource):
    class Meta:
        model = Book
        use_bulk = True
        batch_size = 2

def stream_dataset():
    for i in range(5):
        yield {"id": i + 100, "name": f"Book {i}", "author_email": f"author{i}@example.com", "price": "10.00"}

resource = BookResource()
print("Starting import...")
result = resource.import_data(stream_dataset())
print("Total rows:", result.total_rows)
print("New rows:", result.totals["new"])
print("Books count:", Book.objects.filter(id__gte=100).count())
