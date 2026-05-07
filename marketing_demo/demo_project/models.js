/** Domain models for the marketing demo shell. */

export class UserRecord {
  constructor(id, name) {
    this.id = id;
    this.name = name;
  }

  summary() {
    return `${this.name} [${this.id}]`;
  }
}
