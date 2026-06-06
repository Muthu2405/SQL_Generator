import { useState, useEffect, useRef } from 'react';
import {
  Database,
  Terminal,
  Settings,
  Play,
  Copy,
  Check,
  Trash2,
  History,
  AlertCircle,
  RefreshCw,
  X,
  FileCode,
  Sliders,
} from 'lucide-react';

const DEFAULT_BACKEND_URL = 'http://localhost:8000';

function App() {
  // --- States ---
  const [query, setQuery] = useState('');
  const [dialect, setDialect] = useState('postgresql');
  const [explain, setExplain] = useState(false);
  const [model, setModel] = useState('claude-sonnet-4-6');
  const [maxTokens, setMaxTokens] = useState(1024);
  const [serverUrl, setServerUrl] = useState(DEFAULT_BACKEND_URL);
  const [apiKey, setApiKey] = useState(() => localStorage.getItem('sqlgen_api_key') || '');
  const [provider, setProvider] = useState(() => localStorage.getItem('sqlgen_provider') || 'anthropic');
  const [ollamaHost, setOllamaHost] = useState(() => localStorage.getItem('sqlgen_ollama_host') || 'http://localhost:11434');
  
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [copied, setCopied] = useState(false);
  const [showSettings, setShowSettings] = useState(false);
  const [isInputFocused, setIsInputFocused] = useState(false);
  
  // Health & Server connection status
  const [backendHealthy, setBackendHealthy] = useState(null); // null = loading, true = ok, false = offline
  const [apiKeyConfigured, setApiKeyConfigured] = useState(false);
  
  // History list (persisted in localStorage)
  const [historyList, setHistoryList] = useState(() => {
    try {
      const saved = localStorage.getItem('sqlgen_history');
      return saved ? JSON.parse(saved) : [];
    } catch {
      return [];
    }
  });

  const textareaRef = useRef(null);

  // --- Effects ---
  // Sync history list to localStorage
  useEffect(() => {
    localStorage.setItem('sqlgen_history', JSON.stringify(historyList));
  }, [historyList]);

  // Sync API Key to localStorage
  useEffect(() => {
    localStorage.setItem('sqlgen_api_key', apiKey);
  }, [apiKey]);

  // Sync Provider to localStorage
  useEffect(() => {
    localStorage.setItem('sqlgen_provider', provider);
  }, [provider]);

  // Sync Ollama Host to localStorage
  useEffect(() => {
    localStorage.setItem('sqlgen_ollama_host', ollamaHost);
  }, [ollamaHost]);

  // Health check on load and periodic polling
  const checkHealth = async (url) => {
    try {
      const res = await fetch(`${url}/api/health`);
      if (res.ok) {
        const data = await res.json();
        setBackendHealthy(data.status === 'healthy');
        setApiKeyConfigured(data.api_key_configured);
      } else {
        setBackendHealthy(false);
        setApiKeyConfigured(false);
      }
    } catch {
      setBackendHealthy(false);
      setApiKeyConfigured(false);
    }
  };

  useEffect(() => {
    checkHealth(serverUrl);
    const interval = setInterval(() => checkHealth(serverUrl), 8000);
    return () => clearInterval(interval);
  }, [serverUrl]);

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`;
    }
  }, [query]);

  // --- SQL Syntax Highlighting Helper ---
  const highlightSQL = (sqlCode) => {
    if (!sqlCode) return '';
    
    // HTML Escape to prevent XSS
    let escaped = sqlCode
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;');

    // List of common SQL keywords
    const keywords = [
      'SELECT', 'FROM', 'WHERE', 'JOIN', 'LEFT', 'RIGHT', 'INNER', 'OUTER', 'ON',
      'AND', 'OR', 'GROUP BY', 'ORDER BY', 'LIMIT', 'INSERT', 'UPDATE', 'DELETE',
      'CREATE', 'TABLE', 'ALTER', 'DROP', 'INDEX', 'VIEW', 'WITH', 'AS', 'HAVING',
      'UNION', 'ALL', 'IN', 'ANY', 'SOME', 'EXISTS', 'LIKE', 'ILIKE', 'NOT', 'NULL',
      'IS', 'TRUE', 'FALSE', 'INTERVAL', 'NOW', 'DATE', 'CASE', 'WHEN', 'THEN',
      'ELSE', 'END', 'OVER', 'PARTITION BY', 'ROWS', 'RANGE', 'PRECEDING', 'FOLLOWING',
      'RETURNING', 'DISTINCT', 'COUNT', 'SUM', 'AVG', 'MIN', 'MAX'
    ];

    // Highlight strings (single quotes)
    escaped = escaped.replace(/('[^']*')/g, '<span class="sql-string">$1</span>');
    // Highlight strings (double quotes)
    escaped = escaped.replace(/("[^"]*")/g, '<span class="sql-string">$1</span>');
    
    // Highlight numbers
    escaped = escaped.replace(/\b(\d+)\b/g, '<span class="sql-number">$1</span>');

    // Highlight keywords
    keywords.forEach((keyword) => {
      const regex = new RegExp(`\\b(${keyword})\\b`, 'gi');
      escaped = escaped.replace(regex, '<span class="sql-keyword">$1</span>');
    });

    // Highlight single line comments
    escaped = escaped.replace(/(--.*?)(?=\n|$)/g, '<span class="sql-comment">$1</span>');

    return escaped;
  };

  // --- API Handlers ---
  const handleGenerate = async (e) => {
    if (e) e.preventDefault();
    if (!query.trim() || isLoading) return;

    setIsLoading(true);
    setError(null);
    setResult(null);

    try {
      const response = await fetch(`${serverUrl}/api/generate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          query: query.trim(),
          dialect,
          explain,
          model,
          max_tokens: maxTokens,
          api_key: provider === 'anthropic' ? (apiKey.trim() || undefined) : undefined,
          provider,
          ollama_host: provider === 'ollama' ? (ollamaHost.trim() || undefined) : undefined,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || 'Failed to generate SQL query.');
      }

      const generationResult = {
        sql: data.sql,
        explanation: data.explanation,
      };

      setResult(generationResult);

      // Add to history
      const newHistoryItem = {
        id: Date.now().toString(),
        query: query.trim(),
        dialect,
        explain,
        sql: data.sql,
        explanation: data.explanation,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };
      setHistoryList((prev) => [newHistoryItem, ...prev].slice(0, 50)); // Cap history at 50

    } catch (err) {
      setError(err.message || 'An unexpected error occurred.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleCopy = () => {
    if (!result?.sql) return;
    navigator.clipboard.writeText(result.sql);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleHistoryItemClick = (item) => {
    setQuery(item.query);
    setDialect(item.dialect);
    setExplain(item.explain);
    setResult({ sql: item.sql, explanation: item.explanation });
    setError(null);
  };

  const deleteHistoryItem = (id, e) => {
    e.stopPropagation();
    setHistoryList((prev) => prev.filter((item) => item.id !== id));
  };

  const clearHistory = () => {
    if (window.confirm('Are you sure you want to clear your query history?')) {
      setHistoryList([]);
    }
  };

  return (
    <div className="app-container">
      {/* Sidebar for Query History */}
      <aside className="app-sidebar">
        <div className="sidebar-header">
          <h2>
            <History size={16} />
            Recent Queries
          </h2>
          <button
            onClick={clearHistory}
            className="clear-history-btn"
            disabled={historyList.length === 0}
            title="Clear all history"
          >
            <Trash2 size={16} />
          </button>
        </div>
        <div className="history-list">
          {historyList.length === 0 ? (
            <div className="history-empty">
              <History size={32} style={{ opacity: 0.3 }} />
              <p>No queries yet</p>
              <span style={{ fontSize: '0.75rem' }}>Your generation history will appear here.</span>
            </div>
          ) : (
            historyList.map((item) => (
              <div
                key={item.id}
                onClick={() => handleHistoryItemClick(item)}
                className={`history-item ${
                  result?.sql === item.sql && query === item.query ? 'active' : ''
                }`}
              >
                <p className="history-query">{item.query}</p>
                <div className="history-meta">
                  <span className={`dialect-badge ${item.dialect}`}>{item.dialect}</span>
                  <span>{item.timestamp}</span>
                  <button
                    onClick={(e) => deleteHistoryItem(item.id, e)}
                    className="clear-history-btn"
                    style={{ padding: '0.125rem' }}
                    title="Delete item"
                  >
                    <X size={12} />
                  </button>
                </div>
              </div>
            ))
          )}
        </div>
      </aside>

      {/* Main Workspace */}
      <main className="main-content">
        {/* Header */}
        <header className="app-header">
          <div className="logo-section">
            <Database className="logo-icon" size={28} />
            <h1>sqlgen</h1>
            <span className="version-badge">v0.1.0</span>
          </div>

          <div className="status-badge" title={backendHealthy ? "Backend connected" : "Backend offline"}>
            <span
              className={`status-dot ${
                backendHealthy === true ? 'healthy' : 'unhealthy'
              }`}
            />
            <span>
              {backendHealthy === true
                ? provider === 'ollama'
                  ? 'Server Connected (Ollama)'
                  : (apiKeyConfigured || apiKey.trim() !== '')
                    ? 'Server Connected (Claude)'
                    : 'Key Missing (Set Key)'
                : 'Server Offline'}
            </span>
            <button
              onClick={() => checkHealth(serverUrl)}
              className="action-icon-btn"
              style={{ width: '20px', height: '20px' }}
              title="Refresh connection status"
            >
              <RefreshCw size={12} />
            </button>
          </div>
        </header>

        {/* Input Card */}
        <div className={`glass-card input-card ${isInputFocused ? 'focused' : ''}`}>
          <form onSubmit={handleGenerate}>
            <div className="textarea-container">
              <textarea
                ref={textareaRef}
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                onFocus={() => setIsInputFocused(true)}
                onBlur={() => setIsInputFocused(false)}
                placeholder="Ask a question in plain English (e.g., 'show all users who signed up in the last 30 days and ordered a product')..."
                className="query-textarea"
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    handleGenerate();
                  }
                }}
              />
              <div className="textarea-footer">
                <span className="char-counter">{query.length} characters</span>
                {query && (
                  <button
                    type="button"
                    onClick={() => setQuery('')}
                    className="clear-input-btn"
                  >
                    <X size={12} />
                    Clear
                  </button>
                )}
              </div>
            </div>

            {/* Config & Controls */}
            <div className="config-row">
              {/* Dialect Tabs */}
              <div className="dialect-tabs">
                <button
                  type="button"
                  onClick={() => setDialect('postgresql')}
                  className={`dialect-tab postgresql ${
                    dialect === 'postgresql' ? 'active' : ''
                  }`}
                >
                  PostgreSQL
                </button>
                <button
                  type="button"
                  onClick={() => setDialect('mysql')}
                  className={`dialect-tab mysql ${dialect === 'mysql' ? 'active' : ''}`}
                >
                  MySQL
                </button>
                <button
                  type="button"
                  onClick={() => setDialect('sqlite')}
                  className={`dialect-tab sqlite ${dialect === 'sqlite' ? 'active' : ''}`}
                >
                  SQLite
                </button>
              </div>

              {/* Toggles and Settings */}
              <div style={{ display: 'flex', alignItems: 'center', gap: '1.25rem' }}>
                <div
                  onClick={() => setExplain(!explain)}
                  className={`toggle-container ${explain ? 'active' : ''}`}
                >
                  <div className="toggle-switch" />
                  <span className="toggle-label">Explain Query</span>
                </div>

                <button
                  type="button"
                  onClick={() => setShowSettings(!showSettings)}
                  className={`settings-trigger ${showSettings ? 'active' : ''}`}
                  title="Advanced Settings"
                >
                  <Settings size={18} />
                </button>

                <button
                  type="submit"
                  disabled={!query.trim() || isLoading}
                  className="action-btn"
                >
                  {isLoading ? (
                    <>
                      <svg className="spinner" viewBox="0 0 50 50">
                        <circle
                          className="path"
                          cx="25"
                          cy="25"
                          r="20"
                          fill="none"
                          strokeWidth="5"
                        />
                      </svg>
                      Generating...
                    </>
                  ) : (
                    <>
                      <Play size={14} fill="currentColor" />
                      Generate SQL
                    </>
                  )}
                </button>
              </div>
            </div>

            {/* Expandable Advanced Settings */}
            {showSettings && (
              <div className="settings-section">
                <div className="settings-group" style={{ flex: '1.2' }}>
                  <label>AI Provider</label>
                  <select
                    value={provider}
                    onChange={(e) => {
                      const newProvider = e.target.value;
                      setProvider(newProvider);
                      if (newProvider === 'ollama') {
                        setModel('qwen2.5-coder');
                      } else {
                        setModel('claude-sonnet-4-6');
                      }
                    }}
                    className="settings-select"
                  >
                    <option value="anthropic">Anthropic Claude</option>
                    <option value="ollama">Local Ollama</option>
                  </select>
                </div>

                <div className="settings-group">
                  <label>Model</label>
                  {provider === 'anthropic' ? (
                    <select
                      value={model}
                      onChange={(e) => setModel(e.target.value)}
                      className="settings-select"
                    >
                      <option value="claude-sonnet-4-6">claude-sonnet-4-6 (Default)</option>
                      <option value="claude-opus-2-6">claude-opus-2-6</option>
                      <option value="claude-haiku-3">claude-haiku-3</option>
                    </select>
                  ) : (
                    <input
                      type="text"
                      value={model}
                      onChange={(e) => setModel(e.target.value)}
                      placeholder="e.g. qwen2.5-coder, llama3"
                      className="settings-input"
                    />
                  )}
                </div>

                <div className="settings-group">
                  <label>Max Tokens: {maxTokens}</label>
                  <input
                    type="range"
                    min="256"
                    max="4096"
                    step="128"
                    value={maxTokens}
                    onChange={(e) => setMaxTokens(parseInt(e.target.value))}
                    style={{ accentColor: 'var(--accent-primary)', marginTop: '0.5rem' }}
                  />
                </div>

                <div className="settings-group">
                  <label>API Server URL</label>
                  <input
                    type="text"
                    value={serverUrl}
                    onChange={(e) => setServerUrl(e.target.value)}
                    placeholder="http://localhost:8000"
                    className="settings-input"
                  />
                </div>

                {provider === 'anthropic' ? (
                  <div className="settings-group" style={{ flex: '1.5' }}>
                    <label>Anthropic API Key</label>
                    <input
                      type="password"
                      value={apiKey}
                      onChange={(e) => setApiKey(e.target.value)}
                      placeholder={apiKeyConfigured ? "Configured on server" : "sk-ant-..."}
                      className="settings-input"
                    />
                  </div>
                ) : (
                  <div className="settings-group" style={{ flex: '1.5' }}>
                    <label>Ollama Host URL</label>
                    <input
                      type="text"
                      value={ollamaHost}
                      onChange={(e) => setOllamaHost(e.target.value)}
                      placeholder="http://localhost:11434"
                      className="settings-input"
                    />
                  </div>
                )}
              </div>
            )}
          </form>
        </div>

        {/* Error Alert Panel */}
        {error && (
          <div className="glass-card error-card">
            <AlertCircle className="error-icon" size={20} />
            <div className="error-content">
              <h3>Generation Failed</h3>
              <p>{error}</p>
              {provider === 'anthropic' && !apiKeyConfigured && apiKey.trim() === '' && backendHealthy && (
                <p style={{ fontSize: '0.8rem', marginTop: '0.5rem', opacity: 0.9 }}>
                  <strong>Troubleshooting:</strong> The backend server is connected, but the
                  <code>ANTHROPIC_API_KEY</code> environment variable is not configured.
                  Please click the gear icon (⚙️) to open <strong>Settings</strong> and enter your
                  API key, or set it as an environment variable (<code>set ANTHROPIC_API_KEY=your_key</code>) and restart the server.
                </p>
              )}
            </div>
          </div>
        )}

        {/* Results Panel */}
        {result && (
          <div className="output-section">
            {/* Generated SQL Card */}
            <div className="glass-card output-card">
              <div className="card-header">
                <div className="card-title-group">
                  <Terminal size={14} />
                  <span>Generated SQL Query</span>
                  <span className={`dialect-badge ${dialect}`}>{dialect}</span>
                </div>
                <div className="card-actions">
                  <button
                    onClick={handleCopy}
                    className={`action-icon-btn ${copied ? 'copied' : ''}`}
                    title="Copy code to clipboard"
                  >
                    {copied ? <Check size={16} /> : <Copy size={16} />}
                  </button>
                </div>
              </div>
              <div className="code-container">
                <pre>
                  <code
                    dangerouslySetInnerHTML={{
                      __html: highlightSQL(result.sql),
                    }}
                  />
                </pre>
              </div>
            </div>

            {/* Explanation Card */}
            {result.explanation && (
              <div className="glass-card output-card">
                <div className="card-header">
                  <div className="card-title-group">
                    <Sliders size={14} />
                    <span>Explanation</span>
                  </div>
                </div>
                <div className="explanation-container">
                  <p>{result.explanation}</p>
                </div>
              </div>
            )}
          </div>
        )}
      </main>

      {/* Floating Toast Notification */}
      {copied && (
        <div className="toast">
          <Check size={16} />
          SQL query copied to clipboard!
        </div>
      )}
    </div>
  );
}

export default App;
