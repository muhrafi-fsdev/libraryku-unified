'use strict';

const $ = (id) => document.getElementById(id);

const elements = {
  main: $('main'),
  skip: $('skipLink'),
  views: [...document.querySelectorAll('[data-view]')],
  navLinks: [...document.querySelectorAll('[data-route]')],
  status: $('serviceStatus'),
  statusText: $('statusText'),
  toast: $('toast'),
  address: $('currentAddress'),
  // Mode database
  modeRadios: [...document.querySelectorAll('input[name^="dbmode"]')],
  modeLabels: [...document.querySelectorAll('[data-mode-text]')],
  homeSource: $('homeSource'),
  confirmDb: $('confirmDb'),
  // Beranda
  shelf: $('shelf'),
  shelfCaption: $('shelfCaption'),
  recentCards: $('recentCards'),
  // Katalog
  catSearch: $('catSearch'),
  catFilter: $('catFilter'),
  catCount: $('catCount'),
  catGrid: $('catGrid'),
  // Dashboard
  dashSearch: $('dashSearch'),
  dashFilter: $('dashFilter'),
  dashCount: $('dashCount'),
  table: $('bookTable'),
  list: $('bookList'),
  newBook: $('newBtn'),
  refresh: $('refreshBtn'),
  refreshLabel: $('refreshLabel'),
  // Formulir
  formDialog: $('formDialog'),
  form: $('bookForm'),
  formTitle: $('formTitle'),
  formHint: $('formHint'),
  formError: $('formError'),
  submit: $('submitBtn'),
  cancel: $('cancelBtn'),
  closeForm: $('closeFormBtn'),
  // Hapus
  dialog: $('confirmDialog'),
  confirmBook: $('confirmBook'),
  confirmError: $('confirmError'),
  confirmCancel: $('confirmCancel'),
  confirmDelete: $('confirmDelete'),
};

const ROUTES = {
  beranda: 'Beranda',
  katalog: 'Katalog',
  dashboard: 'Dashboard',
  perbandingan: 'Perbandingan',
  tentang: 'Tentang',
};

const MODES = {
  sql: { key: 'sql', engine: 'PostgreSQL', kind: 'SQL', base: '/api/sql', source: 'tabel books di PostgreSQL', idNote: 'id angka (integer)' },
  nosql: { key: 'nosql', engine: 'MongoDB', kind: 'NoSQL', base: '/api/nosql', source: 'koleksi books di MongoDB', idNote: 'id ObjectId (string 24 karakter)' },
};
const FIELDS = ['title', 'author', 'category', 'year', 'stock'];
const MAX_YEAR = new Date().getFullYear() + 1;
const SHELF_SLOTS = 7;
const numberFormat = new Intl.NumberFormat('id-ID');
const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');

let mode = loadStoredMode();
let loadController = null;
let route = 'beranda';
let books = [];
let loadState = 'loading'; // 'loading' | 'ready' | 'error'
let loadError = '';
let loadSeq = 0;
let editingId = null;
let saving = false;
let deleting = false;
let changedId = null;
let formTrigger = null;
let toastTimeout;
let changedTimeout;

/* ---------- Mode database ---------- */

function loadStoredMode() {
  try {
    const saved = window.sessionStorage.getItem('libraryku-mode');
    return saved === 'nosql' ? 'nosql' : 'sql';
  } catch (error) {
    return 'sql';
  }
}

function modeInfo() {
  return MODES[mode];
}

function booksUrl(suffix = '') {
  return `${modeInfo().base}/books${suffix}`;
}

// Nilai pseudo-acak yang stabil dari id (angka atau string) untuk bentuk punggung buku.
function seedOf(id) {
  let sum = 0;
  for (const char of String(id)) sum = (sum * 31 + char.charCodeAt(0)) % 100003;
  return sum;
}

/* ---------- API ---------- */

class ApiError extends Error {
  constructor(message, { status = 0, network = false, details = null } = {}) {
    super(message);
    this.status = status;
    this.network = network;
    this.details = details;
  }
}

async function api(path, options = {}) {
  let response;
  try {
    response = await fetch(path, {
      ...options,
      headers: { 'Content-Type': 'application/json', 'X-Requested-With': 'libraryku', ...(options.headers || {}) },
    });
  } catch (error) {
    throw new ApiError('Tidak dapat menghubungi server. Pastikan Docker Compose berjalan, lalu coba lagi.', { network: true });
  }
  const data = await response.json().catch(() => null);
  if (!response.ok) {
    if (data === null) {
      const gateway = [502, 503, 504].includes(response.status);
      throw new ApiError(
        gateway
          ? `Layanan API belum siap (HTTP ${response.status}). Tunggu beberapa detik, lalu coba lagi.`
          : `Server memberi respons yang tidak dikenali (HTTP ${response.status}).`,
        { status: response.status }
      );
    }
    if (response.status === 401 || response.status === 403 || response.status === 429) {
      throw new ApiError(data.error || (response.status === 401 ? 'Perlu login untuk mengubah data.' : 'Permintaan ditolak.'), { status: response.status });
    }
    const details = data.details || null;
    const firstDetail = details ? Object.values(details)[0] : '';
    throw new ApiError([data.error || `HTTP ${response.status}`, firstDetail].filter(Boolean).join(' '), {
      status: response.status,
      details,
    });
  }
  if (data === null) throw new ApiError('Respons server tidak bisa dibaca sebagai JSON.', { status: response.status });
  return data;
}

