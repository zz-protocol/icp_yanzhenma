import requests
import hashlib
import time
import uuid
import base64
import numpy as np
from PIL import Image
import io
from typing import Optional, Tuple, Dict, Any
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)


def auth() -> str:
    """获取认证 token"""
    url = "https://hlwicpfwc.miit.gov.cn/icpproject_query/api/auth"
    t = str(round(time.time()))
    data = {
        "authKey": hashlib.md5(("testtest" + t).encode()).hexdigest(),
        "timeStamp": t
    }
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer": "https://beian.miit.gov.cn/",
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json, text/plain, */*"
    }

    try:
        resp = requests.post(url, data=data, headers=headers, timeout=60)
        resp.raise_for_status()
        result = resp.json()["params"]["bussiness"]
        logger.info(f"Token 获取成功: {result[:16]}...")
        return result
    except Exception as e:
        logger.error(f"获取 Token 失败: {e}")
        raise


def get_check_image(token: str) -> Dict[str, Any]:
    """获取验证码图片数据"""
    try:
        url = "https://hlwicpfwc.miit.gov.cn/icpproject_query/api/image/getCheckImagePoint"
        payload = {"clientUid": "point-" + str(uuid.uuid4())}
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Referer": "https://beian.miit.gov.cn/",
            "Token": token,
            "Accept": "application/json, text/plain, */*"
        }

        resp = requests.post(url, headers=headers, json=payload, timeout=30)
        resp.raise_for_status()
        result = resp.json()
        logger.info("验证码图片获取成功")
        return result["params"]

    except requests.exceptions.Timeout:
        logger.error("获取验证码图片超时（30秒）")
        raise
    except Exception as e:
        logger.error(f"获取验证码图片失败: {e}")
        raise


def match_slider_offset(small_image_b64: str, big_image_b64: str) -> Tuple[bool, int]:
    """匹配滑块缺口偏移量"""
    try:
        big_img = np.array(Image.open(io.BytesIO(base64.b64decode(big_image_b64))).convert("RGB"))
        small_img = np.array(Image.open(io.BytesIO(base64.b64decode(small_image_b64))))
        sh, sw = small_img.shape[:2]

        resized = big_img[::2, ::2]
        h, w = resized.shape[:2]
        min_side = int(min(sw, sh) * 0.25)

        q = (resized.astype(np.int32) // 4) * 4
        color_id = q[:, :, 0] + q[:, :, 1] * 256 + q[:, :, 2] * 65536

        flat_colors = color_id.ravel()
        unique, counts = np.unique(flat_colors, return_counts=True)
        top_indices = np.argsort(counts)[-5:]

        best_area = 0
        best_x = 0

        for idx in top_indices:
            c = unique[idx]
            mask = color_id == c

            col_run = np.zeros((h, w), dtype=np.int32)
            col_run[0] = mask[0].astype(np.int32)
            for y in range(1, h):
                col_run[y] = np.where(mask[y], col_run[y - 1] + 1, 0)

            for y in range(min_side, h):
                row = col_run[y] >= min_side
                if not np.any(row):
                    continue

                d = np.diff(row.astype(np.int8))
                starts = np.where(d == 1)[0] + 1
                ends = np.where(d == -1)[0] + 1
                if row[0]:
                    starts = np.concatenate([[0], starts])
                if row[-1]:
                    ends = np.concatenate([ends, [w]])

                for s, e in zip(starts, ends):
                    run_w = e - s
                    if s <= sw // 4:
                        continue
                    run_h = int(col_run[y, s])
                    ratio = run_w / run_h if run_h > 0 else 0

                    if 0.7 < ratio < 1.4 and run_w * run_h > best_area:
                        best_area = run_w * run_h
                        best_x = s

        if best_area == 0:
            logger.warning("未找到有效缺口")
            return False, 0

        offset_x = best_x * 2
        logger.info(f"缺口位置计算成功: offset_x={offset_x}")
        return True, offset_x

    except Exception as e:
        logger.error(f"计算缺口位置失败: {e}")
        raise


def checkImage(token: str, key: str, value: int) -> Optional[str]:
    """
    验证验证码是否有效
    
    Args:
        token: 认证 token
        key: 验证密钥（uuid）
        value: 滑块偏移量
    
    Returns:
        Base64 编码的增强签名字符串
    """
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Referer": "https://beian.miit.gov.cn/",
            "Token": token,
            "Connection": "keep-alive",
            "Accept": "application/json, text/plain, */*",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "zh-CN,zh;q=0.9",
            "Origin": "https://beian.miit.gov.cn"
        }
        data = {"key": key, "value": value}

        resp = requests.post(
            "https://hlwicpfwc.miit.gov.cn/icpproject_query/api/image/checkImage",
            headers=headers,
            json=data,
            timeout=15
        )
        resp.raise_for_status()
        
        print("图片sign验证")
        result = resp.json()
        
        if result["success"] == True:
            # 返回增强的签名（Base64 字符串）
            return result["params"]
        else:
            logger.warning("验证码验证失败")
            return None

    except requests.exceptions.Timeout:
        logger.error("验证验证码超时（15秒）")
        raise
    except Exception as e:
        logger.error(f"验证验证码失败: {e}")
        raise


