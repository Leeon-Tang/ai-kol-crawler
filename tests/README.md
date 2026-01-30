# 测试文档

## 测试结构

```
tests/
├── __init__.py              # 测试模块初始化
├── conftest.py              # Pytest配置和fixtures
├── run_all_tests.py         # 运行所有测试的主文件
├── test_storage.py          # 存储模块测试
├── test_platforms.py        # 平台模块测试
├── test_tasks.py            # 任务模块测试
├── test_utils.py            # 工具模块测试
├── test_ui.py               # UI模块测试
└── test_integration.py      # 集成测试
```

## 运行测试

### 运行所有测试
```bash
python tests/run_all_tests.py
```

或使用pytest:
```bash
pytest tests/ -v
```

### 运行特定测试文件
```bash
pytest tests/test_storage.py -v
pytest tests/test_platforms.py -v
pytest tests/test_tasks.py -v
```

### 运行特定测试函数
```bash
pytest tests/test_storage.py::test_database_connection -v
```

## 测试覆盖

### 存储模块 (test_storage.py)
- 数据库连接测试
- GitHub仓库CRUD操作
- GitHub学术仓库操作
- Twitter仓库操作
- 数据库迁移测试

### 平台模块 (test_platforms.py)
- 平台工厂测试
- GitHub爬虫、搜索器、分析器
- Twitter爬虫、搜索器、分析器

### 任务模块 (test_tasks.py)
- GitHub发现任务
- GitHub导出功能
- GitHub学术人士导出
- Twitter发现任务
- Twitter导出功能

### 工具模块 (test_utils.py)
- 配置加载器
- 日志记录器
- 爬虫状态管理
- 速率限制器
- 重试装饰器
- 文本匹配器
- 联系方式提取器
- 排除规则

### UI模块 (test_ui.py)
- UI模块导入测试
- 文本常量测试
- 仪表盘函数测试

### 集成测试 (test_integration.py)
- GitHub完整工作流程
- Twitter完整工作流程
- 配置到数据库流程
- 备份工作流程

## 测试要求

### 依赖安装
```bash
pip install pytest pytest-cov
```

### 测试数据
测试使用临时数据库和文件，不会影响生产数据。

## 注意事项

1. UI测试需要Streamlit环境，部分测试仅验证导入
2. 平台爬虫测试不进行实际网络请求
3. 所有测试使用临时目录和数据库
4. 测试完成后自动清理临时文件
