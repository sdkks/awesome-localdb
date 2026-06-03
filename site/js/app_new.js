/* ===================================================================
   Awesome Local DB — Catalog App
   Zero-dependency vanilla ES module. Reads index.json and
   filter-options.json, renders a faceted database catalog.
   =================================================================== */

// ── Application state ─────────────────────────────────────────────────
const state = {
  databases: [],
  filterOptions: null,
  activeFilters: {},       // { type: [values] }  e.g. { category: ['relational'] }
  searchQuery: '',
  status: 'loading',       // 'loading' | 'ready' | 'error' | 'empty'
  errorMessage: '',

  // Decision tree
  treeData: null,          // loaded decision-tree.json
  treeStep: 0,             // current step index (0-based)
  treeFilters: {},         // { type: [values] } accumulated from tree choices
  treeSelections: [],      // [{ stepIdx, filters }] for back-tracking
  view: 'browse',          // 'browse' | 'tree' | 'compare'
  treeSourceFilters: new Set(), // keys like 'category:relational' from tree

  // Comparison
  compareSelection: [],    // array of db slugs (max 4)
};

// Debounce timer for search
let searchTimer = null;

// ── DOM helpers ───────────────────────────────────────────────────────
function $(selector, parent = document) {
  return parent.querySelector(selector);
}

function $$(selector, parent = document) {
  return Array.from(parent.querySelectorAll(selector));
}

function clear(el) {
  el.replaceChildren();
}

function html(strings, ...values) {
  let result = '';
  for (let i = 0; i < strings.length; i++) {
    result += strings[i];
    if (i < values.length) {
      let v = values[i];
      if (v === null || v === undefined) v = '';
      if (Array.isArray(v)) v = v.join('');
      result += String(v);
    }
  }
  return result;
}

function formatStars(n) {
  if (n >= 1000) return (n / 1000).toFixed(1) + 'k';
  return String(n);
}

function truncate(str, maxLen) {
  if (str.length <= maxLen) return str;
  return str.slice(0, maxLen).replace(/\s+\S*$/, '') + '…';
}

function escapeHtml(str) {
  const div = document.createElement('div');
  div.appendChild(document.createTextNode(str));
  return div.innerHTML;
}

// ── Tag subcategory groups ────────────────────────────────────────────
const TAG_GROUPS = {
  'Storage':      ['single-file', 'multi-file', 'in-memory', 'persistent', 'blob-storage'],
  'Interface':    ['sql-interface', 'schemaless', 'schemaful', 'json-native'],
  'Platform':     ['mobile', 'desktop', 'cli', 'browser', 'WASM', 'edge', 'iot', 'serverless'],
  'Architecture': ['embedded-only', 'also-server', 'cloud-native', 'copy-on-write', 'append-only', 'columnar', 'row-based'],
  'Workload':     ['concurrent-readers', 'single-writer', 'multi-writer', 'compression', 'encryption'],
  'Features':     ['ai-ml', 'rag', 'full-text-search', 'spatial', 'geospatial', 'time-travel', 'reactive', 'offline-first', 'replication', 'sync', 'horizontal-scale', 'data-pipeline'],
};

function getTagCounts(tagNames, activeFilters) {
  // Count databases matching all active filters EXCEPT tags
  let base = state.databases;
  for (const [type, values] of Object.entries(activeFilters)) {
    if (type === 'tags' || !values || values.length === 0) continue;
    base = base.filter(db => {
      if (type === 'category') {
        return values.some(v => db.category === v || (db.categories && db.categories.includes(v)));
      }
      if (type === 'language') {
        return values.some(v => db.languages && db.languages.some(l => l.name === v));
      }
      if (type === 'license') {
        return values.includes(db.license);
      }
      if (type === 'status') {
        return values.includes(db.maintenance_status);
      }
      return true;
    });
  }
  const counts = {};
  for (const tag of tagNames) {
    counts[tag] = base.filter(db => db.tags && db.tags.includes(tag)).length;
  }
  return counts;
}

// ── URL hash helpers ──────────────────────────────────────────────────
// Hash format: #cat=relational,olap&lang=Python&lic=MIT&status=active&q=search+term&view=tree
const HASH_KEY_MAP = { category: 'cat', language: 'lang', license: 'lic', status: 'status' };
const HASH_KEY_REV = { cat: 'category', lang: 'language', lic: 'license', status: 'status' };

