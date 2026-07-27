import fs from "node:fs/promises";
import path from "node:path";
import process from "node:process";
import { SpreadsheetFile, Workbook } from "@oai/artifact-tool";

const projectRoot = path.resolve(process.argv[2] || ".");
const dataDir = path.join(projectRoot, "Data", "Processed");
const outputDir = path.join(projectRoot, "Excel");
const previewDir = path.join(projectRoot, "Images", "excel-previews");

const C = {
  navy: "#07111F",
  navy2: "#101C2D",
  panel: "#142238",
  blue: "#4CA6FF",
  teal: "#36D7B7",
  purple: "#A78BFA",
  amber: "#FFB547",
  red: "#FF647C",
  cyan: "#67E8F9",
  light: "#F4F7FB",
  white: "#FFFFFF",
  text: "#152238",
  muted: "#667085",
  line: "#D5DEEA",
  input: "#FFF2CC",
  inputFont: "#0000FF",
  linkFont: "#008000",
  paleGreen: "#E7F8F3",
  paleRed: "#FDEBED",
  paleAmber: "#FFF4D6",
};

// A plain accounting-style integer format renders consistently in both Excel
// and artifact-tool previews. Currency context is carried in titles/headers.
const FMT_TRY = "#,##0;[Red](#,##0);-";
const FMT_PCT = "0.0%;[Red](0.0%);-";
const FMT_NUM = "#,##0;[Red](#,##0);-";
const FMT_DEC = "0.000";

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
  const rows = parseCsv(await fs.readFile(path.join(dataDir, filename), "utf8"));
  return {
    headers: rows[0],
    rows: rows.slice(1).map((row) => row.map(coerce)),
  };
}

function colName(index) {
  let value = index + 1;
  let result = "";
  while (value > 0) {
    const remainder = (value - 1) % 26;
    result = String.fromCharCode(65 + remainder) + result;
    value = Math.floor((value - 1) / 26);
  }
  return result;
}

function rangeFor(startRow, startCol, rows, cols) {
  return `${colName(startCol)}${startRow}:${colName(startCol + cols - 1)}${startRow + rows - 1}`;
}

function fieldCol(dataset, header) {
  const index = dataset.headers.indexOf(header);
  if (index < 0) throw new Error(`Missing field ${header}`);
  return colName(index);
}

function sourceRange(sheetName, dataset, header) {
  const column = fieldCol(dataset, header);
  return `'${sheetName}'!$${column}$6:$${column}$${dataset.rows.length + 5}`;
}

function titleBand(sheet, title, subtitle, lastCol = "N") {
  sheet.showGridLines = false;
  sheet.getRange(`A1:${lastCol}2`).merge();
  sheet.getRange("A1").values = [[title]];
  sheet.getRange(`A1:${lastCol}2`).format = {
    fill: C.navy,
    font: { color: C.white, bold: true, size: 20 },
    verticalAlignment: "center",
  };
  sheet.getRange(`A3:${lastCol}3`).merge();
  sheet.getRange("A3").values = [[subtitle]];
  sheet.getRange(`A3:${lastCol}3`).format = {
    fill: C.navy2,
    font: { color: "#D8E6F7", italic: true, size: 10 },
    verticalAlignment: "center",
  };
}

function section(sheet, address, label) {
  sheet.getRange(address).merge();
  sheet.getRange(address.split(":")[0]).values = [[label]];
  sheet.getRange(address).format = {
    fill: C.navy2,
    font: { color: C.white, bold: true, size: 10 },
    verticalAlignment: "center",
  };
}

function styleTable(sheet, address, headerAddress, options = {}) {
  sheet.getRange(address).format = {
    font: { color: C.text, size: options.fontSize || 9 },
    borders: { preset: "all", style: "thin", color: C.line },
    verticalAlignment: "center",
  };
  sheet.getRange(headerAddress).format = {
    fill: C.navy2,
    font: { color: C.white, bold: true, size: options.headerSize || 9 },
    borders: { preset: "all", style: "thin", color: C.navy2 },
    wrapText: true,
    verticalAlignment: "center",
  };
}

function setWidths(sheet, widths) {
  for (const [address, width] of Object.entries(widths)) {
    sheet.getRange(address).format.columnWidth = width;
  }
}

function card(sheet, labelRange, valueRange, label, formula, numberFormat, accent) {
  sheet.getRange(labelRange).merge();
  sheet.getRange(valueRange).merge();
  sheet.getRange(labelRange.split(":")[0]).values = [[label]];
  sheet.getRange(valueRange.split(":")[0]).formulas = [[formula]];
  sheet.getRange(labelRange).format = {
    fill: C.light,
    font: { color: C.muted, bold: true, size: 9 },
    borders: { preset: "outside", style: "thin", color: C.line },
    verticalAlignment: "center",
  };
  sheet.getRange(valueRange).format = {
    fill: C.white,
    font: { color: accent, bold: true, size: 18 },
    borders: { preset: "outside", style: "thin", color: C.line },
    verticalAlignment: "center",
  };
  sheet.getRange(valueRange).format.numberFormat = numberFormat;
}

function addRawSheet(workbook, name, title, subtitle, dataset) {
  const sheet = workbook.worksheets.add(name);
  const lastCol = colName(dataset.headers.length - 1);
  titleBand(sheet, title, subtitle, lastCol);
  const address = rangeFor(5, 0, dataset.rows.length + 1, dataset.headers.length);
  sheet.getRange(address).values = [dataset.headers, ...dataset.rows];
  styleTable(sheet, address, rangeFor(5, 0, 1, dataset.headers.length), {
    fontSize: 8,
    headerSize: 8,
  });
  sheet.freezePanes.freezeRows(5);
  sheet.getRange(address).format.rowHeight = 17;
  return sheet;
}

const [
  customer,
  segments,
  cohortLong,
  cohortMatrix,
  monthly,
  campaignTargets,
  campaignSummary,
  churnModels,
  clvModels,
  shapGlobal,
  fairness,
  drift,
  quality,
  executiveKpis,
] = await Promise.all([
  loadCsv("customer_360.csv"),
  loadCsv("segment_summary.csv"),
  loadCsv("cohort_retention_long.csv"),
  loadCsv("cohort_retention_matrix.csv"),
  loadCsv("monthly_customer_metrics.csv"),
  loadCsv("campaign_targets.csv"),
  loadCsv("campaign_summary.csv"),
  loadCsv("churn_model_comparison.csv"),
  loadCsv("clv_model_comparison.csv"),
  loadCsv("shap_global_importance.csv"),
  loadCsv("fairness_audit.csv"),
  loadCsv("drift_monitoring.csv"),
  loadCsv("data_quality_report.csv"),
  loadCsv("executive_kpis.csv"),
]);

const workbook = Workbook.create();
const cover = workbook.worksheets.add("Cover");
const dashboard = workbook.worksheets.add("Executive Dashboard");
const assumptions = workbook.worksheets.add("Assumptions");
const rfmSheet = workbook.worksheets.add("RFM Segmentation");
const cohortSheet = workbook.worksheets.add("Cohort Retention");
const clvSheet = workbook.worksheets.add("CLV Analysis");
const churnSheet = workbook.worksheets.add("Churn Analysis");
const campaignPlanner = workbook.worksheets.add("Campaign Planner");
const modelPerformance = workbook.worksheets.add("Model Performance");
const shapSheet = workbook.worksheets.add("SHAP Drivers");
const governanceSheet = workbook.worksheets.add("Fairness and Drift");
const customer360 = workbook.worksheets.add("Customer 360");
const monthlyTrends = workbook.worksheets.add("Monthly Trends");
const checks = workbook.worksheets.add("QA Checks");
const dictionary = workbook.worksheets.add("Data Dictionary");
const sources = workbook.worksheets.add("Sources");

