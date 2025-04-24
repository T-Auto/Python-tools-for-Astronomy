import os
import re
import logging
from pathlib import Path
import numpy as np
from astropy.io import fits
from tqdm import tqdm

"""
请根据实际情况修改以下路径
示例：

SOURCE_A_DIR = r"D:\PHOENIX-ACES-AGSS-COND-2011\Z+0.5"
SOURCE_B_DIR = r"D:\PHOENIX-ACES-AGSS-COND-2011\Z+1.0"
OUTPUT_DIR = r"D:\PHOENIX-ACES-AGSS-COND-2011\Z+0.75" 
"""

SOURCE_A_DIR = r"path/to/Z-0.0"
SOURCE_B_DIR = r"path/to/Z+0.5"
OUTPUT_DIR = r"path/to/Z+0.25"

LOG_FILE = "interpolation.log"
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    handlers=[logging.FileHandler(LOG_FILE), logging.StreamHandler()])

FILENAME_PATTERN = re.compile(
    r"lte(?P<Teff>\d{5})"  
    r"(?P<logg_sign>[+-])(?P<logg>\d\.\d{2})"  
    r"(?P<feh>[+-]\d\.\d)"  
    r"(?:\.Alpha=(?P<alpha>[+-]\d\.\d{2}))?" 
    r"\.(PHOENIX-ACES-AGSS-COND-2011-HiRes)\.fits" 
)

METALLICITY_PATH_PATTERN = re.compile(r"^Z([+-]\d+\.\d+)$")

def parse_filename(filename):
    match = FILENAME_PATTERN.match(filename)
    if match:
        params = match.groupdict()
        params['Teff'] = int(params['Teff'])
        logg_with_sign = params['logg_sign'] + params['logg']
        params['logg'] = float(logg_with_sign)
        params['feh'] = float(params['feh'].replace('+', ''))
        alpha_str = params.get('alpha')
        if alpha_str:
            params['alpha'] = float(alpha_str.replace('+', ''))
        else:
            params['alpha'] = 0.0
        params['model_suffix'] = match.group(6)
        return params
    else:
        logging.warning(f"无法解析文件名: {filename}")
        return None

def extract_metallicity_from_path(path):
    try:
        path_obj = Path(path)
        dir_name = path_obj.name
    except TypeError:
        logging.error(f"无效的路径类型: {type(path)}. 需要字符串或Path对象。")
        raise TypeError(f"无效的路径类型: {path}")

    match = METALLICITY_PATH_PATTERN.match(dir_name)
    if match:
        metallicity_str = match.group(1)
        return float(metallicity_str)
    else:
        logging.error(f"无法从路径 '{path}' 的末尾部分 '{dir_name}' 提取金属丰度。期望格式如 'Z-0.0' 或 'Z+0.5'。")
        raise ValueError(f"无法解析路径中的金属丰度: {path}")


def generate_output_filename(params, interp_feh, model_suffix):
    feh_str = f"{interp_feh:+.1f}"
    alpha_str = ""
    if params['alpha'] != 0.0:
        alpha_str = f".Alpha={params['alpha']:+.2f}"

    logg_sign = '+' if params['logg'] >= 0 else ''
    logg_str = f"{logg_sign}{params['logg']:.2f}"

    filename = (
        f"lte{params['Teff']:05d}"
        f"{logg_str}"
        f"{feh_str}"
        f"{alpha_str}"
        f".{model_suffix}.fits"
    )
    return filename

