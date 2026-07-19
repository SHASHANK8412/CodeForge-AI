import pytest
from backend.review.test_parser import TestParser


def test_test_parser_extracts_failures():
    parser = TestParser()

    pytest_log = """
============================= test session starts =============================
collected 1 item

tests/test_login.py::test_login FAILED                                   [100%]

=================================== FAILURES ===================================
__________________________________ test_login __________________________________
def test_login():
>       assert '200' == '401'
E       AssertionError: assert '200' == '401'

tests/test_login.py:12: AssertionError
=========================== short test summary info ===========================
FAILED tests/test_login.py::test_login - AssertionError: assert '200' == '401'
========================= 1 failed in 0.12s =========================
"""

    result = parser.parse_pytest_output(pytest_log)

    assert result["failed"] == 1
    assert len(result["failures_list"]) == 1

    failure = result["failures_list"][0]
    assert failure["file"] == "tests/test_login.py"
    assert failure["test"] == "test_login"
    assert failure["expected"] == "200"
    assert failure["received"] == "401"
