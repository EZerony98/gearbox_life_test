# 齿轮箱寿命测试台

用于替换现有 LabVIEW 上位机的 PySide6 六工位齿轮箱寿命测试项目。程序按真实设备模式运行，通过 FINS/UDP 连接欧姆龙 PLC；未连接时界面明确显示断线状态，不生成任何模拟测量数据。

## 第一版界面

- 六个独立工位，按上三下三排列。
- 每个工位提供独立产品 SN 输入框，并显示实时转速、实时电流（mA）、实时压力、实时扭矩、电机温度、齿轮箱温度、制动器温度、运行时间和记录点数。
- 每个工位可设置目标转速、目标扭矩、压力补偿、温度上限和温度下限。
- 每个工位可独立切换使能、向 PLC 写入参数、启动、暂停/继续和停止，也支持全部启动、全部停止；暂停期间停止该工位的测试与 CSV 记录，继续后随 PLC 运行反馈恢复记录，停止成功后清空该工位产品 SN。
- 底部全程数据缩略图可按工位查看转速、电流、扭矩和最高温度趋势。
- 运行事件、告警状态和 CSV 写入数量会实时更新。
- `config/plc_addresses.json` 已按 `地址内容.xlsx` 整理六工位 PLC 地址。
- `config/devices.json` 配置 PLC IP、FINS 节点、轮询周期、REAL 字序和写入脉冲时间。
- 顶部显示用户提供的品牌 LOGO，界面采用深色设备栏、品牌红和状态色体系。

## 长时间数据记录

- 采样数据由独立后台线程写入，不阻塞 Qt 界面。
- 一个程序运行周期建立一个测试会话目录，每个工位按本地日期分段保存 CSV。
- 默认每 5 秒刷新文件缓存，每 60 秒强制同步磁盘，停止程序时立即同步。
- 只有 PLC 已连接且对应工位反馈为运行状态时才记录样本；每条记录的数据质量固定标记为 `PLC`。
- PLC 实时界面默认每 250 ms 刷新，CSV 按工位限速为最快每秒一条，两种节拍互不影响。
- 实时转速使用各工位 REAL 转速地址（1 号工位为 `%D3724`），整数转速通道不再作为界面实时值。
- 每条记录包含产品 SN、采样序号、时间戳、运行秒数、实时数据、设定参数和告警。
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

`ui/main.ui` 是 Qt Designer 源文件，`ui/ui_main.py` 由 `pyside6-uic` 生成，禁止手工修改。`ui/station_card.py` 实现六工位复用卡片，`ui/main_window.py` 负责界面装配、真实数据呈现和后台服务连接。

当前驱动按欧姆龙 FINS/UDP、DM 区字地址 `0x82`、位地址 `0x02` 实现。上线联调时应根据现场 PLC 工程确认 `config/devices.json` 中的目标节点、源节点自动推导结果、REAL 字序及参数写入脉冲时长；这些设置不正确时程序保持“PLC 未连接”或报告 FINS 结束码，不会回退到假数据。

暂停和停止都通过地址表中的工位 `start_stop` 位向 PLC 写入 `False`；继续写入 `True`。两者在上位机中的区别是：暂停保留产品 SN 与测试上下文以便恢复，停止会结束该工位本次操作并清空产品 SN。地址表未声明电流缩放倍率，当前按现场旧界面量级将 PLC 电流 REAL 原值解释为 mA，不额外乘以 1000。

## 检查

```bash
./.venv/bin/python -m compileall -q main.py drivers models services ui utils workers tests
QT_QPA_PLATFORM=offscreen ./.venv/bin/python -m unittest discover -s tests -v
./.venv/bin/python -m pip check
```
