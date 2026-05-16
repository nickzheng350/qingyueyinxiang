# Hello World 示例插件

这是一个 HydraFlow AI 插件开发示例，演示如何创建自定义插件。

## 功能

- 提供 API 端点 `/api/v1/plugin/hello`
- 提供 CLI 命令 `hydraflow hello`
- 展示插件的基本结构和方法

## 使用方法

### API 调用

```bash
curl "http://localhost:8000/api/v1/plugin/hello?name=YourName"
```

### CLI 调用

```bash
python main.py hello --name YourName
```

## 结构说明

```
example_hello/
├── __init__.py      # 插件模块初始化
├── plugin.py        # 插件主类实现
└── README.md        # 插件文档
```
