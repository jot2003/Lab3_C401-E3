# Hướng dẫn nhóm — Lab 3 (Travel ReAct Agent)

Repo nhóm: [github.com/jot2003/Day-3-Lab-Chatbot-vs-react-agent](https://github.com/jot2003/Day-3-Lab-Chatbot-vs-react-agent)

---

## 1. Share code cho cả nhóm

### Cách 1: Gửi link repo (đủ nếu repo **Public**)

- Link clone HTTPS:
  ```bash
  git clone https://github.com/jot2003/Day-3-Lab-Chatbot-vs-react-agent.git
  cd Day-3-Lab-Chatbot-vs-react-agent
  ```
- Mỗi người tự tạo file `.env` (không commit — đã có trong `.gitignore`).

### Cách 2: Repo **Private** — thêm thành viên

1. Vào GitHub repo → **Settings** → **Collaborators** → **Add people**
2. Nhập GitHub username hoặc email của từng bạn → gửi lời mời
3. Người được mời **Accept** rồi clone như trên

### Làm việc chung (gợi ý)

- Mỗi người làm trên **branch riêng** (`feature/weather`, `feature/agent-v2`…), mở **Pull Request** vào `main`
- Hoặc thống nhất một người merge, còn lại pull trước khi push:
  ```bash
  git pull origin main
  ```

---

## 2. Cài đặt môi trường

```bash
cd Day-3-Lab-Chatbot-vs-react-agent
```

**Python:** khuyến nghị 3.10+

**Cài package (nhẹ, không cần build llama-cpp):**

```bash
pip install -r requirements-travel.txt
```

*(Nếu cần chạy model local GGUF thì cài thêm `requirements.txt` đầy đủ — trên Windows có thể lâu.)*

**Tạo file `.env`:**

```bash
copy .env.example .env
```

Sửa `.env` và điền key thật:

| Biến | Ý nghĩa |
|------|---------|
| `GEMINI_API_KEY` | [Google AI Studio](https://aistudio.google.com/apikey) |
| `DEFAULT_PROVIDER` | `google` |
| `DEFAULT_MODEL` | ví dụ `gemini-1.5-flash` |
| `OPENWEATHER_API_KEY` | [OpenWeatherMap](https://openweathermap.org/api) |
| `AMADEUS_CLIENT_ID` | [Amadeus Developers](https://developers.amadeus.com/) — app **Test** |
| `AMADEUS_CLIENT_SECRET` | cặp với Client ID |
| `DEMO_TRAVEL_APIS` | `1` = thiếu OpenWeather/Amadeus thì dùng dữ liệu mẫu; `0` + đủ key = API thật |
| `AGENT_MAX_STEPS` | mặc định `8` |

**Không** đưa `.env` lên GitHub.

---

## 3. Chạy thử

### Giao diện web (Streamlit)

```bash
pip install streamlit google-generativeai
python -m streamlit run app.py
```

Dùng `python -m streamlit` thay vì gõ `streamlit` trần để trùng với đúng bản Python đã cài package (tránh lỗi `No module named 'google.generativeai'`).

Trình duyệt mở `http://localhost:8501` — chọn Agent hoặc Chatbot, nhập câu hỏi, bấm **Chạy**. Trace ReAct nằm trong phần mở rộng bên dưới kết quả.

### Dòng lệnh (CLI)

Từ thư mục gốc repo:

```bash
python main.py --mode agent
```

```bash
python main.py --mode chatbot -q "Cau hoi cua ban o day"
```

- `--mode agent`: ReAct + 3 tool (thời tiết, vé máy bay, ngân sách)
- `--mode chatbot`: baseline không tool (để so sánh trong báo cáo)

**Test không cần API LLM:**

```bash
python -m pytest tests/test_travel_tools.py -v
```

**Log:** thư mục `logs/` (JSON từng bước — dùng cho báo cáo / Discord trace).

---

## 4. Cấu trúc code quan trọng

| Đường dẫn | Nội dung |
|-----------|----------|
| `main.py` | Điểm vào: chatbot vs agent |
| `src/agent/agent.py` | Vòng lặp ReAct, parse `Action` / `Final Answer` |
| `src/chatbot.py` | Chatbot baseline |
| `src/core/provider_factory.py` | Chọn Gemini / OpenAI / local từ `.env` |
| `src/tools/weather.py` | OpenWeather |
| `src/tools/flights.py` | Amadeus (sandbox) |
| `src/tools/budget.py` | Tính ngân sách chuyến đi |
| `src/tools/registry.py` | Danh sách tool + `execute_tool` |
| `report/NOP_BAI_CHECKLIST.md` | Checklist nộp bài khớp rubric |
| `report/group_report/TEMPLATE_GROUP_REPORT.md` | Template báo cáo nhóm |
| `report/individual_reports/TEMPLATE_INDIVIDUAL_REPORT.md` | Template báo cáo cá nhân |

---

## 5. Tổng hợp log → CSV (báo cáo Evaluation)

Sau khi chạy agent/chatbot (có file trong `logs/`):

```bash
python scripts/summarize_logs.py
```

Kết quả trong `report/exports/`: `llm_metrics.csv`, `sessions_summary.csv`, `event_counts.csv` (thư mục `exports/` không commit — dùng để chèn bảng vào báo cáo).

Checklist việc chi tiết: `report/VIEC_CAN_LAM.md`.

---

## 6. Nộp bài & Discord (tóm tắt)

- **Nhóm:** đổi tên file → `report/group_report/GROUP_REPORT_[TEN_NHOM].md` (theo template)
- **Cá nhân:** `report/individual_reports/REPORT_[HO_TEN].md`
- **Discord:** post trace Thought / Action / Observation, **ít nhất 3 bước**, ghi rõ tool + tham số + kết quả

Chi tiết: `report/NOP_BAI_CHECKLIST.md`, `report/VIEC_CAN_LAM.md`, `SCORING.md`.

---

## 7. Remote Git (cho người maintain)

- `origin` → repo nhóm **jot2003**
- `upstream` → repo gốc VinUni (nếu sau này muốn `git fetch upstream` để xem thay đổi khóa học)

---

*Nếu `search_flights` không trả offer: sandbox Amadeus phụ thuộc ngày/route — thử đổi ngày trong câu hỏi `-q`.*
