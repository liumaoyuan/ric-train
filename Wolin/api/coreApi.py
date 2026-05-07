import logging
import os
import threading
from pathlib import Path
from typing import Optional
from urllib.parse import quote

from fastapi import APIRouter, UploadFile, File, Form, Response

from Base.Ai.llms.qwenLlm import get_default_qwen_llm
from Base.RicUtils.fileUtils import save_upload_file_to_temp
from Base.RicUtils.httpUtils import HttpResponse
from Wolin.ai.interview.iaState import IAState, ApiParams
from Wolin.ai.interview.nodes.iaNodes import get_workflow
from Wolin.core.interviewAnalysis import InterviewAnalysis

router = APIRouter()

logger = logging.getLogger(__name__)


@router.post("/interview_analysis")
async def interview_analysis(
        receive_email: str = Form(...),
        user_name: str = Form(...),
        company_name: str = Form(...),
        audio_file: UploadFile = File(...),
        resume_file: Optional[UploadFile] = None
):
    audio_file_path = await save_upload_file_to_temp(audio_file, use_original_filename=True)
    resume_file_path = None
    if resume_file:
        resume_file_path = await save_upload_file_to_temp(resume_file, use_original_filename=True)
    try:
        def run_analysis():
            try:
                _state = IAState()
                api_params = ApiParams(receive_email=receive_email,user_name=user_name,company_name=company_name)
                _state.api_params = api_params
                _state.asr_info.audio_path = audio_file_path
                _state.resume_info.resume_path = resume_file_path
                wf = get_workflow()
                wf.invoke(_state)
            except Exception as e:
                logger.error(f"[后台线程] InterviewAnalysis 发生异常: {e}", stack_info=True)

        # 3. 后台启动一个线程运行它（不阻塞当前请求）
        # thread = threading.Thread(target=run_analysis)
        # thread.start()
        run_analysis()
        return HttpResponse.ok(msg="正在分析中...")
    finally:
        if audio_file_path and os.path.exists(audio_file_path):
            os.unlink(audio_file_path)
        if resume_file_path and os.path.exists(resume_file_path):
            os.unlink(resume_file_path)


@router.post("audio_2_text")
async def audio_2_text_api(audio_file: UploadFile = File(...),):
    audio_file_path = await save_upload_file_to_temp(audio_file, use_original_filename=True)
    try:
        instance = InterviewAnalysis(audio_file=audio_file_path)
        content = instance.audio_2_text_public()
    except Exception as e:
        raise e
    finally:
        if os.path.exists(audio_file_path):
            os.unlink(audio_file_path)

    text_bytes = content.encode("utf-8")
    safe_filename = quote(Path(audio_file_path).stem, safe="")
    headers = {
        "Content-Disposition": f"attachment; filename=\"fallback.txt\"; filename*=UTF-8''{safe_filename}"
    }
    return Response(
        content=text_bytes,
        media_type="text/plain",
        headers=headers
    )


@router.post("/audio_to_text")
async def audio_to_text(audio_file: UploadFile = File(...)):
    """接收录音文件，调用 Qwen ASR 返回识别文字。"""
    audio_file_path = await save_upload_file_to_temp(audio_file, use_original_filename=True)
    try:
        llm = get_default_qwen_llm()
        text = llm.asr(audio_file_path)
        return HttpResponse.ok(data={"text": text or ""}, msg="识别成功")
    except Exception as e:
        logger.error(f"audio_to_text 失败: {e}", stack_info=True)
        return HttpResponse.error(msg=f"识别失败: {str(e)}")
    finally:
        if audio_file_path and os.path.exists(audio_file_path):
            os.unlink(audio_file_path)