const customerData = addRawSheet(
  workbook,
  "Customer Data",
  "Customer 360 Data",
  "One row per customer | behavior, value, churn risk and recommended action",
  customer,
);
const segmentData = addRawSheet(
  workbook,
  "Segment Data",
  "RFM Segment Data",
  "Segment-level value, risk and campaign economics",
  segments,
);
const cohortData = addRawSheet(
  workbook,
  "Cohort Data",
  "Cohort Retention Data",
  "Long-form acquisition cohort retention curve",
  cohortLong,
);
const monthlyData = addRawSheet(
  workbook,
  "Monthly Data",
  "Monthly Customer Metrics",
  "Four-year revenue, customer and quality trend",
  monthly,
);
const campaignData = addRawSheet(
  workbook,
  "Campaign Data",
  "Campaign Portfolio Data",
  "Budget allocation and expected incremental-margin output",
  campaignSummary,
);
const modelData = addRawSheet(
  workbook,
  "Model Data",
  "Model Comparison Data",
  "Churn and CLV time-based holdout performance",
  {
    headers: [
      "model_family",
      "model",
      "roc_auc",
      "pr_auc",
      "brier_score",
      "f1",
      "precision",
      "recall",
      "lift_at_10pct",
      "threshold",
      "mae",
      "rmse",
      "r2",
      "spearman_correlation",
      "selection_score",
    ],
    rows: [
      ...churnModels.rows.map((row) => [
        "Churn",
        row[churnModels.headers.indexOf("model")],
        row[churnModels.headers.indexOf("roc_auc")],
        row[churnModels.headers.indexOf("pr_auc")],
        row[churnModels.headers.indexOf("brier_score")],
        row[churnModels.headers.indexOf("f1")],
        row[churnModels.headers.indexOf("precision")],
        row[churnModels.headers.indexOf("recall")],
        row[churnModels.headers.indexOf("lift_at_10pct")],
        row[churnModels.headers.indexOf("threshold")],
        null,
        null,
        null,
        null,
        row[churnModels.headers.indexOf("selection_score")],
      ]),
      ...clvModels.rows.map((row) => [
        "CLV",
        row[clvModels.headers.indexOf("model")],
        null,
        null,
        null,
        null,
        null,
        null,
        null,
        null,
        row[clvModels.headers.indexOf("mae")],
        row[clvModels.headers.indexOf("rmse")],
        row[clvModels.headers.indexOf("r2")],
        row[clvModels.headers.indexOf("spearman_correlation")],
        row[clvModels.headers.indexOf("selection_score")],
      ]),
    ],
  },
);
const shapData = addRawSheet(
  workbook,
  "SHAP Data",
  "SHAP Global Importance",
  "Global mean absolute contribution and importance share",
  shapGlobal,
);
const governanceData = addRawSheet(
  workbook,
  "Governance Data",
  "Fairness and Drift Data",
  "Group diagnostics and Population Stability Index",
  {
    headers: ["record_type", ...new Set([...fairness.headers, ...drift.headers])],
    rows: [
      ...fairness.rows.map((row) => [
        "Fairness",
        ...Array.from(
          new Set([...fairness.headers, ...drift.headers]),
          (header) => row[fairness.headers.indexOf(header)] ?? null,
        ),
      ]),
      ...drift.rows.map((row) => [
        "Drift",
        ...Array.from(
          new Set([...fairness.headers, ...drift.headers]),
          (header) => row[drift.headers.indexOf(header)] ?? null,
        ),
      ]),
    ],
  },
);

// Cover
cover.showGridLines = false;
cover.getRange("A1:N4").merge();
cover.getRange("A1").values = [[
  "Customer Intelligence, CLV\n& Churn Prediction Platform",
]];
cover.getRange("A1:N4").format = {
  fill: C.navy,
  font: { color: C.white, bold: true, size: 27 },
  wrapText: true,
  verticalAlignment: "center",
};
cover.getRange("A5:N5").merge();
cover.getRange("A5").values = [[
  "Professional Excel Customer Analytics & Campaign Planning Model",
]];
cover.getRange("A5:N5").format = {
  fill: C.teal,
  font: { color: C.navy, bold: true, size: 12 },
  verticalAlignment: "center",
};
cover.getRange("A7:H13").merge();
cover.getRange("A7").values = [[
  "Purpose\nTransform customer transactions, digital engagement and campaign history into RFM segments, cohort retention, predictive CLV, calibrated churn risk, SHAP explanations and economically prioritized next-best actions.",
]];
cover.getRange("A7:H13").format = {
  fill: C.light,
  font: { color: C.text, size: 13 },
  wrapText: true,
  verticalAlignment: "center",
  borders: { preset: "outside", style: "thin", color: C.line },
};
cover.getRange("J7:N13").merge();
cover.getRange("J7").values = [[
  "Portfolio Scope\n• 6,000 synthetic customers\n• 50,639 orders\n• Four-year history\n• 10 RFM segments\n• 90-day churn horizon\n• 12-month predictive CLV\n• SHAP explainability\n• Campaign budget optimization\n• No real PII",
]];
cover.getRange("J7:N13").format = {
  fill: "#E8F7F3",
  font: { color: C.navy, size: 11, bold: true },
  wrapText: true,
  verticalAlignment: "center",
  borders: { preset: "outside", style: "thin", color: C.teal },
};
cover.getRange("A15:N18").merge();
cover.getRange("A15").values = [[
  "Prepared by Murat Miraç Gedik  |  NovaRetail Group synthetic portfolio  |  Production snapshot: 31 December 2025\nYellow cells with blue font are editable assumptions. Green font indicates links to source worksheets. Black font indicates formulas.",
]];
cover.getRange("A15:N18").format = {
  fill: C.white,
  font: { color: C.muted, italic: true, size: 10 },
  wrapText: true,
  verticalAlignment: "center",
};
setWidths(cover, { "A:N": 12 });

