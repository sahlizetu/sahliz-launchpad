const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const {test} = require('node:test');
const ganache = require('ganache');
const {ethers} = require('ethers');

const window = {};
vm.runInNewContext(fs.readFileSync('static/contracts.js', 'utf8'), {window});
const {Launchpad, Campaign, CampaignToken} = window.launchpadContracts;

test('two issuers, successful claim and payout, failed campaign refund', async () => {
    const rpc = ganache.provider({logging: {quiet: true}});
    try {
        const provider = new ethers.BrowserProvider(rpc, undefined, {cacheTimeout: -1});
        provider.pollingInterval = 25;
        const [academy, greenbox, buyer] = await Promise.all([0, 1, 2].map(index => provider.getSigner(index)));
        const factory = await new ethers.ContractFactory(Launchpad.abi, Launchpad.evm.bytecode.object, academy).deploy();
        await factory.waitForDeployment();
        const price = ethers.parseEther('0.00001');
        const goal = price * 100n;
        const deadline = (await provider.getBlock('latest')).timestamp + 120;
        const launch = async (issuer, name, symbol) => {
            const ref = ethers.id(name);
            await (await factory.connect(issuer).createCampaign(ref, name, symbol, price, goal, 500, deadline)).wait();
            return new ethers.Contract(await factory.campaigns(ref, issuer.address), Campaign.abi, buyer);
        };
        const a = await launch(academy, 'Data Academy', 'DAP');
        const b = await launch(greenbox, 'GreenBox', 'GBC');
        assert.notEqual(a.target, b.target);
        await assert.rejects(a.contribute.staticCall(501, {value: price * 501n}));
        await assert.rejects(a.contribute.staticCall(1, {value: 0}));
        await (await a.contribute(100, {value: goal})).wait();
        await (await b.contribute(10, {value: price * 10n})).wait();
        await assert.rejects(a.claim.staticCall());
        await assert.rejects(b.refund.staticCall());
        await rpc.request({method:'evm_increaseTime', params:[121]});
        await rpc.request({method:'evm_mine', params:[]});
        await assert.rejects(a.contribute.staticCall(1, {value: price}));
        await assert.rejects(a.refund.staticCall());
        await assert.rejects(b.claim.staticCall());
        await assert.rejects(a.withdraw.staticCall());
        await assert.rejects(b.connect(greenbox).withdraw.staticCall());
        await (await a.connect(academy).recoverInventory()).wait();
        await (await a.connect(academy).withdraw()).wait();
        await (await a.claim()).wait();
        const token = new ethers.Contract(await a.token(), CampaignToken.abi, provider);
        assert.equal(await token.balanceOf(buyer.address), ethers.parseEther('100'));
        assert.equal(await token.balanceOf(academy.address), ethers.parseEther('400'));
        await assert.rejects(a.claim.staticCall());
        await (await b.refund()).wait();
        assert.equal(await b.contributions(buyer.address), 0n);
        assert.equal(await provider.getBalance(b.target), 0n);
        assert.equal(await provider.getBalance(a.target), 0n);
        await assert.rejects(b.refund.staticCall());
    } finally {
        await rpc.disconnect();
    }
});

test('approved terms bind fee deployment and commission applies only to successful withdrawals', async () => {
    const rpc = ganache.provider({logging: {quiet: true}});
    try {
        const provider = new ethers.BrowserProvider(rpc, undefined, {cacheTimeout: -1});
        provider.pollingInterval = 25;
        const [admin, issuer, buyer, treasury] = await Promise.all(
            [0, 1, 2, 3].map(index => provider.getSigner(index))
        );
        const artifact = window.launchpadContracts.LaunchpadWithFees;
        const factory = await new ethers.ContractFactory(artifact.abi, artifact.evm.bytecode.object, admin)
            .deploy(treasury.address);
        await factory.waitForDeployment();
        const price = ethers.parseEther('0.00001');
        const goal = price * 100n;
        const fee = ethers.parseEther('0.0001');
        const terms = ['Test Token', 'TEST', price, goal, 500, 120];
        const successRef = ethers.id('success');
        const failRef = ethers.id('failure');
        const issuerFactory = factory.connect(issuer);
        await assert.rejects(issuerFactory.createCampaign.staticCall(successRef, terms, 20, {value: fee}));
        await assert.rejects(issuerFactory.approve.staticCall(successRef, issuer.address, terms, 20));
        for (const rate of [4, 51]) {
            await assert.rejects(factory.approve.staticCall(successRef, issuer.address, terms, rate));
        }
        const initial = await provider.getBalance(treasury.address);
        for (const ref of [successRef, failRef]) {
            await (await factory.approve(ref, issuer.address, terms, 20)).wait();
            await assert.rejects(issuerFactory.createCampaign.staticCall(ref, terms, 21, {value: fee}));
            await assert.rejects(issuerFactory.createCampaign.staticCall(ref, terms, 20, {value: 0}));
            await (await issuerFactory.createCampaign(ref, terms, 20, {value: fee})).wait();
        }
        assert.equal(await provider.getBalance(treasury.address), initial + fee * 2n);
        const campaign = async ref => new ethers.Contract(
            await factory.campaigns(ref, issuer.address), Campaign.abi, buyer
        );
        const success = await campaign(successRef);
        const failed = await campaign(failRef);
        await (await success.contribute(100, {value: goal})).wait();
        await (await failed.contribute(1, {value: price})).wait();
        await rpc.request({method: 'evm_increaseTime', params: [121]});
        await rpc.request({method: 'evm_mine', params: []});
        await (await failed.refund()).wait();
        assert.equal(await provider.getBalance(failed.target), 0n);
        assert.equal(await provider.getBalance(treasury.address), initial + fee * 2n);
        await (await success.connect(issuer).withdraw()).wait();
        assert.equal(await provider.getBalance(treasury.address), initial + fee * 2n + goal / 5n);
        assert.equal(await provider.getBalance(success.target), 0n);
        await (await success.claim()).wait();
    } finally {
        await rpc.disconnect();
    }
});
