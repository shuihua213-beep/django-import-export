import csv
import io
from unittest import mock

import tablib
from core.models import Book, UUIDBook
from django.test import TestCase

from import_export import resources
from import_export.resources import StreamingDataset


class StreamingDatasetTest(TestCase):
    def test_streaming_dataset_from_csv_file(self):
        csv_content = "id,name\n1,Book One\n2,Book Two\n3,Book Three\n"
        csv_file = io.StringIO(csv_content)
        stream_ds = StreamingDataset(csv_file, format='csv')
        
        self.assertEqual(['id', 'name'], stream_ds.headers)
        
        rows = list(stream_ds)
        self.assertEqual(3, len(rows))
        self.assertEqual(['1', 'Book One'], rows[0])
        self.assertEqual(['2', 'Book Two'], rows[1])
        self.assertEqual(['3', 'Book Three'], rows[2])

    def test_streaming_dataset_from_iterator(self):
        def row_iterator():
            yield ['1', 'Book One']
            yield ['2', 'Book Two']
            yield ['3', 'Book Three']
        
        stream_ds = StreamingDataset(row_iterator(), headers=['id', 'name'])
        
        self.assertEqual(['id', 'name'], stream_ds.headers)
        
        rows = list(stream_ds)
        self.assertEqual(3, len(rows))
        self.assertEqual(['1', 'Book One'], rows[0])

    def test_streaming_dataset_raises_on_len(self):
        csv_content = "id,name\n1,Book One\n"
        csv_file = io.StringIO(csv_content)
        stream_ds = StreamingDataset(csv_file, format='csv')
        
        with self.assertRaises(RuntimeError) as context:
            len(stream_ds)
        
        self.assertIn("does not support len()", str(context.exception))

    def test_streaming_dataset_raises_on_dict_access(self):
        csv_content = "id,name\n1,Book One\n"
        csv_file = io.StringIO(csv_content)
        stream_ds = StreamingDataset(csv_file, format='csv')
        
        with self.assertRaises(RuntimeError) as context:
            _ = stream_ds.dict
        
        self.assertIn("does not support dict access", str(context.exception))

    def test_streaming_dataset_requires_format_for_file(self):
        csv_file = io.StringIO("id,name\n")
        
        with self.assertRaises(ValueError) as context:
            StreamingDataset(csv_file)
        
        self.assertIn("format parameter is required", str(context.exception))

    def test_streaming_dataset_requires_headers_for_iterator(self):
        def row_iterator():
            yield ['1', 'Book One']
        
        with self.assertRaises(ValueError) as context:
            StreamingDataset(row_iterator())
        
        self.assertIn("headers parameter is required", str(context.exception))

    def test_streaming_dataset_single_iteration(self):
        csv_content = "id,name\n1,Book One\n2,Book Two\n"
        csv_file = io.StringIO(csv_content)
        stream_ds = StreamingDataset(csv_file, format='csv')
        
        rows1 = list(stream_ds)
        self.assertEqual(2, len(rows1))
        
        with self.assertRaises(RuntimeError):
            list(stream_ds)


