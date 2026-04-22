from fastapi import FastAPI, Query, HTTPException
from pydantic import BaseModel
import logging
from test import crack_query, auth, get_check_image
import time

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(title="ICP 备案查询 API", version="2.0")


class ICPQueryResponse(BaseModel):
    """查询响应模型"""
    status: str
    domain: str
    error: str | None = None
    data: dict | None = None


@app.get("/health")
async def health_check():
    """健康检查接口"""
    return {
        "status": "healthy",
        "timestamp": int(time.time()),
        "service": "ICP 备名查询系统"
    }


@app.get("/query", response_model=ICPQueryResponse)
async def query_icp(domain: str = Query(..., description="要查询的域名", examples=["qq.com"])):
    """
    查询域名的 ICP 备案信息

    **参数**:
    - domain: 要查询的域名（必填）

    **返回示例**:
    ```json
    {
      "status": "success",
      "domain": "qq.com",
      "data": { ... }
    }
    ```
    """
    try:
        logger.info(f"收到查询请求: {domain}")
        result = crack_query(domain)

        if "error" in result:
            logger.warning(f"域名 {domain} 查询失败: {result['error']}")
            return ICPQueryResponse(
                status="failed",
                domain=domain,
                error=result["error"]
            )

        logger.info(f"域名 {domain} 查询成功")
        # 打印查询结果摘要
        query_list = result.get('params', result).get('list', [])
        company_name = query_list[0].get('unitName', '未知') if query_list else '无数据'
        licence = query_list[0].get('mainLicence', '未知') if query_list else '无数据'
        nature = query_list[0].get('natureName', '未知') if query_list else '无数据'

        print(f"\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print(f"查询成功: {domain}")
        print(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print(f"公司名称: {company_name}")
        print(f"备案号: {licence}")
        print(f"企业性质: {nature}")
        print(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

        return ICPQueryResponse(
            status="success",
            domain=domain,
            data=result
        )

    except HTTPException:
        raise
    except ConnectionError as e:
        logger.error(f"网络连接错误: {e}")
        raise HTTPException(status_code=503, detail=f"网络服务不可用: {str(e)}")
    except Exception as e:
        logger.error(f"查询失败: {e}")
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")


@app.get("/auth")
async def get_auth_token():
    """获取新的认证 token（可选功能）"""
    try:
        token = auth()
        return {"token": token[:16] + "..."}
    except Exception as e:
        logger.error(f"获取 Token 失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取 Token 失败: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8000,
        log_level="info"
    )
