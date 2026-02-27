import logging

from Base.Ai.llms.qwenLlm import get_default_qwen_llm
from Base.Ai.prompt.commonPrompt import session_summary_prompt_v1
from Base.Ai.utils.common import jinja2_prompt_render
from Base.Models.BaseLLMConversationModel import BaseLLMConversationModel
from Base.Models.BaseLLMSession import BaseLLMSession

logger = logging.getLogger(__name__)

def ai_summary_session(session_id: str, user_id: str):
    """
    AI生成 会话总结
    """
    session = BaseLLMSession.get_user_last_session(user_id, session_id)
    conversations = BaseLLMConversationModel.get_after_id(session.last_handle_id, session_id, user_id)
    qa_pairs = [{'question': i.get('question'), 'answer': i.get('answer')[:300]} for i in conversations]

    if conversations:
        prompt = jinja2_prompt_render(session_summary_prompt_v1,{"history": qa_pairs,"last_session": session.ai_summary})
        llm = get_default_qwen_llm()
        response = llm.invoke(prompt)
        BaseLLMSession(id = session.id, ai_summary = response, last_handle_id=conversations[-1].get('id')).save()
        return response
    else:
        logs = f"会话 ( ID :{session_id} )在上次处理节点之后 {session.last_handle_id} 没有新的对话记录，跳过摘要生成."
        logger.info(logs)
        BaseLLMSession(id = session.id, update_logs = logs).save()
    return ''



if __name__ == '__main__':
    print(ai_summary_session("string", "string"))
