import unittest
from datetime import timedelta

from eve.utils import config

from eve_mongoengine import get_utc_time
from tests import (
    BaseTest,
    HawkeyDoc,
)


class TestHttpPost(BaseTest, unittest.TestCase):
    def test_post_with_pre_save_hook(self):
        self.__class__.app.config.update(
            {
                "LAST_UPDATED": "updated_at",
                "DATE_CREATED": "created_at",
            }
        )
        self.__class__.ext.last_updated = "updated_at"
        self.__class__.ext.date_created = "created_at"
        self.__class__.ext.add_model(
            HawkeyDoc,
            resource_methods=["GET", "POST", "DELETE"],
            item_methods=["GET", "PATCH", "PUT", "DELETE"],
        )
        # resulting etag has to match (etag must be computed from
        # modified data, not from original!)
        HawkeyDoc.objects.delete()
        data = {"a": "hey"}
        response = self.client.post(
            "/hawkeydoc/", data='{"a": "hey"}', content_type="application/json"
        )
        self.assertEqual(response.status_code, 201)
        resp_json = response.get_json()
        self.assertEqual(resp_json[config.STATUS], "OK")
        etag = resp_json[config.ETAG]

        # verify etag
        resp = self.client.get("/hawkeydoc/%s" % resp_json["_id"])
        self.assertEqual(etag, resp.get_json()[config.ETAG])

        HawkeyDoc(a="a").save()
        queryset = HawkeyDoc.objects()
        for document in queryset:
            self.assertNotEqual(document.created_at, None)

        # test bulk insert no signal
        docs = HawkeyDoc.objects.insert([HawkeyDoc(a="a")])
        for document in docs:
            self.assertEqual(document.created_at, None)

        # cleanup
        HawkeyDoc.objects.delete()

    def test_client_supplied_dates(self):
        yesterday = get_utc_time() - timedelta(days=1)
        doc = HawkeyDoc(a="hello", created_at=yesterday, updated_at=yesterday).save(
            validate=False
        )
        self.assertEqual(doc.updated_at, yesterday)
