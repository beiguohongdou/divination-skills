# 三式占卜 Skills

面向 AI Agent（Cursor / Claude Code 等）的三套传统术数排盘与辅助解读技能：

| 目录 | 体系 | 说明 |
|------|------|------|
| [`yijing-divination`](./yijing-divination/) | 梅花易数 + 六爻 | 时间起卦、铜钱/数字法、六爻装卦 |
| [`daliuren-divination`](./daliuren-divination/) | 大六壬 | 天地盘、四课三传、天将神煞 |
| [`qimen-dunjia`](./qimen-dunjia/) | 奇门遁甲 | 定局排盘、三奇六仪、八门九星 |

各技能的触发条件、工作流与规则索引见对应目录下的 `SKILL.md`。排盘逻辑以各目录的 `scripts/` 为准；条文与断法摘录在 `references/`。

---

## 快速开始

### 1. 克隆

```bash
git clone https://github.com/beiguohongdou/divination-skills.git
cd divination-skills
```

### 2. 安装 Python 依赖

建议 Python 3.10+。当前仓库中依赖声明位于易经脚本目录（节气/农历等为共用能力）：

```bash
pip install -r yijing-divination/scripts/requirements.txt
```

Windows 也可使用：

```bash
py -3 -m pip install -r yijing-divination/scripts/requirements.txt
```

### 3. 接入 Agent

将三个 skill 目录放到所用 Agent 的 skills 搜索路径（名称保持不变），例如：

- Cursor：项目或用户级 skills 目录  
- Claude Code：`~/.claude/skills/`  

也可使用目录联接（junction / symlink）指向本仓库中的对应子目录，避免复制多份。

### 4. 命令行自检（可选）

在已安装依赖的环境下，可直接调用脚本做排盘验算，例如：

```bash
# 梅花：指定时间起卦（示例）
py -3 yijing-divination/scripts/meihua_time.py 2026-07-04 06:00

# 六爻装卦、大六壬、奇门等见各目录 scripts/ 与 SKILL.md
```

仓库根目录另有 `verify-three-endpoints.py`，用于一次性抽检多条固定锚点（维护与回归用）。

---

## 目录说明

| 路径 | 用途 |
|------|------|
| `*/SKILL.md` | Agent 技能说明（必读入口） |
| `*/scripts/` | 起卦 / 起课 / 排盘可执行脚本 |
| `*/references/` | 整理后的规则与断法摘录 |
| `卦理日志/` | 起卦会话落盘与摘要工具；本地 `records/` 默认不进入版本库 |

`卦理日志/records/` 仅保存在本机，用于个人占问记录；克隆仓库后首次起卦时可能自动创建。

---

## 能力边界（请先阅读）

- 本仓库提供的是 **排盘与规则辅助**，不是完整代替人工的「权威断事系统」。  
- 部分特殊课体或流派细则在实现上有意简化或需人工核对（例如大六壬涉害深度、部分课体三传专法、奇门置闰细调等）。以各 `SKILL.md` 与脚本输出中的标注为准。  
- 古籍流派众多，本仓库在文档中择一口径实现；若与你所宗派别不同，请以你的师承/原书为准，并自行调整 `references/` 与脚本。  
- 输出仅供传统文化学习与研究，**不构成**医疗、法律、投资或人生决策建议。

---

## 数据与引用

- Agent 运行时应以本仓库内的 **`references/` + `scripts/`** 为准。  
- `references/` 为便于检索而整理的摘录与结构化说明，可能与纸质原书排版、个别用字不完全一致；遇关键争议请核对原书。  
- 内容用于文化学习研究；请勿将本仓库表述为任何第三方网站或出版方的官方镜像。

---

## License

[MIT](./LICENSE)
