# AI KOL爬虫项目 - 完整上下文

## 项目概述

这是一个用于发现和分析AI领域KOL（意见领袖）的自动化爬虫系统，目标是找到合适的KOL进行推广合作。

### 核心目标
- 从YouTube等平台抓取AI相关内容创作者
- 分析其内容的AI相关度
- 筛选出符合标准的KOL
- 导出数据用于合作评估

---

## 技术架构

### 技术栈
- **语言**: Python 3.12
- **爬虫**: yt-dlp (非官方，无API限制)
- **数据库**: PostgreSQL (Docker容器)
- **导出**: openpyxl (Excel)

### 项目结构
```
ai-kol-crawler/
├── config/
│   └── config.json              # 统一配置文件
├── core/
│   ├── scraper.py              # yt-dlp爬虫封装
│   ├── searcher.py             # 关键词搜索
│   ├── analyzer.py             # KOL分析
│   ├── expander.py             # 扩散发现
│   └── filter.py               # 过滤筛选
├── storage/
│   ├── database.py             # PostgreSQL连接
│   ├── models.py               # 数据模型
│   └── kol_repository.py       # 数据访问层
├── tasks/
│   ├── discovery_task.py       # 发现任务
│   ├── expand_task.py          # 扩散任务
│   ├── update_task.py          # 更新任务
│   └── export_task.py          # 导出任务
├── utils/
│   ├── logger.py               # 彩色日志系统
│   ├── text_matcher.py         # 关键词匹配
│   ├── exclusion_rules.py      # 排除规则
│   ├── rate_limiter.py         # 频率控制
│   └── retry.py                # 重试机制
└── main.py                     # 主入口
```

---

## 当前配置

### 爬取参数 (config.json)
```json
{
  "crawler": {
    "ai_ratio_threshold": 0.3,           // AI内容占比阈值 (30%)
    "sample_video_count": 10,            // 每个频道分析10个视频
    "search_results_per_keyword": 5,     // 每个关键词搜索5个视频
    "expand_batch_size": 3,              // 每次扩散3个KOL
    "max_qualified_kols": 1000,          // 最大KOL数量
    "rate_limit_delay": 2,               // 请求间隔2秒
    "max_retries": 3,                    // 最多重试3次
    "active_days_threshold": 90,         // 活跃度阈值90天
    "socket_timeout": 10-15              // 网络超时10-15秒
  }
}
```

### 当前测试配置
- **关键词数量**: 2个 (随机选择)
- **每个关键词**: 5个视频
- **总搜索**: 2 × 5 = 10个视频
- **预计频道**: 5-10个
- **每频道分析**: 10个视频
- **预计时间**: 2-3分钟

---

## AI判断逻辑

### 判断依据
检查视频的**标题**和**描述**中是否包含预定义的AI关键词。

### 匹配规则
1. 不区分大小写
2. 支持部分匹配
3. 标题和描述都检查
4. 只要有一个关键词匹配就判定为AI相关

### 关键词库 (约45个)

**高优先级** (最新AI工具):
- Sora AI, Sora
- Kling AI, Kling
- Veo
- Runway Gen-3, Runway
- AI video generation, AI video tutorial, AI video
- Seedance

**中优先级** (主流AI工具):
- ChatGPT, GPT-4, GPT
- Claude AI, Claude
- Gemini
- Midjourney, Stable Diffusion, DALL-E
- AI image, AI tools, AI tutorial
- Pika AI, Pika
- AI lipsync, lipsync, lip sync
- wan

**低优先级** (技术术语):
- AI workflow, ComfyUI, LoRA training
- AI automation, generative AI
- Hugging Face, Leonardo AI, Flux AI
- ControlNet, AI music, AI voice
- LLM, Diffusion Model, AI agent
- text to video, text to image, image to video
- video generation, image generation
- AI model, AI training

### 匹配示例
```
标题: "Kling O1 Tutorial: AI Video Tips"
匹配: Kling, AI video → ✓ AI相关

标题: "AI lipsync with Sync..."
匹配: lipsync → ✓ AI相关

标题: "Cooking Tutorial"
匹配: 无 → ✗ 非AI内容
```

---

## 排除规则

### 自动排除的内容类型

**课程/教学频道**:
- 关键词: 第、講、课、lecture、lesson、导论、教程、系列课

