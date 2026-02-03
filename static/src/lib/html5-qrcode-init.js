/**
 * Initialize html5-qrcode globals for Odoo
 * This script runs after html5-qrcode.min.js to ensure window globals are set
 */
(function() {
    'use strict';

    // The library stores everything in __Html5QrcodeLibrary__
    if (window.__Html5QrcodeLibrary__) {
        // Ensure globals are set on window
        window.Html5Qrcode = window.__Html5QrcodeLibrary__.Html5Qrcode;
        window.Html5QrcodeScanner = window.__Html5QrcodeLibrary__.Html5QrcodeScanner;
        window.Html5QrcodeSupportedFormats = window.__Html5QrcodeLibrary__.Html5QrcodeSupportedFormats;
        window.Html5QrcodeScannerState = window.__Html5QrcodeLibrary__.Html5QrcodeScannerState;
        window.Html5QrcodeScanType = window.__Html5QrcodeLibrary__.Html5QrcodeScanType;

        console.log('html5-qrcode library initialized successfully');
    } else {
        console.error('html5-qrcode library failed to load - __Html5QrcodeLibrary__ not found');
    }
})();
