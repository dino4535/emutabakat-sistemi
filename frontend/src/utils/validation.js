/**
 * Form Validation Utilities
 * Real-time validation fonksiyonları
 */

/**
 * Email validation
 */
export const validateEmail = (email) => {
  if (!email) {
    return { isValid: false, error: 'Email adresi zorunludur' };
  }
  
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  if (!emailRegex.test(email)) {
    return { isValid: false, error: 'Geçerli bir email adresi giriniz' };
  }
  
  return { isValid: true, error: null };
};

/**
 * Telefon validation (Türkiye formatı)
 */
export const validatePhone = (phone) => {
  if (!phone) {
    return { isValid: true, error: null }; // Opsiyonel
  }
  
  // Türkiye telefon formatı: 0xxx xxx xx xx veya +90xxx xxx xx xx
  const phoneRegex = /^(\+90|0)?[0-9]{10}$/;
  const cleaned = phone.replace(/[\s\-\(\)]/g, '');
  
  if (!phoneRegex.test(cleaned)) {
    return { isValid: false, error: 'Geçerli bir telefon numarası giriniz (örn: 0555 123 45 67)' };
  }
  
  return { isValid: true, error: null };
};

/**
 * VKN/TC validation
 */
export const validateVKN = (vkn, isTCKN = false) => {
  if (!vkn) {
    return { isValid: false, error: 'VKN/TC No zorunludur' };
  }
  
  const cleaned = vkn.replace(/\s/g, '');
  
  if (isTCKN) {
    // TC Kimlik No: 11 haneli
    if (cleaned.length !== 11) {
      return { isValid: false, error: 'TC Kimlik No 11 haneli olmalıdır' };
    }
    
    if (!/^[1-9][0-9]{10}$/.test(cleaned)) {
      return { isValid: false, error: 'Geçersiz TC Kimlik No' };
    }
  } else {
    // VKN: 10 haneli
    if (cleaned.length !== 10) {
      return { isValid: false, error: 'VKN 10 haneli olmalıdır' };
    }
    
    if (!/^[0-9]{10}$/.test(cleaned)) {
      return { isValid: false, error: 'VKN sadece rakamlardan oluşmalıdır' };
    }
  }
  
  return { isValid: true, error: null };
};

/**
 * Password validation
 */
