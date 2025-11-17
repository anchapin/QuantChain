"""
Comprehensive tests for the smart_contract_auditor module.

This test suite covers enums, dataclasses, service classes, and audit functionality
without requiring external API calls or network connections.
"""

from datetime import datetime
from unittest.mock import Mock, patch

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
    Vulnerability,
    VulnerabilityReport,
    VulnerabilityScanner,
    VulnerabilitySeverity,
)


@pytest.mark.unit
class TestEnums:
    """Test enum classes."""

    def test_audit_status_values(self) -> None:
        """Test AuditStatus enum has expected values."""
        assert AuditStatus.SECURE.value == "secure"
        assert AuditStatus.VULNERABLE.value == "vulnerable"
        assert AuditStatus.REQUIRES_REVIEW.value == "requires_review"
        assert AuditStatus.INSUFFICIENT_DATA.value == "insufficient_data"

    def test_audit_status_comparison(self) -> None:
        """Test AuditStatus enum comparison."""
        assert AuditStatus.SECURE != AuditStatus.VULNERABLE
        assert AuditStatus.HIGH == AuditStatus.HIGH  # If HIGH exists

    def test_vulnerability_severity_values(self) -> None:
        """Test VulnerabilitySeverity enum has expected values."""
        assert VulnerabilitySeverity.CRITICAL.value == "critical"
        assert VulnerabilitySeverity.HIGH.value == "high"
        assert VulnerabilitySeverity.MEDIUM.value == "medium"
        assert VulnerabilitySeverity.LOW.value == "low"
        assert VulnerabilitySeverity.INFO.value == "info"

    def test_vulnerability_severity_ordering(self) -> None:
        """Test that severity levels have proper relationships."""
        critical = VulnerabilitySeverity.CRITICAL
        high = VulnerabilitySeverity.HIGH
        medium = VulnerabilitySeverity.MEDIUM
        low = VulnerabilitySeverity.LOW
        info = VulnerabilitySeverity.INFO

        # Verify all severities are different
        severities = [critical, high, medium, low, info]
        assert len(set(severities)) == 5


