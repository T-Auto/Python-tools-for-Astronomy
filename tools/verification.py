import numpy as np
from astropy.table import Table
from astropy.io import fits
import logging
import os
from tqdm import tqdm

# 要比较的参数列: ('输出列名', '参考列名', '显示名称')
PARAMS_TO_COMPARE = [
    ('teff_est', 'teff', 'Teff'),
    ('logg_est', 'logg', 'logg'),
    ('feh_est', 'feh', '[Fe/H]')
]

OUTPUT_FITS_FILENAME = 'output.fits'
REFERENCE_CATALOG_FILENAME = 'dr11_v1.1_LRS_stellar.fits'
VERIFICATION_MD_FILENAME = 'verification_report_zh.md'

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

OUTPUT_FITS_PATH = os.path.join(SCRIPT_DIR, OUTPUT_FITS_FILENAME)
REFERENCE_CATALOG_PATH = os.path.join(SCRIPT_DIR, REFERENCE_CATALOG_FILENAME)
VERIFICATION_MD_PATH = os.path.join(SCRIPT_DIR, VERIFICATION_MD_FILENAME)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def calculate_percentage_difference(estimated, reference):
    if reference is None or not np.isfinite(reference) or np.isclose(reference, 0):
        return np.nan
    if estimated is None or not np.isfinite(estimated):
        return np.nan
    try:
        return ((float(estimated) - float(reference)) / float(reference)) * 100.0
    except (TypeError, ValueError):
        return np.nan

def format_value(value, precision=2):
    if value is None or not np.isfinite(value):
        return "N/A"
    return f"{value:.{precision}f}"

def format_percentage(value, precision=1):
    formatted_val = format_value(value, precision)
    return f"{formatted_val}%" if formatted_val != "N/A" else "N/A"