export const validatePassword = (password, options = {}) => {
  const {
    minLength = 6,
    requireUppercase = false,
    requireLowercase = false,
    requireNumber = false,
    requireSpecial = false
  } = options;
  
  if (!password) {
    return { isValid: false, error: 'Şifre zorunludur' };
  }
  
  if (password.length < minLength) {
    return { isValid: false, error: `Şifre en az ${minLength} karakter olmalıdır` };
  }
  
  if (requireUppercase && !/[A-Z]/.test(password)) {
    return { isValid: false, error: 'Şifre en az bir büyük harf içermelidir' };
  }
  
  if (requireLowercase && !/[a-z]/.test(password)) {
    return { isValid: false, error: 'Şifre en az bir küçük harf içermelidir' };
  }
  
  if (requireNumber && !/[0-9]/.test(password)) {
    return { isValid: false, error: 'Şifre en az bir rakam içermelidir' };
  }
  
  if (requireSpecial && !/[!@#$%^&*(),.?":{}|<>]/.test(password)) {
    return { isValid: false, error: 'Şifre en az bir özel karakter içermelidir' };
  }
  
  return { isValid: true, error: null };
};

/**
 * Password confirmation validation
 */
export const validatePasswordConfirmation = (password, confirmation) => {
  if (!confirmation) {
    return { isValid: false, error: 'Şifre tekrarı zorunludur' };
  }
  
  if (password !== confirmation) {
    return { isValid: false, error: 'Şifreler eşleşmiyor' };
  }
  
  return { isValid: true, error: null };
};

/**
 * Required field validation
 */
export const validateRequired = (value, fieldName = 'Bu alan') => {
  if (!value || (typeof value === 'string' && value.trim() === '')) {
    return { isValid: false, error: `${fieldName} zorunludur` };
  }
  
  return { isValid: true, error: null };
};

/**
 * Min length validation
 */
export const validateMinLength = (value, minLength, fieldName = 'Bu alan') => {
  if (!value) {
    return { isValid: true, error: null }; // Opsiyonel alan
  }
  
  if (value.length < minLength) {
    return { isValid: false, error: `${fieldName} en az ${minLength} karakter olmalıdır` };
  }
  
  return { isValid: true, error: null };
};

/**
 * Max length validation
 */
export const validateMaxLength = (value, maxLength, fieldName = 'Bu alan') => {
  if (!value) {
    return { isValid: true, error: null };
  }
  
  if (value.length > maxLength) {
    return { isValid: false, error: `${fieldName} en fazla ${maxLength} karakter olmalıdır` };
  }
  
  return { isValid: true, error: null };
};

/**
 * Number validation
 */
export const validateNumber = (value, options = {}) => {
  const { min, max, fieldName = 'Bu alan' } = options;
  
  if (!value && value !== 0) {
    return { isValid: false, error: `${fieldName} zorunludur` };
  }
  
  const num = Number(value);
  
  if (isNaN(num)) {
    return { isValid: false, error: `${fieldName} geçerli bir sayı olmalıdır` };
  }
  
  if (min !== undefined && num < min) {
    return { isValid: false, error: `${fieldName} en az ${min} olmalıdır` };
  }
  
  if (max !== undefined && num > max) {
    return { isValid: false, error: `${fieldName} en fazla ${max} olmalıdır` };
  }
  
  return { isValid: true, error: null };
};

/**
 * URL validation
 */
export const validateURL = (url) => {
  if (!url) {
    return { isValid: true, error: null }; // Opsiyonel
  }
  
  try {
    new URL(url);
    return { isValid: true, error: null };
  } catch {
    return { isValid: false, error: 'Geçerli bir URL giriniz' };
  }
};

/**
 * Date validation
 */
export const validateDate = (date, options = {}) => {
  const { minDate, maxDate, fieldName = 'Tarih' } = options;
  
  if (!date) {
    return { isValid: false, error: `${fieldName} zorunludur` };
  }
  
  const dateObj = new Date(date);
  
  if (isNaN(dateObj.getTime())) {
    return { isValid: false, error: 'Geçerli bir tarih giriniz' };
  }
  
  if (minDate && dateObj < new Date(minDate)) {
    return { isValid: false, error: `${fieldName} ${new Date(minDate).toLocaleDateString('tr-TR')} tarihinden önce olamaz` };
  }
  
  if (maxDate && dateObj > new Date(maxDate)) {
    return { isValid: false, error: `${fieldName} ${new Date(maxDate).toLocaleDateString('tr-TR')} tarihinden sonra olamaz` };
  }
  
  return { isValid: true, error: null };
};

/**
 * File validation
 */
export const validateFile = (file, options = {}) => {
  const {
    maxSize = 5 * 1024 * 1024, // 5MB default
    allowedTypes = [],
    fieldName = 'Dosya'
  } = options;
  
  if (!file) {
    return { isValid: false, error: `${fieldName} seçilmedi` };
  }
  
  if (file.size > maxSize) {
    const maxSizeMB = (maxSize / (1024 * 1024)).toFixed(1);
    return { isValid: false, error: `${fieldName} boyutu en fazla ${maxSizeMB}MB olmalıdır` };
  }
  
  if (allowedTypes.length > 0 && !allowedTypes.includes(file.type)) {
    return { isValid: false, error: `Geçersiz dosya tipi. İzin verilenler: ${allowedTypes.join(', ')}` };
  }
  
  return { isValid: true, error: null };
};

/**
 * Custom regex validation
 */
export const validateRegex = (value, regex, errorMessage = 'Geçersiz format') => {
  if (!value) {
    return { isValid: true, error: null };
  }
  
  if (!regex.test(value)) {
    return { isValid: false, error: errorMessage };
  }
  
  return { isValid: true, error: null };
};

/**
 * Form validation helper - validates multiple fields
 */
export const validateForm = (values, rules) => {
  const errors = {};
  let isValid = true;
  
  Object.keys(rules).forEach(field => {
    const fieldRules = rules[field];
    const value = values[field];
    
    for (const rule of fieldRules) {
      const result = rule(value);
      
      if (!result.isValid) {
        errors[field] = result.error;
        isValid = false;
        break; // İlk hatada dur
      }
    }
  });
  
  return { isValid, errors };
};

/**
 * Password strength calculator
 */
export const getPasswordStrength = (password) => {
  if (!password) return { strength: 0, label: 'Çok Zayıf', color: '#f56565' };
  
  let strength = 0;
  
  // Length
  if (password.length >= 6) strength += 20;
  if (password.length >= 8) strength += 20;
  if (password.length >= 12) strength += 10;
  
  // Character types
  if (/[a-z]/.test(password)) strength += 15;
  if (/[A-Z]/.test(password)) strength += 15;
  if (/[0-9]/.test(password)) strength += 15;
  if (/[^a-zA-Z0-9]/.test(password)) strength += 15;
  
  // Variety
  const uniqueChars = new Set(password.split('')).size;
  if (uniqueChars > password.length * 0.5) strength += 10;
  
  let label = 'Çok Zayıf';
  let color = '#f56565';
  
  if (strength >= 80) {
    label = 'Çok Güçlü';
    color = '#48bb78';
  } else if (strength >= 60) {
    label = 'Güçlü';
    color = '#38a169';
  } else if (strength >= 40) {
    label = 'Orta';
    color = '#ed8936';
  } else if (strength >= 20) {
    label = 'Zayıf';
    color = '#f6ad55';
  }
  
  return { strength: Math.min(strength, 100), label, color };
};

