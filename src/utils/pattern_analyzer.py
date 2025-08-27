import re
from typing import Dict, List, Any
from dataclasses import dataclass
import structlog

logger = structlog.get_logger(__name__)

@dataclass
class SecurityPattern:
    name: str
    pattern: str
    severity: str  # 'low', 'medium', 'high', 'critical'
    description: str
    remediation: str

class AdvancedPatternAnalyzer:
    """Production-grade pattern analyzer with ML-ready features."""

    def __init__(self):
        self.security_patterns = self._load_security_patterns()
        self.quality_patterns = self._load_quality_patterns()
        self.performance_patterns = self._load_performance_patterns()

    def _load_security_patterns(self) -> List[SecurityPattern]:
        """Load security patterns from configuration."""
        return [
            SecurityPattern(
                name="sql_injection",
                pattern=r"SELECT.*WHERE.*\$\{|INSERT INTO.*\$\{|UPDATE.*SET.*\$\{|DELETE FROM.*\$\{|execute\(.*\+.*\)|cursor\.execute\(.*\+.*\)",
                severity="critical",
                description="Potential SQL injection vulnerability",
                remediation="Use parameterized queries or ORM"
            ),
            SecurityPattern(
                name="password_exposure",
                pattern=r"password.*=.*input\(|password.*=.*request\.|password.*=.*get\(|password.*=.*post\(|password.*=.*form\(|password.*=.*args\[",
                severity="high",
                description="Password handling without proper validation",
                remediation="Implement secure password validation and hashing"
            ),
            SecurityPattern(
                name="hardcoded_credentials",
                pattern=r"password.*=.*['\"][^'\"]{8,}['\"]|api_key.*=.*['\"][^'\"]{20,}['\"]|secret.*=.*['\"][^'\"]{10,}['\"]",
                severity="high",
                description="Hardcoded credentials in code",
                remediation="Move credentials to environment variables or secure vault"
            ),
            SecurityPattern(
                name="authentication_bypass",
                pattern=r"if.*admin.*==.*true|if.*user.*==.*admin|if.*role.*==.*admin|bypass.*auth|skip.*auth|disable.*auth",
                severity="critical",
                description="Potential authentication bypass",
                remediation="Implement proper authentication and authorization"
            ),
            SecurityPattern(
                name="input_validation",
                pattern=r"# No validation|# TODO.*validation|# FIXME.*validation|def.*\(.*\):\s*\n\s*return|def.*\(.*\):\s*\n\s*pass",
                severity="medium",
                description="Missing input validation",
                remediation="Add proper input validation for user-provided data"
            )
        ]

    def _load_quality_patterns(self) -> List[SecurityPattern]:
        """Load code quality patterns."""
        return [
            SecurityPattern(
                name="hardcoded_values",
                pattern=r"= ['\"]\d{4,}['\"]|= ['\"][a-zA-Z0-9]{20,}['\"]|= ['\"]https?://[^'\"]*['\"]|= ['\"]\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}['\"]",
                severity="low",
                description="Hardcoded values in code",
                remediation="Move hardcoded values to configuration files"
            ),
            SecurityPattern(
                name="error_handling",
                pattern=r"except:|except Exception:|except.*pass|# TODO.*error|# FIXME.*error",
                severity="medium",
                description="Poor error handling",
                remediation="Implement proper exception handling with specific exception types"
            ),
            SecurityPattern(
                name="logging",
                pattern=r"print\(|console\.log\(|System\.out\.println\(|# TODO.*log",
                severity="low",
                description="Debug logging in production code",
                remediation="Replace debug statements with proper logging framework"
            ),
            SecurityPattern(
                name="documentation",
                pattern=r"def.*\(.*\):\s*\n\s*\"\"\"|# TODO.*doc|# FIXME.*doc|# HACK|# XXX",
                severity="low",
                description="Missing or poor documentation",
                remediation="Add proper docstrings and comments"
            )
        ]

    def _load_performance_patterns(self) -> List[SecurityPattern]:
        """Load performance patterns."""
        return [
            SecurityPattern(
                name="nested_loops",
                pattern=r"for.*:\s*\n.*for.*:",
                severity="medium",
                description="Nested loops detected",
                remediation="Consider refactoring to reduce complexity"
            ),
            SecurityPattern(
                name="long_functions",
                pattern=r"def.*\(.*\):\s*\n(?:.*\n){20,}",
                severity="medium",
                description="Long functions detected",
                remediation="Break down into smaller, focused functions"
            ),
            SecurityPattern(
                name="magic_numbers",
                pattern=r"\b\d{3,}\b",
                severity="low",
                description="Magic numbers in code",
                remediation="Define constants for numeric values"
            )
        ]

    def analyze_commit_security(self, diff_content: str, file_diffs: Dict[str, Any]) -> Dict[str, Any]:
        """Comprehensive security analysis."""
        results = {
            "overall_risk_score": 0,
                "critical_issues": [],
                    "high_risk_issues": [],
                    "medium_risk_issues": [],
                    "low_risk_issues": [],
                    "recommendations": [],
                    "file_analysis": {}
        }

        # Analyze each security pattern
        for pattern in self.security_patterns:
            matches = re.findall(pattern.pattern, diff_content, re.IGNORECASE)
            if matches:
                issue = {
                    "pattern": pattern.name,
                        "severity": pattern.severity,
                            "description": pattern.description,
                            "remediation": pattern.remediation,
                            "matches": matches[:5],  # Limit matches
                    "count": len(matches)
                }

                if pattern.severity == "critical":
                    results["critical_issues"].append(issue)
                    results["overall_risk_score"] += 40
                elif pattern.severity == "high":
                    results["high_risk_issues"].append(issue)
                    results["overall_risk_score"] += 25
                elif pattern.severity == "medium":
                    results["medium_risk_issues"].append(issue)
                    results["overall_risk_score"] += 15
                else:
                    results["low_risk_issues"].append(issue)
                    results["overall_risk_score"] += 5

        # Cap risk score at 100
        results["overall_risk_score"] = min(results["overall_risk_score"], 100)

        # Generate recommendations
        results["recommendations"] = self._generate_security_recommendations(results)

        # Analyze file-specific security
        results["file_analysis"] = self._analyze_file_security(file_diffs)

        return results

    def analyze_code_quality(self, diff_content: str, file_diffs: Dict[str, Any]) -> Dict[str, Any]:
        """Advanced code quality analysis."""
        results = {
            "quality_score": 100,  # Start with perfect score
            "issues": [],
                "improvements": [],
                    "metrics": {
                "complexity": 0,
                    "maintainability": 0,
                        "readability": 0,
                        "documentation": 0
            }
        }

        # Analyze code complexity
        complexity_issues = self._analyze_complexity(diff_content)
        results["issues"].extend(complexity_issues)
        results["quality_score"] -= len(complexity_issues) * 5

        # Analyze maintainability
        maintainability_issues = self._analyze_maintainability(diff_content)
        results["issues"].extend(maintainability_issues)
        results["quality_score"] -= len(maintainability_issues) * 3

        # Analyze readability
        readability_issues = self._analyze_readability(diff_content)
        results["issues"].extend(readability_issues)
        results["quality_score"] -= len(readability_issues) * 2

        # Ensure quality score doesn't go below 0
        results["quality_score"] = max(results["quality_score"], 0)

        return results

    def _analyze_complexity(self, diff_content: str) -> List[Dict[str, Any]]:
        """Analyze code complexity patterns."""
        issues = []

        # Check for nested loops
        nested_loops = re.findall(r"for.*:\s*\n.*for.*:", diff_content)
        if nested_loops:
            issues.append({
                "type": "complexity",
                    "issue": "Nested loops detected",
                        "severity": "medium",
                        "recommendation": "Consider refactoring to reduce complexity"
            })

        # Check for long functions
        long_functions = re.findall(r"def.*\(.*\):\s*\n(?:.*\n){20,}", diff_content)
        if long_functions:
            issues.append({
                "type": "complexity",
                    "issue": "Long functions detected",
                        "severity": "medium",
                        "recommendation": "Break down into smaller, focused functions"
            })

        return issues

    def _analyze_maintainability(self, diff_content: str) -> List[Dict[str, Any]]:
        """Analyze maintainability patterns."""
        issues = []

        # Check for hardcoded values
        hardcoded = re.findall(r"= ['\"]\d{4,}['\"]|= ['\"][a-zA-Z0-9]{20,}['\"]", diff_content)
        if hardcoded:
            issues.append({
                "type": "maintainability",
                    "issue": "Hardcoded values detected",
                        "severity": "low",
                        "recommendation": "Move to configuration files or constants"
            })

        # Check for magic numbers
        magic_numbers = re.findall(r"\b\d{3,}\b", diff_content)
        if magic_numbers:
            issues.append({
                "type": "maintainability",
                    "issue": "Magic numbers detected",
                        "severity": "low",
                        "recommendation": "Define constants for numeric values"
            })

        return issues

    def _analyze_readability(self, diff_content: str) -> List[Dict[str, Any]]:
        """Analyze readability patterns."""
        issues = []

        # Check for long lines
        long_lines = [line for line in diff_content.split('\n') if len(line) > 120]
        if long_lines:
            issues.append({
                "type": "readability",
                    "issue": "Long lines detected",
                        "severity": "low",
                        "recommendation": "Break long lines for better readability"
            })

        # Check for missing comments
        if "def " in diff_content and "#" not in diff_content:
            issues.append({
                "type": "readability",
                    "issue": "Functions without comments",
                        "severity": "low",
                        "recommendation": "Add docstrings to functions"
            })

        return issues

    def _generate_security_recommendations(self, analysis: Dict[str, Any]) -> List[str]:
        """Generate actionable security recommendations."""
        recommendations = []

        if analysis["critical_issues"]:
            recommendations.append("🔴 CRITICAL: Address security vulnerabilities immediately")

        if analysis["high_risk_issues"]:
            recommendations.append("🟠 HIGH: Review and fix security issues before deployment")

        if analysis["overall_risk_score"] > 50:
            recommendations.append("⚠️ Consider security review before merging")

        return recommendations

    def _analyze_file_security(self, file_diffs: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze security patterns by file type."""
        file_analysis = {}

        for filename, file_data in file_diffs.items():
            file_extension = filename.split('.')[-1] if '.' in filename else 'no_extension'

            # Risk assessment by file type
            risk_level = "low"
            if file_extension in ['py', 'js', 'php', 'java']:
                risk_level = "high"
            elif file_extension in ['html', 'xml', 'json']:
                risk_level = "medium"

            file_analysis[filename] = {
                "extension": file_extension,
                    "risk_level": risk_level,
                        "changes": len(file_data.get("additions", [])) + len(file_data.get("deletions", []))
            }

        return file_analysis

    def generate_summary(self, diff_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate summary of changes."""
        total_additions = sum(len(f.get("additions", [])) for f in diff_data.get('file_diffs', {}).values())
        total_deletions = sum(len(f.get("deletions", [])) for f in diff_data.get('file_diffs', {}).values())

        return {
            "total_files_changed": len(diff_data.get('file_diffs', {})),
                "total_additions": total_additions,
                    "total_deletions": total_deletions,
                    "net_change": total_additions - total_deletions,
                    "change_magnitude": "small" if total_additions + total_deletions < 10 else "medium" if total_additions + total_deletions < 50 else "large"
        }

# Global pattern analyzer instance
pattern_analyzer = AdvancedPatternAnalyzer()
