"""Smart Contract Auditor Agent for QuantChain."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class AuditStatus(Enum):
    """Audit status enumeration."""

    SECURE = "secure"
    VULNERABLE = "vulnerable"
    REQUIRES_REVIEW = "requires_review"
    INSUFFICIENT_DATA = "insufficient_data"


class VulnerabilitySeverity(Enum):
    """Vulnerability severity enumeration."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


@dataclass
class SmartContractAuditorConfig:
    """Configuration for Smart Contract Auditor Agent."""

    api_keys: Dict[str, str] = field(default_factory=dict)
    etherscan_api_url: str = "https://api.etherscan.io/api"
    bscscan_api_url: str = "https://api.bscscan.com/api"
    polygonscan_api_url: str = "https://api.polygonscan.com/api"
    cache_expiry_seconds: int = 86400  # 24 hours
    max_concurrent_requests: int = 5
    request_timeout_seconds: int = 30


@dataclass
class ContractSource:
    """Contract source code information."""

    address: str
    source_code: str
    abi: str
    contract_name: str
    compiler_version: str
    optimization_enabled: bool
    constructor_arguments: str
    network: str
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class Vulnerability:
    """Represents a vulnerability found in a smart contract."""

    id: str
    title: str
    description: str
    severity: VulnerabilitySeverity
    line_number: Optional[int] = None
    code_snippet: Optional[str] = None
    references: List[str] = field(default_factory=list)
    confidence: float = 1.0  # 0.0 to 1.0


@dataclass
class VulnerabilityReport:
    """Report of vulnerabilities found in a smart contract."""

    address: str
    network: str
    vulnerabilities: List[Vulnerability]
    timestamp: datetime = field(default_factory=datetime.now)
    security_score: Optional[float] = None  # 0.0 to 10.0
    audit_status: Optional[AuditStatus] = None
    scan_duration: Optional[float] = None  # seconds


@dataclass
class TokenomicsAnalysis:
    """Analysis of tokenomics for a contract."""

    address: str
    network: str
    total_supply: Optional[float] = None
    circulating_supply: Optional[float] = None
    holders_count: Optional[int] = None
    top_holders: List[Dict[str, Any]] = field(default_factory=list)
    token_distribution: Dict[str, float] = field(default_factory=dict)
    inflation_rate: Optional[float] = None
    burn_mechanism: bool = False
    minting_allowed: bool = False
    pausable: bool = False
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class ProtocolAnalysis:
    """Analysis of DeFi protocol components."""

    address: str
    network: str
    protocol_type: str  # e.g., "dex", "lending", "yield", "liquidity"
    dependencies: List[str] = field(default_factory=list)
    integration_points: List[str] = field(default_factory=list)
    tvl: Optional[float] = None  # Total Value Locked
    apy: Optional[float] = None  # Annual Percentage Yield
    impermanent_loss_risk: Optional[str] = None  # "low", "medium", "high"
    liquidation_risk: Optional[str] = None  # "low", "medium", "high"
    governance_model: Optional[str] = None  # "centralized", "dao", "multisig"
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class InvestmentRecommendation:
    """Investment recommendation for a contract."""

    address: str
    network: str
    recommendation: str  # "invest", "avoid", "caution"
    confidence: float  # 0.0 to 1.0
    reasons: List[str] = field(default_factory=list)
    risk_factors: List[str] = field(default_factory=list)
    upside_potential: Optional[float] = None  # percentage
    downside_risk: Optional[float] = None  # percentage
    time_horizon: Optional[str] = None  # "short", "medium", "long"
    expected_apy: Optional[float] = None  # percentage
    audit_score: Optional[float] = None  # 0.0 to 10.0
    timestamp: datetime = field(default_factory=datetime.now)


