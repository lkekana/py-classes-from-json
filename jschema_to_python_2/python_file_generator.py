import os

from jschema_to_python_2 import __version__


class PythonFileGenerator(object):
    def __init__(self, output_directory):
        self.output_directory = output_directory

    def write_generation_comment(self):
        print(
            "# This file was generated by "
            + __package__
            + " - lkekana version.\n"
        )

    def make_output_file_path(self, file_name):
        return os.path.join(self.output_directory, file_name)
