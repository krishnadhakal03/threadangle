import React, { useRef, useState } from 'react';
import { DragDropContext, Draggable, Droppable } from '@hello-pangea/dnd';
import { api } from '../utils/api';
import { useDialog } from '../context/DialogContext';

const TYPE_CONFIG = {
  hook:       { label: 'Hook',       bg: 'bg-purple-500/20', text: 'text-purple-300', border: 'border-purple-500/30', dot: 'bg-purple-400' },
  body:       { label: 'Body',       bg: 'bg-blue-500/20',   text: 'text-blue-300',   border: 'border-blue-500/30',   dot: 'bg-blue-400'   },
  cta:        { label: 'CTA',        bg: 'bg-cyan-500/20',   text: 'text-cyan-300',   border: 'border-cyan-500/30',   dot: 'bg-cyan-400'   },
  transition: { label: 'Transition', bg: 'bg-gray-500/20',   text: 'text-gray-300',   border: 'border-gray-500/30',   dot: 'bg-gray-400'   },
};

function SceneTypeBadge({ type }) {
  const cfg = TYPE_CONFIG[type] || TYPE_CONFIG.body;
  return (
    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold ${cfg.bg} ${cfg.text} border ${cfg.border}`}>
      <span className={`w-1.5 h-1.5 rounded-full ${cfg.dot}`} />
      {cfg.label}
    </span>
  );
}

function MethodBadge({ method, credits }) {
  if (method === 'stock')          return <span className="text-[10px] font-semibold text-emerald-400">◎ Stock · Free</span>;
  if (method === 'image_to_video') return <span className="text-[10px] font-semibold text-purple-300">✦ AI · {credits}cr</span>;
  if (method === 'extend')         return <span className="text-[10px] font-semibold text-blue-300">⟳ Extend · {credits}cr</span>;
  return <span className="text-[10px] font-semibold text-emerald-400">◎ Stock · Free</span>;
}

export default function TimelinePreview({
  scenes,
  onScenesChange,
  onApprove,
  onCancel,
  onRefresh,
  estimatedCost,
  error,
  dryRun = true,
  imageProvider = 'huggingface',
}) {
  const { confirm: confirmDialog } = useDialog();
  const [editingScene, setEditingScene]       = useState(null);
  const [regeneratingScene, setRegeneratingScene] = useState(null);
  const [regenError, setRegenError]           = useState(null);
  const uploadRefs = useRef({});

  const handleDragEnd = (result) => {
    if (!result.destination) return;
    const items = Array.from(scenes || []);
    const [moved] = items.splice(result.source.index, 1);
    items.splice(result.destination.index, 0, moved);
    onScenesChange(items.map((s, i) => ({ ...s, scene_index: i })));
  };

  const regenerateScene = async (sceneIndex) => {
    setRegeneratingScene(sceneIndex);
    setRegenError(null);
    try {
      const data = await api.regenerateSceneImage({
        scene_index: sceneIndex,
        scene_description: scenes[sceneIndex]?.description,
        character_profile: scenes[0]?.character_profile || {},
        image_provider: imageProvider,
        variation_token: `${Date.now()}-${sceneIndex}`,
      });
      const updated = [...scenes];
      const previousImage = updated[sceneIndex]?.image_url;
      const alternatives = [
        ...(Array.isArray(updated[sceneIndex]?.image_alternatives) ? updated[sceneIndex].image_alternatives : []),
        previousImage,
        data.image_url,
      ].filter(Boolean).filter((value, idx, arr) => arr.indexOf(value) === idx).slice(-4);
      updated[sceneIndex] = {
        ...updated[sceneIndex],
        image_url: data.image_url,
        image_provider: data.provider || updated[sceneIndex]?.image_provider,
        image_prompt: data.prompt_used || updated[sceneIndex]?.image_prompt,
        image_alternatives: alternatives,
      };
      onScenesChange(updated);
    } catch {
      setRegenError(sceneIndex);
    } finally {
      setRegeneratingScene(null);
    }
  };

  const uploadSceneImage = (sceneIndex, file) => {
    if (!file) return;
    const reader = new FileReader();
    reader.onload = () => {
      const nextUrl = String(reader.result || '');
      if (!nextUrl) return;
      const updated = [...scenes];
      const previousImage = updated[sceneIndex]?.image_url;
      const alternatives = [
        ...(Array.isArray(updated[sceneIndex]?.image_alternatives) ? updated[sceneIndex].image_alternatives : []),
        previousImage,
        nextUrl,
      ].filter(Boolean).filter((value, idx, arr) => arr.indexOf(value) === idx).slice(-6);
      updated[sceneIndex] = {
        ...updated[sceneIndex],
        image_url: nextUrl,
        image_provider: 'upload_custom',
        image_alternatives: alternatives,
      };
      onScenesChange(updated);
    };
    reader.readAsDataURL(file);
  };

  const handleApprove = async () => {
    if (!dryRun && totalCredits > 0) {
      const confirmed = await confirmDialog({
        title: 'Switch To Live Render?',
        message:
          `You are about to generate ${(scenes || []).length} scene(s) using RunwayML.\n\n` +
          `Estimated cost: ${totalCredits} credits (~$${totalUsd}).\n\n` +
          'Continuing will spend real credits.',
        confirmText: 'Render And Spend Credits',
        cancelText: 'Review Again',
        tone: 'danger',
      });
      if (!confirmed) return;
    }
    onApprove();
  };

  const totalCredits = estimatedCost?.credits ?? 0;
  const totalUsd     = Number(estimatedCost?.usd ?? 0).toFixed(2);
  const sceneCount   = (scenes || []).length;

  return (
    <div className="flex flex-col h-full bg-[#0b0d12]">

      {/* ── top status bar ── */}
      <div className="flex items-center justify-between px-6 py-3 border-b border-[#1f2430] flex-shrink-0">
        <div className="flex items-center gap-4">
          <span className="text-sm text-[#C5D8FF] font-semibold">{sceneCount} scene{sceneCount !== 1 ? 's' : ''}</span>
          <span className="text-[#2D4F8F]">|</span>
          <span className="flex items-center gap-1.5 text-xs text-[#8B97B3]">
            <svg width="12" height="12" viewBox="0 0 12 12" fill="none" className="opacity-60">
              <rect x="1" y="2" width="10" height="1.5" rx="0.75" fill="currentColor"/>
              <rect x="1" y="5.25" width="10" height="1.5" rx="0.75" fill="currentColor"/>
              <rect x="1" y="8.5" width="10" height="1.5" rx="0.75" fill="currentColor"/>
            </svg>
            Drag cards to reorder
          </span>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs text-[#8B97B3]">Estimated:</span>
          <span className="text-sm font-bold text-[#60CDFF]">{totalCredits} cr</span>
          <span className="text-xs text-[#3D4F6A]">~${totalUsd}</span>
        </div>
      </div>

      {/* ── scene strip ── */}
      <div className="flex-1 overflow-y-auto">
        <div className="px-6 pt-5 pb-4">
          <DragDropContext onDragEnd={handleDragEnd}>
            <Droppable droppableId="timeline" direction="horizontal">
              {(provided) => (
                <div
                  {...provided.droppableProps}
                  ref={provided.innerRef}
                  className="flex gap-4 overflow-x-auto pb-3"
                >
                  {(scenes || []).map((scene, index) => (
                    <Draggable key={scene.id} draggableId={scene.id} index={index}>
                      {(dragProvided, snapshot) => (
                        <div
                          ref={dragProvided.innerRef}
                          {...dragProvided.draggableProps}
                          className={`relative flex-shrink-0 w-[200px] rounded-2xl overflow-hidden flex flex-col transition-all duration-150 ${
                            snapshot.isDragging
                              ? 'border-2 border-[#388bfd] shadow-2xl shadow-[#388bfd]/30 scale-[1.03] bg-[#0D1421]'
                              : 'border border-[#21262D] bg-[#161B22] hover:border-[#30363D]'
                          }`}
                        >
                          {/* drag handle */}
                          <div
                            {...dragProvided.dragHandleProps}
                            className="flex items-center justify-between px-3 py-2 bg-[#0D1117]/60 cursor-grab active:cursor-grabbing select-none flex-shrink-0"
                          >
                            <span className="text-[10px] font-bold text-[#8B949E] tracking-widest uppercase">
                              Scene {index + 1}
                            </span>
                            <svg width="14" height="10" viewBox="0 0 14 10" fill="none" className="text-[#484F58]">
                              <rect y="0" width="14" height="1.5" rx="0.75" fill="currentColor"/>
                              <rect y="4.25" width="14" height="1.5" rx="0.75" fill="currentColor"/>
                              <rect y="8.5" width="14" height="1.5" rx="0.75" fill="currentColor"/>
                            </svg>
                          </div>

                          {/* scene image */}
                          <div className="relative h-36 bg-[#0D1117] flex-shrink-0 overflow-hidden">
                            {regeneratingScene === index ? (
                              <div className="absolute inset-0 flex flex-col items-center justify-center bg-[#0D1117]/90 gap-2">
                                <div className="w-8 h-8 border-2 border-[#21262D] border-t-[#388bfd] rounded-full animate-spin" />
                                <span className="text-[10px] text-[#8B949E]">Regenerating…</span>
                              </div>
                            ) : scene.image_url ? (
                              <img
                                src={scene.image_url}
                                alt={`Scene ${index + 1}`}
                                className="w-full h-full object-cover"
                                onError={(e) => { e.currentTarget.style.display = 'none'; }}
                              />
                            ) : (
                              <div className="absolute inset-0 flex flex-col items-center justify-center gap-2 text-[#484F58]">
                                <div className="text-2xl">🎬</div>
                                <span className="text-[10px]">No preview</span>
                              </div>
                            )}

                            {/* overlays */}
                            <div className="absolute bottom-2 left-2">
                              <SceneTypeBadge type={scene.scene_type || 'body'} />
                            </div>
                            <div className="absolute bottom-2 right-2 px-1.5 py-0.5 bg-black/70 rounded text-[10px] font-mono text-white">
                              {scene.duration}s
                            </div>

                            {regenError === index && (
                              <div className="absolute inset-0 flex items-center justify-center bg-red-900/60">
                                <span className="text-[10px] text-red-300 font-semibold">Failed — retry</span>
                              </div>
                            )}
                          </div>

                          {/* content area */}
                          <div className="flex-1 flex flex-col p-3 gap-3">
                            {/* script / description */}
                            <div className="flex-1">
                              <div className="text-[10px] font-bold text-[#484F58] uppercase tracking-widest mb-1.5">Script</div>
                              {editingScene === index ? (
                                <textarea
                                  autoFocus
                                  rows={4}
                                  value={scene.description || ''}
                                  onChange={(e) => {
                                    const updated = [...scenes];
                                    updated[index] = { ...updated[index], description: e.target.value };
                                    onScenesChange(updated);
                                  }}
                                  onBlur={() => setEditingScene(null)}
                                  className="w-full bg-[#0D1117] border border-[#30363D] rounded-lg px-2.5 py-2 text-xs text-[#E6EDF3] resize-none outline-none focus:border-[#388bfd]"
                                />
                              ) : (
                                <p
                                  onClick={() => setEditingScene(index)}
                                  className="text-xs text-[#C9D1D9] leading-relaxed min-h-[7.5rem] max-h-36 overflow-y-auto pr-1 cursor-pointer hover:text-white transition-colors"
                                  title="Click to edit"
                                >
                                  {scene.description || <span className="text-[#484F58] italic">No description</span>}
                                </p>
                              )}
                            </div>

                            {/* actions */}
                            <div className="grid grid-cols-3 gap-2 flex-shrink-0">
                              <button
                                onClick={() => setEditingScene(editingScene === index ? null : index)}
                                className={`flex-1 py-1.5 rounded-lg text-xs font-semibold transition-colors ${
                                  editingScene === index
                                    ? 'bg-[#388bfd]/20 border border-[#388bfd]/40 text-[#388bfd]'
                                    : 'bg-[#21262D] hover:bg-[#30363D] text-[#C9D1D9]'
                                }`}
                              >
                                {editingScene === index ? 'Done' : 'Edit'}
                              </button>
                              <button
                                onClick={() => regenerateScene(index)}
                                disabled={regeneratingScene !== null}
                                className="flex-1 py-1.5 rounded-lg text-xs font-semibold bg-[#1F6FEB] hover:bg-[#388bfd] disabled:opacity-40 disabled:cursor-not-allowed text-white transition-colors"
                              >
                                {regeneratingScene === index ? '…' : 'Regen'}
                              </button>
                              <>
                                <input
                                  ref={(node) => {
                                    if (node) uploadRefs.current[index] = node;
                                  }}
                                  type="file"
                                  accept="image/*"
                                  className="hidden"
                                  onChange={(e) => {
                                    uploadSceneImage(index, e.target.files?.[0]);
                                    e.target.value = '';
                                  }}
                                />
                                <button
                                  onClick={() => uploadRefs.current[index]?.click()}
                                  className="flex-1 py-1.5 rounded-lg text-xs font-semibold bg-[#21262D] hover:bg-[#30363D] text-[#C9D1D9] transition-colors"
                                >
                                  Upload
                                </button>
                              </>
                            </div>

                            {Array.isArray(scene.image_alternatives) && scene.image_alternatives.length > 1 && (
                              <div className="space-y-1.5 flex-shrink-0">
                                <div className="text-[10px] font-bold text-[#484F58] uppercase tracking-widest">Alternatives</div>
                                <div className="flex gap-2 overflow-x-auto pb-1">
                                  {scene.image_alternatives.map((altUrl) => {
                                    const selected = altUrl === scene.image_url;
                                    return (
                                      <button
                                        key={altUrl}
                                        onClick={() => {
                                          const updated = [...scenes];
                                          updated[index] = { ...updated[index], image_url: altUrl };
                                          onScenesChange(updated);
                                        }}
                                        className={`relative h-12 w-12 flex-shrink-0 overflow-hidden rounded-lg border ${selected ? 'border-[#388bfd]' : 'border-[#30363D]'}`}
                                      >
                                        <img src={altUrl} alt="Alternative" className="h-full w-full object-cover" />
                                      </button>
                                    );
                                  })}
                                </div>
                              </div>
                            )}

                            {/* method badge */}
                            <div className="pt-2 border-t border-[#21262D] flex-shrink-0">
                              <MethodBadge method={scene.method} credits={scene.credits_cost} />
                            </div>
                          </div>
                        </div>
                      )}
                    </Draggable>
                  ))}
                  {provided.placeholder}
                </div>
              )}
            </Droppable>
          </DragDropContext>
        </div>
      </div>

      {/* ── error retry banner ── */}
      {error && (
        <div className="flex-shrink-0 border-t border-red-500/30 bg-red-900/20 px-6 py-3">
          <div className="flex items-start gap-3">
            <span className="text-red-400 text-base leading-none mt-0.5 flex-shrink-0">⚠</span>
            <div className="flex-1 min-w-0">
              <div className="text-sm font-semibold text-red-300">Generation failed — your storyboard is preserved</div>
              <div className="text-xs text-red-400/80 mt-0.5 break-words">{error}</div>
            </div>
            <button
              onClick={handleApprove}
              className="flex-shrink-0 px-4 py-1.5 rounded-lg bg-red-600 hover:bg-red-500 text-white text-xs font-bold transition-colors"
            >
              Retry
            </button>
          </div>
        </div>
      )}

      {/* ── bottom action bar ── */}
      <div className="flex-shrink-0 border-t border-[#1f2430] bg-[#0b0d12]/95 px-6 py-4">
        <div className="flex items-center gap-3">
          <button
            onClick={onCancel}
            className="px-4 py-2.5 rounded-xl border border-[#21262D] text-[#8B97B3] hover:text-white hover:border-[#30363D] text-sm font-medium transition-colors flex-shrink-0"
          >
            ← Back
          </button>
          {onRefresh && (
            <button
              onClick={onRefresh}
              className="px-4 py-2.5 rounded-xl border border-[#21262D] text-[#8B97B3] hover:text-white hover:border-[#30363D] text-sm font-medium transition-colors flex-shrink-0"
            >
              ↺ Refresh
            </button>
          )}
          <div className="flex-1" />
          <button
            onClick={handleApprove}
            className={`flex items-center gap-3 px-6 py-2.5 rounded-xl text-white font-bold text-sm transition-colors ${
              dryRun ? 'bg-emerald-600 hover:bg-emerald-500' : 'bg-[#1F6FEB] hover:bg-[#388bfd]'
            }`}
          >
            <span>{dryRun ? '🛡 Approve Dry Run (No Render)' : '🔴 Approve & Spend Credits'}</span>
            <span className="flex items-center gap-1 px-2 py-0.5 rounded-full bg-white/10 text-xs font-semibold">
              {dryRun ? '0 cr · Free' : `${totalCredits} cr · $${totalUsd}`}
            </span>
          </button>
        </div>
      </div>
    </div>
  );
}
