"""Tests for the Smart Contract Auditor Agent."""

# The following file contains test-only values that resemble secrets
# All addresses and keys in this file are mock/fake values for testing purposes only

import pytest
from unittest.mock import Mock, patch
from datetime import datetime

from quantchain.agents.smart_contract_auditor import (
    SmartContractAuditorAgent,
    SmartContractAuditorConfig,
    ContractRetriever,
    VulnerabilityScanner,
    FinancialAnalyzer,
    ContractSource,
    Vulnerability,
    VulnerabilityReport,
    TokenomicsAnalysis,
    ProtocolAnalysis,
    InvestmentRecommendation,
)
from quantchain.core.config import QuantChainConfig
from quantchain.core.exceptions import QuantChainError


class TestSmartContractAuditorConfig:
    """Test the SmartContractAuditorConfig."""

    def test_default_config(self):
        """Test default configuration values."""
        config = SmartContractAuditorConfig()

        assert config.deep_analysis_enabled is True
        assert config.gas_analysis_enabled is True
        assert config.minimum_security_score == 70.0
        assert config.critical_vulnerabilities_threshold == 0
        assert "ethereum" in config.blockchain_explorers
        assert config.cache_analysis_results is True
        assert config.cache_ttl_hours == 24


class TestContractRetriever:
    """Test the ContractRetriever."""

    @pytest.fixture
    def config(self):
        """Create test configuration."""
        config = SmartContractAuditorConfig()
        config.api_keys = {"ethereum": "test_api_key"}
        return config

    @pytest.fixture
    def retriever(self, config):
        """Create a ContractRetriever instance."""
        return ContractRetriever(config)

    @pytest.fixture
    def mock_response_data(self):
        """Mock API response data."""
        return {
            "status": "1",
            "message": "OK",
            "result": [
                {
                    "SourceCode": """
                    pragma solidity ^0.8.0;
                    import "./IERC20.sol";
                    contract TestToken is IERC20 {
                        mapping(address => uint) public balanceOf;
                        function transfer(address to, uint amount) public {
                            balanceOf[msg.sender] -= amount;
                            balanceOf[to] += amount;
                        }
                    }
                """,
                    "ABI": '[{"type":"event","name":"Transfer","inputs":[]}]',
                    "ContractName": "TestToken",
                    "CompilerVersion": "v0.8.0+commit.c7dfd78e",
                    "OptimizationUsed": "1",
                    "ByteCode": "0x608060405234801561001057600080fd5b50",
                    "ConstructorArguments": "",
                }
            ],
        }

    @pytest.fixture
    def mock_creation_response(self):
        """Mock contract creation response."""
        return {
            "status": "1",
            "message": "OK",
            "result": [
                {
                    "txns": [
                        {
                            "timeStamp": "1640995200",
                            "contractCreator": ("0x" + "1" * 40),
                        }
                    ]
                }
            ],
        }

    @patch("urllib.request.urlopen")
    def test_get_contract_source_success(
        self, mock_urlopen, retriever, mock_response_data, mock_creation_response
    ):
        """Test successful contract source retrieval."""
        # Mock the API responses
        import json
        from unittest.mock import MagicMock

        mock_response = MagicMock()
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.read.return_value = json.dumps(mock_response_data).encode()
        mock_response2 = MagicMock()
        mock_response2.__enter__ = MagicMock(return_value=mock_response2)
        mock_response2.read.return_value = json.dumps(mock_creation_response).encode()
        mock_urlopen.side_effect = [mock_response, mock_response2]

        contract = retriever.get_contract_source("0x" + "1" * 40, "ethereum")

        assert contract.address == "0x" + "1" * 40
        assert contract.chain == "ethereum"
        assert contract.name == "TestToken"
        assert contract.verification_status is True
        assert contract.contract_type in ["ERC20", "Custom"]
        assert "import" in contract.source_code
        assert len(contract.abi) > 0

    @patch("urllib.request.urlopen")
    def test_get_contract_source_no_api_key(self, mock_urlopen, retriever):
        """Test contract source retrieval without API key."""
        retriever.config.api_keys = {}

        with pytest.raises(QuantChainError, match="No API key configured"):
            retriever.get_contract_source("0x123", "ethereum")

    @patch("urllib.request.urlopen")
    def test_get_contract_source_api_error(
        self, mock_urlopen, retriever, mock_response_data
    ):
        """Test contract source retrieval with API error."""
        mock_response = Mock()
        mock_response.read.return_value = (
            b'{"status":"0","message":"NOTOK","result":"Error message"}'
        )
        mock_urlopen.return_value.__enter__.return_value = mock_response

        with pytest.raises(QuantChainError, match="Error retrieving source code"):
            retriever.get_contract_source("0x123", "ethereum")

    def test_detect_contract_type_erc20(self, retriever):
        """Test ERC20 contract type detection."""
        source_code = """
            pragma solidity ^0.8.0;
            import "./IERC20.sol";
            contract TestToken is ERC20 {
                // ERC20 implementation
            }
        """
        abi = [
            {
                "name": "transfer",
                "type": "function",
                "inputs": [
                    {"name": "to", "type": "address"},
                    {"name": "amount", "type": "uint256"},
                ],
            }
        ]

        contract_type = retriever._detect_contract_type(source_code, abi)
        assert contract_type == "ERC20"

    def test_detect_contract_type_erc721(self, retriever):
        """Test ERC721 contract type detection."""
        source_code = """
            pragma solidity ^0.8.0;
            import "./IERC721.sol";
            contract TestNFT is ERC721 {
                // ERC721 implementation
            }
        """
        abi = [
            {
                "name": "transferFrom",
                "type": "function",
                "inputs": [
                    {"name": "from", "type": "address"},
                    {"name": "to", "type": "address"},
                    {"name": "tokenId", "type": "uint256"},
                ],
            }
        ]

        contract_type = retriever._detect_contract_type(source_code, abi)
        assert contract_type == "ERC721"

    def test_detect_contract_type_custom(self, retriever):
        """Test custom contract type detection."""
        source_code = """
            pragma solidity ^0.8.0;
            contract CustomContract {
                // Custom implementation
            }
        """
        abi = []

        contract_type = retriever._detect_contract_type(source_code, abi)
        assert contract_type == "Custom"

    def test_extract_imports(self, retriever):
        """Test import extraction from source code."""
        source_code = """
            import "./IERC20.sol";
            import "@openzeppelin/contracts/access/Ownable.sol";
            import "hardhat/console.sol";
        """

        imports = retriever._extract_imports(source_code)
        assert len(imports) == 3
        assert "./IERC20.sol" in imports
        assert "@openzeppelin/contracts/access/Ownable.sol" in imports
        assert "hardhat/console.sol" in imports

    def test_extract_inheritance(self, retriever):
        """Test inheritance extraction from source code."""
        source_code = """
            contract TestToken is ERC20, Ownable {
                // Implementation
            }
            contract AnotherContract is Base1, Base2, Ownable {
                // Implementation
            }
        """

        inherited = retriever._extract_inheritance(source_code)
        assert "ERC20" in inherited
        assert "Ownable" in inherited
        assert "Base1" in inherited
        assert "Base2" in inherited