// Assumptions
titleBand(
  assumptions,
  "Campaign Assumptions & Decision Guardrails",
  "Editable inputs are highlighted in yellow with blue font",
  "J",
);
assumptions.getRange("A5:D12").values = [
  ["Input", "Value", "Owner", "Business Rule"],
  ["Campaign Budget", 400000, "Marketing", "Maximum portfolio contact spend"],
  ["Response Multiplier", 1.0, "Growth", "Scenario scaling of expected response"],
  ["High Risk Threshold", 0.55, "Analytics", "High/Critical risk decision boundary"],
  ["Strategic CLV Threshold", 3500, "CRM", "Minimum predicted CLV for strategic tier"],
  ["Win-Back Cost Multiplier", 1.0, "Marketing", "Sensitivity on high-risk treatment cost"],
  ["Discount Rate", 0.10, "Finance", "Annual CLV discount rate"],
  ["Review Frequency", "Monthly", "Analytics", "Model and campaign governance cadence"],
];
styleTable(assumptions, "A5:D12", "A5:D5");
assumptions.getRange("B6:B11").format = {
  fill: C.input,
  font: { color: C.inputFont, bold: true },
};
assumptions.getRange("B6").format.numberFormat = FMT_TRY;
assumptions.getRange("B7:B8").format.numberFormat = FMT_PCT;
assumptions.getRange("B9").format.numberFormat = FMT_TRY;
assumptions.getRange("B10").format.numberFormat = FMT_PCT;
assumptions.getRange("F5:J12").values = [
  ["Color", "Meaning", "Model Horizon", "Value", "Validation"],
  ["Blue font", "Editable input", "Churn", "90 days", "Time-based holdout"],
  ["Green font", "Linked value", "CLV", "12 months", "2025 actual margin"],
  ["Black font", "Formula", "RFM", "12 months", "Snapshot scoring"],
  ["Red fill", "Failed check", "Cohort", "Monthly", "First-purchase cohort"],
  ["Green fill", "Passed check", "SHAP", "Local/global", "Additivity checked"],
  ["Amber fill", "Review needed", "Drift", "Monthly", "PSI thresholds"],
  ["Gray text", "Documentation", "Campaign", "Budget", "Expected margin"],
];
styleTable(assumptions, "F5:J12", "F5:J5", { fontSize: 8 });
setWidths(assumptions, {
  "A:A": 30,
  "B:B": 18,
  "C:C": 18,
  "D:D": 42,
  "F:G": 20,
  "H:J": 18,
});

// Executive Dashboard
titleBand(
  dashboard,
  "Executive Customer Intelligence Dashboard",
  "Value, risk, retention and campaign economics | production snapshot 31 Dec 2025",
  "N",
);
const customerCountRange = sourceRange("Customer Data", customer, "customer_id");
const frequencyRange = sourceRange("Customer Data", customer, "frequency_12m");
const revenueRange = sourceRange("Customer Data", customer, "monetary_12m");
const clvRange = sourceRange("Customer Data", customer, "predicted_clv_12m");
const churnRange = sourceRange("Customer Data", customer, "churn_probability");
const expectedMarginRange = sourceRange(
  "Customer Data",
  customer,
  "expected_incremental_margin",
);
card(
  dashboard,
  "A5:C5",
  "A6:C8",
  "CUSTOMERS",
  `=COUNTA(${customerCountRange})`,
  FMT_NUM,
  C.blue,
);
card(
  dashboard,
  "D5:F5",
  "D6:F8",
  "ACTIVE CUSTOMERS 12M",
  `=COUNTIF(${frequencyRange},">0")`,
  FMT_NUM,
  C.teal,
);
card(
  dashboard,
  "G5:I5",
  "G6:I8",
  "NET REVENUE 12M (TRY)",
  `=SUM(${revenueRange})`,
  FMT_TRY,
  C.blue,
);
card(
  dashboard,
  "J5:L5",
  "J6:L8",
  "PREDICTED CLV 12M (TRY)",
  `=SUM(${clvRange})`,
  FMT_TRY,
  C.purple,
);
card(
  dashboard,
  "M5:N5",
  "M6:N8",
  "AVG CHURN RISK",
  `=AVERAGE(${churnRange})`,
  FMT_PCT,
  C.red,
);
card(
  dashboard,
  "A10:C10",
  "A11:C13",
  "HIGH / CRITICAL RISK",
  `=COUNTIF(${sourceRange("Customer Data", customer, "risk_band")},"High")+COUNTIF(${sourceRange("Customer Data", customer, "risk_band")},"Critical")`,
  FMT_NUM,
  C.red,
);
card(
  dashboard,
  "D10:F10",
  "D11:F13",
  "EXPECTED CAMPAIGN MARGIN (TRY)",
  `=SUM(${expectedMarginRange})`,
  FMT_TRY,
  C.amber,
);
card(
  dashboard,
  "G10:I10",
  "G11:I13",
  "CHURN ROC-AUC",
  `='Model Data'!C6`,
  FMT_DEC,
  C.teal,
);
card(
  dashboard,
  "J10:L10",
  "J11:L13",
  "TOP 10% LIFT",
  `='Model Data'!I6`,
  '0.00"x"',
  C.amber,
);
card(
  dashboard,
  "M10:N10",
  "M11:N13",
  "M3 RETENTION",
  `=AVERAGEIFS(${sourceRange("Cohort Data", cohortLong, "retention_rate")},${sourceRange("Cohort Data", cohortLong, "cohort_index")},3)`,
  FMT_PCT,
  C.teal,
);
section(dashboard, "A15:H15", "Four-Year Monthly Revenue Trend");
dashboard.getRange("A16:B64").values = [
  ["Month", "Net Revenue"],
  ...monthly.rows.map((row) => [
    row[monthly.headers.indexOf("month")],
    row[monthly.headers.indexOf("net_revenue")],
  ]),
];
styleTable(dashboard, "A16:B64", "A16:B16", { fontSize: 8 });
dashboard.getRange("B17:B64").format.numberFormat = FMT_TRY;
const revenueChart = dashboard.charts.add("line", dashboard.getRange("A16:B64"));
revenueChart.title = "Monthly Net Revenue";
revenueChart.hasLegend = false;
revenueChart.setPosition("D16", "N32");
section(dashboard, "D34:N34", "Segment Predicted CLV");
const segmentHelperStart = 66;
const segmentHelperEnd = segmentHelperStart + segments.rows.length;
dashboard.getRange(`A${segmentHelperStart}:B${segmentHelperEnd}`).values = [
  ["RFM Segment", "Predicted CLV"],
  ...segments.rows.map((row) => [
    row[segments.headers.indexOf("rfm_segment")],
    row[segments.headers.indexOf("predicted_clv_12m")],
  ]),
];
styleTable(
  dashboard,
  `A${segmentHelperStart}:B${segmentHelperEnd}`,
  `A${segmentHelperStart}:B${segmentHelperStart}`,
  { fontSize: 8 },
);
dashboard
  .getRange(`B${segmentHelperStart + 1}:B${segmentHelperEnd}`)
  .format.numberFormat = FMT_TRY;
const segmentChart = dashboard.charts.add(
  "bar",
  dashboard.getRange(`A${segmentHelperStart}:B${segmentHelperEnd}`),
);
segmentChart.title = "Predicted CLV by RFM Segment";
segmentChart.hasLegend = false;
segmentChart.setPosition("D35", "N53");
setWidths(dashboard, { "A:N": 13 });

