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

# pylint: disable=no-name-in-module

import os

from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.botocore import (
    AiobotocoreInstrumentor,
    BotocoreInstrumentor,
)
from opentelemetry.sdk.resources import Resource  # type: ignore
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

from opentelemetry import trace
from opentelemetry.instrumentation import auto_instrumentation

initialized = False


def botocore_request_hook(span, _service_name, _operation_name, api_params: dict):
    """Callback function invoked by BotocoreInstrumentor and AiobotocoreInstrumentor"""
    bucket = api_params.get("Bucket", "")
    key = api_params.get("Key", "")
    span.set_attribute("_path", f"s3://{bucket}/{key}")


def init_traces(service_name: str):
    """
    Init instrumentation of OpenTelemetry traces.

    Args:
        service_name (str): service name
    """
    global initialized
    if initialized:
        return
    initialized = True

    tempo_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "")

    otel_resource = Resource(attributes={"service.name": service_name})
    otel_tracer = TracerProvider(resource=otel_resource)
    otel_tracer.add_span_processor(BatchSpanProcessor(OTLPSpanExporter(endpoint=tempo_endpoint)))

    # Use this tracer everywhere in opentelemetry
    trace.set_tracer_provider(otel_tracer)

    #
    # Specific opentelemetry instrumentation with custom hooks
    #

    BotocoreInstrumentor().instrument(tracer_provider=otel_tracer, request_hook=botocore_request_hook)
    AiobotocoreInstrumentor().instrument(tracer_provider=otel_tracer, request_hook=botocore_request_hook)

    # Instrument all other dependencies under opentelemetry.instrumentation.*
    # NOTE 1: we need 'poetry run opentelemetry-bootstrap -a install' to install these.
    # NOTE 2: we have warnings 'Overriding of current TracerProvider is not allowed' and
    # 'Attempting to instrument while already instrumented' because we already did some specific
    # instrumentations above, but we can ignore these warnings.
    auto_instrumentation.initialize()