if __name__ == "__main__":
    logging.info("开始验证流程...")

    # 1. 加载数据
    logging.info(f"加载估计结果: {OUTPUT_FITS_PATH}")
    try:
        with fits.open(OUTPUT_FITS_PATH) as hdul:
            if len(hdul) < 2:
                 logging.error(f"错误: FITS文件 {OUTPUT_FITS_PATH} 不含数据 HDU。")
                 exit()
            output_table = Table(hdul[1].data)
        logging.info(f"已加载 {len(output_table)} 条结果。")
    except FileNotFoundError:
        logging.error(f"错误: 结果文件未找到: {OUTPUT_FITS_PATH}")
        exit()
    except Exception as e:
        logging.error(f"加载结果文件时出错: {e}")
        exit()

    logging.info(f"加载参考星表: {REFERENCE_CATALOG_PATH}")
    try:
        with fits.open(REFERENCE_CATALOG_PATH) as hdul:
            if len(hdul) < 2:
                 logging.error(f"错误: FITS文件 {REFERENCE_CATALOG_PATH} 不含数据 HDU。")
                 exit()
            ref_catalog = Table(hdul[1].data)
        logging.info(f"已加载 {len(ref_catalog)} 条参考条目。")
    except FileNotFoundError:
        logging.error(f"错误: 参考星表未找到: {REFERENCE_CATALOG_PATH}")
        exit()
    except Exception as e:
        logging.error(f"加载参考星表时出错: {e}")
        exit()

    required_output_cols = ['obsid'] + [p[0] for p in PARAMS_TO_COMPARE]
    missing_output_cols = [col for col in required_output_cols if col not in output_table.colnames]
    if missing_output_cols:
        logging.error(f"错误: 输出表缺少列: {', '.join(missing_output_cols)}")
        exit()

    required_ref_cols = ['obsid'] + [p[1] for p in PARAMS_TO_COMPARE]
    missing_ref_cols = [col for col in required_ref_cols if col not in ref_catalog.colnames]
    if missing_ref_cols:
        logging.error(f"错误: 参考表缺少列: {', '.join(missing_ref_cols)}")
        exit()

    logging.info("构建参考星表查找字典...")
    ref_lookup = {}
    duplicate_obsids = 0
    try:
        iterator = tqdm(range(len(ref_catalog)), desc="构建查找表") if len(ref_catalog) > 10000 else range(len(ref_catalog))
        for i in iterator:
            try:
                obsid = ref_catalog['obsid'][i]
                if isinstance(obsid, bytes):
                    obsid = obsid.decode('utf-8').strip()
                # obsid = str(obsid) # 可选：强制转为字符串

            except Exception as e:
                logging.debug(f"处理参考表第 {i} 行 'obsid' 出错: {e}，跳过。")
                continue

            if obsid not in ref_lookup:
                ref_lookup[obsid] = i
            else:
                duplicate_obsids += 1

        if duplicate_obsids > 0:
             logging.warning(f"参考星表中发现 {duplicate_obsids} 个重复obsid，使用首次出现的条目。")
        logging.info(f"查找字典构建完成，含 {len(ref_lookup)} 个唯一obsid。")
    except KeyError:
        logging.error("错误: 参考星表中未找到 'obsid' 列。")
        exit()
    except Exception as e:
        logging.error(f"构建查找字典时出错: {e}")
        exit()

    logging.info("比较结果与参考星表...")
    comparison_data = []
    not_found_count = 0

    for output_row in tqdm(output_table, desc="比较条目"):
        try:
            obsid = output_row['obsid']
            if isinstance(obsid, bytes):
                obsid = obsid.decode('utf-8').strip()
            # obsid = str(obsid) # 可选：强制转为字符串
        except Exception as e:
            logging.debug(f"处理输出表某行 'obsid' 出错: {e}，跳过。")
            continue

        ref_row_index = ref_lookup.get(obsid)

        if ref_row_index is not None:
            ref_row = ref_catalog[ref_row_index]
            data_row = {'obsid': obsid}
            valid_comparison = True

            for est_col, ref_col, name in PARAMS_TO_COMPARE:
                try:
                    est_val = float(output_row[est_col])
                    ref_val = float(ref_row[ref_col])
                except (ValueError, TypeError, KeyError) as e:
                    logging.debug(f"处理 obsid={obsid}, 参数={name} 出错: {e}")
                    est_val, ref_val = np.nan, np.nan
                    valid_comparison = False

                perc_diff = calculate_percentage_difference(est_val, ref_val)
                data_row[f'{name}_est'] = est_val
                data_row[f'{name}_ref'] = ref_val
                data_row[f'{name}_%diff'] = perc_diff

            # 可选：即使部分无效也记录（移除 if valid_comparison）
            if valid_comparison:
                 comparison_data.append(data_row)
            else:
                 logging.warning(f"obsid={obsid} 数据比较不完整（存在无效值）。")
                 # comparison_data.append(data_row) # 若要记录不完整行，取消此行注释

        else:
            not_found_count += 1
            logging.debug(f"obsid={obsid} 未在参考星表中找到。")

    logging.info(f"比较完成。找到 {len(comparison_data)} 个匹配条目。")
    if not_found_count > 0:
        logging.warning(f"{not_found_count} 个 obsid 未在参考星表中找到。")

    if not comparison_data:
        logging.warning("未找到匹配条目，无法生成报告。")
        markdown_content = "# 验证报告\n\n结果文件与参考星表无匹配项。\n"
    else:
        logging.info("生成Markdown报告...")
        header_parts = ["| obsid "]
        separator_parts = ["|:---|"]
        for _, _, name in PARAMS_TO_COMPARE:
            header_parts.extend([f"| {name} (估计) ", f"| {name} (参考) ", f"| {name} (%差异) "])
            separator_parts.extend(["|---:|---:|---:|"])
        header = "".join(header_parts) + "|"
        separator = "".join(separator_parts) + "|"

        data_rows = []
        for row_data in comparison_data:
            row_parts = [f"| {row_data['obsid']} "]
            for _, _, name in PARAMS_TO_COMPARE:
                precision = 0 if name == 'Teff' else 2
                p_precision = 1
                row_parts.extend([
                    f"| {format_value(row_data[f'{name}_est'], precision)} ",
                    f"| {format_value(row_data[f'{name}_ref'], precision)} ",
                    f"| {format_percentage(row_data[f'{name}_%diff'], p_precision)} "
                ])
            data_rows.append("".join(row_parts) + "|")

        markdown_content = "# 验证报告\n\n"
        markdown_content += f"比较 `{os.path.basename(OUTPUT_FITS_PATH)}` 与 `{os.path.basename(REFERENCE_CATALOG_PATH)}`。\n\n" # 报告中只显示文件名
        markdown_content += header + "\n"
        markdown_content += separator + "\n"
        markdown_content += "\n".join(data_rows)
        markdown_content += "\n"

    try:
        with open(VERIFICATION_MD_PATH, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        logging.info(f"验证报告已写入: {VERIFICATION_MD_PATH}")
    except Exception as e:
        logging.error(f"写入验证报告时出错: {e}")

    logging.info("验证流程结束。")