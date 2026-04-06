# Hướng dẫn lấy OpenWeather API key (free)

## Bước 1 — Tạo tài khoản

1. Vào [https://home.openweathermap.org/users/sign_up](https://home.openweathermap.org/users/sign_up)
2. Đăng ký bằng email, **xác nhận email** (vào hộp thư, bấm link).

## Bước 2 — Lấy API key

1. Đăng nhập: [https://home.openweathermap.org/](https://home.openweathermap.org/)
2. Menu **API keys** (hoặc [My API keys](https://home.openweathermap.org/api_keys)).
3. Copy key (chuỗi dài ~32 ký tự hex). Có thể đặt tên key là `lab` cho dễ nhớ.

## Bước 3 — Chờ key kích hoạt (quan trọng)

- Key **free** thường **không dùng được ngay** sau khi tạo.
- OpenWeather ghi: có thể mất **10 phút đến ~2 giờ** (đôi khi lâu hơn) để key hoạt động.
- Nếu gọi API quá sớm sẽ nhận **401 Invalid API key** dù key đã copy đúng → **đợi thêm** rồi thử lại.

## Bước 4 — Gắn vào project

Trong file `.env` ở thư mục gốc repo:

```env
OPENWEATHER_API_KEY=paste_key_day_du_khong_co_dau_cach_thua
DEMO_TRAVEL_APIS=0
```

- **Không** thêm dấu nháy `'` hoặc `"` quanh key (trừ khi key có ký tự đặc biệt — thường không).
- **Không** có khoảng trắng đầu/cuối dòng.
- Biến phải đúng tên: `OPENWEATHER_API_KEY` (không phải `OPENWEATHER_KEY`).

## Bước 5 — Kiểm tra nhanh (trình duyệt hoặc curl)

Thay `YOUR_KEY` và thử trên trình duyệt:

```
https://api.openweathermap.org/data/2.5/weather?q=Da+Nang,VN&appid=YOUR_KEY&units=metric
```

- Trả JSON có `name`, `main` → key OK.
- Trả `401` + `Invalid API key` → key sai **hoặc** chưa kích hoạt (đợi / tạo key mới).

## Lỗi thường gặp

| Hiện tượng | Nguyên nhân thường gặp |
|------------|-------------------------|
| 401 Invalid API key | Key chưa active (đợi), copy thiếu ký tự, sai biến `.env`, có dấu cách thừa |
| 404 city not found | Tham số `city` sai; thử `Da Nang, VN` hoặc `Hanoi, VN` |
| 429 | Vượt quota free (60 gọi/phút theo tài liệu) — giảm tần suất test |

## API dùng trong code

- [Current weather](https://openweathermap.org/current) — `data/2.5/weather`
- [5 day forecast](https://openweathermap.org/forecast5) — `data/2.5/forecast`

Cả hai đều nằm trong gói **Free** nếu tài khoản đã bật API tương ứng (mặc định khi đăng ký developer).

## Tài liệu chính thức

- FAQ lỗi 401: [openweathermap.org/faq#error401](https://openweathermap.org/faq#error401)
- Pricing: [openweathermap.org/price](https://openweathermap.org/price)
