from core.memory_vector import MemoryVectorStore


def test_basic_similarity():
    store = MemoryVectorStore()
    texts = [
        "abrir youtube",
        "salvar arquivo",
        "tocar música no spotify",
    ]
    ids = store.index_texts(texts)

    # query semelhante a "abrir youtube"
    res = store.query_similar("abrir youtube", k=1)
    assert len(res) == 1
    _id, score, text = res[0]
    assert _id in ids
    assert text == "abrir youtube"
    assert score > 0.0
