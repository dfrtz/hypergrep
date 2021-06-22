"""Test cases for the pyhypergrep module."""

import ctypes
import os
import pytest
import sys

from typing import Any
from typing import Callable

from pyhypergrep import hyperscanner
from pyhypergrep.common import hyper_utils


def _dummy_callback(line_index: int, match_id: int, line_ptr: ctypes.c_char_p) -> None:
    """Callback for C library to send results."""
    line = line_ptr.decode(errors='ignore')
    print(f'{line_index}:{line.rstrip()}')


TEST_FILE = os.path.join(os.path.dirname(__file__), 'dummyfile.txt')
TEST_CASES = {
    'hyperscan': {
        'one pattern': {
            'args': [
                TEST_FILE,
                ['bar'],
                _dummy_callback,
            ],
            'expected': [
                '1:foobar',
                '2:barfoo',
            ]
        },
        'two patterns': {
            'args': [
                TEST_FILE,
                [
                    'bar',
                    'food',
                ],
                _dummy_callback,
            ],
            'expected': [
                '1:foobar',
                '2:barfoo',
                '3:food',
            ]
        },
    },
    'grep': {
        'one pattern, no index': {
            'args': [
                TEST_FILE,
                'bar',
                False,
                False,
            ],
            'expected': [
                'foobar',
                'barfoo'
            ]
        },
        'one pattern, with index': {
            'args': [
                TEST_FILE,
                'bar',
                False,
                True,
            ],
            'expected': [
                (2, 'foobar'),
                (3, 'barfoo'),
            ]
        },
    },
}


def run_basic_test_case(test_case: dict, context: Callable, comparator: Callable = None) -> None:
    """Run a basic test_case configuration against the given context.

    Args:
        test_case: A dictionary containing configuration parameters for testing a callable.
        context: A callable to pass args and kwargs that will return value to compare.
        comparator: A function to use for comparing the expected_results and result.
            Defaults to doing a direct "==" comparison.

    Example:
        test_case (test raising an error) = {'raises': ValueError, 'kwargs': {'value': None}}
        test_case (test getting expected result) = {'expected': 10, 'args': [5, 12]}
    """
    args = test_case.get('args', [])
    kwargs = test_case.get('kwargs', {})
    raises = test_case.get('raises')
    if raises:
        with pytest.raises(raises):
            context(*args, **kwargs)
    else:
        expected = test_case.get('expected')
        result = context(*args, **kwargs)
        message = f'Got an unexpected result.\n\nExpected: {expected}\n\nActual: {result}'
        if comparator:
            comparator(result, expected)
        else:
            assert result == expected, message


@pytest.mark.parametrize(
    'test_case',
    list(TEST_CASES['grep'].values()),
    ids=list(TEST_CASES['grep'].keys()),
)
@pytest.mark.skipif(
    sys.platform != 'linux',
    reason='Hyperscan libraries only support Linux',
)
def test_grep(test_case: dict) -> None:
    """Tests for grep function."""
    run_basic_test_case(test_case, hyperscanner.grep)


@pytest.mark.parametrize(
    'test_case',
    list(TEST_CASES['hyperscan'].values()),
    ids=list(TEST_CASES['hyperscan'].keys()),
)
@pytest.mark.skipif(
    sys.platform != 'linux',
    reason='Hyperscan libraries only support Linux',
)
def test_hyperscan(test_case: dict, capsys: Any) -> None:
    """Tests for hyperscan function."""
    def _grep_helper(*args, **kwargs) -> list:
        """Helper to run hyperscan and capture output for comparisons."""
        hyper_utils.hyperscan(*args, **kwargs)
        capture = capsys.readouterr()
        stdout = capture.out.splitlines()
        return stdout
    run_basic_test_case(test_case, _grep_helper)
