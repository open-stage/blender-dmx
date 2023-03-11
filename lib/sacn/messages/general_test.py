# This file is under MIT license. The license file can be obtained in the root directory of this module.

import pytest


def property_number_range_check(lower_bound: int, upper_bound: int, *functions):
    for function in functions:
        for i in range(lower_bound, upper_bound + 1):
            function(i)
        with pytest.raises(ValueError):
            function(lower_bound - 1)
        with pytest.raises(ValueError):
            function(upper_bound + 1)
        with pytest.raises(TypeError):
            function('Text')
