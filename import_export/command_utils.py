from django.apps import apps
from django.core.management.base import CommandError
from django.http.response import mimetypes
from django.utils.module_loading import import_string

from import_export.formats.base_formats import get_default_formats
from import_export.resources import modelresource_factory


def get_resource_class(model_or_resource_class_name):
    try:
        model = apps.get_model(model_or_resource_class_name)
        return modelresource_factory(model)
    except (LookupError, ValueError):
        try:
            class_name = model_or_resource_class_name
            return import_string(class_name)
        except ImportError:
            raise CommandError(
                f"Cannot import '{model_or_resource_class_name}' as a resource class or model."
            )


def get_mime_type_format_mapping():
    return {
        format_class().get_content_type(): format_class
        for format_class in get_default_formats()
    }


def get_format_class(format_name, file_name, encoding=None):
    if format_name:
        try:
            format_class = import_string(format_name)
        except ImportError:
            fallback_format_name = f"import_export.formats.base_formats.{format_name}"
            try:
                format_class = import_string(fallback_format_name)
            except ImportError:
                try:
                    format_class = import_string(
                        f"import_export.formats.base_formats.{format_name.upper()}"
                    )
                except ImportError:
                    raise CommandError(
                        f"Cannot import '{format_name}' or '{fallback_format_name}'"
                        " format class."
                    )
        return format_class(encoding=encoding)

    mimetype, file_encoding = mimetypes.guess_type(file_name)

    if not mimetype:
        raise CommandError(
            f"Cannot determine MIME type for '{file_name}'. "
            " Please specify format with --format."
        )

    try:
        format_class = get_mime_type_format_mapping()[mimetype]
        return format_class(encoding=encoding or file_encoding)
    except KeyError:
        raise CommandError(
            f"Cannot find format for MIME type '{mimetype}'."
            " Please specify format with --format."
        )


def get_default_format_names():
    return ", ".join([f.__name__ for f in get_default_formats()])
