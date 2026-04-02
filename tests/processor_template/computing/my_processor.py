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

from typing import Any, Optional

from eopf import EOLogging
from eopf.common import file_utils
from eopf.computing import EOProcessingUnit
from eopf.computing.abstract import MappingAuxiliary, MappingDataType
from processor_template.computing.my_processing_unit import MyProcessingUnit
from processor_template.exceptions.errors import MyError


class MyProcessor(EOProcessingUnit):
    """My Processor

    Methods
    -------
    run:
        Execute the processor.

    Parameters
    ----------
    inputs: EOProduct
        Input products
    kwargs: Any
        Named parameters to use for the processor:
        the 'name' parameter is mandatory and shall
        specify the name of the EOProduct created by
        the processing unit.
    """

    def get_mandatory_input_list(self, **kwargs: Any) -> list[str]:
        return ["l1c"]

    def get_mandatory_adf_list(self, **kwargs: Any) -> list[str]:
        return ["gip_convert"]

    def run(
        self,
        inputs: MappingDataType,
        adfs: Optional[MappingAuxiliary] = None,
        **kwargs: Any,
    ) -> MappingDataType:
        """Runs the processor.

        Parameters
        ----------
        inputs: MappingDataType
            all the products to process in this processing unit
        adfs: Optional[Mapping[str,AuxiliaryDataFile]]
            all the ADFs needed to process
        **kwargs: any
            any needed kwargs (e.g. parameters)

        Returns
        -------
        Mapping[str, DataType ]

        Examples
        --------
        This is an example demonstrating how doctest
        can be used to illustrate the usage of the source code.
        See https://numpydoc.readthedocs.io/en/latest/example.html
        for numpydoc examples.

        >>> from processor_template.computing.my_processor import (
        >>>    MyProcessor,
        >>> )
        >>> myProcessor = MyProcessor()
        >>> myProcessor.run()

        """
        logger = EOLogging().get_logger()
        my_processing_unit = MyProcessingUnit()

        logger.info("Validating input")
        # At least one product is expected
        if "l1c" not in inputs:
            raise MyError("Missing mandatory input product for the processor run.")
        if adfs is None or "gip_convert" not in adfs:
            raise MyError("Missing mandatory adf concert for the processor run.")
        convert_param = file_utils.load_json_file(adfs["gip_convert"].path)
        logger.info("Running 'my processing unit'")
        my_product = my_processing_unit.run(inputs, adfs, **convert_param)

        return my_product
