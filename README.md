# AI KOL 爬虫系统 v2.0

多平台内容创作者和开发者发现系统

**支持平台：**
- 🎥 **YouTube**: AI领域KOL（意见领袖）
- 💻 **GitHub**: 独立开发者
- 🔮 **可扩展**: 支持添加更多平台

**⚠️ 免责声明：本项目仅供学习和研究使用，请遵守各平台服务条款和相关法律法规。**

---

## 🆕 v2.0 新特性

- ✅ **多平台支持**: 统一界面管理YouTube和GitHub数据
- ✅ **一键切换**: 在界面顶部轻松切换平台
- ✅ **自动迁移**: 自动检测并迁移旧版数据，无需手动操作
- ✅ **数据安全**: 旧数据保留作为备份，零风险升级
- ✅ **可扩展架构**: 轻松添加新平台

---

## 项目说明

本项目是一个多平台爬虫系统，用于发现和分析不同平台的内容创作者和开发者：

### YouTube平台
- 发现AI相关的优质频道
- 分析频道的内容质量和活跃度
- 追踪AI领域的内容趋势
- 通过关键词搜索和扩散发现

### GitHub平台
- 发现独立开发者
- 分析开发者的项目质量
- 识别AI/ML领域的技术专家
- 通过关键词、Awesome列表、Explore发现

**使用限制：**
- ✅ 个人学习和研究
- ✅ 数据分析和学术研究
- ✅ 内容创作参考
- ❌ 商业用途（需遵守平台API条款）
- ❌ 大规模爬取（请遵守速率限制）
- ❌ 骚扰、垃圾邮件或恶意用途

---

## 🚀 快速开始

### 重要提示：自动升级
如果你之前使用过旧版本，**无需担心数据丢失**！
- ✅ 系统会自动检测并迁移旧数据
- ✅ 旧数据会保留作为备份
- ✅ 迁移过程完全自动，无需手动操作

---

### Windows用户

#### 第一步：双击启动脚本

找到项目文件夹中的 `scripts-windows` 文件夹，双击运行：

```
scripts-windows/启动爬虫.bat
```

**首次运行会自动完成以下操作（需要3-5分钟）：**
- ✅ 下载便携式Python（约15MB）
- ✅ 创建虚拟环境
- ✅ 安装所有依赖包
- ✅ 创建配置文件
- ✅ 初始化数据库
- ✅ **自动迁移旧数据**（如果存在）
- ✅ 启动Web界面

**无需手动安装Python！无需任何配置！**

#### 第二步：等待浏览器自动打开

启动脚本会自动打开浏览器，访问 `http://localhost:8501`

如果浏览器没有自动打开，请手动访问上述地址

#### 第三步：选择平台并开始使用

在Web界面中：
1. 在顶部选择平台（YouTube 或 GitHub）
2. 点击左侧菜单 **🎮 爬虫控制**
3. 配置并启动爬虫任务
4. 在 **📊 仪表盘** 查看数据

**完成！现在爬虫已经开始工作了！**

---

### Mac/Linux用户

#### 第一步：打开终端

在项目文件夹中右键，选择"在终端中打开"

#### 第二步：运行启动脚本

```bash
chmod +x scripts-mac-linux/启动爬虫.sh
./scripts-mac-linux/启动爬虫.sh
```

**需要Python 3.8+**

如未安装Python：
- Mac: `brew install python3`
- Ubuntu: `sudo apt-get install python3 python3-pip python3-venv`

#### 第三步：等待浏览器自动打开

启动脚本会自动打开浏览器，访问 `http://localhost:8501`

#### 第四步：选择平台并开始使用

在Web界面中：
1. 在顶部选择平台（YouTube 或 GitHub）
2. 点击左侧菜单 **🎮 爬虫控制**
3. 配置并启动爬虫任务
4. 在 **📊 仪表盘** 查看数据

**完成！现在爬虫已经开始工作了！**

---

## 📖 使用说明

### Web界面功能

启动后，你会看到以下页面：

#### 平台选择
- 在界面顶部选择 **YouTube** 或 **GitHub**
- 所有数据和功能会根据选择的平台自动切换

#### 1. 📊 数据看板
- 查看已发现的KOL/开发者总数
- 查看合格数量和待分析数量
- 查看最近发现的列表
- 实时统计数据

#### 2. 🎮 爬虫控制
**YouTube平台**：
- 初始发现：通过关键词搜索发现新KOL
- 扩散发现：从已有KOL的推荐列表中发现

**GitHub平台**：
- 关键词搜索：通过技术关键词发现开发者
- Awesome列表：从awesome项目中发现贡献者
- Explore发现：从trending项目中发现

