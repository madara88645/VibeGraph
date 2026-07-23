import React, { useState, useCallback, useRef } from 'react';
import { ToastContext } from '../hooks/useToast';
import { IconAlertCircle, IconCheckCircle, IconClose, IconInfo } from './icons';

let toastId = 0;

export function ToastProvider({ children }) {
    const [toasts, setToasts] = useState([]);
    const timersRef = useRef({});

    const removeToast = useCallback((id) => {
        clearTimeout(timersRef.current[id]);
        delete timersRef.current[id];
        setToasts(prev => {
            const next = [];
            for (let i = 0; i < prev.length; i++) {
                if (prev[i].id !== id) {
                    next.push(prev[i]);
                }
            }
            return next;
        });
    }, []);

    const showToast = useCallback((message, type = 'info') => {
        const id = ++toastId;
        setToasts(prev => [...prev, { id, message, type }]);
        timersRef.current[id] = setTimeout(() => removeToast(id), 4000);
        return id;
    }, [removeToast]);

    return (
        <ToastContext.Provider value={showToast}>
            {children}
            <div className="toast-container" aria-live="polite">
                {toasts.map(t => (
                    <div key={t.id} className={`toast toast-${t.type}`}>
                        {t.type === 'success'
                            ? <IconCheckCircle className="toast-icon" size={17} />
                            : t.type === 'error'
                                ? <IconAlertCircle className="toast-icon" size={17} />
                                : <IconInfo className="toast-icon" size={17} />}
                        <span className="toast-message">{t.message}</span>
                        <button
                            className="toast-close"
                            onClick={() => removeToast(t.id)}
                            aria-label="Dismiss notification"
                            title="Dismiss notification"
                        >
                            <IconClose size={13} />
                        </button>
                    </div>
                ))}
            </div>
        </ToastContext.Provider>
    );
}
