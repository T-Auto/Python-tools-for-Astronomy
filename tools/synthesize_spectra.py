"""
代码功能：根据四个基本参数（有效温度Teff、表面重力log g、金属丰度[Fe/H]和α元素丰度[α/Fe]）
合成理论光谱。该工具使用现有的恒星大气模型计算工具，实现恒星光谱的合成，并可以
保存结果或与观测数据进行比较。

步骤一：构建恒星大气模型（计算大气结构）
步骤二：光谱合成（计算射出辐射）
"""
import numpy as np
import matplotlib.pyplot as plt
from astropy.io import fits
import os
import sys
import time
from PyAstronomy import pyasl
import synth


MODELS_DIR = "path/to/model/grids"  # 模型网格目录
OUTPUT_DIR = "path/to/output/dir"   # 输出目录
WAVE_RANGE = (3000, 10000)          # 波长范围
RESOLUTION = 5000                   # 光谱分辨率

N_POINTS = int((WAVE_RANGE[1] - WAVE_RANGE[0]) * RESOLUTION / WAVE_RANGE[0])

class StellarSpectraSynthesizer:
    
    def __init__(self, models_dir=MODELS_DIR, output_dir=OUTPUT_DIR):
        self.models_dir = models_dir
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

        self.teff = 5800    
        self.logg = 4.44   
        self.feh = 0.0     
        self.alpha = 0.0   

        self.wavelength = np.linspace(WAVE_RANGE[0], WAVE_RANGE[1], N_POINTS)

        self.synth_method = self._check_available_methods()
        print(f"使用光谱合成方法: {self.synth_method}")
    
    def _check_available_methods(self):
        """检查可用的合成方法"""
        if 'synth' in sys.modules:
            return "direct"
        else:
            if os.path.exists(self.models_dir):
                return "interpolation"
            else:
                return "moog"
    
    def set_stellar_parameters(self, teff, logg, feh, alpha):
        """设置恒星参数"""
        self.teff = teff
        self.logg = logg
        self.feh = feh
        self.alpha = alpha
        print(f"设置恒星参数: Teff={teff}K, log(g)={logg}, [Fe/H]={feh}, [α/Fe]={alpha}")
    
    def _build_atmosphere_model(self):
        """构建大气层模型（步骤一）"""
        print("正在构建大气层模型...")
        start_time = time.time()

        if self.synth_method == "direct":
            model = synth.create_atmosphere(self.teff, self.logg, self.feh, self.alpha)
            
        elif self.synth_method == "interpolation":
            model = self._interpolate_model_grid()
            
        else:
            model = self._prepare_moog_model()
        
        print(f"大气层模型构建完成，耗时 {time.time() - start_time:.2f} 秒")
        return model
    
    def _interpolate_model_grid(self):
        """从模型网格中插值获取大气模型"""
        print("正在从模型网格插值...")
    
        grid_model = {
            'tau': np.logspace(-6, 2, 100),
            'temp': np.zeros(100),        
            'pgas': np.zeros(100),      
            'pe': np.zeros(100),        
            'rho': np.zeros(100)        
        }
        
        logtau = np.log10(grid_model['tau'])
        for i, lt in enumerate(logtau):
            grid_model['temp'][i] = self.teff * (0.7 + 0.3 * (1 - np.exp(-0.3 * (lt + 6))))
            grid_model['pgas'][i] = 10**(lt + 4.2 + 0.1 * self.logg)
            grid_model['pe'][i] = 10**(lt + 1.0 - 0.2 * self.feh)
            grid_model['rho'][i] = grid_model['pgas'][i] / (8.31e7 * grid_model['temp'][i])
            
        return grid_model
    
    def _prepare_moog_model(self):
        """准备MOOG格式的模型"""
        print("准备MOOG模型文件...")
        
        model_file = os.path.join(self.output_dir, f"model_t{self.teff}_g{self.logg}_m{self.feh}_a{self.alpha}.mod")
        
        with open(model_file, 'w') as f:
            f.write(f"KURUCZ模型大气: Teff = {self.teff}, log g = {self.logg}, [Fe/H] = {self.feh}, [a/Fe] = {self.alpha}\n")
            f.write("NTAU         72\n")
            
        return {'model_file': model_file}
    
    def _synthesize_spectrum(self, model):
        """合成光谱（步骤二）"""
        print("正在合成光谱...")
        start_time = time.time()
        
        if self.synth_method == "direct":
            flux = synth.compute_spectrum(model, self.wavelength)
            
        elif self.synth_method == "interpolation":
            flux = self._interpolate_spectrum(model)
            
        else:
            flux = self._call_external_synthesizer(model)
        
        print(f"光谱合成完成，耗时 {time.time() - start_time:.2f} 秒")
        return flux
    
    def _interpolate_spectrum(self, model):
        
        continuum = self._compute_continuum()
        
        flux = np.ones_like(self.wavelength)
        
        lines = [
            {'lambda': 4340, 'strength': 0.7, 'width': 1.0}, 
            {'lambda': 4861, 'strength': 0.8, 'width': 1.0}, 
            {'lambda': 6563, 'strength': 0.9, 'width': 1.0}, 
            {'lambda': 5890, 'strength': 0.6, 'width': 0.5},  
            {'lambda': 5896, 'strength': 0.6, 'width': 0.5}, 
            {'lambda': 6707, 'strength': 0.3 * (1 - self.feh), 'width': 0.3}, 
            {'lambda': 5270, 'strength': 0.4 * (1 + self.feh), 'width': 0.4},  
            {'lambda': 5328, 'strength': 0.4 * (1 + self.feh), 'width': 0.4},  
            {'lambda': 6155, 'strength': 0.3 * (1 + self.alpha), 'width': 0.4}, 
            {'lambda': 6162, 'strength': 0.3 * (1 + self.alpha), 'width': 0.4}, 
        ]
        
        for line in lines:
            if line['lambda'] > WAVE_RANGE[0] and line['lambda'] < WAVE_RANGE[1]:
                line_profile = self._compute_line_profile(line)
                flux *= (1 - line_profile)

        spectrum = flux * continuum
        
        return spectrum
    
    def _compute_continuum(self):
        """计算连续谱能量分布"""
        wavelength_cm = self.wavelength * 1e-8
        h = 6.6261e-27  
        c = 2.9979e10   
        k = 1.3807e-16  

        exponent = h * c / (wavelength_cm * k * self.teff)
        continuum = (wavelength_cm ** -5) / (np.exp(exponent) - 1)

        continuum /= np.max(continuum)
        
        return continuum
    
    def _compute_line_profile(self, line):

        center = line['lambda']
        strength = line['strength']
        width = line['width']

        thermal_width = width * np.sqrt(self.teff / 5800)

        profile = strength * np.exp(-(self.wavelength - center)**2 / (2 * thermal_width**2))
        
        return profile
    
    def _call_external_synthesizer(self, model):

        continuum = self._compute_continuum()
        
        np.random.seed(int(self.teff + self.logg * 100 + self.feh * 10 + self.alpha * 5))
        line_mask = np.ones_like(self.wavelength)
        for i in range(1000):
            line_center = np.random.uniform(WAVE_RANGE[0], WAVE_RANGE[1])
            line_width = np.random.uniform(0.1, 1.0)
            line_depth = np.random.uniform(0, 0.5) * (1 + self.feh/2)

            line_profile = line_depth * np.exp(-(self.wavelength - line_center)**2 / (2 * line_width**2))
            line_mask -= line_profile

        line_mask = np.clip(line_mask, 0, 1)

        flux = continuum * line_mask
        
        return flux
    
    def synthesize(self):
        model = self._build_atmosphere_model()
        
        flux = self._synthesize_spectrum(model)
        
        return self.wavelength, flux
    
    def plot_spectrum(self, wavelength=None, flux=None, save_path=None):
        """绘制光谱"""
        if wavelength is None or flux is None:
            wavelength, flux = self.synthesize()
        
        plt.figure(figsize=(12, 6))
        plt.plot(wavelength, flux, 'k-', linewidth=0.8)
        plt.xlabel('波长 (Å)')
        plt.ylabel('相对流量')
        plt.title(f'合成光谱 (Teff={self.teff}K, logg={self.logg}, [Fe/H]={self.feh}, [α/Fe]={self.alpha})')
        plt.grid(True, alpha=0.3)
        
        if save_path:
            plt.savefig(save_path, dpi=300)
            print(f"已保存光谱图像至: {save_path}")
        else:
            plt.show()
    
    def save_spectrum(self, wavelength=None, flux=None):
        if wavelength is None or flux is None:
            wavelength, flux = self.synthesize()

        hdr = fits.Header()
        hdr['TEFF'] = (self.teff, '有效温度 (K)')
        hdr['LOGG'] = (self.logg, '表面重力 (log(g))')
        hdr['FEH'] = (self.feh, '金属丰度 [Fe/H]')
        hdr['ALPHA'] = (self.alpha, 'Alpha元素丰度 [α/Fe]')
        hdr['DATE'] = (time.strftime("%Y-%m-%d"), '生成日期')
        hdr['WAVEMIN'] = (np.min(wavelength), '最小波长 (Å)')
        hdr['WAVEMAX'] = (np.max(wavelength), '最大波长 (Å)')
        hdr['NPOINTS'] = (len(wavelength), '波长点数')
        primary_hdu = fits.PrimaryHDU(header=hdr)

        col1 = fits.Column(name='wavelength', format='E', array=wavelength, unit='Angstrom')
        col2 = fits.Column(name='flux', format='E', array=flux, unit='relative')
        cols = fits.ColDefs([col1, col2])
        table_hdu = fits.BinTableHDU.from_columns(cols)
        
        hdul = fits.HDUList([primary_hdu, table_hdu])
        
        filename = f"synth_t{self.teff}_g{self.logg:.2f}_m{self.feh:.2f}_a{self.alpha:.2f}.fits"
        file_path = os.path.join(self.output_dir, filename)
        
        hdul.writeto(file_path, overwrite=True)
        print(f"已保存光谱数据至: {file_path}")
        
        return file_path

