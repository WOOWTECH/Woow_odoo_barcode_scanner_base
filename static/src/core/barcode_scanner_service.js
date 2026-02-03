/** @odoo-module **/

import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { _t } from "@web/core/l10n/translation";
import { BarcodeScannerDialog } from "./barcode_scanner_dialog";

/**
 * Barcode Scanner Service
 *
 * Provides barcode/QR scanning functionality throughout the application.
 * Can be used from any OWL component via useService("barcodeScanner").
 */
export const barcodeScannerService = {
    dependencies: ["dialog", "notification", "orm"],

    start(env, { dialog, notification, orm }) {
        // Access user context from env if available
        const getUserContext = () => env.services?.user?.context || {};
        // Sound effects (data URLs for small audio clips)
        const successSound = new Audio(
            "data:audio/wav;base64,UklGRnoGAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQoGAACBhYqFbF1fdWuKr5aGl4V7dnRzbW1ujJevqJiMhoF/gYGDiYqKi4qIhoSCgoOEhYaHh4eGhYSDgoGAgH9/f39/f4CAgICAgICAgIB/f39/f39/f4CAgICAgICAgH9/f39/f39/gICAgICAgICAf39/f39/f3+AgICAgICAgIB/f39/f39/f4CAgICAgICAgH9/f39/f39/"
        );
        const errorSound = new Audio(
            "data:audio/wav;base64,UklGRl9vT19teleEhICAf39/gICAgH9/f4CAgICAgICAf39/f4CAgICAgICAf39/f4CAgICAgICAf39/f4CAgICAgICAf39/f4CAgICAgICAf39/f4CAgICAgICAf39/f4CAgICAgICAf39/f4CAgICAgICAf39/f4CAgICAgICAf39/f4CAgICAgICAf39/f4CAgICAgICAf39/f4CAgICAgICA"
        );

        let enableSound = true;
        let scanMode = "all";
        let autoIncrement = true;

        // Load settings
        async function loadSettings() {
            try {
                const settings = await orm.searchRead(
                    "ir.config_parameter",
                    [
                        [
                            "key",
                            "in",
                            [
                                "barcode_scanner.enable_sound",
                                "barcode_scanner.scan_mode",
                                "barcode_scanner.auto_increment",
                            ],
                        ],
                    ],
                    ["key", "value"]
                );

                for (const setting of settings) {
                    switch (setting.key) {
                        case "barcode_scanner.enable_sound":
                            enableSound = setting.value !== "False";
                            break;
                        case "barcode_scanner.scan_mode":
                            scanMode = setting.value || "all";
                            break;
                        case "barcode_scanner.auto_increment":
                            autoIncrement = setting.value !== "False";
                            break;
                    }
                }
            } catch (error) {
                console.warn("Could not load barcode scanner settings:", error);
            }
        }

        // Initialize settings
        loadSettings();

        /**
         * Play success sound
         */
        function playSuccessSound() {
            if (enableSound) {
                try {
                    successSound.currentTime = 0;
                    successSound.play().catch(() => {});
                } catch (e) {
                    // Ignore audio errors
                }
            }
        }

        /**
         * Play error sound
         */
        function playErrorSound() {
            if (enableSound) {
                try {
                    errorSound.currentTime = 0;
                    errorSound.play().catch(() => {});
                } catch (e) {
                    // Ignore audio errors
                }
            }
        }

        /**
         * Show success notification
         */
        function showSuccess(message) {
            playSuccessSound();
            notification.add(message, {
                type: "success",
                sticky: false,
            });
        }

        /**
         * Show error notification
         */
        function showError(message) {
            playErrorSound();
            notification.add(message, {
                type: "danger",
                sticky: false,
            });
        }

        /**
         * Show warning notification
         */
        function showWarning(message) {
            notification.add(message, {
                type: "warning",
                sticky: false,
            });
        }

        /**
         * Open the barcode scanner dialog
         *
         * @param {Object} options
         * @param {Function} options.onScan - Callback when barcode is scanned
         * @param {Function} [options.onClose] - Callback when dialog is closed
         * @param {Array} [options.allowedFormats] - Restrict to specific formats
         * @param {string} [options.title] - Dialog title
         * @returns {Function} Close function
         */
        function openScanner(options = {}) {
            const { onScan, onClose, allowedFormats, title } = options;

            return dialog.add(BarcodeScannerDialog, {
                onScan: (result) => {
                    if (onScan) {
                        onScan(result);
                    }
                },
                onClose: () => {
                    if (onClose) {
                        onClose();
                    }
                },
                allowedFormats: allowedFormats || [],
                title: title || _t("Scan Barcode"),
                scanMode: scanMode,
            });
        }

        /**
         * Find a product by barcode
         *
         * @param {string} barcode - The barcode to search for
         * @param {Object} [options]
         * @param {number} [options.companyId] - Company ID to filter by
         * @returns {Promise<Object>} Product info or error
         */
        async function findProductByBarcode(barcode, options = {}) {
            const userContext = getUserContext();
            const companyId = options.companyId || userContext?.allowed_company_ids?.[0];

            try {
                const result = await orm.call(
                    "product.product",
                    "find_by_barcode_with_info",
                    [barcode, companyId]
                );

                if (result.product) {
                    return {
                        success: true,
                        product: result.product,
                        barcodeType: result.barcode_type,
                        gs1Data: result.gs1_data,
                    };
                } else {
                    return {
                        success: false,
                        error: result.error || _t("Product not found"),
                    };
                }
            } catch (error) {
                console.error("Error finding product by barcode:", error);
                return {
                    success: false,
                    error: error.message || _t("Error searching for product"),
                };
            }
        }

        /**
         * Parse a GS1-128 barcode
         *
         * @param {string} barcode - The barcode to parse
         * @returns {Promise<Object>} Parsed GS1 data
         */
        async function parseGS1Barcode(barcode) {
            try {
                const result = await orm.call("barcode.gs1.parser", "parse", [barcode]);
                return result;
            } catch (error) {
                console.error("Error parsing GS1 barcode:", error);
                return { is_gs1: false };
            }
        }

        /**
         * Open scanner and automatically find product
         *
         * @param {Object} options
         * @param {Function} options.onProduct - Callback with found product
         * @param {Function} [options.onNotFound] - Callback when product not found
         * @param {Function} [options.onClose] - Callback when dialog closed
         * @param {boolean} [options.keepOpen=false] - Keep dialog open after scan
         * @returns {Function} Close function
         */
        function scanForProduct(options = {}) {
            const { onProduct, onNotFound, onClose, keepOpen = false } = options;

            let closeDialog;

            const handleScan = async (result) => {
                const productResult = await findProductByBarcode(result.barcode);

                if (productResult.success) {
                    showSuccess(
                        _t("Found: %s", productResult.product.display_name || productResult.product.name)
                    );
                    if (onProduct) {
                        onProduct({
                            ...productResult,
                            scanResult: result,
                        });
                    }
                    if (!keepOpen && closeDialog) {
                        closeDialog();
                    }
                } else {
                    showError(productResult.error);
                    if (onNotFound) {
                        onNotFound({
                            barcode: result.barcode,
                            error: productResult.error,
                            scanResult: result,
                        });
                    }
                }
            };

            closeDialog = openScanner({
                onScan: handleScan,
                onClose: onClose,
                title: _t("Scan Product"),
            });

            return closeDialog;
        }

        return {
            openScanner,
            findProductByBarcode,
            parseGS1Barcode,
            scanForProduct,
            showSuccess,
            showError,
            showWarning,
            playSuccessSound,
            playErrorSound,
            get enableSound() {
                return enableSound;
            },
            set enableSound(value) {
                enableSound = value;
            },
            get scanMode() {
                return scanMode;
            },
            get autoIncrement() {
                return autoIncrement;
            },
        };
    },
};

// Register the service
registry.category("services").add("barcodeScanner", barcodeScannerService);
