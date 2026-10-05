# Strategia di progetto — Agentic AI per Clinical Evidence Research

**Scopo del documento:** questa è la fonte guida del progetto. Va usata come piano operativo e come riferimento per le decisioni future. L'obiettivo non è costruire il sistema agentico più complesso possibile, ma imparare in modo solido i concetti degli agenti LLM e produrre un progetto GitHub credibile per ruoli **Applied Scientist / Research Scientist / ML Scientist** in healthcare, biotech, pharma e agentic AI.

**Profilo di partenza:** forte background in ML e ricerca quantitativa; Python/PyTorch/Transformers già noti; poca o nessuna esperienza pratica con agenti LLM. Il progetto deve quindi concentrare l'apprendimento su tool calling, orchestration, state, reliability ed evaluation, non su nozioni ML di base.

---

## 1. Obiettivo finale

Costruire un **Clinical Evidence Agent** che riceva una domanda biomedica in linguaggio naturale e produca una risposta strutturata basata su evidenza recuperata da fonti pubbliche, con citazioni verificabili e una fase esplicita di controllo.

Esempio di input:

> What evidence exists for GLP-1 receptor agonists in patients with obesity and cardiovascular disease?

Output atteso:

- sintesi breve;
- studi/paper rilevanti;
- separazione tra evidenza osservazionale, trial e review quando possibile;
- riferimenti PubMed/ClinicalTrials.gov;
- indicazione di eventuali affermazioni non supportate;
- metriche interne sul processo: numero di tool call, latenza, costo/token usage, eventuali retry.

**Il sistema non deve fornire consiglio medico individuale.** È un sistema di ricerca dell'evidenza, non un clinical decision support system.

---

## 2. Perché questo progetto

Il progetto deve massimizzare contemporaneamente quattro obiettivi:

1. **Imparare gli agenti dalle fondamenta**, evitando di nascondere subito la logica dentro framework ad alto livello.
2. **Essere coerente con un profilo di ricerca ML**, con enfasi su benchmark, evaluation, error analysis e ablation.
3. **Aggiungere una credibile componente healthcare/biomedicale** al portfolio senza richiedere accesso a dati clinici sensibili.
4. **Produrre materiale spendibile nei colloqui**, mostrando di saper distinguere tra LLM semplice, retrieval deterministico, RAG, workflow deterministico e agente.

---

## 3. Principio architetturale

Il progetto va sviluppato per versioni successive. Ogni versione deve essere funzionante e misurabile prima di procedere.

```text
V0A  Baseline LLM-only
         ↓
V0B  Fixed one-shot PubMed retrieval + synthesis
         ↓
V1   LLM + function/tool calling, loop scritto manualmente
         ↓
V2   Retrieval iterativo + workflow stateful con LangGraph
         ↓
V3   Verifier + evaluation framework
         ↓
V4   Estensione opzionale: ClinicalTrials.gov / synthetic FHIR / multi-agent
```

La baseline **V0B** permette di valutare se l'agency aggiunga valore
rispetto a un workflow non-agentico: una chiamata LLM genera la query,
l'applicazione esegue una sola ricerca PubMed e recupera fino a top-k
record, quindi una seconda chiamata LLM sintetizza l'evidenza.

La sequenza è fissata dal codice. Il modello non decide se ripetere
la ricerca o quando fermarsi. Questo non garantisce risultati identici
fra esecuzioni. La decisione è descritta in ADR-006.

**Regola:** non introdurre multi-agent prima che V3 sia stabile. Il multi-agent è un'estensione sperimentale, non il cuore del progetto.

---

## 4. Stack tecnico raccomandato

### Core

- Python 3.12+
- `uv` o Poetry per dependency management
- Pydantic per schemi e structured outputs
- pytest
- Docker
- pre-commit / Ruff

### LLM layer

Per la prima implementazione usare un provider con function/tool calling e structured outputs. Il codice deve isolare il provider dietro una piccola interfaccia, per poter cambiare modello senza riscrivere la logica.

### Agent orchestration

- **Prima:** loop manuale Python per capire il meccanismo.
- **Poi:** LangGraph per state, graph routing, retry e checkpointing.
- **Opzionale in una fase successiva:** OpenAI Agents SDK come confronto architetturale, non come prerequisito.

### Data sources

**MVP:** PubMed tramite NCBI E-utilities.

**Estensione:** ClinicalTrials.gov API v2.

**Estensione healthcare data:** Synthea per record paziente sintetici in HL7 FHIR, solamente dopo il completamento del core project.

---

## 5. Scope dell'MVP

