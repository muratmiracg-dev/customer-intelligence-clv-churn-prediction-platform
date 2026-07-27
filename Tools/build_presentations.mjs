import fs from "node:fs/promises";
import path from "node:path";
import process from "node:process";
import { Presentation, PresentationFile } from "@oai/artifact-tool";

const projectRoot = path.resolve(process.argv[2] || ".");
const dataDir = path.join(projectRoot, "Data", "Processed");
const imageDir = path.join(projectRoot, "Images");
const outputDir = path.join(projectRoot, "Presentation");

// Codex Grid-inspired 1280 × 720 layout system:
// 41–48 px outer margins, 1197 px content width, strong title rail,
// modular metric cards, image panels, tables, charts and timelines.
const C = {
  ink: "#122033",
  navy: "#071423",
  navy2: "#102238",
  blue: "#2E8BFF",
  cyan: "#2AC7E8",
  teal: "#26C6A5",
  purple: "#987CF5",
  amber: "#F5A623",
  red: "#F2556D",
  green: "#16A079",
  white: "#FFFFFF",
  canvas: "#F4F7FB",
  panel: "#FFFFFF",
  line: "#D5DFEB",
  muted: "#68778A",
  paleBlue: "#EAF3FF",
  paleCyan: "#E9F9FC",
  paleTeal: "#E8F8F4",
  palePurple: "#F0ECFF",
  paleAmber: "#FFF4DF",
  paleRed: "#FDECEF",
};

function parseCsv(text) {
  const rows = [];
  let row = [];
  let field = "";
  let quoted = false;
  for (let index = 0; index < text.length; index += 1) {
    const character = text[index];
    if (character === '"') {
      if (quoted && text[index + 1] === '"') {
        field += '"';
        index += 1;
      } else {
        quoted = !quoted;
      }
    } else if (character === "," && !quoted) {
      row.push(field);
      field = "";
    } else if ((character === "\n" || character === "\r") && !quoted) {
      if (character === "\r" && text[index + 1] === "\n") index += 1;
      row.push(field);
      if (row.some((cell) => cell !== "")) rows.push(row);
      row = [];
      field = "";
    } else {
      field += character;
    }
  }
  if (field !== "" || row.length) {
    row.push(field);
    rows.push(row);
  }
  return rows;
}

function coerce(value) {
  if (value === "") return null;
  if (value === "True" || value === "TRUE") return true;
  if (value === "False" || value === "FALSE") return false;
  if (/^-?\d+(\.\d+)?([eE][+-]?\d+)?$/.test(value)) return Number(value);
  return value;
}

async function loadCsv(filename) {
  const parsed = parseCsv(await fs.readFile(path.join(dataDir, filename), "utf8"));
  const headers = parsed[0];
  return parsed
    .slice(1)
    .map((row) =>
      Object.fromEntries(headers.map((header, index) => [header, coerce(row[index])])),
    );
}

const [
  executiveKpis,
  segments,
  cohorts,
  churnModels,
  clvModels,
  campaigns,
  shap,
  fairness,
  drift,
  monthly,
  quality,
] = await Promise.all([
  loadCsv("executive_kpis.csv"),
  loadCsv("segment_summary.csv"),
  loadCsv("cohort_retention_long.csv"),
  loadCsv("churn_model_comparison.csv"),
  loadCsv("clv_model_comparison.csv"),
  loadCsv("campaign_summary.csv"),
  loadCsv("shap_global_importance.csv"),
  loadCsv("fairness_audit.csv"),
  loadCsv("drift_monitoring.csv"),
  loadCsv("monthly_customer_metrics.csv"),
  loadCsv("data_quality_report.csv"),
]);

const KPI = Object.fromEntries(executiveKpis.map((row) => [row.kpi, Number(row.value)]));
const churnChampion = churnModels[0];
const clvChampion = clvModels[0];
const campaignPortfolio = campaigns.filter((row) => row.recommended_action !== "Suppress");
const campaignSelected = campaignPortfolio.reduce(
  (sum, row) => sum + Number(row.selected_customers || 0),
  0,
);
const dataRows = {
  customers: 6000,
  products: 48,
  orders: 50639,
  orderLines: 103044,
  interactions: 130671,
  responses: 12000,
  calendar: 1461,
};

const imageNames = [
  "executive-overview",
  "architecture",
  "customer-360",
  "rfm-segmentation",
  "cohort-retention",
  "clv-analysis",
  "churn-risk",
  "model-performance",
  "shap-explainability",
  "campaign-targeting",
];
const assets = {};
for (const name of imageNames) {
  assets[name] = await fs.readFile(path.join(imageDir, `${name}.png`));
}

const COPY = {
  en: {
    brand: "NOVARETAIL GROUP  |  CUSTOMER INTELLIGENCE",
    coverTitle: "Customer Intelligence,\nCLV & Churn Prediction Platform",
    coverSubtitle:
      "A production-style analytics portfolio connecting customer value, retention risk, explainability and next-best-action decisions",
    author: "Murat Miraç Gedik  |  Professional Portfolio Project  |  July 2026",
    notice:
      "Synthetic portfolio data • 2022–2025 • Production snapshot: 31 Dec 2025 • Currency: TRY",
    section: [
      ["Executive Decision Summary", "Value, risk, retention and campaign economics in one view"],
      ["Business Problem", "Turn fragmented customer signals into prioritized commercial action"],
      ["Scope & Deliverables", "An end-to-end analytical product, not a single dashboard"],
      ["Data Landscape", "Four years of governed, relational and privacy-safe portfolio data"],
      ["Solution Architecture", "A reproducible path from transactions to decisions"],
      ["Customer 360 & Semantic Model", "One customer-level decision record across value, risk and action"],
      ["RFM Segmentation", "Behavioral groups connect customer strategy to measurable economics"],
      ["Cohort Retention", "Acquisition quality is measured beyond the first purchase"],
      ["Predictive CLV", "Twelve-month gross-margin contribution guides value-based prioritization"],
      ["Churn Methodology", "Time-aware labels, calibration and threshold governance reduce leakage"],
      ["Risk Portfolio", "Risk tiers focus retention effort where revenue exposure is greatest"],
      ["Model Performance", "Champion selection balances discrimination, calibration and business lift"],
      ["SHAP Explainability", "Global and local drivers make risk scores operationally interpretable"],
      ["Fairness, Drift & Governance", "Responsible use requires controls after model approval"],
      ["Campaign Targeting", "Next-best-action rules convert predictions into controlled interventions"],
      ["Campaign Economics", "Budget is allocated by expected incremental margin and ROI"],
      ["Multi-Platform Delivery", "Power BI, Excel, Tableau, SQL, API and documentation work as one system"],
      ["90-Day Roadmap", "A pragmatic path from portfolio prototype to an operating capability"],
    ],
    closeTitle: "Know customer value.\nAnticipate risk.\nAct with discipline.",
    closeBody:
      "A portfolio-ready customer intelligence platform combining statistical analysis, machine learning, business intelligence, decision science and executive communication.",
    thankYou: "THANK YOU",
  },
  tr: {
    brand: "NOVARETAIL GROUP  |  MÜŞTERİ ZEKÂSI",
    coverTitle: "Müşteri Zekâsı,\nCLV ve Churn Tahmin Platformu",
    coverSubtitle:
      "Müşteri değeri, kayıp riski, açıklanabilirlik ve sonraki en iyi aksiyon kararlarını birleştiren üretim yaklaşımında analitik portföy projesi",
    author: "Murat Miraç Gedik  |  Profesyonel Portföy Projesi  |  Temmuz 2026",
    notice:
      "Sentetik portföy verisi • 2022–2025 • Üretim kesiti: 31 Ara 2025 • Para birimi: TRY",
    section: [
      ["Yönetici Karar Özeti", "Değer, risk, elde tutma ve kampanya ekonomisini tek görünümde birleştirme"],
      ["İş Problemi", "Parçalı müşteri sinyallerini önceliklendirilmiş ticari aksiyona dönüştürme"],
      ["Kapsam ve Teslimatlar", "Tek bir dashboard değil, uçtan uca analitik ürün"],
      ["Veri Kapsamı", "Dört yıllık, ilişkisel, yönetişimli ve gizlilik güvenli portföy verisi"],
      ["Çözüm Mimarisi", "İşlemlerden karara uzanan tekrarlanabilir analitik akış"],
      ["Customer 360 ve Semantik Model", "Değer, risk ve aksiyon için tek müşteri karar kaydı"],
      ["RFM Segmentasyonu", "Davranışsal grupları ölçülebilir müşteri ekonomisine bağlama"],
      ["Cohort Elde Tutma", "Müşteri edinme kalitesini ilk satın alımın ötesinde ölçme"],
      ["Tahmine Dayalı CLV", "12 aylık brüt marj katkısıyla değer bazlı önceliklendirme"],
      ["Churn Metodolojisi", "Zaman duyarlı etiket, kalibrasyon ve eşik yönetişimiyle veri sızıntısını önleme"],
      ["Risk Portföyü", "Elde tutma çabasını gelir maruziyetinin en yüksek olduğu müşterilere odaklama"],
      ["Model Performansı", "Şampiyon model seçiminde ayırt etme, kalibrasyon ve ticari kaldıracı dengeleme"],
      ["SHAP Açıklanabilirliği", "Global ve yerel sürücülerle risk skorunu yorumlanabilir hale getirme"],
      ["Adalet, Drift ve Yönetişim", "Sorumlu kullanım için model onayı sonrasında sürekli kontrol"],
      ["Kampanya Hedefleme", "Sonraki en iyi aksiyon kurallarıyla tahmini kontrollü müdahaleye dönüştürme"],
      ["Kampanya Ekonomisi", "Bütçeyi beklenen artımlı marj ve ROI üzerinden dağıtma"],
      ["Çok Platformlu Teslimat", "Power BI, Excel, Tableau, SQL, API ve dokümantasyonu tek sistemde birleştirme"],
      ["90 Günlük Yol Haritası", "Portföy prototipinden çalışan bir yetkinliğe gerçekçi geçiş"],
    ],
    closeTitle: "Müşteri değerini bil.\nRiski öngör.\nDisiplinle aksiyon al.",
    closeBody:
      "İstatistik, makine öğrenmesi, iş zekâsı, karar bilimi ve yönetici iletişimini birleştiren portföy seviyesinde müşteri zekâsı platformu.",
    thankYou: "TEŞEKKÜRLER",
  },
};

