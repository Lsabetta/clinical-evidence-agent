import xml.etree.ElementTree as ET
from clinical_evidence_agent.schemas import PubMedRecord
from urllib.parse import urlencode
from urllib.request import urlopen

def parse_pubmed_article(
    pubmed_article: ET.Element,
) -> PubMedRecord:
    """Normalize one PubmedArticle XML element."""


    citation = pubmed_article.find("MedlineCitation")
    if citation is None:
        raise ValueError("Missing MedlineCitation")
#######################

    article = citation.find("Article")
    if article is None:
        raise ValueError("Missing Article")
#######################

    title_element = article.find("ArticleTitle")
    if title_element is None:
        raise ValueError("Missing ArticleTitle")
    title = "".join(title_element.itertext()).strip()
#######################

    journal = None
    journal_element = article.find("Journal/Title")
    if journal_element is not None:
        text = "".join(journal_element.itertext()).strip()
        if text:
            journal = text
#######################

    publication_types = []
    for element in article.findall("PublicationTypeList/PublicationType"):
        text = "".join(element.itertext()).strip()
        if text:
            publication_types.append(text)
#######################

    abstract_parts = []
    for element in article.findall("Abstract/AbstractText"):
        text = "".join(element.itertext()).strip()
        if not text:
            continue
        label = element.get("Label")
        if label:
            text = f"{label}: {text}"
        abstract_parts.append(text)
    abstract = "\n\n".join(abstract_parts) or None
#######################

    authors = []
    for author in article.findall("AuthorList/Author"):
        collective_name = author.findtext("CollectiveName")
        if collective_name:
            name = collective_name.strip()
        else:
            first_name = (
                author.findtext("ForeName")
                or author.findtext("Initials")
                or ""
            )
            last_name = author.findtext("LastName") or ""
            name = f"{first_name} {last_name}".strip()
        if name:
            authors.append(name)
#######################

    publication_date = None
    pub_date = article.find("Journal/JournalIssue/PubDate")
    if pub_date is not None:
        medline_date = pub_date.findtext("MedlineDate")

        if medline_date and medline_date.strip():
            publication_date = medline_date.strip()
        else:
            date_parts = []

            for field in ("Year", "Month", "Day", "Season"):
                value = pub_date.findtext(field)
                if value and value.strip():
                    date_parts.append(value.strip())
            publication_date = " ".join(date_parts) or None
#######################

    pmid = (citation.findtext("PMID") or "").strip()
    if not pmid:
        raise ValueError("Missing or empty PMID")

    if not title:
        raise ValueError("Empty ArticleTitle")
#######################

    pmcid = pubmed_article.findtext(
        "PubmedData/ArticleIdList/ArticleId[@IdType='pmc']"
    )
    if pmcid is not None:
        pmcid = pmcid.strip() or None

    record = PubMedRecord(
        pmid=pmid,
        pmcid=pmcid,
        title=title,
        url=f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
        abstract=abstract,
        authors=authors,
        journal=journal,
        publication_date=publication_date,
        publication_types=publication_types,
    )

    return record

def get_pubmed_records(pmids: list[str]) -> list[PubMedRecord]:
    if not pmids:
        return []

    for pmid in pmids:
        if not pmid.isascii() or not pmid.isdecimal():
            raise ValueError(f"Invalid PMID: {pmid!r}")

    # Remove duplicates while preserving input order.
    unique_pmids = list(dict.fromkeys(pmids))

    params = urlencode({
        "db": "pubmed",
        "id": ",".join(unique_pmids),
        "retmode": "xml",
    })
    url = (
        "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
        f"?{params}"
    )

    with urlopen(url, timeout=30) as response:
        root = ET.fromstring(response.read())

    error = root.find(".//ERROR")
    if error is not None:
        message = "".join(error.itertext()).strip()
        raise ValueError(f"PubMed returned an error: {message}")

    if root.tag != "PubmedArticleSet":
        raise ValueError(f"Unexpected XML root: {root.tag}")

    records_by_pmid = {}

    for element in root.findall("PubmedArticle"):
        record = parse_pubmed_article(element)
        records_by_pmid[record.pmid] = record

    missing = [
        pmid for pmid in unique_pmids
        if pmid not in records_by_pmid
    ]
    if missing:
        raise ValueError(f"Requested PMIDs not retrieved: {missing}")

    return [records_by_pmid[pmid] for pmid in unique_pmids]

def search_pubmed(
    query: str,
    max_results: int = 10,
) -> list[str]:
    query = query.strip()
    if not query:
        raise ValueError("Query must be non-empty.")

    if isinstance(max_results, bool) or not isinstance(max_results, int):
        raise ValueError("max_results must be an integer.")
    if max_results <= 0:
        raise ValueError("max_results must be positive.")

    params = urlencode({
        "db": "pubmed",
        "term": query,
        "retmax": max_results,
        "retmode": "xml",
        "sort": "relevance",
        # "sort": "pub_date",
        
    })
    url = (
        "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
        f"?{params}"
    )

    # with urlopen(url, timeout=30) as response:
    #     root = ET.fromstring(response.read())
    # print("Request URL:", url)

    with urlopen(url, timeout=30) as response:
        raw_xml = response.read()

    # print("Raw response:", raw_xml.decode("utf-8"))
    root = ET.fromstring(raw_xml)

    for tag in ("WarningList", "ErrorList"):
        element = root.find(tag)
        if element is not None:
            print(tag, ET.tostring(element, encoding="unicode"))
    error = root.find(".//ERROR")
    if error is not None:
        message = "".join(error.itertext()).strip()
        raise ValueError(f"PubMed returned an error: {message}")

    if root.tag != "eSearchResult":
        raise ValueError(f"Unexpected XML root: {root.tag}")

    id_list = root.find("IdList")
    if id_list is None:
        raise ValueError("Missing IdList in PubMed search response.")

    pmids = []

    for element in id_list.findall("Id"):
        pmid = (element.text or "").strip()
        if not pmid.isascii() or not pmid.isdecimal():
            raise ValueError(f"Invalid PMID in search response: {pmid!r}")
        pmids.append(pmid)

    return pmids