def interpolate_spectra(source_a_dir, source_b_dir, output_dir):
    source_a_dir = Path(source_a_dir)
    source_b_dir = Path(source_b_dir)
    output_dir = Path(output_dir)
    logging.info(f"开始光谱插值...")
    logging.info(f"源目录 A (Z1): {source_a_dir}")
    logging.info(f"源目录 B (Z2): {source_b_dir}")
    logging.info(f"输出目录 (Z3): {output_dir}")

    try:
        z1 = extract_metallicity_from_path(source_a_dir)
        z2 = extract_metallicity_from_path(source_b_dir)
    except ValueError as e:
        logging.error(f"初始化失败: {e}")
        return

    if z1 == z2:
        logging.error("源目录 A 和 B 的金属丰度相同，无法进行插值。")
        return

    z3 = (z1 + z2) / 2.0
    logging.info(f"金属丰度: Z1={z1}, Z2={z2}, 插值目标 Z3={z3}")

    output_dir.mkdir(parents=True, exist_ok=True)

    processed_count = 0
    error_count = 0
    matched_count = 0

    files_a = list(source_a_dir.glob("lte*.fits"))
    total_files = len(files_a)
    
    logging.info(f"正在处理 {total_files} 个文件...")
    
    for file_a_path in tqdm(files_a, desc="处理光谱文件"):
        filename_a = file_a_path.name
        params_a = parse_filename(filename_a)

        if not params_a:
            error_count += 1
            continue

        if not np.isclose(params_a['feh'], z1):
            logging.warning(f"文件 {filename_a} 的金属丰度 ({params_a['feh']}) 与目录 Z1 ({z1}) 不匹配，已跳过。")
            error_count += 1
            continue

        expected_feh_b_str = f"{z2:+.1f}"
        alpha_b_str = ""
        if params_a['alpha'] != 0.0:
            alpha_b_str = f".Alpha={params_a['alpha']:+.2f}"

        logg_sign = '+' if params_a['logg'] >= 0 else ''
        logg_str = f"{logg_sign}{params_a['logg']:.2f}"

        filename_b = (
            f"lte{params_a['Teff']:05d}"
            f"{logg_str}"
            f"{expected_feh_b_str}"
            f"{alpha_b_str}"
            f".{params_a['model_suffix']}.fits"
        )
        file_b_path = source_b_dir / filename_b

        if file_b_path.is_file():
            matched_count += 1

            try:
                with fits.open(file_a_path) as hdul_a, fits.open(file_b_path) as hdul_b:
                    if len(hdul_a) == 0 or len(hdul_b) == 0:
                        logging.warning(f"文件 {filename_a} 或 {filename_b} 没有有效的 HDU，已跳过。")
                        error_count += 1
                        continue
                    flux_a = hdul_a[0].data
                    flux_b = hdul_b[0].data
                    hdr_a = hdul_a[0].header

                    if flux_a.shape != flux_b.shape:
                        logging.warning(f"文件 {filename_a} 和 {filename_b} 的数据形状不匹配，已跳过。")
                        error_count += 1
                        continue

                    flux_interp = (flux_a + flux_b) / 2.0

                    output_filename = generate_output_filename(params_a, z3, params_a['model_suffix'])
                    output_path = output_dir / output_filename

                    hdr_new = hdr_a.copy()
                    hdr_new['SRCMET_1'] = (z1, 'Metallicity of source spectrum 1')
                    hdr_new['SRCMET_2'] = (z2, 'Metallicity of source spectrum 2')
                    hdr_new['FEH_INT'] = (z3, 'Interpolated [Fe/H]')
                    hdr_new['HISTORY'] = f"Interpolated from {filename_a} (Z={z1}) and {filename_b} (Z={z2})"
                    hdr_new.add_history(f"Interpolation script: {os.path.basename(__file__)}")

                    primary_hdu = fits.PrimaryHDU(data=flux_interp, header=hdr_new)
                    hdul_out = fits.HDUList([primary_hdu])

                    hdul_out.writeto(output_path, overwrite=True)
                    processed_count += 1

            except Exception as e:
                logging.error(f"处理文件对 {filename_a} 和 {filename_b} 时出错: {e}")
                error_count += 1
        else:
            logging.debug(f"未找到文件 {filename_a} 在 {source_b_dir} 中的对应文件 {filename_b}")

    logging.info(f"插值处理完成。")
    logging.info(f"总共扫描文件数 (源 A): {total_files}")
    logging.info(f"找到的匹配文件对数: {matched_count}")
    logging.info(f"成功生成的插值光谱数: {processed_count}")
    logging.info(f"处理过程中跳过/错误的文件数: {error_count}")

if __name__ == "__main__":
    interpolate_spectra(SOURCE_A_DIR, SOURCE_B_DIR, OUTPUT_DIR) 