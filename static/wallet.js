const button = document.getElementById('verify-wallet');
const form = document.getElementById('wallet-form');
const mobileLink = document.getElementById('open-wallet-browser');

if (!window.ethereum && location.protocol === 'https:' && /Android|iPhone|iPad|iPod/.test(navigator.userAgent)) {
    mobileLink.href = 'https://link.metamask.io/dapp/' + location.host + location.pathname;
    mobileLink.hidden = false;
}

button.addEventListener('click', async () => {
    button.disabled = true;
    try {
        if (!window.ethereum) throw Error(gettext("Open this page in a browser with MetaMask."));
        await window.ethereum.request({ method: 'eth_requestAccounts' });
        const provider = new ethers.BrowserProvider(window.ethereum);
        const signer = await provider.getSigner();
        const message = JSON.parse(document.getElementById('wallet-message').textContent);
        form.elements.wallet.value = await signer.getAddress();
        form.elements.signature.value = await signer.signMessage(message);
        form.requestSubmit();
    } catch (error) {
        document.getElementById('wallet-status').textContent = error.shortMessage || error.message;
        button.disabled = false;
    }
});