class ContractRetriever:
    """Retrieves contract source code from blockchain explorers."""

    def __init__(self, config: SmartContractAuditorConfig):
        """
        Initialize ContractRetriever.

        Args:
            config: Configuration for the retriever
        """
        self.config = config
        self._cache = {}

    def get_contract_source(
        self, address: str, network: str
    ) -> Optional[ContractSource]:
        """
        Get contract source code from blockchain explorer.

        Args:
            address: Contract address
            network: Blockchain network name

        Returns:
            ContractSource object or None if not found
        """
        # Check cache first
        cache_key = f"{network}:{address}"
        if cache_key in self._cache:
            cached_item = self._cache[cache_key]
            # Check if cache is still valid
            time_diff = (datetime.now() - cached_item["timestamp"]).total_seconds()
            if time_diff < self.config.cache_expiry_seconds:
                return cached_item["source"]

        # Get API key for network
        api_key = self.config.api_keys.get(network)
        if not api_key:
            return None

        # Determine API URL based on network
        if network == "ethereum":
            api_url = self.config.etherscan_api_url
        elif network == "bsc":
            api_url = self.config.bscscan_api_url
        elif network == "polygon":
            api_url = self.config.polygonscan_api_url
        else:
            return None

        # In a real implementation, make HTTP request to get source code
        # For testing purposes, return a mock contract
        mock_source = ContractSource(
            address=address,
            source_code="""
            pragma solidity ^0.8.0;

            contract MockToken {{
                mapping(address => uint256) public balanceOf;
                uint256 public totalSupply = 100000000;

                function transfer(address to, uint256 amount) public {{
                    balanceOf[msg.sender] -= amount;
                    balanceOf[to] += amount;
                }}
            }}
            """,
            abi='[{"type":"event","name":"Transfer","inputs":[]}]',
            contract_name="MockToken",
            compiler_version="v0.8.0+commit.c7dfd78e",
            optimization_enabled=True,
            constructor_arguments="",
            network=network,
        )

        # Cache the result
        self._cache[cache_key] = {"source": mock_source, "timestamp": datetime.now()}

        return mock_source

    def detect_contract_type(self, contract_source: ContractSource) -> str:
        """
        Detect contract type based on source code patterns.

        Args:
            contract_source: Contract source information

        Returns:
            String describing contract type (e.g., "ERC20", "ERC721", "Custom")
        """
        source_code = contract_source.source_code.lower()

        if "interface ierc20" in source_code or "interface erc20" in source_code:
            return "ERC20"
        elif "interface ierc721" in source_code or "interface erc721" in source_code:
            return "ERC721"
        elif "interface ierc1155" in source_code or "interface erc1155" in source_code:
            return "ERC1155"
        elif "contract" in source_code and "token" in source_code:
            return "Custom Token"
        else:
            return "Custom"

    def extract_imports(self, contract_source: ContractSource) -> List[str]:
        """
        Extract import statements from contract source.

        Args:
            contract_source: Contract source information

        Returns:
            List of import statements
        """
        source_lines = contract_source.source_code.split("\n")
        imports = []

        for line in source_lines:
            stripped = line.strip()
            if stripped.startswith("import "):
                imports.append(stripped)

        return imports

    def extract_inheritance(self, contract_source: ContractSource) -> List[str]:
        """
        Extract contract inheritance information.

        Args:
            contract_source: Contract source information

        Returns:
            List of parent contracts
        """
        source_lines = contract_source.source_code.split("\n")
        inheritance = []

        for line in source_lines:
            if "is" in line and "contract" in line:
                # Extract inheritance after "is" and before "{"
                parts = line.split("is")
                if len(parts) > 1:
                    inherit_part = parts[1].split("{")[0].strip()
                    contracts = [c.strip() for c in inherit_part.split(",")]
                    inheritance.extend(contracts)

        return inheritance