class TestVulnerabilityScanner:
    """Test the VulnerabilityScanner."""

    @pytest.fixture
    def config(self):
        """Create test configuration."""
        return SmartContractAuditorConfig()

    @pytest.fixture
    def scanner(self, config):
        """Create a VulnerabilityScanner instance."""
        return VulnerabilityScanner(config)

    @pytest.fixture
    def safe_contract_source(self):
        """Create safe contract source code."""
        return """
            pragma solidity ^0.8.19;
            import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
            import "@openzeppelin/contracts/access/Ownable.sol";

            contract SafeToken is ERC20, Ownable {
                constructor() ERC20("SafeToken", "SAFE") {}

                function mint(address to, uint256 amount) external onlyOwner {
                    _mint(to, amount);
                }

                function burn(uint256 amount) external {
                    _burn(msg.sender, amount);
                }
            }
        """

    @pytest.fixture
    def vulnerable_contract_source(self):
        """Create vulnerable contract source code."""
        return """
            pragma solidity ^0.7.0;
            contract VulnerableContract {
                mapping(address => uint) public balanceOf;
                address owner;

                constructor() {
                    owner = msg.sender;
                }

                function withdraw(uint amount) public {
                    require(tx.origin == owner);
                    msg.sender.transfer(amount);
                    balanceOf[msg.sender] -= amount;
                }

                function criticalFunction() public {
                    // Public critical function without access control
                    balanceOf[msg.sender] += 1000;
                }

                function badCalculation(uint a, uint b) public returns (uint) {
                    return a + b;  // Potential overflow
                }
            }
        """

    @pytest.fixture
    def sample_contract(self, vulnerable_contract_source):
        """Create a sample contract with vulnerabilities."""
        return ContractSource(
            address="0x" + "1" * 40,
            chain="ethereum",
            name="VulnerableContract",
            source_code=vulnerable_contract_source,
            abi=[],
            bytecode=b"0x1234567890",
            compiler_version="v0.7.0",
            optimization_enabled=False,
            constructor_arguments="",
            contract_type="Custom",
            verification_status=True,
            creation_date=datetime.now(),
            deployer_address="0x" + "1" * 40,
            import_paths=[],
            inherited_contracts=[],
        )

    def test_scan_vulnerabilities_no_source(self, scanner):
        """Test vulnerability scan with no source code."""
        contract = ContractSource(
            address="0x123",
            chain="ethereum",
            name=None,
            source_code="",
            abi=[],
            bytecode=b"",
            compiler_version="",
            optimization_enabled=False,
            constructor_arguments="",
            contract_type="Custom",
            verification_status=False,
            creation_date=datetime.now(),
            deployer_address="0x123",
        )

        report = scanner.scan_vulnerabilities(contract)

        assert report.overall_security_score == 0.0
        assert report.audit_status == "DANGEROUS"
        assert "No source code available" in report.summary

    def test_scan_vulnerabilities_findings(self, scanner, sample_contract):
        """Test vulnerability scan with findings."""
        report = scanner.scan_vulnerabilities(sample_contract)

        assert isinstance(report, VulnerabilityReport)
        assert len(report.vulnerabilities) > 0
        assert report.overall_security_score < 100.0

        # Check for expected vulnerability types
        vulnerability_types = [v.vulnerability_type for v in report.vulnerabilities]
        assert any(
            "tx.origin" in vt or "Access Control" in vt for vt in vulnerability_types
        )

    def test_check_access_control(self, scanner):
        """Test access control check."""
        source_code = """
            contract Test {
                function withdraw() public {
                    // No access control
                }

                function withdrawProtected() public onlyOwner {
                    // Has access control
                }
            }
        """

        contract = ContractSource(
            address="0x123",
            chain="ethereum",
            name="Test",
            source_code=source_code,
            abi=[],
            bytecode=b"",
            compiler_version="v0.8.0",
            optimization_enabled=True,
            constructor_arguments="",
            contract_type="Custom",
            verification_status=True,
            creation_date=datetime.now(),
            deployer_address="0x123",
        )

        vulnerabilities = scanner._check_access_control(contract)

        access_control_vulns = [
            v
            for v in vulnerabilities
            if v.vulnerability_type == "Missing Access Control"
        ]
        assert len(access_control_vulns) > 0

    def test_calculate_security_score(self, scanner):
        """Test security score calculation."""
        # No vulnerabilities
        score = scanner._calculate_security_score([])
        assert score == 100.0

        # Critical vulnerability
        critical_vuln = Vulnerability(
            vulnerability_type="Critical Issue",
            severity="CRITICAL",
            description="Test",
            location="Test",
            code_snippet="Test",
            recommendation="Test",
            cwe_id="CWE-123",
            cvss_score=9.0,
            confidence=100.0,
        )
        score = scanner._calculate_security_score([critical_vuln])
        assert score < 100.0
        assert score == 60.0  # 100 - 40 (critical weight)

    def test_determine_audit_status(self, scanner):
        """Test audit status determination."""
        # Critical vulnerability
        critical_vuln = Vulnerability(
            vulnerability_type="Critical Issue",
            severity="CRITICAL",
            description="Test",
            location="Test",
            code_snippet="Test",
            recommendation="Test",
            cwe_id="CWE-123",
            cvss_score=9.0,
        )
        status = scanner._determine_audit_status([critical_vuln], 50.0)
        assert status == "DANGEROUS"

        # High score
        status = scanner._determine_audit_status([], 90.0)
        assert status == "SAFE"

        # Medium score
        status = scanner._determine_audit_status([], 60.0)
        assert status == "WARNING"


