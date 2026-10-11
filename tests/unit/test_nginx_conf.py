"""Guards for docker/nginx.conf: the server must not log visitor addresses."""
import os
import re

CONF = os.path.join(os.path.dirname(__file__), "..", "..", "docker", "nginx.conf")


def conf_text():
    with open(CONF, encoding="utf-8") as f:
        # drop comments so words in explanations do not count
        return re.sub(r"#.*", "", f.read())


def test_access_log_is_off():
    assert re.search(r"^\s*access_log\s+off\s*;", conf_text(), re.M)


def test_error_log_does_not_record_missing_files():
    # "404 not found" is logged at level "error" with the client address
    assert re.search(r"^\s*error_log\s+\S+\s+(crit|alert|emerg)\s*;", conf_text(), re.M)


def test_client_address_is_never_used():
    text = conf_text()
    for variable in ("$remote_addr", "$http_x_forwarded_for", "$http_cf_connecting_ip", "$realip_remote_addr"):
        assert variable not in text