class VulnerabilityScanner:
    """Scans smart contracts for security vulnerabilities."""

    def __init__(self, config: SmartContractAuditorConfig):
        """
        Initialize VulnerabilityScanner.

        Args:
            config: Configuration for the scanner
        """
        self.config = config
        self._vulnerability_patterns = [
            {
                "id": "reentrancy",
                "title": "Reentrancy Vulnerability",
                "description": "Contract may be vulnerable to reentrancy attacks",
                "severity": VulnerabilitySeverity.CRITICAL,
                "patterns": ["call.value", ".call(", ".send(", ".transfer("],
                "context": [".call(", "external", "payable"],
            },
            {
                "id": "overflow",
                "title": "Integer Overflow/Underflow",
                "description": "Contract may be vulnerable to integer overflow/underflow",
                "severity": VulnerabilitySeverity.HIGH,
                "patterns": ["+=", "-=", "*=", "/="],
                "context": ["uint256", "uint", "int", "int256"],
            },
            {
                "id": "access_control",
                "title": "Access Control Issue",
                "description": "Contract lacks proper access control",
                "severity": VulnerabilitySeverity.MEDIUM,
                "patterns": ["function", "modifier"],
                "context": ["public", "external"],
            },
        ]

    def scan_vulnerabilities(
        self, contract_source: ContractSource
    ) -> VulnerabilityReport:
        """
        Scan contract source for vulnerabilities.

        Args:
            contract_source: Contract source information

        Returns:
            VulnerabilityReport with found vulnerabilities
        """
        vulnerabilities = []
        source_lines = contract_source.source_code.split("\n")

        # In a real implementation, use more sophisticated analysis
        # For testing purposes, use simple pattern matching

        for pattern_info in self._vulnerability_patterns:
            for i, line in enumerate(source_lines):
                # Simple pattern matching
                for pattern in pattern_info["patterns"]:
                    if pattern in line:
                        # Found potential vulnerability
                        vulnerability = Vulnerability(
                            id=pattern_info["id"],
                            title=pattern_info["title"],
                            description=pattern_info["description"],
                            severity=pattern_info["severity"],
                            line_number=i + 1,
                            code_snippet=line.strip(),
                        )
                        vulnerabilities.append(vulnerability)
                        break

        # Create report
        report = VulnerabilityReport(
            address=contract_source.address,
            network=contract_source.network,
            vulnerabilities=vulnerabilities,
        )

        # Calculate security score
        report.security_score = self.calculate_security_score(vulnerabilities)

        # Determine audit status
        report.audit_status = self.determine_audit_status(
            report.security_score, vulnerabilities
        )

        return report

    def check_access_control(
        self, contract_source: ContractSource
    ) -> List[Vulnerability]:
        """
        Check for access control vulnerabilities.

        Args:
            contract_source: Contract source information

        Returns:
            List of access control vulnerabilities
        """
        vulnerabilities = []
        source_lines = contract_source.source_code.split("\n")

        # Check for public/external functions without access control
        for i, line in enumerate(source_lines):
            stripped = line.strip()
            if stripped.startswith("function ") and (
                "public" in stripped or "external" in stripped
            ):
                # Check if function has access control
                function_def = stripped
                has_modifier = (
                    " onlyOwner " in function_def or " requiresAuth " in function_def
                )

                # Look for the opening brace to find the function body
                j = i + 1
                while j < len(source_lines) and "{" not in source_lines[j]:
                    j += 1

                if (
                    not has_modifier
                    and "view" not in function_def
                    and "pure" not in function_def
                ):
                    vulnerability = Vulnerability(
                        id="access_control",
                        title="Access Control Issue",
                        description="Function lacks proper access control",
                        severity=VulnerabilitySeverity.MEDIUM,
                        line_number=i + 1,
                        code_snippet=stripped,
                    )
                    vulnerabilities.append(vulnerability)

        return vulnerabilities

    def calculate_security_score(self, vulnerabilities: List[Vulnerability]) -> float:
        """
        Calculate a security score based on found vulnerabilities.

        Args:
            vulnerabilities: List of vulnerabilities found

        Returns:
            Security score from 0.0 to 10.0
        """
        if not vulnerabilities:
            return 10.0

        # Base score is 10
        score = 10.0

        # Deduct points based on severity
        for vuln in vulnerabilities:
            if vuln.severity == VulnerabilitySeverity.CRITICAL:
                score -= 3.0
            elif vuln.severity == VulnerabilitySeverity.HIGH:
                score -= 2.0
            elif vuln.severity == VulnerabilitySeverity.MEDIUM:
                score -= 1.0
            elif vuln.severity == VulnerabilitySeverity.LOW:
                score -= 0.5
            else:  # INFO
                score -= 0.2

        # Ensure score is between 0 and 10
        return max(0.0, min(10.0, score))

    def determine_audit_status(
        self, security_score: float, vulnerabilities: List[Vulnerability]
    ) -> AuditStatus:
        """
        Determine audit status based on security score and vulnerabilities.

        Args:
            security_score: Calculated security score
            vulnerabilities: List of vulnerabilities found

        Returns:
            AuditStatus enumeration
        """
        # Check for critical vulnerabilities
        critical_vulns = [
            v for v in vulnerabilities if v.severity == VulnerabilitySeverity.CRITICAL
        ]
        if critical_vulns:
            return AuditStatus.VULNERABLE

        # Determine status based on security score
        if security_score >= 8.0:
            return AuditStatus.SECURE
        elif security_score >= 5.0:
            return AuditStatus.REQUIRES_REVIEW
        else:
            return AuditStatus.VULNERABLE