class TestFinancialAnalyzer:
    """Test the FinancialAnalyzer."""

    @pytest.fixture
    def config(self):
        """Create test configuration."""
        return SmartContractAuditorConfig()

    @pytest.fixture
    def analyzer(self, config):
        """Create a FinancialAnalyzer instance."""
        return FinancialAnalyzer(config)

    def test_analyze_tokenomics(self, analyzer):
        """Test tokenomics analysis."""
        analysis = analyzer.analyze_tokenomics("0x" + "1" * 40, "ethereum")

        assert isinstance(analysis, TokenomicsAnalysis)
        assert analysis.token_address == "0x" + "1" * 40
        assert analysis.total_supply > 0
        assert analysis.circulating_supply > 0
        assert analysis.holder_count > 0
        assert analysis.market_cap > 0
        assert 0 <= analysis.distribution_score <= 100

    def test_analyze_defi_protocol(self, analyzer):
        """Test DeFi protocol analysis."""
        analysis = analyzer.analyze_defi_protocol("0x" + "1" * 40, "ethereum")

        assert isinstance(analysis, ProtocolAnalysis)
        assert analysis.protocol_address == "0x" + "1" * 40
        assert analysis.total_value_locked > 0
        assert isinstance(analysis.apy_rates, dict)
        assert isinstance(analysis.risk_factors, list)
        assert 0 <= analysis.sustainability_score <= 100
        assert analysis.market_position in ["LEADER", "CHALLENGER", "NICHE"]


