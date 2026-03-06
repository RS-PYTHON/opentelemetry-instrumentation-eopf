# -*- coding: utf-8 -*-
# Copyright 2023-2026 Airbus, CS Group
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Metrics module for eopf auto-instrumentation."""

import functools
import logging
from typing import Callable

from opentelemetry.metrics import Meter

logger = logging.getLogger("otel.eopf")


def safe_metrics_call(func: Callable) -> Callable:
    """Decorator to safely call metric functions without raising exceptions."""

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.debug(f"Metric call failed silently: {e}")

    return wrapper


def init_and_patch(meter: Meter) -> None:
    """Patch eopf for instrumentation."""
    pass


def remove_patches():
    """Unpatch the instrumented methods to restore original behavior."""
    pass