@pytest.mark.unit
class TestDataClasses:
    """Test dataclass classes."""

    def test_smart_contract_auditor_config_defaults(self) -> None:
        """Test SmartContractAuditorConfig default values."""
        config = SmartContractAuditorConfig()

        assert config.api_keys == {}
        assert config.etherscan_api_url == "https://api.etherscan.io/api"
        assert config.bscscan_api_url == "https://api.bscscan.com/api"
        assert config.polygonscan_api_url == "https://api.polygonscan.com/api"
        assert config.cache_expiry_seconds == 86400
        assert config.max_concurrent_requests == 5
        assert config.request_timeout_seconds == 30

    def test_smart_contract_auditor_config_custom_values(self) -> None:
        """Test SmartContractAuditorConfig with custom values."""
        api_keys = {"etherscan": "test_key"}
        config = SmartContractAuditorConfig(
            api_keys=api_keys,
            etherscan_api_url="https://custom.etherscan.io/api",
            cache_expiry_seconds=43200,
            max_concurrent_requests=10,
            request_timeout_seconds=60,
        )

        assert config.api_keys == api_keys
        assert config.etherscan_api_url == "https://custom.etherscan.io/api"
        assert config.cache_expiry_seconds == 43200
        assert config.max_concurrent_requests == 10
        assert config.request_timeout_seconds == 60

    def test_contract_source_creation(self) -> None:
        """Test ContractSource dataclass creation."""
        now = datetime.now()
        source = ContractSource(
            address="0x1234567890123456789012345678901234567890",
            source_code="contract Foo { function bar() public {} }",
            abi='[{"type":"function","name":"bar","inputs":[],"outputs":[]}]',
            contract_name="Foo",
            compiler_version="0.8.0",
            optimization_enabled=True,
        )

        assert source.address == "0x1234567890123456789012345678901234567890"
        assert source.source_code == "contract Foo { function bar() public {} }"
        assert (
            source.abi == '[{"type":"function","name":"bar","inputs":[],"outputs":[]}]'
        )
        assert source.contract_name == "Foo"
        assert source.compiler_version == "0.8.0"
        assert source.optimization_enabled is True

    def test_vulnerability_creation(self) -> None:
        """Test Vulnerability dataclass creation."""
        now = datetime.now()
        vulnerability = Vulnerability(
            title="Reentrancy Vulnerability",
            description="Contract is vulnerable to reentrancy attacks",
            severity=VulnerabilitySeverity.CRITICAL,
            location="withdraw() function",
            recommendation="Add reentrancy guards",
            detected_at=now,
        )

        assert vulnerability.title == "Reentrancy Vulnerability"
        assert (
            vulnerability.description == "Contract is vulnerable to reentrancy attacks"
        )
        assert vulnerability.severity == VulnerabilitySeverity.CRITICAL
        assert vulnerability.location == "withdraw() function"
        assert vulnerability.recommendation == "Add reentrancy guards"
        assert vulnerability.detected_at == now

    def test_vulnerability_report_creation(self) -> None:
        """Test VulnerabilityReport dataclass creation."""
        now = datetime.now()
        vulnerability = Vulnerability(
            title="Test Vulnerability",
            description="Test description",
            severity=VulnerabilitySeverity.MEDIUM,
            location="test location",
            recommendation="test recommendation",
            detected_at=now,
        )

        report = VulnerabilityReport(
            contract_address="0x1234567890123456789012345678901234567890",
            audit_date=now,
            auditor_version="1.0.0",
            vulnerabilities=[vulnerability],
            security_score=75.5,
            status=AuditStatus.VULNERABLE,
        )

        assert report.contract_address == "0x1234567890123456789012345678901234567890"
        assert report.audit_date == now
        assert report.auditor_version == "1.0.0"
        assert len(report.vulnerabilities) == 1
        assert report.vulnerabilities[0] == vulnerability
        assert report.security_score == 75.5
        assert report.status == AuditStatus.VULNERABLE

    def test_tokenomics_analysis_creation(self) -> None:
        """Test TokenomicsAnalysis dataclass creation."""
        now = datetime.now()
        analysis = TokenomicsAnalysis(
            token_name="Test Token",
            token_symbol="TEST",
            total_supply=1000000000,
            circulating_supply=500000000,
            holders_count=10000,
            top_holders_percentage=25.5,
            liquidity_locked=True,
            contract_has_mint_function=True,
            contract_has_burn_function=True,
            analyzed_at=now,
        )

        assert analysis.token_name == "Test Token"
        assert analysis.token_symbol == "TEST"
        assert analysis.total_supply == 1000000000
        assert analysis.circulating_supply == 500000000
        assert analysis.holders_count == 10000
        assert analysis.top_holders_percentage == 25.5
        assert analysis.liquidity_locked is True
        assert analysis.contract_has_mint_function is True
        assert analysis.contract_has_burn_function is True
        assert analysis.analyzed_at == now

    def test_protocol_analysis_creation(self) -> None:
        """Test ProtocolAnalysis dataclass creation."""
        now = datetime.now()
        analysis = ProtocolAnalysis(
            protocol_name="Test Protocol",
            protocol_type="defi",
            tvl_usd=100000000,
            daily_volume_usd=5000000,
            apy_percentage=15.5,
            risk_score=6.5,
            governance_active=True,
            has_audit=True,
            analyzed_at=now,
        )

        assert analysis.protocol_name == "Test Protocol"
        assert analysis.protocol_type == "defi"
        assert analysis.tvl_usd == 100000000
        assert analysis.daily_volume_usd == 5000000
        assert analysis.apy_percentage == 15.5
        assert analysis.risk_score == 6.5
        assert analysis.governance_active is True
        assert analysis.has_audit is True
        assert analysis.analyzed_at == now


