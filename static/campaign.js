const config = JSON.parse(document.getElementById('campaign-config').textContent);
const get = id => document.getElementById(id);
const { Launchpad, LaunchpadWithFees, Campaign, CampaignToken } = window.launchpadContracts;
const factoryABI = config.requiresFee ? LaunchpadWithFees.abi : Launchpad.abi;
const terms = () => [config.name, config.symbol, ethers.parseEther(config.price),
    ethers.parseEther(config.goal), config.cap, config.duration * 60];
const SEPOLIA = '0xaa36a7';
const amount = value => ethers.formatEther(value) + ' ETH';
let provider;
let signer;
let wallet;
let busy = false;
let activeCampaign;
let tokenPrice;
let available;

function showLink(container, kind, hash, label) {
    const link = document.createElement('a');
    link.href = 'https://sepolia.etherscan.io/' + kind + '/' + hash;
    link.target = '_blank';
    link.rel = 'noopener noreferrer';
    link.textContent = label;
    container.append(link, document.createTextNode(' '));
}

async function refresh() {
    activeCampaign = null;
    for (const element of document.querySelectorAll('[data-action], #payment, #metrics')) {
        element.hidden = true;
    }
    get('links').replaceChildren();
    if (get('publish-campaign')) get('publish-campaign').hidden = true;
    if (!ethers.isAddress(config.factory)) {
        get('state').textContent = gettext("Sepolia deployment needs to be configured.");
        return;
    }
    if (!wallet) {
        get('state').textContent = gettext("Connect MetaMask to view campaign data on Sepolia.");
        return;
    }
    if (await window.ethereum.request({method: 'eth_chainId'}) !== SEPOLIA) {
        get('state').textContent = gettext("Reconnect MetaMask on Sepolia.");
        return;
    }
    const factory = new ethers.Contract(config.factory, factoryABI, provider);
    const address = await factory.campaigns(config.reference, config.issuer);
    const issuer = wallet.toLowerCase() === config.issuer.toLowerCase();
    if (address === ethers.ZeroAddress) {
        get('state').textContent = gettext("Campaign approved and awaiting deployment by the startup.");
        if (config.requiresFee) {
            const approval = await factory.approvals(config.reference, config.issuer);
            const expected = ethers.keccak256(ethers.AbiCoder.defaultAbiCoder().encode(
                ['tuple(string,string,uint256,uint256,uint256,uint256)', 'uint16'],
                [terms(), config.commission]
            ));
            const ready = approval === expected;
            if (!ready) get('state').textContent = gettext("Awaiting approval on Sepolia.");
            if (get('approve-on-chain')) {
                get('approve-on-chain').hidden = ready || (await factory.owner()).toLowerCase() !== wallet.toLowerCase();
            }
            if (get('launch')) get('launch').hidden = !issuer || !ready;
        } else if (get('launch')) get('launch').hidden = !issuer;
        return;
    }
    if (get('publish-campaign')) get('publish-campaign').hidden = !issuer;
    const sale = new ethers.Contract(address, Campaign.abi, signer);
    const block = await provider.getBlock('latest');
    const calls = {blockTag: block.number};
    const [deadline, raised, goal, price, cap, sold, allocation, contribution, paid, recovered, tokenAddress] =
        await Promise.all([sale.deadline(calls), sale.raised(calls), sale.goal(calls), sale.price(calls),
            sale.cap(calls), sale.sold(calls), sale.allocations(wallet, calls), sale.contributions(wallet, calls),
            sale.paidOut(calls), sale.inventoryRecovered(calls), sale.token(calls)]);
    const token = new ethers.Contract(tokenAddress, CampaignToken.abi, provider);
    const [symbol, tokenBalance] = await Promise.all([token.symbol(calls), token.balanceOf(wallet, calls)]);
    activeCampaign = sale;
    tokenPrice = price;
    available = cap - sold;
    const ended = BigInt(block.timestamp) >= deadline;
    const succeeded = raised >= goal;
    get('state').textContent = ended ? (succeeded ? gettext("Closed · goal met") : gettext("Closed · refunds available")) : gettext("Campaign open");
    get('token-symbol').textContent = symbol;
    get('goal').textContent = amount(goal);
    get('price').textContent = amount(price);
    get('raised').textContent = amount(raised);
    get('remaining').textContent = available;
    get('deadline').textContent = gettext("Closes") + ": " + new Date(Number(deadline) * 1000).toLocaleString(document.documentElement.lang) +
        " · " + gettext("Your balance") + ": " + ethers.formatUnits(tokenBalance, 18) + ' ' + symbol;
    get('metrics').hidden = false;
    get('payment').hidden = ended || available === 0n;
    get('claim').hidden = !ended || !succeeded || allocation === 0n;
    get('refund').hidden = !ended || succeeded || contribution === 0n;
    get('withdraw').hidden = !issuer || !ended || !succeeded || paid;
    get('recover').hidden = !issuer || !ended || recovered || (succeeded && available === 0n);
    showLink(get('links'), 'address', address, gettext("Campaign contract ↗"));
    showLink(get('links'), 'address', tokenAddress, gettext("Token ↗"));
    quote();
}

