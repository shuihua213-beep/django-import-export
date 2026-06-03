class Widget:
    """
    A Widget takes care of converting between import and export representations.

    This is achieved by the two methods,
    :meth:`~import_export.widgets.Widget.clean` and
    :meth:`~import_export.widgets.Widget.render`.
    """

    def clean(self, value, row=None, *args, **kwargs):
        """
        Returns an appropriate Python object for an imported value.

        For example, if you import a value from a spreadsheet,
        :meth:`~import_export.widgets.Widget.clean` handles conversion
        of this value into the corresponding Python object.

        Numbers or dates can be *cleaned* to their respective data types and
        don't have to be imported as Strings.
        """
        return value

    def render(self, value, obj=None, *args, **kwargs):
        """
        Returns an export representation of a Python value.

        For example, if you have an object you want to export,
        :meth:`~import_export.widgets.Widget.render` takes care of converting
        the object's field to a value that can be written to a spreadsheet.
        """
        return value
