/**
 * UVM 1.2 Documentation - Client-Side RAG & Semantic Search Engine
 * Features:
 * - Local query embedding generation via Transformers.js (ONNX Runtime Web / WASM)
 * - Dot product cosine similarity across precomputed doc vectors (< 3ms)
 * - Smart Snippet Extractor: extracts top 1-2 relevant sentences with keyword highlighting
 * - Optional Hybrid Search (Reciprocal Rank Fusion / Lexical + Vector)
 * - RAM Memory Management (Auto-release after inactivity to prevent RAM bloat)
 * - Cache Manager (Cache API inspect and purge)
 */

(function (root, factory) {
  if (typeof define === 'function' && define.amd) {
    define([], factory);
  } else if (typeof module === 'object' && module.exports) {
    module.exports = factory();
  } else {
    root.UVMRagEngine = factory();
  }
})(typeof self !== 'undefined' ? self : this, function () {
  'use strict';

  const STORAGE_KEYS = {
    CONSENT: 'uvm_rag_consent',
    SELECTED_MODEL: 'uvm_rag_selected_model',
    HYBRID_ENABLED: 'uvm_rag_hybrid_enabled',
    AUTO_SEMANTIC: 'uvm_rag_auto_semantic'
  };

  // Default models catalog fallback if config/rag_models.json is not loaded
  const DEFAULT_MODELS = [
    {
      id: 'all-minilm-l6-v2',
      name: 'MiniLM-L6 (Équilibré & Rapide)',
      description: 'Modèle standard idéal pour la documentation technique.',
      dimension: 384,
      downloadSize: '23 Mo',
      ramUsage: '~60 Mo',
      speedRating: 5,
      accuracyRating: 4,
      lightnessRating: 5,
      modelPath: 'Xenova/all-MiniLM-L6-v2',
      quantized: true,
      recommended: true,
      default: true
    },
    {
      id: 'bge-small-en-v1.5',
      name: 'BGE-Small-EN (Haute Précision)',
      description: 'Modèle BAAI haute fidélité pour l’anglais technique.',
      dimension: 384,
      downloadSize: '33 Mo',
      ramUsage: '~85 Mo',
      speedRating: 4,
      accuracyRating: 5,
      lightnessRating: 4,
      modelPath: 'Xenova/bge-small-en-v1.5',
      quantized: true,
      recommended: false,
      default: false
    },
    {
      id: 'bge-micro-v2',
      name: 'BGE-Micro (Ultra-Léger)',
      description: 'Empreinte minimale, idéal pour connexions lentes.',
      dimension: 384,
      downloadSize: '14 Mo',
      ramUsage: '~35 Mo',
      speedRating: 5,
      accuracyRating: 3,
      lightnessRating: 5,
      modelPath: 'TaylorAI/bge-micro-v2',
      quantized: true,
      recommended: false,
      default: false
    }
  ];

  class RagEngine {
    constructor() {
      this.models = DEFAULT_MODELS;
      this.prompts = [];
      this.chunks = null;
      this.embeddings = null;
      this.pipeline = null;
      this.isModelLoading = false;
      this.isDataLoading = false;
      this.currentModelId = localStorage.getItem(STORAGE_KEYS.SELECTED_MODEL) || 'all-minilm-l6-v2';
      this.isHybrid = localStorage.getItem(STORAGE_KEYS.HYBRID_ENABLED) !== 'false'; // default true
      this.isAutoSemantic = localStorage.getItem(STORAGE_KEYS.AUTO_SEMANTIC) === 'true'; // default false
      this.idleTimer = null;
      this.IDLE_TIMEOUT_MS = 3 * 60 * 1000; // 3 minutes idle release

      this.initConfigs();
    }

    async initConfigs() {
      try {
        const [modelsRes, promptsRes] = await Promise.allSettled([
          fetch('config/rag_models.json').then(r => r.ok ? r.json() : null),
          fetch('config/rag_prompts.json').then(r => r.ok ? r.json() : null)
        ]);
        if (modelsRes.status === 'fulfilled' && modelsRes.value) {
          this.models = modelsRes.value;
        }
        if (promptsRes.status === 'fulfilled' && promptsRes.value) {
          this.prompts = promptsRes.value;
        }
      } catch (e) {
        console.warn('Using default RAG configs', e);
      }
    }

    hasConsent() {
      return localStorage.getItem(STORAGE_KEYS.CONSENT) === 'true';
    }

    grantConsent(modelId) {
      localStorage.setItem(STORAGE_KEYS.CONSENT, 'true');
      if (modelId) {
        this.setModel(modelId);
      }
    }

    getModelConfig(modelId = this.currentModelId) {
      return this.models.find(m => m.id === modelId) || this.models[0];
    }

    setModel(modelId) {
      if (this.currentModelId !== modelId) {
        this.currentModelId = modelId;
        localStorage.setItem(STORAGE_KEYS.SELECTED_MODEL, modelId);
        // Force unload old pipeline so new model loads on demand
        this.unloadPipeline();
      }
    }

    setHybrid(enabled) {
      this.isHybrid = !!enabled;
      localStorage.setItem(STORAGE_KEYS.HYBRID_ENABLED, this.isHybrid ? 'true' : 'false');
    }

    setAutoSemantic(enabled) {
      this.isAutoSemantic = !!enabled;
      localStorage.setItem(STORAGE_KEYS.AUTO_SEMANTIC, this.isAutoSemantic ? 'true' : 'false');
    }

    resetIdleTimer() {
      if (this.idleTimer) clearTimeout(this.idleTimer);
      this.idleTimer = setTimeout(() => {
        this.unloadPipeline();
      }, this.IDLE_TIMEOUT_MS);
    }

    unloadPipeline() {
      if (this.pipeline) {
        console.log('[RAG] Unloading model pipeline from RAM to free memory.');
        this.pipeline = null;
      }
      if (this.idleTimer) {
        clearTimeout(this.idleTimer);
        this.idleTimer = null;
      }
    }

    async loadData() {
      if (this.chunks && this.embeddings) return;
      if (this.isDataLoading) {
        while (this.isDataLoading) {
          await new Promise(r => setTimeout(r, 50));
        }
        return;
      }

      this.isDataLoading = true;
      try {
        const [chunksRes, embRes] = await Promise.all([
          fetch('data/rag_chunks.json'),
          fetch('data/rag_embeddings.bin')
        ]);

        if (!chunksRes.ok || !embRes.ok) {
          throw new Error('Failed to load rag_chunks.json or rag_embeddings.bin. Ensure build_rag_embeddings.py has run.');
        }

        this.chunks = await chunksRes.json();
        const buffer = await embRes.arrayBuffer();
        this.embeddings = new Float32Array(buffer);
        console.log(`[RAG] Loaded ${this.chunks.length} chunks and vector database (${(buffer.byteLength / 1024 / 1024).toFixed(2)} MB).`);
      } finally {
        this.isDataLoading = false;
      }
    }

    async loadModel(onProgress) {
      if (this.pipeline) {
        this.resetIdleTimer();
        return this.pipeline;
      }

      if (this.isModelLoading) {
        while (this.isModelLoading) {
          await new Promise(r => setTimeout(r, 80));
        }
        return this.pipeline;
      }

      this.isModelLoading = true;
      const modelCfg = this.getModelConfig();

      try {
        // Load Transformers.js dynamically from CDN or bundled
        let transformers = window.transformers;
        if (!transformers) {
          transformers = await import('https://cdn.jsdelivr.net/npm/@xenova/transformers@2.17.2');
          window.transformers = transformers;
        }

        // Configure pipeline options
        const { pipeline, env } = transformers;
        env.allowLocalModels = false; // load from HF hub
        env.useBrowserCache = true;  // enable persistent Cache API

        if (onProgress) {
          onProgress({ status: 'init', message: `Initialisation du modèle ${modelCfg.name}...`, progress: 5 });
        }

        const extractor = await pipeline('feature-extraction', modelCfg.modelPath, {
          quantized: modelCfg.quantized !== false,
          progress_callback: (prog) => {
            if (onProgress && prog) {
              const pct = typeof prog.progress === 'number' ? Math.round(prog.progress) : 50;
              onProgress({
                status: 'downloading',
                file: prog.file || 'model weights',
                loaded: prog.loaded,
                total: prog.total,
                progress: pct,
                message: `Téléchargement ${modelCfg.name} (${pct}%)...`
              });
            }
          }
        });

        this.pipeline = extractor;
        this.resetIdleTimer();
        if (onProgress) {
          onProgress({ status: 'ready', message: 'Modèle prêt !', progress: 100 });
        }
        return this.pipeline;
      } catch (err) {
        console.error('[RAG] Failed to load model pipeline:', err);
        throw err;
      } finally {
        this.isModelLoading = false;
      }
    }

    /**
     * Smart Snippet Extractor
     * Splits chunk text into sentences, scores each sentence against query tokens,
     * and returns the top 1-2 most informative sentences with highlighted tokens.
     */
    extractSmartSnippet(chunkText, query) {
      if (!chunkText) return '';
      const clean = chunkText.trim();
      const rawSentences = clean.split(/(?<=[.!?])\s+(?=[A-Z0-9`])/);
      if (rawSentences.length <= 1) {
        return this.highlightSnippet(clean.slice(0, 220), query);
      }

      // Tokenize query words
      const queryTokens = query.toLowerCase()
        .replace(/[^a-z0-9_`]/g, ' ')
        .split(/\s+/)
        .filter(t => t.length > 2);

      if (queryTokens.length === 0) {
        return this.highlightSnippet(rawSentences.slice(0, 2).join(' '), query);
      }

      // Score each sentence
      let bestSentences = [];
      rawSentences.forEach((sentence, idx) => {
        const lower = sentence.toLowerCase();
        let score = 0;
        queryTokens.forEach(t => {
          if (lower.includes(t)) {
            score += 2;
            if (new RegExp(`\\b${t}\\b`, 'i').test(sentence)) score += 3;
          }
        });
        if (score > 0) {
          bestSentences.push({ sentence, score, idx });
        }
      });

      if (bestSentences.length === 0) {
        return this.highlightSnippet(rawSentences.slice(0, 2).join(' '), query);
      }

      // Pick top 2 sentences sorted by original document flow
      bestSentences.sort((a, b) => b.score - a.score);
      const topSelected = bestSentences.slice(0, 2).sort((a, b) => a.idx - b.idx);
      const combined = topSelected.map(s => s.sentence).join(' ');

      return this.highlightSnippet(combined.slice(0, 260), query);
    }

    highlightSnippet(text, query) {
      if (!text) return '';
      const queryTokens = query.trim().split(/\s+/).filter(t => t.length > 2);
      if (queryTokens.length === 0) return this.escapeHtml(text);

      const pattern = queryTokens.map(t => t.replace(/[-/\\^$*+?.()|[\]{}]/g, '\\$&')).join('|');
      const regex = new RegExp(`(${pattern})`, 'gi');

      return this.escapeHtml(text).replace(regex, '<mark class="rag-highlight">$1</mark>');
    }

    escapeHtml(str) {
      return (str || '').replace(/[&<>"']/g, m => ({
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#39;'
      }[m]));
    }

    /**
     * Compute lexical keyword overlap score for hybrid search
     */
    computeLexicalScore(item, queryTokens) {
      if (!queryTokens.length) return 0;
      let score = 0;
      const titleLower = (item.title || '').toLowerCase();
      const classLower = (item.class || '').toLowerCase();
      const textLower = (item.text || '').toLowerCase();

      queryTokens.forEach(t => {
        if (titleLower === t) score += 10;
        else if (titleLower.includes(t)) score += 5;

        if (classLower === t) score += 8;
        else if (classLower.includes(t)) score += 4;

        if (textLower.includes(t)) score += 1;
      });

      return Math.min(score / (queryTokens.length * 10), 1.0);
    }

    /**
     * Main Semantic Search function
     */
    async search(query, options = {}) {
      const topK = options.topK || 20;
      const onProgress = options.onProgress || null;

      if (!query || !query.trim()) {
        return [];
      }

      this.resetIdleTimer();

      // Ensure data and model are loaded
      await Promise.all([
        this.loadData(),
        this.loadModel(onProgress)
      ]);

      const dim = 384;
      const totalChunks = this.chunks.length;

      // 1. Embed query in browser using Transformers.js
      const output = await this.pipeline(query, { pooling: 'mean', normalize: true });
      const queryVec = output.data; // Float32Array

      // 2. Compute Cosine Similarities across all chunks (dot product)
      const queryTokens = query.toLowerCase()
        .replace(/[^a-z0-9_`]/g, ' ')
        .split(/\s+/)
        .filter(t => t.length > 2);

      const scored = [];
      const emb = this.embeddings;

      for (let i = 0; i < totalChunks; i++) {
        let dot = 0.0;
        const offset = i * dim;
        for (let d = 0; d < dim; d++) {
          dot += queryVec[d] * emb[offset + d];
        }

        let finalScore = dot;
        if (this.isHybrid && queryTokens.length > 0) {
          const lexScore = this.computeLexicalScore(this.chunks[i], queryTokens);
          finalScore = (dot * 0.70) + (lexScore * 0.30);
        }

        scored.push({ index: i, score: finalScore, vectorScore: dot });
      }

      // 3. Sort by highest score
      scored.sort((a, b) => b.score - a.score);

      // 4. Enrich top results with smart snippets and badges
      const results = [];
      const topSelected = scored.slice(0, topK);

      for (const item of topSelected) {
        const chunk = this.chunks[item.index];
        const snippet = this.extractSmartSnippet(chunk.text, query);
        const matchPct = Math.round(Math.max(0, Math.min(1, (item.score + 0.2) / 1.1)) * 100);

        results.push({
          chunk,
          score: item.score,
          vectorScore: item.vectorScore,
          matchPct,
          snippet,
          highlightedTitle: this.highlightSnippet(chunk.title, query)
        });
      }

      return results;
    }

    /**
     * Cache Inspection and Purge
     */
    async getCacheInfo() {
      let sizeMB = 0;
      let count = 0;
      if (typeof caches !== 'undefined') {
        const keys = await caches.keys();
        for (const k of keys) {
          if (k.includes('transformers') || k.includes('onnx') || k.includes('xenova')) {
            const cache = await caches.open(k);
            const requests = await cache.keys();
            count += requests.length;
          }
        }
      }
      if (navigator.storage && navigator.storage.estimate) {
        const est = await navigator.storage.estimate();
        if (est.usage) {
          sizeMB = (est.usage / (1024 * 1024)).toFixed(1);
        }
      }
      return { count, sizeMB };
    }

    async clearCache() {
      this.unloadPipeline();
      if (typeof caches !== 'undefined') {
        const keys = await caches.keys();
        for (const k of keys) {
          if (k.includes('transformers') || k.includes('onnx') || k.includes('xenova')) {
            await caches.delete(k);
          }
        }
      }
      console.log('[RAG] Model cache cleared.');
    }
  }

  return new RagEngine();
});