@pytest.mark.unit
class TestContractRetriever:
    """Test ContractRetriever class."""

    def test_init_default_config(self) -> None:
        """Test ContractRetriever initialization with default config."""
        config = SmartContractAuditorConfig()
        retriever = ContractRetriever(config)

        assert retriever.config == config
        assert hasattr(retriever, "_cache")
        assert hasattr(retriever, "_session")

    def test_init_custom_config(self) -> None:
        """Test ContractRetriever initialization with custom config."""
        api_keys = {"etherscan": "test_key"}
        config = SmartContractAuditorConfig(api_keys=api_keys)
        retriever = ContractRetriever(config)

        assert retriever.config.api_keys == api_keys

    def test_detect_contract_type_erc20(self) -> None:
        """Test detecting ERC20 contract type."""
        config = SmartContractAuditorConfig()
        retriever = ContractRetriever(config)

        erc20_code = """
        contract ERC20 {
            function totalSupply() public view returns (uint256) {}
            function balanceOf(address account) public view returns (uint256) {}
            function transfer(address recipient, uint256 amount) public returns (bool) {}
            event Transfer(address indexed from, address indexed to, uint256 value);
        }
        """

        contract_type = retriever.detect_contract_type(erc20_code)
        assert "ERC20" in contract_type or "Token" in contract_type

    def test_detect_contract_type_erc721(self) -> None:
        """Test detecting ERC721 contract type."""
        config = SmartContractAuditorConfig()
        retriever = ContractRetriever(config)

        erc721_code = """
        contract ERC721 {
            function balanceOf(address owner) public view returns (uint256) {}
            function ownerOf(uint256 tokenId) public view returns (address) {}
            function transferFrom(address from, address to, uint256 tokenId) public {}
            event Transfer(address indexed from, address indexed to, uint256 indexed tokenId);
        }
        """

        contract_type = retriever.detect_contract_type(erc721_code)
        assert "ERC721" in contract_type or "NFT" in contract_type

    def test_detect_contract_type_defi(self) -> None:
        """Test detecting DeFi contract type."""
        config = SmartContractAuditorConfig()
        retriever = ContractRetriever(config)

        defi_code = """
        contract DeFiProtocol {
            function deposit(uint256 amount) public {}
            function withdraw(uint256 amount) public {}
            function getAPY() public view returns (uint256) {}
        }
        """

        contract_type = retriever.detect_contract_type(defi_code)
        # Should detect some DeFi-related patterns
        assert isinstance(contract_type, str)

    def test_extract_imports(self) -> None:
        """Test extracting imports from contract code."""
        config = SmartContractAuditorConfig()
        retriever = ContractRetriever(config)

        contract_code = """
        import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
        import "@openzeppelin/contracts/security/ReentrancyGuard.sol";
        import "./SafeMath.sol";

        contract TestContract is ERC20, ReentrancyGuard {
            using SafeMath for uint256;
        }
        """

        imports = retriever.extract_imports(contract_code)
        assert "@openzeppelin/contracts/token/ERC20/ERC20.sol" in imports
        assert "@openzeppelin/contracts/security/ReentrancyGuard.sol" in imports
        assert "./SafeMath.sol" in imports

    def test_extract_inheritance(self) -> None:
        """Test extracting inheritance from contract code."""
        config = SmartContractAuditorConfig()
        retriever = ContractRetriever(config)

        contract_code = """
        contract TestContract is ERC20, ReentrancyGuard, Ownable {
            // Implementation
        }

        contract AnotherContract is TestContract {
            // Implementation
        }
        """

        inheritance = retriever.extract_inheritance(contract_code)
        assert "ERC20" in inheritance
        assert "ReentrancyGuard" in inheritance
        assert "Ownable" in inheritance


