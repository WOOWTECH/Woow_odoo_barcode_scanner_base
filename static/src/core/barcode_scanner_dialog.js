/** @odoo-module **/

import { Component, useState, onMounted, onWillUnmount } from "@odoo/owl";
import { Dialog } from "@web/core/dialog/dialog";
import { _t } from "@web/core/l10n/translation";
import { useService } from "@web/core/utils/hooks";

// Track if library is loaded
let libraryLoaded = false;
let libraryLoadingPromise = null;

/**
 * Load html5-qrcode library dynamically
 */
async function loadHtml5QrcodeLibrary() {
    if (libraryLoaded && window.Html5Qrcode) {
        return true;
    }

    if (libraryLoadingPromise) {
        return libraryLoadingPromise;
    }

    libraryLoadingPromise = new Promise((resolve, reject) => {
        // Check if already loaded
        if (window.Html5Qrcode) {
            libraryLoaded = true;
            resolve(true);
            return;
        }

        // Load the script
        const script = document.createElement('script');
        script.src = '/barcode_scanner_base/static/src/lib/html5-qrcode.min.js';
        script.async = true;

        script.onload = () => {
            // After loading, set up globals from __Html5QrcodeLibrary__
            if (window.__Html5QrcodeLibrary__) {
                window.Html5Qrcode = window.__Html5QrcodeLibrary__.Html5Qrcode;
                window.Html5QrcodeScanner = window.__Html5QrcodeLibrary__.Html5QrcodeScanner;
                window.Html5QrcodeSupportedFormats = window.__Html5QrcodeLibrary__.Html5QrcodeSupportedFormats;
                window.Html5QrcodeScannerState = window.__Html5QrcodeLibrary__.Html5QrcodeScannerState;
                window.Html5QrcodeScanType = window.__Html5QrcodeLibrary__.Html5QrcodeScanType;
            }

            if (window.Html5Qrcode) {
                libraryLoaded = true;
                console.log('html5-qrcode library loaded successfully');
                resolve(true);
            } else {
                reject(new Error('html5-qrcode library failed to initialize'));
            }
        };

        script.onerror = () => {
            reject(new Error('Failed to load html5-qrcode library'));
        };

        document.head.appendChild(script);
    });

    return libraryLoadingPromise;
}

/**
 * BarcodeScannerDialog - OWL component for camera-based barcode/QR scanning
 *
 * Uses html5-qrcode library for scanning.
 * Supports multiple barcode formats: EAN-13, EAN-8, UPC-A, UPC-E, Code 128, Code 39, QR Code
 */
export class BarcodeScannerDialog extends Component {
    static template = "barcode_scanner_base.ScannerDialog";
    static components = { Dialog };
    static props = {
        onScan: { type: Function },
        onClose: { type: Function },
        close: { type: Function },
        allowedFormats: { type: Array, optional: true },
        title: { type: String, optional: true },
        scanMode: { type: String, optional: true }, // 'all', 'barcode_only', 'qr_only'
    };
    static defaultProps = {
        allowedFormats: [],
        title: _t("Scan Barcode"),
        scanMode: "all",
    };

    setup() {
        this.notification = useService("notification");
        this.state = useState({
            isScanning: false,
            error: null,
            lastScanned: null,
            cameras: [],
            selectedCameraId: null,
            isInitializing: true,
        });

        this.scanner = null;
        this.scannerContainerId = "barcode-scanner-container";

        onMounted(() => this.initScanner());
        onWillUnmount(() => this.destroyScanner());
    }

    /**
     * Get supported barcode formats based on scan mode
     */
    getSupportedFormats() {
        // html5-qrcode format constants
        const Html5QrcodeSupportedFormats = window.Html5QrcodeSupportedFormats || {
            QR_CODE: 0,
            AZTEC: 1,
            CODABAR: 2,
            CODE_39: 3,
            CODE_93: 4,
            CODE_128: 5,
            DATA_MATRIX: 6,
            MAXICODE: 7,
            ITF: 8,
            EAN_13: 9,
            EAN_8: 10,
            PDF_417: 11,
            RSS_14: 12,
            RSS_EXPANDED: 13,
            UPC_A: 14,
            UPC_E: 15,
            UPC_EAN_EXTENSION: 16,
        };

        if (this.props.allowedFormats && this.props.allowedFormats.length > 0) {
            return this.props.allowedFormats;
        }

        const barcodeFormats = [
            Html5QrcodeSupportedFormats.EAN_13,
            Html5QrcodeSupportedFormats.EAN_8,
            Html5QrcodeSupportedFormats.UPC_A,
            Html5QrcodeSupportedFormats.UPC_E,
            Html5QrcodeSupportedFormats.CODE_128,
            Html5QrcodeSupportedFormats.CODE_39,
            Html5QrcodeSupportedFormats.CODE_93,
            Html5QrcodeSupportedFormats.CODABAR,
            Html5QrcodeSupportedFormats.ITF,
        ];

        const qrFormats = [
            Html5QrcodeSupportedFormats.QR_CODE,
            Html5QrcodeSupportedFormats.DATA_MATRIX,
            Html5QrcodeSupportedFormats.AZTEC,
        ];

        switch (this.props.scanMode) {
            case "barcode_only":
                return barcodeFormats;
            case "qr_only":
                return qrFormats;
            default:
                return [...barcodeFormats, ...qrFormats];
        }
    }

