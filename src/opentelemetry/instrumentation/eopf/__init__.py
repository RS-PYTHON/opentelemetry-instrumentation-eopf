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
from opentelemetry.instrumentation.utils import is_instrumentation_enabled
from opentelemetry.metrics import get_meter
from opentelemetry.trace import SpanKind, Status, StatusCode, get_tracer
from typing_extensions import override
from wrapt import wrap_function_wrapper

from eopf.computing import EOProcessingUnit
from eopf.triggering.runner import EORunner
from eopf.triggering.workflow import EOProcessorWorkFlow
from opentelemetry.instrumentation.eopf.package import _instruments

_EOPF_INSTRUMENTED_ATTR = "_eopf_instrumented"


class EopfInstrumentor(BaseInstrumentor):
    """An instrumentor for eopf."""

    def __init__(self):
        self._original_eopu_init_subclass = EOProcessingUnit.__init_subclass__
        self._tracer = None
        self._meter = None

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
        self._tracer = get_tracer(__name__, tracer_provider=tracer_provider)
        self._add_tracing_patches()

        meter_provider = kwargs.get("meter_provider")
        self._meter = get_meter(__name__, meter_provider=meter_provider)
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

    def _hydrate_span_from_args(self, func, instance, args, kwargs) -> dict[str, Any]:
        span_attrs = {}

        if isinstance(instance, EORunner):
            if func.__name__ == "run":
                self._set_span_attr_from_arg(span_attrs, self._get_arg(args, kwargs, 0, "payload"), "eopf.payload")

            self._set_span_attr_from_attr(instance, span_attrs, "_payload_dir", "eopf.payload_dir")
            self._set_span_attr_from_attr(instance, span_attrs, "_working_dir", "eopf.working_dir")

        elif isinstance(instance, EOProcessorWorkFlow):
            if func.__name__ == "open_input_products":
                self._set_span_attr_from_arg(
                    span_attrs, self._get_arg(args, kwargs, 0, "inputs_io_products"), "eopf.inputs_io_products"
                )
            elif func.__name__ == "run_workflow":
                self._set_span_attr_from_arg(span_attrs, self._get_arg(args, kwargs, 0, "io_config"), "eopf.io_config")
                self._set_span_attr_from_arg(
                    span_attrs, self._get_arg(args, kwargs, 1, "dask_context"), "eopf.dask_context"
                )
                self._set_span_attr_from_arg(span_attrs, self._get_arg(args, kwargs, 2, "eoqc"), "eopf.eoqc")

            self._set_span_attr_from_attr(instance, span_attrs, "_requested_io_outputs", "eopf.requested_io_outputs")
            self._set_span_attr_from_attr(instance, span_attrs, "_requested_io_inputs", "eopf.requested_io_inputs")
            self._set_span_attr_from_attr(instance, span_attrs, "_requested_io_adfs", "eopf.requested_io_adfs")

        elif isinstance(instance, EOProcessingUnit):
            if func.__name__ in ("run", "run_validating"):
                self._set_span_attr_from_arg(span_attrs, self._get_arg(args, kwargs, 0, "inputs"), "eopf.inputs")
                self._set_span_attr_from_arg(span_attrs, self._get_arg(args, kwargs, 1, "adfs"), "eopf.adfs")

        return span_attrs

    def _get_arg(self, args, kwargs, index, name):
        if len(args) > index:
            return args[index]
        return kwargs.get(name)

    def _do_execute(self, wrapped, instance, args, kwargs):
        if not is_instrumentation_enabled():
            return wrapped(*args, **kwargs)

        exception = None
        span_name = f"{instance.__class__.__name__}.{wrapped.__name__}"
        with self._tracer.start_as_current_span(span_name, kind=SpanKind.INTERNAL) as span:
            if span.is_recording():
                span.set_attributes(self._hydrate_span_from_args(wrapped, instance, args, kwargs))
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

    def _all_subclasses(self, cls):
        for subclass in cls.__subclasses__():
            yield subclass
            yield from self._all_subclasses(subclass)

    def _wrap_function_wrapper_if_exists(self, cls, func_name: str):
        # Wrap function only if it exists and not already wrapped by us
        func = getattr(cls, func_name, None)
        if func and not self._is_already_instrumented(func):
            wrap_function_wrapper(cls, func_name, self._do_execute)
            setattr(getattr(cls, func_name), _EOPF_INSTRUMENTED_ATTR, True)

    def _is_already_instrumented(self, func):
        # Recursive check to see if the function has already been instrumented by us
        current = func
        while current:
            if getattr(current, _EOPF_INSTRUMENTED_ATTR, False):
                return True
            current = self._get_wrapped_function(current)
        return False

    def _safe_unwrap(self, cls, method_name: str):
        # Recursive walk to remove safely our wrapper, and not one from another library
        func = getattr(cls, method_name, None)
        if not func:
            return

        prev = None
        current = func

        while current:
            if getattr(current, _EOPF_INSTRUMENTED_ATTR, False):
                wrapped = self._get_wrapped_function(current)
                if wrapped:
                    if prev is None:
                        setattr(cls, method_name, wrapped)
                    elif hasattr(prev, "_self_wrapper"):
                        prev._self_wrapper = wrapped
                    else:
                        prev.__wrapped__ = wrapped
                    return

            prev = current
            current = self._get_wrapped_function(current)

    def _get_wrapped_function(self, func) -> Any | None:
        return getattr(func, "__wrapped__", getattr(func, "_self_wrapper", None))

    def _instrument_processing_unit(self, cls):
        # Instrument interesting methods from an EOProcessingUnit subclass
        for method in ("run", "run_validating"):
            self._wrap_function_wrapper_if_exists(cls, method)

    def _instrument_future_processing_units(self):
        original_init_subclass = self._original_eopu_init_subclass
        instrument_processing_unit = self._instrument_processing_unit

        def patched_init_subclass(cls, **kwargs):
            original_init_subclass(**kwargs)
            instrument_processing_unit(cls)

        EOProcessingUnit.__init_subclass__ = classmethod(patched_init_subclass)

    def _add_tracing_patches(self):
        # Instrument EOProcessingUnit subclasses loaded afterwards
        self._instrument_future_processing_units()
        # Instrument EOProcessingUnit subclasses already loaded
        for processing_unit_cls in self._all_subclasses(EOProcessingUnit):
            self._instrument_processing_unit(processing_unit_cls)
        # Instrument other classes
        self._wrap_function_wrapper_if_exists(EOProcessorWorkFlow, "open_input_products")
        self._wrap_function_wrapper_if_exists(EOProcessorWorkFlow, "run_workflow")
        self._wrap_function_wrapper_if_exists(EORunner, "run")

    def _remove_tracing_patches(self):
        # Make sure we don't instrument new EOProcessingUnit subclasses
        EOProcessingUnit.__init_subclass__ = self._original_eopu_init_subclass
        # Uninstrument loaded EOProcessingUnit subclasses
        for processing_unit_cls in self._all_subclasses(EOProcessingUnit):
            self._safe_unwrap(processing_unit_cls, "run")
            self._safe_unwrap(processing_unit_cls, "run_validating")
        # Uninstrument other classes
        self._safe_unwrap(EOProcessorWorkFlow, "open_input_products")
        self._safe_unwrap(EOProcessorWorkFlow, "run_workflow")
        self._safe_unwrap(EORunner, "run")

    def _add_metrics_patches(self):
        pass

    def _remove_metrics_patches(self):
        pass