class FinancialAnalyzer:
    """Analyzes financial aspects of smart contracts."""

    def __init__(self, config: SmartContractAuditorConfig):
        """
        Initialize FinancialAnalyzer.

        Args:
            config: Configuration for the analyzer
        """
        self.config = config

    def analyze_tokenomics(self, contract_source: ContractSource) -> TokenomicsAnalysis:
        """
        Analyze tokenomics of a token contract.

        Args:
            contract_source: Contract source information

        Returns:
            TokenomicsAnalysis with token information
        """
        analysis = TokenomicsAnalysis(
            address=contract_source.address, network=contract_source.network
        )

        source_code = contract_source.source_code.lower()

        # Extract tokenomics information from source
        if "totalsupply" in source_code:
            analysis.total_supply = 100000000  # Mock value
            analysis.circulating_supply = 50000000  # Mock value

        # Check for specific features
        analysis.burn_mechanism = "burn" in source_code
        analysis.minting_allowed = "mint" in source_code or "_mint" in source_code
        analysis.pausable = "pause" in source_code or "paused" in source_code

        # Mock holders data
        analysis.holders_count = 1500  # Mock value
        analysis.top_holders = [
            {"address": "0x1234567890abcdef", "percentage": 10.5},
            {"address": "0xabcdef1234567890", "percentage": 5.2},
            {"address": "0x5678901234abcdef", "percentage": 3.1},
        ]
        analysis.token_distribution = {
            "team": 15.0,
            "investors": 20.0,
            "public_sale": 25.0,
            "treasury": 40.0,
        }

        return analysis

    def analyze_defi_protocol(
        self, contract_source: ContractSource
    ) -> ProtocolAnalysis:
        """
        Analyze DeFi protocol components.

        Args:
            contract_source: Contract source information

        Returns:
            ProtocolAnalysis with protocol information
        """
        source_code = contract_source.source_code.lower()

        # Determine protocol type
        if ("swap" in source_code or "exchange" in source_code) and (
            "liquidity" in source_code
        ):
            protocol_type = "dex"
        elif ("lend" in source_code or "borrow" in source_code) and (
            "interest" in source_code
        ):
            protocol_type = "lending"
        elif "reward" in source_code or "yield" in source_code:
            protocol_type = "yield"
        elif "farm" in source_code or "stake" in source_code:
            protocol_type = "liquidity"
        else:
            protocol_type = "other"

        analysis = ProtocolAnalysis(
            address=contract_source.address,
            network=contract_source.network,
            protocol_type=protocol_type,
        )

        # Mock additional data
        analysis.tvl = 1000000.0  # $1M mock value
        analysis.apy = 12.5  # 12.5% mock APY
        analysis.impermanent_loss_risk = "medium"
        analysis.liquidation_risk = "low"
        analysis.governance_model = "dao"

        return analysis


