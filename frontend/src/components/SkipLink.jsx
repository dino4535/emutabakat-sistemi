import React from 'react';
import './SkipLink.css';

/**
 * Skip Link Component
 * Keyboard kullanıcılarının ana içeriğe doğrudan atlamalarını sağlar
 */
const SkipLink = ({ href = '#main-content', children = 'Ana içeriğe git' }) => {
  return (
    <a href={href} className="skip-link">
      {children}
    </a>
  );
};

export default SkipLink;

