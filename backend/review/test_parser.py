import re
import logging

_logger = logging.getLogger("aiforge.performance")


class TestParser:
    """
    Parses raw pytest text stdout into a structured representation of test status and failures.
    """
    __test__ = False

    def __init__(self) -> None:
        pass

    def parse_pytest_output(self, raw_output: str) -> dict:
        """
        Parses the stdout content from a pytest execution.
        """
        _logger.info("INFO Parsing pytest failures output...")
        
        result = {
            "passed": 0,
            "failed": 0,
            "errors": 0,
            "failures_list": []
        }

        # 1. Parse Summary counts (e.g. "45 passed, 3 warnings in 44.72s", "1 failed, 47 passed")
        summary_match = re.search(r"===+ (.*) in \d+\.\d+s ===+", raw_output)
        if not summary_match:
            # Try a broader check at the end of output
            summary_match = re.search(r"===+\s*([\w\s,]+)\s*===+\s*$", raw_output)

        if summary_match:
            summary_text = summary_match.group(1).lower()
            
            passed_match = re.search(r"(\d+)\s+passed", summary_text)
            if passed_match:
                result["passed"] = int(passed_match.group(1))

            failed_match = re.search(r"(\d+)\s+failed", summary_text)
            if failed_match:
                result["failed"] = int(failed_match.group(1))

            error_match = re.search(r"(\d+)\s+error", summary_text)
            if error_match:
                result["errors"] = int(error_match.group(1))

        # 2. Extract Failures and Errors
        # 2. Extract Failures and Errors
        # Separate the output into failure sections using regex headers
        pattern = r"\n_{5,}\s*([\w\.\s\-\/\[\]\:]+)\s*_{5,}\n"
        matches = list(re.finditer(pattern, raw_output))

        for i, match in enumerate(matches):
            test_info = match.group(1).strip()
            test_name = test_info.split(" ")[0]

            # Start and end of the traceback content for this failure
            start_pos = match.end()
            end_pos = matches[i + 1].start() if i + 1 < len(matches) else len(raw_output)

            section = raw_output[start_pos:end_pos]

            traceback_lines = []
            expected_val = ""
            received_val = ""

            lines = section.splitlines()
            for line in lines:
                assert_match = re.search(r"assert\s+['\"]?([^'\"\s\=\>\!]+)['\"]?\s*(?:==|in)\s*['\"]?([^'\"\s\=\>\!]+)['\"]?", line)
                if assert_match:
                    expected_val = assert_match.group(1)
                    received_val = assert_match.group(2)

                if line.startswith("E   ") or line.strip().startswith("Traceback") or "line" in line or "AssertionError" in line:
                    traceback_lines.append(line)

            traceback_content = "\n".join(traceback_lines)

            # Try to resolve file path from the section header or traceback lines
            file_path = "unknown_test_file.py"
            file_match = re.search(r"tests/[a-zA-Z0-9_\.]+", section)
            if file_match:
                file_path = file_match.group(0)
            elif "tests/" in test_info:
                file_path = test_info.split(" ")[-1]

            result["failures_list"].append({
                "test": test_name,
                "file": file_path,
                "expected": expected_val or "True",
                "received": received_val or "False",
                "traceback": traceback_content or section
            })

        # Fallback if counts are zero but failures list has entries
        if len(result["failures_list"]) > 0 and result["failed"] == 0:
            result["failed"] = len(result["failures_list"])

        _logger.info(f"INFO Parsed {result['failed']} failures and {result['passed']} passes")
        return result
