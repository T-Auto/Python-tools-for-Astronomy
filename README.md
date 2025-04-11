# Python-tools-for-Astronomy

[[Englishi]](README.md)✅

[[简体中文]](README_zh.md)

## Environment Setup and Dependencies

To use this toolbox, first ensure that Python is installed on your computer. Then, press win+R, type cmd to open the terminal, copy and run:

```bash
pip install numpy
pip install astropy
pip install tqdm
```

## Tool Introduction

[Information reading.py](https://github.com/T-Auto/Python-tools-for-Astronomy/blob/main/tools/Information reading.py): Reads basic information from .fits files in the same root directory and outputs the first three lines of the .fits file as an example, making .fits files more visually accessible.

_This tool defaults to reading only the single .fits file that is alphabetically first in the root directory to prevent computer lag._

[verification.py](https://github.com/T-Auto/Python-tools-for-Astronomy/blob/main/tools/verification.py): Can perform catalog cross-matching, compare calculated data with public data, and calculate the percentage of relative error.
