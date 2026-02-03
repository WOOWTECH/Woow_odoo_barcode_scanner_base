/** @odoo-module **/

/**
 * This wrapper ensures html5-qrcode globals are available
 * The library is loaded via web.assets_backend and sets up window.Html5Qrcode
 */

// Ensure the library exports are available globally
// The html5-qrcode.min.js should set these on window automatically
if (typeof window.Html5Qrcode === 'undefined') {
    console.warn('html5-qrcode library not loaded yet');
}

// Export for use in other modules if needed
export const Html5Qrcode = window.Html5Qrcode;
export const Html5QrcodeScanner = window.Html5QrcodeScanner;
export const Html5QrcodeSupportedFormats = window.Html5QrcodeSupportedFormats;
