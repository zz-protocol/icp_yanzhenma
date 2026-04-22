# ICP 备案查询 API

一个基于 Python FastAPI 的 ICP 备案信息查询系统，支持自动验证码识别与 ICP 项目查询。

## 功能特性

✨ **核心功能**
- 自动获取阿里云/电信/联通 ICP 备案查询 Token
- 自动识别滑块验证码
- 自动计算滑块缺口偏移量
- 查询单个域名的 ICP 备案信息

🚀 **技术栈**
- FastAPI - Web 框架
- Requests - HTTP 客户端
- OpenCV + NumPy - 图像处理
- Pydantic - 数据验证

## 系统要求

- Python 3.9+
- Windows/Linux/macOS

## 快速开始

### 1. 环境准备

```bash
# 克隆或下载项目
cd D:\h5\icp_yanzhenma_huadong
```

### 2. 安装依赖

```bash
# 使用 pip 安装
pip install -r requirements.txt
```

### 3. 启动服务

```bash
# 方式一：使用批处理脚本
run.bat

# 方式二：直接使用 Python
python web.py
```

### 4. 访问 API

- **健康检查**：http://127.0.0.1:8000/health
- **查询接口**：http://127.0.0.1:8000/query?domain=qq.com
- **接口文档**：http://127.0.0.1:8000/doc

## API 文档

### 1. 查询域名 ICP 备案信息

**接口地址**：`GET /query`

**请求参数**：

| 参数 | 类型 | 必填 | 说明 | 示例 |
|------|------|------|------|------|
| domain | string | ✅ | 要查询的域名 | qq.com |

**请求示例**：

```bash
curl "http://127.0.0.1:8000/query?domain=qq.com"
```

**成功响应（200 OK）**：

```json
{
  "status": "success",
  "domain": "qq.com",
  "error": null,
  "company_name": "深圳市腾讯计算机系统有限公司",
  "licenceno": "粤B2-20090059",
  "nature": "企业",
  "data": {
    "code": 200,
    "msg": "操作成功",
    "success": true,
    "params": {
      "list": [{
        "domain": "qq.com",
        "unitName": "深圳市腾讯计算机系统有限公司",
        "mainLicence": "粤B2-20090059",
        "natureName": "企业",
        "updateRecordTime": "2026-01-15 11:27:48"
      }],
      "total": 1
    }
  }
}
```

### 2. 健康检查

**接口地址**：`GET /health`

**响应示例**：

```json
{
  "status": "healthy",
  "timestamp": 1775123412,
  "service": "ICP 备名查询系统"
}
```

## 使用示例

### Python 调用

```python
import requests

def query_icp(domain):
    """查询 ICP 备案信息"""
    url = "http://127.0.0.1:8000/query"
    params = {"domain": domain}

    response = requests.get(url, params=params)
    result = response.json()

    if result["status"] == "success":
        print(f"公司名: {result['company_name']}")
        print(f"备案号: {result['licenceno']}")
        print(f"性质: {result['nature']}")

        detail = result['data']['params']['list'][0]
        print(f"\\n详细信息: {detail}")
    else:
        print(f"查询失败: {result['error']}")

# 查询示例
query_icp("qq.com")
query_icp("baidu.com")
query_icp("google.com")
```

### cURL 调用

```bash
# 查询 qq.com
curl "http://127.0.0.1:8000/query?domain=qq.com"

# 查询 baidu.com
curl "http://127.0.0.1:8000/query?domain=baidu.com"
```

### Postman 调用

1. 新建 GET 请求
2. URL: `http://127.0.0.1:8000/query`
3. 传参：`domain = qq.com`
4. 点击 Send

## 项目结构

```
icp_yanzhenma_huadong/
├── test.py              # 核心查询逻辑（263行）
├── web.py               # FastAPI 服务（112行）
├── requirements.txt     # 依赖列表
├── run.bat              # Windows 启动脚本
└── README.md            # 项目文档（本文件）
```

## 数据结构

### 核心查询流程

```
1. auth()                      # 获取认证 Token
         ↓
2. get_check_image()          # 获取验证码图片
         ↓
3. match_slider_offset()      # 计算滑块偏移
         ↓
4. checkImage()               # 验证签名
         ↓
5. query_icp_info()           # 查询 ICP
```

### 响应数据结构

| 字段 | 类型 | 说明 |
|------|------|------|
| status | string | 查询状态: success/failed |
| domain | string | 查询域名 |
| company_name | string | 公司名称 |
| licenceno | string | 备案号 |
| nature | string | 企业性质 |
| data | object | 完整的 API 响应数据 |

## 常见问题

### 1. 启动失败：端口被占用

**错误信息**：`Error while attempting to bind on address ('127.0.0.1', 8000)`

**解决方案**：
```bash
# Windows: 查找并杀掉占用进程
netstat -ano | findstr :8000
taskkill //F //PID <PID号>

# 重新启动
python web.py
```

### 2. 查询失败：超时

**错误信息**：`HTTPSConnectionPool... Read timed out`

**解决方案**：检查网络连接，或等待服务端响应

### 3. 403 Forbidden

**错误信息**：`403 Client Error: Forbidden`

**可能原因**：
- 验证码计算失败
- Token 过期
- IP 被限制

## 依赖说明

### 核心依赖

| 依赖包 | 版本 | 用途 |
|--------|------|------|
| requests | >=2.31.0 | HTTP 请求 |
| cryptography | >=42.0.5 | 数据加密 |
| numpy | >=1.26.4 | 数值计算 |
| opencv-python | >=4.10.0.84 | 图像处理 |
| fastapi | >=0.104.0 | Web 框架（仅 Web 使用） |
| uvicorn | >=0.24.0 | ASGI 服务器（仅 Web 使用） |

## 注意事项

1. **时效性**：미IT 官网的反爬虫机制可能会更新，需要定期维护
2. **频率限制**：建议每次查询间隔至少 2 秒，避免请求过快
3. **合法性**：仅用于合法的 ICP 备案查询目的
4. **隐私保护**：查询结果包含企业信息，请勿滥用或泄露

## 更新日志

### v2.0 (2026-04-02)
- ✅ 优化代码结构，移除冗余功能
- ✅ 改进错误处理和日志系统
- ✅ 添加 Pydantic 数据验证
- ✅ 提供 Swagger 文档
- ✅ 支持 60 秒超时

### v1.0
- ✅ 基础查询功能
- ✅ 自动验证码识别

## 许可证

MIT License

## 作者

OpenCode

## 联系方式

如有问题，请联系项目维护者或提交 Issue。

---

**免责声明**：本项目仅供学习交流使用，请勿用于非法用途。使用者需自行承担使用本项目产生的一切法律责任。