import streamlit as st
from groq import Groq
import base64

# ── 페이지 설정 ───────────────────────────────────────────
st.set_page_config(page_title="이미지 분석 AI", page_icon="🖼️")

# ── API 설정 ──────────────────────────────────────────────
client = Groq(api_key=st.secrets["GROQ_API_KEY"])

# ── 이미지 Vision 모델 고정 ───────────────────────────────
# 이미지를 볼 수 있는 모델은 따로 있어요
# llama-3.1-8b-instant는 텍스트 전용 → 이미지 넣으면 오류남
MODEL = "meta-llama/llama-4-scout-17b-16e-instruct"

SYSTEM_PROMPT = """당신은 이미지 분석 전문가입니다.
이미지를 보고 다음을 포함해서 설명해주세요.
- 이미지에 무엇이 있는지
- 전체적인 분위기와 색감
- 눈에 띄는 특징
한국어로 답변하세요."""

# ── 메인 화면 ─────────────────────────────────────────────
st.title("🖼️ 이미지 분석 AI")
st.write("이미지를 올리거나 URL을 입력하면 AI가 분석해드려요!")

st.divider()

# ── 이미지 입력 — URL 또는 파일 ──────────────────────────
tab_url, tab_file = st.tabs(["🔗 URL로 입력", "📁 파일 업로드"])

image_url = None
uploaded_file = None

with tab_url:
    image_url = st.text_input(
        "이미지 URL을 입력하세요",
        placeholder=""
    )
    if image_url:
        st.image(image_url, caption="입력한 이미지", use_column_width=True)

with tab_file:
    uploaded_file = st.file_uploader(
        "이미지 파일을 올려주세요",
        type=["jpg", "jpeg", "png", "webp", "gif"]
    )
    if uploaded_file:
        st.image(uploaded_file, caption="업로드한 이미지", use_column_width=True)

st.divider()

# ── 이미지 content 구성 ───────────────────────────────────
# URL과 파일 중 어느 것이 입력됐는지 확인하고 형식 맞춰주기
def get_image_content():
    if image_url:
        return {
            "type": "image_url",
            "image_url": {"url": image_url}
        }
    elif uploaded_file:
        uploaded_file.seek(0)
        file_bytes = uploaded_file.read()
        base64_image = base64.b64encode(file_bytes).decode("utf-8")
        ext = uploaded_file.type   # 예: "image/jpeg"
        return {
            "type": "image_url",
            "image_url": {
                "url": f"data:{ext};base64,{base64_image}"
            }
        }
    else:
        return None

has_image = image_url or uploaded_file

# ── 대화 기록 초기화 ──────────────────────────────────────
if "img_messages" not in st.session_state:
    st.session_state.img_messages = []

# ── 이전 대화 출력 ────────────────────────────────────────
for message in st.session_state.img_messages:
    with st.chat_message(message["role"]):
        if isinstance(message["content"], list):
            for item in message["content"]:
                if item["type"] == "text":
                    st.write(item["text"])
        else:
            st.write(message["content"])

# ── 사용자 입력 ───────────────────────────────────────────
# 이미지가 없으면 입력창 비활성화
placeholder = "이미지를 먼저 입력하세요..." if not has_image else "이 이미지에 대해 질문하세요..."
user_input = st.chat_input(placeholder, disabled=not has_image)

if user_input:
    image_content = get_image_content()

    # 이미지 + 텍스트를 같이 보내기
    # 매번 이미지를 같이 보내야 AI가 계속 볼 수 있어요
    user_content = [
        image_content,
        {"type": "text", "text": user_input}
    ]

    # 사용자 메시지 화면 출력
    with st.chat_message("user"):
        st.write(user_input)

    # 대화 기록 추가
    st.session_state.img_messages.append({
        "role": "user",
        "content": user_content
    })

    # AI 응답
    with st.chat_message("assistant"):
        with st.spinner("이미지 분석 중..."):
            response = client.chat.completions.create(
                model=MODEL,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    *st.session_state.img_messages
                ],
                max_tokens=1000,
            )
            ai_response = response.choices[0].message.content
            st.write(ai_response)

    # AI 응답 기록 추가
    st.session_state.img_messages.append({
        "role": "assistant",
        "content": ai_response
    })

# ── 대화 초기화 버튼 ──────────────────────────────────────
if st.session_state.img_messages:
    if st.button("🗑️ 대화 초기화"):
        st.session_state.img_messages = []
        st.rerun()