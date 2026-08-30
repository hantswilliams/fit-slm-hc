// FIT-SLM-HC Manuscript Task Dataset
// Source: Williams (2026). FIT-SLM-HC: A Task-Technology Fit Framework for
// Identifying Small Language Model Suitable Tasks in Healthcare.
// Dataset version: aug28 snapshot (matches Table 5 of manuscript/main.tex
// and analysis/data/tasks_master.csv in this repository).
// Changes from the prior snapshot: Pathology IE denominator 97 ("over 97%"
// in the source text; AR 0.94), 4-bit variant corrected to 69% (AR 0.71),
// and the wearable vignette re-referenced to the cloud baseline in its own
// source table (GPT-4 72.2; AR 0.87), with the on-device comparison noted.

const DATASET_VERSION = "aug28-2026";

const MANUSCRIPT_TASKS = [
  // Vignette C (reference-standard vignette; not an extended-table row)
  { task: "Fatigue Prediction (Wearable)", source: "Wang 2025", slm: "Phi-3-mini-4k", ref: "GPT-4 (cloud)", r: 1, k: 1, o: 1, metric: "Accuracy", slmScore: 62.88, refScore: 72.2, ar: 0.87, le: null, envelope: false, vignette: "C", note: "Reference standard flips the verdict: against the on-device comparator (Llama-2-7B, 41.2) the same SLM scores AR = 1.53; the source reports time-to-first-token for on-device models only (LE = 0.78 on-device), so no cloud LE exists." },
  // Vignette B (not an extended-table row)
  { task: "Clinical Note Summarization", source: "Naemi 2025", slm: "LLaMa-3-8B", ref: "GPT-4o", r: 2, k: 1, o: 2, metric: "ROUGE-1", slmScore: 0.535, refScore: 0.731, ar: 0.73, le: 0.50, envelope: false, vignette: "B", note: "On BERTScore (semantic similarity) the same comparison gives AR = 0.98; metric choice is a governance decision. Reported timing settings in the source are partly ambiguous, so LE is indicative." },
  // Extended table — Low complexity (r+k+o = 3)
  { task: "Report Labeling", source: "Zheng 2026", slm: "OPT-350M", ref: "GPT-4o", r: 1, k: 1, o: 1, metric: "F1", slmScore: 0.894, refScore: 0.728, ar: 1.23, le: null, envelope: true },
  { task: "Text Classification", source: "Wu 2025", slm: "MMedIns-Llama3-8B", ref: "GPT-4", r: 1, k: 1, o: 1, metric: "F1", slmScore: 86.7, refScore: 68.1, ar: 1.27, le: null, envelope: true },
  { task: "Information Extraction", source: "Wu 2025", slm: "MMedIns-Llama3-8B", ref: "GPT-4", r: 1, k: 1, o: 1, metric: "Accuracy", slmScore: 83.8, refScore: 76.9, ar: 1.09, le: null, envelope: true },
  { task: "Stress Detection", source: "Hanafi 2024", slm: "Gemma 2 9B", ref: "GPT-4", r: 1, k: 1, o: 1, metric: "Accuracy", slmScore: 72, refScore: 70, ar: 1.03, le: null, envelope: true },
  // Low-moderate complexity (r+k+o = 4)
  { task: "DICOM Harmonization", source: "Zheng 2026", slm: "OPT-350M", ref: "GPT-4o", r: 1, k: 2, o: 1, metric: "Accuracy", slmScore: 0.975, refScore: 0.878, ar: 1.11, le: null, envelope: true },
  { task: "Clinical NER", source: "Wu 2025", slm: "MMedIns-Llama3-8B", ref: "GPT-4", r: 1, k: 2, o: 1, metric: "F1", slmScore: 79.3, refScore: 59.5, ar: 1.33, le: null, envelope: true },
  { task: "Pathology IE", source: "Grothey 2025", slm: "Llama3-8B", ref: "GPT-4", r: 1, k: 2, o: 1, metric: "Accuracy", slmScore: 91, refScore: 97, ar: 0.94, le: 0.54, envelope: true, vignette: "A", note: "Denominator 97 from the source text (\u201cover 97%\u201d; a figure panel shows 98, which would give AR 0.93 with the same verdicts). LE is the midpoint of an interval, 0.50\u20130.58. Inside at the 0.90 default; outside strict 0.95 non-inferiority." },
  { task: "Pathology IE (4-bit)", source: "Grothey 2025", slm: "Llama3-8B 4-bit", ref: "GPT-4", r: 1, k: 2, o: 1, metric: "Accuracy", slmScore: 69, refScore: 97, ar: 0.71, le: null, envelope: false },
  { task: "Clinical Report IE", source: "Liu 2025", slm: "Llama-3.1-8B (LoRA)", ref: "GPT-4", r: 1, k: 2, o: 1, metric: "Exact Match", slmScore: 90.0, refScore: 86.1, ar: 1.05, le: null, envelope: true },
  { task: "Biomedical Lit. CLS (binary)", source: "Dawood 2025", slm: "Qwen2.5-7B", ref: "Gemini 2.5", r: 1, k: 2, o: 1, metric: "Accuracy", slmScore: 92, refScore: 90, ar: 1.02, le: null, envelope: true },
  { task: "Depression Detection", source: "Hanafi 2024", slm: "Gemma 2 9B", ref: "GPT-4", r: 2, k: 1, o: 1, metric: "Accuracy", slmScore: 80.4, refScore: 85.0, ar: 0.95, le: null, envelope: true },
  { task: "Suicide Detection", source: "Hanafi 2024", slm: "Llama3-8B", ref: "GPT-4", r: 2, k: 1, o: 1, metric: "Accuracy", slmScore: 58, refScore: 70, ar: 0.83, le: null, envelope: false },
  // Moderate complexity (r+k+o = 5)
  { task: "Impression Generation", source: "Zheng 2026", slm: "OPT-350M", ref: "GPT-4o", r: 2, k: 1, o: 2, metric: "Likert (ordinal)", slmScore: 4.39, refScore: 3.65, ar: 1.20, le: null, envelope: true, note: "Likert-based AR is illustrative only, not a defensible ratio." },
  { task: "Diagnosis (DDXPlus)", source: "Wu 2025", slm: "MMedIns-Llama3-8B", ref: "GPT-4", r: 2, k: 2, o: 1, metric: "Accuracy", slmScore: 97.5, refScore: 58.1, ar: 1.68, le: null, envelope: true },
  { task: "Treatment Planning", source: "Wu 2025", slm: "MMedIns-Llama3-8B", ref: "GPT-4", r: 2, k: 2, o: 1, metric: "Accuracy", slmScore: 98.5, refScore: 84.7, ar: 1.16, le: null, envelope: true },
  { task: "ICD-10 Coding", source: "Hou 2025", slm: "Llama-1B (fine-tuned)", ref: "GPT-4o mini", r: 2, k: 2, o: 1, metric: "Exact Match", slmScore: 93, refScore: 90, ar: 1.03, le: null, envelope: true },
  { task: "Radiology QA", source: "Ranjit 2024", slm: "RadPhi-3 3.8B", ref: "GPT-4", r: 2, k: 2, o: 1, metric: "F1", slmScore: 40.3, refScore: 34.0, ar: 1.19, le: null, envelope: true },
  { task: "DDI Prediction", source: "De Vito 2025", slm: "Phi-3.5 2.7B (LoRA)", ref: "GPT-4o", r: 2, k: 2, o: 1, metric: "Accuracy", slmScore: 0.913, refScore: 0.926, ar: 0.99, le: null, envelope: true },
  { task: "Biomedical Lit. CLS (3-class)", source: "Dawood 2025", slm: "Llama3-8B", ref: "Gemini 2.5", r: 2, k: 2, o: 1, metric: "Accuracy", slmScore: 70, refScore: 90, ar: 0.78, le: null, envelope: false },
  // High complexity (r+k+o >= 6)
  { task: "Clinical Triage", source: "Wu 2025", slm: "MMedIns-Llama3-8B", ref: "GPT-4", r: 3, k: 2, o: 1, metric: "Accuracy", slmScore: 63.1, refScore: 60.1, ar: 1.05, le: null, envelope: true },
  { task: "Clinical IE (28-task aggregate)", source: "Builtjes 2025", slm: "Llama-3.1-8B", ref: "Llama-3.3-70B", r: 3, k: 2, o: 1, metric: "Utility", slmScore: 0.588, refScore: 0.760, ar: 0.77, le: null, envelope: false, note: "Composite of 28 sub-tasks whose individual axis sums vary; axis shown for display only." },
  { task: "Medical Exam QA", source: "Kim 2025", slm: "Meerkat-7B", ref: "GPT-4", r: 3, k: 3, o: 1, metric: "Accuracy", slmScore: 64.5, refScore: 76.6, ar: 0.84, le: null, envelope: false },
  { task: "Medical QA (USMLE)", source: "Wu 2025", slm: "MMedIns-Llama3-8B", ref: "GPT-4", r: 3, k: 3, o: 1, metric: "Accuracy", slmScore: 63.6, refScore: 85.8, ar: 0.74, le: null, envelope: false },
];