// RFM Segmentation
titleBand(
  rfmSheet,
  "RFM Segmentation",
  "Behavioral segmentation by recency, frequency and monetary value",
  "L",
);
const rfmEnd = 5 + segments.rows.length;
rfmSheet.getRange(`A5:J${rfmEnd}`).values = [
  [
    "RFM Segment",
    "Customers",
    "Customer Share",
    "Revenue 12M",
    "Revenue Share",
    "Gross Margin 12M",
    "Predicted CLV 12M",
    "Average Churn Risk",
    "Campaign Selected",
    "Expected Margin",
  ],
  ...segments.rows.map((row) => [
    row[segments.headers.indexOf("rfm_segment")],
    row[segments.headers.indexOf("customers")],
    row[segments.headers.indexOf("customer_share")],
    row[segments.headers.indexOf("revenue_12m")],
    row[segments.headers.indexOf("revenue_share")],
    row[segments.headers.indexOf("gross_margin_12m")],
    row[segments.headers.indexOf("predicted_clv_12m")],
    row[segments.headers.indexOf("average_churn_probability")],
    row[segments.headers.indexOf("campaign_selected")],
    row[segments.headers.indexOf("expected_incremental_margin")],
  ]),
];
styleTable(rfmSheet, `A5:J${rfmEnd}`, "A5:J5");
rfmSheet.getRange(`C6:C${rfmEnd}`).format.numberFormat = FMT_PCT;
rfmSheet.getRange(`D6:D${rfmEnd}`).format.numberFormat = FMT_TRY;
rfmSheet.getRange(`E6:E${rfmEnd}`).format.numberFormat = FMT_PCT;
rfmSheet.getRange(`F6:G${rfmEnd}`).format.numberFormat = FMT_TRY;
rfmSheet.getRange(`H6:H${rfmEnd}`).format.numberFormat = FMT_PCT;
rfmSheet.getRange(`J6:J${rfmEnd}`).format.numberFormat = FMT_TRY;
rfmSheet.getRange(`H6:H${rfmEnd}`).conditionalFormats.add("colorScale", {
  criteria: [
    { type: "lowestValue", color: C.paleGreen },
    { type: "percentile", value: 50, color: C.paleAmber },
    { type: "highestValue", color: C.paleRed },
  ],
});
const rfmChart = rfmSheet.charts.add("bar", rfmSheet.getRange(`A5:B${rfmEnd}`));
rfmChart.title = "Customers by RFM Segment";
rfmChart.hasLegend = false;
rfmChart.setPosition("A18", "F36");
rfmSheet.getRange(`K5:L${rfmEnd}`).values = [
  ["RFM Segment", "Predicted CLV"],
  ...segments.rows.map((row) => [
    row[segments.headers.indexOf("rfm_segment")],
    row[segments.headers.indexOf("predicted_clv_12m")],
  ]),
];
styleTable(rfmSheet, `K5:L${rfmEnd}`, "K5:L5", { fontSize: 8 });
rfmSheet.getRange(`L6:L${rfmEnd}`).format.numberFormat = FMT_TRY;
const rfmValueChart = rfmSheet.charts.add(
  "bar",
  rfmSheet.getRange(`K5:L${rfmEnd}`),
);
rfmValueChart.title = "RFM Portfolio";
rfmValueChart.setPosition("G18", "L36");
setWidths(rfmSheet, { "A:A": 28, "B:J": 18, "K:K": 28, "L:L": 18 });

// Cohort Retention
titleBand(
  cohortSheet,
  "Cohort Retention Matrix",
  "First-purchase cohort month vs months since acquisition",
  "N",
);
const cohortHeaders = cohortMatrix.headers.slice(0, 14);
const cohortRows = cohortMatrix.rows.slice(-24).map((row) => row.slice(0, 14));
cohortSheet.getRange("A5:N29").values = [cohortHeaders, ...cohortRows];
styleTable(cohortSheet, "A5:N29", "A5:N5", { fontSize: 8 });
cohortSheet.getRange("B6:N29").format.numberFormat = FMT_PCT;
cohortSheet.getRange("B6:N29").conditionalFormats.add("colorScale", {
  criteria: [
    { type: "lowestValue", color: "#EAF1F8" },
    { type: "percentile", value: 50, color: "#8FC8F8" },
    { type: "highestValue", color: C.teal },
  ],
});
cohortSheet.freezePanes.freezeRows(5);
cohortSheet.freezePanes.freezeColumns(1);
setWidths(cohortSheet, { "A:A": 16, "B:N": 10 });

// CLV Analysis
titleBand(
  clvSheet,
  "Predictive Customer Lifetime Value",
  "Twelve-month gross-margin contribution with time-based validation",
  "L",
);
const clvModelEnd = 5 + clvModels.rows.length;
clvSheet.getRange(`A5:F${clvModelEnd}`).values = [
  ["Model", "MAE", "RMSE", "R²", "Spearman", "Selection Score"],
  ...clvModels.rows.map((row) => [
    row[clvModels.headers.indexOf("model")],
    row[clvModels.headers.indexOf("mae")],
    row[clvModels.headers.indexOf("rmse")],
    row[clvModels.headers.indexOf("r2")],
    row[clvModels.headers.indexOf("spearman_correlation")],
    row[clvModels.headers.indexOf("selection_score")],
  ]),
];
styleTable(clvSheet, `A5:F${clvModelEnd}`, "A5:F5");
clvSheet.getRange(`B6:C${clvModelEnd}`).format.numberFormat = FMT_TRY;
clvSheet.getRange(`D6:F${clvModelEnd}`).format.numberFormat = FMT_DEC;
const clvBandIndex = customer.headers.indexOf("clv_band");
const clvBands = ["Low", "Developing", "High", "Strategic"];
clvSheet.getRange("A12:C16").values = [
  ["CLV Band", "Customers", "Predicted CLV"],
  ...clvBands.map((band) => {
    const rows = customer.rows.filter((row) => row[clvBandIndex] === band);
    return [
      band,
      rows.length,
      rows.reduce(
        (sum, row) => sum + Number(row[customer.headers.indexOf("predicted_clv_12m")] || 0),
        0,
      ),
    ];
  }),
];
styleTable(clvSheet, "A12:C16", "A12:C12");
clvSheet.getRange("C13:C16").format.numberFormat = FMT_TRY;
const clvChart = clvSheet.charts.add("column", clvSheet.getRange("A12:C16"));
clvChart.title = "CLV Portfolio by Value Band";
clvChart.setPosition("E11", "L28");
section(clvSheet, "A20:D20", "Model Governance Notes");
clvSheet.getRange("A21:D27").values = [
  ["Control", "Implementation", "Status", "Owner"],
  ["Prediction target", "Future 365-day gross margin", "ACTIVE", "Analytics"],
  ["Holdout", "31 Dec 2024 snapshot → FY2025 actual", "PASS", "Analytics"],
  ["Champion", "Random Forest Regressor", "APPROVED", "Model Owner"],
  ["Non-negative output", "Predictions clipped at zero", "PASS", "Analytics"],
  ["Monitoring", "MAE, R² and rank correlation", "MONTHLY", "CRM Analytics"],
  ["Decision use", "Prioritization, not credit eligibility", "CONTROLLED", "CRM"],
];
styleTable(clvSheet, "A21:D27", "A21:D21", { fontSize: 8 });
setWidths(clvSheet, { "A:A": 36, "B:D": 20, "E:L": 13 });