/* ---------- Status layanan & toast ---------- */

function setStatus(state, message) {
  elements.status.dataset.state = state;
  elements.statusText.textContent = message;
  elements.status.title = message;
}

function statusFromError(error) {
  if (error.network) return 'Server tidak terhubung';
  if (error.status === 503) return `${modeInfo().engine} tidak dapat diakses`;
  if (error.status === 429) return 'Terlalu banyak permintaan';
  return `API bermasalah (HTTP ${error.status})`;
}

async function checkHealth() {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), 6000);
  try {
    const checkMode = mode;
    await api(`${MODES[checkMode].base}/health`, { signal: controller.signal });
    if (checkMode === mode) setStatus('ready', `${MODES[checkMode].engine} terhubung`);
  } catch (error) {
    if (error.name !== 'AbortError') setStatus('error', statusFromError(error));
  } finally {
    clearTimeout(timer);
  }
}

function showToast(message, type = 'ok') {
  clearTimeout(toastTimeout);
  elements.toast.textContent = message;
  elements.toast.classList.toggle('is-error', type === 'error');
  elements.toast.classList.add('is-visible');
  toastTimeout = setTimeout(() => {
    elements.toast.classList.remove('is-visible');
    setTimeout(() => {
      if (!elements.toast.classList.contains('is-visible')) elements.toast.textContent = '';
    }, 300);
  }, type === 'error' ? 8000 : 4500);
}

/* ---------- Pembuat elemen ---------- */