#### 3. 📁 数据浏览
- 浏览所有已发现的数据
- 按状态、质量等筛选
- 导出Excel报告
- 下载CSV数据

#### 4. 📋 日志查看
- 实时查看爬虫运行状态
- 查看详细的抓取日志
- 自动刷新功能
- 清空日志功能

---

## 🎯 首次使用建议

### YouTube平台
1. 在顶部选择 **YouTube**
2. 进入 **🎮 爬虫控制**
3. 选择 **5个关键词**（首次建议从小规模开始）
4. 点击 **▶️ 开始初始发现**
5. 等待5-10分钟
6. 在 **📊 仪表盘** 查看结果

### GitHub平台
1. 在顶部选择 **GitHub**
2. 进入 **🎮 爬虫控制**
3. 选择搜索策略（关键词/Awesome/Explore）
4. 点击开始搜索
5. 等待2-5分钟
6. 在 **📊 仪表盘** 查看结果

---

## 🔧 技术说明

### 数据库
- **类型**: SQLite（轻量级，无需安装）
- **位置**: `data/ai_kol_crawler.db`
- **表结构**: 
  - YouTube: `youtube_kols`, `youtube_videos`, `youtube_expansion_queue`
  - GitHub: `github_developers`, `github_repositories`

### 日志
- **位置**: `logs/` 目录
- **命名**: 按日期命名（如 `20260123.log`）

### 导出
- **位置**: `exports/` 目录
- **格式**: Excel (.xlsx) 和 CSV
- **命名**: 
  - YouTube: `kol_report_YYYYMMDD_HHMMSS.xlsx`
  - GitHub: `github_developers_YYYYMMDD_HHMMSS.xlsx`

### 配置文件
- **位置**: `config/config.json`
- **自动创建**: 首次启动时从 `config.example.json` 自动创建
- **不会上传**: `.gitignore` 已配置，你的自定义配置不会被上传到Git

---

## ❓ 常见问题

### 启动相关

**Q: 双击启动脚本后，窗口一闪而过？**

A: 右键点击启动脚本，选择"编辑"查看错误信息，或在命令行中运行查看详细错误。

**Q: 浏览器没有自动打开？**

A: 手动打开浏览器，访问 `http://localhost:8501`

**Q: 提示"端口被占用"？**

A: 系统会自动尝试8501-8510端口。如果全部被占用，关闭其他占用端口的程序或重启电脑。

### 数据迁移

**Q: 我的旧数据会丢失吗？**

A: 不会。系统会自动迁移旧数据到新表，旧表会保留作为备份。

**Q: 如何确认数据迁移成功？**

A: 
1. 查看日志文件 `logs/YYYYMMDD.log`，搜索"迁移"
2. 在界面中查看数据统计是否正确
3. 在 **📊 仪表盘** 中查看是否有数据显示

**Q: 可以删除旧表吗？**

A: 建议运行新系统1-2周后，确认一切正常再手动删除旧表。

### 平台切换

**Q: 如何切换平台？**

A: 在界面顶部点击 **YouTube** 或 **GitHub** 按钮即可切换。

**Q: 两个平台的数据会混在一起吗？**

A: 不会。每个平台有独立的数据表，互不影响。

### 运行相关

**Q: 爬取速度很慢？**

A: 这是正常的，因为：
- 每次请求之间有2秒延迟（避免被封禁）
- 每个频道/开发者需要分析多个视频/仓库
- 5个关键词大约需要5-10分钟

**Q: 找到的数据很少？**

A: 可能的原因：
- 关键词数量太少（建议至少5个）
- 筛选标准过于严格
- 检查配置文件中的阈值设置

### 依赖安装

**Q: Windows下载Python失败？**

A: 
1. 访问 https://www.python.org/downloads/
2. 下载 "Windows embeddable package (64-bit)"
3. 解压到项目的 `python-portable` 目录
4. 重新运行启动脚本

**Q: Mac/Linux提示Python版本过低？**

A: 确保Python版本 >= 3.8：
```bash
python3 --version
```
如果版本过低，请升级Python。

**Q: 依赖安装失败？**

A: 手动安装依赖：
```bash
# Windows
venv\Scripts\pip.exe install -r requirements.txt

# Mac/Linux
source venv/bin/activate
pip install -r requirements.txt
```

---

## 数据备份

### 为什么要备份？

- 保护你辛苦爬取的数据
- 防止意外删除或损坏
- 记录每天的爬取进度

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

## 📝 项目结构

