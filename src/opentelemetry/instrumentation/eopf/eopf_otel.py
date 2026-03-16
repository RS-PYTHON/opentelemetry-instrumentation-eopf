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

from eopf.cli.cli import eopf_cli
from opentelemetry import context, propagate


def restore_context_from_env():
    """Restore an OpenTelemetry context propagated through environment variables.

    This function reads the ``OTEL_TRACE_CONTEXT`` environment variable,
    which is expected to contain a JSON-encoded carrier produced by
    ``opentelemetry.propagate.inject`` in a parent process. The context
    is extracted and attached to the current execution context so that
    spans created in this process continue the existing trace.
    """
    carrier_json = os.environ.get("OTEL_TRACE_CONTEXT")
    if not carrier_json:
        return
    context.attach(propagate.extract(json.loads(carrier_json)))


def main():
    """Entry point for the ``eopf_otel`` CLI wrapper.

    This wrapper restores a propagated OpenTelemetry trace context
    before invoking the original ``eopf`` Click CLI. It allows
    subprocess executions of ``eopf`` to continue the trace started
    in the parent process when used together with
    ``opentelemetry-instrument``.
    """
    restore_context_from_env()
    eopf_cli()


if __name__ == "__main__":
    main()
