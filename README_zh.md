# 天文学Python工具

[[Englishi]](README.md)

[[简体中文]](README_zh.md)✅

## 环境配置与依赖项

要使用本工具箱，首先要确保您电脑已安装python，然后按win+R，输入cmd打开终端，复制并运行：

```bash
pip install numpy
pip install astropy
pip install tqdm
```

## 工具介绍

[Information reading.py](https://github.com/T-Auto/Python-tools-for-Astronomy/blob/main/tools/Information reading.py)：读取同根目录下.fits文件的基本信息，并输出.fits文件的前三行作为示例，使得fits文件更加可视化。

_此工具默认只读取根目录下首字母排序最靠前的单个.fits文件，以防电脑卡顿_

[verification.py](https://github.com/T-Auto/Python-tools-for-Astronomy/blob/main/tools/verification.py)：可以进行星表交叉，将计算数据与公开数据进行对比，并计算相对误差的百分比。