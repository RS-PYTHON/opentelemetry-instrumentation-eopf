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

from typing import Any, Optional, cast

from eopf import EOProduct
from eopf.computing import EOProcessingUnit
from eopf.computing.abstract import MappingAuxiliary, MappingDataType


class MyPVIProcessor(EOProcessingUnit):
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
        return ["tci"]

    def run(
        self,
        inputs: MappingDataType,
        adfs: Optional[MappingAuxiliary] = None,
        **kwargs: Any,
    ) -> MappingDataType:
        """Runs the processing unit

        A more complete description can be added here.

        Parameters
        ----------
        inputs: EOProduct
            Input products
        adfs: Optional[MappingAuxiliary]
            Auxiliary configuration files
        kwargs: Any
            Named parameters to use for the processor:
            the 'name' parameter is mandatory and shall
            specify the name of the EOProduct created by
            the processing unit.




        """
        # Create valid EOProduct

        in_product = cast(EOProduct, inputs["tci"])
        product = EOProduct(name="pvi", attrs=in_product.attrs.copy())
        product.product_type = "S2MSIPVI"

        # tci_var: EOVariable = cast(EOVariable, in_product["measurements/tci"])
        # tci_array = tci_var.data
        # pvi_array = tci_array.coarsen(x_10m=10, y_10m=10)
        # pvi_array_mean = pvi_array.mean().astype("uint8")  # type: ignore[attr-defined]

        # product["measurements/pvi"] = EOVariable(data=pvi_array_mean)

        product.short_names = {
            "pvi": "measurements/pvi",
        }

        return {"pvi": product}