const RFM_TR = {
  Champions: "Şampiyonlar",
  "Loyal Customers": "Sadık Müşteriler",
  "Potential Loyalists": "Potansiyel Sadıklar",
  "Need Attention": "İlgi Bekleyenler",
  Hibernating: "Uykudakiler",
  Promising: "Umut Verenler",
  "At Risk": "Risk Altında",
};

const ACTION_TR = {
  "VIP Experience": "VIP Deneyimi",
  "Retain & Reward": "Elde Tut ve Ödüllendir",
  Onboarding: "Karşılama",
  "Cross-Sell": "Çapraz Satış",
  "Win-Back": "Geri Kazanım",
  Nurture: "Geliştirme",
};

function label(value, lang, dictionary) {
  return lang === "tr" ? dictionary[value] || value : value;
}

function fmtTry(value, digits = 1) {
  const number = Number(value);
  if (Math.abs(number) >= 1_000_000) return `TRY ${(number / 1_000_000).toFixed(digits)}M`;
  if (Math.abs(number) >= 1_000) return `TRY ${(number / 1_000).toFixed(digits)}K`;
  return `TRY ${number.toFixed(0)}`;
}

function fmtPct(value, digits = 1) {
  return `${(Number(value) * 100).toFixed(digits)}%`;
}

function fmtNum(value) {
  return Math.round(Number(value)).toLocaleString("en-US");
}

function addText(slide, value, position, options = {}) {
  const item = slide.shapes.add({
    geometry: "textbox",
    position,
    fill: "none",
    line: { style: "solid", fill: "none", width: 0 },
    name: options.name,
  });
  item.text = value;
  item.text.style = {
    fontFamily: "Arial",
    fontSize: options.fontSize ?? 18,
    bold: options.bold ?? false,
    color: options.color ?? C.ink,
  };
  item.text.alignment = options.align ?? "left";
  item.text.verticalAlignment = options.vertical ?? "top";
  return item;
}

function addPanel(slide, position, options = {}) {
  return slide.shapes.add({
    geometry: options.geometry ?? "roundRect",
    position,
    fill: options.fill ?? C.panel,
    line: {
      style: "solid",
      fill: options.line ?? C.line,
      width: options.lineWidth ?? 1,
    },
    borderRadius: "rounded-xl",
  });
}

function addHeader(slide, copy, page) {
  const [title, subtitle] = copy.section[page - 2];
  slide.background.fill = C.canvas;
  addText(slide, copy.brand, { left: 48, top: 25, width: 650, height: 20 }, {
    fontSize: 11,
    bold: true,
    color: C.blue,
  });
  addText(slide, title, { left: 48, top: 53, width: 780, height: 52 }, {
    fontSize: 33,
    bold: true,
    color: C.navy,
  });
  addText(slide, subtitle, { left: 838, top: 56, width: 394, height: 48 }, {
    fontSize: 13,
    color: C.muted,
    align: "right",
  });
  slide.shapes.add({
    geometry: "rect",
    position: { left: 48, top: 116, width: 1184, height: 3 },
    fill: C.blue,
    line: { style: "solid", fill: C.blue, width: 0 },
  });
  addText(slide, String(page).padStart(2, "0"), { left: 1180, top: 680, width: 52, height: 18 }, {
    fontSize: 10,
    bold: true,
    color: C.muted,
    align: "right",
  });
}

function addFooter(slide, copy) {
  addText(slide, copy.notice, { left: 48, top: 680, width: 900, height: 16 }, {
    fontSize: 9,
    color: C.muted,
  });
}

function projectSources(...files) {
  return files.map((file) => `Internal synthetic project source: ${file}`);
}

function addNotes(slide, sources, note = "") {
  const body = [
    note,
    "[Sources]",
    ...sources.map((source) => `- ${source}`),
    "[/Sources]",
  ]
    .filter(Boolean)
    .join("\n");
  slide.speakerNotes.textFrame.setText(body);
  slide.speakerNotes.setVisible(true);
}

function metricCard(slide, x, y, width, labelText, value, note, accent = C.blue, height = 132) {
  addPanel(slide, { left: x, top: y, width, height }, { fill: C.white });
  slide.shapes.add({
    geometry: "rect",
    position: { left: x, top: y, width: 7, height },
    fill: accent,
    line: { style: "solid", fill: accent, width: 0 },
  });
  addText(slide, labelText.toUpperCase(), {
    left: x + 20,
    top: y + 17,
    width: width - 36,
    height: 18,
  }, { fontSize: 10, bold: true, color: C.muted });
  addText(slide, value, {
    left: x + 20,
    top: y + 43,
    width: width - 36,
    height: 38,
  }, { fontSize: 25, bold: true, color: accent });
  addText(slide, note, {
    left: x + 20,
    top: y + 90,
    width: width - 36,
    height: height - 98,
  }, { fontSize: 10, color: C.muted });
}

function insightBox(slide, x, y, width, height, title, body, accent = C.blue, fill = C.paleBlue) {
  addPanel(slide, { left: x, top: y, width, height }, { fill, line: accent });
  slide.shapes.add({
    geometry: "rect",
    position: { left: x, top: y, width: 6, height },
    fill: accent,
    line: { style: "solid", fill: accent, width: 0 },
  });
  addText(slide, title, {
    left: x + 20,
    top: y + 16,
    width: width - 38,
    height: 25,
  }, { fontSize: 15, bold: true, color: accent });
  addText(slide, body, {
    left: x + 20,
    top: y + 49,
    width: width - 38,
    height: height - 60,
  }, { fontSize: 13, color: C.ink });
}