function el(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

function icon(name) {
  const svgNs = 'http://www.w3.org/2000/svg';
  const svg = document.createElementNS(svgNs, 'svg');
  svg.setAttribute('class', 'icon');
  svg.setAttribute('aria-hidden', 'true');
  svg.setAttribute('focusable', 'false');
  const use = document.createElementNS(svgNs, 'use');
  use.setAttribute('href', `#i-${name}`);
  svg.appendChild(use);
  return svg;
}

function stockText(book) {
  return book.stock === 0 ? 'Habis' : `${numberFormat.format(book.stock)} eks.`;
}

// Warna punggung buku mengikuti kategori (stabil: kategori yang sama selalu warna yang sama).
const KNOWN_TONES = { Teknologi: 0, Umum: 1, Pendidikan: 2, Sejarah: 3, Fiksi: 4 };

function categoryTone(category) {
  if (Object.prototype.hasOwnProperty.call(KNOWN_TONES, category)) return KNOWN_TONES[category];
  let hash = 0;
  for (const char of category) hash = (hash * 31 + char.charCodeAt(0)) % 997;
  return hash % 5;
}

/* ---------- Rute (hash) ---------- */

function routeFromHash() {
  const name = window.location.hash.replace(/^#/, '');
  return Object.prototype.hasOwnProperty.call(ROUTES, name) ? name : null;
}

function applyRoute({ moveFocus }) {
  elements.views.forEach((view) => { view.hidden = view.dataset.view !== route; });
  elements.navLinks.forEach((link) => {
    if (link.closest('.nav') && link.dataset.route === route) link.setAttribute('aria-current', 'page');
    else link.removeAttribute('aria-current');
  });
  if (route === 'perbandingan') refreshComparison();
  document.title = route === 'beranda' ? 'LibraryKu | Perpustakaan digital kampus' : `${ROUTES[route]} | LibraryKu`;
  if (moveFocus) {
    window.scrollTo({ top: 0, behavior: 'auto' });
    const heading = document.querySelector(`[data-view="${route}"] h1`);
    if (heading) heading.focus({ preventScroll: true });
  }
}

window.addEventListener('hashchange', () => {
  const next = routeFromHash();
  if (next === null || next === route) return;
  route = next;
  applyRoute({ moveFocus: true });
});

// Tautan "Lewati ke konten" memakai #main; jangan ubah rute.
elements.skip.addEventListener('click', (event) => {
  event.preventDefault();
  elements.main.focus();
});

/* ---------- Statistik, filter, kartu ---------- */

function hasFilter(search, select) {
  return Boolean(search.value.trim() || select.value);
}

function filterBooks(search, select) {
  const tokens = search.value.trim().toLocaleLowerCase('id-ID').split(/\s+/).filter(Boolean);
  const category = select.value;
  return books.filter((book) => {
    if (category && book.category !== category) return false;
    const haystack = [book.title, book.author].join(' ').toLocaleLowerCase('id-ID');
    return tokens.every((token) => haystack.includes(token));
  });
}

// Pilihan filter mengikuti kategori yang benar-benar ada di database, termasuk yang dibuat lewat API.
function syncCategoryFilters() {
  const categories = [...new Set(books.map((book) => book.category))].sort((a, b) => a.localeCompare(b, 'id'));
  [elements.catFilter, elements.dashFilter].forEach((select) => {
    const current = select.value;
    select.replaceChildren(new Option('Semua kategori', ''), ...categories.map((name) => new Option(name, name)));
    select.value = categories.includes(current) ? current : '';
  });
}

function renderStats() {
  const ready = loadState === 'ready';
  const values = {
    titles: ready ? numberFormat.format(books.length) : '—',
    stock: ready ? numberFormat.format(books.reduce((sum, book) => sum + book.stock, 0)) : '—',
    categories: ready ? numberFormat.format(new Set(books.map((book) => book.category)).size) : '—',
  };
  document.querySelectorAll('[data-stat]').forEach((node) => { node.textContent = values[node.dataset.stat]; });
}

function countText(filtered, search, select) {
  if (loadState === 'loading') return 'Memuat daftar buku...';
  if (loadState === 'error') return 'Daftar buku belum bisa dimuat';
  const base = hasFilter(search, select) ? `${filtered.length} dari ${books.length} buku` : `${books.length} buku`;
  return loadError ? `${base} · gagal memperbarui, data mungkin belum terbaru` : base;
}

function stateBox({ tone = 'info', iconName, title, text, detail, actionLabel, onAction, actionHref }) {
  const box = el('div', 'state');
  box.dataset.tone = tone;
  const iconWrap = el('span', 'state-icon');
  iconWrap.appendChild(icon(iconName));
  box.append(iconWrap, el('p', 'state-title', title), el('p', 'state-text', text));
  if (detail) box.appendChild(el('p', 'state-detail', detail));
  if (actionLabel) {
    let action;
    if (actionHref) {
      action = el('a', 'btn btn-secondary', actionLabel);
      action.href = actionHref;
    } else {
      action = el('button', 'btn btn-secondary', actionLabel);
      action.type = 'button';
      action.addEventListener('click', onAction);
    }
    box.appendChild(action);
  }
  return box;
}

function bookCard(book, headingTag = 'h3') {
  const card = el('li', 'card');
  card.dataset.tone = String(categoryTone(book.category));
  card.append(
    el('span', 'tag', book.category),
    el(headingTag, 'card-title', book.title),
    el('p', 'card-author', book.author)
  );
  const meta = el('p', 'card-meta');
  const stock = el('span', book.stock === 0 ? 'stock-out' : 'stock-ok', book.stock === 0 ? 'Stok habis' : `Stok ${stockText(book)}`);
  meta.append(el('span', '', `Terbit ${book.year}`), stock);
  card.appendChild(meta);
  return card;
}

function skeletonCards(count) {
  return Array.from({ length: count }, () => {
    const card = el('li', 'card card-skeleton');
    card.setAttribute('aria-hidden', 'true');
    card.append(el('span', 'sk sk-tag'), el('span', 'sk sk-a'), el('span', 'sk sk-b'));
    return card;
  });
}

/* ---------- Beranda ---------- */

function renderShelf() {
  const newest = books.slice(0, SHELF_SLOTS); // API mengurutkan terbaru di atas (SQL: id DESC, MongoDB: _id DESC)
  const items = newest.map((book) => {
    const spine = el('li', 'spine');
    spine.dataset.tone = String(categoryTone(book.category));
    spine.style.setProperty('--h', `${150 + (seedOf(book.id) * 37 % 70)}px`);
    spine.style.setProperty('--w', `${46 + (seedOf(book.id) * 13 % 18)}px`);
    spine.appendChild(el('span', 'spine-title', book.title));
    return spine;
  });
  for (let i = items.length; i < SHELF_SLOTS; i += 1) {
    const empty = el('li', 'spine spine-empty');
    empty.style.setProperty('--h', `${150 + ((i * 29) % 60)}px`);
    items.push(empty);
  }
  elements.shelf.replaceChildren(...items);
  if (loadState === 'ready') {
    elements.shelfCaption.textContent = newest.length
      ? `Rak ini dibuat dari ${newest.length} buku terbaru di database. Slot kosong menunggu buku baru dari Dashboard.`
      : 'Rak masih kosong. Tambahkan buku pertama dari Dashboard.';
  } else {
    elements.shelfCaption.textContent = 'Rak ini dibuat dari buku terbaru di database.';
  }
}

function renderRecent() {
  let nodes;
  if (loadState === 'loading') {
    nodes = skeletonCards(3);
  } else if (loadState === 'error') {
    const item = el('li', 'cards-note');
    item.appendChild(stateBox({
      tone: 'error', iconName: 'alert', title: 'Koleksi belum bisa dimuat',
      text: 'Lihat status koneksi di bagian atas halaman.', actionLabel: 'Coba lagi', onAction: () => loadBooks(),
    }));
    nodes = [item];
  } else if (books.length === 0) {
    const item = el('li', 'cards-note');
    item.appendChild(stateBox({
      iconName: 'book', title: 'Belum ada buku di koleksi',
      text: 'Tambahkan buku pertama dari halaman Dashboard.', actionLabel: 'Buka Dashboard', actionHref: '#dashboard',
    }));
    nodes = [item];
  } else {
    nodes = books.slice(0, 4).map((book) => bookCard(book, 'h3'));
  }
  elements.recentCards.replaceChildren(...nodes);
}

/* ---------- Katalog ---------- */

function clearCatalogFilters() {
  elements.catSearch.value = '';
  elements.catFilter.value = '';
}

function renderCatalog() {
  const filtered = filterBooks(elements.catSearch, elements.catFilter);
  elements.catCount.textContent = countText(filtered, elements.catSearch, elements.catFilter);
  elements.catGrid.setAttribute('aria-busy', String(loadState === 'loading'));

  if (loadState === 'loading') {
    elements.catGrid.replaceChildren(...skeletonCards(6));
    return;
  }
  if (loadState === 'error') {
    const item = el('li', 'cards-note');
    item.appendChild(stateBox({
      tone: 'error', iconName: 'alert', title: 'Koleksi belum bisa dimuat',
      text: 'Pastikan semua layanan berjalan (docker compose ps), lalu coba lagi.', detail: loadError,
      actionLabel: 'Coba lagi', onAction: () => loadBooks(),
    }));
    elements.catGrid.replaceChildren(item);
    return;
  }
  if (books.length === 0) {
    const item = el('li', 'cards-note');
    item.appendChild(stateBox({
      iconName: 'book', title: 'Belum ada buku di koleksi',
      text: 'Koleksi masih kosong. Buku ditambahkan dari halaman Dashboard.', actionLabel: 'Buka Dashboard', actionHref: '#dashboard',
    }));
    elements.catGrid.replaceChildren(item);
    return;
  }
  if (filtered.length === 0) {
    const query = elements.catSearch.value.trim();
    const category = elements.catFilter.value;
    const criteria = [];
    if (query) criteria.push(`kata “${query}”`);
    if (category) criteria.push(`kategori ${category}`);
    const item = el('li', 'cards-note');
    item.appendChild(stateBox({
      iconName: 'search', title: 'Buku tidak ditemukan',
      text: `Tidak ada buku dengan ${criteria.join(' dan ')}. Coba kata lain atau hapus filter.`,
      actionLabel: 'Hapus filter',
      onAction: () => { clearCatalogFilters(); renderCatalog(); elements.catSearch.focus(); },
    }));
    elements.catGrid.replaceChildren(item);
    return;
  }
  elements.catGrid.replaceChildren(...filtered.map((book) => bookCard(book, 'h2')));
}

/* ---------- Dashboard: tabel ---------- */

function cell(className, label) {
  const td = el('td', className);
  td.setAttribute('role', 'cell');
  if (label) td.dataset.label = label;
  return td;
}

function actionButton(className, label, iconName, ariaLabel, onClick) {
  const button = el('button', className);
  button.type = 'button';
  button.append(icon(iconName), el('span', '', label));
  button.setAttribute('aria-label', ariaLabel);
  button.addEventListener('click', onClick);
  return button;
}

function buildRow(book) {
  const row = el('tr');
  row.setAttribute('role', 'row');
  row.dataset.id = String(book.id);
  if (String(book.id) === changedId) row.classList.add('is-changed');

  const titleCell = cell('col-title');
  titleCell.append(el('p', 'book-title', book.title), el('span', 'book-author', book.author));

  const categoryCell = cell('col-category');
  categoryCell.appendChild(el('span', 'tag', book.category));

  const yearCell = cell('col-year', 'Tahun');
  yearCell.textContent = String(book.year);

  const stockCell = cell('col-stock', 'Stok');
  if (book.stock === 0) stockCell.appendChild(el('span', 'stock-out', 'Habis'));
  else stockCell.textContent = stockText(book);

  const actionCell = cell('col-actions');
  const actions = el('div', 'row-actions');
  const edit = actionButton('btn btn-secondary btn-sm', 'Edit', 'edit', `Edit buku ${book.title}`, (event) => startEditing(book, event.currentTarget));
  edit.dataset.editId = String(book.id);
  const remove = actionButton('btn btn-danger-outline btn-sm', 'Hapus', 'trash', `Hapus buku ${book.title}`, (event) => askDelete(book, event.currentTarget));
  remove.dataset.deleteId = String(book.id);
  actions.append(edit, remove);
  actionCell.appendChild(actions);

  row.append(titleCell, categoryCell, yearCell, stockCell, actionCell);
  return row;
}

function stateRow(options) {
  const row = el('tr', 'state-row');
  row.setAttribute('role', 'row');
  const td = cell('');
  td.colSpan = 5;
  td.appendChild(stateBox(options));
  row.appendChild(td);
  return row;
}

function skeletonRows(count = 4) {
  return Array.from({ length: count }, () => {
    const row = el('tr', 'skeleton-row');
    row.setAttribute('aria-hidden', 'true');
    const td = el('td');
    td.colSpan = 5;
    td.append(el('span', 'sk sk-a'), el('span', 'sk sk-b'));
    row.appendChild(td);
    return row;
  });
}

function clearDashFilters() {
  elements.dashSearch.value = '';
  elements.dashFilter.value = '';
}

function renderDashboard() {
  const filtered = filterBooks(elements.dashSearch, elements.dashFilter);
  elements.dashCount.textContent = countText(filtered, elements.dashSearch, elements.dashFilter);
  elements.list.setAttribute('aria-busy', String(loadState === 'loading'));
  elements.table.replaceChildren();

  if (loadState === 'loading') {
    elements.table.append(...skeletonRows());
    return;
  }
  if (loadState === 'error') {
    elements.table.appendChild(stateRow({
      tone: 'error', iconName: 'alert', title: 'Daftar buku belum bisa dimuat',
      text: 'Pastikan semua layanan berjalan (docker compose ps), lalu coba lagi.', detail: loadError,
      actionLabel: 'Coba lagi', onAction: () => loadBooks(),
    }));
    return;
  }
  if (books.length === 0) {
    elements.table.appendChild(stateRow({
      iconName: 'book', title: 'Belum ada buku di koleksi',
      text: 'Tambahkan buku pertama lewat tombol Tambah buku. Datanya langsung tersimpan di PostgreSQL.',
      actionLabel: 'Tambah buku pertama', onAction: (event) => openNewBook(event.currentTarget),
    }));
    return;
  }
  if (filtered.length === 0) {
    const query = elements.dashSearch.value.trim();
    const category = elements.dashFilter.value;
    const criteria = [];
    if (query) criteria.push(`kata “${query}”`);
    if (category) criteria.push(`kategori ${category}`);
    elements.table.appendChild(stateRow({
      iconName: 'search', title: 'Tidak ada buku yang cocok',
      text: `Tidak ada buku dengan ${criteria.join(' dan ')}.`,
      actionLabel: 'Hapus filter',
      onAction: () => { clearDashFilters(); renderDashboard(); elements.dashSearch.focus(); },
    }));
    return;
  }
  filtered.forEach((book) => elements.table.appendChild(buildRow(book)));
}

// Setelah simpan: pastikan baris yang berubah terlihat, walau filter lama tidak lagi cocok.
function revealChanged() {
  if (changedId === null) return;
  let row = elements.table.querySelector(`tr[data-id="${changedId}"]`);
  if (!row && hasFilter(elements.dashSearch, elements.dashFilter)) {
    clearDashFilters();
    renderDashboard();
    row = elements.table.querySelector(`tr[data-id="${changedId}"]`);
  }
  if (!row) {
    changedId = null;
    return;
  }
  if (route === 'dashboard') row.scrollIntoView({ block: 'nearest', behavior: reducedMotion.matches ? 'auto' : 'smooth' });
  const revealedId = changedId;
  clearTimeout(changedTimeout);
  changedTimeout = setTimeout(() => {
    // Jangan hapus penanda milik perubahan yang lebih baru.
    if (changedId === revealedId) changedId = null;
    row.classList.remove('is-changed');
  }, 2600);
}

function renderAll() {
  renderStats();
  renderShelf();
  renderRecent();
  renderCatalog();
  renderDashboard();
}

async function loadBooks() {
  const seq = ++loadSeq;
  const requestMode = mode;
  if (loadController) loadController.abort();
  loadController = new AbortController();
  const { signal } = loadController;
  if (loadState === 'error') {
    loadState = 'loading';
    renderAll();
  }
  elements.refresh.disabled = true;
  elements.refreshLabel.textContent = 'Memuat...';
  try {
    const result = await api(booksUrl(), { signal });
    if (seq !== loadSeq || requestMode !== mode) return;
    books = result.data;
    syncCategoryFilters();
    loadState = 'ready';
    loadError = '';
    setStatus('ready', `${MODES[requestMode].engine} terhubung`);
  } catch (error) {
    if (seq !== loadSeq || requestMode !== mode) return;
    loadError = error.message;
    loadState = books.length > 0 ? 'ready' : 'error';
    setStatus('error', statusFromError(error));
    if (books.length > 0) showToast(`Gagal memperbarui daftar. ${error.message}`, 'error');
  } finally {
    if (seq === loadSeq) {
      elements.refresh.disabled = false;
      elements.refreshLabel.textContent = 'Muat ulang';
    }
  }
  renderAll();
  revealChanged();
}

/* ---------- Formulir: tambah & edit (dialog di Dashboard) ---------- */

function setFieldError(name, message) {
  const input = elements.form.elements[name];
  const error = $(`${name}-error`);
  if (message) {
    input.setAttribute('aria-invalid', 'true');
    error.textContent = message;
    error.hidden = false;
  } else {
    input.removeAttribute('aria-invalid');
    error.textContent = '';
    error.hidden = true;
  }
}

function clearFieldErrors() {
  FIELDS.forEach((name) => setFieldError(name, ''));
  elements.formError.textContent = '';
  elements.formError.hidden = true;
}

function showFieldErrors(errors) {
  clearFieldErrors();
  const invalid = FIELDS.filter((name) => errors[name]);
  invalid.forEach((name) => setFieldError(name, errors[name]));
  if (invalid.length > 0) elements.form.elements[invalid[0]].focus();
  return invalid.length > 0;
}

function validateBook(values) {
  const errors = {};
  const { year, stock } = elements.form.elements;

  if (!values.title) errors.title = 'Judul buku wajib diisi.';
  else if (values.title.length > 150) errors.title = 'Judul maksimal 150 karakter.';

  if (!values.author) errors.author = 'Nama penulis wajib diisi.';
  else if (values.author.length > 100) errors.author = 'Nama penulis maksimal 100 karakter.';

  if (!values.category) errors.category = 'Pilih salah satu kategori.';

  const yearNumber = Number(values.year);
  if (year.validity.badInput) errors.year = 'Tahun harus berupa angka bulat.';
  else if (values.year === '') errors.year = 'Tahun terbit wajib diisi.';
  else if (!Number.isInteger(yearNumber) || yearNumber < 1900 || yearNumber > MAX_YEAR) {
    errors.year = `Tahun harus angka bulat antara 1900 dan ${MAX_YEAR}.`;
  }

  const stockNumber = Number(values.stock);
  if (stock.validity.badInput) errors.stock = 'Stok harus berupa angka bulat.';
  else if (values.stock === '') errors.stock = 'Stok wajib diisi.';
  else if (!Number.isInteger(stockNumber) || stockNumber < 0 || stockNumber > 1000000) {
    errors.stock = 'Stok harus angka bulat antara 0 dan 1.000.000.';
  }
  return errors;
}

// Kategori yang dibuat lewat API (mis. Postman) bisa di luar daftar dropdown.
// Tanpa opsi tambahan, <select> menjadi kosong dan buku itu tidak bisa disimpan saat diedit.
function syncCategoryOptions(selected) {
  const select = elements.form.elements.category;
  select.querySelectorAll('option[data-extra]').forEach((option) => option.remove());
  if (selected && ![...select.options].some((option) => option.value === selected)) {
    const option = new Option(selected, selected);
    option.dataset.extra = 'true';
    select.appendChild(option);
  }
}

function submitLabel() {
  return editingId !== null ? 'Simpan perubahan' : 'Simpan buku';
}

function resetForm() {
  editingId = null;
  clearFieldErrors();
  syncCategoryOptions('');
  elements.form.reset();
  elements.formTitle.textContent = 'Tambah buku';
  elements.formHint.textContent = `Semua kolom wajib diisi. Disimpan ke ${modeInfo().engine}.`;
  elements.submit.textContent = submitLabel();
  elements.formDialog.dataset.mode = 'add';
}

function openFormDialog(trigger) {
  formTrigger = trigger || null;
  if (typeof elements.formDialog.showModal === 'function') elements.formDialog.showModal();
  else elements.formDialog.setAttribute('open', '');
  elements.form.elements.title.focus();
}

function closeFormDialog() {
  if (elements.formDialog.open) elements.formDialog.close();
}

function openNewBook(trigger) {
  resetForm();
  openFormDialog(trigger);
}

function startEditing(book, trigger) {
  resetForm();
  editingId = String(book.id);
  syncCategoryOptions(book.category);
  FIELDS.forEach((name) => { elements.form.elements[name].value = book[name]; });
  elements.formTitle.textContent = 'Edit buku';
  elements.formHint.textContent = `Mengubah buku ${modeInfo().kind === 'SQL' ? 'nomor' : 'dengan id'} ${book.id} di ${modeInfo().engine}. Simpan perubahan atau batalkan.`;
  elements.submit.textContent = submitLabel();
  elements.formDialog.dataset.mode = 'edit';
  openFormDialog(trigger);
}

function setSaving(isSaving) {
  saving = isSaving;
  elements.submit.disabled = isSaving;
  elements.cancel.disabled = isSaving;
  elements.submit.textContent = isSaving ? 'Menyimpan...' : submitLabel();
  elements.form.setAttribute('aria-busy', String(isSaving));
}

elements.form.addEventListener('submit', async (event) => {
  event.preventDefault();
  if (saving) return;

  const values = {
    title: elements.form.elements.title.value.trim(),
    author: elements.form.elements.author.value.trim(),
    category: elements.form.elements.category.value,
    year: elements.form.elements.year.value.trim(),
    stock: elements.form.elements.stock.value.trim(),
  };
  if (showFieldErrors(validateBook(values))) return;

  const payload = { ...values, year: Number(values.year), stock: Number(values.stock) };
  const wasEditing = editingId !== null;
  const requestMode = mode;
  const targetId = editingId;
  setSaving(true);
  try {
    const result = await api(wasEditing ? `${MODES[requestMode].base}/books/${targetId}` : `${MODES[requestMode].base}/books`, {
      method: wasEditing ? 'PUT' : 'POST',
      body: JSON.stringify(payload),
    });
    if (requestMode !== mode) {
      showToast(`Perubahan disimpan di ${MODES[requestMode].engine}, tetapi mode sudah berganti.`);
      return;
    }
    clearTimeout(changedTimeout);
    changedId = String(result.data.id);
    closeFormDialog();
    showToast(wasEditing ? `Perubahan buku “${result.data.title}” disimpan di ${modeInfo().engine}.` : `Buku “${result.data.title}” ditambahkan ke ${modeInfo().engine}.`);
    await loadBooks();
  } catch (error) {
    if (requestMode !== mode) return;
    if (error.details) showFieldErrors(error.details);
    elements.formError.textContent = error.message;
    elements.formError.hidden = false;
    if (wasEditing && error.status === 404) {
      closeFormDialog();
      showToast('Buku ini sudah tidak ada di database. Daftar diperbarui.', 'error');
      await loadBooks();
    }
  } finally {
    setSaving(false);
  }
});

FIELDS.forEach((name) => {
  elements.form.elements[name].addEventListener('input', () => setFieldError(name, ''));
});

elements.cancel.addEventListener('click', closeFormDialog);
elements.closeForm.addEventListener('click', () => { if (!saving) closeFormDialog(); });
elements.formDialog.addEventListener('cancel', (event) => { if (saving) event.preventDefault(); });
elements.formDialog.addEventListener('close', () => {
  resetForm();
  const trigger = formTrigger;
  formTrigger = null;
  if (trigger && trigger.isConnected) trigger.focus();
  else if (route === 'dashboard') $('dashTitle').focus({ preventScroll: true });
});
// Klik pada latar gelap menutup dialog, tetapi hanya jika tombol mouse ditekan dan dilepas di latar.
let pressedOnBackdrop = false;
elements.formDialog.addEventListener('mousedown', (event) => { pressedOnBackdrop = event.target === elements.formDialog; });
elements.formDialog.addEventListener('click', (event) => {
  if (event.target === elements.formDialog && pressedOnBackdrop && !saving) closeFormDialog();
});

/* ---------- Hapus buku ---------- */

function closeDialog() {
  if (elements.dialog.open) elements.dialog.close();
}

async function runDelete(book) {
  if (deleting) return;
  deleting = true;
  const requestMode = mode;
  elements.confirmDelete.disabled = true;
  elements.confirmCancel.disabled = true;
  elements.confirmDelete.textContent = 'Menghapus...';
  try {
    await api(`${MODES[requestMode].base}/books/${book.id}`, { method: 'DELETE' });
    closeDialog();
    if (requestMode !== mode) {
      showToast(`Buku dihapus dari ${MODES[requestMode].engine}, tetapi mode sudah berganti.`);
      return;
    }
    showToast(`Buku “${book.title}” dihapus dari ${modeInfo().engine}.`);
    await loadBooks();
    $('dashTitle').focus({ preventScroll: true });
  } catch (error) {
    if (error.status === 404) {
      closeDialog();
      showToast('Buku ini sudah tidak ada di database. Daftar diperbarui.', 'error');
      await loadBooks();
    } else if (elements.dialog.open) {
      elements.confirmError.textContent = error.message;
      elements.confirmError.hidden = false;
      showToast(error.message, 'error');
    } else {
      showToast(error.message, 'error');
    }
  } finally {
    deleting = false;
    elements.confirmDelete.disabled = false;
    elements.confirmCancel.disabled = false;
    elements.confirmDelete.textContent = 'Hapus buku';
  }
}

function askDelete(book) {
  if (typeof elements.dialog.showModal !== 'function') {
    if (window.confirm(`Hapus buku “${book.title}”?\nTindakan ini tidak bisa dibatalkan.`)) runDelete(book);
    return;
  }
  elements.confirmBook.textContent = book.title;
  elements.confirmDb.textContent = `${modeInfo().engine} (${modeInfo().kind})`;
  elements.confirmError.textContent = '';
  elements.confirmError.hidden = true;
  elements.confirmDelete.onclick = () => runDelete(book);
  elements.dialog.showModal();
}

elements.confirmCancel.addEventListener('click', closeDialog);
elements.dialog.addEventListener('cancel', (event) => {
  if (deleting) event.preventDefault();
});
elements.dialog.addEventListener('click', (event) => {
  if (event.target === elements.dialog && !deleting) closeDialog();
});

/* ---------- Event lain & awal ---------- */

elements.newBook.addEventListener('click', (event) => openNewBook(event.currentTarget));
elements.refresh.addEventListener('click', () => {
  loadBooks();
  checkHealth();
});
elements.catSearch.addEventListener('input', renderCatalog);
elements.catFilter.addEventListener('change', renderCatalog);
elements.dashSearch.addEventListener('input', renderDashboard);
elements.dashFilter.addEventListener('change', renderDashboard);

/* ---------- Perbandingan: data nyata dari kedua database ---------- */

const compareIds = {
  sql: { status: 'cmpSqlStatus', total: 'cmpSqlTotal', sample: 'cmpSqlSample' },
  nosql: { status: 'cmpNosqlStatus', total: 'cmpNosqlTotal', sample: 'cmpNosqlSample' },
};
let comparing = false;

async function refreshOne(key) {
  const ids = compareIds[key];
  $(ids.status).textContent = 'Memeriksa...';
  try {
    await api(`${MODES[key].base}/health`);
    const list = await api(`${MODES[key].base}/books`);
    $(ids.status).textContent = 'Terhubung';
    $(ids.total).textContent = numberFormat.format(list.total);
    $(ids.sample).textContent = list.data.length ? JSON.stringify(list.data[0], null, 2) : 'Belum ada buku di database ini.';
  } catch (error) {
    $(ids.status).textContent = `Tidak tersedia: ${error.message}`;
    $(ids.total).textContent = '—';
    $(ids.sample).textContent = '—';
  }
}

async function refreshComparison() {
  if (comparing) return;
  comparing = true;
  $('cmpRefresh').disabled = true;
  try {
    await Promise.all([refreshOne('sql'), refreshOne('nosql')]);
  } finally {
    comparing = false;
    $('cmpRefresh').disabled = false;
  }
}

function median(values) {
  const sorted = [...values].sort((a, b) => a - b);
  const mid = Math.floor(sorted.length / 2);
  return sorted.length % 2 ? sorted[mid] : (sorted[mid - 1] + sorted[mid]) / 2;
}

let measuring = false;
async function measureLatency() {
  if (measuring) return;
  measuring = true;
  const button = $('cmpMeasure');
  button.disabled = true;
  const body = $('cmpPerfBody');
  const rows = [];
  try {
    for (const key of ['sql', 'nosql']) {
      button.textContent = `Mengukur ${MODES[key].engine}...`;
      const samples = [];
      let failed = '';
      try {
        await api(`${MODES[key].base}/books`); // pemanasan, tidak dihitung
        for (let i = 0; i < 10; i += 1) {
          const start = performance.now();
          await api(`${MODES[key].base}/books`);
          samples.push(performance.now() - start);
        }
      } catch (error) {
        failed = error.message;
      }
      const row = el('tr');
      row.appendChild(el('th', '', `${MODES[key].kind}: ${MODES[key].engine}`));
      row.lastChild.scope = 'row';
      if (failed) {
        const cellNode = el('td', '', `Gagal: ${failed}`);
        cellNode.colSpan = 4;
        row.appendChild(cellNode);
      } else {
        const fmt = (value) => `${value.toFixed(1)} ms`;
        row.append(el('td', '', fmt(median(samples))), el('td', '', fmt(Math.min(...samples))), el('td', '', fmt(Math.max(...samples))), el('td', '', String(samples.length)));
      }
      rows.push(row);
    }
    body.replaceChildren(...rows);
  } finally {
    measuring = false;
    button.disabled = false;
    button.textContent = 'Ukur lagi';
  }
}

$('cmpRefresh').addEventListener('click', refreshComparison);
$('cmpMeasure').addEventListener('click', measureLatency);

/* ---------- Ganti mode database ---------- */

function renderModeUi() {
  const info = modeInfo();
  document.body.dataset.mode = mode;
  elements.modeRadios.forEach((radio) => { radio.checked = radio.value === mode; });
  elements.modeLabels.forEach((node) => {
    const key = node.dataset.modeText;
    node.textContent = key === 'engine' ? info.engine : key === 'kind' ? info.kind : key === 'endpoint' ? `${info.base}/books` : key === 'idnote' ? info.idNote : key === 'source' ? info.source : '';
  });
  if (elements.homeSource) elements.homeSource.textContent = info.source;
  elements.newBook.querySelector('span').textContent = `Tambah buku ke ${info.engine}`;
}

function setMode(next) {
  if (next === mode || !MODES[next]) return;
  if (saving || deleting) {
    renderModeUi(); // kembalikan pilihan: ada permintaan tulis yang masih berjalan
    showToast('Tunggu penyimpanan atau penghapusan selesai sebelum mengganti database.', 'error');
    return;
  }
  if (elements.formDialog.open) elements.formDialog.close();
  if (loadController) loadController.abort();
  loadSeq += 1; // respons mode lama diabaikan
  mode = next;
  try { window.sessionStorage.setItem('libraryku-mode', mode); } catch (error) { /* mode tetap berlaku untuk sesi ini */ }
  books = [];
  loadState = 'loading';
  loadError = '';
  changedId = null;
  editingId = null;
  clearTimeout(changedTimeout);
  clearCatalogFilters();
  clearDashFilters();
  syncCategoryFilters();
  setStatus('checking', `Memeriksa ${modeInfo().engine}...`);
  renderModeUi();
  resetForm();
  renderAll();
  loadBooks();
  checkHealth();
  showToast(`Mode database: ${modeInfo().engine} (${modeInfo().kind}).`);
}

elements.modeRadios.forEach((radio) => {
  radio.addEventListener('change', () => { if (radio.checked) setMode(radio.value); });
});

document.addEventListener('visibilitychange', () => {
  if (document.visibilityState === 'visible') checkHealth();
});
setInterval(() => {
  if (document.visibilityState === 'visible') checkHealth();
}, 30000);

elements.address.textContent = window.location.host || 'localhost';
elements.form.elements.year.max = String(MAX_YEAR);
$('year-hint').textContent = `1900 sampai ${MAX_YEAR}`;
route = routeFromHash() || 'beranda';
applyRoute({ moveFocus: false });
renderModeUi();
resetForm();
renderAll();
loadBooks();
checkHealth();
