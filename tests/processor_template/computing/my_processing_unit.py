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

# Copyright 2023 ESA
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from typing import Any, Optional, cast

import numpy as np
import xarray as xr
from eopf import EOProduct
from eopf.computing import EOProcessingUnit
from eopf.computing.abstract import MappingAuxiliary, MappingDataType
from eopf.computing.breakpoint import eopf_breakpoint_decorator


def rescale_intensity(
    x: xr.DataArray,
    no_data_replace_value,
    rescale_factor,
    radiance_max,
    min_out_value,
    max_out_value,
    output_type=np.uint8,
) -> xr.DataArray:  # or np.float32, etc.
    # Mask for valid values (not equal to NoData)
    valid_mask = x != np.nan

    # Compute the main formula where valid
    value = (x * rescale_factor) / radiance_max + 0.5
    value = xr.where(valid_mask, value, np.nan)  # Only compute where valid

    # Clamp the values
    value = value.clip(min=min_out_value, max=max_out_value)

    # Cast to output type
    result = value.astype(output_type)

    # Replace invalid (NoData) with m_NoDataReplaceValue
    result = result.where(valid_mask, other=no_data_replace_value)

    return result


def create_rgb_image(red: xr.DataArray, green: xr.DataArray, blue: xr.DataArray) -> xr.DataArray:
    # Ensure the bands are all the same shape
    if not red.shape == green.shape == blue.shape:
        raise Exception("Bands must have the same shape")

    # Stack along a new 'band' dimension (or 'channel')
    rgb = xr.concat([red, green, blue], dim="band")

    # Assign band labels if needed
    rgb = rgb.assign_coords(band=["R", "G", "B"])

    return rgb


class MyProcessingUnit(EOProcessingUnit):
    """
    Input Product
    ^^^^^^^^^^^^^
    - **L1C Product**: S2 level 1C product.


    Output Product
    ^^^^^^^^^^^^^^
    - **TCI Product**

    Methods
    -------
    run:
        Execute the input preprocessing unit.
    """

    def get_mandatory_input_list(self, **kwargs: Any) -> list[str]:
        return ["l1c"]

    @eopf_breakpoint_decorator(
        "my_processing_unit",
        description="MyProcessingUnit: wololo",
    )
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

        in_product = cast(EOProduct, inputs["l1c"])
        product = EOProduct(name="tci", attrs=in_product.attrs.copy())
        product.product_type = "S2MSITCI"

        # r10m_group: EOGroup = cast(EOGroup, in_product["/measurements/reflectance/r10m"])
        # red_reflectance: DataArray = cast(EOVariable, r10m_group["b04"]).data
        # green_reflectance = cast(EOVariable, r10m_group["b03"]).data
        # blue_reflectance = cast(EOVariable, r10m_group["b02"]).data

        # red_rescaled = rescale_intensity(
        #     red_reflectance,
        #     no_data_replace_value=kwargs.get("no_data_replace_value"),
        #     rescale_factor=kwargs.get("rescale_factor"),
        #     radiance_max=kwargs.get("radiance_max"),
        #     min_out_value=kwargs.get("min_out_value"),
        #     max_out_value=kwargs.get("max_out_value"),
        # )
        # green_rescaled = rescale_intensity(
        #     green_reflectance,
        #     no_data_replace_value=kwargs.get("no_data_replace_value"),
        #     rescale_factor=kwargs.get("rescale_factor"),
        #     radiance_max=kwargs.get("radiance_max"),
        #     min_out_value=kwargs.get("min_out_value"),
        #     max_out_value=kwargs.get("max_out_value"),
        # )
        # blue_rescaled = rescale_intensity(
        #     blue_reflectance,
        #     no_data_replace_value=kwargs.get("no_data_replace_value"),
        #     rescale_factor=kwargs.get("rescale_factor"),
        #     radiance_max=kwargs.get("radiance_max"),
        #     min_out_value=kwargs.get("min_out_value"),
        #     max_out_value=kwargs.get("max_out_value"),
        # )

        # product["measurements/tci"] = EOVariable(data=create_rgb_image(red_rescaled, green_rescaled, blue_rescaled))

        # product["measurements/tci_red"] = EOVariable(data=red_rescaled)
        # product["measurements/tci_green"] = EOVariable(data=green_rescaled)
        # product["measurements/tci_blue"] = EOVariable(data=blue_rescaled)
        product.short_names = {
            "tci": "measurements/tci",
        }

        return {"tci": product}
