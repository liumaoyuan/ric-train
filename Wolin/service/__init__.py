from Wolin.service.asrService import asr_service
from Wolin.service.emailService import email_service
from Wolin.service.minioService import minio_service


def get_email_service():
    return email_service


def get_asr_service():
    return asr_service


def get_minio_service():
    return minio_service


def get_interview_record_service():
    """获取面试记录持久化服务"""
    # 延迟导入，避免循环依赖
    from Wolin.service.interviewRecordService import get_interview_record_service as service
    return service()
