# 个人每日自动看盘助手

一个本地可运行的自动看盘 MVP：读取股票池，获取行情，计算基础技术指标和风险信号，生成 JSON、Markdown 摘要和可离线打开的单文件 HTML 报告。配置 OpenAI 和新闻搜索 Key 后，会自动增加中文 AI 分析和新闻摘要。

> 本项目只做分析、提醒和辅助决策，不自动下单，不构成投资建议。

## 已实现范围

- Google Sheet CSV 导出读取，适合公开或当前运行环境可访问的 Sheet
- CSV 股票池读取仅作为显式开发/测试入口；正式运行要求 Google Sheet 可用
- 美股/港股优先使用 `yfinance`
- A 股优先使用 `akshare`，失败后尝试 Yahoo Finance 兼容代码
- Google Sheet 或行情源失败时直接报错，不生成假数据报告
- MA5 / MA10 / MA20 / MA60、5日/20日涨跌幅、RSI、放量判断
- 止损、止盈、均线、放量、近期高点等基础信号
- OpenAI 中文分析，未配置 Key 时使用本地规则分析
- Bing News 或 Google News RSS 新闻抓取，未配置时可跳过
- HTML 明细中显示新闻数量、新闻列表和新闻搜索入口
- `output/latest_report.json`
- `output/latest_summary.md`
- `output/latest_report.html`
- `reports/market_report_YYYYMMDD_HHMM.html`
- 单文件 HTML，可离线打开，支持搜索、筛选、展开详情、复制摘要、导出 JSON、打印
- GitHub Actions 定时运行和 GitHub Pages 发布目录
- 基础测试

## 安装

建议使用 Python 3.11+。

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

必须安装依赖后运行。系统不会使用本地假行情顶替真实数据。

## 配置

复制环境变量模板：

```bash
cp .env.example .env
```

真实 API Key 只写入 `.env` 或 GitHub Secrets，不要写进代码。

常用变量：

- `OPENAI_API_KEY`：启用 OpenAI 中文分析
- `BING_SEARCH_API_KEY`：启用 Bing News 搜索
- `GOOGLE_SHEET_ID`：启用 Google Sheet 股票池
- `GOOGLE_SHEET_GID`：Sheet gid，默认 `0`
- `REPORT_BASE_URL`：报告发布后的基础 URL，用于摘要里的完整报告链接

主配置在 `config/config.yaml`：

- `color_convention: CN` 表示红涨绿跌
- `privacy.hide_sensitive_fields` 控制 HTML/JSON 是否隐藏数量、成本、仓位
- `markets` 配置 A 股、港股、美股运行时间

## 股票池格式

正式运行默认读取 `.env` 中配置的 Google Sheet。`config/watchlist.sample.csv` 只用于开发/测试，字段：

```csv
market,ticker,name,type,cost,quantity,position_pct,take_profit,stop_loss,watch_reason,risk_level,enabled,notes
HK,1810.HK,小米集团,holding,27.8,1000,30,35,25.5,手机+汽车+AIoT,medium,true,长期关注
US,TTD,Trade Desk,holding,75,50,20,95,68,广告科技,high,true,波动较大
CN,002594.SZ,比亚迪,watchlist,,,,,,新能源车龙头,medium,true,只观察不持仓
```

代码格式：

- A 股：`002594.SZ`、`600519.SH`
- 港股：`1810.HK`
- 美股：`TTD`

## 本地运行

```bash
.venv/bin/python src/main.py --all --html --json
.venv/bin/python src/main.py --market HK
.venv/bin/python src/main.py --mode pre_close
.venv/bin/python src/main.py --no-ai
```

默认会抓取新闻。只有明确不需要新闻时才使用 `--no-news`。

生成文件：

- `output/latest_summary.md`
- `output/latest_report.json`
- `output/latest_report.html`
- `reports/market_report_YYYYMMDD_HHMM.html`
- `docs/latest_report.html`
- `docs/index.html`

`output/latest_report.html` 是单文件报告，可以直接双击或用浏览器离线打开。

## Google Sheet

第一版支持通过 Google Sheet 的 CSV 导出读取股票池。把 Sheet 设置为当前运行环境可访问，然后在 `.env` 配置：

```bash
GOOGLE_SHEET_ID=你的表格ID
GOOGLE_SHEET_GID=0
```

如果读取失败，系统会直接报错退出，不会回退到本地 CSV。

## GitHub Actions 和 Pages

已包含 `.github/workflows/market-watch.yml` 和 `docs/.nojekyll`。在 GitHub 仓库中配置：

- Secrets：`GOOGLE_SHEET_ID`、`GOOGLE_SHEET_GID`
- 可选 Secrets：`OPENAI_API_KEY`、`BING_SEARCH_API_KEY`
- 可选 Variables：`REPORT_BASE_URL`，例如 `https://你的用户名.github.io/仓库名`
- Pages Source 选择 GitHub Actions

如果没有设置 `REPORT_BASE_URL`，工作流会默认使用 `https://用户名.github.io/仓库名`。工作流会在北京时间大约 10:30、13:45、14:00 对应的 UTC 时间运行，并把 `docs/` 发布到 GitHub Pages。发布后打开：

```text
https://你的用户名.github.io/仓库名/latest_report.html
```

## 测试

```bash
python -m pytest
```

没有安装 `pytest` 时，也可以先直接运行主程序验证输出：

```bash
python src/main.py --all --no-ai --no-news --html --json
```

## 常见问题

**没有 OpenAI 或新闻 API Key 能跑吗？**  
能。会跳过 AI 或新闻增强，但 Google Sheet 和真实行情源必须可用。

**为什么报告提示“行情源不可用”？**  
现在不会用假数据继续生成报告。若 `yfinance/akshare`、网络、代码格式或数据源异常，程序会直接报错，需要先修正问题再生成报告。

**HTML 是否依赖后端？**  
不依赖。CSS、JavaScript、报告 JSON 都内嵌在一个 HTML 文件里。

**是否会隐藏真实持仓？**  
默认 `hide_sensitive_fields: true` 且隐藏 `quantity`。成本价和仓位百分比可在 `config/config.yaml` 调整。

## 免责声明

本系统生成的所有内容仅用于个人看盘辅助，不构成投资建议或收益承诺。市场有风险，所有交易决策与后果由使用者自行承担。