function bulletList(slide, items, x, y, width, options = {}) {
  const rowHeight = options.rowHeight ?? 50;
  items.forEach((item, index) => {
    const top = y + index * rowHeight;
    slide.shapes.add({
      geometry: "ellipse",
      position: { left: x, top: top + 5, width: 10, height: 10 },
      fill: options.accent ?? C.blue,
      line: { style: "solid", fill: options.accent ?? C.blue, width: 0 },
    });
    addText(slide, item, {
      left: x + 23,
      top,
      width: width - 23,
      height: rowHeight - 2,
    }, { fontSize: options.fontSize ?? 16, color: options.color ?? C.ink });
  });
}

function addImage(slide, bytes, position, alt, fit = "contain") {
  addPanel(slide, position, { fill: C.navy, line: C.line });
  return slide.images.add({
    blob: bytes,
    contentType: "image/png",
    alt,
    fit,
    position,
    geometry: "roundRect",
    borderRadius: "rounded-xl",
  });
}

function simpleTable(slide, x, y, widths, headers, rows, options = {}) {
  const rowHeight = options.rowHeight ?? 34;
  const totalWidth = widths.reduce((sum, width) => sum + width, 0);
  slide.shapes.add({
    geometry: "rect",
    position: { left: x, top: y, width: totalWidth, height: rowHeight },
    fill: C.navy,
    line: { style: "solid", fill: C.navy, width: 0 },
  });
  let cursor = x;
  headers.forEach((header, index) => {
    addText(slide, header, {
      left: cursor + 7,
      top: y + 8,
      width: widths[index] - 14,
      height: rowHeight - 10,
    }, { fontSize: options.headerSize ?? 10, bold: true, color: C.white });
    cursor += widths[index];
  });
  rows.forEach((row, rowIndex) => {
    const top = y + (rowIndex + 1) * rowHeight;
    slide.shapes.add({
      geometry: "rect",
      position: { left: x, top, width: totalWidth, height: rowHeight },
      fill: rowIndex % 2 ? C.canvas : C.white,
      line: { style: "solid", fill: C.line, width: 0.5 },
    });
    let cellLeft = x;
    row.forEach((value, index) => {
      addText(slide, String(value), {
        left: cellLeft + 7,
        top: top + 7,
        width: widths[index] - 14,
        height: rowHeight - 10,
      }, { fontSize: options.fontSize ?? 10, color: C.ink });
      cellLeft += widths[index];
    });
  });
}

function addBarChart(slide, position, categories, series, options = {}) {
  return slide.charts.add("bar", {
    position,
    categories,
    series: series.map((item) => ({
      name: item.name,
      categories,
      values: item.values,
      fill: item.color,
    })),
    hasLegend: options.hasLegend ?? series.length > 1,
    legend: { position: "bottom", overlay: false },
    dataLabels: {
      showValue: options.showValue ?? true,
      position: "outEnd",
      numberFormatCode: options.valueFormat ?? "0.0",
    },
    chartFill: C.white,
    chartLine: { style: "solid", width: 0, fill: C.white },
    plotAreaFill: { type: "none" },
    plotAreaLine: { style: "solid", width: 0, fill: C.white },
    xAxis: {
      visible: true,
      line: { style: "solid", width: 1, fill: C.line },
      textStyle: { typeface: "Arial", fontSize: "10px", color: C.muted },
    },
    yAxis: {
      visible: true,
      min: 0,
      numberFormatCode: options.axisFormat ?? "0.0",
      majorGridlines: { style: "solid", width: 1, fill: C.line },
      line: { style: "solid", width: 0, fill: C.white },
      textStyle: { typeface: "Arial", fontSize: "10px", color: C.muted },
    },
    barOptions: {
      direction: options.horizontal ? "bar" : "column",
      grouping: options.grouping ?? "clustered",
      gapWidth: 72,
    },
  });
}

function processRow(slide, items, y) {
  const width = 205;
  const gap = 30;
  const fills = [C.paleBlue, C.paleCyan, C.paleTeal, C.palePurple, C.paleAmber];
  const accents = [C.blue, C.cyan, C.teal, C.purple, C.amber];
  items.forEach((item, index) => {
    const x = 48 + index * (width + gap);
    addPanel(slide, { left: x, top: y, width, height: 154 }, {
      fill: fills[index],
      line: accents[index],
    });
    addText(slide, String(index + 1).padStart(2, "0"), {
      left: x + 16,
      top: y + 15,
      width: 42,
      height: 22,
    }, { fontSize: 13, bold: true, color: accents[index] });
    addText(slide, item[0], {
      left: x + 16,
      top: y + 48,
      width: width - 32,
      height: 38,
    }, { fontSize: 16, bold: true, color: C.navy });
    addText(slide, item[1], {
      left: x + 16,
      top: y + 96,
      width: width - 32,
      height: 44,
    }, { fontSize: 10, color: C.muted });
    if (index < items.length - 1) {
      addText(slide, "→", {
        left: x + width + 7,
        top: y + 58,
        width: 18,
        height: 26,
      }, { fontSize: 20, bold: true, color: C.muted, align: "center" });
    }
  });
}