    /**
     * Initialize the barcode scanner
     */
    async initScanner() {
        try {
            // Load library dynamically
            await loadHtml5QrcodeLibrary();

            // Check if html5-qrcode is loaded
            if (typeof window.Html5Qrcode === "undefined") {
                throw new Error(_t("Barcode scanner library not loaded"));
            }

            // Get available cameras
            const devices = await window.Html5Qrcode.getCameras();
            if (!devices || devices.length === 0) {
                throw new Error(_t("No cameras found on this device"));
            }

            this.state.cameras = devices;
            // Prefer back camera
            const backCamera = devices.find(
                (d) =>
                    d.label.toLowerCase().includes("back") ||
                    d.label.toLowerCase().includes("rear") ||
                    d.label.toLowerCase().includes("environment")
            );
            this.state.selectedCameraId = backCamera ? backCamera.id : devices[0].id;

            // Initialize scanner
            this.scanner = new window.Html5Qrcode(this.scannerContainerId);

            await this.startScanning();
            this.state.isInitializing = false;
        } catch (error) {
            console.error("Scanner initialization error:", error);
            this.state.error = error.message || _t("Failed to initialize scanner");
            this.state.isInitializing = false;
        }
    }

    /**
     * Start the scanning process
     */
    async startScanning() {
        if (!this.scanner || this.state.isScanning) {
            return;
        }

        try {
            this.state.error = null;
            const config = {
                fps: 10,
                qrbox: { width: 250, height: 250 },
                aspectRatio: 1.0,
                formatsToSupport: this.getSupportedFormats(),
                experimentalFeatures: {
                    useBarCodeDetectorIfSupported: true,
                },
            };

            await this.scanner.start(
                this.state.selectedCameraId,
                config,
                (decodedText, decodedResult) => this.onScanSuccess(decodedText, decodedResult),
                (errorMessage) => this.onScanError(errorMessage)
            );

            this.state.isScanning = true;
        } catch (error) {
            console.error("Failed to start scanning:", error);
            this.state.error = error.message || _t("Failed to start camera");
        }
    }

    /**
     * Stop the scanning process
     */
    async stopScanning() {
        if (!this.scanner || !this.state.isScanning) {
            return;
        }

        try {
            await this.scanner.stop();
            this.state.isScanning = false;
        } catch (error) {
            console.error("Failed to stop scanning:", error);
        }
    }

    /**
     * Handle successful scan
     */
    onScanSuccess(decodedText, decodedResult) {
        // Prevent duplicate scans
        if (this.state.lastScanned === decodedText) {
            return;
        }

        this.state.lastScanned = decodedText;

        // Clear the last scanned after delay to allow re-scanning same barcode
        setTimeout(() => {
            if (this.state.lastScanned === decodedText) {
                this.state.lastScanned = null;
            }
        }, 2000);

        // Get format info
        const formatName = decodedResult?.result?.format?.formatName || "Unknown";

        // Call the onScan callback
        this.props.onScan({
            barcode: decodedText,
            format: formatName,
            raw: decodedResult,
        });
    }

    /**
     * Handle scan errors (called frequently when no barcode in view)
     */
    onScanError(errorMessage) {
        // Don't show errors for "no barcode found" - this is normal
        // Only log actual errors
        if (errorMessage && !errorMessage.includes("No MultiFormat Readers")) {
            console.debug("Scan error:", errorMessage);
        }
    }

    /**
     * Switch to a different camera
     */
    async switchCamera(cameraId) {
        if (cameraId === this.state.selectedCameraId) {
            return;
        }

        await this.stopScanning();
        this.state.selectedCameraId = cameraId;
        await this.startScanning();
    }

    /**
     * Toggle camera (switch between front and back)
     */
    async toggleCamera() {
        if (this.state.cameras.length < 2) {
            return;
        }

        const currentIndex = this.state.cameras.findIndex(
            (c) => c.id === this.state.selectedCameraId
        );
        const nextIndex = (currentIndex + 1) % this.state.cameras.length;
        await this.switchCamera(this.state.cameras[nextIndex].id);
    }

    /**
     * Clean up scanner on component unmount
     */
    async destroyScanner() {
        await this.stopScanning();
        if (this.scanner) {
            try {
                await this.scanner.clear();
            } catch (error) {
                console.error("Failed to clear scanner:", error);
            }
            this.scanner = null;
        }
    }

    /**
     * Close the dialog
     */
    onCloseClick() {
        this.props.onClose();
        this.props.close();
    }

    /**
     * Get current camera label
     */
    get currentCameraLabel() {
        const camera = this.state.cameras.find((c) => c.id === this.state.selectedCameraId);
        return camera ? camera.label : _t("Unknown Camera");
    }

    /**
     * Check if multiple cameras are available
     */
    get hasMultipleCameras() {
        return this.state.cameras.length > 1;
    }
}