**学术机构**:
- 关键词: university、大学、college、学院、institute、研究所

**新闻媒体**:
- 关键词: news、新闻、media、媒体、報導

### 排除逻辑
- 检查频道名称
- 检查视频标题模式
- 如果60%以上视频包含课程关键词 → 排除

---

## 数据库结构

### 表1: kols (KOL主表)
```sql
- channel_id (频道ID)
- channel_name (频道名称)
- channel_url (频道链接)
- subscribers (订阅数)
- total_videos (总视频数)
- analyzed_videos (已分析视频数)
- ai_videos (AI相关视频数)
- ai_ratio (AI内容占比)
- avg_views (平均观看数)
- avg_likes (平均点赞数)
- engagement_rate (互动率)
- last_video_date (最后视频日期)
- days_since_last_video (距今天数)
- status (qualified/pending/rejected)
- discovered_from (发现来源)
- discovered_at (发现时间)
```

### 表2: videos (视频表)
```sql
- video_id (视频ID)
- channel_id (所属频道)
- title (标题)
- description (描述)
- published_at (发布时间)
- views (观看数)
- likes (点赞数)
- comments (评论数)
- is_ai_related (是否AI相关)
- matched_keywords (匹配的关键词)
- video_url (视频链接)
```

### 表3: expansion_queue (扩散队列)
```sql
- channel_id (待扩散的频道)
- priority (优先级)
- status (pending/processing/completed)
```

---

## 工作流程

### 1. 初始发现 (关键词搜索)
```
随机选择2个关键词
  ↓
每个关键词搜索5个视频
  ↓
提取频道ID (去重)
  ↓
分析每个频道 (10个视频)
  ↓
计算AI占比
  ↓
≥30% → 合格 → 加入扩散队列
<30% → 不合格
```

### 2. 扩散发现 (推荐列表)
```
从扩散队列取出KOL
  ↓
获取其视频的推荐列表
  ↓
提取新频道
  ↓
分析新频道
  ↓
筛选入库
```

### 3. 持续扩散
```
循环执行扩散任务
  ↓
直到达到1000个合格KOL
  ↓
或扩散队列为空
```

---

## 日志系统

### 彩色日志
- **INFO** - 绿色 (正常信息)
- **WARNING** - 黄色 (警告)
- **ERROR** - 红色 (错误)

### 日志格式
```
======================================================================
开始分析频道: UCxxx
======================================================================

▶ 阶段 1/3: 获取频道基本信息
----------------------------------------------------------------------
  频道名称: AI Tutorial Channel
  订阅数: 125,000
  视频数: 500
  链接: https://www.youtube.com/channel/UCxxx

▶ 阶段 2/3: 获取视频列表 (最多10个)
----------------------------------------------------------------------
  成功获取 10 个视频

▶ 阶段 3/3: 分析视频内容
----------------------------------------------------------------------
  视频 1/10 ✓ AI相关
    标题: Sora AI Tutorial...
    匹配关键词: Sora, AI video
    数据: 观看 10,000 | 点赞 500
    链接: https://www.youtube.com/watch?v=xxx

  视频 2/10 ✗ 非AI内容
    标题: Cooking Tutorial...
    原因: 标题和描述中未找到AI关键词
    数据: 观看 5,000 | 点赞 200
    链接: https://www.youtube.com/watch?v=yyy

  统计: 成功 10 | AI相关 4 | 非AI 6 | 失败 0

======================================================================
分析结果
======================================================================
  频道: AI Tutorial Channel
  分析视频: 10 | AI视频: 4 | AI占比: 40.0%
  平均观看: 7,500 | 平均点赞: 350 | 互动率: 4.67%
  最后更新: 5天前 | 状态: ✓ 合格 (阈值: 30%)
======================================================================
```

---

## 使用方法

### 环境准备
```bash
# 1. 启动数据库
docker start ai-kol-postgres

# 2. 激活虚拟环境
cd ai-kol-crawler
.\venv\Scripts\activate
```

### 运行爬虫
```bash
# 方法1: 快速测试 (2个关键词)
python quick_test.py

# 方法2: 主程序
python main.py
# 选择 1 (初始发现)，输入 2 (使用2个关键词)
```