function createDeck(lang) {
  const copy = COPY[lang];
  const tr = lang === "tr";
  const presentation = Presentation.create({ slideSize: { width: 1280, height: 720 } });

  // 1 — Cover: Codex Grid slide-02 / slide-26 inspired.
  {
    const slide = presentation.slides.add();
    slide.background.fill = C.navy;
    slide.shapes.add({
      geometry: "rect",
      position: { left: 944, top: 0, width: 336, height: 720 },
      fill: C.blue,
      line: { style: "solid", fill: C.blue, width: 0 },
    });
    slide.shapes.add({
      geometry: "ellipse",
      position: { left: 1030, top: 115, width: 185, height: 185 },
      fill: C.teal,
      line: { style: "solid", fill: C.teal, width: 0 },
      opacity: 0.82,
    });
    slide.shapes.add({
      geometry: "ellipse",
      position: { left: 984, top: 350, width: 260, height: 260 },
      fill: C.purple,
      line: { style: "solid", fill: C.purple, width: 0 },
      opacity: 0.58,
    });
    addText(slide, copy.brand, { left: 56, top: 43, width: 680, height: 24 }, {
      fontSize: 12,
      bold: true,
      color: "#8FD8FF",
    });
    addText(slide, copy.coverTitle, { left: 56, top: 157, width: 840, height: 205 }, {
      fontSize: 50,
      bold: true,
      color: C.white,
    });
    addText(slide, copy.coverSubtitle, { left: 56, top: 390, width: 785, height: 95 }, {
      fontSize: 19,
      color: "#D8E6F6",
    });
    addText(slide, copy.author, { left: 56, top: 552, width: 760, height: 28 }, {
      fontSize: 14,
      color: C.white,
    });
    addText(slide, copy.notice, { left: 56, top: 660, width: 820, height: 18 }, {
      fontSize: 10,
      color: "#B7C7D9",
    });
    addText(slide, "RFM\nCLV\nCHURN\nSHAP", {
      left: 1000,
      top: 184,
      width: 225,
      height: 360,
    }, { fontSize: 30, bold: true, color: C.white, align: "center", vertical: "middle" });
    addNotes(slide, projectSources("README.md", "Models/model_metadata.json"));
  }

  // 2 — Executive summary: Codex Grid metric-card layout.
  {
    const slide = presentation.slides.add();
    addHeader(slide, copy, 2);
    metricCard(slide, 48, 148, 276, tr ? "Müşteriler" : "Customers", fmtNum(KPI.Customers), tr ? "4.067 aktif müşteri / 12 ay" : "4,067 active customers / 12M", C.blue, 118);
    metricCard(slide, 344, 148, 276, tr ? "Net Gelir / 12 Ay" : "Net Revenue / 12M", fmtTry(KPI["Net Revenue 12M"]), tr ? "%21,3 brüt marj oranı" : "21.3% gross-margin rate", C.teal, 118);
    metricCard(slide, 640, 148, 276, tr ? "Tahmini CLV / 12 Ay" : "Predicted CLV / 12M", fmtTry(KPI["Predicted CLV 12M"]), tr ? "İleri 12 aylık brüt marj katkısı" : "Forward gross-margin contribution", C.purple, 118);
    metricCard(slide, 936, 148, 296, tr ? "Kampanya Potansiyeli" : "Campaign Upside", fmtTry(KPI["Expected Incremental Margin"], 0), tr ? "236 bin TRY tahsis edilen bütçe" : "TRY 236K allocated budget", C.amber, 118);
    addImage(slide, assets["executive-overview"], {
      left: 48,
      top: 292,
      width: 708,
      height: 354,
    }, "Executive customer intelligence dashboard");
    insightBox(
      slide,
      782,
      292,
      450,
      168,
      tr ? "Yönetim mesajı" : "Management message",
      tr
        ? `Portföyün ${fmtNum(KPI["High/Critical Risk Customers"])} müşterisi yüksek veya kritik riskte ve ${fmtTry(KPI["Revenue at Risk"])} gelir maruziyeti taşıyor. Risk tek başına yeterli değil; değer ve müdahale ekonomisiyle birlikte okunmalı.`
        : `${fmtNum(KPI["High/Critical Risk Customers"])} customers are high or critical risk, representing ${fmtTry(KPI["Revenue at Risk"])} of revenue exposure. Risk should be read together with value and intervention economics.`,
      C.red,
      C.paleRed,
    );
    insightBox(
      slide,
      782,
      478,
      450,
      168,
      tr ? "Karar önceliği" : "Decision priority",
      tr
        ? `${fmtNum(campaignSelected)} müşteri için aksiyon önceliği oluşturuldu. Şampiyon churn modeli ${churnChampion.roc_auc.toFixed(3)} ROC-AUC ve ilk %10'da ${churnChampion.lift_at_10pct.toFixed(2)}x lift üretiyor.`
        : `${fmtNum(campaignSelected)} customers are prioritized for action. The churn champion delivers ${churnChampion.roc_auc.toFixed(3)} ROC-AUC and ${churnChampion.lift_at_10pct.toFixed(2)}x lift in the top decile.`,
      C.teal,
      C.paleTeal,
    );
    addFooter(slide, copy);
    addNotes(slide, projectSources("Data/Processed/executive_kpis.csv", "Images/executive-overview.png"));
  }

  // 3 — Business problem.
  {
    const slide = presentation.slides.add();
    addHeader(slide, copy, 3);
    const cards = tr
      ? [
          ["Parçalı müşteri görünümü", "Satın alma, dijital etkileşim, destek ve kampanya sinyalleri ayrı kaldığında müşteri değeri eksik okunur."],
          ["Reaktif churn yönetimi", "Müşteriyi kaybettikten sonra aksiyon almak, elde tutma bütçesini verimsizleştirir."],
          ["Değerden bağımsız hedefleme", "Yalnızca risk skoru kullanmak düşük değerli müşterilere aşırı yatırım yapılmasına yol açabilir."],
          ["Açıklanabilirlik ve kontrol", "Model çıktısı, nedenleri ve kullanım sınırları görünür değilse iş birimleri güvenemez."],
        ]
      : [
          ["Fragmented customer view", "Customer value is incomplete when purchase, digital, support and campaign signals remain disconnected."],
          ["Reactive churn management", "Acting after the customer leaves makes retention spend inefficient."],
          ["Value-blind targeting", "Using risk alone can overinvest in low-value customers and miss profitable interventions."],
          ["Explainability and control", "Business teams cannot trust a score when its drivers and usage boundaries are invisible."],
        ];
    cards.forEach((item, index) => {
      const x = 48 + (index % 2) * 594;
      const y = 150 + Math.floor(index / 2) * 205;
      insightBox(
        slide,
        x,
        y,
        570,
        176,
        item[0],
        item[1],
        [C.blue, C.cyan, C.amber, C.red][index],
        [C.paleBlue, C.paleCyan, C.paleAmber, C.paleRed][index],
      );
    });
    insightBox(
      slide,
      48,
      575,
      1164,
      72,
      tr ? "Temel karar sorusu" : "Core decision question",
      tr
        ? "Hangi müşteriye, ne zaman, hangi teklifle ve hangi bütçeyle müdahale etmeliyiz?"
        : "Which customer should receive which intervention, at what time and with what budget?",
      C.navy,
      C.white,
    );
    addFooter(slide, copy);
    addNotes(slide, projectSources("Docs/methodology.md", "Docs/campaign_playbook.md"));
  }

  // 4 — Scope and deliverables.
  {
    const slide = presentation.slides.add();
    addHeader(slide, copy, 4);
    processRow(
      slide,
      tr
        ? [
            ["Veri", "Sentetik ama ilişkisel CRM, sipariş ve etkileşim verisi"],
            ["Analitik", "RFM, cohort, CLV, churn ve SHAP"],
            ["Karar", "Risk × değer × ROI hedefleme mantığı"],
            ["Teslimat", "BI, Excel, API, SQL ve raporlama"],
            ["Kontrol", "Test, drift, adalet ve dokümantasyon"],
          ]
        : [
            ["Data", "Synthetic but relational CRM, order and interaction data"],
            ["Analytics", "RFM, cohort, CLV, churn and SHAP"],
            ["Decision", "Risk × value × ROI targeting logic"],
            ["Delivery", "BI, Excel, API, SQL and reporting"],
            ["Control", "Testing, drift, fairness and documentation"],
          ],
      154,
    );
    const deliverables = tr
      ? [
          "12 sayfalık Power BI PBIP ve DAX ölçü kütüphanesi",
          "24 sayfalık formül destekli Excel kampanya planlama modeli",
          "Tableau workbook, Streamlit uygulaması ve FastAPI skorlama servisi",
          "20'şer sayfalık Türkçe/İngilizce sunum ve vektör HD rapor",
        ]
      : [
          "12-page Power BI PBIP plus reusable DAX measure library",
          "24-sheet formula-backed Excel campaign planning model",
          "Tableau workbook, Streamlit app and FastAPI scoring service",
          "20-slide English/Turkish decks and vector HD report",
        ];
    bulletList(slide, deliverables, 70, 385, 585, { fontSize: 16, rowHeight: 52 });
    insightBox(
      slide,
      690,
      375,
      522,
      220,
      tr ? "Portföy gücü" : "Portfolio strength",
      tr
        ? "Proje yalnızca tahmin üretmiyor; veri mühendisliği, model değerlendirme, açıklanabilirlik, iş kuralı, görselleştirme, API, test ve yönetişimi tek ürün yaklaşımında birleştiriyor."
        : "The project does more than generate predictions: it unifies data engineering, model evaluation, explainability, business rules, visualization, API delivery, testing and governance in one product approach.",
      C.purple,
      C.palePurple,
    );
    addFooter(slide, copy);
    addNotes(slide, projectSources("README.md", "PowerBI/Customer_Intelligence_PBIP.zip", "Excel/Customer_Intelligence_CLV_Churn_Campaign_Planner.xlsx"));
  }

  // 5 — Data landscape.
  {
    const slide = presentation.slides.add();
    addHeader(slide, copy, 5);
    const cards = tr
      ? [
          [fmtNum(dataRows.customers), "Müşteri", "Demografi, izin ve sadakat"],
          [fmtNum(dataRows.orders), "Sipariş", "4 yıllık ticari geçmiş"],
          [fmtNum(dataRows.orderLines), "Sipariş satırı", "Ürün ve marj granülerliği"],
          [fmtNum(dataRows.interactions), "Aylık etkileşim", "Oturum, e-posta ve destek"],
          [fmtNum(dataRows.responses), "Kampanya yanıtı", "Kontrollü tepki geçmişi"],
          [fmtNum(dataRows.calendar), "Takvim günü", "Zaman zekâsı omurgası"],
        ]
      : [
          [fmtNum(dataRows.customers), "Customers", "Demographics, consent and loyalty"],
          [fmtNum(dataRows.orders), "Orders", "Four-year commercial history"],
          [fmtNum(dataRows.orderLines), "Order lines", "Product and margin granularity"],
          [fmtNum(dataRows.interactions), "Monthly interactions", "Sessions, email and support"],
          [fmtNum(dataRows.responses), "Campaign responses", "Controlled response history"],
          [fmtNum(dataRows.calendar), "Calendar days", "Time-intelligence backbone"],
        ];
    cards.forEach((item, index) => {
      const x = 48 + (index % 3) * 397;
      const y = 148 + Math.floor(index / 3) * 183;
      metricCard(slide, x, y, 365, item[1], item[0], item[2], [C.blue, C.cyan, C.teal, C.purple, C.amber, C.green][index], 151);
    });
    insightBox(
      slide,
      48,
      535,
      1164,
      112,
      tr ? "Gizlilik tasarımı" : "Privacy by design",
      tr
        ? "Veri tamamen sentetiktir; gerçek kişi bilgisi içermez. Müşteri anahtarları anonimdir, pazarlama izni özellik ve hedefleme katmanlarında açık bir kontrol olarak tutulur."
        : "The dataset is fully synthetic and contains no real personal data. Customer keys are anonymous, while marketing consent remains an explicit feature and targeting control.",
      C.teal,
      C.paleTeal,
    );
    addFooter(slide, copy);
    addNotes(slide, projectSources("Data/Raw/dim_customers.csv", "Data/Raw/fact_orders.csv", "Models/model_metadata.json"));
  }

  // 6 — Architecture image.
  {
    const slide = presentation.slides.add();
    addHeader(slide, copy, 6);
    addImage(slide, assets.architecture, { left: 48, top: 145, width: 820, height: 492 }, "Customer intelligence platform architecture");
    insightBox(
      slide,
      894,
      145,
      338,
      148,
      tr ? "Analitik katman" : "Analytical layer",
      tr
        ? "Python ile özellik üretimi, RFM/cohort analizi, churn sınıflandırması, CLV regresyonu ve SHAP açıklamaları."
        : "Python feature engineering, RFM/cohort analysis, churn classification, CLV regression and SHAP explanations.",
      C.blue,
      C.paleBlue,
    );
    insightBox(
      slide,
      894,
      312,
      338,
      148,
      tr ? "Karar katmanı" : "Decision layer",
      tr
        ? "Risk, değer, izin, maliyet ve beklenen marjı birleştiren sonraki en iyi aksiyon kuralları."
        : "Next-best-action rules combining risk, value, consent, cost and expected margin.",
      C.teal,
      C.paleTeal,
    );
    insightBox(
      slide,
      894,
      479,
      338,
      158,
      tr ? "Teslimat katmanı" : "Delivery layer",
      tr
        ? "Power BI, Excel, Tableau, Streamlit, FastAPI, SQL ve yönetici raporlaması."
        : "Power BI, Excel, Tableau, Streamlit, FastAPI, SQL and executive reporting.",
      C.purple,
      C.palePurple,
    );
    addFooter(slide, copy);
    addNotes(slide, projectSources("Images/architecture.png", "Python/src/customer_intelligence/pipeline.py", "SQL/schema.sql"));
  }

  // 7 — Customer 360.
  {
    const slide = presentation.slides.add();
    addHeader(slide, copy, 7);
    addImage(slide, assets["customer-360"], { left: 48, top: 148, width: 735, height: 468 }, "Customer 360 analytical dashboard");
    const fields = tr
      ? [
          ["Kim?", "Bölge, kanal, sadakat seviyesi ve pazarlama izni"],
          ["Ne yaptı?", "12 aylık sipariş, gelir, marj ve iade davranışı"],
          ["Değeri ne?", "RFM segmenti, CLV tahmini ve değer bandı"],
          ["Riski ne?", "90 günlük churn olasılığı, risk bandı ve SHAP nedenleri"],
          ["Ne yapmalı?", "Önerilen aksiyon, teklif maliyeti ve beklenen ROI"],
        ]
      : [
          ["Who?", "Region, channel, loyalty tier and marketing consent"],
          ["What happened?", "12-month orders, revenue, margin and returns"],
          ["What is the value?", "RFM segment, CLV forecast and value band"],
          ["What is the risk?", "90-day churn probability, risk tier and SHAP reasons"],
          ["What next?", "Recommended action, treatment cost and expected ROI"],
        ];
    fields.forEach((item, index) => {
      insightBox(
        slide,
        810,
        148 + index * 94,
        422,
        82,
        item[0],
        item[1],
        [C.blue, C.cyan, C.teal, C.purple, C.amber][index],
        C.white,
      );
    });
    addFooter(slide, copy);
    addNotes(slide, projectSources("Data/Processed/customer_360.csv", "Images/customer-360.png", "PowerBI/Customer_Intelligence_PBIP/Customer_Intelligence_Analytics.SemanticModel/model.bim"));
  }

  // 8 — RFM.
  {
    const slide = presentation.slides.add();
    addHeader(slide, copy, 8);
    addImage(slide, assets["rfm-segmentation"], { left: 48, top: 145, width: 780, height: 500 }, "RFM segmentation dashboard");
    const topSegments = [...segments].sort((a, b) => b.predicted_clv_12m - a.predicted_clv_12m).slice(0, 3);
    topSegments.forEach((row, index) => {
      metricCard(
        slide,
        854,
        145 + index * 145,
        378,
        label(row.rfm_segment, lang, RFM_TR),
        fmtTry(row.predicted_clv_12m),
        `${fmtNum(row.customers)} ${tr ? "müşteri" : "customers"} • ${fmtPct(row.average_churn_probability)} ${tr ? "risk" : "risk"}`,
        [C.purple, C.blue, C.teal][index],
        126,
      );
    });
    insightBox(
      slide,
      854,
      580,
      378,
      65,
      tr ? "Ticari yorum" : "Commercial interpretation",
      tr
        ? "Şampiyonlar CLV portföyünün temelini oluştururken risk altındaki gruplarda seçici geri kazanım gerekir."
        : "Champions anchor the CLV portfolio; at-risk groups require selective, economics-led win-back.",
      C.amber,
      C.paleAmber,
    );
    addFooter(slide, copy);
    addNotes(slide, projectSources("Data/Processed/rfm_scores.csv", "Data/Processed/segment_summary.csv", "Images/rfm-segmentation.png"));
  }

  // 9 — Cohort retention.
  {
    const slide = presentation.slides.add();
    addHeader(slide, copy, 9);
    addImage(slide, assets["cohort-retention"], { left: 48, top: 145, width: 830, height: 500 }, "Cohort retention heatmap and trend");
    metricCard(slide, 904, 145, 328, tr ? "3. Ay Elde Tutma" : "Month-3 Retention", fmtPct(KPI["M3 Cohort Retention"]), tr ? "Tüm cohort ortalaması" : "Average across cohorts", C.teal, 126);
    metricCard(slide, 904, 289, 328, tr ? "Cohort Ufku" : "Cohort Horizon", "M0–M12", tr ? "İlk satın alımdan sonraki aylar" : "Months after first purchase", C.blue, 126);
    insightBox(
      slide,
      904,
      433,
      328,
      212,
      tr ? "Nasıl kullanılır?" : "How to use it",
      tr
        ? "Kazanım aylarını karşılaştır; erken dönem düşüşleri kanal, teklif ve onboarding kalitesiyle ilişkilendir; yalnızca toplam aktif müşteri sayısına bakma."
        : "Compare acquisition months, link early decay to channel, offer and onboarding quality, and avoid relying on aggregate active-customer counts alone.",
      C.purple,
      C.palePurple,
    );
    addFooter(slide, copy);
    addNotes(slide, projectSources("Data/Processed/cohort_retention_matrix.csv", "Data/Processed/cohort_retention_long.csv", "Images/cohort-retention.png"));
  }

  // 10 — CLV.
  {
    const slide = presentation.slides.add();
    addHeader(slide, copy, 10);
    addImage(slide, assets["clv-analysis"], { left: 48, top: 145, width: 775, height: 500 }, "Predictive CLV analysis dashboard");
    metricCard(slide, 849, 145, 383, tr ? "Şampiyon Model" : "Champion Model", "Random Forest", tr ? "12 aylık brüt marj hedefi" : "12-month gross-margin target", C.purple, 120);
    metricCard(slide, 849, 281, 183, "MAE", fmtTry(clvChampion.mae, 1), tr ? "Holdout hatası" : "Holdout error", C.blue, 120);
    metricCard(slide, 1049, 281, 183, "R²", clvChampion.r2.toFixed(3), tr ? "Açıklanan varyans" : "Explained variance", C.teal, 120);
    metricCard(slide, 849, 417, 183, tr ? "Spearman" : "Spearman", clvChampion.spearman_correlation.toFixed(3), tr ? "Sıralama gücü" : "Ranking power", C.amber, 120);
    metricCard(slide, 1049, 417, 183, tr ? "Portföy CLV" : "Portfolio CLV", fmtTry(KPI["Predicted CLV 12M"]), tr ? "İleri 12 ay" : "Forward 12M", C.purple, 120);
    insightBox(
      slide,
      849,
      553,
      383,
      92,
      tr ? "Karar kullanımı" : "Decision use",
      tr
        ? "CLV; teklif maliyeti, hizmet seviyesi ve elde tutma bütçesi için öncelik katsayısıdır."
        : "CLV is a prioritization factor for offer cost, service level and retention budget.",
      C.teal,
      C.paleTeal,
    );
    addFooter(slide, copy);
    addNotes(slide, projectSources("Data/Processed/clv_model_comparison.csv", "Data/Processed/clv_predictions.csv", "Images/clv-analysis.png"));
  }

  // 11 — Churn methodology: Codex Grid timeline.
  {
    const slide = presentation.slides.add();
    addHeader(slide, copy, 11);
    processRow(
      slide,
      tr
        ? [
            ["Kesit üret", "2024 çeyrek kesitleriyle geçmiş özellikler"],
            ["Etiketle", "İleri 90 günde satın alma yoksa churn"],
            ["Doğrula", "31 Ara 2024 zaman bazlı holdout"],
            ["Kalibre et", "Olasılık kalitesi ve F1 eşiği"],
            ["Üretime al", "31 Ara 2025 müşteri skoru"],
          ]
        : [
            ["Build snapshots", "Historical features from 2024 quarterly cutoffs"],
            ["Label", "No purchase in next 90 days means churn"],
            ["Validate", "31 Dec 2024 time-based holdout"],
            ["Calibrate", "Probability quality and F1 threshold"],
            ["Score", "31 Dec 2025 customer portfolio"],
          ],
      158,
    );
    metricCard(slide, 48, 375, 276, tr ? "Özellik" : "Features", "16", tr ? "Davranış, değer ve etkileşim" : "Behavior, value and engagement", C.blue, 128);
    metricCard(slide, 344, 375, 276, tr ? "Tahmin Ufku" : "Prediction Horizon", "90 days", tr ? "İleriye dönük churn etiketi" : "Forward-looking churn label", C.cyan, 128);
    metricCard(slide, 640, 375, 276, tr ? "Karar Eşiği" : "Decision Threshold", churnChampion.threshold.toFixed(2), tr ? "Holdout öncesi eğitim setinde seçildi" : "Selected on training data before holdout", C.amber, 128);
    metricCard(slide, 936, 375, 296, tr ? "Kalibrasyon" : "Calibration", "Brier 0.145", tr ? "Olasılık güvenilirliği" : "Probability reliability", C.teal, 128);
    insightBox(
      slide,
      48,
      535,
      1184,
      103,
      tr ? "Sızıntı kontrolü" : "Leakage control",
      tr
        ? "Her özellik yalnızca kesit tarihine kadar olan bilgiden üretilir. Eşik seçimi ve model karşılaştırması, üretim kesitinden önce tamamlanır."
        : "Every feature uses information available by the snapshot date. Threshold selection and model comparison are completed before the production snapshot.",
      C.red,
      C.paleRed,
    );
    addFooter(slide, copy);
    addNotes(slide, projectSources("Python/src/customer_intelligence/features.py", "Python/src/customer_intelligence/modeling.py", "Models/model_metadata.json"));
  }

  // 12 — Risk portfolio.
  {
    const slide = presentation.slides.add();
    addHeader(slide, copy, 12);
    addImage(slide, assets["churn-risk"], { left: 48, top: 145, width: 820, height: 500 }, "Churn risk portfolio dashboard");
    metricCard(slide, 894, 145, 338, tr ? "Yüksek / Kritik" : "High / Critical", fmtNum(KPI["High/Critical Risk Customers"]), tr ? "Müşteri" : "Customers", C.red, 126);
    metricCard(slide, 894, 289, 338, tr ? "Riskteki Gelir" : "Revenue at Risk", fmtTry(KPI["Revenue at Risk"]), tr ? "Son 12 ay gelir maruziyeti" : "Last-12-month revenue exposure", C.amber, 126);
    insightBox(
      slide,
      894,
      433,
      338,
      212,
      tr ? "Öncelik mantığı" : "Priority logic",
      tr
        ? "Kritik risk otomatik olarak yüksek harcama anlamına gelmez. CLV, marj, izin ve beklenen tepki birlikte değerlendirilir; düşük ekonomik değerli kayıtlar bastırılabilir."
        : "Critical risk does not automatically justify high spend. CLV, margin, consent and expected response are evaluated together; low-economic-value records may be suppressed.",
      C.purple,
      C.palePurple,
    );
    addFooter(slide, copy);
    addNotes(slide, projectSources("Data/Processed/churn_predictions.csv", "Data/Processed/risk_bands.csv", "Images/churn-risk.png"));
  }

  // 13 — Model performance.
  {
    const slide = presentation.slides.add();
    addHeader(slide, copy, 13);
    addImage(slide, assets["model-performance"], { left: 48, top: 145, width: 785, height: 500 }, "Model performance and validation dashboard");
    metricCard(slide, 859, 145, 176, "ROC-AUC", churnChampion.roc_auc.toFixed(3), tr ? "Ayırt etme" : "Discrimination", C.blue, 118);
    metricCard(slide, 1056, 145, 176, "PR-AUC", churnChampion.pr_auc.toFixed(3), tr ? "Dengesiz sınıf" : "Imbalanced class", C.teal, 118);
    metricCard(slide, 859, 281, 176, tr ? "İlk %10 Lift" : "Top-10% Lift", `${churnChampion.lift_at_10pct.toFixed(2)}x`, tr ? "Hedefleme gücü" : "Targeting power", C.amber, 118);
    metricCard(slide, 1056, 281, 176, "F1", churnChampion.f1.toFixed(3), tr ? "Denge metriği" : "Balance metric", C.purple, 118);
    insightBox(
      slide,
      859,
      417,
      373,
      228,
      tr ? "Şampiyon seçim yaklaşımı" : "Champion selection approach",
      tr
        ? "Random Forest kalibre edilerek en güçlü birleşik seçimi oluşturdu. Seçim yalnızca ROC-AUC'a dayanmadı; PR-AUC, Brier, F1, lift ve karar eşiği birlikte değerlendirildi."
        : "Calibrated Random Forest produced the strongest combined result. Selection was not based on ROC-AUC alone: PR-AUC, Brier, F1, lift and the operating threshold were considered together.",
      C.blue,
      C.paleBlue,
    );
    addFooter(slide, copy);
    addNotes(slide, projectSources("Data/Processed/churn_model_comparison.csv", "Data/Processed/churn_calibration.csv", "Images/model-performance.png"));
  }

  // 14 — SHAP.
  {
    const slide = presentation.slides.add();
    addHeader(slide, copy, 14);
    addImage(slide, assets["shap-explainability"], { left: 48, top: 145, width: 805, height: 500 }, "SHAP churn explainability dashboard");
    const top = shap.slice(0, 3);
    top.forEach((row, index) => {
      metricCard(
        slide,
        879,
        145 + index * 136,
        353,
        row.feature.replaceAll("_", " "),
        fmtPct(row.importance_share),
        tr ? "Global önem payı" : "Global importance share",
        [C.red, C.amber, C.purple][index],
        118,
      );
    });
    insightBox(
      slide,
      879,
      553,
      353,
      92,
      tr ? "Kullanım sınırı" : "Usage boundary",
      tr
        ? "SHAP ilişkiyi açıklar; nedensellik iddiası değildir. İnsan incelemesi ve kampanya kuralları skorun üzerinde kalır."
        : "SHAP explains model association, not causality. Human review and campaign controls remain above the score.",
      C.teal,
      C.paleTeal,
    );
    addFooter(slide, copy);
    addNotes(slide, projectSources("Data/Processed/shap_global_importance.csv", "Data/Processed/shap_local_explanations.csv", "Python/src/customer_intelligence/explainability.py"));
  }

  // 15 — Fairness and drift.
  {
    const slide = presentation.slides.add();
    addHeader(slide, copy, 15);
    const regionRows = fairness.filter((row) => row.audit_attribute === "region").slice(0, 6);
    simpleTable(
      slide,
      48,
      155,
      [190, 110, 145, 145, 145],
      tr
        ? ["Bölge", "Müşteri", "Gözlenen Churn", "Ort. Risk", "ROC-AUC"]
        : ["Region", "Customers", "Observed Churn", "Avg Risk", "ROC-AUC"],
      regionRows.map((row) => [
        row.audit_group,
        fmtNum(row.customers),
        fmtPct(row.observed_churn_rate),
        fmtPct(row.average_predicted_risk),
        Number(row.roc_auc).toFixed(3),
      ]),
      { rowHeight: 39, fontSize: 10 },
    );
    const watch = drift.find((row) => row.status === "Watch");
    metricCard(slide, 810, 155, 195, tr ? "Drift İzleme" : "Drift Watch", watch.feature.replaceAll("_", " "), `PSI ${Number(watch.psi).toFixed(3)}`, C.amber, 126);
    metricCard(slide, 1025, 155, 207, tr ? "Kalite Kapısı" : "Quality Gates", `${quality.filter((row) => row.status === "PASS").length}/${quality.length}`, tr ? "Tümü PASS" : "All PASS", C.teal, 126);
    insightBox(
      slide,
      810,
      306,
      422,
      166,
      tr ? "Adalet kontrolü" : "Fairness control",
      tr
        ? "Bölge ve yaş bandı bazında müşteri sayısı, gözlenen churn, ortalama risk, ROC-AUC ve true-positive-rate izlenir."
        : "Customer count, observed churn, average risk, ROC-AUC and true-positive rate are monitored by region and age band.",
      C.blue,
      C.paleBlue,
    );
    insightBox(
      slide,
      810,
      493,
      422,
      145,
      tr ? "Üretim kuralı" : "Production rule",
      tr
        ? "Aylık performans ve veri kalitesi; üç aylık drift/adalet incelemesi; eşik aşımında yeniden eğitim veya model geri çekme."
        : "Monthly performance and data quality; quarterly drift/fairness review; retrain or withdraw when thresholds are exceeded.",
      C.red,
      C.paleRed,
    );
    addFooter(slide, copy);
    addNotes(slide, projectSources("Data/Processed/fairness_audit.csv", "Data/Processed/drift_monitoring.csv", "Data/Processed/data_quality_report.csv"));
  }

  // 16 — Campaign targeting.
  {
    const slide = presentation.slides.add();
    addHeader(slide, copy, 16);
    addImage(slide, assets["campaign-targeting"], { left: 48, top: 145, width: 820, height: 500 }, "Campaign targeting and next-best-action dashboard");
    metricCard(slide, 894, 145, 338, tr ? "Önceliklendirilen" : "Prioritized", fmtNum(campaignSelected), tr ? "Müşteri aksiyonu" : "Customer actions", C.blue, 126);
    metricCard(slide, 894, 289, 338, tr ? "Tahsis Edilen Bütçe" : "Allocated Budget", fmtTry(KPI["Campaign Budget Allocated"], 0), tr ? "Model bütçe sınırı içinde" : "Within model budget cap", C.amber, 126);
    metricCard(slide, 894, 433, 338, tr ? "Beklenen Marj" : "Expected Margin", fmtTry(KPI["Expected Incremental Margin"], 0), tr ? "Artımlı kampanya katkısı" : "Incremental campaign contribution", C.teal, 126);
    insightBox(
      slide,
      894,
      577,
      338,
      68,
      tr ? "Kontrol" : "Control",
      tr ? "Pazarlama izni olmayan müşteriler bastırılır." : "Customers without marketing consent are suppressed.",
      C.red,
      C.paleRed,
    );
    addFooter(slide, copy);
    addNotes(slide, projectSources("Data/Processed/campaign_targets.csv", "Data/Processed/campaign_summary.csv", "Images/campaign-targeting.png"));
  }

  // 17 — Campaign economics: Codex Grid chart + insight cards.
  {
    const slide = presentation.slides.add();
    addHeader(slide, copy, 17);
    const categories = campaignPortfolio.map((row) =>
      label(row.recommended_action, lang, ACTION_TR),
    );
    addBarChart(
      slide,
      { left: 48, top: 160, width: 610, height: 455 },
      categories,
      [
        {
          name: tr ? "Bütçe (bin TRY)" : "Budget (TRY K)",
          values: campaignPortfolio.map((row) => Number(row.allocated_budget) / 1000),
          color: C.amber,
        },
        {
          name: tr ? "Beklenen Marj (bin TRY)" : "Expected Margin (TRY K)",
          values: campaignPortfolio.map((row) => Number(row.expected_incremental_margin) / 1000),
          color: C.teal,
        },
      ],
      { axisFormat: "0", valueFormat: "0", showValue: false },
    );
    const rules = tr
      ? [
          ["Yatırım", "ROI ≥ 1,0x ve pozitif artımlı marj", C.teal, C.paleTeal],
          ["Test", "ROI 0,25x–1,0x; kontrollü deney", C.amber, C.paleAmber],
          ["Beklet", "Negatif ekonomi veya zayıf uygunluk", C.red, C.paleRed],
        ]
      : [
          ["Invest", "ROI ≥ 1.0x and positive incremental margin", C.teal, C.paleTeal],
          ["Test", "ROI 0.25x–1.0x; controlled experiment", C.amber, C.paleAmber],
          ["Hold", "Negative economics or weak eligibility", C.red, C.paleRed],
        ];
    rules.forEach((item, index) => {
      insightBox(slide, 690, 160 + index * 142, 542, 124, item[0], item[1], item[2], item[3]);
    });
    insightBox(
      slide,
      690,
      590,
      542,
      55,
      tr ? "Portföy ilkesi" : "Portfolio principle",
      tr ? "Model seçer; bütçe sınırlar; deney doğrular." : "The model selects; the budget constrains; experimentation validates.",
      C.purple,
      C.palePurple,
    );
    addFooter(slide, copy);
    addNotes(slide, projectSources("Data/Processed/campaign_summary.csv", "Excel/Customer_Intelligence_CLV_Churn_Campaign_Planner.xlsx", "Python/src/customer_intelligence/campaign.py"));
  }

  // 18 — Multi-platform delivery.
  {
    const slide = presentation.slides.add();
    addHeader(slide, copy, 18);
    const stack = tr
      ? [
          ["Power BI", "12 sayfalık PBIP\nDAX + semantik model", C.blue, C.paleBlue],
          ["Excel", "24 sayfalık karar modeli\nSenaryo ve QA formülleri", C.green, C.paleTeal],
          ["Tableau", "3 dashboard\n8 analiz çalışma sayfası", C.cyan, C.paleCyan],
          ["Python & SQL", "Tekrarlanabilir pipeline\nSQLite analitik katmanı", C.purple, C.palePurple],
          ["API & App", "FastAPI skorlama\nStreamlit keşif uygulaması", C.amber, C.paleAmber],
          ["Yönetişim", "Test, model kartları\nDrift, adalet ve CI", C.red, C.paleRed],
        ]
      : [
          ["Power BI", "12-page PBIP\nDAX + semantic model", C.blue, C.paleBlue],
          ["Excel", "24-sheet decision model\nScenario and QA formulas", C.green, C.paleTeal],
          ["Tableau", "3 dashboards\n8 analytical worksheets", C.cyan, C.paleCyan],
          ["Python & SQL", "Reproducible pipeline\nSQLite analytical layer", C.purple, C.palePurple],
          ["API & App", "FastAPI scoring\nStreamlit exploration app", C.amber, C.paleAmber],
          ["Governance", "Tests and model cards\nDrift, fairness and CI", C.red, C.paleRed],
        ];
    stack.forEach((item, index) => {
      const x = 48 + (index % 3) * 397;
      const y = 150 + Math.floor(index / 3) * 214;
      addPanel(slide, { left: x, top: y, width: 365, height: 184 }, { fill: item[3], line: item[2] });
      addText(slide, item[0], { left: x + 22, top: y + 24, width: 320, height: 32 }, { fontSize: 22, bold: true, color: item[2] });
      addText(slide, item[1], { left: x + 22, top: y + 78, width: 320, height: 72 }, { fontSize: 15, color: C.ink });
    });
    insightBox(
      slide,
      48,
      594,
      1164,
      53,
      tr ? "Tek kaynak ilkesi" : "Single-source principle",
      tr
        ? "Tüm kanallar aynı iş tanımlarını, müşteri anahtarını ve doğrulanmış çıktı tablolarını kullanır."
        : "Every channel uses the same business definitions, customer key and validated output tables.",
      C.navy,
      C.white,
    );
    addFooter(slide, copy);
    addNotes(slide, projectSources("PowerBI/Customer_Intelligence_PBIP.zip", "Tableau/Customer_Intelligence_Dashboard.twb", "API/main.py", "App/streamlit_app.py"));
  }

  // 19 — Roadmap: Codex Grid timeline.
  {
    const slide = presentation.slides.add();
    addHeader(slide, copy, 19);
    slide.shapes.add({
      geometry: "straightConnector1",
      position: { left: 85, top: 335, width: 1100, height: 0 },
      fill: "none",
      line: { style: "solid", width: 3, fill: C.line },
    });
    const phases = tr
      ? [
          ["0–30 Gün", "Temel ve Pilot", "Kaynak eşleme\nKPI sözlüğü\nPilot cohort"],
          ["31–60 Gün", "Model ve Deney", "Zaman bazlı validasyon\nA/B tasarımı\nOnay kapısı"],
          ["61–90 Gün", "Operasyon", "BI yayını\nAPI entegrasyonu\nİzleme ritmi"],
        ]
      : [
          ["Days 0–30", "Foundation & Pilot", "Source mapping\nKPI dictionary\nPilot cohort"],
          ["Days 31–60", "Model & Experiment", "Time-based validation\nA/B design\nApproval gate"],
          ["Days 61–90", "Operate", "BI release\nAPI integration\nMonitoring cadence"],
        ];
    phases.forEach((item, index) => {
      const x = 85 + index * 400;
      slide.shapes.add({
        geometry: "ellipse",
        position: { left: x, top: 323, width: 24, height: 24 },
        fill: [C.blue, C.teal, C.purple][index],
        line: { style: "solid", fill: C.white, width: 3 },
      });
      addText(slide, item[0], { left: x, top: 270, width: 160, height: 24 }, { fontSize: 14, bold: true, color: [C.blue, C.teal, C.purple][index] });
      addPanel(slide, { left: x, top: 380, width: 330, height: 205 }, { fill: [C.paleBlue, C.paleTeal, C.palePurple][index], line: [C.blue, C.teal, C.purple][index] });
      addText(slide, item[1], { left: x + 20, top: 404, width: 290, height: 34 }, { fontSize: 20, bold: true, color: C.navy });
      addText(slide, item[2], { left: x + 20, top: 460, width: 290, height: 92 }, { fontSize: 15, color: C.ink });
    });
    insightBox(
      slide,
      48,
      145,
      1184,
      82,
      tr ? "Başarı ölçütü" : "Success criterion",
      tr
        ? "Pilot başarı; yalnızca model metriğiyle değil, artımlı marj, müşteri deneyimi, operasyon uyumu ve kontrol ihlali olmamasıyla değerlendirilir."
        : "Pilot success is judged by incremental margin, customer experience, operational adoption and absence of control breaches—not model metrics alone.",
      C.amber,
      C.paleAmber,
    );
    addFooter(slide, copy);
    addNotes(slide, projectSources("Docs/model_monitoring.md", "Docs/campaign_playbook.md", "Docs/privacy_ethics.md"));
  }

  // 20 — Close: Codex Grid slide-26 inspired.
  {
    const slide = presentation.slides.add();
    slide.background.fill = C.navy;
    addText(slide, copy.thankYou, { left: 56, top: 43, width: 300, height: 24 }, { fontSize: 12, bold: true, color: "#8FD8FF" });
    addText(slide, copy.closeTitle, { left: 56, top: 158, width: 850, height: 210 }, { fontSize: 48, bold: true, color: C.white });
    addText(slide, copy.closeBody, { left: 56, top: 402, width: 820, height: 105 }, { fontSize: 19, color: "#D8E6F6" });
    addText(slide, "Murat Miraç Gedik", { left: 56, top: 558, width: 370, height: 32 }, { fontSize: 18, bold: true, color: C.white });
    addText(slide, "Python • SQL • Power BI • Excel • Tableau • Scikit-learn • SHAP", { left: 56, top: 602, width: 720, height: 25 }, { fontSize: 13, color: "#8FD8FF" });
    addText(slide, copy.notice, { left: 56, top: 660, width: 820, height: 18 }, { fontSize: 10, color: "#B7C7D9" });
    slide.shapes.add({
      geometry: "ellipse",
      position: { left: 968, top: 182, width: 250, height: 250 },
      fill: C.blue,
      line: { style: "solid", fill: C.blue, width: 0 },
    });
    addText(slide, tr ? "DEĞER\n+\nRİSK\n→\nAKSİYON" : "VALUE\n+\nRISK\n→\nACTION", {
      left: 1010,
      top: 228,
      width: 166,
      height: 160,
    }, { fontSize: 23, bold: true, color: C.white, align: "center", vertical: "middle" });
    addNotes(slide, projectSources("README.md"));
  }

  return presentation;
}

