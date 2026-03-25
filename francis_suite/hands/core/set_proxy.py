"""
hands/core/set_proxy.py

SetProxyHand implements <set-proxy> — probe URL, match body, rotate proxy pool.
See docs/decisions/ADR-004-set-proxy-design.md.
"""

from __future__ import annotations

import json
import random
import re
from pathlib import Path
from urllib.parse import quote

import httpx
from lxml import etree
from lxml import html as lhtml

from francis_suite.core.expressions import FrancisExpression
from francis_suite.core.registry import hand
from francis_suite.core.variables import FVariable, FNodeVariable, FListVariable
from francis_suite.hands.base import AbstractHand

VALID_CLIENTS = frozenset({"httpx"})
VALID_TYPES = frozenset({"local", "manual", "file", "api", "db"})
PROBE_METHODS = frozenset({"GET", "POST", "PUT", "DELETE", "PATCH", "HEAD"})
DEFAULT_POOL_SIZE = 10
DEFAULT_TIMEOUT_MS = 30_000


def _build_proxy_url(rec: dict) -> str:
    scheme = str(rec.get("scheme") or "http").lower().rstrip("/")
    if scheme.endswith(":"):
        scheme = scheme[:-1]
    host = str(rec["host"]).strip()
    port = int(rec["port"])
    user = str(rec.get("username") or rec.get("user") or "").strip()
    password = str(rec.get("password") or rec.get("pass") or "").strip()
    hostport = f"{host}:{port}"
    if user or password:
        u = quote(user, safe="")
        p = quote(password, safe="")
        return f"{scheme}://{u}:{p}@{hostport}"
    return f"{scheme}://{hostport}"


def _normalize_proxy_entry(obj: object, index: int) -> dict:
    if not isinstance(obj, dict):
        raise ValueError(
            f"Invalid proxy list: entry {index} is not a JSON object "
            f"(see ADR-004 — each item needs host, port)."
        )
    if "host" not in obj or "port" not in obj:
        raise ValueError(
            f"Invalid proxy list: entry {index} missing 'host' or 'port'."
        )
    return obj


def _parse_proxy_json_list(data: object) -> list[dict]:
    if isinstance(data, list):
        raw = data
    elif isinstance(data, dict):
        raw = data.get("proxies") or data.get("items")
        if raw is None:
            raise ValueError(
                "Invalid proxy list JSON: expected a top-level array or "
                "an object with 'proxies' or 'items' array."
            )
    else:
        raise ValueError("Invalid proxy list JSON: expected array or object.")
    if not isinstance(raw, list) or len(raw) == 0:
        raise ValueError("Invalid proxy list JSON: proxy array is empty.")
    return [_normalize_proxy_entry(item, i) for i, item in enumerate(raw)]


def _html_to_xml_string(body: str) -> str:
    if not body.strip():
        return ""
    try:
        etree.fromstring(body.encode("utf-8"))
        return body
    except etree.XMLSyntaxError:
        pass
    doc = lhtml.fromstring(body.encode("utf-8"))
    return etree.tostring(doc, pretty_print=True, encoding="unicode", method="xml")


def _xpath_hit(body: str, xpath: str, expected: str | None) -> bool:
    try:
        root = etree.fromstring(body.encode("utf-8"))
    except etree.XMLSyntaxError:
        root = lhtml.fromstring(body.encode("utf-8"))
    try:
        results = root.xpath(xpath)
    except etree.XPathEvalError as e:
        raise ValueError(f"set-proxy invalid match-xpath: {e}") from e
    if not results:
        return False
    if expected is None:
        return True
    first = results[0]
    if isinstance(first, str):
        text = first
    elif hasattr(first, "text_content"):
        text = first.text_content()
    else:
        text = str(first)
    return text.strip() == expected.strip()


def _validate_match_rules(params: dict[str, str]) -> None:
    regex = (params.get("match-regex") or "").strip()
    xpath = (params.get("match-xpath") or "").strip()
    expected = (params.get("match-expected-text") or "").strip()
    if expected and not xpath:
        raise ValueError(
            "set-proxy: match-expected-text requires match-xpath "
            "(see ADR-004)."
        )
    if not regex and not xpath:
        raise ValueError(
            "set-proxy requires at least one of match-regex or match-xpath "
            "(see ADR-004)."
        )