// Contextual explanations by axis-sum band
const BAND_EXPLANATIONS = {
  low: "Of the 18 unique extended-table tasks with axis sum \u2264 5 in the manuscript, 16 reached AR \u2265 0.90 and 13 exceeded AR \u2265 1.0, most under fine-tuning or instruction-tuning. The most consistent results appeared on the most constrained tasks: report labeling, text classification, clinical NER, and information extraction. Results at AR \u2265 1.0 often reflect a fine-tuned SLM vs. a merely prompted cloud reference \u2014 an apples-to-oranges comparison that inflates the ratio. Note the manuscript's aug28 sensitivity analyses: the apparent axis-sum gradient is not robust to outcome-blind re-scoring or to removal of the two hardest tasks, so band summaries here are descriptive, not predictive.",
  mid: "Tasks at this complexity level (r+k+o = 6) showed mixed results. Clinical triage achieved AR = 1.05 with instruction-tuned SLMs, but a 28-task clinical IE composite (whose individual axis sums vary; reported here at 6 for display) fell to AR = 0.77. Careful, task-specific evaluation is recommended.",
  high: "Tasks in this complexity range (r+k+o \u2265 7) fell below AR \u2265 0.90 in the manuscript's analysis. Open-domain medical reasoning tasks achieved AR of 0.74\u20130.84. Cloud or human-led approaches are generally recommended."
};