L'MVP deve usare solo **PubMed**.

Tool iniziali:

```python
search_pubmed(query: str, max_results: int = 10)
get_pubmed_record(pmid: str)
get_pubmed_records(pmids: list[str])
```

Ogni record normalizzato deve contenere almeno:

```text
pmid
title
abstract
authors
journal
publication_date
publication_types
url
```

Dalla fase V1, il modello deve poter decidere:

- quale query PubMed eseguire;
- se la query va riformulata;
- quali risultati leggere in dettaglio;
- quando dispone di evidenza sufficiente per produrre una risposta.

Vincolo iniziale del loop agentico, dalla fase V1: massimo 6 tool call
per richiesta, per evitare loop incontrollati.
V0B mantiene una sola ricerca e un recupero batch.

### Vincolo sulla disponibilità dell'evidenza

Salvo quando il full text è esplicitamente disponibile e recuperato dal sistema, grounding e verification devono essere eseguiti **solo rispetto ai metadata e agli abstract effettivamente recuperati**.

Il sistema non deve affermare che un claim è verificato dal paper completo se ha accesso soltanto all'abstract. Nei risultati e nell'evaluation va mantenuta esplicita la distinzione tra:

- claim supportato dall'abstract/metadata disponibile;
- claim supportato da full text effettivamente disponibile;
- claim non verificabile con l'evidenza recuperata.

---

## 6. Roadmap concreta

### Fase 0 — Setup + baseline LLM-only | 2–3 ore

**Obiettivo:** repository pulito e prima baseline non-agentica.

Task:

- creare repository;
- configurare ambiente Python, lint, test, `.env.example`;
- definire un `EvidenceAnswer` Pydantic model;
- implementare `question -> LLM -> structured answer` senza retrieval;
- salvare prompt, output, latenza e token usage.

**Definition of Done:** una CLI accetta una domanda e produce JSON valido secondo lo schema.

**Cosa imparare:** structured outputs, schema validation, separazione tra model layer e application layer.

---

### Fase 1 — PubMed baseline + primo vero agente | 1 settimana

**Obiettivo:** costruire prima una baseline one-shot a flusso fisso e poi capire il loop agentico senza framework.

#### 1A — Fixed one-shot PubMed retrieval + synthesis

Implementare:

```text
user question
    ↓
one-shot LLM PubMed query generation
    ↓
single PubMed search
    ↓
retrieve top-k records
    ↓
LLM synthesis over retrieved evidence
```

La query viene generata con un prompt versionato e una configurazione
fissata. Non sono previsti riformulazione dopo il retrieval, retry,
reranking o loop agentici.

Conservare nei log la query effettiva e tutti i record forniti alla
sintesi. Mantenere la domanda originale come query quale comparatore
minimo separato.

Nel confronto con V1, condividere i componenti di query generation e
sintesi dove applicabile, documentando differenze di modello e budget
di retrieval, per evitare di attribuire all'agency miglioramenti dovuti
ad altri cambiamenti.

Task:

- wrapper PubMed E-utilities;
- normalizzazione dei record;
- baseline one-shot con ricerca singola;
- logging di query, PMIDs recuperati, latenza e token usage;
- mantenere questa pipeline come baseline permanente per le fasi successive.

**Definition of Done:** la stessa domanda produce una ricerca PubMed one-shot, recupera un insieme di record e genera una risposta strutturata basata solo sull'evidenza recuperata.

#### 1B — Tool calling manuale

Implementare manualmente:

```text
user question
    ↓
LLM chooses action
    ↓
Python dispatches tool
    ↓
tool result appended to state
    ↓
LLM chooses next action
    ↓
... until final answer / max steps
```

Task:

- definizione di 2–3 tool con schema esplicito;
- dispatcher Python;
- loop massimo di N step;
- logging completo delle decisioni;
- gestione di errori HTTP, result set vuoti e malformed tool arguments;
- almeno 10 test manuali;
- confronto qualitativo iniziale con la baseline one-shot.

**Definition of Done:** il modello riesce a cercare e leggere PubMed autonomamente prima di rispondere, senza LangGraph, e la baseline one-shot a flusso fisso resta disponibile per confronto.

**Deliverable importante:** file `docs/agent_loop.md` che spiega in parole proprie cosa rende questo sistema un agente, quali decisioni sono delegate al modello e quali failure mode sono state osservate.

---

### Fase 2 — Retrieval iterativo + LangGraph | 1 settimana

**Obiettivo:** trasformare il prototipo in un workflow esplicito e osservabile.

Stato minimo del graph:

