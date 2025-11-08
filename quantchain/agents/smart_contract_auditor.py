"""Smart Contract Auditor Agent for security and financial analysis of smart
contracts."""

import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
import re

# Required for blockchain interactions
import urllib.request
import urllib.parse
import json as json_lib

try:
    from web3 import Web3
except ImportError:
    Web3 = None  # type: ignore

from ..core.agent_engine import QuantChainAgent
from ..core.config import QuantChainConfig
from ..core.exceptions import QuantChainError
from ..core.llm_providers import LLMProvider


logger = logging.getLogger(__name__)


@dataclass
class ContractSource:
    """Contract source code and metadata."""

    address: str
    chain: str
    name: Optional[str]
    source_code: str
    abi: List[Dict[str, Any]]
    bytecode: bytes
    compiler_version: str
    optimization_enabled: bool
    constructor_arguments: str
    contract_type: str  # ERC20, ERC721, Custom, etc.
    verification_status: bool
    creation_date: datetime
    deployer_address: str
    import_paths: List[str] = field(default_factory=list)
    inherited_contracts: List[str] = field(default_factory=list)


@dataclass
class Vulnerability:
    """Security vulnerability found in contract."""

    vulnerability_type: str  # "reentrancy", "overflow", "access_control", etc.
    severity: str  # "CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"
    description: str
    location: str  # File and line number
    code_snippet: str
    recommendation: str
    cwe_id: Optional[str]  # Common Weakness Enumeration ID
    cvss_score: Optional[float]  # CVSS severity score
    confidence: float = 0.0  # Confidence in finding (0-100)


@dataclass
class VulnerabilityReport:
    """Complete vulnerability analysis report."""

    contract_address: str
    chain: str
    scan_date: datetime
    vulnerabilities: List[Vulnerability]
    overall_security_score: float  # 0-100
    gas_efficiency_score: float  # 0-100
    code_quality_score: float  # 0-100
    audit_status: str  # "SAFE", "WARNING", "DANGEROUS"
    summary: str
    recommendations: List[str]


@dataclass
class TokenomicsAnalysis:
    """Token economics analysis."""

    token_address: str
    total_supply: float
    circulating_supply: float
    holder_count: int
    top_holders: List[Dict[str, Any]]  # Address and percentage
    vesting_schedule: List[Dict[str, Any]]
    liquidity_pools: List[Dict[str, Any]]
    market_cap: float
    fully_diluted_market_cap: float
    inflation_rate: float
    distribution_score: float  # 0-100, higher = more decentralized
    token_type: str  # ERC20, ERC721, etc.
    decimals: int = 18


@dataclass
class ProtocolAnalysis:
    """DeFi protocol analysis."""

    protocol_address: str
    protocol_name: str
    total_value_locked: float
    annual_revenue: float
    apy_rates: Dict[str, float]  # Different pools/strategies
    risk_factors: List[str]
    sustainability_score: float  # 0-100
    competitor_comparison: Dict[str, Any]
    market_position: str  # "LEADER", "CHALLENGER", "NICHE"
    governance: Optional[str] = None  # DAO governance info


@dataclass
class InvestmentRecommendation:
    """Investment recommendation for a contract/protocol."""

    contract_address: str
    contract_type: str
    recommendation: str  # "STRONG_BUY", "BUY", "HOLD", "AVOID", "STRONG_AVOID"
    confidence_score: float  # 0-100
    security_score: float  # 0-100
    financial_score: float  # 0-100
    risk_level: str  # "VERY_LOW", "LOW", "MEDIUM", "HIGH", "VERY_HIGH"
    potential_return: Optional[float]
    risk_factors: List[str]
    opportunity_factors: List[str]
    investment_horizon: str  # "SHORT", "MEDIUM", "LONG"
    reasoning: str
    timestamp: datetime