def _body_matches(match_params: dict[str, str], body: str) -> bool:
    regex = (match_params.get("match-regex") or "").strip()
    xpath = (match_params.get("match-xpath") or "").strip()
    expected_raw = match_params.get("match-expected-text")
    expected = (expected_raw or "").strip() if expected_raw is not None else ""

    ok_regex = False
    if regex:
        ok_regex = re.search(regex, body, re.DOTALL) is not None

    ok_xpath = False
    if xpath:
        ok_xpath = _xpath_hit(
            body, xpath, expected if expected else None
        )

    if regex and xpath:
        return ok_regex or ok_xpath
    if regex:
        return ok_regex
    return ok_xpath


@hand(tag="set-proxy")
class SetProxyHand(AbstractHand):
    """
    Configure session httpx proxy after probing a URL and matching the body.

    Returns FListVariable of three FNodeVariable items:
        1. \"true\" or \"false\" — probe succeeded for one proxy in the pool
        2. Last response body text (HTML or plain)
        3. Same body converted to well-formed XML when possible (else \"\")

    Attributes:
        client (required): \"httpx\" (other clients reserved for later).
        type (required): local | manual | file | api | db
        proxy-list-path (required when type=file): path to JSON proxy list
        timeout-ms (optional): probe timeout, default 30000
    """

    def execute(self) -> FVariable:
        try:
            return self._do_execute()
        finally:
            self.session.clear_httpx_block_after_set_proxy()

    def _do_execute(self) -> FVariable:
        engine = FrancisExpression(self.context)
        client = engine.resolve(self.require_attr("client")).strip().lower()
        if client not in VALID_CLIENTS:
            raise ValueError(
                f"set-proxy invalid client '{client}'. Supported: {', '.join(sorted(VALID_CLIENTS))}."
            )

        ptype = engine.resolve(self.require_attr("type")).strip().lower()
        if ptype not in VALID_TYPES:
            raise ValueError(
                f"set-proxy invalid type '{ptype}'. "
                f"Valid: {', '.join(sorted(VALID_TYPES))}."
            )

        if ptype == "db":
            raise ValueError(
                'set-proxy type="db" is not implemented yet. '
                "Use type=\"file\" or type=\"api\", or see "
                "docs/decisions/ADR-004-set-proxy-design.md."
            )

        timeout_ms = float(engine.resolve(self.attr("timeout-ms", str(DEFAULT_TIMEOUT_MS))))
        timeout_sec = max(timeout_ms / 1000.0, 0.001)

        proxy_params = self._collect_proxy_params(engine)
        probe_method, probe_headers, probe_data = self._collect_probe_http(engine)

        probe_url = (proxy_params.get("url") or "").strip()
        if not probe_url:
            raise ValueError(
                'set-proxy requires <proxy-param name="url"> for the probe URL.'
            )

        _validate_match_rules(proxy_params)

        pool = self._build_pool(ptype, engine, proxy_params, timeout_sec)

        pool_size = DEFAULT_POOL_SIZE
        if "pool-size" in proxy_params and str(proxy_params["pool-size"]).strip():
            try:
                pool_size = max(1, int(str(proxy_params["pool-size"]).strip()))
            except ValueError as e:
                raise ValueError("set-proxy pool-size must be a positive integer.") from e

        provider = (proxy_params.get("provider") or "").strip()
        if provider:
            pool = [p for p in pool if str(p.get("provider", "")).strip() == provider]
        if not pool:
            raise ValueError(
                "set-proxy: no proxies left after provider filter (or empty pool)."
            )

        pool = pool.copy()
        random.shuffle(pool)
        pool = pool[:pool_size]

        last_body = ""
        last_xml = ""

        for entry in pool:
            proxy_url: str | None
            if entry is None:
                self.session.set_httpx_proxy_url(None)
                proxy_url = None
            else:
                proxy_url = _build_proxy_url(entry)
                self.session.set_httpx_proxy_url(proxy_url)

            body = self._run_probe(
                probe_url, probe_method, probe_headers, probe_data, timeout_sec
            )
            last_body = body
            last_xml = _html_to_xml_string(body) if body.strip() else ""

            if _body_matches(proxy_params, body):
                return FListVariable(
                    [
                        FNodeVariable("true"),
                        FNodeVariable(last_body),
                        FNodeVariable(last_xml),
                    ]
                )

        self.session.set_httpx_proxy_url(None)
        return FListVariable(
            [
                FNodeVariable("false"),
                FNodeVariable(last_body),
                FNodeVariable(last_xml),
            ]
        )

    def _collect_proxy_params(self, engine: FrancisExpression) -> dict[str, str]:
        out: dict[str, str] = {}
        for child in self._node.children:
            if child.tag != "proxy-param":
                continue
            name = child.get_attr("name", "").strip()
            if not name:
                continue
            out[name] = engine.resolve(child.text or "")
        return out

    def _collect_probe_http(
        self, engine: FrancisExpression
    ) -> tuple[str, dict[str, str], dict[str, str]]:
        method = "GET"
        headers: dict[str, str] = {}
        data: dict[str, str] = {}

        for child in self._node.children:
            if child.tag == "set-proxy-method":
                raw = (child.text or "").strip()
                if raw:
                    method = engine.resolve(raw).upper()
            elif child.tag == "set-proxy-header":
                name = child.get_attr("name", "").strip()
                if name:
                    headers[name] = engine.resolve(child.text or "")
            elif child.tag == "set-proxy-http-param":
                name = child.get_attr("name", "").strip()
                if name:
                    data[name] = engine.resolve(child.text or "")

        if method not in PROBE_METHODS:
            raise ValueError(
                f"set-proxy invalid probe method '{method}'. "
                f"Valid: {', '.join(sorted(PROBE_METHODS))}."
            )
        return method, headers, data

    def _child_body(self, engine: FrancisExpression, tag: str) -> str:
        for child in self._node.children:
            if child.tag == tag:
                return engine.resolve(child.text or "").strip()
        return ""

    def _build_pool(
        self,
        ptype: str,
        engine: FrancisExpression,
        proxy_params: dict[str, str],
        timeout_sec: float,
    ) -> list[dict | None]:
        if ptype == "local":
            return [None]

        if ptype == "manual":
            host = self._child_body(engine, "proxy-host")
            port_s = self._child_body(engine, "proxy-port")
            if not host or not port_s:
                raise ValueError(
                    "set-proxy type=manual requires <proxy-host> and <proxy-port>."
                )
            try:
                port = int(port_s)
            except ValueError as e:
                raise ValueError("set-proxy proxy-port must be an integer.") from e
            user = self._child_body(engine, "proxy-username")
            password = self._child_body(engine, "proxy-password")
            return [
                {
                    "scheme": "http",
                    "host": host,
                    "port": port,
                    "username": user,
                    "password": password,
                }
            ]

        if ptype == "file":
            path_s = engine.resolve(self.require_attr("proxy-list-path"))
            path = Path(path_s)
            if not path.is_file():
                raise ValueError(f"set-proxy proxy-list-path not found: {path.as_posix()}")
            text = path.read_text(encoding="utf-8")
            try:
                data = json.loads(text)
            except json.JSONDecodeError as e:
                raise ValueError(
                    f"set-proxy invalid JSON in proxy-list-path: {e}"
                ) from e
            return _parse_proxy_json_list(data)

        if ptype == "api":
            list_url = (proxy_params.get("proxy-list-url") or "").strip()
            if not list_url:
                raise ValueError(
                    'set-proxy type=api requires <proxy-param name="proxy-list-url">.'
                )
            try:
                with httpx.Client(timeout=timeout_sec, follow_redirects=True) as client:
                    r = client.get(list_url)
                    r.raise_for_status()
                    data = r.json()
            except httpx.HTTPError as e:
                raise ValueError(f"set-proxy failed to fetch proxy list API: {e}") from e
            except json.JSONDecodeError as e:
                raise ValueError(
                    f"set-proxy proxy-list-url returned invalid JSON: {e}"
                ) from e
            return _parse_proxy_json_list(data)

        raise ValueError(f"set-proxy internal error: unhandled type {ptype!r}")

    def _run_probe(
        self,
        url: str,
        method: str,
        headers: dict[str, str],
        data: dict[str, str],
        timeout_sec: float,
    ) -> str:
        proxy = self.session.get_httpx_proxy_url()
        kw: dict = {
            "method": method,
            "url": url,
            "headers": headers or None,
            "timeout": timeout_sec,
            "follow_redirects": True,
        }
        if proxy:
            kw["proxy"] = proxy
        if method == "GET":
            kw["params"] = data or None
        else:
            kw["data"] = data or None
        try:
            r = httpx.request(**kw)
        except httpx.RequestError:
            self.session.record_httpx_response(None)
            return ""
        self.session.record_httpx_response(r)
        return r.text
