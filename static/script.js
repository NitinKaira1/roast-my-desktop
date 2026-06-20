// static/script.js
"use strict";

const dropzone = document.getElementById("dropzone");
const dropzoneEmpty = document.getElementById("dropzoneEmpty");
const fileInput = document.getElementById("fileInput");
const previewImg = document.getElementById("previewImg");
const clearBtn = document.getElementById("clearBtn");

const judgeSelect = document.getElementById("judgeSelect");
const analyzeBtn = document.getElementById("analyzeBtn");
const randomBtn = document.getElementById("randomBtn");
const allBtn = document.getElementById("allBtn");

const verdictPlaceholder = document.getElementById("verdictPlaceholder");
const verdictLoading = document.getElementById("verdictLoading");
const verdictContent = document.getElementById("verdictContent");
const verdictError = document.getElementById("verdictError");
const verdictJudgeName = document.getElementById("verdictJudgeName");
const verdictText = document.getElementById("verdictText");
const loadingText = document.getElementById("loadingText");

let selectedFile = null;

const LOADING_MESSAGES = [
  "The court is deliberating…",
  "Reviewing the evidence…",
  "Cross-examining your tabs…",
  "Consulting case law…",
  "The bench is not impressed yet…",
];

// ---------------- FILE HANDLING ----------------

function setFile(file) {
  if (!file) return;

  const validTypes = ["image/png", "image/jpeg", "image/webp"];
  if (!validTypes.includes(file.type)) {
    showError("Unsupported file type. Please upload a PNG, JPG, or WEBP image.");
    return;
  }

  if (file.size > 10 * 1024 * 1024) {
    showError("Image too large. Max size is 10MB.");
    return;
  }

  selectedFile = file;

  const reader = new FileReader();
  reader.onload = (e) => {
    previewImg.src = e.target.result;
    previewImg.hidden = false;
    dropzoneEmpty.hidden = true;
    clearBtn.hidden = false;
  };
  reader.readAsDataURL(file);

  resetVerdict();
}

function clearFile() {
  selectedFile = null;
  fileInput.value = "";
  previewImg.src = "";
  previewImg.hidden = true;
  dropzoneEmpty.hidden = false;
  clearBtn.hidden = true;
  resetVerdict();
}

dropzone.addEventListener("click", () => fileInput.click());

fileInput.addEventListener("change", () => {
  if (fileInput.files && fileInput.files[0]) {
    setFile(fileInput.files[0]);
  }
});

clearBtn.addEventListener("click", (e) => {
  e.stopPropagation();
  clearFile();
});

["dragenter", "dragover"].forEach((evt) => {
  dropzone.addEventListener(evt, (e) => {
    e.preventDefault();
    e.stopPropagation();
    dropzone.classList.add("dragover");
  });
});

["dragleave", "drop"].forEach((evt) => {
  dropzone.addEventListener(evt, (e) => {
    e.preventDefault();
    e.stopPropagation();
    dropzone.classList.remove("dragover");
  });
});

dropzone.addEventListener("drop", (e) => {
  const file = e.dataTransfer.files && e.dataTransfer.files[0];
  if (file) setFile(file);
});

// also support pasting an image from clipboard
window.addEventListener("paste", (e) => {
  const items = e.clipboardData && e.clipboardData.items;
  if (!items) return;
  for (const item of items) {
    if (item.type.startsWith("image/")) {
      const file = item.getAsFile();
      if (file) setFile(file);
      break;
    }
  }
});

// ---------------- VERDICT RENDERING ----------------

function resetVerdict() {
  verdictPlaceholder.hidden = false;
  verdictLoading.hidden = true;
  verdictContent.hidden = true;
  verdictError.hidden = true;
}

function showLoading() {
  verdictPlaceholder.hidden = true;
  verdictLoading.hidden = false;
  verdictContent.hidden = true;
  verdictError.hidden = true;
  loadingText.textContent =
    LOADING_MESSAGES[Math.floor(Math.random() * LOADING_MESSAGES.length)];
}

function showError(message) {
  verdictPlaceholder.hidden = true;
  verdictLoading.hidden = true;
  verdictContent.hidden = true;
  verdictError.hidden = false;
  verdictError.textContent = message;
}

function showResult(judgeName, resultText) {
  verdictPlaceholder.hidden = true;
  verdictLoading.hidden = true;
  verdictError.hidden = true;
  verdictContent.hidden = false;
  verdictJudgeName.textContent = judgeName;
  verdictText.innerHTML = renderMarkdownish(resultText);
}

