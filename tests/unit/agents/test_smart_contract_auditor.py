"""
Unit tests for SmartContractAuditor agent.
"""

import unittest
from unittest.mock import patch

import pytest

from quantchain.agents.smart_contract_auditor import (
    AuditStatus,
    ContractRetriever,
    ContractSource,
    FinancialAnalyzer,
    ProtocolAnalysis,
    SmartContractAuditorAgent,
    SmartContractAuditorConfig,
    TokenomicsAnalysis,
    VulnerabilityReport,
    VulnerabilityScanner,
)


@pytest.mark.unit
class TestSmartContractAuditor(unittest.TestCase):
    """Test cases for SmartContractAuditorAgent and components."""

    def setUp(self):
        """Set up test fixtures."""
        self.config = SmartContractAuditorConfig(
            api_keys={"ethereum": "test_key"},
            cache_expiry_seconds=3600,
        )
        self.agent = SmartContractAuditorAgent(self.config)

    def test_config_initialization(self):
        """Test configuration initialization."""
        self.assertEqual(self.config.api_keys["ethereum"], "test_key")
        self.assertEqual(self.config.cache_expiry_seconds, 3600)

    @patch(
        "quantchain.agents.smart_contract_auditor.ContractRetriever.get_contract_source"
    )
    def test_audit_contract_success(self, mock_get_source):
        """Test successful contract audit."""
        # Mock contract source
        mock_source = ContractSource(
            address="0x123",
            source_code="contract Test { }",
            abi="[]",
            contract_name="Test",
            compiler_version="0.8.0",
            optimization_enabled=True,
            constructor_arguments="",
            network="ethereum",
        )
        mock_get_source.return_value = mock_source

        # Run audit
        result = self.agent.audit_contract("0x123", "ethereum")

        # Verify results
        self.assertEqual(result["address"], "0x123")
        self.assertEqual(result["network"], "ethereum")
        self.assertIn("vulnerability_report", result)
        self.assertIn("recommendation", result)

    @patch(
        "quantchain.agents.smart_contract_auditor.ContractRetriever.get_contract_source"
    )
    def test_audit_contract_not_found(self, mock_get_source):
        """Test audit when contract is not found."""
        mock_get_source.return_value = None

        result = self.agent.audit_contract("0x123", "ethereum")

        self.assertIn("error", result)
        self.assertEqual(result["error"], "Could not retrieve contract source")

    def test_vulnerability_scanner(self):
        """Test vulnerability scanning logic."""
        scanner = VulnerabilityScanner(self.config)

        # Test contract with potential reentrancy
        source_code = """
        contract Vulnerable {
            function withdraw() public {
                msg.sender.call.value(amount)("");
                balances[msg.sender] = 0;
            }
        }
        """
        source = ContractSource(
            address="0x123",
            source_code=source_code,
            abi="[]",
            contract_name="Vulnerable",
            compiler_version="0.8.0",
            optimization_enabled=True,
            constructor_arguments="",
            network="ethereum",
        )

        report = scanner.scan_vulnerabilities(source)

        # Should detect reentrancy
        self.assertTrue(any(v.id == "reentrancy" for v in report.vulnerabilities))
        self.assertLess(report.security_score, 10.0)

    def test_access_control_check(self):
        """Test access control vulnerability check."""
        scanner = VulnerabilityScanner(self.config)

        source_code = """
        contract Insecure {
            function sensitiveAction() public {
                // No access control
            }
        }
        """
        source = ContractSource(
            address="0x123",
            source_code=source_code,
            abi="[]",
            contract_name="Insecure",
            compiler_version="0.8.0",
            optimization_enabled=True,
            constructor_arguments="",
            network="ethereum",
        )

        vulns = scanner.check_access_control(source)
        self.assertTrue(len(vulns) > 0)
        self.assertEqual(vulns[0].id, "access_control")

    def test_financial_analyzer_tokenomics(self):
        """Test tokenomics analysis."""
        analyzer = FinancialAnalyzer(self.config)

        source_code = """
        contract Token {
            uint256 public totalSupply = 1000000;
            function burn(uint256 amount) public { }
            function mint(address to, uint256 amount) public { }
        }
        """
        source = ContractSource(
            address="0x123",
            source_code=source_code,
            abi="[]",
            contract_name="Token",
            compiler_version="0.8.0",
            optimization_enabled=True,
            constructor_arguments="",
            network="ethereum",
        )

        analysis = analyzer.analyze_tokenomics(source)

        self.assertTrue(analysis.burn_mechanism)
        self.assertTrue(analysis.minting_allowed)

    def test_financial_analyzer_defi(self):
        """Test DeFi protocol analysis."""
        analyzer = FinancialAnalyzer(self.config)

        source_code = """
        contract DEX {
            function swap() public { }
            function addLiquidity() public { }
        }
        """
        source = ContractSource(
            address="0x123",
            source_code=source_code,
            abi="[]",
            contract_name="DEX",
            compiler_version="0.8.0",
            optimization_enabled=True,
            constructor_arguments="",
            network="ethereum",
        )

        analysis = analyzer.analyze_defi_protocol(source)

        self.assertEqual(analysis.protocol_type, "dex")

    def test_investment_recommendation(self):
        """Test investment recommendation generation."""
        # Create mock report and analysis
        vuln_report = VulnerabilityReport(
            address="0x123",
            network="ethereum",
            vulnerabilities=[],
            security_score=9.0,
            audit_status=AuditStatus.SECURE,
        )

        tokenomics = TokenomicsAnalysis(
            address="0x123", network="ethereum", burn_mechanism=True, holders_count=2000
        )

        protocol = ProtocolAnalysis(
            address="0x123", network="ethereum", protocol_type="dex", apy=15.0
        )

        recommendation = self.agent.generate_investment_recommendation(
            ContractSource("0x123", "", "", "", "", True, "", "ethereum"),
            vuln_report,
            tokenomics,
            protocol,
        )

        self.assertEqual(recommendation.recommendation, "caution")
        self.assertEqual(recommendation.confidence, 0.7)
        self.assertTrue(any("burn mechanism" in r for r in recommendation.reasons))

    def test_contract_retriever_caching(self):
        """Test contract retriever caching mechanism."""
        retriever = ContractRetriever(self.config)

        # Mock API call
        with patch.object(retriever, "_cache", {}) as mock_cache:
            # First call - should hit "API" (mocked in this case by the method logic)
            source1 = retriever.get_contract_source("0x123", "ethereum")

            # Verify it's in cache
            cache_key = "ethereum:0x123"
            self.assertIn(cache_key, retriever._cache)

            # Second call - should return same object
            source2 = retriever.get_contract_source("0x123", "ethereum")
            self.assertEqual(source1, source2)

    def test_detect_contract_type(self):
        """Test contract type detection."""
        retriever = ContractRetriever(self.config)

        source = ContractSource(
            address="0x123",
            source_code="interface IERC20 { }",
            abi="[]",
            contract_name="Token",
            compiler_version="0.8.0",
            optimization_enabled=True,
            constructor_arguments="",
            network="ethereum",
        )

        contract_type = retriever.detect_contract_type(source)
        self.assertEqual(contract_type, "ERC20")

    def test_extract_imports(self):
        """Test import extraction."""
        retriever = ContractRetriever(self.config)

        source_code = """
        import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
        import "./interfaces/IUniswap.sol";

        contract Test {}
        """
        source = ContractSource(
            address="0x123",
            source_code=source_code,
            abi="[]",
            contract_name="Test",
            compiler_version="0.8.0",
            optimization_enabled=True,
            constructor_arguments="",
            network="ethereum",
        )

        imports = retriever.extract_imports(source)
        self.assertEqual(len(imports), 2)
        self.assertIn(
            'import "@openzeppelin/contracts/token/ERC20/ERC20.sol";', imports
        )

    def test_extract_inheritance(self):
        """Test inheritance extraction."""
        retriever = ContractRetriever(self.config)

        source_code = """
        contract MyToken is ERC20, Ownable {
        }
        """
        source = ContractSource(
            address="0x123",
            source_code=source_code,
            abi="[]",
            contract_name="MyToken",
            compiler_version="0.8.0",
            optimization_enabled=True,
            constructor_arguments="",
            network="ethereum",
        )

        parents = retriever.extract_inheritance(source)
        self.assertIn("ERC20", parents)
        self.assertIn("Ownable", parents)