class StreamingImportTest(TestCase):
    def setUp(self):
        class _BookResource(resources.ModelResource):
            class Meta:
                model = Book
                use_bulk = True

        self.resource = _BookResource()

    def test_import_stream_basic(self):
        csv_content = "id,name\n1,Book One\n2,Book Two\n3,Book Three\n"
        csv_file = io.StringIO(csv_content)
        stream_ds = StreamingDataset(csv_file, format='csv')
        
        result = self.resource.import_stream(stream_ds)
        
        self.assertEqual(3, result.total_rows)
        self.assertEqual(3, Book.objects.count())
        self.assertEqual(3, result.totals["new"])

    def test_import_stream_with_batch_size(self):
        class _BookResource(resources.ModelResource):
            class Meta:
                model = Book
                use_bulk = True
                batch_size = 2

        resource = _BookResource()
        
        csv_content = "id,name\n1,Book One\n2,Book Two\n3,Book Three\n4,Book Four\n5,Book Five\n"
        csv_file = io.StringIO(csv_content)
        stream_ds = StreamingDataset(csv_file, format='csv')
        
        with mock.patch("core.models.Book.objects.bulk_create") as mock_bulk:
            result = resource.import_stream(stream_ds)
            self.assertEqual(3, mock_bulk.call_count)
        
        self.assertEqual(5, result.total_rows)
        self.assertEqual(5, Book.objects.count())

    def test_import_stream_dry_run(self):
        csv_content = "id,name\n1,Book One\n2,Book Two\n"
        csv_file = io.StringIO(csv_content)
        stream_ds = StreamingDataset(csv_file, format='csv')
        
        result = self.resource.import_stream(stream_ds, dry_run=True)
        
        self.assertEqual(2, result.total_rows)
        self.assertEqual(0, Book.objects.count())
        self.assertEqual(2, result.totals["new"])

    def test_import_stream_update(self):
        Book.objects.create(id=1, name="Original One")
        Book.objects.create(id=2, name="Original Two")
        
        csv_content = "id,name\n1,Updated One\n2,Updated Two\n"
        csv_file = io.StringIO(csv_content)
        stream_ds = StreamingDataset(csv_file, format='csv')
        
        class _BookResource(resources.ModelResource):
            class Meta:
                model = Book
                use_bulk = True
                import_id_fields = ('id',)

        resource = _BookResource()
        result = resource.import_stream(stream_ds)
        
        self.assertEqual(2, result.total_rows)
        self.assertEqual(2, result.totals["update"])
        
        self.assertEqual("Updated One", Book.objects.get(id=1).name)
        self.assertEqual("Updated Two", Book.objects.get(id=2).name)

    def test_import_stream_with_iterator(self):
        def row_generator():
            for i in range(1, 6):
                yield [str(i), f'Book {i}']
        
        stream_ds = StreamingDataset(row_generator(), headers=['id', 'name'])
        
        result = self.resource.import_stream(stream_ds)
        
        self.assertEqual(5, result.total_rows)
        self.assertEqual(5, Book.objects.count())

    def test_import_stream_preserves_hooks(self):
        hook_calls = []
        
        class _BookResource(resources.ModelResource):
            def before_import(self, dataset, **kwargs):
                hook_calls.append('before_import')
                super().before_import(dataset, **kwargs)
            
            def before_import_row(self, row, **kwargs):
                hook_calls.append(f'before_import_row_{row.get("id")}')
                super().before_import_row(row, **kwargs)
            
            def after_import_row(self, row, row_result, **kwargs):
                hook_calls.append(f'after_import_row_{row.get("id")}')
                super().after_import_row(row, row_result, **kwargs)
            
            class Meta:
                model = Book
                use_bulk = True

        resource = _BookResource()
        
        csv_content = "id,name\n1,Book One\n2,Book Two\n"
        csv_file = io.StringIO(csv_content)
        stream_ds = StreamingDataset(csv_file, format='csv')
        
        result = resource.import_stream(stream_ds)
        
        self.assertIn('before_import', hook_calls)
        self.assertIn('before_import_row_1', hook_calls)
        self.assertIn('before_import_row_2', hook_calls)
        self.assertIn('after_import_row_1', hook_calls)
        self.assertIn('after_import_row_2', hook_calls)
        
        self.assertEqual(2, result.total_rows)

    def test_import_stream_error_handling(self):
        class _BookResource(resources.ModelResource):
            class Meta:
                model = Book
                use_bulk = True
                batch_size = 1000

        resource = _BookResource()
        
        csv_content = "id,name\n1,Book One\n2,Book Two\n"
        csv_file = io.StringIO(csv_content)
        stream_ds = StreamingDataset(csv_file, format='csv')
        
        with mock.patch("core.models.Book.objects.bulk_create") as mock_bulk:
            mock_bulk.side_effect = ValueError("test error")
            result = resource.import_stream(stream_ds, raise_errors=False)
            
            self.assertTrue(result.has_errors())

    def test_import_stream_raises_on_error(self):
        class _BookResource(resources.ModelResource):
            class Meta:
                model = Book
                use_bulk = True

        resource = _BookResource()
        
        csv_content = "id,name\n1,Book One\n"
        csv_file = io.StringIO(csv_content)
        stream_ds = StreamingDataset(csv_file, format='csv')
        
        with mock.patch("core.models.Book.objects.bulk_create") as mock_bulk:
            mock_bulk.side_effect = ValueError("test error")
            
            from import_export import exceptions
            with self.assertRaises(exceptions.ImportError):
                resource.import_stream(stream_ds, raise_errors=True)