@dataclass
class SmartContractAuditorConfig:
    """Configuration for the Smart Contract Auditor Agent."""

    # Analysis settings
    deep_analysis_enabled: bool = True
    gas_analysis_enabled: bool = True
    supply_chain_analysis: bool = True

    # Security thresholds
    minimum_security_score: float = 70.0
    critical_vulnerabilities_threshold: int = 0
    high_vulnerabilities_threshold: int = 2

    # Financial analysis thresholds
    minimum_liquidity: float = 100000.0  # USD
    maximum_holder_concentration: float = 0.30  # 30% top holders
    minimum_distributed_supply: float = 0.60  # 60% circulating

    # Investment criteria
    minimum_confidence_score: float = 75.0
    minimum_combined_score: float = 70.0  # Weighted average of security + financial

    # Data sources
    blockchain_explorers: Dict[str, str] = field(
        default_factory=lambda: {
            "ethereum": "https://api.etherscan.io/api",
            "bsc": "https://api.bscscan.com/api",
            "polygon": "https://api.polygonscan.com/api",
            "arbitrum": "https://api.arbiscan.io/api",
        }
    )

    # API keys for blockchain explorers
    api_keys: Dict[str, str] = field(default_factory=dict)

    # Caching settings
    cache_analysis_results: bool = True
    cache_ttl_hours: int = 24


class ContractRetriever:
    """Retrieves contract source code and metadata from blockchain explorers."""

    def __init__(self, config: SmartContractAuditorConfig):
        self.config = config

    def get_contract_source(self, address: str, chain: str) -> ContractSource:
        """Retrieve contract source code and metadata."""

        if not self.config.api_keys.get(chain):
            raise QuantChainError(f"No API key configured for {chain}")

        explorer_url = self.config.blockchain_explorers.get(chain)
        if not explorer_url:
            raise QuantChainError(f"Unsupported chain: {chain}")

        api_key = self.config.api_keys[chain]

        # Get contract source code
        source_params = {
            "module": "contract",
            "action": "getsourcecode",
            "address": address,
            "apikey": api_key,
        }

        try:
            # Ensure urllib module is available
            if urllib is None or urllib.parse is None or urllib.request is None:
                raise ImportError("urllib module not available")
            url = f"{explorer_url}?{urllib.parse.urlencode(source_params)}"
            with urllib.request.urlopen(url) as response:
                data = json_lib.loads(response.read().decode())

            if data["status"] != "1":
                raise QuantChainError(
                    f"Error retrieving source code: {data.get('message', 'Unknown')}"
                )

            result = data["result"][0]

            # Get contract creation info
            creation_params = {
                "module": "contract",
                "action": "getcontractcreation",
                "contractaddresses": address,
                "apikey": api_key,
            }

            creation_url = f"{explorer_url}?{urllib.parse.urlencode(creation_params)}"
            with urllib.request.urlopen(creation_url) as creation_response:
                creation_data = json_lib.loads(creation_response.read().decode())

            creation_date = datetime.now()
            deployer = "0x0000000000000000000000000000000000000000"

            if creation_data["status"] == "1":
                creation_result = creation_data["result"][0]
                creation_date = datetime.fromtimestamp(
                    int(creation_result["txns"][0]["timeStamp"])
                )
                deployer = creation_result["txns"][0]["contractCreator"]

            # Parse ABI
            abi = []
            if (
                result.get("ABI")
                and result["ABI"] != "Contract source code not verified"
            ):
                try:
                    abi = json_lib.loads(result["ABI"])
                except Exception:
                    logger.warning(f"Failed to parse ABI for {address}")

            return ContractSource(
                address=address,
                chain=chain,
                name=result.get("ContractName"),
                source_code=result.get("SourceCode", ""),
                abi=abi,
                bytecode=(
                    bytes.fromhex(result.get("ByteCode", "")[2:])
                    if result.get("ByteCode")
                    else b""
                ),
                compiler_version=result.get("CompilerVersion", ""),
                optimization_enabled=result.get("OptimizationUsed") == "1",
                constructor_arguments=result.get("ConstructorArguments", ""),
                contract_type=self._detect_contract_type(
                    result.get("SourceCode", ""), abi
                ),
                verification_status=result.get("SourceCode")
                != "Contract source code not verified",
                creation_date=creation_date,
                deployer_address=deployer,
                import_paths=self._extract_imports(result.get("SourceCode", "")),
                inherited_contracts=self._extract_inheritance(
                    result.get("SourceCode", "")
                ),
            )

        except Exception as e:
            raise QuantChainError(f"API request failed: {e}")
        except Exception as e:
            raise QuantChainError(f"Error processing contract data: {e}")

    def _detect_contract_type(self, source_code: str, abi: List[Dict[str, Any]]) -> str:
        """Detect contract type from source code and ABI."""

        # Check ABI for standard interfaces
        if any(
            event.get("type") == "event" and "Transfer" in event.get("name", "")
            for event in abi
        ):
            # Check if it's ERC20 or ERC721 based on parameters
            for func in abi:
                if func.get("name") == "transferFrom":
                    inputs = func.get("inputs", [])
                    if len(inputs) == 3:
                        if "uint256" in inputs[2].get("type", ""):
                            return "ERC20"
                        elif inputs[2].get("type", "") in ["uint256", "uint8"]:
                            return "ERC721"

        # Check source code for inheritance
        if "ERC20" in source_code:
            return "ERC20"
        elif "ERC721" in source_code:
            return "ERC721"
        elif "ERC1155" in source_code:
            return "ERC1155"
        elif "UniswapV2" in source_code or "UniswapV3" in source_code:
            return "DEX"
        elif "Aave" in source_code or "Compound" in source_code:
            return "Lending"

        return "Custom"

    def _extract_imports(self, source_code: str) -> List[str]:
        """Extract import statements from source code."""
        import_pattern = r'import\s+[\'"]([^\'"]+)[\'"]'
        return re.findall(import_pattern, source_code)

    def _extract_inheritance(self, source_code: str) -> List[str]:
        """Extract inherited contracts from source code."""
        # Pattern to match: contract Name is Contract1, Contract2, Contract3 {
        inheritance_pattern = r"contract\s+\w+\s+is\s+([^{\s]+(?:\s*,\s*[^{\s]+)*)\s*\{"
        matches = re.findall(inheritance_pattern, source_code)

        inherited = []
        for match in matches:
            # Split by commas and strip whitespace
            contracts = [c.strip() for c in match.split(",")]
            inherited.extend(contracts)

        return inherited


