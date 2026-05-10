export class User {
    constructor(name) {
        this.name = name;
    }

    getName() {
        return this.name;
    }

    static getRole() {
        return "user";
    }
}

export class Admin extends User {
    constructor(name) {
        super(name);
    }

    static getRole() {
        return "admin";
    }
}
