"""
文件名: app/services/email_service.py
创建时间: 2026-06-26
作者: TalentSense Team
功能描述: 邮件发送 + SMTP 配置 + HTML 报告生成
入参: to_email / candidate_ids / config
出参: 发送结果 / 配置
对应 Business-Requirements F17/F18
"""
import base64
import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.core.database import MongoDB
from app.core.logger import logger


def encrypt(plain: str) -> str:
    """简单加密（生产应使用 Fernet/AES）

    入参:
        plain: 明文
    出参:
        base64 编码字符串
    """
    return base64.b64encode(plain.encode()).decode()


def decrypt(cipher: str) -> str:
    """解密

    入参:
        cipher: base64 编码字符串
    出参:
        明文
    """
    return base64.b64decode(cipher.encode()).decode()


class EmailService:
    """邮件服务：发送推荐邮件 + SMTP 配置管理"""

    def __init__(self):
        self.config_coll = MongoDB.db.email_config if MongoDB.db else None
        self.resumes_coll = MongoDB.db.resumes if MongoDB.db else None

    async def send_recommendation(
        self, to_email: str, candidate_ids: list[str], job_title: str = ""
    ) -> dict:
        """AC17.1-17.3: 发送推荐邮件

        入参:
            to_email: 收件人
            candidate_ids: 候选人 ID 列表
            job_title: 岗位名称
        出参:
            {"status": "success"|"error", "sent_count": N, "message": "..."}
        """
        if self.config_coll is None:
            return {"status": "error", "message": "未配置 SMTP"}
        config = await self.config_coll.find_one({"_id": "default"})
        if not config:
            return {"status": "error", "message": "未配置 SMTP"}

        if self.resumes_coll is None:
            return {"status": "error", "message": "数据库未连接"}
        cursor = self.resumes_coll.find({"candidate_id": {"$in": candidate_ids}})
        candidates = await cursor.to_list(length=len(candidate_ids))

        html = self._build_html_report(candidates, job_title)

        msg = MIMEMultipart("alternative")
        msg["From"] = config["smtp_user"]
        msg["To"] = to_email
        msg["Subject"] = f"候选人推荐报告 - {job_title or '岗位'}"
        msg.attach(MIMEText(html, "html"))

        try:
            password = decrypt(config["smtp_password_encrypted"])
            await aiosmtplib.send(
                msg,
                hostname=config["smtp_host"], port=config["smtp_port"],
                username=config["smtp_user"], password=password,
                use_tls=config.get("smtp_port") == 465,
            )
            logger.info(f"邮件已发送到 {to_email}, 候选人数={len(candidates)}")
            return {"status": "success", "sent_count": len(candidates)}
        except Exception as e:
            logger.error(f"邮件发送失败: {e}")
            return {"status": "error", "message": str(e)}

    async def get_config(self) -> dict:
        """AC18.1: 获取配置（脱敏）

        出参:
            {"smtp_host", "smtp_port", "smtp_user", "smtp_password": ""}
        """
        if self.config_coll is None:
            return {}
        config = await self.config_coll.find_one({"_id": "default"})
        if not config:
            return {}
        return {
            "smtp_host": config.get("smtp_host", ""),
            "smtp_port": config.get("smtp_port", 465),
            "smtp_user": config.get("smtp_user", ""),
            "smtp_password": "",  # 不返回密码
        }

    async def update_config(self, config: dict) -> None:
        """AC18.2: 更新配置（加密存储）

        入参:
            config: {smtp_host, smtp_port, smtp_user, smtp_password}
        """
        if self.config_coll is None:
            return
        encrypted_pwd = encrypt(config.get("smtp_password", ""))
        await self.config_coll.update_one(
            {"_id": "default"},
            update={"$set": {
                "smtp_host": config["smtp_host"],
                "smtp_port": config["smtp_port"],
                "smtp_user": config["smtp_user"],
                "smtp_password_encrypted": encrypted_pwd,
            }},
            upsert=True,
        )
        logger.info("SMTP 配置已更新")

    def _build_html_report(self, candidates: list[dict], job_title: str = "") -> str:
        """AC17.3: 生成 HTML 报告

        入参:
            candidates: 候选人列表
            job_title: 岗位名称
        出参:
            HTML 字符串
        """
        rows = ""
        for c in candidates:
            skills = "、".join(c.get("skills", []))
            salary = c.get("expected_salary", {}) or {}
            salary_str = f"{salary.get('min', 0)}-{salary.get('max', 0)}K"
            rows += f"""
            <tr>
                <td>{c.get('name', '')}</td>
                <td>{c.get('work_years', 0)}年</td>
                <td>{skills}</td>
                <td>{salary_str}</td>
            </tr>"""
        return f"""
        <html><body>
            <h2>候选人推荐报告 - {job_title or '岗位'}</h2>
            <p>共推荐 {len(candidates)} 位候选人：</p>
            <table border="1" cellpadding="6" cellspacing="0">
                <tr><th>姓名</th><th>工作年限</th><th>技能</th><th>期望薪资</th></tr>
                {rows}
            </table>
        </body></html>"""


email_service = EmailService()
