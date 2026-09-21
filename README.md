# Reovu Week 9 - Sentiment Analysis Sample

Proyek contoh untuk analisis sentimen (sentiment analysis) sebagai bagian dari materi Week 9.

## Deskripsi

Repositori ini digunakan untuk mengeksplorasi dan membangun model/pipeline analisis sentimen, mulai dari pengumpulan data, praproses teks, pelatihan model, hingga evaluasi hasil prediksi sentimen (positif, negatif, atau netral).

## Struktur Proyek

```
.
├── data/           # Dataset mentah dan hasil praproses
│   └── output/     # Hasil labeling (dibuat otomatis oleh skrip)
├── notebooks/      # Jupyter notebook untuk eksplorasi dan eksperimen
├── scripts/        # Skrip pemrosesan data (labeling, dsb.)
└── README.md
```

## Cara Memulai

1. Clone repositori ini
   ```bash
   git clone https://github.com/huseindra/reovu-week-9-sentiment-sample.git
   cd reovu-week-9-sentiment-sample
   ```
2. Buat virtual environment dan install dependencies (akan ditambahkan seiring perkembangan proyek)
3. Jalankan notebook atau skrip sesuai kebutuhan

## Labeling Feedback

`scripts/label_feedback.py` membaca `data/feedback.csv` dan melabeli setiap baris dengan:

- **sentiment** — `positive`, `negative`, atau `neutral`, berdasarkan kata kunci polaritas dalam pesan.
- **topic** — kategori isi pesan, misalnya `billing-payments`, `authentication`, `data-loss`,
  `reliability-outage`, `security-privacy`, `bug-stability`, `performance`, `support-response`,
  `data-request`, `feature-request`, `usability`, `onboarding`, `notifications`, `documentation`,
  `pricing-plans`, `reporting-data-accuracy`, `content-typo`, atau `general`.
- **severity** — `critical`, `high`, `medium`, atau `low`. Topik yang berdampak langsung ke akses,
  data, atau keamanan (`authentication`, `data-loss`, `reliability-outage`, `security-privacy`)
  otomatis `critical`; masalah finansial/kepatuhan (`billing-payments`, `reporting-data-accuracy`,
  `data-request`) menjadi `high`; sisanya dinilai dari kata kunci dan sentimen.

Jalankan:

```bash
python3 scripts/label_feedback.py
```

Skrip menghasilkan tiga file di `data/output/`:

- `labeled_feedback.csv` — semua baris beserta label lengkap.
- `high_critical_feedback.csv` — baris dengan severity `high` atau `critical`.
- `routine_feedback.csv` — sisanya (`medium`/`low`).

Aturan klasifikasi bersifat rule-based (keyword matching), bukan model ML, sehingga mudah
dibaca dan disesuaikan langsung di `scripts/label_feedback.py`.

## Escalation Reports

`scripts/generate_reports.py` membaca `data/output/labeled_feedback.csv` (hasil dari
`label_feedback.py`) dan menghasilkan dua file di `reports/`:

- `escalation_email_draft.txt` — draf satu email ke support lead yang merangkum semua
  baris `high`/`critical`, masing-masing dengan draf balasan yang disarankan untuk pelanggan.
- `routine_log.txt` — log teks untuk baris `medium`/`low` yang tidak perlu balasan segera.

Jalankan setelah `label_feedback.py`:

```bash
python3 scripts/label_feedback.py
python3 scripts/generate_reports.py --support-lead "<Nama Support Lead> <email@perusahaan.com>"
```

> **Catatan:** skrip ini hanya membuat **draf**. Repositori ini tidak terhubung ke layanan
> email mana pun, jadi `escalation_email_draft.txt` perlu disalin dan dikirim secara manual
> oleh support lead (atau melalui integrasi email terpisah).

## Testing

```bash
python3 -m unittest discover tests
```

Unit test di `tests/test_label_feedback.py` mencakup klasifikasi sentiment/topic/severity
serta pemisahan baris `high`/`critical` dari baris rutin, menggunakan data contoh di
`tests/fixtures/sample_feedback.csv`.

## Status

Proyek masih dalam tahap awal pengembangan.
