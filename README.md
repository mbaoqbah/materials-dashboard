# Materials & Projects Dashboard (Streamlit + SQLite)

هذا المشروع يحقق كل المتطلبات التي اتفقنا عليها:
- قاعدة بيانات للمواد (كود + وصف) قابلة للتحديث من Excel.
- حركة المواد بين المستودع وخط الإنتاج.
- مراحل المشروع مع الحالة.
- سجل عمل الموظفين وعدد الساعات.
- داشبورد تفاعلي مع مؤشرات أداء وتقارير قابلة للتنزيل.

## المتطلبات
- Python 3.10+
- تثبيت الحزم: `pip install -r requirements.txt`

## التشغيل
1) ضع ملفات البيانات (Excel) داخل مجلد `data/`، أو استخدم القوالب الجاهزة في `data/templates`.
2) شغل الـ ETL لتحميل البيانات إلى SQLite:
   ```bash
   python etl.py --materials data/materials.xlsx --movements data/movements.xlsx --phases data/phases.xlsx --worklog data/worklog.xlsx --db data/app.db
   ```
3) شغل التطبيق:
   ```bash
   streamlit run streamlit_app.py
   ```
4) افتح الرابط الذي يظهر في الطرفية (عادة http://localhost:8501).

## تحديث البيانات
- حدّث ملفات Excel ثم أعد تشغيل أمر ETL، أو استخدم واجهة الرفع داخل التطبيق لتحميل بيانات جديدة.

## مخرجات التقارير
- من داخل التطبيق، يمكنك تصدير تقارير Excel إلى مجلد `reports/` مباشرة.