### 查看数据
```bash
# 方法1: 主程序查看统计
python main.py
# 选择 7 (查看统计)

# 方法2: 查看脚本
python view_data.py

# 方法3: 直接查询数据库
docker exec -it ai-kol-postgres psql -U postgres -d ai_kol_crawler
SELECT channel_name, ai_ratio, subscribers FROM kols WHERE status='qualified';
\q
```

### 导出Excel
```bash
# 方法1: 主程序
python main.py
# 选择 6 (导出Excel)

# 方法2: 查看脚本
python view_data.py
# 选择 1 (导出Excel)

# 文件位置: exports/kol_report_YYYYMMDD_HHMMSS.xlsx
```

---

## 常见问题

### 1. 超时卡住
- 已添加10-15秒超时机制
- 超时后自动重试3次
- 失败后跳过继续下一个

### 2. 会员专属视频
- 自动检测并跳过
- 日志显示: ⚠ 获取失败 | 原因: 会员专属视频

### 3. 误判AI内容
- 查看日志中的视频链接
- 确认标题是否包含AI关键词
- 如果需要，添加新关键词到 `config.json`

### 4. 课程频道被收录
- 检查排除规则是否生效
- 可以在 `config.json` 的 `exclusion_rules` 中添加关键词

---

## 性能指标

### 当前配置下的预期
- **搜索阶段**: 10个视频，约30秒
- **分析阶段**: 5-10个频道 × 10个视频 = 50-100个视频，约2-3分钟
- **预计找到**: 2-4个合格KOL
- **数据量**: 约50-100个视频元数据 (10-25 MB)

### 扩大规模
- 10个关键词 × 30个视频 = 约100个频道
- 预计时间: 1-2小时
- 预计找到: 20-40个合格KOL

---

## 配置调整

### 提高质量
```json
{
  "ai_ratio_threshold": 0.5  // 提高到50%
}
```

### 加快速度
```json
{
  "sample_video_count": 5,   // 减少分析视频数
  "rate_limit_delay": 1       // 降低延迟 (有风险)
}
```

### 扩大规模
```json
{
  "search_results_per_keyword": 30,  // 增加搜索结果
  "sample_video_count": 30           // 增加分析视频数
}
```

---

## 数据库管理

### Docker命令
```bash
# 查看容器状态
docker ps

# 启动数据库
docker start ai-kol-postgres

# 停止数据库
docker stop ai-kol-postgres

# 重启数据库
docker restart ai-kol-postgres

# 查看日志
docker logs ai-kol-postgres

# 进入数据库
docker exec -it ai-kol-postgres psql -U postgres -d ai_kol_crawler
```

### 数据库连接信息
```
Host: localhost
Port: 5432
Database: ai_kol_crawler
User: postgres
Password: mypassword123
```

---

## 文件说明

### 核心文档
- `README.md` - 项目说明
- `PROJECT_CONTEXT.md` - 本文件，完整上下文
- `USAGE_GUIDE.md` - 使用指南
- `AI_DETECTION_LOGIC.md` - AI判断逻辑说明
- `KEYWORD_MATCHING.md` - 关键词匹配说明
- `TROUBLESHOOTING.md` - 故障排除

### 配置文件
- `config/config.json` - 统一配置文件
- `.env.example` - 环境变量示例

### 测试脚本
- `quick_test.py` - 快速测试 (2个关键词)
- `test_db.py` - 测试数据库连接
- `test_scraper.py` - 测试爬虫功能
- `view_data.py` - 查看和导出数据

---

## 下一步计划

### 短期
- [ ] 优化关键词库 (根据实际运行结果)
- [ ] 完善排除规则 (减少误判)
- [ ] 添加更多平台 (X, Reddit等)

### 长期
- [ ] 实现自动化定时爬取
- [ ] 添加Web界面
- [ ] 使用AI模型进行内容分类
- [ ] 添加KOL联系方式提取

---

## 注意事项

1. **网络要求**: 需要能访问YouTube
2. **频率控制**: 默认2秒间隔，避免被封禁
3. **数据备份**: 定期备份PostgreSQL数据库
4. **合规性**: 仅用于个人研究，不公开分享数据
5. **持续优化**: 根据实际结果调整关键词和阈值

---

**最后更新**: 2026-01-20
**版本**: 1.0
**状态**: 测试运行中
