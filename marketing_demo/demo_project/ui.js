import { fetchUserData } from './api.js';
import { UserRecord } from './models.js';
import { formatDisplayName } from './utils.js';

/** Coordinates startup loading for the demo shell. */
export class DashboardController {
  constructor(rootSelector = '#app') {
    this.rootSelector = rootSelector;
  }

  initialize() {
    return this.loadPrimaryUser();
  }

  async loadPrimaryUser() {
    const remote = await fetchUserData(1);
    const record = new UserRecord(remote.id, remote.name);
    return formatDisplayName(record);
  }

  renderHint(label) {
    return `Dashboard ready: ${label}`;
  }
}
