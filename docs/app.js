const COUNTIES = [
  "臺北市", "新北市", "桃園市", "臺中市", "臺南市", "高雄市",
  "基隆市", "新竹市", "嘉義市",
  "新竹縣", "苗栗縣", "彰化縣", "南投縣", "雲林縣", "嘉義縣",
  "屏東縣", "宜蘭縣", "花蓮縣", "臺東縣", "澎湖縣", "金門縣", "連江縣",
];
const UNKNOWN = "__unknown__";

const selectEl = document.getElementById("county");
const gridEl = document.getElementById("grid");
const summaryEl = document.getElementById("summary");
const emptyEl = document.getElementById("empty");
const updatedEl = document.getElementById("updated");
const sortEl = document.getElementById("sort");
const typeEl = document.getElementById("type");
const moreEl = document.getElementById("more");

// 一次只顯示一批卡片，點「載入更多」才顯示下一批，避免一次載入全部圖片造成卡頓
const PAGE_SIZE = 24;
let shown = PAGE_SIZE;

let cats = [];

function makeEl(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined && text !== "") node.textContent = text;
  return node;
}

function countByCounty() {
  const counts = new Map();
  for (const cat of cats) {
    const key = cat.county || UNKNOWN;
    counts.set(key, (counts.get(key) || 0) + 1);
  }
  return counts;
}

function renderOptions() {
  const counts = countByCounty();
  selectEl.replaceChildren();
  selectEl.append(new Option(`全部縣市（${cats.length}）`, ""));
  for (const county of COUNTIES) {
    const n = counts.get(county) || 0;
    selectEl.append(new Option(`${county}（${n}）`, county));
  }
  if (counts.has(UNKNOWN)) {
    selectEl.append(new Option(`未標示縣市（${counts.get(UNKNOWN)}）`, UNKNOWN));
  }
}

function matches(cat, selected) {
  if (!selected) return true;
  if (selected === UNKNOWN) return !cat.county;
  return cat.county === selected;
}

function matchesType(cat, mode) {
  return !mode || cat.source_type === mode;
}

// 沒有照片時使用統一的黑貓占位圖；占位圖也載入失敗時，退回文字占位框
const PLACEHOLDER_IMG = "assets/no-photo.png";

function textPlaceholder() {
  return makeEl("div", "media placeholder", "無照片");
}

function placeholder() {
  const wrap = makeEl("div", "media");
  const img = makeEl("img");
  img.src = PLACEHOLDER_IMG;
  img.alt = "無照片";
  img.decoding = "async";
  img.addEventListener("error", () => wrap.replaceWith(textPlaceholder()));
  wrap.append(img);
  return wrap;
}

// 有圖片網址就顯示圖片；沒有網址或載入失敗時，都換成統一的占位圖
function buildMedia(cat) {
  if (!cat.image || !/^https?:\/\//.test(cat.image)) {
    return placeholder();
  }
  const wrap = makeEl("div", "media");
  const img = makeEl("img");
  img.src = cat.image;
  img.alt = cat.name;
  img.loading = "lazy";
  img.decoding = "async";
  img.referrerPolicy = "no-referrer";
  img.addEventListener("error", () => wrap.replaceWith(placeholder()));
  wrap.append(img);
  return wrap;
}

function buildCard(cat) {
  const card = makeEl("article", "card");
  card.append(buildMedia(cat));

  const body = makeEl("div", "body");
  const isPrivate = cat.source_type === "private";
  body.append(makeEl("span", `tag ${isPrivate ? "private" : "public"}`, isPrivate ? "民間" : "公家"));
  body.append(makeEl("h2", "", cat.name));
  const metaParts = [cat.county, cat.colour, cat.sex, cat.age].filter(Boolean);
  body.append(makeEl("div", "meta", metaParts.join("・")));
  if (cat.shelter) body.append(makeEl("div", "meta", cat.shelter));

  const link = makeEl("a", "", "搜尋此收容所");
  link.href = cat.url;
  link.target = "_blank";
  link.rel = "noopener noreferrer";
  body.append(link);

  card.append(body);
  return card;
}

function sortCats(list, mode) {
  if (mode === "age-asc") {
    // age_rank 越小越年輕；未知年齡排在最後。Array.prototype.sort 穩定，同年齡保留原順序
    return [...list].sort((a, b) => (a.age_rank ?? 99) - (b.age_rank ?? 99));
  }
  return list;
}

function render() {
  const selected = selectEl.value;
  const visible = sortCats(
    cats.filter((cat) => matches(cat, selected) && matchesType(cat, typeEl.value)),
    sortEl.value,
  );

  gridEl.replaceChildren(...visible.slice(0, shown).map(buildCard));
  moreEl.hidden = visible.length <= shown;
  emptyEl.hidden = visible.length > 0;
  summaryEl.textContent = selected
    ? `共 ${visible.length} 隻黑貓`
    : `全台共 ${visible.length} 隻黑貓`;
}

// 篩選或排序改變時，從第一批重新開始
function resetAndRender() {
  shown = PAGE_SIZE;
  render();
}

async function load() {
  try {
    const res = await fetch("data/cats.json", { cache: "no-cache" });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    cats = data.cats || [];
    updatedEl.textContent = data.updated_at
      ? `資料更新於 ${new Date(data.updated_at).toLocaleString("zh-TW", { timeZone: "Asia/Taipei" })}`
      : "尚無資料";
  } catch (err) {
    updatedEl.textContent = "資料載入失敗，請稍後再試。";
    cats = [];
  }
  renderOptions();
  render();
}

selectEl.addEventListener("change", resetAndRender);
sortEl.addEventListener("change", resetAndRender);
typeEl.addEventListener("change", resetAndRender);
moreEl.addEventListener("click", () => {
  shown += PAGE_SIZE;
  render();
});
load();