const CONTEXTUAL_NOTES = {
  metricSensitivity: "The same task can appear adequate or inadequate depending on metric choice. Clinical note summarization showed AR = 0.73 on ROUGE-1 (content completeness) but AR = 0.98 on BERTScore (semantic similarity).",
  quantization: "System-side configuration changes can shift the envelope boundary. 4-bit quantization dropped one task from AR = 0.94 to AR = 0.71 on the same model and task.",
  fineTuning: "Fine-tuning acts as an 'envelope expander.' Instruction-tuned SLMs frequently outperformed zero-shot cloud models on constrained tasks (r+k+o \u2264 5). Many of the highest AR values in the manuscript reflect a fine-tuned SLM vs. a merely prompted cloud reference (3-shot GPT-4 in the largest source cluster) \u2014 a known asymmetry that inflates the ratio. Readers should interpret AR as SLM-suitability within a chosen evaluation setup, not as an absolute performance claim.",
  likertCaveat: "A small number of entries (e.g. Impression Generation) use Likert-rated quality scores. Ordinal Likert ratios are illustrative only and should not be interpreted as a defensible performance ratio.",
  latencyGap: "Of the 13 studies examined in the manuscript, only one reported timing for both systems in a form that supports LE; two more reported timing for one side only. The LE dimension remains under-reported in healthcare AI benchmarks.",
  referenceStandard: "An envelope verdict is indexed to its reference standard. In the wearable vignette, the same SLM on the same task scores AR = 1.53 against the best on-device comparator and AR = 0.87 against GPT-4 in the same source table. Always name the reference.",
  scope: "FIT-SLM-HC is a deployment-triage overlay, not a replacement for full benchmarking, calibration, or safety assessment."
};
