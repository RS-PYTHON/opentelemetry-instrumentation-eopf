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
"""Tracing module for eopf auto-instrumentation."""

import functools

from opentelemetry.trace import SpanKind, Status, StatusCode, Tracer


def traced_method(tracer: Tracer, span_name: str):
    """Decorator to trace a method with OpenTelemetry."""

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            with tracer.start_as_current_span(span_name, kind=SpanKind.INTERNAL) as span:
                if span.is_recording():
                    # Add all kwargs as attributes
                    for k, v in kwargs.items():
                        if isinstance(v, (str, int, float, bool)):
                            span.set_attribute(f"kwarg.{k}", v)
                        else:
                            span.set_attribute(f"kwarg.{k}", f"<{type(v).__name__}>")
                try:
                    result = func(*args, **kwargs)
                    if span.is_recording():
                        span.set_status(Status(StatusCode.OK))
                    return result
                except Exception as exc:
                    if span.is_recording():
                        span.set_status(Status(StatusCode.ERROR, str(exc)))
                        span.record_exception(exc)
                    raise

        return wrapper

    return decorator


def patch_eopf(tracer: Tracer):
    """Patch for tracing."""
    pass


def remove_patches():
    """Restore if patched."""
    pass
