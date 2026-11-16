/**
 * UVM 1.2 Documentation - Graph-Enhanced Client-Side RAG Engine (V2)
 * Features:
 * - Local query embedding generation via Transformers.js (ONNX Runtime Web / WASM)
 * - Asymmetric queryPrefix support (e.g. BGE-Small-EN)
 * - Bilingual FR -> EN query normalization & UVM entity extraction
 * - 5-Profile Intent Router (SYMBOL_API, INHERITED_MEMBER, COMPARISON, PRACTICAL_EXAMPLE, CONCEPTUAL)
 * - Multi-field BM25 + Vector Cosine Hybrid Fusion
 * - Dynamic OOP Inheritance Resolution via data/rag_graph.json (C.ancestors -> A::M)
 * - Graph Structural Reranking, Edge Score Propagation & Diversified Top-K (promoting Overviews & Examples)
 * - Context Bundle Assembly (inheritance chain, signatures, overrides, cross-links, A vs B comparison)
 * - RAM Memory Management & Cache API management
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
    AUTO_SEMANTIC: 'uvm_rag_auto_semantic',
    DISPLAY_MODE: 'uvm_rag_display_mode'
  };

  const DEFAULT_MODELS = [
    {
      id: 'all-minilm-l6-v2',
      name: 'MiniLM-L6 (Balanced & Fast)',
      description: 'Standard general-purpose model ideal for technical documentation.',
      dimension: 384,
      downloadSize: '23 MB',
      ramUsage: '~60 MB',
      speedRating: 5,
      accuracyRating: 4,
      lightnessRating: 5,
      modelPath: 'Xenova/all-MiniLM-L6-v2',
      queryPrefix: '',
      quantized: true,
      recommended: true,
      default: true
    },
    {
      id: 'bge-small-en-v1.5',
      name: 'BGE-Small-EN (High Precision)',
      description: 'High-fidelity BAAI model tuned for technical English.',
      dimension: 384,
      downloadSize: '33 MB',
      ramUsage: '~85 MB',
      speedRating: 4,
      accuracyRating: 5,
      lightnessRating: 4,
      modelPath: 'Xenova/bge-small-en-v1.5',
      queryPrefix: 'Represent this sentence for searching relevant passages: ',
      quantized: true,
      recommended: false,
      default: false
    },
    {
      id: 'bge-micro-v2',
      name: 'BGE-Micro (Ultra-Light)',
      description: 'Minimal footprint, ideal for constrained or slow connections.',
      dimension: 384,
      downloadSize: '14 MB',
      ramUsage: '~35 MB',
      speedRating: 5,
      accuracyRating: 3,
      lightnessRating: 5,
      modelPath: 'TaylorAI/bge-micro-v2',
      queryPrefix: '',
      quantized: true,
      recommended: false,
      default: false
    }
  ];

  // Lightweight FR -> EN technical normalization dictionary
  const FR_TO_EN_RULES = [
    [/\bh[ée]ritage\b|\bh[ée]rite(?:r|nt)?\b/gi, 'inheritance extends parent'],
    [/\bsurcharg(?:e|er|ée?)\b|\bred[ée]fini(?:r|tion)\b/gi, 'override virtual super'],
    [/\bdiff[ée]rence(?:s)?\s+entre\b|\bcomparer\b|\bcomparaison\b/gi, 'difference between compare vs'],
    [/\binterface\s+virtuelle\b/gi, 'virtual interface vif'],
    [/\bs[ée]quenceur\b/gi, 'sequencer'],
    [/\bs[ée]quence(?:s)?\b/gi, 'sequence'],
    [/\bpilote\b/gi, 'driver'],
    [/\bmoniteur\b/gi, 'monitor'],
    [/\bregistre(?:s)?\b/gi, 'register ral uvm_reg'],
    [/\bexemple(?:s)?\b|\bcas\s+d['’]usage\b|\btutoriel\b/gi, 'example testbench usage'],
    [/\bfin\s+de\s+(?:test|simulation)\b|\barr[êe]t\b/gi, 'objection drain time end of test'],
    [/\bcomment\b/gi, 'how to'],
    [/\bpourquoi\b/gi, 'why'],
    [/\bqu['’]est[- ]ce\s+que\b/gi, 'what is'],
    [/\bsynchroniser\b|\bsynchronisation\b/gi, 'synchronize barrier event'],
    [/\bd[ée]pr[ée]ci[ée]e?\b/gi, 'deprecated']
  ];

  const STOP_WORDS = new Set([
    'the', 'and', 'for', 'with', 'that', 'this', 'from', 'into', 'how', 'what', 'why',
    'when', 'where', 'can', 'does', 'are', 'use', 'using', 'between', 'versus', 'uvm',
    'to', 'in', 'on', 'of', 'is', 'it', 'or', 'an', 'as', 'by', 'do', 'be', 'at', 'was',
    'le', 'la', 'les', 'un', 'une', 'des', 'du', 'de', 'et', 'ou', 'au', 'aux', 'en',
    'pour', 'par', 'dans', 'sur', 'avec', 'sans', 'comment', 'pourquoi', 'quel', 'quelle',
    'entre', 'est', 'qui', 'que', 'quoi'
  ]);

  const GENERIC_METHOD_WORDS = new Set([
    'new', 'create', 'set', 'get', 'type', 'name', 'size', 'print', 'copy', 'compare',
    'check', 'report', 'write', 'read', 'run', 'start', 'stop', 'wait', 'connect',
    'register', 'configure', 'build', 'sample', 'clear', 'reset', 'init', 'lock', 'unlock'
  ]);

  class RagEngine {
    constructor() {
      this.models = DEFAULT_MODELS;
      this.prompts = [];
      this.chunks = null;
      this.graph = null;
      this.embeddings = null;
      this.bm25 = null;
      this.docUrlToChunk = null;
      this.loadedModelId = null;
      this.pipeline = null;
      this.isModelLoading = false;
      this.isDataLoading = false;
      this.currentModelId = localStorage.getItem(STORAGE_KEYS.SELECTED_MODEL) || 'all-minilm-l6-v2';
      this.isHybrid = localStorage.getItem(STORAGE_KEYS.HYBRID_ENABLED) !== 'false';
      this.isAutoSemantic = localStorage.getItem(STORAGE_KEYS.AUTO_SEMANTIC) === 'true';
      this.displayMode = localStorage.getItem(STORAGE_KEYS.DISPLAY_MODE) || 'consolidated';
      this.idleTimer = null;
      this.IDLE_TIMEOUT_MS = 3 * 60 * 1000;

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
      if (modelId) this.setModel(modelId);
    }

    getModelConfig(modelId = this.currentModelId) {
      return this.models.find(m => m.id === modelId) || this.models[0];
    }

    setModel(modelId) {
      if (this.currentModelId !== modelId) {
        this.currentModelId = modelId;
        localStorage.setItem(STORAGE_KEYS.SELECTED_MODEL, modelId);
        this.unloadPipeline();
        this.embeddings = null;
        this.loadedModelId = null;
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

    setDisplayMode(mode) {
      this.displayMode = (mode === 'mixed') ? 'mixed' : 'consolidated';
      localStorage.setItem(STORAGE_KEYS.DISPLAY_MODE, this.displayMode);
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
      const modelId = this.currentModelId;
      if (this.chunks && this.embeddings && this.loadedModelId === modelId) return;

      if (this.isDataLoading) {
        while (this.isDataLoading) {
          await new Promise(r => setTimeout(r, 50));
        }
        return;
      }

      this.isDataLoading = true;
      try {
        const binFile = `data/rag_embeddings_${modelId}.bin?v=2.1`;
        const [chunksRes, graphRes, embRes] = await Promise.all([
          this.chunks ? Promise.resolve(null) : fetch('data/rag_chunks.json?v=2.1'),
          this.graph ? Promise.resolve(null) : fetch('data/rag_graph.json?v=2.1').catch(() => null),
          fetch(binFile).then(r => r.ok ? r : fetch('data/rag_embeddings.bin?v=2.1'))
        ]);

        if (chunksRes && !this.chunks) {
          if (!chunksRes.ok) throw new Error('Failed to load rag_chunks.json.');
          this.chunks = await chunksRes.json();
          this.buildIndexes();
        }

        if (graphRes && graphRes.ok && !this.graph) {
          this.graph = await graphRes.json();
          console.log(`[RAG] Loaded relational graph v${this.graph.version}:`, this.graph.stats);
        }

        if (!embRes || !embRes.ok) {
          throw new Error(`Failed to load vector database for model '${modelId}'. Ensure build_rag_embeddings.py has run.`);
        }

        const buffer = await embRes.arrayBuffer();
        this.embeddings = new Float32Array(buffer);
        this.loadedModelId = modelId;
        console.log(`[RAG] Loaded ${this.chunks.length} chunks and vectors for '${modelId}' (${(buffer.byteLength / 1024 / 1024).toFixed(2)} MB).`);
      } finally {
        this.isDataLoading = false;
      }
    }

    /**
     * Precompute multi-field BM25 index and docUrl lookup map
     */
    buildIndexes() {
      const N = this.chunks.length;
      const df = new Map();
      const docFields = new Array(N);
      const docLengths = new Float32Array(N);
      this.docUrlToChunk = new Map();

      let totalLen = 0;

      for (let i = 0; i < N; i++) {
        const c = this.chunks[i];
        if (c.level === 'parent' && c.docUrl && !this.docUrlToChunk.has(c.docUrl)) {
          this.docUrlToChunk.set(c.docUrl, c);
        }

        const titleFreq = this.tokenizeWeighted(c.title, true);
        const sigFreq = this.tokenizeWeighted(c.sig || '', true);
        const metaFreq = this.tokenizeWeighted(
          `${(c.synonyms || []).join(' ')} ${c.class || ''}`,
          true
        );
        const apisFreq = this.tokenizeWeighted((c.coveredApis || []).join(' '), false);
        const textFreq = this.tokenizeWeighted(c.text || '', false);

        // Combined weighted term frequency per chunk
        const tf = new Map();
        const addMap = (m, weight) => {
          for (const [tok, cnt] of m.entries()) {
            tf.set(tok, (tf.get(tok) || 0) + cnt * weight);
          }
        };
        addMap(titleFreq, 6.0);
        addMap(sigFreq, 2.0);
        addMap(metaFreq, 1.8);
        addMap(apisFreq, 0.65);
        addMap(textFreq, 1.0);

        let len = 0;
        for (const [tok, w] of tf.entries()) {
          len += w;
          df.set(tok, (df.get(tok) || 0) + 1);
        }
        docFields[i] = tf;
        docLengths[i] = len;
        totalLen += len;
      }

      const idf = new Map();
      for (const [tok, count] of df.entries()) {
        idf.set(tok, Math.log(1 + (N - count + 0.5) / (count + 0.5)));
      }

      this.bm25 = {
        N,
        avgDocLen: totalLen / Math.max(1, N),
        idf,
        docFields,
        docLengths
      };
    }

    tokenizeWeighted(str, splitSnake = true) {
      const freq = new Map();
      if (!str) return freq;
      const rawTokens = str.toLowerCase().replace(/[^a-z0-9_`]+/g, ' ').trim().split(/\s+/);
      for (const tok of rawTokens) {
        if (!tok || tok.length < 2) continue;
        freq.set(tok, (freq.get(tok) || 0) + 1);
        if (splitSnake && tok.includes('_')) {
          const parts = tok.replace(/^`/, '').split('_');
          for (const p of parts) {
            if (p.length >= 3 && !STOP_WORDS.has(p)) {
              freq.set(p, (freq.get(p) || 0) + 0.45);
            }
          }
        }
      }
      return freq;
    }

    computeBM25Score(chunkIdx, queryTokens) {
      if (!this.bm25 || queryTokens.length === 0) return 0;
      const { avgDocLen, idf, docFields, docLengths } = this.bm25;
      const tfMap = docFields[chunkIdx];
      const dl = docLengths[chunkIdx] || 1;
      const k1 = 1.4;
      const b = 0.65;

      let score = 0;
      for (const tok of queryTokens) {
        const tokIdf = idf.get(tok) || 1.0;
        const tf = tfMap.get(tok) || 0;
        if (tf > 0) {
          score += tokIdf * ((tf * (k1 + 1)) / (tf + k1 * (1 - b + b * (dl / avgDocLen))));
        }
      }
      // Smooth saturation avoiding false 1.000 spikes on single common tokens
      return score > 0 ? Math.min(1.0, score / (score + 1.8 * Math.sqrt(queryTokens.length))) : 0;
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
        let transformers = window.transformers;
        if (!transformers) {
          transformers = await import('https://cdn.jsdelivr.net/npm/@xenova/transformers@2.17.2');
          window.transformers = transformers;
        }

        const { pipeline, env } = transformers;
        env.allowLocalModels = false;
        env.useBrowserCache = true;

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
     * Normalize FR -> EN and expand known domain aliases
     */
    normalizeQuery(rawQuery) {
      let q = (rawQuery || '').trim();
      for (const [regex, replacement] of FR_TO_EN_RULES) {
        q = q.replace(regex, replacement);
      }

      // Expand graph aliases (e.g. vif -> uvm_config_db)
      const aliases = (this.graph && this.graph.aliases) ? this.graph.aliases : {};
      const lower = q.toLowerCase();
      const extraTerms = [];
      for (const [alias, targets] of Object.entries(aliases)) {
        if (new RegExp(`\\b${alias}\\b`, 'i').test(lower)) {
          extraTerms.push(...targets);
        }
      }

      return {
        raw: rawQuery.trim(),
        normalized: extraTerms.length > 0 ? `${q} ${extraTerms.join(' ')}` : q
      };
    }

    /**
     * Extract UVM classes, methods, macros and classify query into one of 5 intent profiles
     */
    classifyIntent(rawQuery, normQuery) {
      const classesNode = (this.graph && this.graph.nodes && this.graph.nodes.classes) || {};
      const methodsIdx = (this.graph && this.graph.nodes && this.graph.nodes.methodsIndex) || {};
      const macrosNode = (this.graph && this.graph.nodes && this.graph.nodes.macros) || {};

      const tokens = normQuery.toLowerCase().replace(/[^a-z0-9_`]+/g, ' ').trim().split(/\s+/).filter(Boolean);
      const targetClasses = [];
      const targetMethods = [];
      const targetMacros = [];

      for (const tok of tokens) {
        const cleanTok = tok.replace(/^`/, '');
        if (classesNode[cleanTok] && !targetClasses.includes(cleanTok)) {
          targetClasses.push(cleanTok);
        }
        if (methodsIdx[cleanTok] && !targetMethods.includes(cleanTok)) {
          targetMethods.push(cleanTok);
        }
        if ((macrosNode[`\`${cleanTok}`] || tok.startsWith('`')) && !targetMacros.includes(`\`${cleanTok}`)) {
          targetMacros.push(`\`${cleanTok}`);
        }
      }

      const hasScopeOp = rawQuery.includes('::') || rawQuery.includes('`');
      const isComparisonSyntax = /\b(vs\.?|versus|difference\s+between|diff[ée]rence\s+entre|compare)\b/i.test(rawQuery);
      const isExampleSyntax = /\b(example|exemple|testbench|snippet|how\s+to\s+use|tutorial|tutoriel|demo)\b/i.test(normQuery);
      const isConceptualSyntax = /^(how|what|why|where|when|explain|overview|describe|understanding|comment|pourquoi|qu['’]est)/i.test(rawQuery.trim());

      let profile = 'CONCEPTUAL';
      let weights = { vec: 0.65, bm25: 0.25, graph: 0.10 };
      let isSurgicalSymbol = false;

      const meaningfulMethods = targetMethods.filter(m =>
        !GENERIC_METHOD_WORDS.has(m) || (!isConceptualSyntax && tokens.length <= 4)
      );

      if (isComparisonSyntax || (targetClasses.length >= 2 && !isConceptualSyntax && tokens.length <= 6)) {
        profile = 'COMPARISON';
        weights = { vec: 0.50, bm25: 0.25, graph: 0.25 };
      } else if (targetClasses.length === 1 && meaningfulMethods.length >= 1 && !hasScopeOp && (!isConceptualSyntax || tokens.length <= 4)) {
        const clsInfo = classesNode[targetClasses[0]];
        const mName = meaningfulMethods[0];
        if (clsInfo && !(clsInfo.ownMethods || []).includes(mName)) {
          profile = 'INHERITED_MEMBER';
          weights = { vec: 0.45, bm25: 0.30, graph: 0.25 };
        } else {
          profile = 'SYMBOL_API';
          weights = { vec: 0.40, bm25: 0.45, graph: 0.15 };
          isSurgicalSymbol = true;
        }
      } else if (isExampleSyntax) {
        profile = 'PRACTICAL_EXAMPLE';
        weights = { vec: 0.55, bm25: 0.25, graph: 0.20 };
      } else if (hasScopeOp || targetMacros.length > 0 || (tokens.length <= 2 && (targetClasses.length > 0 || targetMethods.length > 0))) {
        profile = 'SYMBOL_API';
        weights = { vec: 0.40, bm25: 0.45, graph: 0.15 };
        isSurgicalSymbol = hasScopeOp || targetMacros.length > 0 || (targetMethods.length > 0 && targetClasses.length === 0);
      } else if (isConceptualSyntax) {
        profile = 'CONCEPTUAL';
        weights = { vec: 0.65, bm25: 0.25, graph: 0.10 };
      }

      return {
        profile,
        weights,
        isSurgicalSymbol,
        targetClasses,
        targetMethods: meaningfulMethods.length > 0 ? meaningfulMethods : targetMethods,
        targetMacros,
        queryTokens: tokens.filter(t => t.length >= 2 && !STOP_WORDS.has(t))
      };
    }

    /**
     * Resolve inherited methods dynamically by walking C.ancestors in data/rag_graph.json
     */
    resolveInheritedMatches(intent) {
      if (!this.graph || !this.graph.nodes || intent.targetClasses.length === 0 || intent.targetMethods.length === 0) {
        return [];
      }
      const classesNode = this.graph.nodes.classes || {};
      const methodsIdx = this.graph.nodes.methodsIndex || {};
      const syntheticHits = [];

      for (const clsName of intent.targetClasses) {
        const clsInfo = classesNode[clsName];
        if (!clsInfo) continue;

        for (const mName of intent.targetMethods) {
          if ((clsInfo.ownMethods || []).includes(mName)) continue; // Already on class

          const candidates = methodsIdx[mName] || [];
          // Walk ancestors nearest-first
          for (const anc of (clsInfo.ancestors || [])) {
            const match = candidates.find(c => c.class === anc);
            if (match && this.chunks[match.chunkId]) {
              const ancChunk = this.chunks[match.chunkId];
              const overrideInfo = (clsInfo.overrides || {})[mName];
              syntheticHits.push({
                targetClass: clsName,
                ancestorClass: anc,
                methodName: mName,
                chunk: ancChunk,
                sig: match.sig,
                callsSuper: overrideInfo ? overrideInfo.callsSuper : match.callsSuper,
                isVirtual: match.virtual,
                isPureVirtual: match.pureVirtual
              });
              break;
            }
          }
        }
      }
      return syntheticHits;
    }

    /**
     * Multi-Location Smart Snippet Extractor
     */
    extractMultiLocationSnippet(parentText, childChunks, query) {
      if (!parentText && (!childChunks || childChunks.length === 0)) return '';

      const queryTokens = (query || '').toLowerCase()
        .replace(/[^a-z0-9_`]/g, ' ')
        .split(/\s+/)
        .filter(t => t.length > 2);

      const stripDupTitlePrefix = (s) => {
        if (!s) return '';
        let out = s.trim();
        const colonM = out.match(/^([^:]{3,60}):\s*\1\b/i);
        if (colonM) out = out.slice(colonM[1].length + 1).trim();
        return out;
      };

      const scoreSentences = (text, sourceTag) => {
        if (!text) return [];
        const raw = stripDupTitlePrefix(text).split(/(?<=[.!?])\s+(?=[A-Z0-9`])/);
        const list = [];
        raw.forEach((sentence, idx) => {
          const clean = sentence.trim();
          if (clean.length < 25) return;
          const lower = clean.toLowerCase();
          let score = 0;
          queryTokens.forEach(t => {
            if (lower.includes(t)) {
              score += 2;
              if (new RegExp(`\\b${t}\\b`, 'i').test(clean)) score += 3;
            }
          });
          if (sourceTag === 'Intro' && idx < 3) score += 1.5;
          list.push({ sentence: clean, score, idx, sourceTag });
        });
        return list;
      };

      const introSentences = scoreSentences(parentText, 'Intro');
      introSentences.sort((a, b) => b.score - a.score);
      const bestIntro = introSentences.length > 0 ? introSentences[0] : null;

      const childCandidates = [];
      if (childChunks && childChunks.length > 0) {
        childChunks.forEach(c => {
          const rawName = c.rawTitle || (c.title ? c.title.split('::').pop() : 'Section');
          const sents = scoreSentences(c.text, rawName);
          childCandidates.push(...sents);
        });
        childCandidates.sort((a, b) => b.score - a.score);
      }
      const bestChild = childCandidates.length > 0 ? childCandidates[0] : null;

      if (bestIntro && bestChild && bestIntro.sentence !== bestChild.sentence) {
        const hIntro = this.highlightSnippet(bestIntro.sentence.slice(0, 190), query);
        const hChild = this.highlightSnippet(bestChild.sentence.slice(0, 190), query);
        return `<span class="snippet-source-tag">[Intro]</span> ${hIntro} ` +
               `<span class="snippet-source-tag">[${this.escapeHtml(bestChild.sourceTag)}]</span> ${hChild}`;
      }

      if (bestIntro) {
        const topIntro = introSentences.slice(0, 2).sort((a, b) => a.idx - b.idx);
        const combined = topIntro.map(s => s.sentence).join(' ');
        return `<span class="snippet-source-tag">[Intro]</span> ${this.highlightSnippet(combined.slice(0, 280), query)}`;
      }

      if (bestChild) {
        return `<span class="snippet-source-tag">[${this.escapeHtml(bestChild.sourceTag)}]</span> ${this.highlightSnippet(bestChild.sentence.slice(0, 280), query)}`;
      }

      return this.highlightSnippet((parentText || '').slice(0, 220), query);
    }

    extractSmartSnippet(chunkText, query) {
      if (!chunkText) return '';
      const clean = chunkText.trim();
      const rawSentences = clean.split(/(?<=[.!?])\s+(?=[A-Z0-9`])/);
      if (rawSentences.length <= 1) {
        return this.highlightSnippet(clean.slice(0, 220), query);
      }

      const queryTokens = query.toLowerCase()
        .replace(/[^a-z0-9_`]/g, ' ')
        .split(/\s+/)
        .filter(t => t.length > 2);

      if (queryTokens.length === 0) {
        return this.highlightSnippet(rawSentences.slice(0, 2).join(' '), query);
      }

      const bestSentences = [];
      rawSentences.forEach((sentence, idx) => {
        const lower = sentence.toLowerCase();
        let score = 0;
        queryTokens.forEach(t => {
          if (lower.includes(t)) {
            score += 2;
            if (new RegExp(`\\b${t}\\b`, 'i').test(sentence)) score += 3;
          }
        });
        if (score > 0) bestSentences.push({ sentence, score, idx });
      });

      if (bestSentences.length === 0) {
        return this.highlightSnippet(rawSentences.slice(0, 2).join(' '), query);
      }

      bestSentences.sort((a, b) => b.score - a.score);
      const topSelected = bestSentences.slice(0, 2).sort((a, b) => a.idx - b.idx);
      const combined = topSelected.map(s => s.sentence).join(' ');
      return this.highlightSnippet(combined.slice(0, 260), query);
    }

    highlightSnippet(text, query) {
      if (!text) return '';
      const queryTokens = (query || '')
        .toLowerCase()
        .replace(/[^a-z0-9_`]+/g, ' ')
        .trim()
        .split(/\s+/)
        .filter(t => t.length > 2)
        .sort((a, b) => b.length - a.length);
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
     * Build Context Bundle (inheritance breadcrumb, signature, badges, cross-links) for a result
     */
    buildContextBundle(chunk, targetChildChunk, inheritedMeta = null) {
      if (!this.graph || !this.graph.nodes) return null;

      const classesNode = this.graph.nodes.classes || {};
      const examplesNode = this.graph.nodes.examples || {};
      const macrosNode = this.graph.nodes.macros || {};

      const clsName = inheritedMeta ? inheritedMeta.targetClass : (chunk.class || chunk.title);
      const clsInfo = classesNode[clsName];

      let inheritanceChain = [];
      let signature = (targetChildChunk && targetChildChunk.sig) || chunk.sig || '';
      const badges = [];
      const crossLinks = {
        macros: [],
        examples: [],
        relatedClasses: []
      };

      if (clsInfo) {
        const chainNames = [...(clsInfo.ancestors || []).slice().reverse(), clsName];
        inheritanceChain = chainNames
          .filter(n => n !== 'uvm_void' || chainNames.length <= 2)
          .map(n => {
            const info = classesNode[n];
            return {
              name: n,
              url: info && info.docUrl ? `${info.docUrl}#MainTopic` : null,
              current: n === clsName
            };
          });

        if (clsInfo.isDeprecated) badges.push('deprecated');
        if (clsInfo.isVirtual && chunk.type === 'class') badges.push('virtual');

        // Related examples
        for (const exUrl of (clsInfo.relatedExamples || []).slice(0, 2)) {
          const exMeta = examplesNode[exUrl];
          if (exMeta) {
            crossLinks.examples.push({ title: exMeta.title, url: `${exUrl}#MainTopic` });
          }
        }

        // Related macros
        for (const macName of (clsInfo.relatedMacros || []).slice(0, 2)) {
          const mInfo = macrosNode[macName];
          if (mInfo && mInfo.docUrl) {
            crossLinks.macros.push({ name: macName, url: mInfo.docUrl });
          }
        }

        // Co-occurring classes
        for (const peer of (clsInfo.coOccursWith || []).slice(0, 3)) {
          const pInfo = classesNode[peer];
          if (pInfo && pInfo.docUrl) {
            crossLinks.relatedClasses.push({ name: peer, url: `${pInfo.docUrl}#MainTopic` });
          }
        }
      } else if (chunk.type === 'example' && examplesNode[chunk.docUrl]) {
        const exInfo = examplesNode[chunk.docUrl];
        for (const api of (exInfo.apis || []).slice(0, 4)) {
          if (classesNode[api] && classesNode[api].docUrl) {
            crossLinks.relatedClasses.push({ name: api, url: `${classesNode[api].docUrl}#MainTopic` });
          }
        }
      }

      if (inheritedMeta) {
        badges.push(`inherited from ${inheritedMeta.ancestorClass}`);
        if (inheritedMeta.isPureVirtual) badges.push('pure virtual');
        else if (inheritedMeta.isVirtual) badges.push('virtual');
        if (inheritedMeta.callsSuper) badges.push('calls_super');
        signature = inheritedMeta.sig || signature;
      }

      return {
        inheritanceChain,
        inheritedFrom: inheritedMeta ? {
          className: inheritedMeta.ancestorClass,
          method: inheritedMeta.methodName
        } : null,
        signature,
        badges,
        crossLinks
      };
    }

    /**
     * Main Semantic & Graph-Enhanced Search function
     */
    async search(query, options = {}) {
      const topK = options.topK || 20;
      const onProgress = options.onProgress || null;
      const displayMode = options.displayMode || this.displayMode;

      if (!query || !query.trim()) return [];

      this.resetIdleTimer();

      await Promise.all([
        this.loadData(),
        this.loadModel(onProgress)
      ]);

      const { raw, normalized } = this.normalizeQuery(query);
      const intent = this.classifyIntent(raw, normalized);

      // Apply model-specific asymmetric query prefix (e.g., BGE-Small-EN)
      const modelCfg = this.getModelConfig();
      const queryPrefix = modelCfg.queryPrefix || '';
      const embedInput = queryPrefix ? `${queryPrefix}${normalized}` : normalized;

      const output = await this.pipeline(embedInput, { pooling: 'mean', normalize: true });
      const queryVec = output.data;

      const dim = 384;
      const totalChunks = this.chunks.length;
      const emb = this.embeddings;
      const scored = new Array(totalChunks);

      const wVec = intent.weights.vec;
      const wBm25 = intent.weights.bm25;

      for (let i = 0; i < totalChunks; i++) {
        let dot = 0.0;
        const offset = i * dim;
        for (let d = 0; d < dim; d++) {
          dot += queryVec[d] * emb[offset + d];
        }

        let hybridScore = dot;
        if (this.isHybrid && intent.queryTokens.length > 0) {
          const bm25Score = this.computeBM25Score(i, intent.queryTokens);
          const denom = wVec + wBm25;
          hybridScore = ((dot * wVec) + (bm25Score * wBm25)) / (denom || 1);
        }

        scored[i] = { index: i, score: hybridScore, vectorScore: dot, chunk: this.chunks[i] };
      }

      scored.sort((a, b) => b.score - a.score);

      if (displayMode === 'mixed') {
        return this.formatMixedResults(scored, raw, intent, topK);
      }
      return this.formatConsolidatedResults(scored, raw, intent, topK);
    }

    /**
     * Option A: Graph-Reranked Parent-Child Consolidation with Overview/Example Promotion & Context Bundles
     */
    formatConsolidatedResults(scored, rawQuery, intent, topK) {
      const docsMap = new Map();
      const classesNode = (this.graph && this.graph.nodes && this.graph.nodes.classes) || {};
      const overviewsNode = (this.graph && this.graph.nodes && this.graph.nodes.overviews) || {};
      const overviewMeta = (this.graph && this.graph.nodes && this.graph.nodes.overviewMeta) || {};
      const examplesMeta = (this.graph && this.graph.nodes && this.graph.nodes.examples) || {};

      // Collect top 300 chunk candidates
      const poolLimit = Math.min(scored.length, 300);
      for (let i = 0; i < poolLimit; i++) {
        const item = scored[i];
        const chunk = item.chunk;
        const docUrl = chunk.docUrl || chunk.url.split('#')[0];

        if (!docsMap.has(docUrl)) {
          docsMap.set(docUrl, {
            docUrl,
            parentChunk: chunk.level === 'parent' ? chunk : null,
            parentScore: chunk.level === 'parent' ? item.score : null,
            parentVectorScore: chunk.level === 'parent' ? item.vectorScore : null,
            children: [],
            topScore: item.score
          });
        }

        const entry = docsMap.get(docUrl);
        if (chunk.level === 'parent' && !entry.parentChunk) {
          entry.parentChunk = chunk;
          entry.parentScore = item.score;
          entry.parentVectorScore = item.vectorScore;
        } else if (chunk.level === 'child') {
          entry.children.push(item);
        }
        if (item.score > entry.topScore) {
          entry.topScore = item.score;
        }
      }

      // Ensure Overviews & Examples linked to high-scoring pillar classes are included in docsMap (Edge Score Propagation)
      const ensureLinkedDoc = (docUrl, propagatedScore) => {
        if (!docUrl) return;
        const pChunk = this.docUrlToChunk ? this.docUrlToChunk.get(docUrl) : null;
        if (!pChunk) return;
        if (!docsMap.has(docUrl)) {
          docsMap.set(docUrl, {
            docUrl,
            parentChunk: pChunk,
            parentScore: propagatedScore,
            parentVectorScore: propagatedScore,
            children: [],
            topScore: propagatedScore,
            propagated: true
          });
        } else {
          const ex = docsMap.get(docUrl);
          if (propagatedScore > (ex.parentScore || 0)) {
            ex.parentScore = propagatedScore;
            ex.topScore = Math.max(ex.topScore, propagatedScore);
          }
        }
      };

      const rawResults = [];
      for (const [docUrl, entry] of docsMap.entries()) {
        let pChunk = entry.parentChunk;
        if (!pChunk) {
          pChunk = (this.docUrlToChunk && this.docUrlToChunk.get(docUrl)) ||
                   (entry.children.length > 0 ? entry.children[0].chunk : null);
        }
        if (!pChunk) continue;

        let effectiveParentScore = (entry.parentScore !== null) ? entry.parentScore : (entry.topScore * 0.78);
        const pType = pChunk.type || (docUrl.includes('examples_view/') ? 'example' : 'class');
        const clsName = pChunk.class || pChunk.title;
        const clsLower = (clsName || '').toLowerCase();

        // Exact Target Class Boost: when query explicitly names class C, ensure C leads
        if (pType === 'class' && intent.targetClasses.includes(clsLower)) {
          effectiveParentScore += (intent.profile === 'SYMBOL_API') ? 0.22 : 0.12;
        }

        // Gentle, profile-aware type priors (never overriding semantic relevance)
        if (pType === 'overview') {
          if (intent.profile === 'CONCEPTUAL' || intent.profile === 'COMPARISON') effectiveParentScore += 0.08;
          else if (intent.profile === 'PRACTICAL_EXAMPLE') effectiveParentScore += 0.03;
        } else if (pType === 'example') {
          if (intent.profile === 'PRACTICAL_EXAMPLE') effectiveParentScore += 0.12;
          else if (intent.profile === 'CONCEPTUAL' || intent.profile === 'COMPARISON') effectiveParentScore += 0.04;
        }

        entry.children.sort((a, b) => b.score - a.score);
        const topChildren = entry.children.slice(0, 3);
        const bestChild = topChildren.length > 0 ? topChildren[0] : null;
        let cScore = bestChild ? bestChild.score : effectiveParentScore;

        if (bestChild && (bestChild.chunk.type === 'stepper' || bestChild.chunk.type === 'studio')) {
          cScore += (intent.profile === 'PRACTICAL_EXAMPLE') ? 0.08 : 0.02;
        }

        let combinedScore = (Math.max(effectiveParentScore, cScore) * 0.65) + (Math.min(effectiveParentScore, cScore) * 0.35);

        // Graph structural reranking (gentle centrality, deprecated, internal)
        const clsInfo = classesNode[clsName];
        if (clsInfo) {
          combinedScore *= (0.92 + 0.14 * (clsInfo.centrality || 0.5));
          const exactDepRequested = intent.queryTokens.includes(clsLower);
          if (clsInfo.isDeprecated && !exactDepRequested) {
            combinedScore *= 0.45;
          } else if (clsInfo.isInternal && intent.profile !== 'SYMBOL_API') {
            combinedScore *= 0.72;
          }
        } else if (pType === 'overview' && overviewMeta[docUrl]) {
          combinedScore *= 1.02;
        } else if (pType === 'example' && examplesMeta[docUrl]) {
          combinedScore *= 1.02;
        }

        rawResults.push({
          docUrl,
          pChunk,
          pType,
          effectiveParentScore,
          topChildren,
          bestChild,
          cScore,
          combinedScore,
          vectorScore: entry.parentVectorScore || (bestChild ? bestChild.vectorScore : combinedScore),
          allChildren: entry.children
        });
      }

      // Edge Score Propagation from top 2 pillar classes to their linked Overviews & specific Examples
      rawResults.sort((a, b) => b.combinedScore - a.combinedScore);
      const topClasses = rawResults.filter(r => r.pType === 'class').slice(0, 2);
      for (const topCls of topClasses) {
        const clsName = topCls.pChunk.class || topCls.pChunk.title;
        const clsInfo = classesNode[clsName];
        if (!clsInfo || clsInfo.isDeprecated || clsInfo.isInternal) continue;

        const propScore = topCls.combinedScore * 0.74;
        for (const ovUrl of (overviewsNode[clsName] || clsInfo.relatedOverviews || []).slice(0, 1)) {
          const existing = rawResults.find(r => r.docUrl === ovUrl);
          if (existing) {
            existing.combinedScore = Math.max(existing.combinedScore, propScore);
          } else {
            ensureLinkedDoc(ovUrl, propScore);
          }
        }
        for (const exUrl of (clsInfo.relatedExamples || []).slice(0, 1)) {
          const existing = rawResults.find(r => r.docUrl === exUrl);
          if (existing) {
            existing.combinedScore = Math.max(existing.combinedScore, propScore);
          } else {
            ensureLinkedDoc(exUrl, propScore);
          }
        }
      }

      // Inject any newly propagated overviews/examples that weren't in rawResults yet
      for (const [docUrl, entry] of docsMap.entries()) {
        if (entry.propagated && !rawResults.some(r => r.docUrl === docUrl)) {
          const pChunk = entry.parentChunk;
          const pType = pChunk.type || (docUrl.includes('examples_view/') ? 'example' : 'overview');
          rawResults.push({
            docUrl,
            pChunk,
            pType,
            effectiveParentScore: entry.parentScore,
            topChildren: [],
            bestChild: null,
            cScore: entry.parentScore,
            combinedScore: entry.parentScore,
            vectorScore: entry.parentVectorScore,
            allChildren: []
          });
        }
      }

      rawResults.sort((a, b) => b.combinedScore - a.combinedScore);

      // Dynamic OOP Inheritance Resolution: prepend synthetic contextualized hits if applicable
      const inheritedHits = this.resolveInheritedMatches(intent);
      const formattedResults = [];
      const seenInheritedUrls = new Set();

      for (const inh of inheritedHits) {
        const synUrl = inh.chunk.url;
        if (seenInheritedUrls.has(synUrl)) continue;
        seenInheritedUrls.add(synUrl);

        const topScore = rawResults.length > 0 ? rawResults[0].combinedScore : 0.85;
        const inhScore = Math.max(0.88, topScore + 0.04);
        const matchPct = Math.round(Math.max(0, Math.min(1, (inhScore + 0.15) / 1.1)) * 100);
        const contextBundle = this.buildContextBundle(inh.chunk, inh.chunk, inh);

        formattedResults.push({
          mode: 'consolidated',
          score: inhScore,
          vectorScore: inhScore,
          matchPct,
          chunk: inh.chunk,
          children: [],
          targetUrl: synUrl,
          targetSections: [{ title: inh.methodName, url: synUrl, type: inh.chunk.type, isIntro: false }],
          targetType: inh.chunk.type || 'method',
          type: inh.chunk.type || 'method',
          title: `${inh.targetClass}::${inh.methodName} (hérité de ${inh.ancestorClass})`,
          pageHeading: inh.chunk.pageHeading || inh.ancestorClass,
          category: inh.chunk.category,
          breadcrumb: `${inh.chunk.category} > ${inh.targetClass} > (via ${inh.ancestorClass}) > ${inh.methodName}`,
          snippet: `<span class="snippet-source-tag">[Hérité de ${this.escapeHtml(inh.ancestorClass)}]</span> ${this.extractSmartSnippet(inh.chunk.text, rawQuery)}`,
          highlightedTitle: this.highlightSnippet(`${inh.targetClass}::${inh.methodName}`, rawQuery) + ` <span class="rag-inherited-suffix">(via ${this.escapeHtml(inh.ancestorClass)})</span>`,
          contextBundle,
          intentProfile: intent.profile
        });
      }

      // Diversified Top-5 selection: ensure relevant Overviews/Examples are visible without displacing #1 symbol match
      let orderedPool = rawResults;
      const topScoreFloor = rawResults.length > 0 ? rawResults[0].combinedScore * 0.62 : 0;
      const hasStrongOverviewOrEx = rawResults.some(
        it => (it.pType === 'overview' || it.pType === 'example') && it.combinedScore >= topScoreFloor
      );
      if (!intent.isSurgicalSymbol && hasStrongOverviewOrEx && rawResults.length > 4) {
        const topFive = [];
        const deferred = [];
        let apiCount = 0;

        for (const item of rawResults) {
          if (topFive.length < 5) {
            const isRawApi = (item.pType === 'class' || item.pType === 'method' || item.pType === 'function' || item.pType === 'task');
            if (isRawApi && apiCount >= 3) {
              deferred.push(item);
              continue;
            }
            if ((item.pType === 'overview' || item.pType === 'example') && item.combinedScore < topScoreFloor) {
              deferred.push(item);
              continue;
            }
            if (isRawApi) apiCount++;
            topFive.push(item);
          } else {
            deferred.push(item);
          }
        }
        // Fill remaining Top-5 slots from deferred if fewer than 5 items selected
        while (topFive.length < 5 && deferred.length > 0) {
          topFive.push(deferred.shift());
        }
        orderedPool = [...topFive, ...deferred];
      }

      for (const r of orderedPool) {
        const { pChunk, pType, effectiveParentScore, topChildren, bestChild, cScore, combinedScore, vectorScore, allChildren } = r;

        const targetSections = [];
        if (effectiveParentScore >= (cScore - 0.12)) {
          targetSections.push({ title: 'Intro', url: pChunk.url, type: 'overview', isIntro: true });
        }

        const childThreshold = bestChild ? bestChild.score * 0.72 : 0;
        topChildren.forEach(childItem => {
          if (childItem.score >= childThreshold) {
            targetSections.push({
              title: childItem.chunk.rawTitle || (childItem.chunk.title ? childItem.chunk.title.split('::').pop() : 'Section'),
              url: childItem.chunk.url,
              type: childItem.chunk.type,
              isIntro: false
            });
          }
        });

        const targetUrl = (bestChild && bestChild.score > (effectiveParentScore + 0.08)) ? bestChild.chunk.url : pChunk.url;
        const childChunks = topChildren.map(c => c.chunk);
        const snippet = this.extractMultiLocationSnippet(pChunk.text, childChunks, rawQuery);
        const matchPct = Math.round(Math.max(0, Math.min(1, (combinedScore + 0.2) / 1.1)) * 100);

        let tType = pType;
        if (bestChild && bestChild.chunk && bestChild.chunk.type) {
          tType = bestChild.chunk.type;
        }

        const contextBundle = this.buildContextBundle(pChunk, bestChild ? bestChild.chunk : null, null);

        formattedResults.push({
          mode: 'consolidated',
          score: combinedScore,
          vectorScore,
          matchPct,
          chunk: pChunk,
          children: allChildren,
          targetUrl,
          targetSections,
          targetType: tType,
          type: pType,
          title: pChunk.title,
          pageHeading: pChunk.pageHeading || pChunk.title,
          category: pChunk.category,
          breadcrumb: pChunk.breadcrumb,
          snippet,
          highlightedTitle: this.highlightSnippet(pChunk.title, rawQuery),
          contextBundle,
          intentProfile: intent.profile
        });

        if (formattedResults.length >= topK) break;
      }

      return formattedResults.slice(0, topK);
    }

    /**
     * Option B: Mixed Results with Strict Single-Page Deduplication & Context Bundles
     */
    formatMixedResults(scored, rawQuery, intent, topK) {
      const results = [];
      const seenDocs = new Set();

      for (const item of scored) {
        const chunk = item.chunk;
        const docUrl = chunk.docUrl || chunk.url.split('#')[0];

        if (seenDocs.has(docUrl)) continue;
        seenDocs.add(docUrl);

        const snippet = this.extractSmartSnippet(chunk.text, rawQuery);
        const matchPct = Math.round(Math.max(0, Math.min(1, (item.score + 0.2) / 1.1)) * 100);
        const chunkType = chunk.type || (chunk.url && chunk.url.includes('examples_view/') ? 'example' : 'class');
        const contextBundle = this.buildContextBundle(chunk, chunk, null);

        results.push({
          mode: 'mixed',
          score: item.score,
          vectorScore: item.vectorScore,
          matchPct,
          chunk,
          targetChunk: chunk,
          targetUrl: chunk.url,
          targetSectionTitle: null,
          targetType: chunkType,
          type: chunkType,
          title: chunk.title,
          pageHeading: chunk.title,
          category: chunk.category,
          breadcrumb: chunk.breadcrumb,
          snippet,
          highlightedTitle: this.highlightSnippet(chunk.title, rawQuery),
          contextBundle,
          intentProfile: intent.profile
        });

        if (results.length >= topK) break;
      }

      return results;
    }

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
