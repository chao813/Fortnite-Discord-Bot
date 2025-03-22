const fs = require('fs');
const path = require('path');
const os = require('os');

/**
 * Loads and processes the config file.
 *
 * @returns {object} Merged and processed config
 */
function initializeConfig() {
    const config = loadAndMergeConfigs();
    validateConfig(config);
    return overrideWithOsSpecificConfig(config);
}

/**
 * Loads and merges the base and local configs.
 *
 * @returns {object} Merged config object
 */
function loadAndMergeConfigs() {
    const configPath = path.join(__dirname, '../config/config.json');
    const localConfigPath = path.join(__dirname, '../config/config-local.json');

    let config;
    try {
        config = JSON.parse(fs.readFileSync(configPath, 'utf-8'));
    } catch (error) {
        console.error(`Error loading base config: ${error}`);
        throw new Error(`Failed to load config file: ${error.message}`);
    }

    return mergeLocalConfig(config, localConfigPath);
}

/**
 * Merges local config with the base config if available.
 *
 * @param {object} baseConfig - Base config
 * @param {string} localConfigPath - Path to the local config file
 * @returns {object} Merged config
 */
function mergeLocalConfig(baseConfig, localConfigPath) {
    let config = { ...baseConfig };

    if (fs.existsSync(localConfigPath)) {
        const localConfig = JSON.parse(fs.readFileSync(localConfigPath, 'utf-8'));

        config = deepMerge(config, localConfig);

        console.log(`Additional configs loaded from local-config.json`);
    }

    return config;
}

/**
 * Deep merges two objects with the exception that arrays are replaced
 * and not merged.
 *
 * @param {object} target - Target object to merge into
 * @param {object} source - Source object to merge from
 * @returns {object} Merged object
 */
function deepMerge(target, source) {
    const output = { ...target };

    if (isObject(target) && isObject(source)) {
        Object.keys(source).forEach(key => {
            if (isObject(source[key])) {
                if (!(key in target)) {
                    output[key] = source[key];
                } else {
                    output[key] = deepMerge(target[key], source[key]);
                }
            } else {
                output[key] = source[key];
            }
        });
    }

    return output;
}

/**
 * Checks if value is an object.
 *
 * @param {*} item - Item to check
 * @returns {boolean} True if item is an object, otherwise false
 */
function isObject(item) {
    return (item && typeof item === 'object' && !Array.isArray(item));
}

/**
 * Validates that the config has the Fortnite guidToPlayerName mapping.
 *
 * @param {object} config - Config to validate
 */
function validateConfig(config) {
    const guidMapIsEmpty = !config.fortnite?.guidToPlayerName ||
                           Object.keys(config.fortnite.guidToPlayerName).length === 0;

    if (guidMapIsEmpty) {
        throw new Error(
            "Missing guid to player name mappings. Please create a config-local.json file with " +
            "fortnite.guidToPlayerName defined before trying again."
        );
    }
}

/**
 * Override the config with predefined configs for the current
 * Operating System.
 *
 * @param {object} config - Config to process
 * @returns {object} Config with OS-specific configs overridden
 */
function overrideWithOsSpecificConfig(config) {
    const result = { ...config };
    const platform = os.platform();

    if (platform === 'win32') {
        let windowsConfig = { ...config.fileMonitor.windows };

        // Replace environment variables in paths
        if (windowsConfig.replaysDirectory.includes('%LOCALAPPDATA%')) {
            windowsConfig.replaysDirectory = windowsConfig.replaysDirectory.replace(
                '%LOCALAPPDATA%',
                process.env.LOCALAPPDATA || ''
            );
        }

        result.fileMonitor = windowsConfig;
    } else {
        result.fileMonitor = config.fileMonitor.mac;
    }

    return result;
}

module.exports = {
    initializeConfig,
};
