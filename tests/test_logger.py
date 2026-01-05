# Copyright (C) 2025 - 2026 ANSYS, Inc. and/or its affiliates.
# SPDX-License-Identifier: MIT
#
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
"""Module for testing the logger."""

import logging

import pytest

from ansys.tools.common.logger import LOGGER, Logger
from ansys.tools.common.logger_formatter import DEFAULT_FORMATTER, PyAnsysBaseFormatter


def test_logger_singleton():
    """Test that Logger is a singleton."""
    another_instance = Logger(level=logging.INFO, logger_name="AnotherLogger")
    assert LOGGER is another_instance


def test_logger_name():
    """Test the name of the logger."""
    assert LOGGER.get_logger().name == "Logger"


def test_logger_level():
    """Test setting and getting the logger level."""
    LOGGER.set_level(logging.WARNING)
    assert LOGGER.get_logger().level == logging.WARNING


def test_logger_enable_output(capsys):
    """Test enabling logger output to a stream."""
    LOGGER.enable_output()
    LOGGER.set_level(logging.DEBUG)  # Set the logger to DEBUG level for testing
    LOGGER.info("Test message")
    captured = capsys.readouterr()
    assert "Test message" in captured.err


def test_logger_file_handler(tmp_path):
    """Test adding a file handler to the logger."""
    log_dir = tmp_path / "logs"
    LOGGER.add_file_handler(log_dir)
    LOGGER.set_level(logging.DEBUG)  # Set the logger to DEBUG level for testing
    LOGGER.info("Test message in file handler")
    log_file = next(log_dir.glob("log_*.log"))
    assert log_file.exists()
    with log_file.open() as f:
        content = f.read()
    assert "Timestamp" in content


def test_custom_formatter_truncation():
    """Test truncation of module and function names in PyAnsysBaseFormatter."""
    formatter = PyAnsysBaseFormatter("%(module).10s | %(funcName).10s")
    # assert formatter.max_column_width == 15  # Default width
    formatter.set_column_width(10)
    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname="test_path",
        lineno=1,
        msg="Test message",
        args=None,
        exc_info=None,
    )
    record.module = "very_long_module_name"
    record.funcName = "very_long_function_name"
    formatted_message = formatter.format(record)
    assert "very_long_ | very_long_" in formatted_message


def test_custom_formatter_column_width():
    """Test setting and getting column width in PyAnsysBaseFormatter."""
    formatter = PyAnsysBaseFormatter("%(module)s | %(funcName)s")
    formatter.set_column_width(12)
    assert formatter.max_column_width == 12

    with pytest.raises(ValueError):
        formatter.set_column_width(5)


def test_default_formatter():
    """Test the default formatter."""
    formatter = DEFAULT_FORMATTER
    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname="test_path",
        lineno=1,
        msg="Test message",
        args=None,
        exc_info=None,
    )
    record.module = "very_long_module_name"
    record.funcName = "very_long_function_name"
    assert "[INFO     | very_long_module_name | very_long_function_name:1   ] > Test message" in formatter.format(
        record
    )


def test_logger_debug(capsys):
    """Test the debug method."""
    LOGGER.enable_output()
    LOGGER.set_level(logging.DEBUG)  # Set the logger to DEBUG level for testing
    LOGGER.debug("Debug message")
    captured = capsys.readouterr()
    assert "DEBUG" in captured.err
    assert "Debug message" in captured.err


def test_logger_info(capsys):
    """Test the info method."""
    LOGGER.enable_output()
    LOGGER.set_level(logging.INFO)  # Set the logger to DEBUG level for testing
    LOGGER.info("Debug message")
    captured = capsys.readouterr()
    assert "INFO" in captured.err
    assert "Debug message" in captured.err


def test_logger_warn(capsys):
    """Test the warn method."""
    LOGGER.enable_output()
    LOGGER.set_level(logging.WARN)  # Set the logger to DEBUG level for testing
    LOGGER.warn("Debug message")
    captured = capsys.readouterr()
    assert "WARN" in captured.err
    assert "Debug message" in captured.err


def test_logger_warning(capsys):
    """Test the warning method."""
    LOGGER.enable_output()
    LOGGER.set_level(logging.WARNING)  # Set the logger to DEBUG level for testing
    LOGGER.warning("Debug message")
    captured = capsys.readouterr()
    assert "WARNING" in captured.err
    assert "Debug message" in captured.err


def test_logger_error(capsys):
    """Test the error method."""
    LOGGER.enable_output()
    LOGGER.set_level(logging.ERROR)  # Set the logger to DEBUG level for testing
    LOGGER.error("Debug message")
    captured = capsys.readouterr()
    assert "ERROR" in captured.err
    assert "Debug message" in captured.err


def test_logger_critical(capsys):
    """Test the critical method."""
    LOGGER.enable_output()
    LOGGER.set_level(logging.CRITICAL)  # Set the logger to DEBUG level for testing
    LOGGER.critical("Debug message")
    captured = capsys.readouterr()
    assert "CRITICAL" in captured.err
    assert "Debug message" in captured.err


def test_logger_fatal(capsys):
    """Test the fatal method."""
    LOGGER.enable_output()
    LOGGER.set_level(logging.FATAL)  # Set the logger to DEBUG level for testing
    LOGGER.fatal("Debug message")
    captured = capsys.readouterr()
    assert "CRITICAL" in captured.err
    assert "Debug message" in captured.err


def test_logger_log(capsys):
    """Test the fatal method."""
    LOGGER.enable_output()
    LOGGER.set_level(logging.FATAL)  # Set the logger to DEBUG level for testing
    LOGGER.log(logging.FATAL, "Debug message")
    captured = capsys.readouterr()
    assert "CRITICAL" in captured.err
    assert "Debug message" in captured.err
