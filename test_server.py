import unittest

import server


class NormalizeKnownSpecMismatchesTest(unittest.TestCase):
    def test_news_rest_id_is_not_required_and_id_is_accepted(self) -> None:
        spec = {
            "components": {
                "schemas": {
                    "News": {
                        "required": ["rest_id"],
                        "properties": {
                            "rest_id": {"type": "string"},
                        },
                    },
                },
            },
        }

        server.normalize_known_spec_mismatches(spec)

        news = spec["components"]["schemas"]["News"]
        self.assertNotIn("required", news)
        self.assertEqual(news["properties"]["id"], {"type": "string"})
        self.assertEqual(news["properties"]["rest_id"], {"type": "string"})

    def test_news_normalization_preserves_other_required_fields(self) -> None:
        spec = {
            "components": {
                "schemas": {
                    "News": {
                        "required": ["rest_id", "name"],
                        "properties": {
                            "id": {"type": "string"},
                            "rest_id": {"type": "string"},
                            "name": {"type": "string"},
                        },
                    },
                },
            },
        }

        server.normalize_known_spec_mismatches(spec)

        news = spec["components"]["schemas"]["News"]
        self.assertEqual(news["required"], ["name"])
        self.assertEqual(news["properties"]["id"], {"type": "string"})


if __name__ == "__main__":
    unittest.main()
