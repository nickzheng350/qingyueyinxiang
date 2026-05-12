# HydraFlow AI 安全加固指南

## 安全架构概述

HydraFlow AI 采用多层安全防护体系，包括：
- **认证与授权**: JWT + OAuth2
- **输入验证**: 多层验证机制
- **速率限制**: 防止暴力破解和 DDoS
- **安全头**: 防止 XSS、CSRF、点击劫持等攻击
- **日志脱敏**: 防止敏感信息泄露

## 已实现的安全措施

### 1. 认证与授权

#### JWT 令牌
- 使用 HS256 算法签名
- 访问令牌有效期: 30 分钟
- 刷新令牌有效期: 7 天
- 密码使用 bcrypt 哈希（salt rounds = 12）

#### 角色权限
- `user`: 普通用户权限
- `admin`: 管理员权限

### 2. 输入验证

#### Pydantic 模型验证
```python
class ParseRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=10000)
    parser: str = Field(default="qwen2.5", max_length=100)
```

#### SQL 注入防护
- 使用 SQLAlchemy ORM 参数化查询
- 禁止字符串拼接 SQL

#### XSS 防护
- 输入验证中间件检测 XSS 模式
- 输出自动转义（FastAPI 默认）

### 3. 速率限制

| 端点类型 | 限制 |
|---------|------|
| 登录 | 10/分钟 |
| 注册 | 5/分钟 |
| API 调用 | 100/分钟 |
| 管理操作 | 10/分钟 |

### 4. 安全头

```http
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
X-XSS-Protection: 1; mode=block
Strict-Transport-Security: max-age=31536000; includeSubDomains
Referrer-Policy: strict-origin-when-cross-origin
Content-Security-Policy: default-src 'self'; ...
```

### 5. CORS 配置

```python
allow_origins=["http://localhost:3000"]  # 生产环境需限制
allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"]
allow_headers=["Content-Type", "Authorization", "X-CSRF-Token", "X-Request-ID"]
```

## 安全检查清单

### 部署前检查

- [ ] 所有 API 端点都有认证要求（除登录/注册）
- [ ] 管理操作需要管理员权限
- [ ] 速率限制已配置
- [ ] 安全头已启用
- [ ] CORS 已限制为已知域名
- [ ] .env 文件不在版本控制中
- [ ] JWT_SECRET_KEY 已更改为强随机密钥
- [ ] 数据库连接使用 SSL（生产环境）
- [ ] 日志不包含敏感信息
- [ ] 文件上传已限制类型和大小

### 定期检查

- [ ] 运行 `python scripts/security_check.py`
- [ ] 更新依赖项: `pip install --upgrade -r requirements.txt`
- [ ] 检查依赖漏洞: `pip-audit`
- [ ] 审查访问日志
- [ ] 检查异常登录尝试

## 已知风险与缓解措施

### 1. 依赖项漏洞

**风险**: 第三方库可能包含已知漏洞

**缓解措施**:
- 定期更新依赖项
- 使用 `pip-audit` 检查漏洞
- 锁定依赖版本

### 2. 暴力破解

**风险**: 攻击者尝试暴力破解密码

**缓解措施**:
- 登录速率限制: 10/分钟
- 密码复杂度要求: 最少 6 位
- 密码哈希: bcrypt (salt rounds = 12)

### 3. DDoS 攻击

**风险**: 大量请求导致服务不可用

**缓解措施**:
- 全局速率限制: 100/分钟
- 使用 Redis 作为限流存储
- 考虑使用 Cloudflare 或类似服务

### 4. 数据泄露

**风险**: 敏感数据意外泄露

**缓解措施**:
- 日志脱敏
- API 响应不包含敏感字段
- 数据库字段加密（如适用）
- 定期备份和加密

### 5. CSRF 攻击

**风险**: 跨站请求伪造

**缓解措施**:
- 使用 SameSite Cookie
- 验证 Origin 头
- 考虑实现 CSRF Token

## 安全最佳实践

### 开发阶段

1. **永远不要信任用户输入**
   - 在边界验证所有输入
   - 使用类型安全的验证器（Pydantic）
   - 不要依赖客户端验证

2. **最小权限原则**
   - 用户只能访问自己的资源
   - 管理操作需要管理员权限
   - 数据库连接使用最小权限

3. **安全编码**
   - 使用参数化查询
   - 避免使用 `eval()` 和 `exec()`
   - 不要硬编码密钥

### 部署阶段

1. **环境隔离**
   - 开发、测试、生产环境分离
   - 使用不同的数据库和密钥
   - 生产环境禁用 DEBUG 模式

2. **网络隔离**
   - 数据库不直接暴露到公网
   - 使用防火墙限制访问
   - 启用 HTTPS

3. **监控与日志**
   - 记录所有认证事件
   - 监控异常行为
   - 设置告警规则

### 运维阶段

1. **定期更新**
   - 操作系统补丁
   - 依赖项更新
   - 安全补丁

2. **备份与恢复**
   - 定期备份数据库
   - 测试恢复流程
   - 备份加密存储

3. **应急响应**
   - 制定安全事件响应计划
   - 定期演练
   - 建立联系机制

## 安全工具

### 代码审计

```bash
# 运行安全检查
python scripts/security_check.py

# 检查依赖漏洞
pip-audit

# 静态代码分析
bandit -r src/

# 类型检查
mypy src/
```

### 渗透测试

```bash
# 使用 OWASP ZAP
zap-baseline.py -t http://localhost:8000

# 使用 sqlmap
sqlmap -u "http://localhost:8000/api/v1/models?id=1"

# 使用 nikto
nikto -h http://localhost:8000
```

## 安全事件响应

### 发现安全漏洞

1. **立即隔离**
   - 停止受影响的服务
   - 保留日志和证据
   - 通知相关团队

2. **评估影响**
   - 确定漏洞范围
   - 评估数据泄露风险
   - 确定受影响用户

3. **修复漏洞**
   - 应用补丁
   - 更新配置
   - 测试修复

4. **通知用户**
   - 如有数据泄露，及时通知
   - 提供补救措施
   - 透明沟通

### 安全报告

如有安全漏洞发现，请通过以下方式报告：
- Email: security@hydraflow.ai
- GitHub Security Advisory

## 参考资料

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/)
- [Python Security Best Practices](https://python.readthedocs.io/en/stable/library/security_warnings.html)
- [CWE Top 25](https://cwe.mitre.org/top25/)