// Minimal, dependency-free markdown-ish renderer.
// Handles: # ## ### headings, **bold**, bullet lists, numbered lists, horizontal rules, line breaks.
function renderMarkdownish(raw) {
  const escapeHtml = (s) =>
    s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");

  const lines = escapeHtml(raw).split("\n");
  let html = "";
  let inList = false;
  let listType = null;

  const closeList = () => {
    if (inList) {
      html += listType === "ol" ? "</ol>" : "</ul>";
      inList = false;
      listType = null;
    }
  };

  for (let line of lines) {
    const trimmed = line.trim();

    if (trimmed === "" ) {
      closeList();
      continue;
    }

    if (/^---+$/.test(trimmed)) {
      closeList();
      html += "<hr>";
      continue;
    }

    let headingMatch = trimmed.match(/^(#{1,3})\s+(.*)$/);
    if (headingMatch) {
      closeList();
      const level = headingMatch[1].length;
      html += `<h${level}>${inlineFormat(headingMatch[2])}</h${level}>`;
      continue;
    }

    let bulletMatch = trimmed.match(/^[-*•]\s+(.*)$/);
    if (bulletMatch) {
      if (!inList || listType !== "ul") {
        closeList();
        html += "<ul>";
        inList = true;
        listType = "ul";
      }
      html += `<li>${inlineFormat(bulletMatch[1])}</li>`;
      continue;
    }

    let numberedMatch = trimmed.match(/^\d+[.)]\s+(.*)$/);
    if (numberedMatch) {
      if (!inList || listType !== "ol") {
        closeList();
        html += "<ol>";
        inList = true;
        listType = "ol";
      }
      html += `<li>${inlineFormat(numberedMatch[1])}</li>`;
      continue;
    }

    closeList();
    html += `<p>${inlineFormat(trimmed)}</p>`;
  }

  closeList();
  return html;
}

function inlineFormat(text) {
  return text
    .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
    .replace(/\*(.+?)\*/g, "<em>$1</em>")
    .replace(/`(.+?)`/g, "<code>$1</code>");
}

// ---------------- API CALLS ----------------

function setButtonsDisabled(disabled) {
  analyzeBtn.disabled = disabled;
  randomBtn.disabled = disabled;
  allBtn.disabled = disabled;
}

async function callApi(endpoint, formData) {
  const response = await fetch(endpoint, {
    method: "POST",
    body: formData,
  });

  let data;
  try {
    data = await response.json();
  } catch {
    throw new Error("The court received a malformed reply. Try again.");
  }

  if (!response.ok) {
    throw new Error(data.error || "Something went wrong. Try again.");
  }

  return data;
}

function requireFile() {
  if (!selectedFile) {
    showError("Please submit a screenshot before requesting a verdict.");
    return false;
  }
  return true;
}

async function handleAnalyze() {
  if (!requireFile()) return;

  showLoading();
  setButtonsDisabled(true);

  const formData = new FormData();
  formData.append("image", selectedFile);
  formData.append("judge_name", judgeSelect.value);

  try {
    const data = await callApi("/api/analyze", formData);
    showResult(data.judge_name, data.result);
  } catch (err) {
    showError(err.message);
  } finally {
    setButtonsDisabled(false);
  }
}

async function handleRandom() {
  if (!requireFile()) return;

  showLoading();
  setButtonsDisabled(true);

  const formData = new FormData();
  formData.append("image", selectedFile);

  try {
    const data = await callApi("/api/analyze-random", formData);
    showResult(data.judge_name, data.result);
  } catch (err) {
    showError(err.message);
  } finally {
    setButtonsDisabled(false);
  }
}

async function handleAll() {
  if (!requireFile()) return;

  showLoading();
  setButtonsDisabled(true);
  loadingText.textContent = "Convening the full tribunal — this takes a moment…";

  const formData = new FormData();
  formData.append("image", selectedFile);

  try {
    const data = await callApi("/api/analyze-all", formData);
    showResult(data.judge_name, data.result);
  } catch (err) {
    showError(err.message);
  } finally {
    setButtonsDisabled(false);
  }
}

analyzeBtn.addEventListener("click", handleAnalyze);
randomBtn.addEventListener("click", handleRandom);
allBtn.addEventListener("click", handleAll);
