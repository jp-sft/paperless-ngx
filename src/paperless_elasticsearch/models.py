import itertools

from django.conf import settings
from django.urls import reverse
from django_elasticsearch_dsl import Document as ESDocument
from django_elasticsearch_dsl import fields as es_fields
from django_elasticsearch_dsl.registries import registry
from elasticsearch_dsl import analyzer
from elasticsearch_dsl import token_filter

from documents import models as doc_models

ascii_fold = analyzer(
    "ascii_fold",
    # we don't want to split O'Brian or Toulouse-Lautrec
    tokenizer="whitespace",
    filter=["lowercase", token_filter("ascii_fold", "asciifolding")],
)
# Configure search analyzer to have stopwords in French, Arabic and English
french_stop = token_filter(
    "french_stop",
    "stop",
    stopwords="_french_",
    ignore_case=True,
)
arabic_stop = token_filter(
    "arabic_stop",
    "stop",
    stopwords="_arabic_",
    ignore_case=True,
)
english_stop = token_filter(
    "english_stop",
    "stop",
    stopwords="_english_",
    ignore_case=True,
)
html_strip = token_filter("html_strip", "html_strip")
search_analyzer = analyzer(
    "search_analyzer",
    type="custom",
    tokenizer="standard",
    filter=["lowercase", french_stop, arabic_stop, english_stop, html_strip],
)
default_analyzer = analyzer(
    "default_analyzer",
    type="custom",
    tokenizer="standard",
    filter=[
        "lowercase",
    ],
)


@registry.register_document
class Document(ESDocument):

    title = es_fields.TextField(
        attr="title",
        required=False,
        term_vector="with_positions_offsets",
        analyzer=default_analyzer,
        fields={"raw": es_fields.KeywordField()},
    )

    type = es_fields.ObjectField(
        properties={
            "id": es_fields.KeywordField(),
            "name": es_fields.TextField(
                term_vector="with_positions_offsets",
                analyzer=default_analyzer,
                fields={"raw": es_fields.KeywordField()},
            ),
        },
        required=False,
    )

    tags = es_fields.NestedField(
        properties={
            "id": es_fields.KeywordField(),
            "name": es_fields.TextField(
                term_vector="with_positions_offsets",
                analyzer=default_analyzer,
                fields={"raw": es_fields.KeywordField()},
            ),
            "color": es_fields.KeywordField(),
        },
        multi=True,
    )
    text = es_fields.TextField(
        attr="content",
        required=False,
        term_vector="with_positions_offsets",
        analyzer=search_analyzer,
    )
    suggest = es_fields.Completion(analyzer=ascii_fold)
    language = es_fields.KeywordField()
    category = es_fields.TextField(
        term_vector="with_positions_offsets",
        analyzer=default_analyzer,
        fields={"raw": es_fields.KeywordField()},
    )
    # thumbnail_url = es_fields.KeywordField()
    # preview_url = es_fields.KeywordField()
    links = es_fields.ObjectField(
        properties={
            "thumbnail": es_fields.KeywordField(),
            "preview": es_fields.KeywordField(),
            "download": es_fields.KeywordField(),
        },
        required=False,
    )

    class Index:
        name = settings.PAPERLESS_ELASTICSEARCH["index"]

    class Django:
        model = doc_models.Document

        fields = ["created", "filename"]
        related_models = [doc_models.DocumentType, doc_models.Tag]

    def clean(self):
        self.suggest = construct_suggest(self.title, self.popularity)
        return super().clean()

    def get_queryset(self):

        return super().get_queryset()

    def get_instances_from_related(self, related_instance):
        """If related_models is set, define how to retrieve the Car instance(s) from the related model.
        The related_models option should be used with caution because it can lead in the index
        to the updating of a lot of items.
        """
        if isinstance(related_instance, (doc_models.DocumentType, doc_models.Tag)):
            return related_instance.documents.all()

    def prepare_language(self, instance):
        filename = instance.filename
        if not filename:
            return None
        if "fr" in filename.lower():
            return "Français"
        if "ar" in instance.filename.lower():
            return "العربية"
        return "Français"

    def prepare_category(self, instance):
        tags = instance.tags.all()
        # skip first tag
        return [t.name for t in tags[1:]]

    def _thumbnail_url(self, instance):
        url = reverse("document-thumb", kwargs={"pk": instance.pk})
        return url

    def _preview_url(self, instance):
        url = reverse("document-preview", kwargs={"pk": instance.pk})
        return url

    def _download_url(self, instance):
        url = reverse("document-download", kwargs={"pk": instance.pk})
        return url

    def prepare_links(self, instance):
        return {
            "thumbnail": self._thumbnail_url(instance),
            "preview": self._preview_url(instance),
            "download": self._download_url(instance),
        }


def construct_suggest(title, popularity):
    """
    Automatically construct the suggestion input and weight by taking all
    possible permutation of Person's name as ``input`` and taking their
    popularity as ``weight``.
    """

    title = title or ""
    if not popularity:
        popularity = 1
    if title:
        inputs_ = list(
            set(
                itertools.chain.from_iterable(
                    itertools.permutations(title.split(), i)
                    for i in range(min(3, len(title.split())))
                ),
            ),
        )
        return [{"input": " ".join(input_), "weight": popularity} for input_ in inputs_]
    return []
