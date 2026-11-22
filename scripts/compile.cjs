const fs = require('node:fs');
const solc = require('solc');
const source = 'contracts/Launchpad.sol';
const output = JSON.parse(solc.compile(JSON.stringify({
    language: 'Solidity',
    sources: { [source]: { content: fs.readFileSync(source, 'utf8') } },
    settings: { optimizer: { enabled: true, runs: 200 }, evmVersion: 'paris',
        outputSelection: { '*': { '*': ['abi', 'evm.bytecode.object'] } } }
}), { import: name => ({ contents: fs.readFileSync('node_modules/' + name, 'utf8') }) }));
for (const error of output.errors ?? []) {
    if (error.severity === 'error') throw new Error(error.formattedMessage);
}
const contracts = output.contracts[source];
fs.writeFileSync('static/contracts.js', 'window.launchpadContracts = ' + JSON.stringify(contracts) + ';\n');
