# opentelemetry-instrumentation-eopf
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
- execution mode
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

## Contributing

This projects adheres to the OpenTelemetry Python [guidelines for instrumentations](https://github.com/open-telemetry/opentelemetry-python-contrib/blob/main/CONTRIBUTING.md#guideline-for-instrumentations).

## Licensing

The code in this project is licensed under Apache License 2.0.

Test data: Contains Copernicus data (2026), ESA. It has been downloaded from [Copernicus Browser](https://browser.dataspace.copernicus.eu).

---

![](https://raw.githubusercontent.com/RS-PYTHON/.github/refs/heads/main/profile/banner_logo.jpg)

This project is funded by the EU and ESA.
