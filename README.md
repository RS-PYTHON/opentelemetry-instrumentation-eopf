# opentelemetry-instrumentation-eopf

[![PyPI version](https://badge.fury.io/py/opentelemetry-instrumentation-eopf.svg)](https://pypi.org/project/opentelemetry-instrumentation-eopf)

OpenTelemetry [Instrumentation Library](https://opentelemetry.io/docs/specs/otel/overview/#instrumentation-libraries) for ESA Copernicus Earth Observation Processor Framework ([EOPF](https://eopf.copernicus.eu))

## EOPF OpenTelemetry Instrumentation

`EopfInstrumentor` provides automatic OpenTelemetry tracing for the **EOPF processing framework**.
It instruments key execution points of the framework in order to generate spans describing workflow execution and processing units.

### What it does

The instrumentor automatically creates spans for:

- `EORunner.run`
- `EOProcessorWorkFlow.open_input_products`
- `EOProcessorWorkFlow.run_workflow`
- `EOProcessingUnit.run`
- `EOProcessingUnit.run_validating`

Each span is named using the pattern:

```
<ClassName>.<method>
```

Example:

```
MyProcessingUnit.run
```

### Automatic instrumentation of processing units

All subclasses of `EOProcessingUnit` are instrumented automatically:

- **Existing subclasses** are detected and instrumented when the instrumentor is activated.
- **Future subclasses** are instrumented dynamically by patching `EOProcessingUnit.__init_subclass__`.

This ensures that any processing unit loaded later (in particular via dynamic imports made by eopf triggering) is automatically traced.

### Span attributes

The instrumentor enriches spans with contextual information extracted from method arguments and instance attributes, such as:

- payload information
- workflow I/O configuration
- processing unit inputs and ADFs
- working directory and payload directory

### Error handling

If an exception occurs during the execution of an instrumented method:

- the exception is recorded in the span
- the span status is set to `ERROR`

### Uninstrumentation

The instrumentor can be safely disabled.
When uninstrumented, it restores the original methods and removes all wrappers.

### Metrics

Metric instrumentation hooks are present but currently not implemented.

## CLI wrapper for subprocess trace propagation

This package also provides a small CLI wrapper named `eopf_otel` to enable **OpenTelemetry trace context propagation when `eopf` is executed as a subprocess**.

When launching `eopf` from another Python process, the parent process can inject the current trace context into environment variables using OpenTelemetry propagation APIs. The `eopf_otel` wrapper restores this context before invoking the original `eopf` CLI so that all spans produced during the execution belong to the same distributed trace.

This is particularly useful when orchestrating EOPF processing pipelines from external services or workflow engines.

### How it works

The wrapper performs the following steps:

1. Reads the `OTEL_TRACE_CONTEXT` environment variable containing a JSON-encoded propagation carrier.
2. Restores the OpenTelemetry context using `opentelemetry.propagate.extract`.
3. Attaches the context to the current execution.
4. Executes the original `eopf` CLI.

### Example usage

Parent process:

```python
from opentelemetry.propagate import inject
import json
import os

carrier = {}
inject(carrier)

env = os.environ.copy()
env["OTEL_TRACE_CONTEXT"] = json.dumps(carrier)
```

## Contributing

This projects adheres to the OpenTelemetry Python [guidelines for instrumentations](https://github.com/open-telemetry/opentelemetry-python-contrib/blob/main/CONTRIBUTING.md#guideline-for-instrumentations).

## Licensing

The code in this project is licensed under Apache License 2.0.

Test data: Contains Copernicus data (2026), ESA. It has been downloaded from [Copernicus Browser](https://browser.dataspace.copernicus.eu).

---

![](https://raw.githubusercontent.com/RS-PYTHON/.github/refs/heads/main/profile/banner_logo.jpg)

This project is funded by the EU and ESA.
