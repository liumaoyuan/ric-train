import logging
import os
import threading
import uuid as uuid_lib

from fastapi import APIRouter, UploadFile, File, Form, Path as FastPathParam

from Base.Ai.llms.qwenLlm import get_default_qwen_llm
from Base.Client.minioClient import MinioClient
from Base.RicUtils.fileUtils import save_upload_file_to_temp
from Base.RicUtils.httpUtils import HttpResponse
from Wolin.models.po.interviewDialoguePo import InterviewDialoguePo
from Wolin.service.interviewQuestionService import generate_and_store_questions_async, get_questions_with_audio_url

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/interview/questions")
async def submit_interview_questions(
        resume_file: UploadFile = File(...),
        user_name: str = Form(""),
        voice: str = Form("中文女"),
):
    """
    上传简历文件，立即返回成功，后台异步生成面试问题并存储。
    """
    resume_file_path = await save_upload_file_to_temp(resume_file, use_original_filename=True)

    # 启动后台线程异步执行
    thread = threading.Thread(
        target=generate_and_store_questions_async,
        args=(resume_file_path, user_name, voice),
        daemon=True,
    )
    thread.start()

    return HttpResponse.ok(msg="任务已提交，正在后台生成面试问题...")


@router.get("/interview/questions/{record_uuid}")
async def get_questions_api(
        record_uuid: str = FastPathParam(..., description="面试记录 UUID"),
):
    """
    查询已生成的面试问题列表，返回带 MinIO 预签名音频 URL 的结果。
    """
    questions = get_questions_with_audio_url(record_uuid)
    return HttpResponse.ok(data=questions, msg="查询成功")


@router.post("/interview/dialogue")
async def save_dialogue(
        record_uuid: str = Form(..., description="面试记录 UUID"),
        question_text: str = Form(..., description="面试官问题文本"),
        answer_text: str = Form(..., description="求职者回答文本"),
        question_tts_path: str = Form(None, description="问题 TTS 音频路径"),
        answer_audio_path: str = Form(None, description="回答音频路径"),
):
    """
    保存一轮面试对话记录。每答一次调用一次。
    """
    dialogue = InterviewDialoguePo.create_dialogue(
        record_uuid=record_uuid,
        question_text=question_text,
        answer_text=answer_text,
        question_tts_path=question_tts_path,
        answer_audio_path=answer_audio_path,
    )
    return HttpResponse.ok(data={"id": dialogue.id, "dialogue_order": dialogue.dialogue_order}, msg="对话记录已保存")


@router.post("/interview/audio_answer")
async def submit_audio_answer(
        record_uuid: str = Form(..., description="面试记录 UUID"),
        question_text: str = Form(..., description="面试官问题文本"),
        question_tts_path: str = Form(None, description="问题 TTS 音频路径"),
        answer_audio: UploadFile = File(..., description="用户回答的录音文件"),
):
    """接收用户录音，上传到 MinIO，调用 ASR 识别文本，保存对话记录。"""
    temp_audio_path = await save_upload_file_to_temp(answer_audio, use_original_filename=True)
    try:
        minio_client = MinioClient()
        object_name = f"answer-audio/{record_uuid}/{uuid_lib.uuid4().hex}.webm"
        upload_ok = minio_client.upload_file("interview-answers", object_name, temp_audio_path)
        if not upload_ok:
            return HttpResponse.error(msg="音频上传到 MinIO 失败")

        llm = get_default_qwen_llm()
        answer_text = llm.asr(temp_audio_path) or ""

        dialogue = InterviewDialoguePo.create_dialogue(
            record_uuid=record_uuid,
            question_text=question_text,
            answer_text=answer_text,
            question_tts_path=question_tts_path,
            answer_audio_path=object_name,
        )
        return HttpResponse.ok(
            data={"id": dialogue.id, "dialogue_order": dialogue.dialogue_order, "answer_text": answer_text},
            msg="回答已保存",
        )
    except Exception as e:
        logger.error(f"submit_audio_answer 失败: {e}", stack_info=True)
        return HttpResponse.error(msg=f"保存回答失败: {str(e)}")
    finally:
        if temp_audio_path and os.path.exists(temp_audio_path):
            os.unlink(temp_audio_path)