```
ai-kol-crawler/
├── app.py                      # Streamlit Web界面（主入口）
├── main.py                     # 命令行入口（可选）
├── backup_daily.py             # 备份脚本
├── requirements.txt            # Python依赖
│
├── platforms/                  # 平台模块
│   ├── youtube/                # YouTube平台实现
│   │   ├── scraper.py          # YouTube爬虫
│   │   ├── searcher.py         # 搜索策略
│   │   ├── analyzer.py         # KOL分析
│   │   ├── expander.py         # 扩散发现
│   │   └── filter.py           # 过滤筛选
│   └── github/                 # GitHub平台实现
│       ├── scraper.py          # GitHub API爬虫
│       ├── searcher.py         # 搜索策略
│       └── analyzer.py         # 开发者分析
│
├── storage/                    # 数据层
│   ├── database.py             # 统一数据库管理
│   ├── repositories/           # 数据访问层
│   │   ├── youtube_repository.py
│   │   └── github_repository.py
│   └── migrations/             # 数据迁移
│       └── migration_v2.py     # v1->v2迁移脚本
│
├── tasks/                      # 任务层
│   ├── youtube/                # YouTube任务
│   │   ├── discovery.py        # 初始发现
│   │   ├── expand.py           # 扩散发现
│   │   ├── update.py           # 更新任务
│   │   └── export.py           # 导出任务
│   └── github/                 # GitHub任务
│       ├── discovery.py        # 开发者发现
│       └── export.py           # 导出任务
│
├── utils/                      # 工具模块（共享）
│   ├── logger.py               # 日志系统
│   ├── config_loader.py        # 配置加载
│   ├── rate_limiter.py         # 频率限制
│   ├── retry.py                # 重试机制
│   └── contact_extractor.py    # 联系方式提取
│
├── config/                     # 配置文件
│   ├── config.json             # 主配置（自动创建）
│   └── config.example.json     # 配置模板
│
├── scripts-windows/            # Windows脚本
│   ├── 启动爬虫.bat
│   └── 每日备份.bat
│
├── scripts-mac-linux/          # Mac/Linux脚本
│   ├── 启动爬虫.sh
│   └── 每日备份.sh
│
├── data/                       # 数据目录（自动创建）
│   └── ai_kol_crawler.db       # SQLite数据库
│
├── logs/                       # 日志目录（自动创建）
│   └── YYYYMMDD.log
│
├── exports/                    # 导出目录（自动创建）
│   ├── kol_report_*.xlsx       # YouTube导出
│   └── github_developers_*.xlsx # GitHub导出
│
└── backups/                    # 备份目录（自动创建）
    └── YYYYMMDD/
```

### 架构说明

**多平台设计**：
- `platforms/` 目录包含所有平台的实现
- 每个平台实现统一的接口
- 数据库表按平台分离（`youtube_*`, `github_*`）
- 任务按平台分离，互不影响

**可扩展性**：
添加新平台只需：
1. 在 `platforms/` 下创建新目录
2. 实现平台接口
3. 在数据库中添加对应表
4. 创建对应的任务模块
5. 在界面中添加支持

**代码复用**：
- `utils/` 中的工具模块被所有平台共享
- 日志、配置、限流等功能统一管理

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

1. **当天数据** - 只包含今天新增的数据
2. **日志文件** - 今天和昨天的日志
3. **完整数据库** - 所有历史数据的完整备份

### 备份位置

```
backups/YYYYMMDD/
├── daily_data_YYYYMMDD.db      # 今天的数据
├── YYYYMMDD.log                # 今天的日志
└── full_database_backup.db     # 完整备份
```

备份脚本会自动删除7天前的旧备份，节省空间。

---

## 💡 使用技巧

### 1. 从小规模开始
- 首次使用建议5个关键词
- 观察结果质量
- 逐步扩大规模

### 2. 定期备份数据
- 建议每天运行一次备份脚本
- 保护你辛苦爬取的数据

### 3. 查看日志排查问题
- 如果遇到问题，查看日志文件
- 日志位置：`logs/YYYYMMDD.log`

### 4. 导出数据分析
- 定期导出Excel报告
- 分析数据质量
- 筛选合适的合作对象

### 5. 平台切换
- 在界面顶部轻松切换平台
- 每个平台独立管理
- 数据互不影响

---

## 📄 许可证

本项目采用 MIT License 开源协议。

**重要提示：**
- 本软件仅供教育和研究目的使用
- 用户需自行承担使用本软件的责任
- 请遵守各平台服务条款和相关法律法规
- 作者不对软件的滥用承担任何责任

详见 [LICENSE](LICENSE) 文件。

---

## 🤝 贡献与反馈

### 遇到问题？

1. 查看本README的"常见问题"部分
2. 查看日志文件排查错误
3. 通过GitHub Issues反馈问题

### 想要改进？

欢迎提交Pull Request！

---

## � 联系方式

如有问题或建议，请通过GitHub Issues联系。

---

**再次提醒：请合法合规使用本工具，尊重数据来源平台的规则和他人的权益。**
