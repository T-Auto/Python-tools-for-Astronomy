import os
import shutil
import re

FITS_DIR = "path/to/fits/dir"  # FITS文件所在目录
# 筛选条件范围（左右闭区间）
TEMP_RANGE = (5500, 6500)  # 温度范围，单位K
LOGG_RANGE = (1.0, 6.0)    # 重力范围，log(g)
METAL_RANGE = (-1.0, 0.5)  # 金属丰度范围，[M/H]
ALPHA_RANGE = (-0.5, 1.0)  # Alpha元素增强范围

def parse_filename(filename):
    """解析FITS文件名，提取参数"""
    if not filename.endswith('.fits'):
        return None
    
    try:
        temp_match = re.search(r'lte(\d{5})', filename)
        if not temp_match:
            return None
        temp = int(temp_match.group(1))

        pattern = r'lte\d{5}-(\d+\.\d+)([+-]\d+\.\d+)'
        match = re.search(pattern, filename)
        if not match:
            return None
            
        logg = float(match.group(1))
        metal = float(match.group(2))
        
        alpha = 0.0
        alpha_match = re.search(r'Alpha=([+-]\d+\.\d+)', filename)
        if alpha_match:
            alpha = float(alpha_match.group(1))
        
        return {
            'temp': temp,
            'logg': logg,
            'metal': metal,
            'alpha': alpha,
            'filename': filename
        }
    except Exception as e:
        print(f"解析文件名出错 {filename}: {str(e)}")
        return None

def main():
    target_dir_name = f"{str(TEMP_RANGE[0]).zfill(5)}-{str(TEMP_RANGE[1]).zfill(5)}-" \
                      f"{LOGG_RANGE[0]:.2f}-{LOGG_RANGE[1]:.2f}-" \
                      f"{METAL_RANGE[0]:.1f}-{METAL_RANGE[1]:.1f}-" \
                      f"{ALPHA_RANGE[0]:.2f}-{ALPHA_RANGE[1]:.2f}"
    
    target_dir_path = os.path.join(FITS_DIR, target_dir_name)
    
    if not os.path.exists(target_dir_path):
        os.makedirs(target_dir_path)
        print(f"创建目标文件夹: {target_dir_path}")
    
    moved_count = 0
    files = os.listdir(FITS_DIR)
    
    for filename in files:
        file_path = os.path.join(FITS_DIR, filename)
        
        if os.path.isdir(file_path):
            continue
        
        file_info = parse_filename(filename)
        if not file_info:
            continue
        
        if (TEMP_RANGE[0] <= file_info['temp'] <= TEMP_RANGE[1] and
            LOGG_RANGE[0] <= file_info['logg'] <= LOGG_RANGE[1] and
            METAL_RANGE[0] <= file_info['metal'] <= METAL_RANGE[1] and
            ALPHA_RANGE[0] <= file_info['alpha'] <= ALPHA_RANGE[1]):
            
            target_file_path = os.path.join(target_dir_path, filename)
            shutil.move(file_path, target_file_path)
            moved_count += 1
            print(f"移动文件: {filename} -> {target_dir_name}/{filename}")
    
    print(f"\n操作完成! 共移动了 {moved_count} 个文件到 {target_dir_name} 文件夹")

if __name__ == "__main__":
    main()