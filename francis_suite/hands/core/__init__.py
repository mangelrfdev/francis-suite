"""
hands/core/__init__.py

Importing this module registers all built-in hands
into the HandRegistry automatically.
"""

from francis_suite.hands.core import log
from francis_suite.hands.core import box_def
from francis_suite.hands.core import sleep
from francis_suite.hands.core import empty
from francis_suite.hands.core import httpx_call
from francis_suite.hands.core import convert_html_to_xml
from francis_suite.hands.core import xpath_extract
from francis_suite.hands.core import loop
from francis_suite.hands.core import loop_list
from francis_suite.hands.core import loop_body
from francis_suite.hands.core import case_
from francis_suite.hands.core import if_
from francis_suite.hands.core import else_
from francis_suite.hands.core import box
from francis_suite.hands.core import box_def
from francis_suite.hands.core import while_
from francis_suite.hands.core import try_
from francis_suite.hands.core import catch_
from francis_suite.hands.core import function_create
from francis_suite.hands.core import function_call
from francis_suite.hands.core import function_param
from francis_suite.hands.core import function_return
from francis_suite.hands.core import regex
from francis_suite.hands.core import regex_pattern
from francis_suite.hands.core import regex_input
from francis_suite.hands.core import regex_result
from francis_suite.hands.core import text_format
from francis_suite.hands.core import text_split
from francis_suite.hands.core import evaluate
from francis_suite.hands.core import exit_
from francis_suite.hands.core import build_list
from francis_suite.hands.core import call_workflow
from francis_suite.hands.core import convert_json_to_xml
from francis_suite.hands.core import convert_xml_to_json
from francis_suite.hands.core import file_read
from francis_suite.hands.core import file_write
from francis_suite.hands.core import file_download
from francis_suite.hands.core import file_upload
from francis_suite.hands.core import file_manage