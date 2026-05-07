import { fetchUserData } from './api.js';
import { UserRecord } from './models.js';
import { formatDisplayName } from './utils.js';

/** Dashboard shell — ties models, API, and presentation helpers. */
export class DashboardController {
  constructor() {
    this.label = 'demo';
  }

  async loadPrimaryUser() {
    const remote = await fetchUserData(1);
    const record = new UserRecord(remote.id, remote.name);
    return formatDisplayName(record);
  }

  renderBootstrapHint() {
    return 'ready';
  }
}
