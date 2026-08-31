"""Unit tests for ClauseNode / DocumentEnvelope serialization."""

from models.clause import CharSpan, ClauseNode, DocumentEnvelope, LlmClaim


def test_clause_node_round_trip():
    child = ClauseNode(
        clause_id="1.1",
        text="Child text",
        char_span=CharSpan(10, 20),
        page=1,
        confidence="high",
    )
    root = ClauseNode(
        clause_id="1",
        text="Parent text",
        char_span=CharSpan(0, 11),
        masked_text="[ORG_1] text",
        category="Confidentiality",
        page=1,
        children=[child],
        llm_claims=[
            LlmClaim(
                quoted_text="Child text",
                clause_id="1.1",
                explanation="example",
            )
        ],
    )
    data = root.to_dict()
    restored = ClauseNode.from_dict(data)
    assert restored.clause_id == "1"
    assert restored.masked_text == "[ORG_1] text"
    assert restored.children[0].text == "Child text"
    assert restored.children[0].char_span.start == 10
    assert restored.llm_claims[0].quoted_text == "Child text"
    assert restored.to_dict() == data


def test_document_envelope_round_trip():
    tree = ClauseNode(
        clause_id="root",
        text="",
        char_span=CharSpan(0, 0),
        children=[
            ClauseNode(
                clause_id="1",
                text="Hello world",
                char_span=CharSpan(0, 11),
            )
        ],
    )
    env = DocumentEnvelope(
        doc_id="abc123",
        filename="demo.docx",
        full_text="Hello world",
        tree=tree,
        entity_map={"[ORG_1]": "Acme"},
        parser_mode="layout",
        role="Client",
    )
    data = env.to_dict()
    restored = DocumentEnvelope.from_dict(data)
    assert restored.doc_id == "abc123"
    assert restored.entity_map["[ORG_1]"] == "Acme"
    assert restored.span_text(restored.tree.children[0]) == "Hello world"
    assert restored.to_dict() == data


def test_iter_nodes_flattens():
    root = ClauseNode(
        clause_id="root",
        text="",
        char_span=CharSpan(0, 0),
        children=[
            ClauseNode(
                clause_id="1",
                text="A",
                char_span=CharSpan(0, 1),
                children=[
                    ClauseNode(
                        clause_id="1.1",
                        text="B",
                        char_span=CharSpan(2, 3),
                    )
                ],
            )
        ],
    )
    ids = [n.clause_id for n in root.iter_nodes()]
    assert ids == ["root", "1", "1.1"]
