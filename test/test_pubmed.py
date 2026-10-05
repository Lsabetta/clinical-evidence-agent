import xml.etree.ElementTree as ET

from clinical_evidence_agent.tools.pubmed import parse_pubmed_article
import pytest
from io import BytesIO
from urllib.parse import parse_qs, urlparse

from clinical_evidence_agent.tools import pubmed
def test_parse_structured_abstract():
    xml = """
    <PubmedArticle>
        <MedlineCitation>
            <PMID>123</PMID>
            <Article>
                <ArticleTitle>Effect of <i>treatment</i> on outcomes.</ArticleTitle>
                <Abstract>
                    <AbstractText Label="BACKGROUND">Study question.</AbstractText>
                    <AbstractText Label="RESULTS">Risk was <b>lower</b>.</AbstractText>
                    <CopyrightInformation>Copyright notice.</CopyrightInformation>
                </Abstract>
            </Article>
        </MedlineCitation>
    </PubmedArticle>
    """

    record = parse_pubmed_article(ET.fromstring(xml))

    assert record.title == "Effect of treatment on outcomes."
    assert record.abstract == (
        "BACKGROUND: Study question.\n\n"
        "RESULTS: Risk was lower."
    )


def test_parse_record_without_optional_metadata():
    xml = """
    <PubmedArticle>
        <MedlineCitation>
            <PMID>123</PMID>
            <Article>
                <ArticleTitle>Example title.</ArticleTitle>
            </Article>
        </MedlineCitation>
    </PubmedArticle>
    """

    record = parse_pubmed_article(ET.fromstring(xml))

    assert record.pmid == "123"
    assert record.url == "https://pubmed.ncbi.nlm.nih.gov/123/"
    assert record.abstract is None
    assert record.pmcid is None
    assert record.journal is None
    assert record.publication_date is None
    assert record.authors == []
    assert record.publication_types == []

@pytest.mark.parametrize(
    ("pmid_xml", "title_xml", "expected_error"),
    [
        ("", "<ArticleTitle>Title.</ArticleTitle>", "Missing or empty PMID"),
        ("<PMID> </PMID>", "<ArticleTitle>Title.</ArticleTitle>",
         "Missing or empty PMID"),
        ("<PMID>123</PMID>", "", "Missing ArticleTitle"),
        ("<PMID>123</PMID>", "<ArticleTitle> </ArticleTitle>",
         "Empty ArticleTitle"),
    ],
    ids=["missing-pmid", "blank-pmid", "missing-title", "blank-title"],
)
def test_rejects_missing_required_content(
    pmid_xml: str,
    title_xml: str,
    expected_error: str,
):
    xml = f"""
    <PubmedArticle>
        <MedlineCitation>
            {pmid_xml}
            <Article>{title_xml}</Article>
        </MedlineCitation>
    </PubmedArticle>
    """

    with pytest.raises(ValueError, match=expected_error):
        parse_pubmed_article(ET.fromstring(xml))

def test_get_records_preserves_order_and_removes_duplicates(monkeypatch):
    response_xml = b"""
    <PubmedArticleSet>
        <PubmedArticle>
            <MedlineCitation>
                <PMID>222</PMID>
                <Article><ArticleTitle>Second article.</ArticleTitle></Article>
            </MedlineCitation>
        </PubmedArticle>
        <PubmedArticle>
            <MedlineCitation>
                <PMID>111</PMID>
                <Article><ArticleTitle>First article.</ArticleTitle></Article>
            </MedlineCitation>
        </PubmedArticle>
    </PubmedArticleSet>
    """

    calls = []

    def fake_urlopen(url, timeout):
        calls.append((url, timeout))
        return BytesIO(response_xml)

    monkeypatch.setattr(pubmed, "urlopen", fake_urlopen)

    records = pubmed.get_pubmed_records(["111", "222", "111"])

    assert [record.pmid for record in records] == ["111", "222"]
    assert [record.title for record in records] == [
        "First article.",
        "Second article.",
    ]

    assert len(calls) == 1
    url, timeout = calls[0]
    params = parse_qs(urlparse(url).query)

    assert params["id"] == ["111,222"]
    assert params["db"] == ["pubmed"]
    assert params["retmode"] == ["xml"]
    assert timeout == 30

def test_get_records_rejects_missing_requested_pmid(monkeypatch):
    response_xml = b"""
    <PubmedArticleSet>
        <PubmedArticle>
            <MedlineCitation>
                <PMID>111</PMID>
                <Article><ArticleTitle>First article.</ArticleTitle></Article>
            </MedlineCitation>
        </PubmedArticle>
    </PubmedArticleSet>
    """

    def fake_urlopen(url, timeout):
        return BytesIO(response_xml)

    monkeypatch.setattr(pubmed, "urlopen", fake_urlopen)

    with pytest.raises(
        ValueError,
        match=r"Requested PMIDs not retrieved: \['222'\]",
    ):
        pubmed.get_pubmed_records(["111", "222"])

@pytest.mark.parametrize(
    ("ids_xml", "expected_pmids"),
    [
        ("<Id>222</Id><Id>111</Id>", ["222", "111"]),
        ("", []),
    ],
    ids=["preserves-result-order", "no-results"],
)
def test_search_pubmed(monkeypatch, ids_xml, expected_pmids):
    response_xml = f"""
    <eSearchResult>
        <Count>{len(expected_pmids)}</Count>
        <IdList>{ids_xml}</IdList>
    </eSearchResult>
    """.encode("utf-8")

    calls = []

    def fake_urlopen(url, timeout):
        calls.append((url, timeout))
        return BytesIO(response_xml)

    monkeypatch.setattr(pubmed, "urlopen", fake_urlopen)

    result = pubmed.search_pubmed(
        "semaglutide AND cardiovascular",
        max_results=3,
    )

    assert result == expected_pmids
    assert len(calls) == 1

    url, timeout = calls[0]
    parsed_url = urlparse(url)

    assert parsed_url.path == "/entrez/eutils/esearch.fcgi"
    assert parse_qs(parsed_url.query) == {
        "db": ["pubmed"],
        "term": ["semaglutide AND cardiovascular"],
        "retmax": ["3"],
        "retmode": ["xml"],
        "sort": ["relevance"],
    }
    assert timeout == 30