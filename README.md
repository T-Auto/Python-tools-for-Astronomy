# Python-tools-for-Astronomy

[[English]](README.md)✅

[[简体中文]](README_zh.md)

## Environment Setup and Dependencies

To use this toolkit, first ensure that Python is installed on your computer. Then, right-click in the project root directory, select "Open in Terminal", and execute the following command:

```bash
pip install -r requirements.txt
```

## Tool Introduction

[Information reading.py](https://github.com/T-Auto/Python-tools-for-Astronomy/blob/main/tools/Information%20reading.py): Reads basic information from .fits files in the root directory and outputs the first three lines of the .fits file as an example, making .fits files more visual.

_※This tool defaults to reading only the single .fits file with the alphabetically earliest filename in the root directory to prevent computer lag.※_

[verification.py](https://github.com/T-Auto/Python-tools-for-Astronomy/blob/main/tools/verification.py): Can perform star catalog cross-matching to compare calculated data with public data and calculate the percentage relative error.
