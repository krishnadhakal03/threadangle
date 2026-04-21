import React, { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';

const DialogContext = createContext(null);

function normalizeOptions(input, fallbackTitle) {
  if (typeof input === 'string') {
    return {
      title: fallbackTitle,
      message: input,
      confirmText: 'Continue',
      cancelText: 'Cancel',
      tone: 'default',
      dismissible: true,
    };
  }

  return {
    title: input?.title || fallbackTitle,
    message: input?.message || '',
    confirmText: input?.confirmText || 'Continue',
    cancelText: input?.cancelText || 'Cancel',
    tone: input?.tone || 'default',
    dismissible: input?.dismissible !== false,
  };
}

export function DialogProvider({ children }) {
  const [dialog, setDialog] = useState(null);

  const showAlert = useCallback((options) => {
    return new Promise((resolve) => {
      const normalized = normalizeOptions(options, 'Notice');
      setDialog({
        kind: 'alert',
        ...normalized,
        confirmText: normalized.confirmText === 'Continue' ? 'OK' : normalized.confirmText,
        resolve,
      });
    });
  }, []);

  const showConfirm = useCallback((options) => {
    return new Promise((resolve) => {
      const normalized = normalizeOptions(options, 'Please Confirm');
      setDialog({
        kind: 'confirm',
        ...normalized,
        resolve,
      });
    });
  }, []);

  const closeDialog = useCallback((value) => {
    setDialog((prev) => {
      if (!prev) return prev;
      prev.resolve(value);
      return null;
    });
  }, []);

  useEffect(() => {
    if (!dialog) return;

    const onKeyDown = (event) => {
      if (event.key !== 'Escape' || !dialog.dismissible) return;
      closeDialog(dialog.kind === 'alert');
    };

    window.addEventListener('keydown', onKeyDown);
    return () => window.removeEventListener('keydown', onKeyDown);
  }, [dialog, closeDialog]);

  const contextValue = useMemo(
    () => ({ alert: showAlert, confirm: showConfirm }),
    [showAlert, showConfirm]
  );

  const toneStyles = {
    default: {
      iconBg: 'bg-sky-500/20',
      iconText: 'text-sky-300',
      buttonBg: 'bg-[#3B82F6] hover:bg-[#2563EB]',
    },
    danger: {
      iconBg: 'bg-red-500/20',
      iconText: 'text-red-300',
      buttonBg: 'bg-red-600 hover:bg-red-500',
    },
    success: {
      iconBg: 'bg-emerald-500/20',
      iconText: 'text-emerald-300',
      buttonBg: 'bg-emerald-600 hover:bg-emerald-500',
    },
  };

  const activeTone = toneStyles[dialog?.tone] || toneStyles.default;

  return (
    <DialogContext.Provider value={contextValue}>
      {children}

      {dialog && (
        <div className="fixed inset-0 z-[11000] flex items-center justify-center bg-black/75 backdrop-blur-sm p-4">
          <div className="w-full max-w-md rounded-2xl border border-[#3F3F46] bg-[#101114] shadow-[0_30px_80px_rgba(0,0,0,0.65)]">
            <div className="px-6 pt-6 pb-4">
              <div className="flex items-start gap-3">
                <div className={`mt-0.5 inline-flex h-9 w-9 items-center justify-center rounded-full ${activeTone.iconBg} ${activeTone.iconText}`}>
                  <svg className="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v4m0 4h.01M4.93 19h14.14c1.54 0 2.5-1.67 1.73-3L13.73 3c-.77-1.33-2.69-1.33-3.46 0L3.2 16c-.77 1.33.19 3 1.73 3z" />
                  </svg>
                </div>
                <div className="min-w-0 flex-1">
                  <h3 className="text-lg font-bold text-white leading-tight">{dialog.title}</h3>
                  <p className="mt-2 text-sm text-[#A1A1AA] whitespace-pre-line">{dialog.message}</p>
                </div>
              </div>
            </div>

            <div className="flex items-center justify-end gap-2 border-t border-[#27272A] px-6 py-4">
              {dialog.kind === 'confirm' && (
                <button
                  onClick={() => closeDialog(false)}
                  className="px-4 py-2 rounded-lg border border-[#3F3F46] text-[#D4D4D8] hover:text-white hover:border-[#71717A] transition-colors text-sm font-semibold"
                >
                  {dialog.cancelText}
                </button>
              )}
              <button
                onClick={() => closeDialog(true)}
                className={`px-4 py-2 rounded-lg text-white transition-colors text-sm font-semibold ${activeTone.buttonBg}`}
              >
                {dialog.confirmText}
              </button>
            </div>
          </div>
        </div>
      )}
    </DialogContext.Provider>
  );
}

export function useDialog() {
  const context = useContext(DialogContext);
  if (!context) {
    throw new Error('useDialog must be used within a DialogProvider');
  }
  return context;
}
