# ICP 备案查询 API — 协议逆向与验证码对抗实践

<div align="center">

![Python](https://img.shields.io/badge/Python-3.9+-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-2.0-009688?logo=fastapi&logoColor=white)
![NumPy](https://img.shields.io/badge/NumPy-向量化算法-013243?logo=numpy&logoColor=white)
![Crypto](https://img.shields.io/badge/AES--ECB-加密通信-6B4C9A)

**对工信部 ICP 备案查询接口的完整逆向实现:签名算法还原 → 滑块验证码 CV 识别 → 加密参数构造 → 服务化封装**

</div>

> ⚠️ **免责声明**:本项目仅用于安全研究与学习交流,演示 Web 协议分析与验证码对抗技术。请遵守《网络安全法》等相关法规,勿用于任何违规用途,并对目标系统保持合理的请求频率。

> ✅ **可用性验证**:2026-08 在干净虚拟环境中全链路实测通过(token 获取 → 缺口识别 offset=318 → 签名换取 → 加密查询返回正确备案数据)。

## 🔍 逆向技术链

对 `beian.miit.gov.cn` 查询流程的完整还原,每一步都是手工分析协议所得:

```
① 签名算法逆向        authKey = md5(salt + timestamp)   ← 还原接口鉴权规则
        ↓
② 验证码图像获取      背景大图 + 滑块小图 (base64)       ← 会话级 uuid 绑定
        ↓
③ 缺口偏移识别        NumPy 向量化颜色量化匹配           ← 核心算法,见下文
        ↓
④ 验证提交            偏移量校验通过 → 换取增强签名 Sign
        ↓
⑤ 加密参数构造        AES-ECB + 自定义 padding 构造请求
        ↓
⑥ 查询请求            Sign/Uuid/Token/Cookie 多重凭据协同
        ↓
⑦ FastAPI 服务化     封装为 HTTP API,一条命令查询任意域名
```

## 🧮 核心算法:滑块缺口识别

不依赖第三方打码平台,纯本地计算:

1. **降采样**:背景图 `[::2, ::2]` 减半,平衡精度与速度
2. **颜色量化**:`(pixel // 4) * 4` 抑制噪声,相近颜色归簇
3. **色彩编码**:RGB 三通道编码为单一整数 id(`R + G×256 + B×65536`)
4. **频次统计**:`np.unique` 统计各颜色簇频次 —— 缺口区域因阴影/蒙层形成独立的低频色块
5. **偏移定位**:结合滑块尺寸约束,锁定缺口 x 偏移

全程 NumPy 向量化,无逐像素循环。

## 🚀 快速开始

```bash
pip install -r requirements.txt
python web.py          # 或 run.bat
```

```bash
# 查询任意域名备案信息
curl "http://127.0.0.1:8000/query?domain=qq.com"
```

## 📡 API

| 端点 | 说明 |
|---|---|
| `GET /query?domain=` | 查询域名 ICP 备案信息(主办单位/备案号/企业性质) |
| `GET /auth` | 独立获取认证 token(调试用) |
| `GET /health` | 健康检查 |

## 📁 项目结构

```
icp_yanzhenma/
├── test.py           # 核心逆向逻辑:签名/验证码/AES/查询全链路
├── web.py            # FastAPI 服务封装
├── requirements.txt
└── run.bat / install.bat
```

## 🛠 技术栈

Python · FastAPI · Requests · NumPy · Pillow · cryptography(AES) · hashlib(MD5)

## License

MIT License
