# 三式占卜 Skills

梅花易数/六爻、大六壬、奇门遁甲 三套 AI Agent 占卜技能。

**远程仓库**：<https://github.com/beiguohongdou/divination-skills>（分支 `master`）

## 包含

| Skill | 体系 | 参考文件 |
|-------|------|---------|
| `yijing-divination` | 梅花易数 + 六爻 | 9+（卦辞爻辞、纳甲八宫、万物类象、meihua_time 等） |
| `daliuren-divination` | 大六壬神课 | 7 个（毕法赋、邵公断案、天地盘等） |
| `qimen-dunjia` | 奇门遁甲 | 7 个（十干克应、八门九星、格局克应等） |

## HanakoWorkSpace 唯一源

| 线 | 本地目录 | 说明 |
|----|----------|------|
| 源 | `skills/divination-skills/` | **只在这里改** |
| Cursor | `.agents/skills/yijing-divination/` 等 | junction → 源 |
| Claude | `~/.claude/skills/yijing-divination/` 等 | junction → 源（本机已配） |

与 `AI伴侣` / `ai-chat` **完全分离**，占卜改动勿提交到 ai-chat 仓库。

## 安装（其它机器）

```bash
git clone https://github.com/beiguohongdou/divination-skills.git
cd divination-skills/yijing-divination/scripts && pip install -r requirements.txt
```

将三个 skill 目录放到 Agent 的 skills 路径，或建 junction 指向本仓库。

## 三端同步核对清单

改完 skill 后按此检查，确保 Cursor / Claude / Hanako 算法一致：

- [ ] 改动在 `skills/divination-skills/` 内完成（非 ai-chat 根仓库）
- [ ] `git push origin master` 已推到 GitHub
- [ ] `.agents/skills/yijing-divination` 为 junction，目标为 `skills/divination-skills/yijing-divination`
- [ ] `~/.claude/skills/yijing-divination` 同上（或其它机器 pull 后重建 junction）
- [ ] 验算：`python scripts/meihua_time.py 2026-07-04 06:00` → 本卦 **地雷复**，年数 **7**（丙午，非公历2026）
- [ ] 三端各问同一时间，卦名与取数过程一致

## 易经起卦要点（2026-06 更新）

- 用户给**具体时间** → `yijing-divination/scripts/meihua_time.py`
- 要**六爻装卦** → `liuyao_pan.py`
- **大六壬** → `daliuren-divination/scripts/daliuren_pan.py`
- **奇门定局** → `qimen-dunjia/scripts/qimen_pan.py`
- Windows 优先 **`py -3`**；年数随农历年自动变

## 数据来源

古籍原文来自 [luckclub.cn](https://www.luckclub.cn)，PDF 仅供文化学习研究。

## License

MIT
