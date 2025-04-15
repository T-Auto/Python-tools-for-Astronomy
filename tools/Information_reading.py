"""
代码功能：读取同根目录下的.fits文件，选择首字母排序最靠前的文件，输出其文件结构，并根据用户选择输出markdown或csv格式的数据，为初学者学习fits文件提供指引
"""
import sys 
from astropy.io import fits
import os
import csv

FITS_DIR = r"path/to/fits/dir"
OUTPUT_DIR = r"path/to/output/dir"

def analyze_fits_file(file_path, output_format='markdown', start_row=0, end_row=2):

    base_filename = os.path.basename(file_path)
    output_filename_base = os.path.splitext(os.path.basename(file_path))[0]

    try:
        with fits.open(file_path, mode='readonly', ignore_missing_end=True) as hdul:
            print("\nFITS文件基本信息:")
            hdul.info(output=sys.stdout)
            if len(hdul) < 2 or not hasattr(hdul[1], 'data') or hdul[1].data is None:
                 print(f"\n警告: 文件 {base_filename} 的 HDU 1 中没有找到有效的数据表。跳过此文件的数据处理。")
                 return 
            try:
                 data = hdul[1].data
                 columns = data.columns
            except IndexError:
                 print(f"\n错误: 无法访问文件 {base_filename} 的 HDU 1。文件可能不包含标准的数据表扩展。")
                 return
            except AttributeError:
                 if hasattr(hdul[1], 'shape'):
                     print(f"\n注意: 文件 {base_filename} 的 HDU 1 包含图像数据，而非表格数据。跳过列信息和输出。")
                 else:
                     print(f"\n错误: 文件 {base_filename} 的 HDU 1 不包含列数据 (可能不是表格数据)。")
                 return

            print("\n数据列信息:")
            print(f"{'列名':<25} {'数据类型':<15} {'单位'}") 
            print(f"{'-'*25:<25} {'-'*15:<15} {'-'*10}") 
            for col in columns:
                unit_str = col.unit if hasattr(col, 'unit') and col.unit is not None else '无'
                print(f"{col.name:<25} {col.format:<15} {unit_str}")
            print("-" * (25 + 1 + 15 + 1 + 10))
            
            
            if output_format.lower() == 'markdown':
                md_filename = os.path.join(OUTPUT_DIR, output_filename_base + ".md")
                try:
                    num_rows_to_sample = 3
                    sample_data = data[:min(num_rows_to_sample, len(data))]

                    if len(sample_data) == 0:
                        print(f"注意: 文件 {base_filename} 的数据表为空，无法生成示例。")
                        return

                    column_names = columns.names 
                    md_content = f"# 数据示例 (前{len(sample_data)}行): {base_filename}\n\n" 

                    md_content += "| " + " | ".join(column_names) + " |\n"
                    md_content += "|-" + "-|".join(['-' * max(3, len(str(name))) for name in column_names]) + "-|\n"

                    for row_index in range(len(sample_data)):
                        row = sample_data[row_index]
                        row_str = [str(item).strip() if item is not None else '' for item in row] 
                        md_content += "| " + " | ".join(row_str) + " |\n"

                    with open(md_filename, 'w', encoding='utf-8') as md_file:
                        md_file.write(md_content)
                    print(f"写入数据示例到: {md_filename}中...")

                except Exception as e:
                    print(f"写入 Markdown 文件 {os.path.basename(md_filename)} 时出错: {e}")
            
            elif output_format.lower() == 'csv':
                csv_filename = os.path.join(OUTPUT_DIR, output_filename_base + ".csv")
                try:
                    end_row = min(end_row, len(data) - 1)
                    
                    if start_row > end_row:
                        print(f"警告: 开始行 ({start_row}) 大于结束行 ({end_row})，无法生成CSV文件。")
                        return
                    
                    if start_row < 0:
                        print(f"警告: 开始行不能为负数，已设置为0。")
                        start_row = 0

                    selected_data = data[start_row:end_row+1]
                    
                    if len(selected_data) == 0:
                        print(f"注意: 文件 {base_filename} 的指定范围内无数据，无法生成CSV文件。")
                        return
                    
                    column_names = columns.names
                    
                    with open(csv_filename, 'w', newline='', encoding='utf-8') as csv_file:
                        csv_writer = csv.writer(csv_file)
                        csv_writer.writerow(column_names)
                        for row in selected_data:
                            row_values = [str(item).strip() if item is not None else '' for item in row]
                            csv_writer.writerow(row_values)
                    
                    print(f"写入CSV数据到: {csv_filename}中...")
                    print(f"已保存第{start_row}行到第{end_row}行的数据。")
                
                except Exception as e:
                    print(f"写入CSV文件 {os.path.basename(csv_filename)} 时出错: {e}")


    except FileNotFoundError:
        print(f"错误: 文件未找到 - {file_path}")
    except OSError as e:
        print(f"处理文件 {base_filename} 时发生IO错误: {e}")
    except Exception as e:
        import traceback
        print(f"处理文件 {base_filename} 时发生未知错误: {e}")
        print("详细错误追踪:")
        traceback.print_exc(file=sys.stdout) 

def get_user_choice():
    """获取用户输出格式选择"""
    print("\n请选择输出格式:")
    print("1. Markdown格式 (默认)")
    print("2. CSV格式")
    
    while True:
        choice = input("请输入选择 (1/2): ").strip()
        if not choice or choice == '1':
            return 'markdown', 0, 2
        elif choice == '2':
            print("\n请指定CSV输出范围 (从第几行到第几行，闭区间，从0开始)")
            while True:
                start_row = int(input("开始行 : ").strip())
                end_row = int(input("结束行: ").strip())
                return 'csv', start_row, end_row
        else:
            print("无效选择，请重新输入")

if __name__ == "__main__":

    print(f"fits目录: {FITS_DIR}")
    print(f"输出目录: {OUTPUT_DIR}")

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    print("查找目录下的 .fits 文件...")
    fits_files = []
    try:
        for filename in os.listdir(FITS_DIR):
            if filename.lower().endswith('.fits'):
                full_path = os.path.join(FITS_DIR, filename)
                if os.path.isfile(full_path):
                    fits_files.append(full_path)
    except Exception as e:
        print(f"错误: 查找文件时出错 - {e}")
        sys.exit(1)

    if not fits_files:
        print("在指定目录中未找到任何 .fits 文件。")
    else:
        print(f"找到 {len(fits_files)} 个 .fits 文件:")
        for f in fits_files:
            print(f"  - {os.path.basename(f)}")
        print()

        output_format, start_row, end_row = get_user_choice()

        fits_files.sort()
        for file_to_process in fits_files:
            print("-" * 50)
            file_path = file_to_process
            print(f"\n开始处理: {os.path.basename(file_path)}")
            analyze_fits_file(file_path, output_format, start_row, end_row)

            print(f"完成处理: {os.path.basename(file_path)}")

    print("-" * 50)
    print("\n全部文件处理完毕。")
    sys.stdout.flush()
