# ☯ 本地易经占卜 · Yijing Local Divination

纯本地运行的易经占卜技能。**不调用任何外部 API，不需要注册任何服务，零隐私风险。** 您的占卦问题只留在您自己的电脑上。

> 对比市面上需要 API Key、会把问题文本发送到第三方服务器的占卜技能——这个 skill 是另一个路数。

---

## 功能

- **年月日时起卦（推荐有时间场景）**：`meihua_time.py` 自动公历→农历，按梅花易数先天数法出本卦/变卦/体用
- **铜钱起卦**：模拟三枚铜钱六次投掷，自动区分老阴(6)/少阳(7)/少阴(8)/老阳(9)
- **数字起卦**：随口报三个数即可起卦
- **梅花易数其它起卦法**：物数、声音、字占、方位、颜色、动物、静物（见 `references/meihua-qigua.md`）
- **自动识别卦象**：六十四卦本卦 + 变卦 + 互卦，含二进制编码
- **384 爻辞完整收录**：按动爻自动引用对应爻辞
- **体用生克分析**：含四时旺衰、体党用党、互变卦判断
- **八卦万物类象**：每卦 20+ 维度（天时、地理、人物、身体、婚姻、求财、疾病……）
- **纳甲八宫基础**：世应、纳地支、装六亲、装六神
- **分类占断指南**：婚姻、求财、求名、疾病、官讼、出行、失物、行人、家宅、生产
- **应期判断**：含干支换算脚本，支持旬空、月破、合冲、入墓等应期规则

---

## 安装

### HanakoWorkSpace（Cursor / Claude 本机）

本仓库为 **唯一源**。HanakoWorkSpace 内已通过 junction 挂载：

| 路径 | 说明 |
|------|------|
| `skills/divination-skills/yijing-divination/` | **改这里** |
| `.agents/skills/yijing-divination/` | junction → 上 |
| `~/.claude/skills/yijing-divination/` | junction → 上（若已配置） |

### 其它机器

```bash
git clone https://github.com/beiguohongdou/divination-skills.git
# 将 yijing-divination/ 链到或复制到 Agent skills 目录
```

### 依赖

```bash
cd yijing-divination/scripts
pip install -r requirements.txt   # 安装 zhdate（年月日时起卦必需）
```

| 脚本 | 依赖 | 用途 |
|------|------|------|
| `meihua_time.py` | **zhdate** | 年月日时起卦（有时间必用） |
| `tongqian.py` | 无 | 铜钱法 |
| `ganzhi.py` | 无 | 应期判断 / 日干支 |

Windows 若 `python` 不可用，可试 `py -3 scripts/meihua_time.py ...`。

---

## 使用

### 对 AI 说

> 「7月4日早上6点阿根廷那场，帮我起一卦」

> 「帮我算一卦，最近工作能不能有突破」

AI 应自动触发此技能。**用户给出具体时刻时，Agent 必须运行 `meihua_time.py`，禁止心算或背固定年数。**

### 手动验算（对账用）

```bash
cd yijing-divination/scripts
python meihua_time.py 2026-07-04 06:00
python meihua_time.py --datetime "2026-07-04 06:00" --json
```

预期示例：`丙午年` → 年数 **7**（非公历 2026）→ 本卦 **地雷复**，变 **山雷颐**。

---

## Agent 执行纪律

1. **有时间** → 跑 `meihua_time.py`，把取数过程展示给用户
2. **报三数** → 数字法
3. **都没有** → 跑 `tongqian.py`
4. **年数随农历年变**，禁止硬编码「某公历年=某数」
5. **体用**：年月日时卦以脚本输出的体/用/生克为准；铜钱/数字卦按 `references/hexagrams.md` 体用生克节

---

## 数据来源

本技能的数据来自以下古籍典藏（luckclub.cn 整理，仅用于文化学习研究）：

- 《易经》（通行本王弼本）
- 《梅花易数》（邵雍）
- 《京氏易传》（京房）
- 《筮学指要》
- 《卜筮正宗》（王洪绪）
- 《增删卜易》（野鹤老人）
- 《断易天机》
- 《卜筮全书》

---

## 目录结构

```
yijing-divination/
├── SKILL.md                           # 主技能指令（Agent 必读）
├── README.md                          # 本文件
├── scripts/
│   ├── meihua_time.py                 # 年月日时起卦（有时间必用）
│   ├── tongqian.py                    # 铜钱法
│   ├── ganzhi.py                      # 干支 / 旬空 / 月建
│   └── requirements.txt               # zhdate
└── references/
    ├── hexagrams.md                   # 六十四卦速查表 + 体用生克详解
    ├── zhouyi-yaoci.md                # 384 爻辞速查
    ├── meihua-wanwu-leixiang.md       # 八卦万物属类（梅花易数）
    ├── meihua-qigua.md                # 梅花易数起卦法
    ├── najia-bagong.md                # 纳甲八宫基础（世应/六亲/六神）
    └── fenlei-zhangu.md               # 分类占断指南（11 类常见占问）
```

---

## 隐私

- ✅ 所有运算在本地完成
- ✅ 不发送任何数据到外部服务器
- ✅ 不需要注册任何账号
- ✅ 不需要 API Key
- ✅ 您的占卦问题只留在您的电脑上

---

## License

MIT
