"""Tests for smart contract auditor module."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from quantchain.agents.smart_contract_auditor import (
    SmartContractAuditorConfig,
    ContractRetriever,
    SmartContractAuditorAgent,
    VulnerabilityScanner,
    FinancialAnalyzer,
    ContractSource,
    VulnerabilityReport,
    Vulnerability,
    TokenomicsAnalysis,
    ProtocolAnalysis,
    InvestmentRecommendation,
    AuditStatus,
    VulnerabilitySeverity,
)


class TestSmartContractAuditorConfig:
    """Test SmartContractAuditorConfig."""

    def test_default_config(self) -> None:
        """Test default configuration values."""
        config = SmartContractAuditorConfig()
        assert config.api_keys == {}
        assert config.etherscan_api_url == "https://api.etherscan.io/api"
        assert config.cache_expiry_seconds == 86400
        assert config.max_concurrent_requests == 5

    def test_custom_config(self) -> None:
        """Test custom configuration values."""
        config = SmartContractAuditorConfig(
            api_keys={"ethereum": "test_key"},
            etherscan_api_url="https://api.etherscan.io/api",
            cache_expiry_seconds=43200,
            max_concurrent_requests=3
        )
        assert config.api_keys == {"ethereum": "test_key"}
        assert config.cache_expiry_seconds == 43200
        assert config.max_concurrent_requests == 3


class TestAuditStatusAndSeverity:
    """Test audit status and vulnerability severity enums."""

    def test_audit_status_values(self) -> None:
        """Test audit status enum values."""
        assert AuditStatus.SECURE.value == "secure"
        assert AuditStatus.VULNERABLE.value == "vulnerable"
        assert AuditStatus.REQUIRES_REVIEW.value == "requires_review"
        assert AuditStatus.INSUFFICIENT_DATA.value == "insufficient_data"

    def test_vulnerability_severity_values(self) -> None:
        """Test vulnerability severity enum values."""
        assert VulnerabilitySeverity.CRITICAL.value == "critical"
        assert VulnerabilitySeverity.HIGH.value == "high"
        assert VulnerabilitySeverity.MEDIUM.value == "medium"
        assert VulnerabilitySeverity.LOW.value == "low"
        assert VulnerabilitySeverity.INFO.value == "info"


class TestContractRetriever:
    """Test ContractRetriever."""

    @pytest.fixture
    def config(self) -> SmartContractAuditorConfig:
        """Create test configuration."""
        config = SmartContractAuditorConfig()
        config.api_keys = {"ethereum": "test_key"}
        return config

    @pytest.fixture
    def retriever(self, config) -> ContractRetriever:
        """Create a ContractRetriever instance."""
        return ContractRetriever(config)

    @patch("urllib.request.urlopen")
    def test_get_contract_source_success(
        self, mock_urlopen, retriever
    ) -> None:
        """Test successful contract source retrieval."""
        contract = retriever.get_contract_source("0x123", "ethereum")
        assert contract.address == "0x123"
        assert contract.network == "ethereum"
        assert "MockToken" in contract.source_code
        assert contract.contract_name == "MockToken"

    def test_detect_contract_type_erc20(self, retriever) -> None:
        """Test ERC20 contract type detection."""
        erc20_code = """
        contract ERC20Token {
            string public name;
            string public symbol;
            uint8 public decimals;
            uint256 public totalSupply;
            mapping(address => uint256) public balanceOf;
            function transfer(address to, uint256 amount) public returns (bool);
        }
        """
        contract_source = ContractSource(
            address="0x123",
            source_code=erc20_code,
            abi="[]",
            contract_name="ERC20Token",
            compiler_version="v0.8.0",
            optimization_enabled=True,
            constructor_arguments="",
            network="ethereum"
        )
        contract_type = retriever.detect_contract_type(contract_source)
        assert "ERC20" in contract_type

    def test_detect_contract_type_erc721(self, retriever) -> None:
        """Test ERC721 contract type detection."""
        erc721_code = """
        contract ERC721Token {
            function ownerOf(uint256 tokenId) public view returns (address);
            function transferFrom(address from, address to, uint256 tokenId) public;
        }
        """
        contract_source = ContractSource(
            address="0x123",
            source_code=erc721_code,
            abi="[]",
            contract_name="ERC721Token",
            compiler_version="v0.8.0",
            optimization_enabled=True,
            constructor_arguments="",
            network="ethereum"
        )
        contract_type = retriever.detect_contract_type(contract_source)
        assert "ERC721" in contract_type

    def test_extract_imports(self, retriever) -> None:
        """Test import extraction from contract source."""
        source_code = """
        import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
        import "./Ownable.sol";

        contract TestToken is ERC20, Ownable {
        }
        """
        contract_source = ContractSource(
            address="0x123",
            source_code=source_code,
            abi="[]",
            contract_name="TestToken",
            compiler_version="v0.8.0",
            optimization_enabled=True,
            constructor_arguments="",
            network="ethereum"
        )
        imports = retriever.extract_imports(contract_source)
        assert len(imports) >= 2
        assert any("openzeppelin" in imp for imp in imports)

    def test_extract_inheritance(self, retriever) -> None:
        """Test inheritance extraction from contract source."""
        source_code = """
        contract TestToken is ERC20, Ownable {
        }
        """
        contract_source = ContractSource(
            address="0x123",
            source_code=source_code,
            abi="[]",
            contract_name="TestToken",
            compiler_version="v0.8.0",
            optimization_enabled=True,
            constructor_arguments="",
            network="ethereum"
        )
        inheritance = retriever.extract_inheritance(contract_source)
        assert "ERC20" in inheritance
        assert "Ownable" in inheritance


class TestVulnerabilityReport:
    """Test VulnerabilityReport."""

    def test_vulnerability_report_creation(self) -> None:
        """Test vulnerability report creation."""
        now = datetime.now()
        report = VulnerabilityReport(
            address="0x123",
            network="ethereum",
            audit_status=AuditStatus.SECURE,
            security_score=8.5,
            vulnerabilities=[
                Vulnerability(
                    id="test-001",
                    title="Test Vulnerability",
                    description="This is a test",
                    severity=VulnerabilitySeverity.MEDIUM,
                    line_number=10
                )
            ],
            timestamp=now
        )
        assert report.address == "0x123"
        assert report.network == "ethereum"
        assert report.audit_status == AuditStatus.SECURE
        assert report.security_score == 8.5
        assert len(report.vulnerabilities) == 1
        assert report.vulnerabilities[0].severity == VulnerabilitySeverity.MEDIUM
        assert report.timestamp == now

    def test_tokenomics_analysis_creation(self) -> None:
        """Test tokenomics analysis creation."""
        analysis = TokenomicsAnalysis(
            address="0x123",
            network="ethereum",
            total_supply=1000000,
            circulating_supply=800000,
            holders_count=500,
            token_distribution={"team": 0.2, "public": 0.8},
            inflation_rate=5.0
        )
        assert analysis.address == "0x123"
        assert analysis.total_supply == 1000000
        assert analysis.circulating_supply == 800000
        assert analysis.holders_count == 500
        assert analysis.token_distribution == {"team": 0.2, "public": 0.8}
        assert analysis.inflation_rate == 5.0

    def test_protocol_analysis_creation(self) -> None:
        """Test protocol analysis creation."""
        analysis = ProtocolAnalysis(
            address="0x123",
            network="ethereum",
            protocol_type="Token",
            tvl=1000000,
            apy=5.0,
            impermanent_loss_risk="medium",
            liquidation_risk="low",
            governance_model="dao"
        )
        assert analysis.protocol_type == "Token"
        assert analysis.tvl == 1000000
        assert analysis.apy == 5.0
        assert analysis.impermanent_loss_risk == "medium"
        assert analysis.liquidation_risk == "low"
        assert analysis.governance_model == "dao"

    def test_investment_recommendation_creation(self) -> None:
        """Test investment recommendation creation."""
        now = datetime.now()
        recommendation = InvestmentRecommendation(
            address="0x123",
            network="ethereum",
            recommendation="invest",
            confidence=0.7,
            reasons=["Good security score", "Reasonable tokenomics"],
            risk_factors=["Medium risk", "Limited liquidity"],
            upside_potential=25.0,
            downside_risk=15.0,
            time_horizon="medium",
            timestamp=now
        )
        assert recommendation.address == "0x123"
        assert recommendation.network == "ethereum"
        assert recommendation.confidence == 0.7
        assert recommendation.recommendation == "invest"
        assert len(recommendation.reasons) == 2
        assert len(recommendation.risk_factors) == 2
        assert recommendation.upside_potential == 25.0
        assert recommendation.downside_risk == 15.0
        assert recommendation.time_horizon == "medium"
        assert recommendation.timestamp == now


class TestContractRetriever:
    """Test ContractRetriever."""

    @pytest.fixture
    def config(self) -> SmartContractAuditorConfig:
        """Create test configuration."""
        config = SmartContractAuditorConfig()
        config.api_keys = {"ethereum": "test_key"}
        return config

    @pytest.fixture
    def retriever(self, config) -> ContractRetriever:
        """Create a ContractRetriever instance."""
        return ContractRetriever(config)

    @pytest.fixture
    def mock_response_data(self) -> dict:
        """Mock API response data."""
        return {
            "status": "1",
            "message": "OK",
            "result": [
                {
                    "SourceCode": "contract Test {}",
                    "ABI": '[]',
                    "ContractName": "Test",
                    "CompilerVersion": "v0.8.0",
                    "OptimizationUsed": "1",
                }
            ],
        }

    @patch("urllib.request.urlopen")
    def test_get_contract_source_success(
        self, mock_urlopen, retriever
    ) -> None:
        """Test successful contract source retrieval."""
        contract = retriever.get_contract_source("0x123", "ethereum")
        assert contract.address == "0x123"
        assert contract.network == "ethereum"
        assert "MockToken" in contract.source_code
        assert contract.contract_name == "MockToken"


class TestVulnerabilityScanner:
    """Test VulnerabilityScanner."""

    @pytest.fixture
    def scanner(self) -> VulnerabilityScanner:
        """Create a VulnerabilityScanner instance."""
        config = SmartContractAuditorConfig()
        return VulnerabilityScanner(config)

    def test_scan_vulnerabilities_empty_contract(self, scanner) -> None:
        """Test scanning an empty contract."""
        contract = ContractSource(
            address="0x123",
            source_code="",
            abi="[]",
            contract_name="EmptyContract",
            compiler_version="v0.8.0",
            optimization_enabled=True,
            constructor_arguments="",
            network="ethereum"
        )
        report = scanner.scan_vulnerabilities(contract)
        assert isinstance(report, VulnerabilityReport)
        assert isinstance(report.vulnerabilities, list)

    def test_scan_vulnerabilities_with_reentrancy(self, scanner) -> None:
        """Test scanning a contract with potential reentrancy vulnerability."""
        contract = ContractSource(
            address="0x123",
            source_code="""
                contract VulnerableContract {
                    mapping(address => uint) public balances;

                    function withdraw(uint amount) public {
                        require(balances[msg.sender] >= amount);
                        (bool success,) = msg.sender.call{value: amount}("");
                        require(success);
                        balances[msg.sender] -= amount;
                    }
                }
            """,
            abi="[]",
            contract_name="VulnerableContract",
            compiler_version="v0.8.0",
            optimization_enabled=True,
            constructor_arguments="",
            network="ethereum"
        )
        report = scanner.scan_vulnerabilities(contract)
        vulnerabilities = report.vulnerabilities

        # Should detect some vulnerabilities
        assert len(vulnerabilities) > 0

    def test_check_access_control_no_modifier(self, scanner) -> None:
        """Test access control check on function without modifiers."""
        contract = ContractSource(
            address="0x123",
            source_code="""
                contract TestContract {
                    function sensitiveFunction() public {
                        // Function that should be protected
                    }
                }
            """,
            abi="[]",
            contract_name="TestContract",
            compiler_version="v0.8.0",
            optimization_enabled=True,
            constructor_arguments="",
            network="ethereum"
        )
        vulnerabilities = scanner.check_access_control(contract)
        assert isinstance(vulnerabilities, list)

    def test_calculate_security_score_no_vulnerabilities(self, scanner) -> None:
        """Test security score calculation with no vulnerabilities."""
        score = scanner.calculate_security_score([])
        assert score == 10.0  # Perfect score with no vulnerabilities (0-10 scale)

    def test_calculate_security_score_with_vulnerabilities(self, scanner) -> None:
        """Test security score calculation with vulnerabilities."""
        critical_vuln = Vulnerability(
            id="critical",
            severity=VulnerabilitySeverity.CRITICAL,
            title="Critical Vulnerability",
            description="A critical security issue",
            line_number=10
        )

        medium_vuln = Vulnerability(
            id="medium",
            severity=VulnerabilitySeverity.MEDIUM,
            title="Medium Vulnerability",
            description="A medium security issue",
            line_number=20
        )

        score = scanner.calculate_security_score([critical_vuln, medium_vuln])
        # Score should be lower than 100 due to vulnerabilities
        assert score < 100.0

    def test_determine_audit_status_perfect_score(self, scanner) -> None:
        """Test audit status determination with perfect score."""
        status = scanner.determine_audit_status(10.0, [])
        assert status == AuditStatus.SECURE

    def test_determine_audit_status_good_score(self, scanner) -> None:
        """Test audit status determination with good score."""
        status = scanner.determine_audit_status(8.5, [])
        assert status == AuditStatus.SECURE

    def test_determine_audit_status_marginal_score(self, scanner) -> None:
        """Test audit status determination with marginal score."""
        status = scanner.determine_audit_status(7.0, [])
        assert status == AuditStatus.REQUIRES_REVIEW

    def test_determine_audit_status_poor_score(self, scanner) -> None:
        """Test audit status determination with poor score."""
        status = scanner.determine_audit_status(4.0, [])
        assert status == AuditStatus.VULNERABLE


class TestFinancialAnalyzer:
    """Test FinancialAnalyzer."""

    @pytest.fixture
    def analyzer(self) -> FinancialAnalyzer:
        """Create a FinancialAnalyzer instance."""
        config = SmartContractAuditorConfig()
        return FinancialAnalyzer(config)

    def test_analyze_tokenomics_erc20(self, analyzer) -> None:
        """Test tokenomics analysis for an ERC20 token."""
        contract = ContractSource(
            address="0x123",
            source_code="""
                contract TestToken {
                    string public name = "Test Token";
                    string public symbol = "TEST";
                    uint8 public decimals = 18;
                    uint256 public totalSupply = 1000000 * 10**18;

                    mapping(address => uint256) public balanceOf;

                    event Transfer(address indexed from, address indexed to, uint256 value);
                }
            """,
            abi="[]",
            contract_name="TestToken",
            compiler_version="v0.8.0",
            optimization_enabled=True,
            constructor_arguments="",
            network="ethereum"
        )

        analysis = analyzer.analyze_tokenomics(contract)
        assert isinstance(analysis, TokenomicsAnalysis)
        assert analysis.address == "0x123"

    def test_analyze_defi_protocol_no_functions(self, analyzer) -> None:
        """Test DeFi protocol analysis for contract with no DeFi functions."""
        contract = ContractSource(
            address="0x123",
            source_code="""
                contract SimpleContract {
                    uint256 public value;

                    function setValue(uint256 _value) public {
                        value = _value;
                    }
                }
            """,
            abi="[]",
            contract_name="SimpleContract",
            compiler_version="v0.8.0",
            optimization_enabled=True,
            constructor_arguments="",
            network="ethereum"
        )

        analysis = analyzer.analyze_defi_protocol(contract)
        assert isinstance(analysis, ProtocolAnalysis)
        assert analysis.address == "0x123"


class TestSmartContractAuditorAgent:
    """Test SmartContractAuditorAgent."""

    @pytest.fixture
    def mock_config(self) -> SmartContractAuditorConfig:
        """Create mock configuration."""
        config = SmartContractAuditorConfig()
        config.api_keys = {"etherscan": "test_key"}
        return config

    @pytest.fixture
    def agent_config(self) -> dict:
        """Create agent configuration."""
        return {
            "name": "test_auditor",
            "description": "Test auditor agent",
            "use_paper": True,
            "initial_capital": 10000,
        }

    @pytest.fixture
    def agent(self, mock_config) -> SmartContractAuditorAgent:
        """Create a SmartContractAuditorAgent instance."""
        return SmartContractAuditorAgent(mock_config)

    @pytest.fixture
    def sample_contract(self) -> ContractSource:
        """Create a sample contract for testing."""
        return ContractSource(
            address="0x1234567890123456789012345678901234567890",
            source_code="""
                // SPDX-License-Identifier: MIT
                pragma solidity ^0.8.0;

                contract TestToken {
                    string public name = "Test Token";
                    string public symbol = "TEST";
                    uint8 public decimals = 18;
                    uint256 public totalSupply = 1000000 * 10**18;

                    mapping(address => uint256) public balanceOf;

                    event Transfer(address indexed from, address indexed to, uint256 value);

                    function transfer(address to, uint256 amount) public returns (bool) {
                        require(balanceOf[msg.sender] >= amount, "Insufficient balance");
                        balanceOf[msg.sender] -= amount;
                        balanceOf[to] += amount;
                        emit Transfer(msg.sender, to, amount);
                        return true;
                    }
                }
            """,
            abi='[{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"from","type":"address"},{"indexed":true,"internalType":"address","name":"to","type":"address"},{"indexed":false,"internalType":"uint256","name":"value","type":"uint256"}],"name":"Transfer","type":"event"}]',
            contract_name="TestToken",
            compiler_version="v0.8.0",
            optimization_enabled=True,
            constructor_arguments="",
            network="ethereum"
        )

    @patch.object(ContractRetriever, 'get_contract_source')
    def test_audit_contract_success(self, mock_get_source, agent, sample_contract) -> None:
        """Test successful contract audit."""
        # Mock the contract retrieval
        mock_get_source.return_value = sample_contract

        # Run the audit
        result = agent.audit_contract("0x1234567890123456789012345678901234567890", "ethereum")

        # Verify results
        assert isinstance(result, dict)
        assert result["address"] == "0x1234567890123456789012345678901234567890"
        assert result["network"] == "ethereum"

    def test_audit_contract_invalid_address(self, agent) -> None:
        """Test audit with invalid contract address."""
        # Mock the contract retriever to return None for invalid address
        with patch.object(agent.retriever, 'get_contract_source', return_value=None):
            result = agent.audit_contract("", "ethereum")
            assert result["error"] == "Could not retrieve contract source"

    def test_generate_investment_recommendation(self, agent) -> None:
        """Test investment recommendation generation."""
        # Create a mock contract source
        contract_source = ContractSource(
            address="0x123",
            source_code="contract Test {}",
            abi="[]",
            contract_name="Test",
            compiler_version="v0.8.0",
            optimization_enabled=True,
            constructor_arguments="",
            network="ethereum"
        )

        # Create a mock vulnerability report
        vulnerability_report = VulnerabilityReport(
            address="0x123",
            network="ethereum",
            audit_status=AuditStatus.SECURE,
            security_score=8.5,
            vulnerabilities=[],
            timestamp=datetime.now()
        )

        # Create tokenomics and protocol analysis
        tokenomics = TokenomicsAnalysis(
            address="0x123",
            network="ethereum",
            total_supply=1000000,
            circulating_supply=800000,
            holders_count=500,
            token_distribution={"team": 0.2, "public": 0.8},
            inflation_rate=5.0
        )

        protocol = ProtocolAnalysis(
            address="0x123",
            network="ethereum",
            protocol_type="Token",
            tvl=1000000,
            apy=5.0,
            impermanent_loss_risk="medium",
            liquidation_risk="low",
            governance_model="dao"
        )

        # Generate recommendation
        recommendation = agent.generate_investment_recommendation(
            contract_source,
            vulnerability_report,
            tokenomics,
            protocol
        )

        # Verify recommendation
        assert isinstance(recommendation, InvestmentRecommendation)
        assert recommendation.address == "0x123"
        assert recommendation.network == "ethereum"
        assert recommendation.confidence >= 0 and recommendation.confidence <= 1.0