```python
question
messages
search_queries
candidate_pmids
evidence
answer
verification
step_count
```

Nodi suggeriti:

```text
plan/search
    ↓
retrieve
    ↓
select evidence
    ↓
draft answer
```

Routing condizionale:

- nessun risultato -> reformulate query;
- evidenza insufficiente -> altra ricerca;
- step limit raggiunto -> risposta con limitation esplicita;
- evidenza sufficiente -> draft.

Task:

- ricostruire il loop con `StateGraph`;
- rendere lo state serializzabile;
- introdurre retry controllati;
- aggiungere tracing/logging per ogni nodo;
- confrontare output e complessità con la Fase 1.

**Definition of Done:** il graph è riproducibile, ogni transizione è interpretabile e non esistono loop infiniti.

---

### Fase 3 — Verifier + evaluation | 1–2 settimane

**Obiettivo:** rendere il progetto da portfolio di ricerca, non una semplice demo LLM.

Aggiungere un nodo `verify` che controlli ogni claim importante rispetto all'evidenza effettivamente recuperata.

Output del verifier:

```text
claim
supporting_pmids
support_status = supported | partially_supported | unsupported
evidence_scope = metadata | abstract | full_text
notes
```

Se esistono claim non supportati:

```text
verify
  ├── pass -> final
  └── fail -> revise -> verify
```

Massimo un ciclo di revisione nell'MVP.

#### Dataset di evaluation

Creare inizialmente 30 domande, poi portarle a 50–100.

Dividere le domande in categorie:

- semplice retrieval fattuale;
- confronto tra interventi;
- domanda che richiede più paper;
- domanda volutamente ambigua;
- domanda con evidenza scarsa;
- domanda fuori scope.

Per un sottoinsieme di almeno 20 domande, creare annotazioni manuali minime:

- PMIDs rilevanti o set di riferimento;
- 2–5 claim attesi;
- risposta accettabile / non accettabile.

#### Metriche obbligatorie

**Retrieval**

- Precision@k
- Recall@k sul sottoinsieme annotato

**Answer quality / grounding**

- citation precision: quota di citazioni che supportano realmente il claim rispetto all'evidenza disponibile;
- claim support rate: quota di claim supportati;
- unsupported claim rate;
- completeness score manuale o rubric-based.

**Agent behavior**

- task success rate;
- average tool calls;
- failed tool calls;
- retry rate;
- latency;
- token usage / estimated cost.

**Definition of Done:** esiste uno script `evaluate.py` che esegue il benchmark e produce almeno un CSV/JSON con metriche aggregate e per domanda.

---

### Fase 4 — Ablation study | 3–5 giorni

**Obiettivo:** dimostrare approccio scientifico.

Confrontare almeno:

```text
A. LLM-only
B. fixed one-shot PubMed retrieval + synthesis
C. agentic search + retrieval
D. agentic search + verifier
```

Domanda centrale del progetto:

> L'agency migliora effettivamente la qualità dell'evidenza e la groundedness abbastanza da giustificare costo e complessità aggiuntivi rispetto a una pipeline one-shot a flusso fisso?

Produrre una tabella con:

- success rate;
- citation precision;
- unsupported claim rate;
- latency;
- token/tool cost.

**Questa comparazione è uno dei principali elementi da mostrare a colloquio.**

---

### Fase 5 — Portfolio polish | 3–5 giorni

**Obiettivo:** rendere il repository valutabile in 5 minuti da un hiring manager.

README con:

1. problema;
2. architettura;
3. diagramma del workflow;
4. esempio input/output;
5. risultati dell'evaluation;
6. principali failure mode;
7. istruzioni di esecuzione;
8. disclaimer sanitario;
9. roadmap.

Aggiungere:

- Dockerfile;
- `make demo` o comando equivalente;
- test unitari sui tool;
- sample traces senza dati sensibili;
- screenshot/diagramma architetturale;
- notebook o report di evaluation solo se realmente utile.

Una UI Streamlit/Gradio è **opzionale** e va fatta solo dopo evaluation e README.

---

## 7. Estensioni da fare solo dopo l'MVP

### A. ClinicalTrials.gov

Aggiungere tool:

```text
search_trials(condition, intervention, status)
get_trial(nct_id)
```

Il sistema deve distinguere tra letteratura pubblicata e trial registrati.

### B. Synthetic EHR / FHIR con Synthea

Obiettivo: dimostrare familiarità con dati sanitari strutturati senza usare patient data reali.

Possibile task:

> Given a synthetic FHIR patient record, identify relevant conditions/medications and construct an evidence-search query; retrieve literature; return an evidence summary.