function quantity() {
    const input = get('quantity').value;
    if (!/^[1-9]\d*$/.test(input) || BigInt(input) > available) {
        throw Error(gettext("Choose a quantity between 1 and the available supply."));
    }
    return BigInt(input);
}

function quote() {
    if (!activeCampaign) return;
    try { get('quote').textContent = gettext("Amount") + ": " + amount(quantity() * tokenPrice); }
    catch (error) { get('quote').textContent = error.message; }
}

async function run(action) {
    if (busy) return;
    busy = true;
    const buttons = document.querySelectorAll('button');
    for (const button of buttons) button.disabled = true;
    try { await action(); }
    catch (error) {
        get('status').textContent = error.code === 'ACTION_REJECTED'
            ? gettext("Request canceled in MetaMask.") : error.reason || error.shortMessage || error.message;
    } finally {
        busy = false;
        for (const button of buttons) button.disabled = false;
    }
}

async function transact(send) {
    await refresh();
    get('status').textContent = gettext("Confirm in MetaMask.");
    const transaction = await send();
    get('transaction').replaceChildren();
    showLink(get('transaction'), 'tx', transaction.hash, gettext("View transaction ↗"));
    get('status').textContent = gettext("Transaction awaiting confirmation.");
    await transaction.wait();
    get('status').textContent = gettext("Transaction confirmed.");
    try { await refresh(); }
    catch { get('status').textContent = gettext("Transaction confirmed. Refresh to view updated data."); }
}

const mobileWallet = get('mobile-wallet');
const isMobile = /Android|iPhone|iPad|iPod/.test(navigator.userAgent)
    || (navigator.platform === 'MacIntel' && navigator.maxTouchPoints > 1);
if (isMobile && !window.ethereum && location.protocol === 'https:') {
    mobileWallet.href = 'https://link.metamask.io/dapp/' + location.host + location.pathname;
    mobileWallet.hidden = false;
    get('connect').hidden = true;
    get('state').textContent = gettext("Open the campaign in MetaMask to view its Sepolia status.");
}

get('refresh').onclick = () => run(refresh);
get('connect').onclick = () => run(async () => {
    if (!window.ethereum) throw Error(gettext("Open this page in a browser with MetaMask."));
    await window.ethereum.request({method: 'eth_requestAccounts'});
    await window.ethereum.request({method: 'wallet_switchEthereumChain', params: [{chainId: SEPOLIA}]});
    provider = new ethers.BrowserProvider(window.ethereum);
    signer = await provider.getSigner();
    wallet = await signer.getAddress();
    get('connect').textContent = wallet.slice(0, 8) + '…' + wallet.slice(-4);
    get('refresh').hidden = false;
    await refresh();
    get('status').textContent = gettext("MetaMask connected on Sepolia.");
});
if (get('approve-on-chain')) get('approve-on-chain').onclick = () => run(() => transact(() => {
    const factory = new ethers.Contract(config.factory, factoryABI, signer);
    return factory.approve(config.reference, config.issuer, terms(), config.commission);
}));
if (get('launch')) get('launch').onclick = () => run(() => transact(async () => {
    if (!wallet || get('launch').hidden) throw Error(gettext("Connect the startup wallet."));
    const factory = new ethers.Contract(config.factory, factoryABI, signer);
    if (config.requiresFee) {
        return factory.createCampaign(config.reference, terms(), config.commission, {value: await factory.registrationFee()});
    }
    const block = await provider.getBlock('latest');
    return factory.createCampaign(config.reference, config.name, config.symbol, ethers.parseEther(config.price),
        ethers.parseEther(config.goal), config.cap, block.timestamp + config.duration * 60);
}));
get('quantity').oninput = quote;
get('payment').onsubmit = event => {
    event.preventDefault();
    run(() => transact(() => {
        if (!activeCampaign || get('payment').hidden) throw Error(gettext("The campaign is closed."));
        const count = quantity();
        return activeCampaign.contribute(count, {value: count * tokenPrice});
    }));
};
for (const [id, method] of Object.entries({claim:'claim', refund:'refund', withdraw:'withdraw', recover:'recoverInventory'})) {
    get(id).onclick = () => run(() => transact(() => {
        if (!activeCampaign || get(id).hidden) throw Error(gettext("Action unavailable."));
        return activeCampaign[method]();
    }));
}
if (window.ethereum) {
    for (const event of ['accountsChanged', 'chainChanged']) {
        window.ethereum.on(event, () => {
            wallet = null;
            signer = null;
            get('connect').textContent = gettext("Reconnect MetaMask");
            get('refresh').hidden = true;
            refresh();
        });
    }
}
refresh();
