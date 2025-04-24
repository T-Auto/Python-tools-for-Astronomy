# 天文学Python工具

[[English]](README.md)

[[简体中文]](README_zh.md)✅

## 环境配置与依赖项

要使用本工具箱，首先要确保您电脑已安装python，创建虚拟环境后（推荐），使用以下命令安装依赖：

```bash
pip install -r requirements.txt
```

## 工具介绍

运行python文件前，务必先修改文件最上方的配置项，如：  

```python
FITS_DIR = "path/to/fits/dir"  # FITS文件所在目录
# 筛选条件范围（左右闭区间）
TEMP_RANGE = (5500, 6500)  # 温度范围，单位K
LOGG_RANGE = (0.0, 4.5)    # 重力范围，log(g)
METAL_RANGE = (-0.5, 0.5)  # 金属丰度范围，[M/H]
ALPHA_RANGE = (-0.2, 1.2)  # Alpha元素增强范围
```

[Information_reading.py](https://github.com/T-Auto/Python-tools-for-Astronomy/blob/main/tools/Information%20reading.py)：读取指定目录下.fits文件的基本信息，并输出.fits文件的前几行作为示例，使得fits文件更加可视化。支持选择输出Markdown或CSV格式的数据。

[verification.py](https://github.com/T-Auto/Python-tools-for-Astronomy/blob/main/tools/verification.py)：进行星表交叉匹配，将计算数据与公开数据进行对比，并计算相对误差的百分比。生成详细的Markdown格式验证报告。

[move.py](https://github.com/T-Auto/Python-tools-for-Astronomy/blob/main/tools/move.py)：根据指定的参数范围（温度、重力、金属丰度和Alpha元素增强）筛选并移动FITS文件。创建一个名称包含筛选条件的新目录来存放筛选后的文件。

[interpolate_spectra.py](https://github.com/T-Auto/Python-tools-for-Astronomy/blob/main/tools/interpolate_spectra.py)：对PHOENIX光谱模型进行金属丰度插值。从两个不同金属丰度的光谱目录（例如Z-0.0和Z+0.5）中找到相同参数（温度、重力、alpha元素丰度）的文件对，进行线性插值产生中间金属丰度（如Z+0.25）的光谱。