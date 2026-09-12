import sys
import os
sys.path.append(os.path.abspath("."))
from app.utils.snippet import _get_parsed_ast

print(_get_parsed_ast("app/models.py", os.path.getmtime("app/models.py")))
