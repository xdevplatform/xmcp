import os

import pytest

from server import (
    collect_comma_params,
    filter_openapi_spec,
    is_truthy,
    parse_csv_env,
    should_exclude_operation,
    should_join_query_param,
)


class TestIsTruthy:
    @pytest.mark.parametrize("value", ["1", "true", "yes", "on", "TRUE", "Yes", " on "])
    def test_truthy_values(self, value):
        assert is_truthy(value) is True

    @pytest.mark.parametrize("value", ["0", "false", "no", "off", "", " ", "maybe"])
    def test_falsy_values(self, value):
        assert is_truthy(value) is False

    def test_none(self):
        assert is_truthy(None) is False


class TestParseCsvEnv:
    def test_empty_env(self, monkeypatch):
        monkeypatch.delenv("TEST_CSV", raising=False)
        assert parse_csv_env("TEST_CSV") == set()

    def test_blank_env(self, monkeypatch):
        monkeypatch.setenv("TEST_CSV", "  ")
        assert parse_csv_env("TEST_CSV") == set()

    def test_single_value(self, monkeypatch):
        monkeypatch.setenv("TEST_CSV", "alpha")
        assert parse_csv_env("TEST_CSV") == {"alpha"}

    def test_multiple_values(self, monkeypatch):
        monkeypatch.setenv("TEST_CSV", "alpha,beta,gamma")
        assert parse_csv_env("TEST_CSV") == {"alpha", "beta", "gamma"}

    def test_whitespace_stripping(self, monkeypatch):
        monkeypatch.setenv("TEST_CSV", " alpha , beta , gamma ")
        assert parse_csv_env("TEST_CSV") == {"alpha", "beta", "gamma"}

    def test_empty_items_skipped(self, monkeypatch):
        monkeypatch.setenv("TEST_CSV", "alpha,,beta,")
        assert parse_csv_env("TEST_CSV") == {"alpha", "beta"}


class TestShouldJoinQueryParam:
    def test_matching_param(self):
        param = {"in": "query", "schema": {"type": "array"}, "explode": False}
        assert should_join_query_param(param) is True

    def test_not_query(self):
        param = {"in": "path", "schema": {"type": "array"}, "explode": False}
        assert should_join_query_param(param) is False

    def test_not_array(self):
        param = {"in": "query", "schema": {"type": "string"}, "explode": False}
        assert should_join_query_param(param) is False

    def test_explode_true(self):
        param = {"in": "query", "schema": {"type": "array"}, "explode": True}
        assert should_join_query_param(param) is False

    def test_explode_missing(self):
        param = {"in": "query", "schema": {"type": "array"}}
        assert should_join_query_param(param) is False

    def test_empty_dict(self):
        assert should_join_query_param({}) is False


class TestCollectCommaParams:
    def test_from_components(self):
        spec = {
            "components": {
                "parameters": {
                    "fields": {
                        "name": "tweet.fields",
                        "in": "query",
                        "schema": {"type": "array"},
                        "explode": False,
                    }
                }
            }
        }
        assert collect_comma_params(spec) == {"tweet.fields"}

    def test_from_paths(self):
        spec = {
            "paths": {
                "/2/tweets": {
                    "get": {
                        "operationId": "getTweets",
                        "parameters": [
                            {
                                "name": "ids",
                                "in": "query",
                                "schema": {"type": "array"},
                                "explode": False,
                            }
                        ],
                    }
                }
            }
        }
        assert collect_comma_params(spec) == {"ids"}

    def test_skips_ref_params(self):
        spec = {
            "paths": {
                "/2/tweets": {
                    "get": {
                        "operationId": "getTweets",
                        "parameters": [
                            {"$ref": "#/components/parameters/fields"}
                        ],
                    }
                }
            }
        }
        assert collect_comma_params(spec) == set()

    def test_empty_spec(self):
        assert collect_comma_params({}) == set()


class TestShouldExcludeOperation:
    def test_webhooks_path(self):
        assert should_exclude_operation("/2/webhooks/config", {}) is True

    def test_stream_path(self):
        assert should_exclude_operation("/2/tweets/stream", {}) is True

    def test_stream_tag(self):
        assert should_exclude_operation("/2/tweets", {"tags": ["Stream"]}) is True

    def test_webhooks_tag(self):
        assert should_exclude_operation("/2/tweets", {"tags": ["Webhooks"]}) is True

    def test_streaming_flag(self):
        op = {"x-twitter-streaming": True}
        assert should_exclude_operation("/2/tweets", op) is True

    def test_normal_operation(self):
        op = {"tags": ["Posts"], "operationId": "createPosts"}
        assert should_exclude_operation("/2/tweets", op) is False

    def test_no_tags(self):
        assert should_exclude_operation("/2/tweets", {}) is False


