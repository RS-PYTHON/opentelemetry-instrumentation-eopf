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
"""OpenTelemetry wrapper of eopf CLI."""

import json
import os

from opentelemetry.trace.propagation import SPAN_KEY
from opentelemetry.trace.span import SpanContext
from rs_dpr_service.utils.init_opentelemetry import init_traces, start_span

from eopf.cli.cli import eopf_cli
from opentelemetry import propagate


def restore_context_from_env() -> SpanContext | None:
    """Return an OpenTelemetry span context propagated through environment variables.

    This function reads the ``OTEL_TRACE_CONTEXT`` environment variable,
    which is expected to contain a JSON-encoded carrier produced by
    ``opentelemetry.propagate.inject`` in a parent process. The context
    is extracted and returned by this function so that
    spans created in this process continue the existing trace.
    """
    carrier_json = os.environ.get("OTEL_TRACE_CONTEXT")
    try:
        # The json should contain a context
        extracted_context = propagate.extract(json.loads(carrier_json))

        # The context should contain a key starting by SPAN_KEY
        span_value = [value for key, value in extracted_context.items() if key.startswith(SPAN_KEY)][0]

        # This value should be a NonRecordingSpan object, that contains a SpanContext
        return span_value.get_span_context()
    except Exception:
        return


def main():
    """Entry point for the ``eopf_otel`` CLI wrapper.

    This wrapper restores a propagated OpenTelemetry trace context
    before invoking the original ``eopf`` Click CLI. It allows
    subprocess executions of ``eopf`` to continue the trace started
    in the parent process when used together with
    ``opentelemetry-instrument``.
    """
    # Should be dpr.<processor_name>
    span_name = os.environ.get("EOPF_SPAN_NAME", "eopf_otel")

    # Init opentelemetry
    init_traces(None, span_name)

    # Call eopf command line from an opentelemetry span
    with start_span(__name__, span_name, span_context=restore_context_from_env()):
        eopf_cli()


if __name__ == "__main__":
    main()
