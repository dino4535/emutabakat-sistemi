import './SkeletonLoader.css'

/**
 * Skeleton Loader Component
 * Çeşitli loading durumları için animasyonlu placeholder'lar
 */
export default function SkeletonLoader({ type = 'card', count = 1, height = 'auto' }) {
  const renderSkeleton = () => {
    switch(type) {
      case 'card':
        return <CardSkeleton height={height} />
      case 'table-row':
        return <TableRowSkeleton />
      case 'list-item':
        return <ListItemSkeleton />
      case 'stats-card':
        return <StatsCardSkeleton />
      case 'text':
        return <TextSkeleton />
      case 'circle':
        return <CircleSkeleton />
      default:
        return <CardSkeleton />
    }
  }

  return (
    <div className="skeleton-container">
      {Array.from({ length: count }).map((_, index) => (
        <div key={index} className="skeleton-item">
          {renderSkeleton()}
        </div>
      ))}
    </div>
  )
}

// Card Skeleton (Dashboard kartları için)
function CardSkeleton({ height }) {
  return (
    <div className="skeleton-card" style={{ height }}>
      <div className="skeleton-card-header">
        <div className="skeleton-line skeleton-title"></div>
      </div>
      <div className="skeleton-card-body">
        <div className="skeleton-line skeleton-text"></div>
        <div className="skeleton-line skeleton-text short"></div>
      </div>
    </div>
  )
}

// Table Row Skeleton (Tablolar için)
function TableRowSkeleton() {
  return (
    <div className="skeleton-table-row">
      <div className="skeleton-cell"></div>
      <div className="skeleton-cell"></div>
      <div className="skeleton-cell"></div>
      <div className="skeleton-cell short"></div>
    </div>
  )
}

// List Item Skeleton (Listeler için)
function ListItemSkeleton() {
  return (
    <div className="skeleton-list-item">
      <div className="skeleton-avatar"></div>
      <div className="skeleton-list-content">
        <div className="skeleton-line skeleton-text"></div>
        <div className="skeleton-line skeleton-text short"></div>
      </div>
    </div>
  )
}

// Stats Card Skeleton (İstatistik kartları için)
function StatsCardSkeleton() {
  return (
    <div className="skeleton-stats-card">
      <div className="skeleton-stats-icon"></div>
      <div className="skeleton-stats-content">
        <div className="skeleton-line skeleton-number"></div>
        <div className="skeleton-line skeleton-label"></div>
      </div>
    </div>
  )
}

// Text Skeleton (Basit metin için)
function TextSkeleton() {
  return <div className="skeleton-line skeleton-text"></div>
}

// Circle Skeleton (Avatar, ikon için)
function CircleSkeleton() {
  return <div className="skeleton-circle"></div>
}