class VulnerabilityScanner:
    """Scans contracts for security vulnerabilities."""

    def __init__(self, config: SmartContractAuditorConfig):
        self.config = config
        self.vulnerability_patterns = self._load_vulnerability_patterns()

    def scan_vulnerabilities(self, contract: ContractSource) -> VulnerabilityReport:
        """Scan contract for security vulnerabilities."""

        vulnerabilities = []

        if not contract.source_code:
            return VulnerabilityReport(
                contract_address=contract.address,
                chain=contract.chain,
                scan_date=datetime.now(),
                vulnerabilities=[],
                overall_security_score=0.0,
                gas_efficiency_score=0.0,
                code_quality_score=0.0,
                audit_status="DANGEROUS",
                summary="No source code available for analysis",
                recommendations=["Verify source code on blockchain explorer"],
            )

        # Check for common vulnerability patterns
        for pattern in self.vulnerability_patterns:
            matches = self._check_pattern(contract.source_code, pattern)
            for match in matches:
                vulnerabilities.append(match)

        # Perform additional checks
        if self.config.deep_analysis_enabled:
            # Check for access control issues
            vulnerabilities.extend(self._check_access_control(contract))

            # Check for arithmetic overflow/underflow
            vulnerabilities.extend(self._check_arithmetic_issues(contract))

            # Check for reentrancy
            vulnerabilities.extend(self._check_reentrancy(contract))

        # Calculate scores
        security_score = self._calculate_security_score(vulnerabilities)
        gas_score = self._calculate_gas_efficiency_score(contract)
        quality_score = self._calculate_code_quality_score(contract, vulnerabilities)

        # Determine audit status
        audit_status = self._determine_audit_status(vulnerabilities, security_score)

        return VulnerabilityReport(
            contract_address=contract.address,
            chain=contract.chain,
            scan_date=datetime.now(),
            vulnerabilities=vulnerabilities,
            overall_security_score=security_score,
            gas_efficiency_score=gas_score,
            code_quality_score=quality_score,
            audit_status=audit_status,
            summary=self._generate_summary(vulnerabilities, security_score),
            recommendations=self._generate_recommendations(vulnerabilities),
        )

    def _load_vulnerability_patterns(self) -> List[Dict[str, Any]]:
        """Load vulnerability patterns database."""

        # Simplified pattern database - in production, this would be more comprehensive
        return [
            {
                "id": "solidity_version",
                "name": "Outdated Solidity Version",
                "cwe": "CWE-1205",
                "severity": "MEDIUM",
                "pattern": r"pragma\s+solidity\s+\^?([0-9]\.[0-9]\.[0-9])",
                "description": "Using outdated Solidity compiler version",
                "recommendation": "Update to latest stable Solidity version",
                "cvss_base": 4.3,
            },
            {
                "id": "transfer_direct",
                "name": "Direct Transfer Instead of call",
                "cwe": "CWE-843",
                "severity": "HIGH",
                "pattern": r"\.transfer\(",
                "description": "Using .transfer() can lead to failed transactions",
                "recommendation": "Use .call() with proper gas limits",
                "cvss_base": 7.5,
            },
            {
                "id": "suicide_delegatecall",
                "name": "Use of Deprecated Functions",
                "cwe": "CWE-676",
                "severity": "HIGH",
                "pattern": r"\b(suicide|selfdestruct|delegatecall\([^)]*\))",
                "description": "Using deprecated or dangerous functions",
                "recommendation": (
                    "Avoid suicide/selfdestruct, use delegatecall carefully"
                ),
                "cvss_base": 8.2,
            },
            {
                "id": "tx_origin",
                "name": "Use of tx.origin for Authentication",
                "cwe": "CWE-290",
                "severity": "HIGH",
                "pattern": r"tx\.origin",
                "description": (
                    "Using tx.origin for authentication is vulnerable to phishing"
                ),
                "recommendation": "Use msg.sender instead of tx.origin",
                "cvss_base": 7.5,
            },
        ]

    def _check_pattern(
        self, source_code: str, pattern: Dict[str, Any]
    ) -> List[Vulnerability]:
        """Check for a specific vulnerability pattern in source code."""
        vulnerabilities = []

        regex = pattern["pattern"]
        matches = list(re.finditer(regex, source_code))

        for match in matches:
            # Extract line context
            lines = source_code[: match.start()].split("\n")
            line_number = len(lines)
            context_start = max(0, line_number - 2)
            context_lines = source_code.split("\n")[context_start : line_number + 1]

            vulnerabilities.append(
                Vulnerability(
                    vulnerability_type=pattern["name"],
                    severity=pattern["severity"],
                    description=pattern["description"],
                    location=f"Line {line_number}",
                    code_snippet="\n".join(context_lines),
                    recommendation=pattern["recommendation"],
                    cwe_id=pattern["cwe"],
                    cvss_score=pattern["cvss_base"],
                    confidence=90.0,
                )
            )

        return vulnerabilities

    def _check_access_control(self, contract: ContractSource) -> List[Vulnerability]:
        """Check for access control vulnerabilities."""
        vulnerabilities = []

        # Check for public critical functions
        critical_functions = [
            "withdraw",
            "mint",
            "burn",
            "transferOwnership",
            "pause",
            "unpause",
        ]

        lines = contract.source_code.split("\n")
        for i, line in enumerate(lines):
            # Normalize the line
            line_clean = line.strip()

            for func in critical_functions:
                # Look for function declaration
                if f"function {func}(" in line_clean:
                    # Check if function is public (either explicitly or by default)
                    is_public = "public" in line_clean or (
                        "private" not in line_clean
                        and "internal" not in line_clean
                        and "external" not in line_clean
                    )

                    if is_public:
                        # Check if there's a modifier on the same or next line
                        has_modifier = False
                        # Check current line
                        if (
                            "onlyOwner" in line_clean
                            or "require(" in line_clean
                            or "isOwner" in line_clean
                            or "msg.sender == owner" in line_clean
                        ):
                            has_modifier = True
                        else:
                            # Check next few lines
                            for j in range(i + 1, min(i + 5, len(lines))):
                                next_line = lines[j].strip()
                                if (
                                    "onlyOwner" in next_line
                                    or "require(" in next_line
                                    or "isOwner" in next_line
                                    or "msg.sender == owner" in next_line
                                ):
                                    has_modifier = True
                                    break
                                # Stop if we hit another function or closing brace
                                if (
                                    next_line.startswith("}")
                                    or "function " in next_line
                                ):
                                    break

                        if not has_modifier:
                            vulnerabilities.append(
                                Vulnerability(
                                    vulnerability_type="Missing Access Control",
                                    severity="HIGH",
                                    description=(
                                        f"Critical function {func} is public "
                                        f"without access control"
                                    ),
                                    location=f"Line {i + 1}",
                                    code_snippet=line,
                                    recommendation=(
                                        f"Add access control modifier to {func} "
                                        f"function"
                                    ),
                                    cwe_id="CWE-284",
                                    cvss_score=7.5,
                                    confidence=85.0,
                                )
                            )

        return vulnerabilities

    def _check_arithmetic_issues(self, contract: ContractSource) -> List[Vulnerability]:
        """Check for arithmetic overflow/underflow issues."""
        vulnerabilities = []

        # Look for arithmetic operations without SafeMath
        lines = contract.source_code.split("\n")
        safe_math_imported = "SafeMath" in contract.source_code
        using_solidity_08 = any("pragma solidity ^0.8." in line for line in lines)

        if not safe_math_imported and not using_solidity_08:
            # Look for arithmetic operations
            arithmetic_pattern = r"([a-zA-Z_]\w*)\s*([+\-*/]=?)\s*"

            for i, line in enumerate(lines):
                if re.search(arithmetic_pattern, line):
                    # Check if it's inside SafeMath or in safe version
                    if not any(
                        safe in line
                        for safe in ["SafeMath", "add(", "sub(", "mul(", "div("]
                    ):
                        vulnerabilities.append(
                            Vulnerability(
                                vulnerability_type="Arithmetic Overflow/Underflow",
                                severity="MEDIUM",
                                description=(
                                    "Potential arithmetic overflow/"
                                    "underflow vulnerability"
                                ),
                                location=f"Line {i + 1}",
                                code_snippet=line,
                                recommendation=(
                                    "Use SafeMath library or Solidity ^0.8.0+"
                                ),
                                cwe_id="CWE-190",
                                cvss_score=5.5,
                                confidence=75.0,
                            )
                        )

        return vulnerabilities

    def _check_reentrancy(self, contract: ContractSource) -> List[Vulnerability]:
        """Check for reentrancy vulnerabilities."""
        vulnerabilities = []

        lines = contract.source_code.split("\n")

        # Look for external calls followed by state changes
        for i, line in enumerate(lines):
            if any(
                call_pattern in line
                for call_pattern in [".call(", ".transfer(", ".send("]
            ):
                # Check if state changes happen after
                for j in range(i, min(i + 5, len(lines))):
                    next_line = lines[j]
                    if any(
                        state_change in next_line
                        for state_change in ["balance[", "totalSupply", "allowance"]
                    ):
                        vulnerabilities.append(
                            Vulnerability(
                                vulnerability_type="Reentrancy",
                                severity="HIGH",
                                description="Potential reentrancy vulnerability",
                                location=f"Line {i + 1}",
                                code_snippet=line + "\n" + next_line,
                                recommendation=(
                                    "Use checks-effects-interactions pattern"
                                ),
                                cwe_id="CWE-841",
                                cvss_score=7.5,
                                confidence=80.0,
                            )
                        )
                        break

        return vulnerabilities

    def _calculate_security_score(self, vulnerabilities: List[Vulnerability]) -> float:
        """Calculate overall security score (0-100)."""
        if not vulnerabilities:
            return 100.0

        # Weight by severity
        severity_weights = {
            "CRITICAL": 40,
            "HIGH": 20,
            "MEDIUM": 10,
            "LOW": 5,
            "INFO": 1,
        }

        total_penalty: float = 0
        for vuln in vulnerabilities:
            weight = severity_weights.get(vuln.severity, 5)
            confidence_factor = vuln.confidence / 100.0
            total_penalty += weight * confidence_factor

        score = int(max(0, 100 - total_penalty))
        return score

    def _calculate_gas_efficiency_score(self, contract: ContractSource) -> float:
        """Calculate gas efficiency score."""
        if not contract.source_code:
            return 0.0

        score = 100.0

        # Deductions for inefficient patterns
        if "storage" in contract.source_code.lower():
            score -= 10  # Potential overuse of storage

        if contract.compiler_version and not contract.optimization_enabled:
            score -= 15  # Optimization not enabled

        # Check for loops in functions
        loop_patterns = ["for(", "while("]
        lines = contract.source_code.split("\n")
        loop_count = sum(
            1 for line in lines if any(pattern in line for pattern in loop_patterns)
        )

        if loop_count > 5:
            score -= 10  # Potentially gas-intensive loops

        return max(0, score)

    def _calculate_code_quality_score(
        self, contract: ContractSource, vulnerabilities: List[Vulnerability]
    ) -> float:
        """Calculate code quality score."""
        if not contract.source_code:
            return 0.0

        score = 100.0

        # Deductions based on vulnerabilities
        for vuln in vulnerabilities:
            if vuln.severity in ["CRITICAL", "HIGH"]:
                score -= 15
            elif vuln.severity == "MEDIUM":
                score -= 10
            elif vuln.severity == "LOW":
                score -= 5

        # Additional quality checks
        if not contract.verification_status:
            score -= 20  # Unverified contract

        if len(contract.source_code.split("\n")) < 50:
            score -= 10  # Very small contracts might be suspicious

        return max(0, score)

    def _determine_audit_status(
        self, vulnerabilities: List[Vulnerability], security_score: float
    ) -> str:
        """Determine overall audit status."""

        critical_count = sum(1 for v in vulnerabilities if v.severity == "CRITICAL")
        high_count = sum(1 for v in vulnerabilities if v.severity == "HIGH")

        if (
            critical_count > 0
            or high_count > self.config.high_vulnerabilities_threshold
        ):
            return "DANGEROUS"
        elif security_score < self.config.minimum_security_score:
            return "WARNING"
        else:
            return "SAFE"

    def _generate_summary(
        self, vulnerabilities: List[Vulnerability], security_score: float
    ) -> str:
        """Generate audit summary."""
        if not vulnerabilities:
            return "No vulnerabilities found. Contract appears secure."

        severity_counts: Dict[str, int] = {}
        for vuln in vulnerabilities:
            severity_counts[vuln.severity] = severity_counts.get(vuln.severity, 0) + 1

        summary_parts = [f"Security Score: {security_score:.1f}/100"]

        for severity in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]:
            if severity in severity_counts:
                summary_parts.append(f"{severity_counts[severity]} {severity} issue(s)")

        if security_score < 50:
            summary_parts.append("High-risk contract requiring immediate attention")
        elif security_score < 75:
            summary_parts.append("Medium-risk contract with security concerns")
        else:
            summary_parts.append("Low-risk contract with minor issues")

        return ". ".join(summary_parts)

    def _generate_recommendations(
        self, vulnerabilities: List[Vulnerability]
    ) -> List[str]:
        """Generate security recommendations."""
        recommendations = []

        if not vulnerabilities:
            recommendations.append("Continue following security best practices")
            return recommendations

        # Group recommendations by type
        rec_by_type: Dict[str, List[str]] = {}
        for vuln in vulnerabilities:
            vuln_type = vuln.vulnerability_type
            if vuln_type not in rec_by_type:
                rec_by_type[vuln_type] = []
            if vuln.recommendation not in rec_by_type[vuln_type]:
                rec_by_type[vuln_type].append(vuln.recommendation)

        for vuln_type, recs in rec_by_type.items():
            for rec in recs:
                recommendations.append(rec)

        # General recommendations
        critical_count = sum(1 for v in vulnerabilities if v.severity == "CRITICAL")
        if critical_count > 0:
            recommendations.insert(
                0, "CRITICAL: Address critical vulnerabilities before deployment"
            )

        return recommendations


