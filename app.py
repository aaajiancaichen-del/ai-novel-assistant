"""AI 小说创作助手：Streamlit + OpenAI Responses API。"""
import os

import streamlit as st
from openai import OpenAI

st.set_page_config(
    page_title="AI 小说创作助手",
    page_icon="📖",
    layout="wide",
)

# 密钥只能配置在 Streamlit Cloud 的 Secrets 页面或本地环境变量里。
# 请勿把 API Key 写进本文件或上传到 GitHub。
def get_api_key():
    try:
        return st.secrets.get("OPENAI_API_KEY", "") or os.getenv("OPENAI_API_KEY", "")
    except Exception:
        return os.getenv("OPENAI_API_KEY", "")


PLATFORMS = {
    "知乎短篇": "开头三段内抛出强钩子，冲突迅速建立；重视人物情感、反转逻辑、爽虐节奏，语言自然，不要模板式开场。",
    "番茄男频": "突出升级成长、强冲突、战斗与打脸的反馈，情节推进快，章末有悬念，避免冗长说明。",
    "七猫男频": "注重情节密度、悬念、男主行动力和阶段性反转，语言利落，场景有画面感。",
    "通用小说": "人物动机可信、细节具体、情节连贯，不写空泛套话。",
}

TASKS = {
    "生成大纲": "给出故事核心卖点、主要人物、开篇钩子、分阶段冲突、关键反转和结局，并说明伏笔如何回收。",
    "写小说开篇": "直接写小说正文，用具体场景开篇，尽早抛出矛盾，不要先解释设定。",
    "续写章节": "严格承接提供的已有正文，延续人设、视角与时间线，写出有推进力的下一段剧情，结尾保留吸引人的钩子。",
    "设计高能反转": "提供多处前后因果相扣的反转：铺垫、触发、揭露、人物代价及后续爽点。",
    "加强虐点与爽点": "围绕主角目标设计具体现实压力、误解或背叛、情绪爆点和有逻辑的反击，不靠角色突然降智。",
    "润色已有正文": "保留原文事实、人物、事件和叙事视角，优化对话、节奏、画面与情绪张力，不擅自改动核心剧情。",
}

SYSTEM_PROMPT = """你是资深中文网络小说作者与编辑。
遵循用户指定的平台、题材和任务完成创作。强调情节可读性、人物一致性与因果逻辑；
不用‘以下是’等套话，不对读者解释自己的创作过程。
小说正文使用自然中文引号“”表示对白，每个说话人的对话独立成段。
不要复制现成小说或模仿特定在世作者的原文。
"""

st.title("📖 AI 小说创作助手")
st.caption("从想法到大纲、从开篇到续写｜适合知乎短篇、番茄男频等创作方向")
st.info("建议先用“生成大纲”，再分章节创作。万字长篇需要分多次生成与人工检查衔接。")

with st.sidebar:
    st.header("⚙️ 创作设置")
    platform = st.selectbox("发布方向", list(PLATFORMS))
    task = st.selectbox("创作任务", list(TASKS))
    genre = st.selectbox("小说类型", [
        "追妻火葬场", "大女主爽文", "甜宠双洁", "灵异恐怖", "悬疑反转",
        "高武战斗", "都市逆袭", "双男主情感", "其他",
    ])
    length = st.select_slider("本次目标字数", options=[600, 1000, 1500, 2000, 2500], value=1500)
    st.caption("目标字数为写作参考，AI 每次输出可能有偏差。")

left, right = st.columns(2)
with left:
    title = st.text_input("小说名称（可选）", placeholder="例如：他跪在我的婚礼外")
    characters = st.text_area(
        "人物设定", height=180,
        placeholder="女主：曾为家庭放弃事业，性格清醒。\n男主：误信他人，失去后追悔。",
    )
with right:
    ideas = st.text_area(
        "剧情要求（建议具体一些）", height=268,
        placeholder="例如：第一段就出现离婚协议；前300字埋两个钩子；中段三次反转；结局女主绝不回头。",
    )

previous = st.text_area(
    "已有正文（选填；续写或润色时请粘贴）", height=200,
    placeholder="把之前写好的章节粘贴在这里。",
)

if "generated_text" not in st.session_state:
    st.session_state.generated_text = ""

if st.button("✨ 开始生成", type="primary", use_container_width=True):
    key = get_api_key()
    if not key:
        st.error("尚未配置 OpenAI API Key。请前往 Streamlit Cloud → App settings → Secrets，添加 OPENAI_API_KEY。")
    elif task in ("续写章节", "润色已有正文") and not previous.strip():
        st.warning("续写或润色需要先在“已有正文”中粘贴原文。")
    elif not any([title.strip(), characters.strip(), ideas.strip(), previous.strip()]):
        st.warning("请至少填写小说名称、人物设定、剧情要求或已有正文。")
    else:
        prompt = f"""发布方向：{platform}
平台创作特点：{PLATFORMS[platform]}
创作任务：{task}
任务要求：{TASKS[task]}
题材：{genre}
小说名称：{title or '由你拟定'}
主要人物：{characters or '根据剧情自行构思'}
剧情要求：{ideas or '围绕题材自行构思有吸引力的主线'}
已有正文：{previous or '无'}
本次目标长度：约{length}个汉字。请优先确保质量与情节完整；
若本次只创作一个章节，不要强行写完整部长篇。"""
        try:
            with st.spinner("正在构思和写作……"):
                client = OpenAI(api_key=key, timeout=180.0)
                result = client.responses.create(
                    model="gpt-4.1-mini",
                    instructions=SYSTEM_PROMPT,
                    input=prompt,
                    max_output_tokens=6500,
                )
                st.session_state.generated_text = result.output_text or ""
            if not st.session_state.generated_text:
                st.warning("模型未返回可显示的文字，请调整要求后重试。")
        except Exception as exc:
            # 错误信息只显示类型，不暴露可能包含敏感配置的内部详情。
            st.error(f"生成失败（{type(exc).__name__}）。请检查 API 额度、密钥权限或稍后重试。")

if st.session_state.generated_text:
    st.divider()
    st.subheader("📝 生成结果")
    st.text_area("小说内容", value=st.session_state.generated_text, height=480)
    st.download_button(
        "⬇️ 下载为 TXT 文件",
        data=st.session_state.generated_text.encode("utf-8-sig"),
        file_name="AI小说创作结果.txt",
        mime="text/plain",
        use_container_width=True,
    )

st.divider()
st.caption("注意：AI 内容仍需人工核对人设、情节衔接与原创性。API 调用按用量计费；不要分享密钥。")
