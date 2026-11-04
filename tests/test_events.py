def test_requests_and_events_are_logged_once_per_line_without_file_handlers(client, caplog):
    caplog.set_level(logging.INFO, logger="lockerline")
    body = drop(client)
    client.post("/pickups", json={"code": body["code"]})

    messages = [
        record.getMessage()
        for record in caplog.records
        if record.name.startswith("lockerline")
    ]
    assert sum("method=POST path=/drops" in message for message in messages) == 1
    assert sum("method=POST path=/pickups" in message for message in messages) == 1

    for kind in ("dropped", "code_issued", "opened"):
        assert sum(f"event kind={kind} " in message for message in messages) == 1

    assert all("\n" not in message for message in messages)
    assert body["code"] not in "\n".join(messages)

    for name in ("lockerline", "lockerline.access", "lockerline.events"):
        logger = logging.getLogger(name)
        assert not any(
            isinstance(handler, logging.FileHandler)
            for handler in logger.handlers
        )