async function writeBlob(filename, blob) {
  await fs.writeFile(filename, new Uint8Array(await blob.arrayBuffer()));
}

async function exportDeck(lang) {
  const presentation = createDeck(lang);
  const previewDir = path.join(outputDir, `previews-${lang}`);
  await fs.mkdir(previewDir, { recursive: true });
  for (const [index, slide] of presentation.slides.items.entries()) {
    const stem = `slide-${String(index + 1).padStart(2, "0")}`;
    const png = await presentation.export({ slide, format: "png", scale: 1.5 });
    await writeBlob(path.join(previewDir, `${stem}.png`), png);
    const layout = await slide.export({ format: "layout" });
    await fs.writeFile(path.join(previewDir, `${stem}.layout.json`), await layout.text(), "utf8");
  }
  const montage = await presentation.export({ format: "webp", montage: true, scale: 0.7 });
  await writeBlob(path.join(previewDir, "deck-montage.webp"), montage);
  const inspection = await presentation.inspect({
    kind: "slide,textbox,shape,chart,notes,layout",
    maxChars: 24000,
    options: { maxResults: 900 },
  });
  await fs.writeFile(path.join(previewDir, "deck-inspection.ndjson"), inspection.ndjson, "utf8");
  const pptx = await PresentationFile.exportPptx(presentation);
  const filename =
    lang === "tr"
      ? "Musteri_Zekasi_CLV_Churn_Tahmin_Platformu_Profesyonel_Sunum_TR.pptx"
      : "Customer_Intelligence_CLV_Churn_Prediction_Professional_Deck_EN.pptx";
  const outputPath = path.join(outputDir, filename);
  await pptx.save(outputPath);
  return outputPath;
}

await fs.mkdir(outputDir, { recursive: true });
const english = await exportDeck("en");
const turkish = await exportDeck("tr");
console.log(JSON.stringify({ english, turkish }, null, 2));
