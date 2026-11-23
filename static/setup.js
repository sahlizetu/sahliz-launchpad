function bindDeployment(buttonId, resultId, addressId, contractName) {
    const deploy = document.getElementById(buttonId);
    if (!deploy) return;
    const result = document.getElementById(resultId);
    deploy.onclick = async () => {
        deploy.disabled = true;
        try {
            if (!window.ethereum) throw Error(gettext("MetaMask is required."));
            await window.ethereum.request({method: 'eth_requestAccounts'});
            await window.ethereum.request({method: 'wallet_switchEthereumChain', params: [{chainId: '0xaa36a7'}]});
            const provider = new ethers.BrowserProvider(window.ethereum);
            const signer = await provider.getSigner();
            const artifact = window.launchpadContracts[contractName];
            const factory = new ethers.ContractFactory(artifact.abi, artifact.evm.bytecode.object, signer);
            const contract = await factory.deploy(...(deploy.dataset.treasury ? [deploy.dataset.treasury] : []));
            result.textContent = gettext("Deployment awaiting confirmation.");
            await contract.waitForDeployment();
            document.getElementById(addressId).value = await contract.getAddress();
            result.textContent = gettext("Deployment confirmed.");
        } catch (error) {
            result.textContent = error.shortMessage || error.message;
            deploy.disabled = false;
        }
    };
}

bindDeployment('deploy-factory', 'result', 'factory-address', 'Launchpad');
bindDeployment('deploy-fee-factory', 'fee-result', 'fee-factory-address', 'LaunchpadWithFees');