Questa estensione crea un ponte molto forte tra **health data + LLM agents + evidence retrieval**.

### C. Multi-agent

Solo come esperimento di ablation:

```text
Research Agent
     ↓
Synthesis Agent
     ↓
Verification Agent
```

Confrontarlo contro un singolo agent/workflow. Se non migliora le metriche, documentare il risultato invece di mantenerlo solo perché “multi-agent” suona più avanzato.

### D. Human-in-the-loop

Aggiungere un checkpoint prima della risposta finale per approvare/modificare le fonti selezionate. Utile per ragionare su sistemi ad alto rischio.

---

## 8. Struttura repository suggerita

```text
clinical-evidence-agent/
├── README.md
├── pyproject.toml
├── Dockerfile
├── .env.example
├── src/
│   └── clinical_evidence_agent/
│       ├── __init__.py
│       ├── config.py
│       ├── schemas.py
│       ├── llm.py
│       ├── tools/
│       │   ├── pubmed.py
│       │   └── clinical_trials.py        # fase successiva
│       ├── agent/
│       │   ├── manual_loop.py
│       │   ├── state.py
│       │   ├── graph.py
│       │   └── prompts.py
│       ├── evaluation/
│       │   ├── metrics.py
│       │   ├── evaluator.py
│       │   └── datasets.py
│       └── cli.py
├── tests/
│   ├── test_pubmed.py
│   ├── test_schemas.py
│   └── test_agent.py
├── eval/
│   ├── questions.jsonl
│   ├── annotations.jsonl
│   └── results/
└── docs/
    ├── architecture.md
    ├── agent_loop.md
    └── failure_analysis.md
```

---

## 9. Regole di scope control

Queste regole sono vincolanti fino al completamento della Fase 3.

- Non usare CrewAI/AutoGen/altro framework multi-agent.
- Non costruire una UI prima delle metriche.
- Non introdurre un vector database nell'MVP se PubMed search è sufficiente.
- Non fare fine-tuning.
- Non usare dati clinici reali.
- Non costruire memoria long-term utente.
- Non cercare di simulare un medico.
- Non aggiungere dieci tool: 2–4 tool ben progettati sono sufficienti.
- Non ottimizzare il prompt prima di avere casi di test ed errori misurabili.
- Non chiamare “RAG” una semplice ricerca PubMed one-shot a meno che l'architettura implementata corrisponda effettivamente a una pipeline RAG.

---

## 10. Failure modes da studiare esplicitamente

Il progetto deve documentare almeno questi comportamenti:

- query PubMed troppo generica;
- query troppo specifica con zero risultati;
- modello che legge solo il primo risultato;
- selezione di paper non pertinenti;
- citazione corretta ma claim più forte dell'abstract;
- inferenza presentata come se derivasse dal full text non disponibile;
- claim senza supporto;
- loop di ricerca inutile;
- tool call ridondanti;
- uso eccessivo di review quando servirebbero primary studies;
- output che confonde absence of evidence con evidence of absence;
- errore nel distinguere trial registrato da risultato pubblicato.

Per ciascuno: esempio, causa ipotizzata, possibile mitigation, effetto sulle metriche.

---

## 11. Criteri di successo del progetto

Il progetto è pronto per GitHub/CV quando soddisfa tutti i seguenti criteri:

- baseline LLM-only conservata;
- baseline PubMed one-shot a flusso fisso conservata;
- agente con tool calling funzionante;
- implementazione manuale del loop conservata e spiegata;
- versione LangGraph funzionante;
- output strutturato con fonti verificabili;
- verifier implementato;
- distinzione esplicita tra supporto da abstract/metadata e full text;
- benchmark di almeno 30 domande;
- confronto con almeno due baseline;
- metriche di qualità e di costo;
- failure analysis scritta;
- test automatici;
- README con risultati concreti;
- nessuna dipendenza da dati clinici privati.

---

## 12. Obiettivo di apprendimento

Alla fine del progetto bisogna essere in grado di spiegare senza buzzword:

- che cos'è un agent loop;
- differenza tra tool calling e agent;
- differenza tra retrieval one-shot, RAG e agentic retrieval;
- quando scegliere un workflow deterministico;
- ruolo dello state;
- routing condizionale;
- retry e termination conditions;
- structured outputs;
- tracing;
- evaluation di retrieval, tool use e groundedness;
- differenza tra single-agent e multi-agent;
- perché maggiore agency aumenta anche superficie di errore, costo e non-determinismo;
- pperché una baseline non-agentica è necessaria per valutare se l’agency aggiunge davvero valore».
