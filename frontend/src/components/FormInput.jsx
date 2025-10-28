import React, { useState, useEffect } from 'react';
import './FormInput.css';

/**
 * FormInput Component
 * Real-time validation ve hata mesajları ile input component
 * 
 * @param {string} label - Input label
 * @param {string} type - Input tipi (text, email, password, tel, number, etc.)
 * @param {string} name - Input name
 * @param {string|number} value - Input value
 * @param {function} onChange - Change handler
 * @param {function} onBlur - Blur handler
 * @param {function} validate - Validation fonksiyonu (value) => { isValid, error }
 * @param {string} error - External error message
 * @param {boolean} required - Zorunlu alan mı?
 * @param {boolean} disabled - Disabled mi?
 * @param {string} placeholder - Placeholder text
 * @param {string} helpText - Yardımcı metin
 * @param {React.Node} icon - Sol tarafta icon
 * @param {boolean} showPasswordToggle - Şifre göster/gizle butonu (sadece password için)
 */
const FormInput = ({
  label,
  type = 'text',
  name,
  value,
  onChange,
  onBlur,
  validate,
  error: externalError,
  required = false,
  disabled = false,
  placeholder,
  helpText,
  icon,
  showPasswordToggle = true,
  ...props
}) => {
  const [internalError, setInternalError] = useState(null);
  const [touched, setTouched] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [isFocused, setIsFocused] = useState(false);
  
  // Error priority: external error > internal error
  const displayError = externalError || (touched && internalError);
  const isValid = !displayError;
  const hasValue = value && value.toString().length > 0;
  
  // Real-time validation
  useEffect(() => {
    if (touched && validate) {
      const result = validate(value);
      setInternalError(result.isValid ? null : result.error);
    }
  }, [value, validate, touched]);
  
  const handleBlur = (e) => {
    setTouched(true);
    setIsFocused(false);
    
    if (validate) {
      const result = validate(value);
      setInternalError(result.isValid ? null : result.error);
    }
    
    if (onBlur) {
      onBlur(e);
    }
  };
  
  const handleFocus = () => {
    setIsFocused(true);
  };
  
  const inputType = type === 'password' && showPassword ? 'text' : type;
  
  return (
    <div className={`form-input-wrapper ${disabled ? 'disabled' : ''}`}>
      {label && (
        <label htmlFor={name} className="form-label">
          {label}
          {required && <span className="required-asterisk">*</span>}
        </label>
      )}
      
      <div className={`form-input-container ${isFocused ? 'focused' : ''} ${!isValid ? 'error' : ''} ${hasValue ? 'has-value' : ''}`}>
        {icon && <span className="input-icon">{icon}</span>}
        
        <input
          id={name}
          type={inputType}
          name={name}
          value={value || ''}
          onChange={onChange}
          onBlur={handleBlur}
          onFocus={handleFocus}
          disabled={disabled}
          placeholder={placeholder}
          aria-invalid={!isValid}
          aria-describedby={displayError ? `${name}-error` : helpText ? `${name}-help` : undefined}
          className={`form-input ${icon ? 'has-icon' : ''}`}
          {...props}
        />
        
        {type === 'password' && showPasswordToggle && (
          <button
            type="button"
            className="password-toggle"
            onClick={() => setShowPassword(!showPassword)}
            tabIndex={-1}
            aria-label={showPassword ? 'Şifreyi gizle' : 'Şifreyi göster'}
          >
            {showPassword ? (
              <svg width="20" height="20" viewBox="0 0 20 20" fill="currentColor">
                <path d="M10 12a2 2 0 100-4 2 2 0 000 4z" />
                <path fillRule="evenodd" d="M.458 10C1.732 5.943 5.522 3 10 3s8.268 2.943 9.542 7c-1.274 4.057-5.064 7-9.542 7S1.732 14.057.458 10zM14 10a4 4 0 11-8 0 4 4 0 018 0z" clipRule="evenodd" />
              </svg>
            ) : (
              <svg width="20" height="20" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M3.707 2.293a1 1 0 00-1.414 1.414l14 14a1 1 0 001.414-1.414l-1.473-1.473A10.014 10.014 0 0019.542 10C18.268 5.943 14.478 3 10 3a9.958 9.958 0 00-4.512 1.074l-1.78-1.781zm4.261 4.26l1.514 1.515a2.003 2.003 0 012.45 2.45l1.514 1.514a4 4 0 00-5.478-5.478z" clipRule="evenodd" />
                <path d="M12.454 16.697L9.75 13.992a4 4 0 01-3.742-3.741L2.335 6.578A9.98 9.98 0 00.458 10c1.274 4.057 5.065 7 9.542 7 .847 0 1.669-.105 2.454-.303z" />
              </svg>
            )}
          </button>
        )}
        
        {!isValid && touched && (
          <span className="error-icon" aria-hidden="true">
            <svg width="18" height="18" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
            </svg>
          </span>
        )}
        
        {isValid && hasValue && touched && (
          <span className="success-icon" aria-hidden="true">
            <svg width="18" height="18" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
            </svg>
          </span>
        )}
      </div>
      
      {displayError && (
        <p id={`${name}-error`} className="form-error animate-fadeIn" role="alert">
          {displayError}
        </p>
      )}
      
      {helpText && !displayError && (
        <p id={`${name}-help`} className="form-help-text">
          {helpText}
        </p>
      )}
    </div>
  );
};

export default FormInput;

