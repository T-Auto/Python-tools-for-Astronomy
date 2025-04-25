# Python-tools-for-Astronomy

[[English]](README.md)✅

[[简体中文]](README_zh.md)

## Environment Setup and Dependencies

To use this toolkit, first make sure you have python installed on your computer, and after creating a virtual environment (recommended), install the dependencies using the following commands:

```bash
pip install -r requirements.txt
```

## Tool Introduction

Before running the Python files, be sure to modify the configuration settings at the top of each file, such as:

```python
FITS_DIR = "path/to/fits/dir"  # Directory containing FITS files
# Filter condition ranges (closed intervals)
TEMP_RANGE = (5500, 6500)  # Temperature range in K
LOGG_RANGE = (0.0, 4.5)    # Gravity range, log(g)
METAL_RANGE = (-0.5, 0.5)  # Metallicity range, [M/H]
ALPHA_RANGE = (-0.2, 1.2)  # Alpha element enhancement range
```

[Information_reading.py](https://github.com/T-Auto/Python-tools-for-Astronomy/blob/main/tools/Information%20reading.py): Reads basic information from .fits files in the specified directory and outputs the first three lines of the .fits file as an example, making fits files more visual. Supports output in both Markdown and CSV formats according to user choice.

[verification.py](https://github.com/T-Auto/Python-tools-for-Astronomy/blob/main/tools/verification.py): Performs star catalog cross-matching to compare calculated data with public data and calculate the percentage relative error. Generates a detailed validation report in Markdown format.

[move.py](https://github.com/T-Auto/Python-tools-for-Astronomy/blob/main/tools/move.py): Filters and moves FITS files based on specified parameter ranges (temperature, gravity, metallicity, and alpha element enhancement). Creates a new directory with a name that indicates the filter criteria.

[interpolate_spectra.py](https://github.com/T-Auto/Python-tools-for-Astronomy/blob/main/tools/interpolate_spectra.py): Performs metallicity interpolation on PHOENIX spectral models. Finds matching pairs of spectra with identical parameters (temperature, gravity, alpha enhancement) but different metallicities (e.g., Z-0.0 and Z+0.5), and creates interpolated spectra at the intermediate metallicity (e.g., Z+0.25). 

[synthesize_spectra.py](https://github.com/T-Auto/Python-tools-for-Astronomy/blob/main/tools/synthesize_spectra.py): Synthesizes theoretical stellar spectra based on four basic input parameters (effective temperature Teff, surface gravity log g, metallicity [Fe/H], and α-element abundance [α/Fe]). This tool implements the complete process of stellar atmosphere model construction and spectrum synthesis, supports multiple synthesis methods, and can save results as FITS files or images for scientific research and educational purposes. 