function parseHash() {
  const raw = window.location.hash.replace(/^#/, '');
  if (!raw) return { filters: {}, searchQuery: '', view: 'browse' };

  const result = { filters: {}, searchQuery: '', view: 'browse' };

  for (const part of raw.split('&')) {
    const eq = part.indexOf('=');
    if (eq === -1) continue;
    const shortKey = decodeURIComponent(part.slice(0, eq));
    const rawVal = decodeURIComponent(part.slice(eq + 1));

    if (shortKey === 'q') {
      result.searchQuery = rawVal;
    } else if (shortKey === 'view') {
      result.view = rawVal;
    } else {
      const fullKey = HASH_KEY_REV[shortKey] || shortKey;
      const values = rawVal.split(',').filter(v => v.length > 0);
      if (values.length > 0) {
        result.filters[fullKey] = values;
      }
    }
  }

  return result;
}

function writeHash(filters, searchQuery, view) {
  const parts = [];
  for (const [type, values] of Object.entries(filters)) {
    if (!values || values.length === 0) continue;
    const shortKey = HASH_KEY_MAP[type] || type;
    const joined = values.map(v => encodeURIComponent(v)).join(',');
    if (joined) parts.push(shortKey + '=' + joined);
  }
  if (searchQuery && searchQuery.trim()) {
    parts.push('q=' + encodeURIComponent(searchQuery.trim()));
  }
  if (view && view !== 'browse') {
    parts.push('view=' + encodeURIComponent(view));
  }
  const newHash = parts.length ? '#' + parts.join('&') : '';
  if (window.location.hash !== newHash) {
    history.replaceState(null, '', newHash || window.location.pathname);
  }
}

function updateHash() {
  writeHash(state.activeFilters, state.searchQuery, state.view);
}

// ── Filtering logic ───────────────────────────────────────────────────
function applyFilters() {
  let results = state.databases;

  // Text search against _search_tokens
  if (state.searchQuery.trim()) {
    const q = state.searchQuery.trim().toLowerCase();
    results = results.filter(db => {
      if (!db._search_tokens) return false;
      return db._search_tokens.some(token => token.includes(q));
    });
  }

  // AND logic across filter types, OR within a type
  for (const [type, values] of Object.entries(state.activeFilters)) {
    if (!values || values.length === 0) continue;
    results = results.filter(db => {
      if (type === 'category') {
        return values.some(v => db.category === v || (db.categories && db.categories.includes(v)));
      }
      if (type === 'language') {
        return values.some(v => db.languages && db.languages.some(l => l.name === v));
      }
      if (type === 'license') {
        return values.includes(db.license);
      }
      if (type === 'status') {
        return values.includes(db.maintenance_status);
      }
      if (type === 'tags') {
        return values.some(v => db.tags && db.tags.includes(v));
      }
      return true;
    });
  }

  return results;
}

// ── Render functions ──────────────────────────────────────────────────
function renderLoading() {
  const root = document.getElementById('app-root');
  root.innerHTML = html`
    <div class="loading-state" role="status" aria-label="Loading catalog">
      <div class="spinner" aria-hidden="true"></div>
      <p>Loading catalog&hellip;</p>
    </div>
  `;
}

function renderError(message) {
  const root = document.getElementById('app-root');
  root.innerHTML = html`
    <div class="error-state" role="alert">
      <h2>Something went wrong</h2>
      <p>` + escapeHtml(message || 'Failed to load the database catalog.') + `</p>
      <button class="btn" onclick="location.reload()">Try again</button>
    </div>
  `;
}

function renderEmpty() {
  const root = document.getElementById('app-root');
  root.innerHTML = html`
    <div class="empty-state">
      <h2>No databases found</h2>
      <p>There are no databases in the catalog yet.</p>
      <p>Check back soon, or contribute at GitHub.</p>
    </div>
  `;
}

function renderNoResults() {
  return html`
    <div class="empty-state">
      <h2>No databases match your filters</h2>
      <p>Try adjusting or clearing your filters to see more results.</p>
      <button class="btn" id="clear-filters-action">Clear all filters</button>
    </div>
  `;
}

function renderCategoryBadge(category) {
  const label = category.replace('-', ' ');
  return html`<span class="cat-badge cat-` + escapeHtml(category) + `">` + escapeHtml(label) + `</span>`;
}

function renderCards(databases) {
  if (databases.length === 0) {
    return renderNoResults();
  }

  const cards = databases.map(db => {
    const langTags = (db.languages || [])
      .slice(0, 4)
      .map(l => html`<span class="lang-tag">` + escapeHtml(l.name) + `</span>`)
      .join('');

    const repoUrl = db.repository_url || 'https://github.com/' + (db._repo_path || '');
    const examplesUrl = db._repo_path
      ? 'https://github.com/sdkks/awesome-localdb/blob/main/' + db._repo_path + '/README.md'
      : null;

    const isSelected = state.compareSelection.includes(db.slug);
    const isDisabled = !isSelected && state.compareSelection.length >= 4;

    return html`
      <article class="db-card" tabindex="0">
        <div class="db-card-header">
          <h3 class="db-card-name">
            <a href="` + escapeHtml(repoUrl) + `" target="_blank" rel="noopener">
              ` + escapeHtml(db.name) + `
            </a>
          </h3>
          <div class="db-card-header-actions">
            <button class="compare-toggle` + (isSelected ? ' selected' : '') + `"
                    data-compare-slug="` + escapeHtml(db.slug) + `"
                    aria-label="` + (isSelected ? 'Remove from comparison' : 'Add to comparison') + `"
                    title="` + (isDisabled ? 'Max 4 databases can be compared' : (isSelected ? 'Remove from comparison' : 'Add to comparison')) + `"
                    ` + (isDisabled ? 'disabled' : '') + `>
              <svg class="compare-icon" viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <line x1="18" y1="20" x2="18" y2="10"></line>
                <line x1="12" y1="20" x2="12" y2="4"></line>
                <line x1="6" y1="20" x2="6" y2="14"></line>
                <line x1="18" y1="5" x2="22" y2="10"></line>
                <line x1="18" y1="5" x2="14" y2="10"></line>
                <line x1="2" y1="20" x2="22" y2="20"></line>
              </svg>
            </button>
            ` + renderCategoryBadge(db.category) + `
          </div>
        </div>
        <p class="db-card-description">` + escapeHtml(truncate(db.description, 120)) + `</p>
        <div class="db-card-meta">
          ` + (langTags ? html`<span class="meta-item">` + langTags + `</span>` : '') + `
          ` + (db.license ? html`<span class="meta-item">` + escapeHtml(db.license) + `</span>` : '') + `
          ` + (db.github_stars ? html`<span class="meta-item stars" title="~` + db.github_stars + ` GitHub stars">&star; ` + formatStars(db.github_stars) + `</span>` : '') + `
        </div>
        ` + (examplesUrl ? html`
          <a class="db-card-examples" href="` + escapeHtml(examplesUrl) + `" target="_blank" rel="noopener">
            Code examples &rarr;
          </a>` : '') + `
      </article>
    `;
  }).join('');

  return html`<div class="card-grid">` + cards + `</div>`;
}

function renderFilters() {
  if (!state.filterOptions) return '';

  const sections = [];

  // Categories
  if (state.filterOptions.categories && state.filterOptions.categories.length > 0) {
    const chips = state.filterOptions.categories.filter(c => c).map(cat => {
      const active = (state.activeFilters.category || []).includes(cat);
      return html`
        <button class="filter-chip` + (active ? ' active' : '') + `"
                data-filter-type="category"
                data-filter-value="` + escapeHtml(cat) + `"
                aria-pressed="` + (active ? 'true' : 'false') + `">
          ` + escapeHtml(cat.replace('-', ' ')) + `
        </button>
      `;
    }).join('');

    sections.push(html`
      <div class="filter-group">
        <h3 id="filter-group-label-category">Category</h3>
        <div class="filter-chips" role="group" aria-labelledby="filter-group-label-category">` + chips + `</div>
      </div>
    `);
  }

  // Languages (show up to 12)
  if (state.filterOptions.languages && state.filterOptions.languages.length > 0) {
    const visible = state.filterOptions.languages.filter(l => l).slice(0, 12);
    const chips = visible.map(lang => {
      const active = (state.activeFilters.language || []).includes(lang);
      return html`
        <button class="filter-chip` + (active ? ' active' : '') + `"
                data-filter-type="language"
                data-filter-value="` + escapeHtml(lang) + `"
                aria-pressed="` + (active ? 'true' : 'false') + `">
          ` + escapeHtml(lang) + `
        </button>
      `;
    }).join('');

    if (chips) {
      sections.push(html`
        <div class="filter-group">
          <h3 id="filter-group-label-language">Language</h3>
          <div class="filter-chips" role="group" aria-labelledby="filter-group-label-language">` + chips + `</div>
        </div>
      `);
    }
  }

  // Licenses
  if (state.filterOptions.licenses && state.filterOptions.licenses.length > 0) {
    const chips = state.filterOptions.licenses.filter(l => l).map(lic => {
      const active = (state.activeFilters.license || []).includes(lic);
      return html`
        <button class="filter-chip` + (active ? ' active' : '') + `"
                data-filter-type="license"
                data-filter-value="` + escapeHtml(lic) + `"
                aria-pressed="` + (active ? 'true' : 'false') + `">
          ` + escapeHtml(lic) + `
        </button>
      `;
    }).join('');

    if (chips) {
      sections.push(html`
        <div class="filter-group">
          <h3 id="filter-group-label-license">License</h3>
          <div class="filter-chips" role="group" aria-labelledby="filter-group-label-license">` + chips + `</div>
        </div>
      `);
    }
  }

  // Statuses
  if (state.filterOptions.statuses && state.filterOptions.statuses.length > 0) {
    const chips = state.filterOptions.statuses.filter(s => s).map(status => {
      const active = (state.activeFilters.status || []).includes(status);
      return html`
        <button class="filter-chip` + (active ? ' active' : '') + `"
                data-filter-type="status"
                data-filter-value="` + escapeHtml(status) + `"
                aria-pressed="` + (active ? 'true' : 'false') + `">
          ` + escapeHtml(status) + `
        </button>
      `;
    }).join('');

    if (chips) {
      sections.push(html`
        <div class="filter-group">
          <h3 id="filter-group-label-status">Status</h3>
          <div class="filter-chips" role="group" aria-labelledby="filter-group-label-status">` + chips + `</div>
        </div>
      `);
    }
  }

  // Tags accordion (collapsed by default)
  const allTagNames = (state.filterOptions.tags || []).filter(t => t);
  if (allTagNames.length > 0) {
    const tagCounts = getTagCounts(allTagNames, state.activeFilters);
    const hasActiveTags = (state.activeFilters.tags || []).length > 0;

    // Build subgroup sections for tags that exist in the data
    const subgroupSections = [];
    for (const [groupName, groupTags] of Object.entries(TAG_GROUPS)) {
      const existingTags = groupTags.filter(t => allTagNames.includes(t));
      if (existingTags.length === 0) continue;

      const chips = existingTags.map(tag => {
        const active = (state.activeFilters.tags || []).includes(tag);
        const count = tagCounts[tag] || 0;
        return html`
          <button class="filter-chip tag-chip` + (active ? ' active' : '') + `"
                  data-filter-type="tags"
                  data-filter-value="` + escapeHtml(tag) + `"
                  aria-pressed="` + (active ? 'true' : 'false') + `"
                  ` + (count === 0 && !active ? 'disabled' : '') + `>
            ` + escapeHtml(tag) + `
            <span class="tag-count">` + count + `</span>
          </button>
        `;
      }).join('');

      subgroupSections.push(html`
        <div class="tag-subgroup">
          <h4 class="tag-subgroup-label">` + escapeHtml(groupName) + `</h4>
          <div class="filter-chips" role="group" aria-label="` + escapeHtml(groupName) + ` tags">` + chips + `</div>
        </div>
      `);
    }

    sections.push(html`
      <details class="filter-accordion">
        <summary class="filter-accordion-summary">
          <span>Tags</span>
          ` + (hasActiveTags ? html`<span class="accordion-badge">` + state.activeFilters.tags.length + `</span>` : '') + `
          <span class="accordion-arrow" aria-hidden="true"></span>
        </summary>
        <div class="accordion-content">
          ` + subgroupSections.join('') + `
        </div>
      </details>
    `);
  }

  return sections.join('');
}

function renderActiveFilters() {
  const entries = Object.entries(state.activeFilters).filter(function(e) { return e[1].length > 0; });
  if (entries.length === 0) return '';

  const pills = entries.flatMap(function(entry) {
    const type = entry[0];
    const values = entry[1];
    return values.map(function(v) {
      const isTreeOrigin = state.treeSourceFilters.has(type + ':' + v);
      const typeLabel = type === 'tags' ? '' : type + ': ';
      return html`
        <span class="active-filter-pill filter-type-` + escapeHtml(type) + (isTreeOrigin ? ' tree-origin' : '') + `">
          ` + (isTreeOrigin ? html`<span class="tree-pill-icon" title="From decision tree">&#x1F332;</span>` : '') + `
          ` + escapeHtml(typeLabel + v) + `
          <button data-remove-filter="` + escapeHtml(type) + `"
                  data-remove-value="` + escapeHtml(v) + `"
                  aria-label="Remove filter: ` + escapeHtml(type) + ` ` + escapeHtml(v) + `">&times;</button>
        </span>
      `;
    });
  }).join('');

  return html`
    <div class="active-filters">
      <span class="label">Filters:</span>
      ` + pills + `
      <button class="clear-filters-btn" id="clear-filters-btn">Clear all</button>
    </div>
  `;
}

function renderApp() {
  const root = document.getElementById('app-root');

  // Tree view
  if (state.view === 'tree') {
    root.innerHTML = renderTreeView();
    wireTreeEvents();
    return;
  }

  // Compare view
  if (state.view === 'compare') {
    root.innerHTML = renderCompareView();
    wireCompareEvents();
    return;
  }

  // Browse view
  const filtered = applyFilters();
  const hasAnyFilters = Object.values(state.activeFilters).some(function(v) { return v.length > 0; }) || state.searchQuery.trim();

  const filterHtml = renderFilters();
  const activeFiltersHtml = renderActiveFilters();

  root.innerHTML = html`
    <div class="search-bar">
      <input type="search"
             id="search-input"
             placeholder="Search databases by name, description, tags…"
             value="` + escapeHtml(state.searchQuery) + `"
             aria-label="Search databases">
    </div>
    <div class="app-layout">
      <aside class="filter-sidebar" aria-label="Filter options">
        ` + filterHtml + `
      </aside>
      <div class="content-area">
        ` + activeFiltersHtml + `
        ` + (hasAnyFilters ? html`<p class="results-summary" aria-live="polite" role="status">` + filtered.length + ` database` + (filtered.length !== 1 ? 's' : '') + ` found</p>` : '') + `
        <div id="cards-container">
          ` + renderCards(filtered) + `
        </div>
      </div>
    </div>
  `;

  // Wire up events after render
  wireFilterEvents();
  wireSearchEvent();
  wireClearEvents();
  wireCardEvents();
  wireFilterChipKeyboard();
  wireCardKeyboard();
}

// ── Event wiring ──────────────────────────────────────────────────────
function wireFilterEvents() {
  $$('.filter-chip').forEach(function(chip) {
    chip.addEventListener('click', function() {
      const type = chip.dataset.filterType;
      const value = chip.dataset.filterValue;
      toggleFilter(type, value);
    });
  });
}

function wireSearchEvent() {
  const input = $('#search-input');
  if (!input) return;

  // Remove old listener by cloning (simple approach)
  const clone = input.cloneNode(true);
  input.parentNode.replaceChild(clone, input);

  clone.addEventListener('input', function(e) {
    const q = e.target.value;
    clearTimeout(searchTimer);
    searchTimer = setTimeout(function() {
      state.searchQuery = q;
      updateHash();
      renderApp();
    }, 300);
  });

  // Preserve cursor position by focusing the new input
  clone.focus();
  clone.setSelectionRange(clone.value.length, clone.value.length);
}

function wireClearEvents() {
  const clearBtn = $('#clear-filters-btn');
  if (clearBtn) {
    clearBtn.addEventListener('click', clearAllFilters);
  }

  const clearAction = $('#clear-filters-action');
  if (clearAction) {
    clearAction.addEventListener('click', clearAllFilters);
  }

  $$('.active-filter-pill button').forEach(function(btn) {
    btn.addEventListener('click', function(e) {
      e.stopPropagation();
      const type = btn.dataset.removeFilter;
      const value = btn.dataset.removeValue;
      removeFilter(type, value);
    });
  });
}

function wireCardEvents() {
  $$('.compare-toggle').forEach(function(btn) {
    btn.addEventListener('click', function(e) {
      e.stopPropagation();
      const slug = btn.dataset.compareSlug;
      toggleCompareDB(slug);
    });
  });
}

// ── Filter actions ────────────────────────────────────────────────────
function toggleFilter(type, value) {
  if (!state.activeFilters[type]) {
    state.activeFilters[type] = [];
  }
  const idx = state.activeFilters[type].indexOf(value);
  if (idx >= 0) {
    state.activeFilters[type].splice(idx, 1);
    if (state.activeFilters[type].length === 0) {
      delete state.activeFilters[type];
    }
  } else {
    state.activeFilters[type].push(value);
  }
  updateHash();
  renderApp();
}

function removeFilter(type, value) {
  if (!state.activeFilters[type]) return;
  const idx = state.activeFilters[type].indexOf(value);
  if (idx >= 0) {
    state.activeFilters[type].splice(idx, 1);
    if (state.activeFilters[type].length === 0) {
      delete state.activeFilters[type];
    }
    // Clear tree origin tracking for this filter
    state.treeSourceFilters.delete(type + ':' + value);
  }
  updateHash();
  renderApp();
}

function clearAllFilters() {
  state.activeFilters = {};
  state.searchQuery = '';
  state.treeSourceFilters.clear();
  updateHash();
  renderApp();
}

// ── Decision Tree ────────────────────────────────────────────────────
function loadDecisionTree() {
  return fetch('decision-tree.json')
    .then(function(res) {
      if (!res.ok) throw new Error('Failed to load decision tree (HTTP ' + res.status + ')');
      return res.json();
    })
    .then(function(data) {
      state.treeData = data;
    })
    .catch(function(err) {
      console.warn('Decision tree unavailable:', err.message);
      state.treeData = null;
    });
}

function applyTreeFilters() {
  // Apply accumulated tree filters against the full dataset to get live count
  let results = state.databases;
  for (const [type, values] of Object.entries(state.treeFilters)) {
    if (!values || values.length === 0) continue;
    results = results.filter(function(db) {
      if (type === 'category') {
        return values.some(function(v) { return db.category === v || (db.categories && db.categories.includes(v)); });
      }
      if (type === 'language') {
        return values.some(function(v) { return db.languages && db.languages.some(function(l) { return l.name === v; }); });
      }
      if (type === 'tags') {
        return values.some(function(v) { return db.tags && db.tags.includes(v); });
      }
      return true;
    });
  }
  return results;
}

function accumulateTreeFilters(filters) {
  // Merge a choice's filters into treeFilters (OR logic within each type)
  for (const [type, values] of Object.entries(filters)) {
    if (!values || values.length === 0) continue;
    if (!state.treeFilters[type]) {
      state.treeFilters[type] = [];
    }
    for (const v of values) {
      if (!state.treeFilters[type].includes(v)) {
        state.treeFilters[type].push(v);
      }
    }
  }
}

function removeStepFilters(stepIdx) {
  // Rebuild treeFilters by replaying selections up to stepIdx (exclusive)
  state.treeFilters = {};
  for (let i = 0; i < stepIdx; i++) {
    const sel = state.treeSelections[i];
    if (sel && sel.filters) {
      accumulateTreeFilters(sel.filters);
    }
  }
}

function startDecisionTree() {
  state.view = 'tree';
  state.treeStep = 0;
  state.treeFilters = {};
  state.treeSelections = [];
  updateNavButtons();
  renderApp();
}

function exitDecisionTree(applyResults) {
  if (applyResults) {
    // Merge tree filters into activeFilters
    for (const [type, values] of Object.entries(state.treeFilters)) {
      if (!values || values.length === 0) continue;
      if (!state.activeFilters[type]) {
        state.activeFilters[type] = [];
      }
      for (const v of values) {
        if (!state.activeFilters[type].includes(v)) {
          state.activeFilters[type].push(v);
        }
        state.treeSourceFilters.add(type + ':' + v);
      }
    }
  }
  state.view = 'browse';
  updateNavButtons();
  updateHash();
  renderApp();
}

function makeTreeChoice(stepIdx, filters) {
  // Record selection
  state.treeSelections[stepIdx] = { stepIdx: stepIdx, filters: filters };
  // Trim any selections beyond current (in case of back-then-forward)
  state.treeSelections.length = stepIdx + 1;

  // Accumulate filters
  accumulateTreeFilters(filters);

  // Advance to next step
  if (stepIdx + 1 >= state.treeData.steps.length) {
    // Last step completed — show results
    exitDecisionTree(true);
  } else {
    state.treeStep = stepIdx + 1;
    renderApp();
  }
}

function goToPreviousStep() {
  if (state.treeStep > 0) {
    const prevStep = state.treeStep - 1;
    // Clear the previous step's selection so user can re-choose
    // Remove filters from prevStep onward (inclusive)
    removeStepFilters(prevStep);
    // Trim selections to just before the step we're going back to
    state.treeSelections.length = prevStep;
    state.treeStep = prevStep;
    renderApp();
  }
}

function skipCurrentStep() {
  const total = state.treeData ? state.treeData.steps.length : 0;
  const stepIdx = state.treeStep;
  // Record an empty selection for this step
  state.treeSelections[stepIdx] = { stepIdx: stepIdx, filters: {} };
  state.treeSelections.length = stepIdx + 1;

  if (stepIdx + 1 >= total) {
    exitDecisionTree(true);
  } else {
    state.treeStep = stepIdx + 1;
    renderApp();
  }
}

// ── Tree render helpers ───────────────────────────────────────────────
const TREE_ICONS = {
  sqli: '\u{1F4CB}',
  flex: '\u{1F504}',
  reads: '\u{1F4D6}',
  writes: '\u{270F}\u{FE0F}',
  mixed: '\u{2696}\u{FE0F}',
  vector: '\u{1F9E0}',
  desktop: '\u{1F5A5}\u{FE0F}',
  mobile: '\u{1F4F1}',
  browser: '\u{1F310}',
  server: '\u{2601}\u{FE0F}',
  py: '\u{1F40D}',
  rs: '\u{1F980}',
  go: '\u{1F438}',
  js: '\u{1F4DC}',
  java: '\u{2615}',
  cpp: '\u{2699}\u{FE0F}',
  acid: '\u{1F512}',
  offline: '\u{1F4E1}',
  ai: '\u{1F916}',
  search: '\u{1F50E}',
};

function renderTreeView() {
  if (!state.treeData || !state.treeData.steps || state.treeData.steps.length === 0) {
    return html`
      <div class="error-state">
        <h2>Decision tree unavailable</h2>
        <p>The decision tree data could not be loaded.</p>
        <button class="btn" id="back-to-browse-btn">Back to browse</button>
      </div>
    `;
  }

  const steps = state.treeData.steps;
  const currentStepIdx = state.treeStep;
  const currentStep = steps[currentStepIdx];
  const total = steps.length;
  const isLastStep = currentStepIdx >= total - 1;
  const filtered = applyTreeFilters();
  const count = filtered.length;
  const hasPrevSelection = state.treeSelections[currentStepIdx];

  return html`
    <div class="tree-view">
      <div class="tree-intro">
        <h2>` + escapeHtml(state.treeData.title || 'Find Your Database') + `</h2>
        <p class="tree-intro-desc">` + escapeHtml(state.treeData.description || '') + `</p>
      </div>

      ` + renderTreeStepIndicators(steps, currentStepIdx) + `
      ` + renderTreeProgressBar(currentStepIdx, total) + `

      <div class="tree-question-card">
        <p class="tree-question">` + escapeHtml(currentStep.question) + `</p>
        <p class="tree-help">` + escapeHtml(currentStep.help) + `</p>
        <div class="tree-choices">
          ` + (currentStep.choices || []).map(function(choice, i) {
            const choiceIcon = TREE_ICONS[choice.icon] || '\u{1F4CC}';
            const isSelected = hasPrevSelection && hasPrevSelection.filters === choice.filters;
            return html`
              <button class="tree-choice-btn` + (isSelected ? ' selected' : '') + `"
                      data-tree-step="` + currentStepIdx + `"
                      data-tree-choice="` + i + `"
                      aria-pressed="` + (isSelected ? 'true' : 'false') + `">
                <span class="choice-icon">` + choiceIcon + `</span>
                ` + escapeHtml(choice.text) + `
              </button>
            `;
          }).join('') + `
        </div>
      </div>

      <div class="tree-nav">
        ` + (currentStepIdx > 0 ? html`
          <button class="tree-back-btn" id="tree-back-btn">
            &larr; Back
          </button>
        ` : html`<span></span>`) + `
        ` + (currentStepIdx < total - 1 ? html`
          <button class="tree-skip-btn" id="tree-skip-btn">Skip this step</button>
        ` : '') + `
        <button class="tree-results-btn" id="tree-results-btn">
          ` + (isLastStep ? 'See Results' : 'Skip to Results') + `
        </button>
      </div>

      <div class="tree-live-count` + (count === 0 ? ' empty' : '') + `" aria-live="polite" role="status">
        ` + count + ` database` + (count !== 1 ? 's' : '') + ` match` + (count === 1 ? 'es' : '') + ` so far
      </div>
    </div>
  `;
}

function renderTreeStepIndicators(steps, currentStepIdx) {
  const dots = steps.map(function(_, i) {
    let cls = 'tree-step-dot';
    if (i < currentStepIdx) {
      cls += ' completed';
    } else if (i === currentStepIdx) {
      cls += ' active';
    }
    const label = i < currentStepIdx ? '✓' : String(i + 1);
    return html`<div class="` + cls + `">` + label + `</div>`;
  }).join('');

  return html`<div class="tree-step-indicators">` + dots + `</div>`;
}

function renderTreeProgressBar(currentStepIdx, total) {
  const pct = total > 0 ? Math.round((currentStepIdx / total) * 100) : 0;
  return html`
    <div class="tree-progress">
      <span class="progress-label">Step ` + (currentStepIdx + 1) + ` of ` + total + `</span>
      <div class="progress-bar-track">
        <div class="progress-bar-fill" style="width:` + pct + `%"></div>
      </div>
      <span class="progress-count">` + currentStepIdx + `/` + total + `</span>
    </div>
  `;
}

function wireTreeEvents() {
  // Choice buttons
  $$('.tree-choice-btn').forEach(function(btn) {
    btn.addEventListener('click', function() {
      const stepIdx = parseInt(btn.dataset.treeStep, 10);
      const choiceIdx = parseInt(btn.dataset.treeChoice, 10);
      const step = state.treeData.steps[stepIdx];
      const choice = step.choices[choiceIdx];
      makeTreeChoice(stepIdx, choice.filters);
    });
  });

  // Keyboard navigation for tree choices
  wireTreeChoiceKeyboard();

  // Back button
  const backBtn = $('#tree-back-btn');
  if (backBtn) {
    backBtn.addEventListener('click', goToPreviousStep);
  }

  // Skip button
  const skipBtn = $('#tree-skip-btn');
  if (skipBtn) {
    skipBtn.addEventListener('click', skipCurrentStep);
  }

  // Results / Skip to Results button
  const resultsBtn = $('#tree-results-btn');
  if (resultsBtn) {
    resultsBtn.addEventListener('click', function() { exitDecisionTree(true); });
  }

  // Back to browse (error state)
  const backBrowseBtn = $('#back-to-browse-btn');
  if (backBrowseBtn) {
    backBrowseBtn.addEventListener('click', function() { exitDecisionTree(false); });
  }
}

function updateNavButtons() {
  const browseBtn = document.getElementById('nav-browse');
  const treeBtn = document.getElementById('nav-tree');
  const compareBtn = document.getElementById('nav-compare');
  if (!browseBtn || !treeBtn) return;

  browseBtn.classList.remove('active-view');
  browseBtn.setAttribute('aria-pressed', 'false');
  treeBtn.classList.remove('active-view');
  treeBtn.setAttribute('aria-pressed', 'false');
  if (compareBtn) {
    compareBtn.classList.remove('active-view');
    compareBtn.setAttribute('aria-pressed', 'false');
  }

  if (state.view === 'browse') {
    browseBtn.classList.add('active-view');
    browseBtn.setAttribute('aria-pressed', 'true');
  } else if (state.view === 'tree') {
    treeBtn.classList.add('active-view');
    treeBtn.setAttribute('aria-pressed', 'true');
  } else if (state.view === 'compare' && compareBtn) {
    compareBtn.classList.add('active-view');
    compareBtn.setAttribute('aria-pressed', 'true');
  }

  // Update compare button count
  if (compareBtn) {
    const count = state.compareSelection.length;
    compareBtn.querySelector('.nav-label').textContent = count > 0 ? 'Compare (' + count + ')' : 'Compare';
    if (count < 2 && state.view !== 'compare') {
      compareBtn.disabled = true;
      compareBtn.setAttribute('title', 'Select 2–4 databases to compare');
    } else {
      compareBtn.disabled = false;
      compareBtn.removeAttribute('title');
    }
  }
}

// ── Comparison ────────────────────────────────────────────────────────
function toggleCompareDB(slug) {
  const idx = state.compareSelection.indexOf(slug);
  if (idx >= 0) {
    state.compareSelection.splice(idx, 1);
  } else {
    if (state.compareSelection.length >= 4) return;
    state.compareSelection.push(slug);
  }
  updateNavButtons();
  // Re-render only the card grid to update toggle states
  renderApp();
}

function startComparison() {
  if (state.compareSelection.length < 2) return;
  state.view = 'compare';
  updateNavButtons();
  renderApp();
}

function exitComparison() {
  state.view = 'browse';
  updateNavButtons();
  renderApp();
}

function removeFromComparison(slug) {
  const idx = state.compareSelection.indexOf(slug);
  if (idx >= 0) {
    state.compareSelection.splice(idx, 1);
  }
  // If fewer than 2, go back to browse
  if (state.compareSelection.length < 2) {
    exitComparison();
  } else {
    renderApp();
  }
}

function getComparisonDBs() {
  return state.compareSelection
    .map(function(slug) { return state.databases.find(function(db) { return db.slug === slug; }); })
    .filter(Boolean);
}

function renderCompareToggle(slug, isSelected) {
  const disabled = !isSelected && state.compareSelection.length >= 4;
  return html`
    <button class="compare-toggle` + (isSelected ? ' selected' : '') + `"
            data-compare-slug="` + escapeHtml(slug) + `"
            aria-label="` + (isSelected ? 'Remove from comparison' : 'Add to comparison') + `"
            title="` + (disabled ? 'Max 4 databases can be compared' : (isSelected ? 'Remove from comparison' : 'Add to comparison')) + `"
            ` + (disabled ? 'disabled' : '') + `>
      <svg class="compare-icon" viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <line x1="18" y1="20" x2="18" y2="10"></line>
        <line x1="12" y1="20" x2="12" y2="4"></line>
        <line x1="6" y1="20" x2="6" y2="14"></line>
        <line x1="18" y1="5" x2="22" y2="10"></line>
        <line x1="18" y1="5" x2="14" y2="10"></line>
        <line x1="2" y1="20" x2="22" y2="20"></line>
      </svg>
    </button>
  `;
}

function renderCompareView() {
  const dbs = getComparisonDBs();
  if (dbs.length < 2) {
    return html`
      <div class="empty-state">
        <h2>Select databases to compare</h2>
        <p>Click the balance-scale icon on 2&ndash;4 database cards to add them to the comparison.</p>
        <button class="btn" id="back-to-browse-btn">Back to browse</button>
      </div>
    `;
  }

  const rows = [
    { label: 'Category', field: 'category', render: function(db) { return renderCategoryBadge(db.category); } },
    { label: 'License', field: 'license', render: function(db) { return db.license ? escapeHtml(db.license) : '—'; } },
    { label: 'Disk Format', field: 'format_on_disk', render: function(db) { return db.format_on_disk ? escapeHtml(truncate(db.format_on_disk, 140)) : '—'; } },
    { label: 'Stars', field: 'github_stars', render: function(db) { return db.github_stars ? html`&star; ` + formatStars(db.github_stars) : '—'; } },
    { label: 'Maintenance', field: 'maintenance_status', render: function(db) { return db.maintenance_status ? escapeHtml(db.maintenance_status) : '—'; } },
    {
      label: 'Languages',
      field: 'languages',
      render: function(db) {
        if (!db.languages || db.languages.length === 0) return '—';
        return db.languages.map(function(l) { return html`<span class="lang-tag">` + escapeHtml(l.name) + `</span>`; }).join(' ');
      },
    },
    {
      label: 'Best Use Cases',
      field: 'best_use_cases',
      render: function(db) {
        if (!db.best_use_cases || db.best_use_cases.length === 0) return '—';
        return html`<ul class="compare-list">` + db.best_use_cases.map(function(uc) { return html`<li>` + escapeHtml(uc) + `</li>`; }).join('') + `</ul>`;
      },
    },
    { label: 'Remarks', field: 'remarks', render: function(db) { return db.remarks ? escapeHtml(truncate(db.remarks, 250)) : '—'; } },
  ];

  const colHeaders = dbs.map(function(db) {
    const repoUrl = db.repository_url || 'https://github.com/' + (db._repo_path || '');
    return html`
      <th class="compare-col-header" scope="col">
        <div class="compare-col-header-content">
          <a class="compare-db-name" href="` + escapeHtml(repoUrl) + `" target="_blank" rel="noopener">` + escapeHtml(db.name) + `</a>
          <button class="compare-remove-btn"
                  data-compare-remove="` + escapeHtml(db.slug) + `"
                  aria-label="Remove ` + escapeHtml(db.name) + ` from comparison"
                  title="Remove ` + escapeHtml(db.name) + `">&times;</button>
        </div>
      </th>
    `;
  }).join('');

  const tableRows = rows.map(function(row) {
    const cells = dbs.map(function(db) {
      const rendered = row.render(db);
      return html`<td>` + rendered + `</td>`;
    }).join('');

    return html`
      <tr>
        <th class="compare-row-label" scope="row">` + escapeHtml(row.label) + `</th>
        ` + cells + `
      </tr>
    `;
  }).join('');

  return html`
    <div class="compare-view">
      <div class="compare-header">
        <h2>Compare Databases</h2>
        <p class="compare-subtitle">` + dbs.length + ` database` + (dbs.length !== 1 ? 's' : '') + ` selected</p>
        <button class="btn back-browse-btn" id="back-to-browse-btn">&larr; Back to Browse</button>
      </div>
      <div class="compare-table-wrapper">
        <table class="comparison-table">
          <thead>
            <tr>
              <th class="compare-row-label-header" scope="col"></th>
              ` + colHeaders + `
            </tr>
          </thead>
          <tbody>
            ` + tableRows + `
          </tbody>
        </table>
      </div>
    </div>
  `;
}

function wireCompareEvents() {
  // Remove buttons in column headers
  $$('.compare-remove-btn').forEach(function(btn) {
    btn.addEventListener('click', function() {
      const slug = btn.dataset.compareRemove;
      removeFromComparison(slug);
    });
  });

  // Back to browse button
  const backBtn = $('#back-to-browse-btn');
  if (backBtn) {
    backBtn.addEventListener('click', exitComparison);
  }

  // Focus trap for comparison view
  wireCompareFocusTrap();
}

// ── Keyboard Navigation Helpers ────────────────────────────────────────
function getFocusableElements(container) {
  const selector = 'a[href], button:not([disabled]), input:not([disabled]), [tabindex]:not([tabindex="-1"])';
  return Array.from(container.querySelectorAll(selector));
}

function focusTrap(container, e) {
  const focusable = getFocusableElements(container);
  if (focusable.length === 0) return;
  const first = focusable[0];
  const last = focusable[focusable.length - 1];
  if (e.key === 'Tab') {
    if (e.shiftKey) {
      if (document.activeElement === first) {
        e.preventDefault();
        last.focus();
      }
    } else {
      if (document.activeElement === last) {
        e.preventDefault();
        first.focus();
      }
    }
  }
}

// ── Card Grid Keyboard Navigation ──────────────────────────────────────
function wireCardKeyboard() {
  const grid = document.querySelector('.card-grid');
  if (!grid) return;

  grid.addEventListener('keydown', function(e) {
    const card = document.activeElement.closest('.db-card');
    if (!card) return;

    const cards = Array.from(grid.querySelectorAll('.db-card'));
    const idx = cards.indexOf(card);
    if (idx === -1) return;

    switch (e.key) {
      case 'ArrowDown':
      case 'ArrowRight': {
        e.preventDefault();
        const next = idx + 1 < cards.length ? cards[idx + 1] : cards[0];
        next.focus();
        break;
      }
      case 'ArrowUp':
      case 'ArrowLeft': {
        e.preventDefault();
        const prev = idx - 1 >= 0 ? cards[idx - 1] : cards[cards.length - 1];
        prev.focus();
        break;
      }
      case 'Home': {
        e.preventDefault();
        cards[0].focus();
        break;
      }
      case 'End': {
        e.preventDefault();
        cards[cards.length - 1].focus();
        break;
      }
      case 'Enter':
      case ' ': {
        // Open the primary link in the card
        e.preventDefault();
        const link = card.querySelector('.db-card-name a');
        if (link) link.click();
        break;
      }
    }
  });
}

// ── Filter Chip Keyboard Navigation ────────────────────────────────────
function wireFilterChipKeyboard() {
  const groups = document.querySelectorAll('.filter-chips');
  groups.forEach(function(group) {
    group.addEventListener('keydown', function(e) {
      const chip = document.activeElement.closest('.filter-chip');
      if (!chip || !group.contains(chip)) return;

      const chips = Array.from(group.querySelectorAll('.filter-chip'));
      const idx = chips.indexOf(chip);
      if (idx === -1) return;

      switch (e.key) {
        case 'ArrowRight':
        case 'ArrowDown': {
          e.preventDefault();
          const next = idx + 1 < chips.length ? chips[idx + 1] : chips[0];
          next.focus();
          break;
        }
        case 'ArrowLeft':
        case 'ArrowUp': {
          e.preventDefault();
          const prev = idx - 1 >= 0 ? chips[idx - 1] : chips[chips.length - 1];
          prev.focus();
          break;
        }
        case 'Home': {
          e.preventDefault();
          chips[0].focus();
          break;
        }
        case 'End': {
          e.preventDefault();
          chips[chips.length - 1].focus();
          break;
        }
        case 'Enter':
        case ' ': {
          e.preventDefault();
          chip.click();
          break;
        }
      }
    });
  });
}

// ── Tree Choice Keyboard Navigation ────────────────────────────────────
function wireTreeChoiceKeyboard() {
  const choicesContainer = document.querySelector('.tree-choices');
  if (!choicesContainer) return;

  choicesContainer.addEventListener('keydown', function(e) {
    const choice = document.activeElement.closest('.tree-choice-btn');
    if (!choice || !choicesContainer.contains(choice)) return;

    const choices = Array.from(choicesContainer.querySelectorAll('.tree-choice-btn'));
    const idx = choices.indexOf(choice);
    if (idx === -1) return;

    switch (e.key) {
      case 'ArrowDown': {
        e.preventDefault();
        const next = idx + 1 < choices.length ? choices[idx + 1] : choices[0];
        next.focus();
        break;
      }
      case 'ArrowUp': {
        e.preventDefault();
        const prev = idx - 1 >= 0 ? choices[idx - 1] : choices[choices.length - 1];
        prev.focus();
        break;
      }
      case 'Enter':
      case ' ': {
        e.preventDefault();
        choice.click();
        break;
      }
    }
  });
}

// ── View-Level Keyboard Shortcuts (Esc, left arrow in tree) ────────────
function handleGlobalKeydown(e) {
  // Ignore if user is typing in an input or textarea
  const tag = document.activeElement ? document.activeElement.tagName : '';
  const isInput = tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT';

  // Decision tree: Escape to return to browse
  if (state.view === 'tree' && e.key === 'Escape') {
    e.preventDefault();
    exitDecisionTree(false);
    return;
  }

  // Decision tree: ArrowLeft to go back
  if (state.view === 'tree' && e.key === 'ArrowLeft' && !isInput) {
    if (state.treeStep > 0) {
      e.preventDefault();
      goToPreviousStep();
    }
    return;
  }

  // Comparison view: Escape to close
  if (state.view === 'compare' && e.key === 'Escape') {
    e.preventDefault();
    exitComparison();
    return;
  }
}

// ── Comparison View Focus Trap ─────────────────────────────────────────
function wireCompareFocusTrap() {
  const view = document.querySelector('.compare-view');
  if (!view) return;

  view.addEventListener('keydown', function(e) {
    if (e.key === 'Tab') {
      focusTrap(view, e);
    }
  });
}

// ── Data loading ──────────────────────────────────────────────────────
async function loadData() {
  state.status = 'loading';
  renderLoading();

  try {
    const [indexRes, filterRes] = await Promise.all([
      fetch('index.json'),
      fetch('filter-options.json'),
    ]);

    if (!indexRes.ok) {
      throw new Error('Failed to load index (HTTP ' + indexRes.status + ')');
    }

    const indexData = await indexRes.json();

    state.databases = indexData.databases || [];

    if (filterRes.ok) {
      state.filterOptions = await filterRes.json();
    } else {
      // Build filter options from data if filter-options.json unavailable
      state.filterOptions = buildFilterOptions(state.databases);
    }

    // Restore filter, search, and view state from URL hash
    const hashState = parseHash();
    state.activeFilters = hashState.filters || {};
    state.searchQuery = hashState.searchQuery || '';
    if (hashState.view) {
      state.view = hashState.view;
    }

    state.status = state.databases.length === 0 ? 'empty' : 'ready';
  } catch (err) {
    state.status = 'error';
    state.errorMessage = err.message;
  }
}

function buildFilterOptions(databases) {
  const categories = new Set();
  const languages = new Set();
  const licenses = new Set();
  const statuses = new Set();
  const tags = new Set();

  for (const db of databases) {
    if (db.category) categories.add(db.category);
    if (db.categories) db.categories.forEach(function(c) { categories.add(c); });
    if (db.license) licenses.add(db.license);
    if (db.maintenance_status) statuses.add(db.maintenance_status);
    if (db.languages) db.languages.forEach(function(l) {
      if (l.name) languages.add(l.name);
    });
    if (db.tags) db.tags.forEach(function(t) { tags.add(t); });
  }

  return {
    categories: Array.from(categories).sort(),
    all_categories: Array.from(categories).sort(),
    languages: Array.from(languages).sort(),
    ecosystems: [],
    licenses: Array.from(licenses).sort(),
    statuses: Array.from(statuses).sort(),
    tags: Array.from(tags).sort(),
  };
}

// ── Initialization ────────────────────────────────────────────────────
async function init() {
  await loadData();

  if (state.status === 'error') {
    renderError(state.errorMessage);
    return;
  }

  if (state.status === 'empty') {
    renderEmpty();
    return;
  }

  // Load decision tree (non-blocking)
  loadDecisionTree();

  // Wire navigation buttons
  wireNavButtons();

  // Global keyboard shortcuts (Escape, tree left-arrow)
  document.addEventListener('keydown', handleGlobalKeydown);

  renderApp();
}

function wireNavButtons() {
  const browseBtn = document.getElementById('nav-browse');
  const treeBtn = document.getElementById('nav-tree');
  const compareBtn = document.getElementById('nav-compare');

  if (browseBtn) {
    browseBtn.addEventListener('click', function() {
      if (state.view !== 'browse') {
        state.view = 'browse';
        updateNavButtons();
        renderApp();
      }
    });
  }

  if (treeBtn) {
    treeBtn.addEventListener('click', function() {
      if (state.view !== 'tree') {
        startDecisionTree();
      }
    });
  }

  if (compareBtn) {
    compareBtn.addEventListener('click', function() {
      if (state.compareSelection.length >= 2) {
        startComparison();
      }
    });
  }
}

// Boot when the DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', init);
} else {
  init();
}
