import pytest
from monoco.features.issue.core import parse_search_query, check_issue_match
from monoco.features.issue.models import IssueMetadata, IssueType, IssueStatus

class TestQueryParser:
    def test_basic_implicit_terms(self):
        """Test simple terms without prefixes (Nice to have)"""
        pos, terms, negs = parse_search_query("login bug")
        assert pos == []
        assert terms == ["login", "bug"]
        assert negs == []

    def test_explicit_positives(self):
        """Test +term syntax (Must include)"""
        pos, terms, negs = parse_search_query("+auth +api")
        assert pos == ["auth", "api"]
        assert terms == []
        assert negs == []

    def test_explicit_negatives(self):
        """Test -term syntax (Must NOT include)"""
        pos, terms, negs = parse_search_query("-docs -ui")
        assert pos == []
        assert terms == []
        assert negs == ["docs", "ui"]

    def test_mixed_query(self):
        """Test mixed syntax"""
        # +critical -wontfix login
        pos, terms, negs = parse_search_query("+critical -wontfix login")
        assert pos == ["critical"]
        assert terms == ["login"]
        assert negs == ["wontfix"]
    
    def test_quoted_phrases(self):
        """Test quoted phrases"""
        # "access denied" -"unit test" +core
        pos, terms, negs = parse_search_query('"access denied" -"unit test" +core')
        assert pos == ["core"]
        assert terms == ["access denied"]
        assert negs == ["unit test"]

    def test_complex_quotes(self):
        """Test quotes with prefixes inside/outside"""
        # We support +term, -term. What about +"phrase"?
        # Current shlex logic splits: '+"foo bar"' -> ['+foo bar']? NO.
        # shlex.split('+"foo bar"') -> ['+foo bar']
        # check_issue_match logic: startswith("+") -> len > 1 -> strip 1.
        
        pos, terms, negs = parse_search_query('+"critical error" -"minor bug"')
        assert pos == ["critical error"]
        assert negs == ["minor bug"]
        assert terms == []


class TestIssueMatcher:
    @pytest.fixture
    def mock_issue(self):
        return IssueMetadata(
            id="FEAT-001",
            type=IssueType.FEATURE,
            status=IssueStatus.OPEN,
            title="Implement User Login System",
            tags=["auth", "security", "high-priority"]
        )

    def test_match_simple_term(self, mock_issue):
        """Implicit OR: Should match if term exists"""
        assert check_issue_match(mock_issue, [], ["login"], []) is True
        assert check_issue_match(mock_issue, [], ["logout"], []) is False # No match
        
    def test_match_multiple_terms_or_logic(self, mock_issue):
        """Implicit OR: 'login logout' -> matches login"""
        # If no explicit positives, terms are implicit OR.
        assert check_issue_match(mock_issue, [], ["login", "logout"], []) is True
        assert check_issue_match(mock_issue, [], ["logout", "payment"], []) is False

    def test_match_explicit_positive(self, mock_issue):
        """Must Include logic"""
        assert check_issue_match(mock_issue, ["auth"], [], []) is True
        assert check_issue_match(mock_issue, ["payment"], [], []) is False
        
    def test_match_explicit_negative(self, mock_issue):
        """Must Not Include logic"""
        assert check_issue_match(mock_issue, [], [], ["docs"]) is True
        assert check_issue_match(mock_issue, [], [], ["auth"]) is False # Exclude tag

    def test_match_mixed_logic(self, mock_issue):
        """Mixed logic: +auth -docs login"""
        # Should match: Has 'auth', No 'docs'. 'login' is optional nice-to-have.
        assert check_issue_match(mock_issue, ["auth"], ["login"], ["docs"]) is True
        
        # Even if 'login' is missing, it should match because +auth is present!
        # Rule: If explicit positives exist, terms are optional.
        assert check_issue_match(mock_issue, ["auth"], ["missing_term"], ["docs"]) is True

    def test_match_phrase(self, mock_issue):
        """Exact phrase matching"""
        # Title: "Implement User Login System"
        assert check_issue_match(mock_issue, [], ["user login"], []) is True
        assert check_issue_match(mock_issue, [], ["login user"], []) is False # Order matters in blob? 
        # Actually our implementation joins fields with space.
        # "Implement User Login System" -> blob has "user login".
        
    def test_all_fields_search(self, mock_issue):
        """Search across ID, Status, Tags"""
        assert check_issue_match(mock_issue, [], ["feat-001"], []) is True # ID
        assert check_issue_match(mock_issue, [], ["open"], []) is True # Status
        assert check_issue_match(mock_issue, [], ["security"], []) is True # Tag