class SmartContractAuditorAgent:
    """Agent for auditing smart contracts."""

    def __init__(self, config: SmartContractAuditorConfig):
        """
        Initialize SmartContractAuditorAgent.

        Args:
            config: Configuration for the agent
        """
        self.config = config
        self.retriever = ContractRetriever(config)
        self.scanner = VulnerabilityScanner(config)
        self.analyzer = FinancialAnalyzer(config)

    def audit_contract(self, address: str, network: str) -> Dict[str, Any]:
        """
        Perform a comprehensive audit of a smart contract.

        Args:
            address: Contract address
            network: Blockchain network name

        Returns:
            Dictionary containing audit results
        """
        # Get contract source
        contract_source = self.retriever.get_contract_source(address, network)
        if not contract_source:
            return {
                "error": "Could not retrieve contract source",
                "address": address,
                "network": network,
            }

        # Detect contract type
        contract_type = self.retriever.detect_contract_type(contract_source)

        # Scan for vulnerabilities
        vulnerability_report = self.scanner.scan_vulnerabilities(contract_source)

        # Analyze tokenomics if it's a token contract
        tokenomics_analysis = None
        if "token" in contract_type.lower():
            tokenomics_analysis = self.analyzer.analyze_tokenomics(contract_source)

        # Analyze DeFi protocol if applicable
        protocol_analysis = self.analyzer.analyze_defi_protocol(contract_source)

        # Generate investment recommendation
        recommendation = self.generate_investment_recommendation(
            contract_source,
            vulnerability_report,
            tokenomics_analysis,
            protocol_analysis,
        )

        return {
            "address": address,
            "network": network,
            "contract_type": contract_type,
            "vulnerability_report": vulnerability_report,
            "tokenomics_analysis": tokenomics_analysis,
            "protocol_analysis": protocol_analysis,
            "recommendation": recommendation,
        }

    def generate_investment_recommendation(
        self,
        contract_source: ContractSource,
        vulnerability_report: VulnerabilityReport,
        tokenomics_analysis: Optional[TokenomicsAnalysis] = None,
        protocol_analysis: Optional[ProtocolAnalysis] = None,
    ) -> InvestmentRecommendation:
        """
        Generate an investment recommendation based on analysis.

        Args:
            contract_source: Contract source information
            vulnerability_report: Vulnerability scan results
            tokenomics_analysis: Tokenomics analysis (if applicable)
            protocol_analysis: Protocol analysis (if applicable)

        Returns:
            InvestmentRecommendation with investment advice
        """
        # Default recommendation
        recommendation = "caution"
        confidence = 0.5
        reasons = []
        risk_factors = []
        upside_potential = None
        downside_risk = None

        # Consider vulnerability report
        if vulnerability_report.audit_status == AuditStatus.SECURE:
            reasons.append("Security audit passed with high score")
            confidence += 0.2
        elif vulnerability_report.audit_status == AuditStatus.VULNERABLE:
            risk_factors.append("Critical security vulnerabilities found")
            recommendation = "avoid"
            confidence += 0.3

        # Consider tokenomics
        if tokenomics_analysis:
            if tokenomics_analysis.burn_mechanism:
                reasons.append("Token has burn mechanism which can increase value")

            if tokenomics_analysis.minting_allowed:
                risk_factors.append("Unlimited minting possible")

            if (
                tokenomics_analysis.holders_count
                and tokenomics_analysis.holders_count > 1000
            ):
                reasons.append("Wide token distribution")

        # Consider protocol
        if protocol_analysis and protocol_analysis.protocol_type in [
            "dex",
            "lending",
            "yield",
        ]:
            if protocol_analysis.apy and protocol_analysis.apy > 10.0:
                reasons.append(f"High APY: {protocol_analysis.apy}%")
                upside_potential = protocol_analysis.apy

                # Higher APY usually means higher risk
                if protocol_analysis.apy > 20.0:
                    risk_factors.append("Extremely high APY may indicate high risk")

        # Finalize recommendation and confidence
        confidence = min(1.0, max(0.0, confidence))

        if recommendation == "caution":
            if confidence > 0.7:
                recommendation = "invest"
            elif confidence < 0.3:
                recommendation = "avoid"

        # Estimate upside/downside based on confidence
        if upside_potential is None:
            upside_potential = confidence * 15.0  # Mock value

        downside_risk = (1.0 - confidence) * 20.0  # Mock value

        return InvestmentRecommendation(
            address=contract_source.address,
            network=contract_source.network,
            recommendation=recommendation,
            confidence=confidence,
            reasons=reasons,
            risk_factors=risk_factors,
            upside_potential=upside_potential,
            downside_risk=downside_risk,
            time_horizon="medium",
            expected_apy=upside_potential if protocol_analysis else None,
            audit_score=vulnerability_report.security_score,
        )
