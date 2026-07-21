"""Справочник поселенца как база знаний агента — лестница модуля 14 в одном файле.

Loading → Indexing → Querying над локальной папкой knowledge/ (это подрезанные
куски НАСТОЯЩЕЙ вики игры): SimpleDirectoryReader читает .md, SentenceSplitter
режет на Node, HuggingFaceEmbedding считает векторы локально на CPU (без
ключей), VectorStoreIndex держит их в памяти. Chroma из ноутбука здесь не
нужна: корпус крошечный и версионируется git-ом вместе с кодом, пересобрать
индекс на старте (секунды) дешевле, чем возить рядом базу. Правило одного
векторного пространства соблюдено: и куски, и запросы кодирует одна модель.

Эмбеддер НЕ тот, что в ноутбуке, и это осознанно: bge-small-en-v1.5 обучен на
английском и на кириллице слепнет, а справочник и вопросы агента — русские.
Берём multilingual-e5-small (~0.5 ГБ, качается один раз); семейство e5 обучено
с префиксами "query:"/"passage:" — их подставляет сам эмбеддер, см. ниже.

Двери к индексу (лекция: «три двери») — переключатель HANDBOOK_DOOR в .env:

- retriever (дефолт) — инструмент отдаёт агенту top-3 куска справочника
  ДОСЛОВНО, со score и источником. Синтеза нет: агент сам решает, что делать
  с правдой. Быстро (без второго вызова LLM на каждый вопрос) и надёжно —
  слабая локальная модель не перевирает справку пересказом.
- query_engine — классический QueryEngineTool из лекции: внутри инструмента
  куски СНАЧАЛА пересказываются той же локальной моделью, агент получает
  готовый ответ словами. Красиво, но на каждый вопрос — второй LLM-вызов,
  а пересказ слабой 7B — лишняя точка вранья. Включите и сравните сами.

Третья дверь — chat engine — здесь не нужна: память диалога живёт у самого
агента (Context в app.py), справочнику своя не полагается.
"""

import os
from pathlib import Path

from llama_index.core import SimpleDirectoryReader, VectorStoreIndex
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.tools import FunctionTool, QueryEngineTool
from llama_index.embeddings.huggingface import HuggingFaceEmbedding

KNOWLEDGE_DIR = Path(__file__).parent / "knowledge"

# Многоязычный эмбеддер под русский справочник (в ноутбуке — английский
# bge-small-en, тут он не годится). Качается один раз, дальше кэш HF.
EMBED_MODEL_ID = "intfloat/multilingual-e5-small"

# Описание — часть контракта: «дизайн description — это дизайн поведения
# агента» (лекция 14). Одно на обе двери: агенту всё равно, какая механика
# за именем handbook, — в этом и смысл переключателя.
HANDBOOK_DESCRIPTION = (
    "Справочник поселенца Cognopolis: правила мира и карты 7x7, направления и "
    "координаты, добыча и склад (авто-банк на доме), бой и враги, кулдауны и "
    "основные коды ошибок сервера. Зови, когда не уверен в правилах ИГРЫ, а "
    "не угадывай. Чтение, мир не меняет."
)


def build_index() -> VectorStoreIndex:
    """Собрать индекс над knowledge/ — Loading и Indexing из пяти стадий RAG.

    chunk_size=512 — рабочий диапазон из ноутбука (256–512); страницы
    справочника короткие, крошить мельче незачем."""
    documents = SimpleDirectoryReader(str(KNOWLEDGE_DIR)).load_data()
    embed_model = HuggingFaceEmbedding(
        model_name=EMBED_MODEL_ID,
        device="cpu",
        # Семейство e5 обучено с этими префиксами: вопрос и документ кодируются
        # чуть по-разному. Без них качество поиска заметно проседает.
        query_instruction="query:",
        text_instruction="passage:",
    )
    return VectorStoreIndex.from_documents(
        documents,
        embed_model=embed_model,
        transformations=[SentenceSplitter(chunk_size=512, chunk_overlap=50)],
    )


def search(index: VectorStoreIndex, query: str, top_k: int = 3) -> str:
    """Дверь-retriever для ЧЕЛОВЕКА (боковая панель): top-k кусков со score.

    Работает целиком без LLM — главный keyless-момент модуля: поиск по смыслу
    бесплатен и офлайн, платный только синтез."""
    query = (query or "").strip()
    if not query:
        return "Введите вопрос — например: «как сдать ресурсы на склад?»"
    hits = index.as_retriever(similarity_top_k=top_k).retrieve(query)
    if not hits:
        return "Ничего не нашлось."
    parts = []
    for n in hits:
        source = n.node.metadata.get("file_name", "?")
        text = n.node.get_content().strip()
        parts.append(f"**{source}** · score {n.score:.3f}\n\n{text}")
    return "\n\n---\n\n".join(parts)


def build_handbook_tool(index: VectorStoreIndex, llm):
    """Инструмент «справочник» для агента — какая дверь, решает HANDBOOK_DOOR."""
    door = os.getenv("HANDBOOK_DOOR", "retriever").strip().lower()

    if door == "query_engine":
        # Дверь 2 из лекции: QueryEngineTool за три строки. Внутри каждого
        # вызова — retrieval + синтез тем же локальным LLM (response_mode
        # compact — дефолт; в ноутбуке сравниваются и другие).
        return QueryEngineTool.from_defaults(
            query_engine=index.as_query_engine(llm=llm, similarity_top_k=3),
            name="handbook",
            description=HANDBOOK_DESCRIPTION,
        )

    # Дверь 1 (дефолт): retriever как FunctionTool. Тот же «паспорт» — имя,
    # description, схема из сигнатуры; агент снаружи разницы не видит.
    def handbook(query: str) -> str:
        """—"""  # настоящий description ниже, единый для обеих дверей
        hits = index.as_retriever(similarity_top_k=3).retrieve(query)
        chunks = []
        for n in hits:
            source = n.node.metadata.get("file_name", "?")
            chunks.append(f"[{source}] {n.node.get_content().strip()}")
        return "\n\n".join(chunks) or "В справочнике ничего не нашлось."

    return FunctionTool.from_defaults(
        handbook, name="handbook", description=HANDBOOK_DESCRIPTION
    )