class TestFilterOpenapiSpec:
    def _make_spec(self, paths):
        return {"paths": paths}

    def test_excludes_streaming(self):
        spec = self._make_spec({
            "/2/tweets": {"get": {"operationId": "getTweets", "tags": ["Posts"]}},
            "/2/tweets/stream": {"get": {"operationId": "streamTweets", "tags": ["Stream"]}},
        })
        filtered = filter_openapi_spec(spec)
        assert "/2/tweets" in filtered["paths"]
        assert "/2/tweets/stream" not in filtered["paths"]

    def test_allowlist(self, monkeypatch):
        monkeypatch.setenv("X_API_TOOL_ALLOWLIST", "getTweets")
        monkeypatch.delenv("X_API_TOOL_TAGS", raising=False)
        monkeypatch.delenv("X_API_TOOL_DENYLIST", raising=False)
        spec = self._make_spec({
            "/2/tweets": {"get": {"operationId": "getTweets", "tags": ["Posts"]}},
            "/2/users": {"get": {"operationId": "getUsers", "tags": ["Users"]}},
        })
        filtered = filter_openapi_spec(spec)
        assert "/2/tweets" in filtered["paths"]
        assert "/2/users" not in filtered["paths"]

    def test_denylist(self, monkeypatch):
        monkeypatch.setenv("X_API_TOOL_DENYLIST", "getUsers")
        monkeypatch.delenv("X_API_TOOL_ALLOWLIST", raising=False)
        monkeypatch.delenv("X_API_TOOL_TAGS", raising=False)
        spec = self._make_spec({
            "/2/tweets": {"get": {"operationId": "getTweets", "tags": ["Posts"]}},
            "/2/users": {"get": {"operationId": "getUsers", "tags": ["Users"]}},
        })
        filtered = filter_openapi_spec(spec)
        assert "/2/tweets" in filtered["paths"]
        assert "/2/users" not in filtered["paths"]

    def test_tag_filter(self, monkeypatch):
        monkeypatch.setenv("X_API_TOOL_TAGS", "Posts")
        monkeypatch.delenv("X_API_TOOL_ALLOWLIST", raising=False)
        monkeypatch.delenv("X_API_TOOL_DENYLIST", raising=False)
        spec = self._make_spec({
            "/2/tweets": {"get": {"operationId": "getTweets", "tags": ["Posts"]}},
            "/2/users": {"get": {"operationId": "getUsers", "tags": ["Users"]}},
        })
        filtered = filter_openapi_spec(spec)
        assert "/2/tweets" in filtered["paths"]
        assert "/2/users" not in filtered["paths"]

    def test_no_filters(self, monkeypatch):
        monkeypatch.delenv("X_API_TOOL_ALLOWLIST", raising=False)
        monkeypatch.delenv("X_API_TOOL_TAGS", raising=False)
        monkeypatch.delenv("X_API_TOOL_DENYLIST", raising=False)
        spec = self._make_spec({
            "/2/tweets": {"get": {"operationId": "getTweets", "tags": ["Posts"]}},
            "/2/users": {"get": {"operationId": "getUsers", "tags": ["Users"]}},
        })
        filtered = filter_openapi_spec(spec)
        assert "/2/tweets" in filtered["paths"]
        assert "/2/users" in filtered["paths"]

    def test_preserves_non_method_keys(self, monkeypatch):
        monkeypatch.delenv("X_API_TOOL_ALLOWLIST", raising=False)
        monkeypatch.delenv("X_API_TOOL_TAGS", raising=False)
        monkeypatch.delenv("X_API_TOOL_DENYLIST", raising=False)
        spec = self._make_spec({
            "/2/tweets": {
                "parameters": [{"name": "id"}],
                "get": {"operationId": "getTweets", "tags": ["Posts"]},
            },
        })
        filtered = filter_openapi_spec(spec)
        path_item = filtered["paths"]["/2/tweets"]
        assert "parameters" in path_item
        assert "get" in path_item
