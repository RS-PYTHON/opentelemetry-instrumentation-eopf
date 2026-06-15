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

"""OpenTelemetry utility"""

import os
from threading import Lock

from opentelemetry.instrumentation.botocore import (
    AiobotocoreInstrumentor,
    BotocoreInstrumentor,
)

from opentelemetry.instrumentation import auto_instrumentation

lock = Lock()
INITIALIZED = False


def botocore_hook(span, _service_name, _operation_name, api_params: dict):
    """Callback function invoked by BotocoreInstrumentor and AiobotocoreInstrumentor"""
    if not (span and span.is_recording()):
        return
    bucket = api_params.get("Bucket", "")
    key = api_params.get("Key", "")
    span.set_attribute("_path", f"s3://{bucket}/{key}")


def init_traces():
    """
    Init instrumentation of OpenTelemetry traces.

    NOTE: the OTEL_SERVICE_NAME and OTEL_EXPORTER_OTLP_ENDPOINT must be set by the caller.
    """
    with lock:
        global INITIALIZED  # pylint: disable=global-statement
        if INITIALIZED:
            return
        INITIALIZED = True

    # We'll use custom instrumentation for these packages (separated by ,)
    org_disabled = os.getenv("OTEL_PYTHON_DISABLED_INSTRUMENTATIONS", "")
    os.environ["OTEL_PYTHON_DISABLED_INSTRUMENTATIONS"] = f"{org_disabled},aiobotocore,botocore"

    # Run the opentelemetry auto instrumentation on all packages under opentelemetry.instrumentation.*
    # This is what the command line "opentelemetry-instrumentation" would do.
    # NOTE: we need 'poetry run opentelemetry-bootstrap -a install' to install these packages.
    try:
        auto_instrumentation.initialize()
    finally:
        os.environ["OTEL_PYTHON_DISABLED_INSTRUMENTATIONS"] = org_disabled

    #
    # Specific opentelemetry instrumentation with custom hooks
    #

    AiobotocoreInstrumentor().instrument(request_hook=botocore_hook)
    BotocoreInstrumentor().instrument(request_hook=botocore_hook)
