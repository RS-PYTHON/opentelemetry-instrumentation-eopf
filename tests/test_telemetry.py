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
"""Opentelemetry tests."""

from pathlib import Path

from eopf.triggering.runner import EORunner
from opentelemetry.test.test_base import TestBase
from opentelemetry.trace import Span, SpanKind
from typing_extensions import override

from opentelemetry.instrumentation.eopf import EopfInstrumentor


class TestEopfInstrumentation(TestBase):
    """Test EOPF instrumentation"""

    @override
    def setUp(self):
        super().setUp()
        EopfInstrumentor().instrument()

    @override
    def tearDown(self):
        super().tearDown()
        EopfInstrumentor().uninstrument()

    def test_eopf_instrumentor(self):
        """Test EOPF instrumentation"""
        test_dir = Path(__file__).parent
        EORunner().run_from_file(test_dir / "trigger.yaml", test_dir)

        spans: list[Span] = self.sorted_spans(self.memory_exporter.get_finished_spans())
        self.assertEqual(len(spans), 6)

        for span in spans:
            self.assertEqual(SpanKind.INTERNAL, span.kind)

        self.assertEqual("MyPVIProcessor", spans[0].name)
        self.assertEqual("MyProcessingUnit.run", spans[1].name)
        self.assertEqual("MyProcessor.run", spans[2].name)
        self.assertEqual("EOProcessorWorkFlow.open_input_products", spans[3].name)
        self.assertEqual("EOProcessorWorkFlow.run_workflow", spans[4].name)
        self.assertEqual("EORunner.run", spans[5].name)
