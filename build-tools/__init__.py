"""
Build the three search tools step by step.

Run the step*.py files in order to see how each tool works.
"""

from .step1_list_files import list_files
from .step2_grep import grep
from .step3_read_file import read_file

__all__ = ["list_files", "grep", "read_file"]