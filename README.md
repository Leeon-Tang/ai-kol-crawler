# AI KOL 爬虫系统

YouTube AI领域KOL自动发现与分析系统

**⚠️ 免责声明：本项目仅供学习和研究使用，请遵守YouTube服务条款和相关法律法规。**

---

## 项目说明

本项目是一个用于发现和分析YouTube AI领域KOL的自动化工具，帮助研究人员和内容创作者：
- 发现AI相关的优质频道
- 分析频道的内容质量和活跃度
- 追踪AI领域的内容趋势

**使用限制：**
- ✅ 个人学习和研究
- ✅ 数据分析和学术研究
- ✅ 内容创作参考
- ❌ 商业用途（需遵守YouTube API条款）
- ❌ 大规模爬取（请遵守速率限制）
- ❌ 骚扰、垃圾邮件或恶意用途

---

## 🚀 快速开始

### Windows用户

**双击运行 `autostart-windows.bat`**

首次运行会自动：
- 下载便携式Python（约15MB）
- 创建虚拟环境
- 安装所有依赖
- 启动Web界面

**无需手动安装Python！**

---

### Windows用户（已安装Python）

如果你已经安装了Python 3.8+：

**双击运行 `start-windows.bat`**

---

### Mac/Linux用户

1. 打开终端，进入项目目录
2. 运行启动脚本：

```bash
chmod +x autostart-mac-linux.sh
./autostart-mac-linux.sh
```

**需要Python 3.8+**

如未安装Python：
- Mac: `brew install python3`
- Ubuntu: `sudo apt-get install python3 python3-pip python3-venv`

**说明：** Mac和Linux都使用 `.sh` 脚本文件（Shell脚本），这是Unix系统的标准脚本格式

---

## 📖 使用说明

### 启动后

浏览器会自动打开 `http://localhost:8501`

如果端口被占用，系统会自动尝试8502-8510端口

### 功能页面

1. **📊 数据看板** - 查看统计数据和KOL列表
2. **🎮 爬虫控制** - 启动/停止爬虫，查看运行状态
3. **📁 数据浏览** - 浏览和导出KOL数据
4. **📋 日志查看** - 实时查看系统日志
5. **🎯 AI规则** - 配置AI相关度和关键词规则
6. **⚙️ 系统设置** - 配置搜索关键词和导出选项

### 首次使用

1. 进入 **🎯 AI规则** 页面，配置：
   - AI相关度阈值（推荐30-50%）
   - 高/中/低优先级关键词
   - 排除规则

2. 进入 **⚙️ 系统设置** 页面，配置：
   - 搜索关键词（每行一个）
   - 导出选项

3. 进入 **🎮 爬虫控制** 页面，点击"启动爬虫"

4. 系统会自动跳转到 **📋 日志查看** 页面，实时显示爬虫进度

---

## 🔧 技术说明

### 数据库

使用SQLite数据库，数据文件位于 `data/ai_kol_crawler.db`

无需安装PostgreSQL或Docker

### 日志

日志文件位于 `logs/` 目录，按日期命名

### 导出

导出的Excel文件位于 `exports/` 目录

---

## ❓ 常见问题

### 端口被占用

系统会自动尝试8501-8510端口，如果全部被占用：
1. 关闭其他占用端口的程序
2. 重启电脑
3. 重新运行启动脚本

### Windows: 下载Python失败

如果自动下载失败：
1. 访问 https://www.python.org/downloads/
2. 下载 "Windows embeddable package (64-bit)"
3. 解压到项目的 `python-portable` 目录
4. 重新运行 `scripts-windows/启动爬虫.bat`

### Mac/Linux: Python版本过低

确保Python版本 >= 3.8：
```bash
python3 --version
```

如果版本过低，请升级Python

### 依赖安装失败

手动安装依赖：
```bash
# Windows
venv\Scripts\pip.exe install -r requirements.txt

# Mac/Linux
source venv/bin/activate
pip install -r requirements.txt
```

---

## 📝 项目结构

```
ai-kol-crawler/
├── app.py                      # Streamlit Web界面
├── main.py                     # 命令行入口
├── backup_daily.py             # 备份逻辑（Python脚本）
├── requirements.txt            # Python依赖
├── scripts-windows/            # Windows脚本
│   ├── 启动爬虫.bat            # 一键启动（零配置）
│   └── 每日备份.bat            # 数据备份
├── scripts-mac-linux/          # Mac/Linux脚本
│   ├── 启动爬虫.sh             # 一键启动
│   └── 每日备份.sh             # 数据备份
├── automation/                 # 自动化工具（可选）
├── config/                     # 配置文件
├── core/                       # 核心功能模块
├── storage/                    # 数据库模块
├── tasks/                      # 任务模块
├── utils/                      # 工具模块
├── data/                       # 数据库文件（主数据库）
├── logs/                       # 日志文件
├── exports/                    # 导出文件
└── backups/                    # 每日备份（自动创建）
    └── YYYYMMDD/               # 按日期分类
        ├── daily_data_YYYYMMDD.db    # 当天数据
        ├── YYYYMMDD.log              # 当天日志
        └── full_database_backup.db   # 完整数据库备份
```

---

## 🔒 数据备份

### 自动备份（推荐）

**每天运行一次备份脚本：**

Windows:
```bash
双击 scripts-windows/每日备份.bat
```

Mac/Linux:
```bash
chmod +x scripts-mac-linux/每日备份.sh
./scripts-mac-linux/每日备份.sh
```

### 备份内容

1. **当天数据** - 只包含今天新增的KOL和视频
2. **日志文件** - 今天和昨天的日志
3. **完整数据库** - 所有历史数据的完整备份

### 备份位置

```
backups/
├── 20260122/
│   ├── daily_data_20260122.db      # 今天的数据
│   ├── 20260122.log                # 今天的日志
│   └── full_database_backup.db     # 完整备份
├── 20260123/
│   └── ...
```

### 自动清理

备份脚本会自动删除7天前的旧备份，节省空间。

---

## 🛠️ 开发说明

### 手动运行

```bash
# 激活虚拟环境
# Windows
venv\Scripts\activate

# Mac/Linux
source venv/bin/activate

# 启动Web界面
streamlit run app.py

# 或使用命令行
python main.py
```

### 配置文件

配置文件位于 `config/config.json`，包含：
- 搜索关键词
- AI相关度阈值
- 关键词匹配规则
- 排除规则
- 导出选项

---

## 📄 许可证

本项目采用 MIT License 开源协议。

**重要提示：**
- 本软件仅供教育和研究目的使用
- 用户需自行承担使用本软件的责任
- 请遵守YouTube服务条款和相关法律法规
- 作者不对软件的滥用承担任何责任

详见 [LICENSE](LICENSE) 文件。

---

## 🤝 贡献

欢迎提交Issue和Pull Request！

---

## 📧 联系方式

如有问题或建议，请通过GitHub Issues联系。

---

**再次提醒：请合法合规使用本工具，尊重数据来源平台的规则和他人的权益。**