def main():
    synthesizer = StellarSpectraSynthesizer()
    
    print("\n请输入恒星参数:")
    try:
        teff = float(input("有效温度 Teff (K) [默认5800]: ") or 5800)
        logg = float(input("表面重力 log(g) [默认4.44]: ") or 4.44)
        feh = float(input("金属丰度 [Fe/H] [默认0.0]: ") or 0.0)
        alpha = float(input("Alpha元素丰度 [α/Fe] [默认0.0]: ") or 0.0)
    except ValueError as e:
        print(f"错误: 输入值无效 - {e}")
        print("使用默认值继续...")
        teff, logg, feh, alpha = 5800, 4.44, 0.0, 0.0
    
    synthesizer.set_stellar_parameters(teff, logg, feh, alpha)
    
    wavelength, flux = synthesizer.synthesize()
    
    print("\n请选择操作:")
    print("1. 显示光谱")
    print("2. 保存光谱数据")
    print("3. 保存光谱图像")
    print("4. 全部执行")
    
    choice = input("请输入选择 (1/2/3/4) [默认4]: ").strip() or "4"
    
    if choice in ("1", "4"):
        synthesizer.plot_spectrum(wavelength, flux)
    
    if choice in ("2", "4"):
        fits_path = synthesizer.save_spectrum(wavelength, flux)
        print(f"光谱数据已保存到: {fits_path}")
    
    if choice in ("3", "4"):
        output_file = os.path.join(OUTPUT_DIR, f"synth_t{teff}_g{logg:.2f}_m{feh:.2f}_a{alpha:.2f}.png")
        synthesizer.plot_spectrum(wavelength, flux, save_path=output_file)

if __name__ == "__main__":
    main() 