const fs = require('fs');
const { User } = require('./models.js');

function setupUtils() {
    const data = fs.readFileSync('data.txt');
    return new User('system');
}

module.exports = { setupUtils };