class FinancialAnalyzer:
    """Analyzes financial aspects of tokens and DeFi protocols."""

    def __init__(self, config: SmartContractAuditorConfig):
        self.config = config

    def analyze_tokenomics(
        self, contract_address: str, chain: str
    ) -> TokenomicsAnalysis:
        """Analyze token economics and distribution."""
        # Simplified implementation - in production, would use APIs like
        # Covalent, Moralis
        return TokenomicsAnalysis(
            token_address=contract_address,
            total_supply=1000000000.0,
            circulating_supply=600000000.0,
            holder_count=5000,
            top_holders=[
                {"address": "0x123...", "percentage": 15.0},
                {"address": "0x456...", "percentage": 10.0},
            ],
            vesting_schedule=[
                {"date": "2024-01-01", "amount": 100000000.0, "type": "team"},
                {"date": "2024-07-01", "amount": 50000000.0, "type": "investors"},
            ],
            liquidity_pools=[
                {"dex": "Uniswap V2", "pair": "TOKEN/ETH", "liquidity": 1000000.0},
                {"dex": "SushiSwap", "pair": "TOKEN/USDT", "liquidity": 500000.0},
            ],
            market_cap=5000000.0,
            fully_diluted_market_cap=8333333.33,
            inflation_rate=5.0,
            distribution_score=75.0,
            token_type="ERC20",
            decimals=18,
        )

    def analyze_defi_protocol(
        self, protocol_address: str, chain: str
    ) -> ProtocolAnalysis:
        """Analyze DeFi protocol metrics and sustainability."""
        # Simplified implementation
        return ProtocolAnalysis(
            protocol_address=protocol_address,
            protocol_name="DeFi Protocol",
            total_value_locked=50000000.0,
            annual_revenue=2500000.0,
            apy_rates={"stable_pool": 8.5, "volatile_pool": 15.2, "farm_pool": 25.7},
            risk_factors=[
                "Smart contract risk",
                "Impermanent loss",
                "Regulatory uncertainty",
            ],
            sustainability_score=80.0,
            competitor_comparison={
                "protocol_a": {"tvl": 75000000, "apy": 12.0},
                "protocol_b": {"tvl": 30000000, "apy": 18.5},
            },
            market_position="CHALLENGER",
            governance="DAO with token voting",
        )