// Churn Analysis
titleBand(
  churnSheet,
  "Churn Prediction & Risk Tiers",
  "Calibrated 90-day churn probability and top-decile lift",
  "L",
);
const churnModelEnd = 5 + churnModels.rows.length;
churnSheet.getRange(`A5:I${churnModelEnd}`).values = [
  [
    "Model",
    "ROC-AUC",
    "PR-AUC",
    "Brier",
    "F1",
    "Precision",
    "Recall",
    "Lift @10%",
    "Threshold",
  ],
  ...churnModels.rows.map((row) => [
    row[churnModels.headers.indexOf("model")],
    row[churnModels.headers.indexOf("roc_auc")],
    row[churnModels.headers.indexOf("pr_auc")],
    row[churnModels.headers.indexOf("brier_score")],
    row[churnModels.headers.indexOf("f1")],
    row[churnModels.headers.indexOf("precision")],
    row[churnModels.headers.indexOf("recall")],
    row[churnModels.headers.indexOf("lift_at_10pct")],
    row[churnModels.headers.indexOf("threshold")],
  ]),
];
styleTable(churnSheet, `A5:I${churnModelEnd}`, "A5:I5", { fontSize: 8 });
churnSheet.getRange(`B6:I${churnModelEnd}`).format.numberFormat = FMT_DEC;
const riskIndex = customer.headers.indexOf("risk_band");
const riskBands = ["Low", "Medium", "High", "Critical"];
churnSheet.getRange("A13:C17").values = [
  ["Risk Band", "Customers", "Revenue at Risk"],
  ...riskBands.map((band) => {
    const rows = customer.rows.filter((row) => row[riskIndex] === band);
    return [
      band,
      rows.length,
      rows.reduce(
        (sum, row) => sum + Number(row[customer.headers.indexOf("monetary_12m")] || 0),
        0,
      ),
    ];
  }),
];
styleTable(churnSheet, "A13:C17", "A13:C13");
churnSheet.getRange("C14:C17").format.numberFormat = FMT_TRY;
const riskChart = churnSheet.charts.add("column", churnSheet.getRange("A13:B17"));
riskChart.title = "Customer Risk Mix";
riskChart.hasLegend = false;
riskChart.setPosition("E12", "L29");
setWidths(churnSheet, { "A:A": 40, "B:I": 14, "J:L": 4 });

// Campaign Planner
titleBand(
  campaignPlanner,
  "Campaign Targeting & Budget Planner",
  "Formula-backed scenario planning linked to editable assumptions",
  "L",
);
section(campaignPlanner, "A5:D5", "Scenario Inputs");
campaignPlanner.getRange("A6:B8").values = [
  ["Campaign Budget", null],
  ["Response Multiplier", null],
  ["Win-Back Cost Multiplier", null],
];
campaignPlanner.getRange("B6").formulas = [["=Assumptions!B6"]];
campaignPlanner.getRange("B7").formulas = [["=Assumptions!B7"]];
campaignPlanner.getRange("B8").formulas = [["=Assumptions!B10"]];
styleTable(campaignPlanner, "A6:B8", "A6:B6");
campaignPlanner.getRange("B6:B8").format = {
  fill: "#E8F7F1",
  font: { color: C.linkFont, bold: true },
};
campaignPlanner.getRange("B6").format.numberFormat = FMT_TRY;
campaignPlanner.getRange("B7:B8").format.numberFormat = FMT_PCT;
const campaignPortfolioRows = campaignSummary.rows.filter(
  (row) => row[campaignSummary.headers.indexOf("recommended_action")] !== "Suppress",
);
const campaignPlannerEnd = 11 + campaignPortfolioRows.length;
campaignPlanner.getRange(`A11:I${campaignPlannerEnd}`).values = [
  [
    "Recommended Action",
    "Eligible",
    "Model Selected",
    "Model Budget",
    "Expected Margin",
    "Scenario Budget",
    "Scenario Margin",
    "Scenario ROI",
    "Decision",
  ],
  ...campaignPortfolioRows.map((row) => [
      row[campaignSummary.headers.indexOf("recommended_action")],
      row[campaignSummary.headers.indexOf("eligible_customers")],
      row[campaignSummary.headers.indexOf("selected_customers")],
      row[campaignSummary.headers.indexOf("allocated_budget")],
      row[campaignSummary.headers.indexOf("expected_incremental_margin")],
      null,
      null,
      null,
      null,
    ]),
];
styleTable(campaignPlanner, `A11:I${campaignPlannerEnd}`, "A11:I11", { fontSize: 8 });
for (let row = 12; row <= campaignPlannerEnd; row += 1) {
  campaignPlanner.getRange(`F${row}`).formulas = [[
    `=MIN(D${row},$B$6*D${row}/SUM($D$12:$D$${campaignPlannerEnd}))`,
  ]];
  campaignPlanner.getRange(`G${row}`).formulas = [[
    `=MAX(0,E${row}*$B$7-(F${row}-D${row}))`,
  ]];
  campaignPlanner.getRange(`H${row}`).formulas = [[
    `=IFERROR(G${row}/F${row},0)`,
  ]];
  campaignPlanner.getRange(`I${row}`).formulas = [[
    `=IF(H${row}>=1,"INVEST",IF(H${row}>=0.25,"TEST","HOLD"))`,
  ]];
}
campaignPlanner.getRange(`D12:G${campaignPlannerEnd}`).format.numberFormat = FMT_TRY;
campaignPlanner.getRange(`H12:H${campaignPlannerEnd}`).format.numberFormat = '0.00"x"';
campaignPlanner.getRange(`F12:I${campaignPlannerEnd}`).format.font = { color: C.linkFont };
campaignPlanner.getRange(`I12:I${campaignPlannerEnd}`).conditionalFormats.add("containsText", {
  text: "INVEST",
  format: { fill: C.paleGreen, font: { color: "#0F7C62", bold: true } },
});
campaignPlanner.getRange(`I12:I${campaignPlannerEnd}`).conditionalFormats.add("containsText", {
  text: "HOLD",
  format: { fill: C.paleRed, font: { color: C.red, bold: true } },
});
const campaignChart = campaignPlanner.charts.add(
  "column",
  campaignPlanner.getRange(`A11:G${campaignPlannerEnd}`),
);
campaignChart.title = "Model vs Scenario Campaign Economics";
campaignChart.setPosition("A21", "L40");
setWidths(campaignPlanner, { "A:A": 28, "B:I": 17, "J:L": 5 });

// Model Performance
titleBand(
  modelPerformance,
  "Model Performance & Validation",
  "Time-based holdout results for churn classification and CLV regression",
  "L",
);
modelPerformance.getRange(`A5:D${churnModelEnd}`).values = [
  ["Churn Model", "ROC-AUC", "PR-AUC", "Brier Score"],
  ...churnModels.rows.map((row) => [
    row[churnModels.headers.indexOf("model")],
    row[churnModels.headers.indexOf("roc_auc")],
    row[churnModels.headers.indexOf("pr_auc")],
    row[churnModels.headers.indexOf("brier_score")],
  ]),
];
styleTable(modelPerformance, `A5:D${churnModelEnd}`, "A5:D5");
modelPerformance.getRange(`B6:D${churnModelEnd}`).format.numberFormat = FMT_DEC;
modelPerformance.getRange(`F5:J${clvModelEnd}`).values = [
  ["CLV Model", "MAE", "RMSE", "R²", "Spearman"],
  ...clvModels.rows.map((row) => [
    row[clvModels.headers.indexOf("model")],
    row[clvModels.headers.indexOf("mae")],
    row[clvModels.headers.indexOf("rmse")],
    row[clvModels.headers.indexOf("r2")],
    row[clvModels.headers.indexOf("spearman_correlation")],
  ]),
];
styleTable(modelPerformance, `F5:J${clvModelEnd}`, "F5:J5");
modelPerformance.getRange(`G6:H${clvModelEnd}`).format.numberFormat = FMT_TRY;
modelPerformance.getRange(`I6:J${clvModelEnd}`).format.numberFormat = FMT_DEC;
const churnChart = modelPerformance.charts.add(
  "column",
  modelPerformance.getRange(`A5:C${churnModelEnd}`),
);
churnChart.title = "Churn Model ROC-AUC and PR-AUC";
churnChart.setPosition("A13", "F30");
const clvPerfChart = modelPerformance.charts.add(
  "bar",
  modelPerformance.getRange(`F5:I${clvModelEnd}`),
);
clvPerfChart.title = "CLV Model Performance";
clvPerfChart.setPosition("G13", "L30");
setWidths(modelPerformance, { "A:A": 42, "B:D": 15, "E:E": 4, "F:F": 42, "G:J": 15, "K:L": 4 });

