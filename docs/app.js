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

function buildCard(cat) {
  const card = makeEl("article", "card");

  if (cat.image && /^https?:\/\//.test(cat.image)) {
    const img = makeEl("img");
    img.src = cat.image;
    img.alt = cat.name;
    img.loading = "lazy";
    img.referrerPolicy = "no-referrer";
    img.addEventListener("error", () => img.remove());
    card.append(img);
  }

  const body = makeEl("div", "body");
  body.append(makeEl("h2", "", cat.name));
  const metaParts = [cat.county, cat.colour, cat.sex, cat.age].filter(Boolean);
  body.append(makeEl("div", "meta", metaParts.join("・")));
  if (cat.shelter) body.append(makeEl("div", "meta", cat.shelter));

  const link = makeEl("a", "", "前往原站查看");
  link.href = cat.url;
  link.target = "_blank";
  link.rel = "noopener noreferrer";
  body.append(link);

  card.append(body);
  return card;
}

function render() {
  const selected = selectEl.value;
  const visible = cats.filter((cat) => matches(cat, selected));

  gridEl.replaceChildren(...visible.map(buildCard));
  emptyEl.hidden = visible.length > 0;
  summaryEl.textContent = selected
    ? `共 ${visible.length} 隻黑貓`
    : `全台共 ${visible.length} 隻黑貓`;
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

selectEl.addEventListener("change", render);
load();
