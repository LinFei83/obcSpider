"""
角色语音数据集生成器
基于obcSpider爬取的语音数据，生成训练用数据集
"""

import os
import csv
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
from pydub import AudioSegment
from pypinyin import lazy_pinyin

from obcSpider import ObcSpider


def get_pinyin_abbr(name: str) -> str:
    """获取角色名的拼音首字母缩写(大写)"""
    return ''.join([p[0].upper() for p in lazy_pinyin(name)])


def download_audio(url: str, save_path: Path, sample_rate: int = 22500) -> bool:
    """下载音频并转换为指定采样率的wav格式"""
    if url is None:
        return False
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        # 临时保存原始文件
        temp_path = save_path.with_suffix('.tmp')
        temp_path.write_bytes(response.content)
        
        # 转换为wav格式并设置采样率
        audio = AudioSegment.from_file(temp_path)
        audio = audio.set_frame_rate(sample_rate)
        audio.export(save_path, format='wav')
        
        temp_path.unlink()  # 删除临时文件
        return True
    except Exception as e:
        print(f"  下载失败 {url}: {e}")
        return False


class DatasetBuilder:
    """角色语音数据集构建器"""
    
    def __init__(self, output_dir: str = 'dataset', sample_rate: int = 22500, max_workers: int = 4):
        self.output_dir = Path(output_dir)
        self.sample_rate = sample_rate
        self.max_workers = max_workers
    
    def build_character_dataset(self, name: str, lines: list) -> int:
        """为单个角色构建数据集，返回成功处理的语音数量"""
        if not lines:
            print(f"  {name}: 无语音数据")
            return 0
        
        # 创建角色文件夹
        char_dir = self.output_dir / name
        char_dir.mkdir(parents=True, exist_ok=True)
        
        # 生成拼音缩写前缀
        prefix = get_pinyin_abbr(name)
        
        # 准备下载任务
        tasks = []
        for idx, (title, text, audio_url) in enumerate(lines):
            if text is None:
                continue
            # 去除文本中的换行符
            text = text.replace('\n', '').replace('\r', '')
            filename = f"{prefix}{idx:05d}.wav"
            filepath = char_dir / filename
            tasks.append({
                'filename': filename,
                'filepath': filepath,
                'text': text,
                'audio_url': audio_url,
                'title': title
            })
        
        # 并行下载音频
        success_items = []
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_map = {
                executor.submit(download_audio, t['audio_url'], t['filepath'], self.sample_rate): t
                for t in tasks
            }
            for future in as_completed(future_map):
                task = future_map[future]
                if future.result():
                    success_items.append(task)
        
        # 按文件名排序后写入CSV
        success_items.sort(key=lambda x: x['filename'])
        csv_path = char_dir / f"{name}.csv"
        with open(csv_path, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f, delimiter='|', quoting=csv.QUOTE_NONE, escapechar='\\')
            for item in success_items:
                writer.writerow([item['filename'], item['text']])
        
        print(f"  {name}: 成功 {len(success_items)}/{len(tasks)} 条")
        return len(success_items)
    
    def build(self, configuration_key: str = 'genshin_impact', lang_id: int = 0,
              include: list = None, exclude: list = None):
        """构建完整数据集"""
        print(f"开始构建数据集: {configuration_key}, 语言ID: {lang_id}")
        
        spider = ObcSpider(
            configuration_key=configuration_key,
            lang_id=lang_id,
            include=include,
            exclude=exclude
        )
        
        total = 0
        for name, summary, cid, lines in spider:
            print(f"\n处理角色: {name}")
            total += self.build_character_dataset(name, lines)
        
        print(f"\n完成! 共处理 {total} 条语音")


if __name__ == '__main__':
    # 示例: 构建钟离的中文语音数据集
    builder = DatasetBuilder(output_dir='dataset', sample_rate=22500)
    builder.build(
        configuration_key='genshin_impact',
        lang_id=0,  # 0=中文, 1=日语, 2=韩语, 3=英语
        include=['钟离']  # 指定角色，None表示全部
    )

