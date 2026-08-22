interface StateBlockProps {
  loading?: boolean;
  error?: string;
  empty?: boolean;
  emptyText?: string;
}

export function StateBlock({ loading, error, empty, emptyText = "Chưa có dữ liệu." }: StateBlockProps) {
  if (loading) return <div className="state state-loading">Đang tải dữ liệu...</div>;
  if (error) return <div className="state state-error">{error}</div>;
  if (empty) return <div className="state state-empty">{emptyText}</div>;
  return null;
}

export function FieldError({ message }: { message?: string }) {
  return message ? <span className="field-error">{message}</span> : null;
}