class SmartContractAuditorAgent(QuantChainAgent):
    """Smart Contract Auditor Agent for security and financial analysis."""

    def __init__(
        self,
        config: QuantChainConfig,
        llm_provider: Optional[LLMProvider] = None,
        agent_config: Optional[SmartContractAuditorConfig] = None,
    ):
        self.agent_config = agent_config or SmartContractAuditorConfig()

        # Initialize base agent
        super().__init__(config, llm_provider=llm_provider)

        # Initialize components
        self.contract_retriever = ContractRetriever(self.agent_config)
        self.vulnerability_scanner = VulnerabilityScanner(self.agent_config)
        self.financial_analyzer = FinancialAnalyzer(self.agent_config)

    def audit_contract(
        self, address: str, chain: str, financial_analysis: bool = True
    ) -> Dict[str, Any]:
        """Perform comprehensive contract audit."""

        try:
            # Get contract source and metadata
            contract = self.contract_retriever.get_contract_source(address, chain)

            # Perform security analysis
            vulnerability_report = self.vulnerability_scanner.scan_vulnerabilities(
                contract
            )

            # Perform financial analysis if requested
            tokenomics = None
            protocol_analysis = None

            if financial_analysis:
                if contract.contract_type == "ERC20":
                    tokenomics = self.financial_analyzer.analyze_tokenomics(
                        address, chain
                    )
                else:
                    protocol_analysis = self.financial_analyzer.analyze_defi_protocol(
                        address, chain
                    )

            # Generate investment recommendation
            recommendation = self._generate_investment_recommendation(
                contract, vulnerability_report, tokenomics, protocol_analysis
            )

            return {
                "contract": {
                    "address": address,
                    "chain": chain,
                    "name": contract.name,
                    "type": contract.contract_type,
                    "verified": contract.verification_status,
                    "compiler_version": contract.compiler_version,
                    "creation_date": contract.creation_date.isoformat(),
                },
                "security": {
                    "score": vulnerability_report.overall_security_score,
                    "status": vulnerability_report.audit_status,
                    "vulnerabilities": [
                        {
                            "type": v.vulnerability_type,
                            "severity": v.severity,
                            "description": v.description,
                            "location": v.location,
                            "recommendation": v.recommendation,
                        }
                        for v in vulnerability_report.vulnerabilities
                    ],
                    "summary": vulnerability_report.summary,
                    "recommendations": vulnerability_report.recommendations,
                },
                "financial": {
                    "tokenomics": (
                        {
                            "total_supply": tokenomics.total_supply,
                            "circulating_supply": tokenomics.circulating_supply,
                            "distribution_score": tokenomics.distribution_score,
                            "market_cap": tokenomics.market_cap,
                        }
                        if tokenomics
                        else None
                    ),
                    "protocol": (
                        {
                            "name": protocol_analysis.protocol_name,
                            "tvl": protocol_analysis.total_value_locked,
                            "apy_rates": protocol_analysis.apy_rates,
                            "sustainability_score": (
                                protocol_analysis.sustainability_score
                            ),
                        }
                        if protocol_analysis
                        else None
                    ),
                },
                "investment": {
                    "recommendation": recommendation.recommendation,
                    "confidence": recommendation.confidence_score,
                    "risk_level": recommendation.risk_level,
                    "potential_return": recommendation.potential_return,
                    "horizon": recommendation.investment_horizon,
                    "reasoning": recommendation.reasoning,
                    "risk_factors": recommendation.risk_factors,
                    "opportunity_factors": recommendation.opportunity_factors,
                },
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"Error auditing contract {address}: {e}")
            return {
                "error": str(e),
                "contract": {"address": address, "chain": chain},
                "timestamp": datetime.now().isoformat(),
            }

    def _generate_investment_recommendation(
        self,
        contract: ContractSource,
        vulnerability_report: VulnerabilityReport,
        tokenomics: Optional[TokenomicsAnalysis],
        protocol_analysis: Optional[ProtocolAnalysis],
    ) -> InvestmentRecommendation:
        """Generate investment recommendation based on all analyses."""

        security_score = vulnerability_report.overall_security_score

        # Calculate financial score
        financial_score = 50.0  # Default if no financial data
        if tokenomics:
            financial_score = (
                min(100, tokenomics.distribution_score * 0.4)
                + min(
                    100,
                    (tokenomics.circulating_supply / tokenomics.total_supply * 100)
                    * 0.3,
                )
                + min(
                    100,
                    (1 - max(0, tokenomics.market_cap - 10000000) / 10000000)
                    * 100
                    * 0.3,
                )
            )
        elif protocol_analysis:
            financial_score = (
                min(100, protocol_analysis.sustainability_score * 0.5)
                + min(
                    100,
                    (
                        1
                        - max(0, protocol_analysis.total_value_locked - 100000000)
                        / 100000000
                    )
                    * 100
                    * 0.3,
                )
                + min(
                    100,
                    (
                        1
                        - max(0, max(protocol_analysis.apy_rates.values() or [0]) - 30)
                        / 30
                    )
                    * 100
                    * 0.2,
                )
            )

        # Determine recommendation
        avg_score = security_score * 0.6 + financial_score * 0.4

        if security_score < 30:
            recommendation = "STRONG_AVOID"
            risk_level = "VERY_HIGH"
        elif security_score < 50:
            recommendation = "AVOID"
            risk_level = "HIGH"
        elif avg_score < 60:
            recommendation = "HOLD"
            risk_level = "MEDIUM"
        elif avg_score < 75:
            recommendation = "BUY"
            risk_level = "MEDIUM"
        else:
            recommendation = "STRONG_BUY"
            risk_level = "LOW"

        # Collect risk and opportunity factors
        risk_factors = []
        opportunity_factors = []

        if vulnerability_report.vulnerabilities:
            risk_factors.append(
                f"{len(vulnerability_report.vulnerabilities)} security issues found"
            )

        if not contract.verification_status:
            risk_factors.append("Contract source not verified")

        if tokenomics:
            if tokenomics.distribution_score < 50:
                risk_factors.append("Poor token distribution")
            if tokenomics.market_cap < 1000000:
                opportunity_factors.append("Low market cap with growth potential")

        if protocol_analysis:
            if protocol_analysis.sustainability_score > 80:
                opportunity_factors.append("High protocol sustainability")
            if protocol_analysis.total_value_locked < 10000000:
                opportunity_factors.append("Undervalued protocol with growth potential")

        # Calculate potential return (simplified)
        potential_return = None
        if tokenomics and tokenomics.market_cap > 0:
            # Simplified calculation based on market cap and distribution
            potential_return = max(
                0, (100 - security_score) / 100 * 50 + financial_score / 100 * 30
            )

        return InvestmentRecommendation(
            contract_address=contract.address,
            contract_type=contract.contract_type,
            recommendation=recommendation,
            confidence_score=avg_score,
            security_score=security_score,
            financial_score=financial_score,
            risk_level=risk_level,
            potential_return=potential_return,
            risk_factors=risk_factors,
            opportunity_factors=opportunity_factors,
            investment_horizon="MEDIUM",  # Default
            reasoning=(
                f"Based on security score of {security_score:.1f} "
                f"and financial score of {financial_score:.1f}"
            ),
            timestamp=datetime.now(),
        )