// SHAP Drivers
titleBand(
  shapSheet,
  "SHAP Churn Drivers",
  "Global mean absolute contribution and direction of influence",
  "K",
);
shapSheet.getRange("A5:D21").values = [
  ["Feature", "Mean |SHAP|", "Mean SHAP", "Importance Share"],
  ...shapGlobal.rows.map((row) => [
    row[shapGlobal.headers.indexOf("feature")],
    row[shapGlobal.headers.indexOf("mean_abs_shap")],
    row[shapGlobal.headers.indexOf("mean_shap")],
    row[shapGlobal.headers.indexOf("importance_share")],
  ]),
];
styleTable(shapSheet, "A5:D21", "A5:D5");
shapSheet.getRange("B6:C21").format.numberFormat = FMT_DEC;
shapSheet.getRange("D6:D21").format.numberFormat = FMT_PCT;
const shapChart = shapSheet.charts.add("bar", shapSheet.getRange("A5:B17"));
shapChart.title = "Top Global Churn Drivers";
shapChart.hasLegend = false;
shapChart.setPosition("F5", "K24");
shapSheet.getRange("A24:K29").merge();
shapSheet.getRange("A24").values = [[
  "Interpretation: Positive SHAP values increase churn probability; negative values reduce it. Protected attributes are excluded from the feature set. Explanations are reviewed before customer treatment and are not used for credit, employment or eligibility decisions.",
]];
shapSheet.getRange("A24:K29").format = {
  fill: C.light,
  font: { color: C.text, size: 10 },
  borders: { preset: "outside", style: "thin", color: C.line },
  wrapText: true,
  verticalAlignment: "center",
};
setWidths(shapSheet, { "A:A": 34, "B:D": 18, "E:E": 4, "F:K": 13 });

// Fairness & Drift
titleBand(
  governanceSheet,
  "Fairness, Stability & Model Governance",
  "Group diagnostics and population stability monitoring",
  "L",
);
governanceSheet.getRange("A5:G17").values = [
  [
    "Attribute",
    "Group",
    "Customers",
    "Observed Churn",
    "Average Risk",
    "ROC-AUC",
    "True Positive Rate",
  ],
  ...fairness.rows.slice(0, 12).map((row) => [
    row[fairness.headers.indexOf("audit_attribute")],
    row[fairness.headers.indexOf("audit_group")],
    row[fairness.headers.indexOf("customers")],
    row[fairness.headers.indexOf("observed_churn_rate")],
    row[fairness.headers.indexOf("average_predicted_risk")],
    row[fairness.headers.indexOf("roc_auc")],
    row[fairness.headers.indexOf("true_positive_rate")],
  ]),
];
styleTable(governanceSheet, "A5:G17", "A5:G5", { fontSize: 8 });
governanceSheet.getRange("D6:G17").format.numberFormat = FMT_PCT;
governanceSheet.getRange("I5:L17").values = [
  ["Feature", "PSI", "Status", "Production Mean"],
  ...drift.rows.slice(0, 12).map((row) => [
    row[drift.headers.indexOf("feature")],
    row[drift.headers.indexOf("psi")],
    row[drift.headers.indexOf("status")],
    row[drift.headers.indexOf("production_mean")],
  ]),
];
styleTable(governanceSheet, "I5:L17", "I5:L5", { fontSize: 8 });
governanceSheet.getRange("J6:J17").format.numberFormat = FMT_DEC;
governanceSheet.getRange("K6:K17").conditionalFormats.add("containsText", {
  text: "Stable",
  format: { fill: C.paleGreen, font: { color: "#0F7C62", bold: true } },
});
governanceSheet.getRange("K6:K17").conditionalFormats.add("containsText", {
  text: "Watch",
  format: { fill: C.paleAmber, font: { color: "#9A6500", bold: true } },
});
governanceSheet.getRange("K6:K17").conditionalFormats.add("containsText", {
  text: "Investigate",
  format: { fill: C.paleRed, font: { color: C.red, bold: true } },
});
const driftChart = governanceSheet.charts.add(
  "bar",
  governanceSheet.getRange("I5:J17"),
);
driftChart.title = "Population Stability Index";
driftChart.hasLegend = false;
driftChart.setPosition("A20", "L38");
setWidths(governanceSheet, { "A:B": 22, "C:G": 16, "H:H": 4, "I:I": 30, "J:L": 17 });

// Customer 360
titleBand(
  customer360,
  "Customer 360 Priority View",
  "Top customer records by expected incremental campaign margin",
  "T",
);
const priorityRows = [...customer.rows]
  .sort(
    (left, right) =>
      Number(right[customer.headers.indexOf("expected_incremental_margin")] || 0) -
      Number(left[customer.headers.indexOf("expected_incremental_margin")] || 0),
  )
  .slice(0, 250);
const selectedHeaders = [
  "customer_id",
  "region",
  "loyalty_tier",
  "recency_days",
  "frequency_12m",
  "monetary_12m",
  "rfm_segment",
  "predicted_clv_12m",
  "clv_band",
  "churn_probability",
  "risk_band",
  "recommended_action",
  "campaign_priority",
  "expected_incremental_margin",
  "selected_for_campaign",
];
customer360.getRange("A5:O255").values = [
  selectedHeaders,
  ...priorityRows.map((row) =>
    selectedHeaders.map((header) => row[customer.headers.indexOf(header)]),
  ),
];
styleTable(customer360, "A5:O255", "A5:O5", { fontSize: 8, headerSize: 8 });
customer360.getRange("F6:F255").format.numberFormat = FMT_TRY;
customer360.getRange("H6:H255").format.numberFormat = FMT_TRY;
customer360.getRange("J6:J255").format.numberFormat = FMT_PCT;
customer360.getRange("N6:N255").format.numberFormat = FMT_TRY;
customer360.freezePanes.freezeRows(5);
customer360.getRange("J6:J255").conditionalFormats.add("colorScale", {
  criteria: [
    { type: "lowestValue", color: C.paleGreen },
    { type: "percentile", value: 50, color: C.paleAmber },
    { type: "highestValue", color: C.paleRed },
  ],
});
setWidths(customer360, { "A:A": 15, "B:C": 22, "D:E": 14, "F:F": 18, "G:G": 25, "H:H": 18, "I:M": 18, "N:N": 21, "O:O": 16 });

