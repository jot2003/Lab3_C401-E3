"""
Giao diện web (Streamlit). Chạy từ thư mục gốc repo:
  streamlit run app.py
"""
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st
from dotenv import load_dotenv

load_dotenv(ROOT / ".env")

from src.agent.agent import ReActAgent
from src.chatbot import TravelChatbotBaseline
from src.core.provider_factory import build_llm_from_env
from src.tools.registry import get_tool_specs

# Đổi chuỗi này nếu cần ép Streamlit bỏ cache LLM cũ (đã từng cache gemini-1.5-flash).
_LLM_CACHE_VERSION = "v4-keyed-cache"


def _llm_resource_cache_key() -> tuple:
    """Khóa cache: đổi .env (model/key) là tạo LLM mới, không dùng bản 1.5-flash cũ."""
    load_dotenv(ROOT / ".env", override=True)
    key = os.getenv("GEMINI_API_KEY", "") or ""
    hint = (key[:12] + key[-8:]) if len(key) > 20 else key
    return (
        os.getenv("DEFAULT_PROVIDER", "google"),
        os.getenv("DEFAULT_MODEL", "gemini-2.5-flash"),
        hint,
        _LLM_CACHE_VERSION,
    )


@st.cache_resource
def _cached_llm(_cache_key: tuple):
    try:
        return build_llm_from_env()
    except ModuleNotFoundError as e:
        name = (e.name or str(e)).lower()
        if "google" in name or "generativeai" in str(e).lower():
            py = sys.executable
            raise RuntimeError(
                "Thiếu package `google-generativeai` trong đúng môi trường Python đang chạy Streamlit.\n\n"
                f"Chạy trong terminal:\n```\n\"{py}\" -m pip install google-generativeai\n```\n"
                f"Sau đó khởi động lại UI bằng **cùng** Python:\n```\n\"{py}\" -m streamlit run app.py\n```\n"
                "(Tránh gõ lệnh `streamlit` trần nếu máy có nhiều Python — dễ cài nhầm env.)"
            ) from e
        raise


def main() -> None:
    load_dotenv(ROOT / ".env", override=True)

    st.set_page_config(
        page_title="Lab 3 — Travel Agent",
        page_icon="✈️",
        layout="wide",
    )

    st.title("Lab 3: Chatbot vs ReAct Agent")
    st.caption("Chủ đề du lịch — Gemini + OpenWeather + Amadeus + tính ngân sách")

    with st.sidebar:
        st.subheader("Cấu hình")
        mode = st.radio(
            "Chế độ",
            options=["agent", "chatbot"],
            format_func=lambda x: (
                "ReAct Agent (có tools)" if x == "agent" else "Chatbot baseline (không tools)"
            ),
            index=0,
        )
        max_steps = st.number_input(
            "Agent: số bước tối đa",
            min_value=1,
            max_value=24,
            value=int(os.getenv("AGENT_MAX_STEPS", "8")),
        )
        st.divider()
        if st.button("Xóa cache LLM & tải lại", help="Bắt buộc sau khi đổi model/API; tránh lỗi 404 model cũ."):
            st.cache_resource.clear()
            st.rerun()
        st.markdown(
            "Cần file `.env` với `GEMINI_API_KEY` và (tuỳ chọn) OpenWeather / Amadeus. "
            "Sau khi sửa `.env`: bấm nút trên hoặc **⋮ → Clear cache**."
        )
        st.caption(f"Python đang dùng: `{sys.executable}`")
        st.caption(
            f"Model trong `.env`: `{os.getenv('DEFAULT_MODEL', '')}` "
            f"(code sẽ map sang model API còn hỗ trợ nếu cần)."
        )

    default_q = (
        "I want to fly from Hanoi (HAN) to Da Nang (DAD) on 2026-04-15. "
        "Budget 8000000 VND total for 2 nights, hotel 900000 VND per night. "
        "Check weather in Da Nang and flight prices, then say if the budget works."
    )
    question = st.text_area("Câu hỏi / kịch bản", value=default_q, height=140)

    if st.button("Chạy", type="primary"):
        q = question.strip()
        if not q:
            st.warning("Nhập câu hỏi trước khi chạy.")
            return

        try:
            llm = _cached_llm(_llm_resource_cache_key())
        except RuntimeError as e:
            st.markdown(str(e))
            return
        except Exception as e:
            st.error(f"Không khởi tạo được LLM. Kiểm tra `.env` và API key: {e}")
            return

        with st.spinner("Đang xử lý (có thể mất vài chục giây với agent)…"):
            if mode == "chatbot":
                bot = TravelChatbotBaseline(llm)
                answer = bot.reply(q)
                st.subheader("Trả lời (chatbot)")
                st.markdown(answer)
            else:
                agent = ReActAgent(llm, get_tool_specs(), max_steps=int(max_steps))
                answer = agent.run(q)
                st.subheader("Kết quả (agent)")
                st.markdown(answer)

                if agent.history:
                    with st.expander("Trace ReAct — Thought / Action / Observation", expanded=True):
                        for h in agent.history:
                            st.markdown(f"##### Bước {h['step']}")
                            st.markdown("**LLM (raw)**")
                            st.code(h.get("llm", "") or "", language="markdown")
                            if h.get("final"):
                                st.success("Final Answer trong khối trên.")
                            if h.get("tool"):
                                st.markdown(f"**Tool:** `{h['tool']}`")
                                st.markdown("**Observation**")
                                obs = h.get("observation") or ""
                                try:
                                    st.json(json.loads(obs))
                                except (json.JSONDecodeError, TypeError):
                                    st.text(obs)


if __name__ == "__main__":
    main()
