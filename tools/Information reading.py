# 代码功能：读取同根目录下的.fits文件，选择首字母排序最靠前的文件，输出其文件结构，并输出一个包含fits文件前3行的.md文件作为示例，为初学者学习fits文件提供指引
# 注意，由于.fits文件巨大，会出现输出缓存问题，通常IDE会显示程序未结束运行，这时候强行关闭程序即可。这也算只读取首字母排序最靠前的文件的原因。

import sys 
from astropy.io import fits
import os

def analyze_fits_file(file_path):
    """
    分析单个 FITS 文件，打印信息并将数据示例写入 Markdown 文件。
    """
    base_filename = os.path.basename(file_path)
    print(f"\n分析文件: {base_filename}")
    print("=" * 50)

    try:
        with fits.open(file_path, mode='readonly', ignore_missing_end=True) as hdul:
            print("\nFITS文件基本信息:")
            print("-" * 30)
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
                     print(f"\n注意: 文件 {base_filename} 的 HDU 1 包含图像数据，而非表格数据。跳过列信息和 Markdown 输出。")
                 else:
                     print(f"\n错误: 文件 {base_filename} 的 HDU 1 不包含列数据 (可能不是表格数据)。")
                 return

            print("\n数据列信息:")
            print("-" * 30)
            print(f"{'列名':<25} {'数据类型':<15} {'单位'}") 
            print(f"{'-'*25:<25} {'-'*15:<15} {'-'*10}") 
            for col in columns:
                unit_str = col.unit if hasattr(col, 'unit') and col.unit is not None else '无'
                print(f"{col.name:<25} {col.format:<15} {unit_str}")
            print("-" * (25 + 1 + 15 + 1 + 10)) 
            print("\n生成数据示例 Markdown 文件...")
            print("-" * 30)
            md_filename = os.path.splitext(file_path)[0] + ".md"

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
                print(f"数据示例已成功写入: {os.path.basename(md_filename)}")

            except Exception as e:
                print(f"写入 Markdown 文件 {os.path.basename(md_filename)} 时出错: {e}")


    except FileNotFoundError:
        print(f"错误: 文件未找到 - {file_path}")
    except OSError as e:
        print(f"处理文件 {base_filename} 时发生IO错误: {e}")
    except Exception as e:
        import traceback
        print(f"处理文件 {base_filename} 时发生未知错误: {e}")
        print("详细错误追踪:")
        traceback.print_exc(file=sys.stdout) 

if __name__ == "__main__":
    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
    except NameError:
        script_dir = os.getcwd()
        print("警告: 无法确定脚本文件路径，将使用当前工作目录:", script_dir)

    print(f"脚本运行目录: {script_dir}")

    print("\n正在查找目录下的 .fits 文件...")
    fits_files = []
    try:
        for filename in os.listdir(script_dir):
            if filename.lower().endswith('.fits'):
                full_path = os.path.join(script_dir, filename)
                if os.path.isfile(full_path):
                    fits_files.append(full_path)
    except Exception as e:
        print(f"错误: 查找文件时出错 - {e}")
        sys.exit(1)


    if not fits_files:
        print("在脚本目录中未找到任何 .fits 文件。")
    else:
        print(f"找到 {len(fits_files)} 个 .fits 文件:")
        for f in fits_files:
            print(f"  - {os.path.basename(f)}")

        fits_files.sort() 
        file_to_process = fits_files[0] 

        print(f"\n将处理首字母排序最靠前的文件: {os.path.basename(file_to_process)}")

        print("\n开始处理文件...")
        print("=" * 50)
        file_path = file_to_process
        print(f"\n--- 开始处理: {os.path.basename(file_path)} ---")
        analyze_fits_file(file_path)

        print(f"--- 完成处理: {os.path.basename(file_path)} ---")
        print("-" * 50) 

    print("\n文件处理完毕。")
    sys.stdout.flush() 

    print("\n程序运行结束。") 
