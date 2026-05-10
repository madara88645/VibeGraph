import { User, Admin } from './models.js';

export default {
    async fetchData() {
        const u = new User('api_user');
        return u.getName();
    }
}

export const fetchAdminData = async () => {
    const a = new Admin('api_admin');
    return a.getName();
};
