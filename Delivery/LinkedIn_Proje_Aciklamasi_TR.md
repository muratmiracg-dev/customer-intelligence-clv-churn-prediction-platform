Proje Adı: Customer Intelligence, CLV & Churn Prediction Platform

Kullanılan Araçlar: Python, SQL, Power BI, DAX, Power Query, Excel, Tableau, Scikit-learn, SHAP, FastAPI, Streamlit, SQLite, Plotly, Pytest, Ruff, GitHub Actions, Docker, PBIP

Açıklama:

- Dört yıllık sentetik perakende verisini müşteri değeri, kayıp riski ve sonraki en iyi aksiyon kararlarına dönüştüren uçtan uca müşteri zekâsı platformu geliştirdim. 6.000 müşteri, 50.639 sipariş, 103.044 sipariş satırı, 130.671 aylık etkileşim ve 12.000 kampanya yanıtından oluşan ilişkisel yapı kurdum.

- RFM segmentasyonu, M0–M12 cohort analizi, 90 günlük churn ve 12 aylık tahmine dayalı CLV için yeniden kullanılabilir müşteri kesitleri ürettim. Gelecek bilgisi sızıntısını önlemek için zaman bazlı validasyon uyguladım.

- Churn için 0,867 ROC-AUC, 0,908 PR-AUC ve ilk %10'da 1,77x lift sağlayan kalibre Random Forest; CLV için 1.258 TRY MAE, 0,564 R² ve 0,792 Spearman korelasyonuna sahip Random Forest Regressor seçtim.

- SHAP açıklamaları, olasılık kalibrasyonu, PSI drift takibi, bölge/yaş bandı adalet kontrolleri, model kartları ve otomatik veri kalitesi kapıları ekledim.

- Churn riski, CLV, RFM, pazarlama izni, beklenen yanıt, teklif maliyeti ve bütçe sınırlarını birleştiren aksiyon motoru tasarladım. 3.501 müşteriyi 236 bin TRY bütçe ve 547 bin TRY beklenen artımlı marjla önceliklendirdim.

- 12 sayfalık Power BI PBIP, 24 sayfalık formül destekli Excel planlayıcısı, Tableau workbook, SQLite veri tabanı, FastAPI, Streamlit, 20'şer sayfalık Türkçe/İngilizce sunum ve 12 sayfalık vektör HD rapor teslim ettim.

- 28 otomatik test, %100 API kapsamı, 10/10 başarılı veri kalite kontrolü ve GitHub Actions CI geliştirdim.
