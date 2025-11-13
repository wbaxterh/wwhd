'use client';

import { useState, useEffect } from 'react';
import { useAuth } from '@/contexts/auth';
import { AuthModal } from '@/components/AuthModal';

interface Document {
  id: number;
  namespace: string;
  title: string;
  content: string;
  source_url?: string;
  vector_id?: string;
  uploaded_by?: number;
  created_at: string;
  youtube_url?: string;
  is_transcript?: boolean;
}

interface Namespace {
  name: string;
  document_count: number;
}

function KnowledgeBaseInterface() {
  const { token, isAuthenticated } = useAuth();
  const [documents, setDocuments] = useState<Document[]>([]);
  const [namespaces, setNamespaces] = useState<Namespace[]>([]);
  const [selectedNamespace, setSelectedNamespace] = useState<string>('');
  const [isLoading, setIsLoading] = useState(false);
  const [showAuthModal, setShowAuthModal] = useState(false);

  // Form states
  const [showUploadForm, setShowUploadForm] = useState(false);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [editingDocument, setEditingDocument] = useState<Document | null>(null);

  // Upload form state
  const [uploadData, setUploadData] = useState({
    namespace: 'general',
    title: '',
    youtube_url: ''
  });
  const [selectedFile, setSelectedFile] = useState<File | null>(null);

  // Create/Edit form state
  const [formData, setFormData] = useState({
    namespace: 'general',
    title: '',
    content: '',
    source_url: '',
    youtube_url: ''
  });

  // Custom namespace input states
  const [showCustomNamespace, setShowCustomNamespace] = useState(false);
  const [customNamespace, setCustomNamespace] = useState('');
  const [showCustomNamespaceEdit, setShowCustomNamespaceEdit] = useState(false);
  const [customNamespaceEdit, setCustomNamespaceEdit] = useState('');

  // Predefined agent namespaces
  const predefinedNamespaces = [
    'general',
    'health',
    'philosophy',
    'martial-arts',
    'shaolin',
    'tcm',
    'meditation',
    'wellness',
    'wisdom',
    'spirituality'
  ];

  useEffect(() => {
    if (!isAuthenticated) {
      setShowAuthModal(true);
    }
  }, [isAuthenticated]);

  useEffect(() => {
    if (isAuthenticated) {
      loadNamespaces();
      loadDocuments();
    }
  }, [isAuthenticated, selectedNamespace]);

  const loadNamespaces = async () => {
    try {
      const response = await fetch('/api/knowledgebase/namespaces', {
        headers: {
          ...(token && { 'Authorization': `Bearer ${token}` }),
        },
      });

      if (response.ok) {
        const data = await response.json();
        setNamespaces(data);
      }
    } catch (error) {
      console.error('Failed to load namespaces:', error);
    }
  };

  const loadDocuments = async () => {
    setIsLoading(true);
    try {
      const params = new URLSearchParams();
      if (selectedNamespace) {
        params.append('namespace', selectedNamespace);
      }

      const response = await fetch(`/api/knowledgebase/documents?${params}`, {
        headers: {
          ...(token && { 'Authorization': `Bearer ${token}` }),
        },
      });

      if (response.ok) {
        const data = await response.json();
        setDocuments(data);
      }
    } catch (error) {
      console.error('Failed to load documents:', error);
    } finally {
      setIsLoading(false);
    }
  };

  // Helper functions for namespace management
  const getAllAvailableNamespaces = () => {
    const existing = namespaces.map(ns => ns.name);
    const combined = Array.from(new Set([...predefinedNamespaces, ...existing]));
    return combined.sort();
  };

  const handleNamespaceChange = (value: string, type: 'upload' | 'edit') => {
    if (value === 'custom') {
      if (type === 'upload') {
        setShowCustomNamespace(true);
        setCustomNamespace('');
      } else {
        setShowCustomNamespaceEdit(true);
        setCustomNamespaceEdit('');
      }
    } else {
      if (type === 'upload') {
        setUploadData({ ...uploadData, namespace: value });
        setShowCustomNamespace(false);
      } else {
        setFormData({ ...formData, namespace: value });
        setShowCustomNamespaceEdit(false);
      }
    }
  };

  const handleCustomNamespaceSubmit = (type: 'upload' | 'edit') => {
    const namespace = type === 'upload' ? customNamespace : customNamespaceEdit;
    if (namespace.trim()) {
      if (type === 'upload') {
        setUploadData({ ...uploadData, namespace: namespace.trim() });
        setShowCustomNamespace(false);
      } else {
        setFormData({ ...formData, namespace: namespace.trim() });
        setShowCustomNamespaceEdit(false);
      }
    }
  };

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedFile) return;

    const finalNamespace = showCustomNamespace && customNamespace.trim()
      ? customNamespace.trim()
      : uploadData.namespace;

    const formDataObj = new FormData();
    formDataObj.append('file', selectedFile);
    formDataObj.append('namespace', finalNamespace);
    if (uploadData.title) formDataObj.append('title', uploadData.title);
    if (uploadData.youtube_url) formDataObj.append('youtube_url', uploadData.youtube_url);

    try {
      setIsLoading(true);
      const response = await fetch('/api/knowledgebase/upload', {
        method: 'POST',
        headers: {
          ...(token && { 'Authorization': `Bearer ${token}` }),
        },
        body: formDataObj,
      });

      if (response.ok) {
        setShowUploadForm(false);
        setSelectedFile(null);
        setUploadData({ namespace: 'general', title: '', youtube_url: '' });
        setShowCustomNamespace(false);
        setCustomNamespace('');
        loadDocuments();
        loadNamespaces();
      } else {
        const error = await response.json();
        alert(error.detail || 'Upload failed');
      }
    } catch (error) {
      console.error('Upload failed:', error);
      alert('Upload failed');
    } finally {
      setIsLoading(false);
    }
  };

  const handleCreateDocument = async (e: React.FormEvent) => {
    e.preventDefault();

    const finalNamespace = showCustomNamespaceEdit && customNamespaceEdit.trim()
      ? customNamespaceEdit.trim()
      : formData.namespace;

    const finalFormData = {
      ...formData,
      namespace: finalNamespace
    };

    try {
      setIsLoading(true);
      const response = await fetch('/api/knowledgebase/documents', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token && { 'Authorization': `Bearer ${token}` }),
        },
        body: JSON.stringify(finalFormData),
      });

      if (response.ok) {
        setShowCreateForm(false);
        setFormData({ namespace: 'general', title: '', content: '', source_url: '', youtube_url: '' });
        setShowCustomNamespaceEdit(false);
        setCustomNamespaceEdit('');
        loadDocuments();
        loadNamespaces();
      } else {
        const error = await response.json();
        alert(error.detail || 'Create failed');
      }
    } catch (error) {
      console.error('Create failed:', error);
      alert('Create failed');
    } finally {
      setIsLoading(false);
    }
  };

  const handleUpdateDocument = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingDocument) return;

    try {
      setIsLoading(true);
      const response = await fetch(`/api/knowledgebase/documents/${editingDocument.id}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          ...(token && { 'Authorization': `Bearer ${token}` }),
        },
        body: JSON.stringify({
          title: formData.title,
          content: formData.content,
          source_url: formData.source_url,
          youtube_url: formData.youtube_url
        }),
      });

      if (response.ok) {
        setEditingDocument(null);
        setFormData({ namespace: 'general', title: '', content: '', source_url: '', youtube_url: '' });
        loadDocuments();
      } else {
        const error = await response.json();
        alert(error.detail || 'Update failed');
      }
    } catch (error) {
      console.error('Update failed:', error);
      alert('Update failed');
    } finally {
      setIsLoading(false);
    }
  };

  const handleDeleteDocument = async (documentId: number) => {
    if (!confirm('Are you sure you want to delete this document?')) return;

    try {
      setIsLoading(true);
      const response = await fetch(`/api/knowledgebase/documents/${documentId}`, {
        method: 'DELETE',
        headers: {
          ...(token && { 'Authorization': `Bearer ${token}` }),
        },
      });

      if (response.ok) {
        loadDocuments();
        loadNamespaces();
      } else {
        const error = await response.json();
        alert(error.detail || 'Delete failed');
      }
    } catch (error) {
      console.error('Delete failed:', error);
      alert('Delete failed');
    } finally {
      setIsLoading(false);
    }
  };

  const startEdit = (document: Document) => {
    setEditingDocument(document);
    setFormData({
      namespace: document.namespace,
      title: document.title,
      content: document.content,
      source_url: document.source_url || '',
      youtube_url: document.youtube_url || ''
    });
  };

  return (
    <div className="h-screen bg-background flex flex-col">
      <AuthModal isOpen={showAuthModal} onClose={() => setShowAuthModal(false)} />

      {/* Header */}
      <header className="border-b border-border bg-card flex-shrink-0">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <h1 className="text-2xl font-bold text-foreground">Knowledge Base</h1>
              <span className="text-sm text-muted-foreground">Manage documents and training data</span>
            </div>
            <div className="flex items-center space-x-4">
              <a
                href="/chat"
                className="text-sm text-muted-foreground hover:text-foreground transition-colors"
              >
                → Chat
              </a>
              <a
                href="/"
                className="text-sm text-muted-foreground hover:text-foreground transition-colors"
              >
                ← Back to Home
              </a>
            </div>
          </div>
        </div>
      </header>

      <main className="flex-1 flex overflow-hidden">
        {/* Sidebar - Namespaces */}
        <div className="w-64 bg-card border-r border-border p-4 overflow-y-auto">
          <div className="mb-4">
            <h3 className="text-lg font-semibold text-foreground mb-2">Namespaces</h3>
            <button
              onClick={() => setSelectedNamespace('')}
              className={`w-full text-left px-3 py-2 rounded-md transition-colors ${
                selectedNamespace === ''
                  ? 'bg-primary text-primary-foreground'
                  : 'hover:bg-muted'
              }`}
            >
              <div className="flex justify-between">
                <span>All Documents</span>
                <span className="text-sm opacity-70">
                  {documents.length}
                </span>
              </div>
            </button>
          </div>

          <div className="space-y-1">
            {namespaces.map((ns) => (
              <button
                key={ns.name}
                onClick={() => setSelectedNamespace(ns.name)}
                className={`w-full text-left px-3 py-2 rounded-md transition-colors ${
                  selectedNamespace === ns.name
                    ? 'bg-primary text-primary-foreground'
                    : 'hover:bg-muted'
                }`}
              >
                <div className="flex justify-between">
                  <span className="capitalize">{ns.name}</span>
                  <span className="text-sm opacity-70">{ns.document_count}</span>
                </div>
              </button>
            ))}
          </div>
        </div>

        {/* Main Content */}
        <div className="flex-1 flex flex-col">
          {/* Actions Bar */}
          <div className="p-4 border-b border-border bg-background">
            <div className="flex gap-2">
              <button
                onClick={() => setShowUploadForm(true)}
                className="px-4 py-2 bg-white text-slate-900 rounded-md hover:bg-slate-100 transition-colors shadow-md"
              >
                Upload PDF
              </button>
              <button
                onClick={() => setShowCreateForm(true)}
                className="px-4 py-2 border border-border text-foreground rounded-md hover:bg-muted transition-colors"
              >
                Create Document
              </button>
            </div>
          </div>

          {/* Documents List */}
          <div className="flex-1 overflow-y-auto p-4">
            {isLoading ? (
              <div className="text-center py-8 text-muted-foreground">Loading...</div>
            ) : documents.length === 0 ? (
              <div className="text-center py-8 text-muted-foreground">
                No documents found. Upload or create your first document!
              </div>
            ) : (
              <div className="space-y-4">
                {documents.map((doc) => (
                  <div key={doc.id} className="bg-card border border-border rounded-lg p-4">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-2">
                          <h4 className="font-semibold text-foreground">{doc.title}</h4>
                          <span className="px-2 py-1 bg-muted text-muted-foreground text-xs rounded-md">
                            {doc.namespace}
                          </span>
                          {doc.youtube_url && (
                            <span className="px-2 py-1 bg-red-100 text-red-800 text-xs rounded-md">
                              Transcript
                            </span>
                          )}
                        </div>
                        <p className="text-muted-foreground text-sm mb-2">
                          {doc.content.substring(0, 200)}...
                        </p>
                        <div className="flex items-center gap-4 text-xs text-muted-foreground">
                          <span>Created: {new Date(doc.created_at).toLocaleDateString()}</span>
                          {doc.youtube_url && (
                            <a
                              href={doc.youtube_url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="text-blue-600 hover:text-blue-800"
                            >
                              📺 YouTube Link
                            </a>
                          )}
                          {doc.source_url && (
                            <a
                              href={doc.source_url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="text-blue-600 hover:text-blue-800"
                            >
                              🔗 Source
                            </a>
                          )}
                        </div>
                      </div>
                      <div className="flex items-center gap-2 ml-4">
                        <button
                          onClick={() => startEdit(doc)}
                          className="px-3 py-1 text-sm border border-border rounded-md hover:bg-muted transition-colors"
                        >
                          Edit
                        </button>
                        <button
                          onClick={() => handleDeleteDocument(doc.id)}
                          className="px-3 py-1 text-sm bg-red-500 text-white rounded-md hover:bg-red-600 transition-colors"
                        >
                          Delete
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </main>

      {/* Upload Modal */}
      {showUploadForm && (
        <div className="fixed inset-0 bg-background/80 backdrop-blur-sm z-50 flex items-center justify-center">
          <div className="bg-card border border-border rounded-lg p-6 w-full max-w-md mx-4">
            <h3 className="text-lg font-semibold text-foreground mb-4">Upload PDF Document</h3>
            <form onSubmit={handleUpload} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-foreground mb-1">
                  PDF File
                </label>
                <input
                  type="file"
                  accept=".pdf"
                  onChange={(e) => setSelectedFile(e.target.files?.[0] || null)}
                  className="w-full px-3 py-2 border border-border rounded-md"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-foreground mb-1">
                  Namespace
                </label>
                {showCustomNamespace ? (
                  <div className="flex gap-2">
                    <input
                      type="text"
                      value={customNamespace}
                      onChange={(e) => setCustomNamespace(e.target.value)}
                      className="flex-1 px-3 py-2 border border-border rounded-md bg-background text-foreground"
                      placeholder="Enter custom namespace..."
                      autoFocus
                    />
                    <button
                      type="button"
                      onClick={() => handleCustomNamespaceSubmit('upload')}
                      className="px-3 py-2 bg-white text-slate-900 rounded-md hover:bg-slate-100 transition-colors"
                      disabled={!customNamespace.trim()}
                    >
                      ✓
                    </button>
                    <button
                      type="button"
                      onClick={() => setShowCustomNamespace(false)}
                      className="px-3 py-2 border border-border rounded-md hover:bg-muted transition-colors"
                    >
                      ✕
                    </button>
                  </div>
                ) : (
                  <select
                    value={uploadData.namespace}
                    onChange={(e) => handleNamespaceChange(e.target.value, 'upload')}
                    className="w-full px-3 py-2 border border-border rounded-md bg-background text-foreground"
                    required
                  >
                    {getAllAvailableNamespaces().map(ns => (
                      <option key={ns} value={ns} className="capitalize">
                        {ns} {namespaces.find(n => n.name === ns) ? `(${namespaces.find(n => n.name === ns)?.document_count} docs)` : ''}
                      </option>
                    ))}
                    <option value="custom">+ Add Custom Namespace</option>
                  </select>
                )}
              </div>
              <div>
                <label className="block text-sm font-medium text-foreground mb-1">
                  Title (optional)
                </label>
                <input
                  type="text"
                  value={uploadData.title}
                  onChange={(e) => setUploadData({...uploadData, title: e.target.value})}
                  className="w-full px-3 py-2 border border-border rounded-md bg-background text-foreground"
                  placeholder="Document title..."
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-foreground mb-1">
                  YouTube URL (if transcript)
                </label>
                <input
                  type="url"
                  value={uploadData.youtube_url}
                  onChange={(e) => setUploadData({...uploadData, youtube_url: e.target.value})}
                  className="w-full px-3 py-2 border border-border rounded-md bg-background text-foreground"
                  placeholder="https://youtube.com/watch?v=..."
                />
              </div>
              <div className="flex justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => {
                    setShowUploadForm(false);
                    setShowCustomNamespace(false);
                    setCustomNamespace('');
                  }}
                  className="px-4 py-2 border border-border text-foreground rounded-md hover:bg-muted transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isLoading || !selectedFile}
                  className="px-4 py-2 bg-white text-slate-900 rounded-md hover:bg-slate-100 disabled:opacity-50 transition-colors shadow-md"
                >
                  {isLoading ? 'Uploading...' : 'Upload'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Create/Edit Modal */}
      {(showCreateForm || editingDocument) && (
        <div className="fixed inset-0 bg-background/80 backdrop-blur-sm z-50 flex items-center justify-center">
          <div className="bg-card border border-border rounded-lg p-6 w-full max-w-2xl mx-4 max-h-[90vh] overflow-y-auto">
            <h3 className="text-lg font-semibold text-foreground mb-4">
              {editingDocument ? 'Edit Document' : 'Create Document'}
            </h3>
            <form onSubmit={editingDocument ? handleUpdateDocument : handleCreateDocument} className="space-y-4">
              {!editingDocument && (
                <div>
                  <label className="block text-sm font-medium text-foreground mb-1">
                    Namespace
                  </label>
                  {showCustomNamespaceEdit ? (
                    <div className="flex gap-2">
                      <input
                        type="text"
                        value={customNamespaceEdit}
                        onChange={(e) => setCustomNamespaceEdit(e.target.value)}
                        className="flex-1 px-3 py-2 border border-border rounded-md bg-background text-foreground"
                        placeholder="Enter custom namespace..."
                        autoFocus
                      />
                      <button
                        type="button"
                        onClick={() => handleCustomNamespaceSubmit('edit')}
                        className="px-3 py-2 bg-white text-slate-900 rounded-md hover:bg-slate-100 transition-colors"
                        disabled={!customNamespaceEdit.trim()}
                      >
                        ✓
                      </button>
                      <button
                        type="button"
                        onClick={() => setShowCustomNamespaceEdit(false)}
                        className="px-3 py-2 border border-border rounded-md hover:bg-muted transition-colors"
                      >
                        ✕
                      </button>
                    </div>
                  ) : (
                    <select
                      value={formData.namespace}
                      onChange={(e) => handleNamespaceChange(e.target.value, 'edit')}
                      className="w-full px-3 py-2 border border-border rounded-md bg-background text-foreground"
                      required
                    >
                      {getAllAvailableNamespaces().map(ns => (
                        <option key={ns} value={ns} className="capitalize">
                          {ns} {namespaces.find(n => n.name === ns) ? `(${namespaces.find(n => n.name === ns)?.document_count} docs)` : ''}
                        </option>
                      ))}
                      <option value="custom">+ Add Custom Namespace</option>
                    </select>
                  )}
                </div>
              )}
              <div>
                <label className="block text-sm font-medium text-foreground mb-1">
                  Title
                </label>
                <input
                  type="text"
                  value={formData.title}
                  onChange={(e) => setFormData({...formData, title: e.target.value})}
                  className="w-full px-3 py-2 border border-border rounded-md bg-background text-foreground"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-foreground mb-1">
                  Content
                </label>
                <textarea
                  value={formData.content}
                  onChange={(e) => setFormData({...formData, content: e.target.value})}
                  className="w-full px-3 py-2 border border-border rounded-md bg-background text-foreground"
                  rows={10}
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-foreground mb-1">
                  Source URL (optional)
                </label>
                <input
                  type="url"
                  value={formData.source_url}
                  onChange={(e) => setFormData({...formData, source_url: e.target.value})}
                  className="w-full px-3 py-2 border border-border rounded-md bg-background text-foreground"
                  placeholder="https://..."
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-foreground mb-1">
                  YouTube URL (if transcript)
                </label>
                <input
                  type="url"
                  value={formData.youtube_url}
                  onChange={(e) => setFormData({...formData, youtube_url: e.target.value})}
                  className="w-full px-3 py-2 border border-border rounded-md bg-background text-foreground"
                  placeholder="https://youtube.com/watch?v=..."
                />
              </div>
              <div className="flex justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => {
                    setShowCreateForm(false);
                    setEditingDocument(null);
                    setFormData({ namespace: 'general', title: '', content: '', source_url: '', youtube_url: '' });
                    setShowCustomNamespaceEdit(false);
                    setCustomNamespaceEdit('');
                  }}
                  className="px-4 py-2 border border-border text-foreground rounded-md hover:bg-muted transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isLoading}
                  className="px-4 py-2 bg-white text-slate-900 rounded-md hover:bg-slate-100 disabled:opacity-50 transition-colors shadow-md"
                >
                  {isLoading ? 'Saving...' : editingDocument ? 'Update' : 'Create'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

export default function KnowledgeBasePage() {
  return <KnowledgeBaseInterface />;
}