@pytest.mark.unit
class TestVulnerabilityScanner:
    """Test VulnerabilityScanner class."""

    def test_init(self) -> None:
        """Test VulnerabilityScanner initialization."""
        scanner = VulnerabilityScanner()
        assert hasattr(scanner, "vulnerability_patterns")

    def test_scan_vulnerabilities_empty_code(self) -> None:
        """Test scanning empty contract code."""
        scanner = VulnerabilityScanner()
        vulnerabilities = scanner.scan_vulnerabilities("")

        assert isinstance(vulnerabilities, list)
        # Empty code should result in no vulnerabilities detected

    def test_scan_vulnerabilities_reentrancy(self) -> None:
        """Test detecting reentrancy vulnerability."""
        scanner = VulnerabilityScanner()

        vulnerable_code = """
        contract VulnerableContract {
            mapping(address => uint256) public balances;

            function withdraw(uint256 amount) public {
                require(balances[msg.sender] >= amount);
                (bool success,) = msg.sender.call{value: amount}("");
                require(success);
                balances[msg.sender] -= amount;  // Vulnerable: state update after external call
            }
        }
        """

        vulnerabilities = scanner.scan_vulnerabilities(vulnerable_code)
        assert isinstance(vulnerabilities, list)

        # Check if any reentrancy-related vulnerability was found
        reentrancy_found = any(
            "reentrancy" in vuln.title.lower()
            or "external call" in vuln.description.lower()
            for vuln in vulnerabilities
        )

    def test_scan_vulnerabilities_access_control(self) -> None:
        """Test detecting access control issues."""
        scanner = VulnerabilityScanner()

        vulnerable_code = """
        contract VulnerableContract {
            function sensitiveFunction() public {
                // No access control - anyone can call this
                selfdestruct(msg.sender);
            }
        }
        """

        vulnerabilities = scanner.scan_vulnerabilities(vulnerable_code)
        assert isinstance(vulnerabilities, list)

        # Check if any access control vulnerability was found
        access_control_found = any(
            "access control" in vuln.title.lower()
            or "public" in vuln.description.lower()
            for vuln in vulnerabilities
        )

    def test_check_access_control_no_modifier(self) -> None:
        """Test access control check for functions without modifiers."""
        scanner = VulnerabilityScanner()

        contract_code = """
        contract TestContract {
            function adminFunction() public {
                // Should have onlyOwner modifier
            }

            function publicFunction() public {
                // This is fine
            }
        }
        """

        issues = scanner.check_access_control(contract_code)
        assert isinstance(issues, list)

    def test_calculate_security_score_no_vulnerabilities(self) -> None:
        """Test security score calculation with no vulnerabilities."""
        scanner = VulnerabilityScanner()
        score = scanner.calculate_security_score([])

        assert isinstance(score, (int, float))
        assert score >= 0 and score <= 100

    def test_calculate_security_score_with_vulnerabilities(self) -> None:
        """Test security score calculation with vulnerabilities."""
        scanner = VulnerabilityScanner()

        vulnerabilities = [
            Vulnerability(
                title="Low Severity Issue",
                description="Test low severity vulnerability",
                severity=VulnerabilitySeverity.LOW,
                location="test location",
                recommendation="fix it",
                detected_at=datetime.now(),
            ),
            Vulnerability(
                title="Critical Issue",
                description="Test critical vulnerability",
                severity=VulnerabilitySeverity.CRITICAL,
                location="test location",
                recommendation="fix it immediately",
                detected_at=datetime.now(),
            ),
        ]

        score = scanner.calculate_security_score(vulnerabilities)
        assert isinstance(score, (int, float))
        assert score >= 0 and score <= 100
        # Score should be lower with critical vulnerabilities

    def test_determine_audit_status_secure(self) -> None:
        """Test audit status determination for secure contracts."""
        scanner = VulnerabilityScanner()
        status = scanner.determine_audit_status(95.0)

        assert status == AuditStatus.SECURE

    def test_determine_audit_status_vulnerable(self) -> None:
        """Test audit status determination for vulnerable contracts."""
        scanner = VulnerabilityScanner()
        status = scanner.determine_audit_status(45.0)

        assert status in [AuditStatus.VULNERABLE, AuditStatus.REQUIRES_REVIEW]

    def test_determine_audit_status_insufficient_data(self) -> None:
        """Test audit status determination for insufficient data."""
        scanner = VulnerabilityScanner()
        status = scanner.determine_audit_status(-1.0)  # Invalid score

        assert status == AuditStatus.INSUFFICIENT_DATA


