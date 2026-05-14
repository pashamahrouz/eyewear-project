# 👓 اوپتیک ویژن — فروشگاه عینک

سایت فروش خرده و عمده عینک با استایل Apple، بک‌اند Flask، و دیتابیس SQLite.

-----

## ساختار پروژه

```
eyewear-project/
├── index.html          ← فرانت‌اند سایت
├── backend/
│   ├── server.py       ← بک‌اند Flask
│   ├── requirements.txt
│   ├── db/             ← دیتابیس SQLite (auto-created)
│   └── uploads/        ← فایل‌های پروانه کسب (auto-created)
└── README.md
```

-----

## نصب و اجرا

### ۱. نصب dependencies

```bash
cd backend
pip install -r requirements.txt
```

### ۲. اجرای سرور

```bash
python server.py
```

سرور روی `http://localhost:5000` بالا می‌آید.

### ۳. باز کردن سایت

فایل `index.html` را در مرورگر باز کنید.

-----

## API Endpoints

|Method|URL                         |توضیح                 |
|------|----------------------------|----------------------|
|GET   |`/api/products`             |لیست همه محصولات      |
|POST  |`/api/wholesale/apply`      |ثبت درخواست عمده‌فروشی |
|GET   |`/api/admin/requests`       |لیست درخواست‌ها (ادمین)|
|PUT   |`/api/admin/requests/<id>`  |تأیید/رد درخواست      |
|GET   |`/api/admin/stats`          |آمار داشبورد          |
|GET   |`/api/admin/file/<filename>`|دانلود پروانه کسب     |

### نمونه: ثبت درخواست عمده

```bash
curl -X POST http://localhost:5000/api/wholesale/apply \
  -F "store_name=اپتیک نور" \
  -F "phone=09121234567" \
  -F "license=@parvane.pdf"
```

### نمونه: تأیید درخواست

```bash
curl -X PUT http://localhost:5000/api/admin/requests/<id> \
  -H "Content-Type: application/json" \
  -d '{"status": "approved", "note": "پروانه تأیید شد"}'
```

-----

## ویژگی‌ها

- ✅ فروش خرده و عمده با قیمت‌های جداگانه
- ✅ دسته‌بندی عینک: آفتابی / طبی / برند
- ✅ آپلود پروانه کسب برای عمده‌فروشان
- ✅ پنل ادمین برای تأیید/رد درخواست‌ها
- ✅ دیتابیس SQLite (بدون نیاز به نصب)
- ✅ استایل Apple — فارسی RTL