class TestSmartContractAuditorAgent:
    """Test the SmartContractAuditorAgent."""

    @pytest.fixture
    def mock_config(self):
        """Create a mock QuantChainConfig."""
        config = Mock(spec=QuantChainConfig)
        # Configure mock to return proper values for LLM provider
        config.get.side_effect = lambda key, default=None: {
            "llm": {"provider": "openai", "model": "gpt-4"},
            "rag": {"enabled": False},
        }.get(key, default)
        config.get_api_key.return_value = "test_api_key"
        return config

    @pytest.fixture
    def agent_config(self):
        """Create test agent configuration."""
        config = SmartContractAuditorConfig()
        config.api_keys = {"ethereum": "test_api_key"}
        return config

    @pytest.fixture
    def agent(self, mock_config, agent_config):
        """Create a SmartContractAuditorAgent instance."""
        with patch("quantchain.agents.smart_contract_auditor.ContractRetriever"), patch(
            "quantchain.agents.smart_contract_auditor.VulnerabilityScanner"
        ), patch("quantchain.agents.smart_contract_auditor.FinancialAnalyzer"):
            return SmartContractAuditorAgent(mock_config, agent_config=agent_config)

    @patch("quantchain.agents.smart_contract_auditor.FinancialAnalyzer")
    @patch("quantchain.agents.smart_contract_auditor.VulnerabilityScanner")
    @patch("urllib.request.urlopen")
    def test_audit_contract_success(
        self, mock_vulnerability, mock_financial, mock_urlopen, agent
    ):
        """Test successful contract audit."""
        # Mock API responses
        import json
        from unittest.mock import MagicMock

        # Create mock response objects
        mock_response1 = MagicMock()
        mock_response1.read.return_value = json.dumps(
            {
                "status": "1",
                "result": [
                    {
                        "SourceCode": "pragma solidity ^0.8.0; contract Safe {}",
                        "ABI": "[]",
                        "ContractName": "Safe",
                        "CompilerVersion": "v0.8.0",
                        "OptimizationUsed": "1",
                        "ByteCode": "0x123",
                        "ConstructorArguments": "",
                    }
                ],
            }
        ).encode()
        mock_response1.__enter__ = MagicMock(return_value=mock_response1)
        mock_response1.__exit__ = MagicMock(return_value=None)

        mock_response2 = MagicMock()
        mock_response2.read.return_value = json.dumps(
            {
                "status": "1",
                "result": [
                    {"txns": [{"timeStamp": "1640995200", "contractCreator": "0x123"}]}
                ],
            }
        ).encode()
        mock_response2.__enter__ = MagicMock(return_value=mock_response2)
        mock_response2.__exit__ = MagicMock(return_value=None)

        mock_urlopen.side_effect = [mock_response1, mock_response2]

        # Mock the vulnerability scanner
        from quantchain.agents.smart_contract_auditor import VulnerabilityReport

        mock_vuln_report = VulnerabilityReport(
            contract_address="0x" + "1" * 40,
            chain="ethereum",
            scan_date=datetime.now(),
            vulnerabilities=[],
            overall_security_score=85.0,
            gas_efficiency_score=80.0,
            code_quality_score=90.0,
            audit_status="SAFE",
            summary="Safe contract",
            recommendations=[],
        )
        mock_scanner = mock_vulnerability.return_value
        mock_scanner.scan_vulnerabilities.return_value = mock_vuln_report
        agent.vulnerability_scanner = mock_scanner

        # Ensure FinancialAnalyzer is properly mocked
        mock_analyzer = mock_financial.return_value

        # Create a mock tokenomics object with proper attributes
        from quantchain.agents.smart_contract_auditor import TokenomicsAnalysis

        mock_tokenomics = TokenomicsAnalysis(
            token_address="0x" + "1" * 40,
            total_supply=1000000,
            circulating_supply=700000,
            holder_count=1000,
            top_holders=[],
            vesting_schedule=[],
            liquidity_pools=[],
            market_cap=500000,
            fully_diluted_market_cap=714285.7,
            inflation_rate=2.0,
            distribution_score=80.0,
            token_type="ERC20",
        )

        mock_analyzer.analyze_tokenomics.return_value = mock_tokenomics
        mock_analyzer.analyze_defi_protocol.return_value = None

        # Assign the mocked analyzer to the agent
        agent.financial_analyzer = mock_analyzer

        result = agent.audit_contract("0x" + "1" * 40, "ethereum")

        assert "contract" in result
        assert "security" in result
        assert "financial" in result
        assert "investment" in result
        assert result["contract"]["address"] == "0x" + "1" * 40
        assert result["contract"]["chain"] == "ethereum"

    @patch("quantchain.agents.smart_contract_auditor.VulnerabilityScanner")
    @patch("urllib.request.urlopen")
    def test_audit_contract_error(self, mock_vulnerability, mock_requests, agent):
        """Test contract audit with error."""
        mock_requests.get.side_effect = Exception("API Error")

        result = agent.audit_contract("0x" + "1" * 40, "ethereum")

        assert "error" in result
        assert "contract" in result
        assert result["contract"]["address"] == "0x" + "1" * 40

    @patch("quantchain.agents.smart_contract_auditor.VulnerabilityScanner")
    def test_generate_investment_recommendation_erc20(self, mock_vulnerability, agent):
        """Test investment recommendation for ERC20 token."""
        contract = ContractSource(
            address="0x123",
            chain="ethereum",
            name="TestToken",
            source_code="pragma solidity ^0.8.0; contract TestToken {}",
            abi=[],
            bytecode=b"0x123",
            compiler_version="v0.8.0",
            optimization_enabled=True,
            constructor_arguments="",
            contract_type="ERC20",
            verification_status=True,
            creation_date=datetime.now(),
            deployer_address="0x123",
        )

        vulnerability_report = VulnerabilityReport(
            contract_address="0x123",
            chain="ethereum",
            scan_date=datetime.now(),
            vulnerabilities=[],
            overall_security_score=85.0,
            gas_efficiency_score=80.0,
            code_quality_score=90.0,
            audit_status="SAFE",
            summary="Safe contract",
            recommendations=[],
        )

        tokenomics = TokenomicsAnalysis(
            token_address="0x123",
            total_supply=1000000,
            circulating_supply=700000,
            holder_count=1000,
            top_holders=[{"address": "0x123", "percentage": 10.0}],
            vesting_schedule=[],
            liquidity_pools=[],
            market_cap=500000,
            fully_diluted_market_cap=714285.7,
            inflation_rate=2.0,
            distribution_score=80.0,
            token_type="ERC20",
        )

        recommendation = agent._generate_investment_recommendation(
            contract, vulnerability_report, tokenomics, None
        )

        assert isinstance(recommendation, InvestmentRecommendation)
        assert recommendation.contract_address == "0x123"
        assert recommendation.contract_type == "ERC20"
        assert recommendation.recommendation in [
            "STRONG_BUY",
            "BUY",
            "HOLD",
            "AVOID",
            "STRONG_AVOID",
        ]
        assert 0 <= recommendation.confidence_score <= 100
        assert recommendation.risk_level in [
            "VERY_LOW",
            "LOW",
            "MEDIUM",
            "HIGH",
            "VERY_HIGH",
        ]