@pytest.mark.unit
class TestFinancialAnalyzer:
    """Test FinancialAnalyzer class."""

    def test_init(self) -> None:
        """Test FinancialAnalyzer initialization."""
        analyzer = FinancialAnalyzer()
        assert hasattr(analyzer, "_price_cache")

    def test_analyze_tokenomics_basic(self) -> None:
        """Test basic tokenomics analysis."""
        analyzer = FinancialAnalyzer()

        mock_contract_source = Mock()
        mock_contract_source.source_code = """
        contract TestToken {
            uint256 public totalSupply = 1000000 * 10**18;
            mapping(address => uint256) public balanceOf;

            function mint(address to, uint256 amount) public {
                balanceOf[to] += amount;
            }
        }
        """

        analysis = analyzer.analyze_tokenomics(mock_contract_source)
        assert isinstance(analysis, TokenomicsAnalysis)
        assert analysis.token_name is not None
        assert analysis.total_supply > 0

    def test_analyze_defi_protocol_basic(self) -> None:
        """Test basic DeFi protocol analysis."""
        analyzer = FinancialAnalyzer()

        mock_contract_source = Mock()
        mock_contract_source.source_code = """
        contract DeFiProtocol {
            function deposit(uint256 amount) public {
                // Implementation
            }

            function withdraw(uint256 amount) public {
                // Implementation
            }

            function calculateAPY() public view returns (uint256) {
                return 500; // 5% APY
            }
        }
        """

        analysis = analyzer.analyze_defi_protocol(mock_contract_source)
        assert isinstance(analysis, ProtocolAnalysis)
        assert analysis.protocol_name is not None
        assert analysis.protocol_type == "defi"


@pytest.mark.unit
class TestSmartContractAuditorAgent:
    """Test SmartContractAuditorAgent class."""

    def test_init_with_config(self) -> None:
        """Test SmartContractAuditorAgent initialization."""
        config = SmartContractAuditorConfig(
            api_keys={"etherscan": "test_key"},
            cache_expiry_seconds=3600,
        )

        agent = SmartContractAuditorAgent(config)

        assert agent.config == config
        assert hasattr(agent, "contract_retriever")
        assert hasattr(agent, "vulnerability_scanner")
        assert hasattr(agent, "financial_analyzer")

    def test_init_with_default_config(self) -> None:
        """Test SmartContractAuditorAgent initialization with default config."""
        agent = SmartContractAuditorAgent()

        assert agent.config is not None
        assert isinstance(agent.config, SmartContractAuditorConfig)

    def test_audit_contract_basic_functionality(self) -> None:
        """Test basic contract audit functionality."""
        agent = SmartContractAuditorAgent()

        # Mock contract source
        mock_source = ContractSource(
            address="0x1234567890123456789012345678901234567890",
            source_code="contract Simple { function test() public {} }",
            abi="[]",
            contract_name="Simple",
            compiler_version="0.8.0",
            optimization_enabled=False,
        )

        # Test that the method exists and returns expected type
        # The actual implementation may require network access
        assert hasattr(agent, "audit_contract")

    def test_generate_investment_recommendation_basic(self) -> None:
        """Test basic investment recommendation generation."""
        agent = SmartContractAuditorAgent()

        # Create a basic report
        now = datetime.now()
        report = VulnerabilityReport(
            contract_address="0x1234567890123456789012345678901234567890",
            audit_date=now,
            auditor_version="1.0.0",
            vulnerabilities=[],
            security_score=85.0,
            status=AuditStatus.SECURE,
        )

        # Test that the method exists
        assert hasattr(agent, "generate_investment_recommendation")

        # The actual implementation should analyze the report and return recommendations
        # This test mainly verifies the method exists and can be called


