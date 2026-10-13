# 齿轮箱寿命测试台

用于替换现有 LabVIEW 上位机的 PySide6 六工位齿轮箱寿命测试项目。当前提交是可交互的界面原型，默认使用模拟数据，不会连接或写入 PLC。

## 第一版界面

- 六个独立工位，按上三下三排列。
- 每个工位提供独立产品 SN 输入框，并显示转速、电流、压力、扭矩、3 路温度、运行时间和记录点数。
- 每个工位可设置目标转速、目标扭矩、压力补偿、温度上限和温度下限。
- 每个工位可独立启动、停止和写入界面参数，也支持全部启动、全部停止。
- 底部全程数据缩略图可按工位查看转速、电流、扭矩和最高温度趋势。
- 运行事件、告警状态和 CSV 写入数量会实时更新。
- `config/plc_addresses.json` 已按 `地址内容.xlsx` 整理六工位 PLC 地址。

## 长时间数据记录

- 采样数据由独立后台线程写入，不阻塞 Qt 界面。
- 一个程序运行周期建立一个测试会话目录，每个工位按本地日期分段保存 CSV。
- 默认每 5 秒刷新文件缓存，每 60 秒强制同步磁盘，停止程序时立即同步。
- 每条记录包含产品 SN、采样序号、时间戳、运行秒数、实时数据、设定参数、告警和数据质量。
- 界面趋势最多保留 20,000 个抽样点，秒级原始数据全部保存在 CSV 中。

数据目录结构：

```text
data/YYYYMMDD_HHMMSS/
├── test_info.json
├── events.csv
├── station_01/YYYY-MM-DD.csv
├── station_02/YYYY-MM-DD.csv
└── ...
```

## 运行

```bash
cd /Users/apple/PycharmProjects/gearbox_life_test
./.venv/bin/python main.py
```

## 说明

`ui/main.ui` 是 Qt Designer 源文件，`ui/ui_main.py` 由 `pyside6-uic` 生成，禁止手工修改。`ui/station_card.py` 实现六工位复用卡片，`ui/main_window.py` 负责界面装配和首版模拟交互。

PLC 通讯驱动仍处于占位状态。接入设备前需要确认 PLC 型号、通讯协议、IP/端口、字节序、REAL 数据格式和启停写入握手规则。

## 检查

```bash
./.venv/bin/python -m compileall -q main.py drivers models services ui utils workers tests
QT_QPA_PLATFORM=offscreen ./.venv/bin/python -m unittest discover -s tests -v
./.venv/bin/python -m pip check
```
