import { useEffect, useId, useRef } from "react";

import { trapDialogFocus } from "@/lib/dialogFocus";

type ConfirmDialogProps = {
  open: boolean;
  title: string;
  description: string;
  confirmLabel?: string;
  cancelLabel?: string;
  busy?: boolean;
  destructive?: boolean;
  onConfirm: () => void;
  onCancel: () => void;
};

export function ConfirmDialog({ open, title, description, confirmLabel = "Kinnita", cancelLabel = "Tühista", busy = false, destructive = false, onConfirm, onCancel }: ConfirmDialogProps) {
  const dialogRef = useRef<HTMLDialogElement>(null);
  const cancelRef = useRef<HTMLButtonElement>(null);
  const titleId = useId();
  const descriptionId = useId();

  useEffect(() => {
    const dialog = dialogRef.current;
    if (!dialog) return;
    const previous = document.activeElement instanceof HTMLElement ? document.activeElement : null;
    if (open && !dialog.open) {
      dialog.showModal();
      requestAnimationFrame(() => cancelRef.current?.focus());
    } else if (!open && dialog.open) {
      dialog.close();
    }
    return () => {
      if (dialog.open) dialog.close();
      previous?.focus();
    };
  }, [open]);

  return <dialog
    ref={dialogRef}
    className="w-[min(92vw,32rem)] rounded-2xl border border-border bg-background p-0 shadow-2xl backdrop:bg-black/40"
    aria-labelledby={titleId}
    aria-describedby={descriptionId}
    onKeyDown={trapDialogFocus}
    onCancel={(event) => { event.preventDefault(); if (!busy) onCancel(); }}
  >
    <div className="p-5">
      <h2 id={titleId} className="text-lg font-semibold">{title}</h2>
      <p id={descriptionId} className="mt-2 text-sm text-muted-foreground">{description}</p>
      <div className="mt-5 flex justify-end gap-2">
        <button ref={cancelRef} type="button" className="secondary-action" disabled={busy} onClick={onCancel}>{cancelLabel}</button>
        <button type="button" className={destructive ? "secondary-action warning" : "primary-action"} disabled={busy} aria-busy={busy} onClick={onConfirm}>{busy ? "Töötlen…" : confirmLabel}</button>
      </div>
    </div>
  </dialog>;
}
