// SPDX-License-Identifier: MIT
pragma solidity 0.8.28;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "@openzeppelin/contracts/utils/ReentrancyGuard.sol";

contract CampaignToken is ERC20 {
    constructor(string memory name, string memory symbol, uint256 supply, address recipient)
        ERC20(name, symbol)
    {
        _mint(recipient, supply);
    }
}

contract Campaign is ReentrancyGuard {
    address public immutable issuer;
    CampaignToken public immutable token;
    uint256 public immutable price;
    uint256 public immutable goal;
    uint256 public immutable cap;
    uint256 public immutable deadline;
    uint256 public raised;
    uint256 public sold;
    bool public paidOut;
    bool public inventoryRecovered;
    mapping(address => uint256) public contributions;
    mapping(address => uint256) public allocations;

    event Contribution(address indexed participant, uint256 amount, uint256 tokens);
    event Claimed(address indexed participant, uint256 tokens);
    event Refunded(address indexed participant, uint256 amount);
    event Withdrawn(uint256 amount);

    constructor(address issuer_, string memory name, string memory symbol, uint256 price_,
        uint256 goal_, uint256 cap_, uint256 deadline_)
    {
        require(price_ > 0 && cap_ > 0 && cap_ <= type(uint256).max / 1 ether, "Invalid price or supply");
        require(price_ <= type(uint256).max / cap_, "Invalid price or supply");
        require(goal_ > 0 && goal_ <= price_ * cap_, "Invalid goal");
        require(deadline_ > block.timestamp, "Invalid deadline");
        issuer = issuer_;
        price = price_;
        goal = goal_;
        cap = cap_;
        deadline = deadline_;
        token = new CampaignToken(name, symbol, cap_ * 1 ether, address(this));
    }

    function contribute(uint256 quantity) external payable nonReentrant {
        require(block.timestamp < deadline, "Campaign ended");
        require(quantity > 0 && quantity <= cap - sold, "Invalid quantity");
        require(msg.value == quantity * price, "Incorrect payment");
        raised += msg.value;
        sold += quantity;
        contributions[msg.sender] += msg.value;
        allocations[msg.sender] += quantity;
        emit Contribution(msg.sender, msg.value, quantity);
    }

    function claim() external nonReentrant {
        require(block.timestamp >= deadline && raised >= goal, "Campaign not successful");
        uint256 amount = allocations[msg.sender];
        require(amount > 0, "Nothing to claim");
        allocations[msg.sender] = 0;
        require(token.transfer(msg.sender, amount * 1 ether), "Transfer failed");
        emit Claimed(msg.sender, amount);
    }

    function refund() external nonReentrant {
        require(block.timestamp >= deadline && raised < goal, "Refund unavailable");
        uint256 amount = contributions[msg.sender];
        require(amount > 0, "Nothing to refund");
        contributions[msg.sender] = 0;
        _pay(msg.sender, amount);
        emit Refunded(msg.sender, amount);
    }

    function withdraw() external nonReentrant {
        require(msg.sender == issuer, "Issuer only");
        require(block.timestamp >= deadline && raised >= goal && !paidOut, "Withdrawal unavailable");
        paidOut = true;
        _pay(issuer, raised);
        emit Withdrawn(raised);
    }

    function recoverInventory() external nonReentrant {
        require(msg.sender == issuer, "Issuer only");
        require(block.timestamp >= deadline && !inventoryRecovered, "Recovery unavailable");
        inventoryRecovered = true;
        uint256 quantity = raised >= goal ? cap - sold : cap;
        require(token.transfer(issuer, quantity * 1 ether), "Transfer failed");
    }

    function _pay(address recipient, uint256 amount) private {
        (bool success,) = payable(recipient).call{value: amount}("");
        require(success, "Payment failed");
    }
}

contract Launchpad {
    mapping(bytes32 => mapping(address => address)) public campaigns;
    event CampaignCreated(bytes32 indexed referenceId, address indexed issuer, address campaign);

    function createCampaign(bytes32 referenceId, string calldata name, string calldata symbol,
        uint256 price, uint256 goal, uint256 cap, uint256 deadline) external returns (address)
    {
        require(referenceId != bytes32(0) && campaigns[referenceId][msg.sender] == address(0), "Campaign already exists");
        Campaign campaign = new Campaign(msg.sender, name, symbol, price, goal, cap, deadline);
        campaigns[referenceId][msg.sender] = address(campaign);
        emit CampaignCreated(referenceId, msg.sender, address(campaign));
        return address(campaign);
    }
}
