export default function PageHeader({ title, subtitle, actions }) {
  return (
    <div className="page-header">
      <div className="page-header-top">
        <span className="page-header-crumb">{title}</span>
        {actions && <div className="page-header-actions">{actions}</div>}
      </div>
      <h1 className="page-header-title">{title}</h1>
      {subtitle && <p className="page-header-subtitle">{subtitle}</p>}
    </div>
  );
}
