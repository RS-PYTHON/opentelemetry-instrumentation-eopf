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

"""Unit tests for OpenTelemetry."""

from opentelemetry.instrumentation.eopf.init_opentelemetry import (
    botocore_hook,
    init_traces,
)


def test_botocore_hook(mocker):
    """Test botocore_hook() enriches a recording span with path."""

    span = mocker.Mock()
    span.is_recording.return_value = True
    api_params = {"Bucket": "my_bucket", "Key": "my_key"}

    botocore_hook(span, None, None, api_params)

    # The ASGI hook enriches the same span
    span.set_attribute.assert_any_call("_path", "s3://my_bucket/my_key")


def test_instrumentation(mocker, monkeypatch):
    """
    Call instrumentation code. It's only for the code coverage, don't run additional checks
    on the openlemetry internal code.
    """
    mocker.patch("opentelemetry.instrumentation.eopf.init_opentelemetry.initialized", False)
    monkeypatch.setenv("TEMPO_ENDPOINT", "none")

    mocker.patch("opentelemetry.instrumentation.eopf.init_opentelemetry.auto_instrumentation")
    mocker.patch("opentelemetry.instrumentation.fastapi.FastAPIInstrumentor.instrument_app")
    mocker.patch("opentelemetry.instrumentation.instrumentor.BaseInstrumentor.instrument")

    init_traces()
