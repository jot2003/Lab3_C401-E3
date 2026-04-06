# Individual Report: Lab 3 - Chatbot vs ReAct Agent

- **Student Name**: Hoàng Kim Trí Thành
- **Student ID**: 2A202600372
- **Date**: 2026-04-06

---

## I. Technical Contribution (15 Points)

- **Modules Implementated**: `src/tools/weather.py`, `docs/OPENWEATHER_SETUP_VI.md`, `app.py`.
- **Code Highlights**:
  - Cải thiện weather query retry với biến thể tên thành phố.
  - Bổ sung link kiểm chứng trực tiếp và message lỗi rõ ràng.
  - Cập nhật hiển thị citation theo kết quả tool.
- **Documentation**:
  - Đồng bộ hướng dẫn cấu hình OpenWeather để hỗ trợ debug nhanh cho team.

---

## II. Debugging Case Study (10 Points)

- **Problem Description**: Agent trả lời sai lý do lỗi weather (hallucination) thay vì dùng observation thật.
- **Log Source**: `logs/YYYY-MM-DD.log` tại chuỗi `AGENT_LLM_STEP` và `AGENT_OBSERVATION`.
- **Diagnosis**: Prompt chưa đủ ràng buộc nên model bịa hạn chế API.
- **Solution**: Cập nhật system prompt: bắt buộc dựa vào Observation, không tự chế nguyên nhân kỹ thuật.

---

## III. Personal Insights: Chatbot vs ReAct (10 Points)

1. **Reasoning**: `Thought` giúp LLM chia bài toán thành từng bước rõ ràng và quyết định đúng thời điểm gọi tool.
2. **Reliability**: Agent có thể kém hơn chatbot khi tool lỗi liên tục hoặc prompt quá mơ hồ làm tăng vòng lặp.
3. **Observation**: Observation là tín hiệu phản hồi quan trọng giúp agent tự sửa Action ở bước sau thay vì trả lời đoán.

---

## IV. Future Improvements (5 Points)

- **Scalability**: Thêm tầng cache weather theo city/time.
- **Safety**: Chuẩn hóa message lỗi thân thiện nhưng trung thực dữ liệu.
- **Performance**: Giảm token qua prompt template ngắn hơn cho weather-only.

---

> [!NOTE]
> Submit this report by renaming it to `REPORT_[YOUR_NAME].md` and placing it in this folder.