// Monthly Trends
titleBand(
  monthlyTrends,
  "Monthly Customer & Revenue Trends",
  "Four-year operational history",
  "L",
);
monthlyTrends.getRange("A5:H53").values = [
  [
    "Month",
    "Orders",
    "Active Customers",
    "New Customers",
    "Net Revenue",
    "Gross Margin",
    "AOV",
    "Repeat Rate",
  ],
  ...monthly.rows.map((row) => [
    row[monthly.headers.indexOf("month")],
    row[monthly.headers.indexOf("orders")],
    row[monthly.headers.indexOf("active_customers")],
    row[monthly.headers.indexOf("new_customers")],
    row[monthly.headers.indexOf("net_revenue")],
    row[monthly.headers.indexOf("gross_margin")],
    row[monthly.headers.indexOf("average_order_value")],
    row[monthly.headers.indexOf("repeat_customer_rate")],
  ]),
];
styleTable(monthlyTrends, "A5:H53", "A5:H5", { fontSize: 8 });
monthlyTrends.getRange("E6:G53").format.numberFormat = FMT_TRY;
monthlyTrends.getRange("H6:H53").format.numberFormat = FMT_PCT;
monthlyTrends.getRange("J5:L53").values = [
  ["Month", "Net Revenue", "Gross Margin"],
  ...monthly.rows.map((row) => [
    row[monthly.headers.indexOf("month")],
    row[monthly.headers.indexOf("net_revenue")],
    row[monthly.headers.indexOf("gross_margin")],
  ]),
];
styleTable(monthlyTrends, "J5:L53", "J5:L5", { fontSize: 8 });
monthlyTrends.getRange("K6:L53").format.numberFormat = FMT_TRY;
const monthlyRevenueChart = monthlyTrends.charts.add(
  "line",
  monthlyTrends.getRange("J5:L53"),
);
monthlyRevenueChart.title = "Revenue and Gross Margin Trend";
monthlyRevenueChart.setPosition("A56", "F74");
const monthlyCustomerChart = monthlyTrends.charts.add(
  "column",
  monthlyTrends.getRange("A5:D53"),
);
monthlyCustomerChart.title = "Active and New Customers";
monthlyCustomerChart.setPosition("G56", "L74");
setWidths(monthlyTrends, { "A:A": 16, "B:H": 18, "I:L": 5 });

// QA checks
titleBand(
  checks,
  "Automated QA Checks",
  "Formula-backed controls plus pipeline data-quality results",
  "H",
);
checks.getRange("A5:F12").values = [
  ["Control", "Expected", "Actual", "Tolerance", "Status", "Owner"],
  ["Customer count", 6000, null, 0, null, "Analytics"],
  ["Minimum churn probability is valid", 1, null, 0, null, "Model Risk"],
  ["Maximum churn probability is valid", 1, null, 0, null, "Model Risk"],
  ["Campaign budget is within cap", 1, null, 0, null, "Marketing"],
  ["SHAP importance share", 1, null, 0.0001, null, "Analytics"],
  ["Data quality checks passed", quality.rows.length, null, 0, null, "Data Engineering"],
  ["Cohort retention bounds", 1, null, 0, null, "Analytics"],
];
checks.getRange("C6").formulas = [[`=COUNTA(${customerCountRange})`]];
checks.getRange("C7").formulas = [[`=IF(MIN(${churnRange})>=0,1,0)`]];
checks.getRange("C8").formulas = [[`=IF(MAX(${churnRange})<=1,1,0)`]];
checks.getRange("C9").formulas = [[
  `=IF(SUM(${sourceRange("Campaign Data", campaignSummary, "allocated_budget")})<=Assumptions!B6,1,0)`,
]];
checks.getRange("C10").formulas = [[`=SUM(${sourceRange("SHAP Data", shapGlobal, "importance_share")})`]];
checks.getRange("C11").formulas = [[
  `=COUNTIF($B$17:$B$${quality.rows.length + 16},"PASS")`,
]];
checks.getRange("C12").formulas = [[
  `=IF(AND(MIN(${sourceRange("Cohort Data", cohortLong, "retention_rate")})>=0,MAX(${sourceRange("Cohort Data", cohortLong, "retention_rate")})<=1),1,0)`,
]];
for (let row = 6; row <= 12; row += 1) {
  checks.getRange(`E${row}`).formulas = [[
    `=IF(ABS(C${row}-B${row})<=D${row},"PASS","FAIL")`,
  ]];
}
styleTable(checks, "A5:F12", "A5:F5");
checks.getRange("B6:D12").format.numberFormat = FMT_DEC;
checks.getRange("E6:E12").conditionalFormats.add("containsText", {
  text: "PASS",
  format: { fill: C.paleGreen, font: { color: "#0F7C62", bold: true } },
});
checks.getRange("E6:E12").conditionalFormats.add("containsText", {
  text: "FAIL",
  format: { fill: C.paleRed, font: { color: C.red, bold: true } },
});
section(checks, "A15:F15", "Pipeline Quality Gate Results");
checks.getRange(`A16:C${quality.rows.length + 16}`).values = [
  quality.headers,
  ...quality.rows,
];
styleTable(
  checks,
  `A16:C${quality.rows.length + 16}`,
  "A16:C16",
  { fontSize: 8 },
);
setWidths(checks, { "A:A": 38, "B:D": 18, "E:E": 14, "F:F": 20 });

// Data Dictionary
titleBand(
  dictionary,
  "Customer Intelligence Data Dictionary",
  "Core analytical entities, KPIs and modeling definitions",
  "H",
);
dictionary.getRange("A5:H25").values = [
  ["Entity", "Field / KPI", "Type", "Definition", "Grain", "Window", "Owner", "Notes"],
  ["customer_360", "Customer ID", "Key", "Synthetic customer identifier", "Customer", "Snapshot", "CRM", "No real PII"],
  ["customer_360", "Recency Days", "Days", "Days since latest order at snapshot", "Customer", "Lifetime", "Analytics", "Point-in-time"],
  ["customer_360", "Frequency 12M", "Count", "Distinct orders in trailing 12 months", "Customer", "12M", "Analytics", "RFM input"],
  ["customer_360", "Revenue 12M", "TRY", "Net recognized revenue in trailing 12 months", "Customer", "12M", "Finance", "After returns"],
  ["rfm_scores", "RFM Segment", "Category", "Business segment from R, F and M quintiles", "Customer", "12M", "CRM", "10 segments"],
  ["cohort_retention", "Retention Rate", "Percentage", "Active customers divided by original cohort size", "Cohort-month", "Monthly", "Growth", "First purchase"],
  ["clv_predictions", "Predicted CLV 12M", "TRY", "Expected future 365-day gross-margin contribution", "Customer", "12M future", "Analytics", "Non-negative"],
  ["churn_predictions", "Churn Probability", "Probability", "Calibrated likelihood of no order in next 90 days", "Customer", "90D future", "Analytics", "Time holdout"],
  ["shap_importance", "Mean |SHAP|", "Probability", "Average absolute feature contribution", "Feature", "Production sample", "Model Risk", "Additive"],
  ["campaign_targets", "Expected Incremental Margin", "TRY", "Expected response margin less contact cost", "Customer", "Campaign", "Marketing", "Scenario input"],
  ["campaign_targets", "Selected for Campaign", "Boolean", "Budget-constrained target flag", "Customer", "Campaign", "Marketing", "Consent required"],
  ["drift_monitoring", "PSI", "Index", "Population Stability Index vs 2024 holdout", "Feature", "Snapshot", "Model Risk", "<0.10 stable"],
  ["fairness_audit", "True Positive Rate", "Percentage", "Recall within monitoring group", "Group", "Holdout", "Model Risk", "Audit only"],
  ["churn_model", "ROC-AUC", "Metric", "Ranking performance across all thresholds", "Model", "Holdout", "Analytics", "Higher is better"],
  ["churn_model", "PR-AUC", "Metric", "Precision-recall tradeoff", "Model", "Holdout", "Analytics", "Higher is better"],
  ["churn_model", "Brier Score", "Metric", "Mean squared probability error", "Model", "Holdout", "Analytics", "Lower is better"],
  ["clv_model", "MAE", "TRY", "Mean absolute future-margin prediction error", "Model", "Holdout", "Analytics", "Lower is better"],
  ["clv_model", "R²", "Metric", "Explained variance on time holdout", "Model", "Holdout", "Analytics", "Higher is better"],
  ["campaign", "Expected ROI", "Multiple", "Expected incremental margin divided by contact cost", "Action", "Campaign", "Marketing", "Model-based"],
  ["quality", "Data Quality Gate", "Boolean", "Automated structural and business-rule validation", "Project", "Build", "Data Engineering", "10 controls"],
];
styleTable(dictionary, "A5:H25", "A5:H5", { fontSize: 8 });
dictionary.getRange("A5:H25").format.wrapText = true;
setWidths(dictionary, { "A:A": 24, "B:B": 28, "C:C": 16, "D:D": 48, "E:H": 20 });

