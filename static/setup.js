const deploy = document.getElementById('deploy-factory');
const result = document.getElementById('result');

deploy.onclick = async () => {
    deploy.disabled = true;
    try {
        if (!window.ethereum) throw Error(gettext("MetaMask is required."));
        await window.ethereum.request({method: 'eth_requestAccounts'});
        await window.ethereum.request({method: 'wallet_switchEthereumChain', params: [{chainId: '0xaa36a7'}]});
        const provider = new ethers.BrowserProvider(window.ethereum);
        const signer = await provider.getSigner();
        const artifact = window.launchpadContracts.Launchpad;
        const factory = new ethers.ContractFactory(artifact.abi, artifact.evm.bytecode.object, signer);
        const contract = await factory.deploy();
        result.textContent = gettext("Deployment awaiting confirmation.");
        await contract.waitForDeployment();
        document.getElementById('factory-address').value = await contract.getAddress();
        result.textContent = gettext("Deployment confirmed.");
    } catch (error) {
        result.textContent = error.shortMessage || error.message;
        deploy.disabled = false;
    }
};