def query_icp_info(sign: str, uuid_token: str, domain: str, token: str) -> Dict[str, Any]:
    """
    查询 ICP 备案信息

    Args:
        sign: 验证验证码返回的增强签名
        uuid_token: UUID token
        domain: 要查询的域名
        token: 认证 token

    Returns:
        查询结果 JSON
    """
    try:
        import json

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Referer": "https://beian.miit.gov.cn/",
            "Token": token,
            "Sign": sign,
            "Uuid": uuid_token,
            "Content-Type": "application/json",
            "Cookie": f"__jsluid_s={uuid.uuid4().hex[:32]}"
        }
        data = {"pageNum": "", "pageSize": "", "unitName": domain, "serviceType": 1}

        resp = requests.post(
            "https://hlwicpfwc.miit.gov.cn/icpproject_query/api/icpAbbreviateInfo/queryByCondition",
            headers=headers,
            data=json.dumps(data).replace(" ", ""),
            timeout=30
        )
        resp.raise_for_status()

        print("域名查询")
        return resp.json()

    except requests.exceptions.Timeout:
        logger.error(f"查询域名 {domain} 超时（30秒）")
        raise
    except Exception as e:
        logger.error(f"查询域名 {domain} 失败: {e}")
        raise


def crack_query(domain: str) -> Dict[str, Any]:
    """
    完整的验证码计算与查询流程

    Args:
        domain: 要查询的域名

    Returns:
        查询结果或错误信息
    """
    try:
        logger.info(f"开始查询域名: {domain}")

        # 步骤 1: 获取 Token
        token = auth()

        # 步骤 2: 获取验证码图片
        image_params = get_check_image(token)

        # 步骤 3: 计算滑块偏移
        success, offset = match_slider_offset(
            image_params["smallImage"],
            image_params["bigImage"]
        )
        if not success:
            return {"error": "无法计算缺口位置"}

        # 步骤 4: 验证验证码
        sign = checkImage(token, image_params["uuid"], int(offset))
        print(sign)

        if sign is None:
            return {"error": "验证码验证失败"}

        # 步骤 5: 查询 ICP
        result = query_icp_info(sign, image_params["uuid"], domain, token)

        # 确保 result 是标准字典，避免 numpy 类型
        if not isinstance(result, dict):
            result = {}

        return result

    except Exception as e:
        logger.error(f"查询域名 {domain} 过程出错: {e}")
        error_msg = str(e)
        # 确保 error_msg 是 Python 原生类型
        if isinstance(error_msg, bytes):
            error_msg = error_msg.decode('utf-8', errors='ignore')
        return {"error": error_msg}


def aes_ecb_encrypt(plaintext: bytes, key: bytes) -> str:
    """AES ECB 模式加密"""
    try:
        backend = default_backend()
        cipher = Cipher(algorithms.AES(key), modes.ECB(), backend=backend)
        padding_length = 16 - (len(plaintext) % 16)
        plaintext_padded = plaintext + bytes([padding_length]) * padding_length
        encryptor = cipher.encryptor()
        ciphertext = encryptor.update(plaintext_padded) + encryptor.finalize()
        return base64.b64encode(ciphertext).decode('utf-8')
    except Exception as e:
        logger.error(f"AES 加密失败: {e}")
        raise


def main():
    """主测试流程"""
    import json

    domain = 'qq.com'

    try:
        result = crack_query(domain)
        print(f"\n查询结果: {json.dumps(result, indent=2, ensure_ascii=False)}")
    except KeyboardInterrupt:
        logger.info("用户中断查询")
    except Exception as e:
        logger.error(f"程序执行出错: {e}")


if __name__ == "__main__":
    main()