// Sources
titleBand(
  sources,
  "Sources, Lineage & Data Notice",
  "Synthetic portfolio data, generated artifacts and ownership",
  "I",
);
sources.getRange("A5:I18").values = [
  ["Item", "Location", "Purpose", "Type", "Period", "Owner", "Disclosure", "Refresh", "Status"],
  ["Customer dimension", "Data/Raw/dim_customers.csv", "Customer attributes", "Generated", "2022-2025", "CRM", "Synthetic", "Pipeline", "READY"],
  ["Orders", "Data/Raw/fact_orders.csv", "Revenue and frequency", "Generated", "2022-2025", "Commerce", "Synthetic", "Pipeline", "READY"],
  ["Order lines", "Data/Raw/fact_order_lines.csv", "Category and margin", "Generated", "2022-2025", "Commerce", "Synthetic", "Pipeline", "READY"],
  ["Interactions", "Data/Raw/fact_interactions_monthly.csv", "Engagement features", "Generated", "2022-2025", "Digital", "Synthetic", "Pipeline", "READY"],
  ["Campaign history", "Data/Raw/fact_campaign_responses.csv", "Response calibration", "Generated", "2024-2025", "Marketing", "Synthetic", "Pipeline", "READY"],
  ["RFM", "Data/Processed/rfm_scores.csv", "Behavior segmentation", "Calculated", "31 Dec 2025", "Analytics", "Synthetic", "Pipeline", "READY"],
  ["Cohorts", "Data/Processed/cohort_retention_long.csv", "Retention analysis", "Calculated", "2022-2025", "Growth", "Synthetic", "Pipeline", "READY"],
  ["CLV", "Data/Processed/clv_predictions.csv", "Future value", "Model output", "2026 horizon", "Analytics", "Synthetic", "Pipeline", "READY"],
  ["Churn", "Data/Processed/churn_predictions.csv", "90-day risk", "Model output", "31 Dec 2025", "Analytics", "Synthetic", "Pipeline", "READY"],
  ["SHAP", "Data/Processed/shap_global_importance.csv", "Explainability", "Model output", "Production", "Model Risk", "Synthetic", "Pipeline", "READY"],
  ["Campaign targets", "Data/Processed/campaign_targets.csv", "Activation plan", "Optimization", "Next campaign", "Marketing", "Synthetic", "Pipeline", "READY"],
  ["Author", "Murat Miraç Gedik", "Portfolio attribution", "Metadata", "July 2026", "Author", "No real company data", "Versioned", "READY"],
  ["License", "LICENSE", "Open-source terms", "MIT", "2026", "Author", "Portfolio use", "Versioned", "READY"],
];
styleTable(sources, "A5:I18", "A5:I5", { fontSize: 8 });
sources.getRange("A5:I18").format.wrapText = true;
setWidths(sources, { "A:A": 24, "B:B": 44, "C:C": 30, "D:I": 18 });

// Raw data formatting and widths
customerData.getRange(
  `${fieldCol(customer, "monetary_12m")}6:${fieldCol(customer, "gross_margin_12m")}${customer.rows.length + 5}`,
).format.numberFormat = FMT_TRY;
customerData.getRange(
  `${fieldCol(customer, "predicted_clv_12m")}6:${fieldCol(customer, "predicted_clv_12m")}${customer.rows.length + 5}`,
).format.numberFormat = FMT_TRY;
customerData.getRange(
  `${fieldCol(customer, "churn_probability")}6:${fieldCol(customer, "churn_probability")}${customer.rows.length + 5}`,
).format.numberFormat = FMT_PCT;
setWidths(customerData, { "A:A": 15, "B:AT": 18 });
setWidths(segmentData, { "A:A": 28, "B:I": 20 });
setWidths(cohortData, { "A:E": 18 });
setWidths(monthlyData, { "A:L": 18 });
setWidths(campaignData, { "A:A": 26, "B:I": 20 });
setWidths(modelData, { "A:B": 38, "C:K": 16 });
setWidths(shapData, { "A:A": 32, "B:D": 18 });
setWidths(governanceData, { "A:B": 20, "C:N": 18 });

for (const sheet of [
  cover,
  dashboard,
  assumptions,
  rfmSheet,
  cohortSheet,
  clvSheet,
  churnSheet,
  campaignPlanner,
  modelPerformance,
  shapSheet,
  governanceSheet,
  customer360,
  monthlyTrends,
  checks,
  dictionary,
  sources,
]) {
  sheet.getUsedRange()?.format?.autofitRows?.();
}

await fs.mkdir(outputDir, { recursive: true });
await fs.mkdir(previewDir, { recursive: true });
const outputPath = path.join(
  outputDir,
  "Customer_Intelligence_CLV_Churn_Campaign_Planner.xlsx",
);
const xlsx = await SpreadsheetFile.exportXlsx(workbook);
await xlsx.save(outputPath);

const previewSheets = [
  "Cover",
  "Executive Dashboard",
  "Assumptions",
  "RFM Segmentation",
  "Cohort Retention",
  "CLV Analysis",
  "Churn Analysis",
  "Campaign Planner",
  "Model Performance",
  "SHAP Drivers",
  "Fairness and Drift",
  "Customer 360",
  "Monthly Trends",
  "QA Checks",
  "Data Dictionary",
  "Sources",
];
for (const sheetName of previewSheets) {
  const important = ["Executive Dashboard", "Campaign Planner", "Model Performance"].includes(
    sheetName,
  );
  const preview = await workbook.render({
    sheetName,
    autoCrop: "all",
    scale: important ? 1.15 : 0.75,
    format: "png",
  });
  const safeName = sheetName.toLowerCase().replaceAll(" ", "-");
  await fs.writeFile(
    path.join(previewDir, `${safeName}.png`),
    new Uint8Array(await preview.arrayBuffer()),
  );
}

const inspection = await workbook.inspect({
  kind: "workbook,sheet,formula,drawing",
  maxChars: 25000,
  tableMaxRows: 8,
  tableMaxCols: 10,
  options: { maxResults: 320 },
});
await fs.writeFile(
  path.join(outputDir, "workbook_inspection.json"),
  JSON.stringify(inspection, null, 2),
  "utf8",
);
const errorScan = await workbook.inspect({
  kind: "match",
  searchTerm: "#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A",
  options: { useRegex: true, maxResults: 200 },
  maxChars: 12000,
});
await fs.writeFile(
  path.join(outputDir, "formula_error_scan.json"),
  JSON.stringify(errorScan, null, 2),
  "utf8",
);
await fs.rm(`${outputPath}.inspect.ndjson`, { force: true });
console.log(outputPath);
