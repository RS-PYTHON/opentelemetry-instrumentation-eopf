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
"""OpenTelemetry auto-instrumentation for eopf."""

from typing import Collection
from typing_extensions import override

from opentelemetry.instrumentation.instrumentor import BaseInstrumentor
from opentelemetry.metrics import get_meter
from opentelemetry.trace import get_tracer

from opentelemetry.instrumentation.eopf import metrics, tracing
from opentelemetry.instrumentation.eopf.package import _instruments


class eopfInstrumentor(BaseInstrumentor):
    """An instrumentor for eopf."""

    def __init__(self) -> None:
        """Init the instrumentor for eopf."""
        super().__init__()

    @override
    def instrumentation_dependencies(self) -> Collection[str]:
        """Return a list of python packages with versions that the will be instrumented.

        :returns: The list of instrumented python packages.
        :rtype: Collection[str]
        """
        return _instruments

    @override
    def _instrument(self, **kwargs) -> None:
        """Instruments eopf."""
        tracer_provider = kwargs.get("tracer_provider")
        tracer = get_tracer(__name__, tracer_provider=tracer_provider)

        tracing.patch_eopf(tracer)

        meter_provider = kwargs.get("meter_provider")
        meter = get_meter(__name__, meter_provider=meter_provider)

        metrics.init_and_patch(meter)

    @override
    def _uninstrument(self, **kwargs) -> None:
        """Uninstrument the library.

        This only works if no other module also patches eopf.
        """
        metrics.remove_patches()
        tracing.remove_patches()
