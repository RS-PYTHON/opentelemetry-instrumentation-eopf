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

from typing import Any, Collection

from opentelemetry.instrumentation.instrumentor import BaseInstrumentor
from opentelemetry.instrumentation.utils import (
    is_instrumentation_enabled,
    unwrap,
)
from opentelemetry.metrics import get_meter
from opentelemetry.trace import SpanKind, Status, StatusCode, get_tracer
from typing_extensions import override
from wrapt import wrap_function_wrapper

from eopf.computing import EOProcessingUnit
from eopf.triggering.runner import EORunner
from eopf.triggering.workflow import EOProcessorWorkFlow
from opentelemetry.instrumentation.eopf.package import _instruments


class EopfInstrumentor(BaseInstrumentor):
    """An instrumentor for eopf."""

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
        self._tracer = get_tracer(__name__, tracer_provider=tracer_provider)  # pylint: disable=W0201
        self._add_tracing_patches()

        meter_provider = kwargs.get("meter_provider")
        self._meter = get_meter(__name__, meter_provider=meter_provider)  # pylint: disable=W0201
        self._add_metrics_patches()

    @override
    def _uninstrument(self, **kwargs) -> None:
        """Uninstrument the library.

        This only works if no other module also patches eopf.
        """
        self._remove_tracing_patches()
        self._remove_metrics_patches()

    @staticmethod
    def _set_span_attr_from_arg(span_attrs: dict, arg: Any, span_attr_name: str):
        if arg is not None:
            span_attrs[span_attr_name] = str(arg)

    @staticmethod
    def _set_span_attr_from_attr(instance, span_attrs: dict, attr_name: str, span_attr_name: str):
        value = getattr(instance, attr_name, None)
        if value is not None:
            span_attrs[span_attr_name] = value

    def _hydrate_span_from_args(self, func, instance, args) -> dict[str, Any]:
        span_attributes = {}

        if isinstance(instance, EORunner):
            if func.__name__ == "run":
                self._set_span_attr_from_arg(span_attributes, args[0], "eopf.payload")

            self._set_span_attr_from_attr(instance, span_attributes, "_payload_dir", "eopf.payload_dir")
            self._set_span_attr_from_attr(instance, span_attributes, "_working_dir", "eopf.working_dir")

        elif isinstance(instance, EOProcessorWorkFlow):
            if func.__name__ == "open_input_products":
                self._set_span_attr_from_arg(span_attributes, args[0], "eopf.inputs_io_products")
            elif func.__name__ == "run_workflow":
                self._set_span_attr_from_arg(span_attributes, args[0], "eopf.io_config")
                self._set_span_attr_from_arg(span_attributes, args[1], "eopf.dask_context")
                self._set_span_attr_from_arg(span_attributes, args[2], "eopf.eoqc")

            self._set_span_attr_from_attr(
                instance, span_attributes, "_requested_io_outputs", "eopf.requested_io_outputs"
            )
            self._set_span_attr_from_attr(instance, span_attributes, "_requested_io_inputs", "eopf.requested_io_inputs")
            self._set_span_attr_from_attr(instance, span_attributes, "_requested_io_adfs", "eopf.requested_io_adfs")

        elif isinstance(instance, EOProcessingUnit):
            if func.__name__ in ("run", "run_validating"):
                self._set_span_attr_from_arg(span_attributes, args[0], "eopf.inputs")
                self._set_span_attr_from_arg(span_attributes, args[1], "eopf.adfs")
                self._set_span_attr_from_arg(span_attributes, args[2], "eopf.mode")

        return span_attributes

    def _do_execute(self, wrapped, instance, args, kwargs):
        if not is_instrumentation_enabled():
            return wrapped(*args, **kwargs)

        exception = None

        with self._tracer.start_as_current_span(wrapped.__qualname__, kind=SpanKind.INTERNAL) as span:
            if span.is_recording():
                span.set_attributes(self._hydrate_span_from_args(wrapped, instance, args))
            try:
                result = wrapped(*args, **kwargs)
            except Exception as exc:  # pylint: disable=W0703
                exception = exc
                raise
            finally:
                if span.is_recording() and exception is not None:
                    span.record_exception(exception)
                    span.set_status(Status(StatusCode.ERROR, str(exception)))

        return result

    def _add_tracing_patches(self):
        wrap_function_wrapper(EOProcessingUnit, "run", self._do_execute)
        wrap_function_wrapper(EOProcessingUnit, "run_validating", self._do_execute)
        wrap_function_wrapper(EOProcessorWorkFlow, "open_input_products", self._do_execute)
        wrap_function_wrapper(EOProcessorWorkFlow, "run_workflow", self._do_execute)
        wrap_function_wrapper(EORunner, "run", self._do_execute)

    def _remove_tracing_patches(self):
        unwrap(EOProcessingUnit, "run")
        unwrap(EOProcessingUnit, "run_validating")
        unwrap(EOProcessorWorkFlow, "open_input_products")
        unwrap(EOProcessorWorkFlow, "run_workflow")
        unwrap(EORunner, "run")

    def _add_metrics_patches(self):
        pass

    def _remove_metrics_patches(self):
        pass