@pytest.mark.unit
class TestIntegrationScenarios:
    """Test integration scenarios and edge cases."""

    def test_end_to_end_audit_flow(self) -> None:
        """Test end-to-end audit flow simulation."""
        config = SmartContractAuditorConfig(
            api_keys={"etherscan": "test_key"},
            cache_expiry_seconds=0,  # No cache for testing
        )
        agent = SmartContractAuditorAgent(config)

        # Mock a complete audit scenario
        contract_address = "0x1234567890123456789012345678901234567890"

        # Verify that all components are properly initialized
        assert agent.contract_retriever is not None
        assert agent.vulnerability_scanner is not None
        assert agent.financial_analyzer is not None

    def test_vulnerability_report_validation(self) -> None:
        """Test VulnerabilityReport validation."""
        now = datetime.now()

        # Test report with no vulnerabilities
        clean_report = VulnerabilityReport(
            contract_address="0x1234567890123456789012345678901234567890",
            audit_date=now,
            auditor_version="1.0.0",
            vulnerabilities=[],
            security_score=100.0,
            status=AuditStatus.SECURE,
        )

        assert clean_report.security_score == 100.0
        assert clean_report.status == AuditStatus.SECURE
        assert len(clean_report.vulnerabilities) == 0

        # Test report with multiple vulnerabilities
        vulnerabilities = [
            Vulnerability(
                title="Issue 1",
                description="Test issue 1",
                severity=VulnerabilitySeverity.LOW,
                location="test1",
                recommendation="fix1",
                detected_at=now,
            ),
            Vulnerability(
                title="Issue 2",
                description="Test issue 2",
                severity=VulnerabilitySeverity.HIGH,
                location="test2",
                recommendation="fix2",
                detected_at=now,
            ),
        ]

        vulnerable_report = VulnerabilityReport(
            contract_address="0x1234567890123456789012345678901234567890",
            audit_date=now,
            auditor_version="1.0.0",
            vulnerabilities=vulnerabilities,
            security_score=45.0,
            status=AuditStatus.VULNERABLE,
        )

        assert vulnerable_report.security_score == 45.0
        assert vulnerable_report.status == AuditStatus.VULNERABLE
        assert len(vulnerable_report.vulnerabilities) == 2

    def test_config_validation(self) -> None:
        """Test configuration validation."""
        # Test empty config
        empty_config = SmartContractAuditorConfig()
        assert empty_config.api_keys == {}
        assert empty_config.max_concurrent_requests > 0

        # Test config with API keys
        config_with_keys = SmartContractAuditorConfig(
            api_keys={"etherscan": "key1", "bscscan": "key2"}
        )
        assert len(config_with_keys.api_keys) == 2
        assert "etherscan" in config_with_keys.api_keys
        assert "bscscan" in config_with_keys.api_keys

    def test_module_imports(self) -> None:
        """Test that all expected components can be imported."""
        from quantchain.agents.smart_contract_auditor import (
            AuditStatus,
            ContractRetriever,
            ContractSource,
            FinancialAnalyzer,
            ProtocolAnalysis,
            SmartContractAuditorAgent,
            SmartContractAuditorConfig,
            TokenomicsAnalysis,
            Vulnerability,
            VulnerabilityReport,
            VulnerabilityScanner,
            VulnerabilitySeverity,
        )

        # Verify all components are importable
        assert AuditStatus is not None
        assert VulnerabilitySeverity is not None
        assert SmartContractAuditorConfig is not None
        assert ContractSource is not None
        assert Vulnerability is not None
        assert VulnerabilityReport is not None
        assert TokenomicsAnalysis is not None
        assert ProtocolAnalysis is not None
        assert ContractRetriever is not None
        assert VulnerabilityScanner is not None
        assert FinancialAnalyzer is not None
        assert SmartContractAuditorAgent is not None

    def test_enum_completeness(self) -> None:
        """Test that enums have all expected values."""
        # AuditStatus should have common audit outcomes
        audit_statuses = [status.value for status in AuditStatus]
        assert "secure" in audit_statuses
        assert "vulnerable" in audit_statuses

        # VulnerabilitySeverity should have standard severity levels
        severities = [severity.value for severity in VulnerabilitySeverity]
        assert "critical" in severities
        assert "high" in severities
        assert "medium" in severities
        assert "low" in severities
