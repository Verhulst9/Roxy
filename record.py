import numpy as np

# 修复 numpy 2.0 与 soundcard 的兼容性问题
# soundcard 使用了已移除的 numpy.fromstring 二进制模式
if hasattr(np, 'fromstring'):
    _original_fromstring = np.fromstring
    def _fromstring_compat(string, dtype=float, count=-1, sep=''):
        if sep == '':
            # 如果 sep 为空，说明是二进制模式，转发给 frombuffer
            return np.frombuffer(string, dtype=dtype, count=count)
        return _original_fromstring(string, dtype=dtype, count=count, sep=sep)
    np.fromstring = _fromstring_compat

import soundcard as sc
import soundfile as sf

# 设置录制时长（秒）
DURATION = 10 
OUTPUT_FILE = "dataset_sample.wav"
SAMPLE_RATE = 44100

print("正在寻找默认扬声器...")
# 获取默认扬声器的 Loopback（内录）
# include_loopback=True 是关键
default_speaker = sc.default_speaker()
mic = sc.get_microphone(id=default_speaker.id, include_loopback=True)

print(f"开始录制 {DURATION} 秒系统音频...")
with mic.recorder(samplerate=SAMPLE_RATE) as recorder:
    # 录制数据
    data = recorder.record(numframes=SAMPLE_RATE * DURATION)
    
    # 保存为文件
    sf.write(file=OUTPUT_FILE, data=data, samplerate=SAMPLE_RATE)
    print(f"录制完成！已保存为 {OUTPUT_FILE}")