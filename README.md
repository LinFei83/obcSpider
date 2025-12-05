# obcSpider

米游社语音爬虫，可自动爬取原神和星穹铁道角色的语音文本、wav链接等信息。支持多语言。

## 安装依赖

```bash
pip install -r requirements.txt
```

注意: `pydub` 需要系统安装 FFmpeg。

## 使用

### 基础爬虫

`class ObcSpider` 是一个可枚举对象。可以直接使用`for`循环遍历：

```python
for (name, summary, cid, lines) in ObcSpider(configuration_key='honkai:_star_rail', lang_id=0, include=['彦卿']):
    print(f"{name} - {summary}")
    for (title, line, audio_url) in lines:
        print(f"\t{title} - {line}: {audio_url}")
```

- `configuration_key`，必填，表示获取哪个游戏。只有 `honkai:_star_rail` 和 `genshin_impact` 两个选择。默认为 `genshin_impact`。
- `lang_id`：语言编号，从0到3分别为 `['汉语', '日语', '韩语', '英语']`。
- `exclude`：排除的角色名。
- `include`：包含的角色名。和 `exclude` 同时指定时，该项优先级更高。即结果中将首先包含 `include` 有的项，然后再去掉 `exclude` 排除的项。

除此以外，也可以直接执行 `obcSpider.py` 脚本，它会以人类可读的方式直接输出所有找到的角色名、角色简介、语音台词和语音wav地址。

---

### 数据集构建器

`dataset_builder.py` 可以自动下载语音并生成训练用数据集。

```python
from dataset_builder import DatasetBuilder

builder = DatasetBuilder(output_dir='dataset', sample_rate=22500)
builder.build(
    configuration_key='genshin_impact',
    lang_id=0,  # 0=中文, 1=日语, 2=韩语, 3=英语
    include=['钟离', '甘雨']  # 指定角色，None表示全部
)
```

#### 参数说明

- `output_dir`: 输出目录，默认 `dataset`
- `sample_rate`: 音频采样率，默认 22500Hz
- `max_workers`: 并行下载线程数，默认 4

#### 输出格式

每个角色会生成一个独立文件夹，包含：

```
dataset/
├── 钟离/
│   ├── 钟离.csv
│   ├── ZL00000.wav
│   ├── ZL00001.wav
│   └── ...
└── 甘雨/
    ├── 甘雨.csv
    ├── GY00000.wav
    └── ...
```

CSV 文件格式（`|`分隔）：

```
ZL00000.wav|天之痕。
ZL00001.wav|持起红缨枪，追赶对方半公里。
```

- 文件名格式：`{角色拼音首字母大写}{5位编号}.wav`
- CSV 中 `|` 前为文件名，`|` 后为语音文本内容
