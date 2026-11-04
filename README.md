## Run with Docker

Build and start the app with Docker:

```bash
docker build -t lockerline .
# Quick run without persistent storage:
# docker run -p 8080:8080 lockerline
# Copy .env.example to .env and set CODE_HASH_KEY before the persistent run:
docker run -d --name lockerline -p 8080:8080 -v lockerline-data:/data --env-file .env lockerline
# Create a parcel and note the returned parcel_id and six-digit code:
curl -i -X POST http://127.0.0.1:8080/drops -H "Content-Type: application/json" -d '{"size_class":"M","flat":"302"}'
# Replace P001 with the parcel_id returned by the drop:
curl http://127.0.0.1:8080/parcels/P001
# Replace 482913 with the code returned by the drop:
curl -i -X POST http://127.0.0.1:8080/pickups -H "Content-Type: application/json" -d '{"code":"482913"}'

<!-- learntube:start -->
---

[![tests](https://github.com/ag7531601-sketch/lockerline-python/actions/workflows/tests.yml/badge.svg)](https://github.com/ag7531601-sketch/lockerline-python/actions/workflows/tests.yml)

### Progress

- [x] Ticket 1 · Forty-eight doors, and a wall you can look at
- [x] Ticket 2 · A courier asks for a door
- [x] Ticket 3 · The code that dies at midnight
- [x] Ticket 4 · Three ways to say no
- [x] Ticket 5 · The door opens, and the clock stops
- [x] Ticket 6 · A notebook nobody can rewrite
- [x] Ticket 7 · One file becomes an app
- [x] Ticket 8 · The rule table, and then the rule changes
- [x] Ticket 9 · It runs on a machine that isn't yours
- [x] Ticket 10 · It survives being switched off

Built by Avinash Gupta on [LearnTube Guided Projects](https://guidedprojects.learntube.ai).
<!-- learntube:end -->
