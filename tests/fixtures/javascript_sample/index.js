import api, { fetchAdminData } from './api.js';
import { setupUtils } from './utils.js';
import * as config from './config.js';

export async function main() {
    setupUtils();
    console.log(config.defaultConfig);
    const result = await api.fetchData();
    const admin = await fetchAdminData();
    return { result, admin };
}

export const helper = () => {
    return "help";
};
