import os

from paperless.settings import *  # noqa: F403

ELASTICSEARCH_DSL = {
    "default": {
        "hosts": os.environ.get(
            "PAPERLESS_ELASTICSEARCH_HOST",
            "http://localhost:9200",
        ),
        "http_auth": (
            os.environ.get("PAPERLESS_ELASTICSEARCH_USER", "elastic"),
            os.environ.get("PAPERLESS_ELASTICSEARCH_PASSWORD", "changeme"),
        ),
        "ca_certs": os.environ.get("PAPERLESS_ELASTICSEARCH_CA_CERTS", None),
        "ssl_assert_fingerprint": os.environ.get(
            "PAPERLESS_ELASTICSEARCH_CERT_FINGERPRINT",
            None,
        ),
    },
}
ELASTICSEARCH_DSL_AUTOSYNC = True
ELASTICSEARCH_DSL_INDEX_SETTINGS = {}
# ELASTICSEARCH_DSL_SIGNAL_PROCESSOR = (
#     "django_elasticsearch_dsl.signals.CelerySignalProcessor"
# )
ELASTICSEARCH_DSL_PARALLEL = True
PAPERLESS_ELASTICSEARCH = {
    "index": os.environ.get("PAPERLESS_ELASTICSEARCH_INDEX", "paperless"),
}
