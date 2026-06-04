/**
 * Nate's AI — Frontend
 */
(function () {
  const state = {
    chatHistory: [],
  };

  // --- API helpers ---

  async function apiGet(path) {
    const res = await fetch(path, { method: 'GET' });
    if (!res.ok) throw new Error(res.statusText || `HTTP ${res.status}`);
    return res.json();
  }

  async function apiPost(path, body) {
    const res = await fetch(path, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(err.detail || `HTTP ${res.status}`);
    }
    return res.json();
  }

  // --- Escape / render ---

  function escapeHtml(str) {
    if (str == null) return '';
    const d = document.createElement('div');
    d.textContent = str;
    return d.innerHTML;
  }

  function renderMarkdown(text) {
    if (!text) return '';
    return marked.parse(String(text));
  }

  function highlightText(text, keywords) {
    if (!text || !keywords || !keywords.length) return escapeHtml(String(text));
    const escaped = escapeHtml(text);
    const pattern = keywords.map(k => k.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')).join('|');
    return escaped.replace(new RegExp(`(${pattern})`, 'gi'), '<span class="highlight">$1</span>');
  }

  // --- Timing ---

  function renderTiming(timing) {
    if (!timing || !Object.keys(timing).length) return '';
    const labels = {
      query_refinement_ms: 'Query Refinement',
      embedding_ms: 'Embedding',
      retrieval_ms: 'Retrieval (KB + QA)',
      answer_generation_ms: 'Answer Generation',
      total_chat_ms: 'Total',
    };
    let rows = '';
    for (const [key, label] of Object.entries(labels)) {
      const v = timing[key];
      if (v != null && Number(v) > 0) {
        const secs = key === 'total_chat_ms' ? ` (${(v / 1000).toFixed(2)}s)` : '';
        rows += `<div class="timing-row"><span class="timing-label">${escapeHtml(label)}</span><span class="timing-value">${Number(v).toFixed(0)} ms${secs}</span></div>`;
      }
    }
    return rows ? `<div class="timing-card"><strong>⏱ Performance</strong>${rows}</div>` : '';
  }

  // --- Chunk cards ---

  function renderChunkCard(chunk, index, keywords) {
    const score = chunk.score != null ? Number(chunk.score).toFixed(3) : '—';
    const isQA = chunk.file_type === 'qa_pair';
    const level = chunk.level;

    let levelClass = 'result-card--level-2';
    if (isQA) levelClass = 'result-card--qa';
    else if (level === 0) levelClass = 'result-card--level-0';
    else if (level === 1) levelClass = 'result-card--level-1';

    // Metadata pills
    let meta = '<div class="chunk-metadata">';
    if (isQA) {
      meta += `<span class="chunk-meta-pill chunk-meta-qa">Q&amp;A</span>`;
      if (chunk.document_name) meta += `<span class="chunk-meta-pill chunk-meta-doc" title="Client">${escapeHtml(chunk.document_name)}</span>`;
      if (chunk.tags && chunk.tags.length) {
        chunk.tags.slice(0, 3).forEach(t => {
          meta += `<span class="chunk-meta-pill chunk-meta-tag">${escapeHtml(t)}</span>`;
        });
      }
    } else {
      if (chunk.document_name) meta += `<span class="chunk-meta-pill chunk-meta-doc">${escapeHtml(chunk.document_name)}</span>`;
      if (chunk.topic) meta += `<span class="chunk-meta-pill chunk-meta-topic">${escapeHtml(chunk.topic)}</span>`;
      if (chunk.doc_type) meta += `<span class="chunk-meta-pill chunk-meta-level">${escapeHtml(chunk.doc_type)}</span>`;
      if (level != null) meta += `<span class="chunk-meta-pill chunk-meta-level">L${level}</span>`;
      if (chunk.page_number != null) meta += `<span class="chunk-meta-pill chunk-meta-page">p.${chunk.page_number}</span>`;
    }
    meta += '</div>';

    // Body
    let body = '';
    if (isQA) {
      body = `
        <div class="chunk-content qa-question"><strong>Q:</strong> ${highlightText(chunk.text, keywords)}</div>
        <div class="chunk-content qa-answer"><strong>A:</strong> ${highlightText(chunk.answer || '', keywords)}</div>
      `;
    } else {
      const highlighted = highlightText(chunk.text || '', keywords);
      let context = '';
      if (chunk.prev_chunk || chunk.next_chunk) {
        context = '<div class="context-section"><p class="context-title">Context</p>';
        if (chunk.prev_chunk) context += `<details class="context-expander"><summary>Previous</summary><div class="context-expander-body">${highlightText(chunk.prev_chunk, keywords)}</div></details>`;
        if (chunk.next_chunk) context += `<details class="context-expander"><summary>Next</summary><div class="context-expander-body">${highlightText(chunk.next_chunk, keywords)}</div></details>`;
        context += '</div>';
      }
      body = `<div class="chunk-content">${highlighted}</div>${context}`;
    }

    return `
      <article class="result-card ${levelClass}">
        <div class="chunk-header">
          <span class="chunk-number">#${index + 1}</span>
          <span class="score-badge">${score}</span>
        </div>
        ${meta}
        ${body}
      </article>
    `;
  }

  function renderChunks(chunks, keywords) {
    if (!chunks || !chunks.length) return '<p class="help-text">No chunks retrieved.</p>';
    let html = `<div class="chunks-header"><h4 class="chunks-title">Retrieved context</h4><span class="chunks-count">${chunks.length} chunk${chunks.length !== 1 ? 's' : ''}</span></div><div class="chunks-list">`;
    chunks.forEach((c, i) => { html += renderChunkCard(c, i, keywords); });
    html += '</div>';
    return html;
  }

  // --- Refinement info ---

  function renderRefinement(data) {
    if (!data) return '';
    let rows = '';
    if (data.refined_query) rows += `<div class="timing-row timing-row--block"><span class="timing-label">Refined query</span><span class="timing-value">${escapeHtml(data.refined_query)}</span></div>`;
    if (data.keywords && data.keywords.length) {
      const pills = data.keywords.slice(0, 12).map(k => `<span class="keyword-pill">${escapeHtml(k)}</span>`).join('');
      rows += `<div class="timing-row timing-row--keywords"><span class="timing-label">Keywords</span><div class="keyword-pills">${pills}</div></div>`;
    }
    return rows ? `<div class="timing-card refinement-params-card"><strong>📋 Query Refinement</strong>${rows}</div>` : '';
  }

  // --- Stats ---

  async function loadStats() {
    const el = document.getElementById('stats-content');
    if (!el) return;
    try {
      const data = await apiGet('/stats');
      el.innerHTML = `
        <div class="stat-card"><div class="value">${data.points_count ?? '—'}</div><div class="label">Total Points</div></div>
        <div class="stat-card"><div class="value">${data.kb_chunks ?? '—'}</div><div class="label">KB Chunks</div></div>
        <div class="stat-card"><div class="value">${data.qa_pairs ?? '—'}</div><div class="label">QA Pairs</div></div>
        <div class="stat-card"><div class="value">${data.status === 'Active' ? '✅ Active' : escapeHtml(data.status || '—')}</div><div class="label">Status</div></div>
      `;
    } catch (e) {
      el.innerHTML = `<p class="upload-result error">Failed to load stats: ${escapeHtml(e.message)}</p>`;
    }
  }

  async function loadConfig() {
    try {
      const data = await apiGet('/config');
      const el = id => document.getElementById(id);
      if (el('info-collection')) el('info-collection').textContent = data.qdrant_collection_name || '—';
      if (el('info-embedding')) el('info-embedding').textContent = data.openai_embedding_model || '—';
      if (el('info-llm')) el('info-llm').textContent = data.openai_model || '—';
    } catch (_) {}
  }

  // --- Block helpers ---

  function showBlock(id, show) {
    const el = document.getElementById(id);
    if (el) { if (show) el.classList.remove('hidden'); else el.classList.add('hidden'); }
  }

  // --- Filters ---

  function getFilters() {
    const topic = document.getElementById('topic-filter')?.value || null;
    const doc_type = document.getElementById('doctype-filter')?.value || null;
    return { topic: topic || null, doc_type: doc_type || null };
  }

  // --- Chat rendering ---

  function renderChatHistory() {
    const container = document.getElementById('chat-history');
    if (!container) return;
    if (!state.chatHistory.length) {
      container.innerHTML = '<p class="chat-caption" style="margin-top:0">No messages yet. Ask a question below.</p>';
      return;
    }
    container.innerHTML = state.chatHistory.map(msg => {
      const role = msg.role || 'user';
      const content = role === 'assistant' ? renderMarkdown(msg.content) : escapeHtml(msg.content);
      let extra = '';
      if (role === 'assistant') {
        if (msg.timing) extra += `<details class="results-details"><summary>⏱ Performance</summary>${renderTiming(msg.timing)}</details>`;
        if (msg.refinement) extra += `<details class="results-details"><summary>📋 Query refinement</summary>${renderRefinement(msg.refinement)}</details>`;
        if (msg.chunks && msg.chunks.length) extra += `<details><summary>🔍 Retrieved chunks (${msg.chunks.length})</summary>${renderChunks(msg.chunks, msg.keywords || [])}</details>`;
      }
      return `
        <div class="chat-message ${role}">
          <div class="chat-avatar">${role === 'user' ? '👤' : '🤖'}</div>
          <div class="chat-body">
            <div class="content">${content}</div>
            ${extra}
          </div>
        </div>
      `;
    }).join('');
    container.scrollTop = container.scrollHeight;
  }

  function showTypingIndicator() {
    const container = document.getElementById('chat-history');
    if (!container) return;
    const el = document.createElement('div');
    el.id = 'typing-indicator';
    el.className = 'typing-indicator';
    el.innerHTML = `<div class="chat-avatar">🤖</div><div class="typing-dots"><span class="typing-dot"></span><span class="typing-dot"></span><span class="typing-dot"></span></div>`;
    container.appendChild(el);
    el.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
  }

  function hideTypingIndicator() {
    document.getElementById('typing-indicator')?.remove();
  }

  // --- Search ---

  async function runSearch() {
    const queryEl = document.getElementById('search-query');
    const resultsEl = document.getElementById('search-results');
    const query = queryEl?.value?.trim() || '';
    if (!query) return;
    const btn = document.getElementById('btn-search');
    btn.disabled = true;
    btn.classList.add('spinner');
    resultsEl.innerHTML = '<p class="help-text">Searching...</p>';
    try {
      const { topic, doc_type } = getFilters();
      const body = { query };
      if (topic) body.topic = topic;
      if (doc_type) body.doc_type = doc_type;
      const data = await apiPost('/search/', body);
      const keywords = data.keywords || [];
      let html = '<div class="query-processing">';
      html += `<div class="query-box original"><strong>Original:</strong> ${escapeHtml(query)}</div>`;
      html += `<div class="query-box refined"><strong>Refined:</strong> ${escapeHtml(data.refined_query || query)}</div>`;
      html += '</div>';
      if (keywords.length) {
        html += `<div class="keywords-row"><strong>Keywords:</strong> <span class="keyword-pills-inline">${keywords.slice(0, 10).map(k => `<span class="keyword-pill">${escapeHtml(k)}</span>`).join('')}</span></div>`;
      }
      if (data.timing) html += `<details class="results-details"><summary>⏱ Performance</summary>${renderTiming(data.timing)}</details>`;
      html += renderChunks(data.results || [], keywords);
      resultsEl.innerHTML = html;
    } catch (e) {
      resultsEl.innerHTML = `<p class="upload-result error">❌ ${escapeHtml(e.message)}</p>`;
    }
    btn.classList.remove('spinner');
    btn.disabled = false;
  }

  // --- Event listeners ---

  document.getElementById('btn-search-mode')?.addEventListener('click', () => showBlock('search-block', true));
  document.getElementById('btn-close-search')?.addEventListener('click', () => showBlock('search-block', false));
  document.getElementById('btn-chat-mode')?.addEventListener('click', () => {
    showBlock('search-block', false);
    document.querySelector('.chat-section')?.scrollIntoView({ behavior: 'smooth' });
  });
  document.getElementById('btn-stats')?.addEventListener('click', async () => {
    showBlock('stats-block', true);
    await loadStats();
  });
  document.getElementById('btn-close-stats')?.addEventListener('click', () => showBlock('stats-block', false));
  document.getElementById('btn-clear-chat')?.addEventListener('click', () => {
    state.chatHistory = [];
    renderChatHistory();
  });
  document.getElementById('btn-reset-limits')?.addEventListener('click', () => {
    ['limit-pages', 'limit-paragraphs', 'limit-final'].forEach(id => {
      const el = document.getElementById(id);
      if (el) el.value = '';
    });
  });
  document.getElementById('btn-clear-system-prompt')?.addEventListener('click', () => {
    const el = document.getElementById('system-prompt');
    if (el) el.value = '';
  });
  document.getElementById('btn-search')?.addEventListener('click', runSearch);
  document.getElementById('search-query')?.addEventListener('keydown', e => {
    if (e.key === 'Enter') { e.preventDefault(); runSearch(); }
  });

  document.getElementById('chat-input')?.addEventListener('keydown', e => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); document.getElementById('chat-form')?.requestSubmit(); }
  });

  document.getElementById('chat-form')?.addEventListener('submit', async function (e) {
    e.preventDefault();
    const input = document.getElementById('chat-input');
    const question = input?.value?.trim() || '';
    if (!question) return;
    input.value = '';
    const btn = document.getElementById('btn-send');
    btn.disabled = true;
    btn.classList.add('spinner');

    state.chatHistory.push({ role: 'user', content: question });
    renderChatHistory();
    showTypingIndicator();

    try {
      const { topic, doc_type } = getFilters();
      const historyForApi = state.chatHistory.slice(-10)
        .filter(m => m.role === 'user' || m.role === 'assistant')
        .map(m => ({ role: m.role, content: m.content }));

      const body = { question, chat_history: historyForApi };
      if (topic) body.topic = topic;
      if (doc_type) body.doc_type = doc_type;
      const systemPrompt = document.getElementById('system-prompt')?.value?.trim() || null;
      if (systemPrompt) body.system_prompt = systemPrompt;

      const data = await apiPost('/chat/', body);
      const search = data.search || {};
      const chunks = search.results || [];
      const keywords = search.keywords || [];
      const refinement = { refined_query: search.refined_query, keywords };

      state.chatHistory.push({
        role: 'assistant',
        content: data.answer || "I couldn't generate an answer.",
        chunks,
        keywords,
        timing: data.timing || {},
        refinement,
      });
    } catch (e) {
      state.chatHistory.push({ role: 'assistant', content: '❌ Error: ' + e.message, chunks: [], keywords: [], timing: {}, refinement: null });
    }

    hideTypingIndicator();
    renderChatHistory();
    btn.classList.remove('spinner');
    btn.disabled = false;
  });

  // --- Init ---
  loadConfig();
  renderChatHistory();
  showBlock('stats-block', false);
  showBlock('search-block', false);
})();
