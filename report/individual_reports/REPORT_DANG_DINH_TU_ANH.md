# Individual Report: Lab 3 - Chatbot vs ReAct Agent

- **Student Name**: Đặng Đình Tú Anh
- **Student ID**: 2A202600019
- **Date**: 2026-04-06

---

## I. Technical Contribution (15 Points)

- **Modules Implementated**: `src/tools/flights.py`, `src/tools/registry.py`, `app.py`.
- **Code Highlights**:
  - Triển khai tìm vé nâng cao: crawl ưu tiên, fallback API/demo.
  - Bổ sung tool `search_roundtrip_flights`, `search_itinerary_flights`.
  - Cập nhật citation theo nguồn thực tế (crawl/API).
- **Documentation**:
  - Luồng Agent gọi tool qua `registry.py`, parse tham số an toàn, và xuất observation có metadata để LLM tổng hợp câu trả lời.

---

## II. Debugging Case Study (10 Points)

- **Problem Description**: Lỗi 422 khi tìm chuyến bay dù input nhìn đúng.
- **Log Source**: `logs/YYYY-MM-DD.log` với sự kiện `AGENT_OBSERVATION` chứa lỗi Duffel.
- **Diagnosis**: Parser chưa bóc nháy đơn nên `'SGN'` được gửi nguyên văn thành IATA không hợp lệ.
- **Solution**: Sửa parser để chuẩn hóa cả nháy đơn/nháy kép, thêm test hồi quy trong `tests/test_travel_tools.py`.

---

## III. Personal Insights: Chatbot vs ReAct (10 Points)

1. **Reasoning**: ReAct giúp chia bài toán flight phức tạp thành các bước rõ ràng thay vì suy luận một lần.
2. **Reliability**: Agent có thể kém ổn định nếu nguồn dữ liệu thời gian thực timeout hoặc trả về rỗng.
3. **Observation**: Observation là căn cứ để agent điều chỉnh tool call kế tiếp, đặc biệt ở các query nhiều chặng.

---

## IV. Future Improvements (5 Points)

- **Scalability**: Tách worker cho flight tool call bất đồng bộ và cache truy vấn tuyến lặp.
- **Safety**: Thêm lớp kiểm duyệt Action trước khi gọi API ngoài.
- **Performance**: Áp dụng schema output cứng + heuristic giảm số bước loop không cần thiết.

---

> [!NOTE]
> Submit this report by renaming it to `REPORT_[YOUR_NAME].md` and placing it in this folder.
