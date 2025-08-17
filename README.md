# Portable Digital Library

All-in-one, fully portable self-hosted library stack (books, audiobooks, downloads, automation). Entire system (configs + media + databases + compose) lives in this directory for simple tar backup & redeploy anywhere Docker runs.

## Stack Overview

Services included (all enabled by default):

- BookLore (modern book/comic manager) + MariaDB backend
- Book Downloader (search/request -> BookLore ingest)
- AudiobookShelf (audiobooks & podcasts)
- qBittorrent (download client)

All data/config/media are bind-mounted into subfolders here:

```
media/books/ (consolidated book library)
media/audiobooks/ (audiobook files)
media/podcasts/ (podcast files)
configs/ (service configurations)
data/ (databases, internal metadata)
downloads/ (incomplete, complete, watch)
ingest/booklore/ (BookLore BookDrop auto-import folder)
```

## Directory Structure

```
my-library/
├── .env                          # Environment variables
├── docker-compose.yml            # Service definitions
├── Makefile                      # Convenience commands
├── README.md                     # This file
├── SERVICE_CONFIGURATION_GUIDE.md # Service setup guide
└── library/                      # All data lives here
    ├── configs/                  # Service configurations
    │   ├── audiobookshelf/       # AudiobookShelf config
    │   ├── booklore/             # BookLore config
    │   └── qbittorrent/          # qBittorrent config
    ├── data/                     # Databases and metadata
    │   ├── audiobookshelf/       # AudiobookShelf metadata
    │   ├── booklore/             # BookLore app data
    │   └── mariadb/              # MariaDB database files
    ├── downloads/                # Download directories
    │   ├── complete/             # Completed downloads
    │   ├── incomplete/           # In-progress downloads
    │   └── watch/                # Watch folder for torrents
    ├── ingest/                   # Auto-import folders
    │   └── booklore/             # BookLore BookDrop folder
    └── media/                    # Media libraries
        ├── audiobooks/           # AudiobookShelf audiobooks
        ├── books/                # Consolidated book library
        └── podcasts/             # AudiobookShelf podcasts
```


## Quick Start

1. Copy `.env` and edit secrets:
   - Set `MYSQL_ROOT_PASSWORD` & `MYSQL_PASSWORD`
   - Adjust ports if needed
2. (Optional) Remove services you don't want from `docker-compose.yml`
3. Launch:

```bash
docker compose pull
docker compose up -d
````

4. Initial access:
   - BookLore: http://localhost:6060
   - Book Downloader: http://localhost:8084
   - AudiobookShelf: http://localhost:13378
   - qBittorrent UI: http://localhost:8080

## Adding Content

- Drop ebooks for BookLore into `ingest/booklore/`
- Place completed downloads (if external) into `downloads/complete/`
- Put audiobooks into `media/audiobooks/` (AudiobookShelf auto-detect)

## Auth & Integration Notes

- qBittorrent will print a temporary password in container logs first start (change in UI). If using a reverse proxy later, consider enabling authentication and TLS at the proxy.
- Book Downloader integrates directly with BookLore for seamless book ingestion.

## Backup & Restore

Single-file backup (while running is usually fine; for absolute consistency you can `docker compose down` first):

```bash
tar -czf portable-library-backup_$(date +%Y%m%d).tar.gz .
```

Restore on a new host:

```bash
tar -xzf portable-library-backup_YYYYMMDD.tar.gz
cd my-library
cp .env.example .env # if you kept an example, else edit existing .env
docker compose up -d
```

(No separate DB dump required—MariaDB and all SQLite / metadata live inside `data/` and `configs/`.)

## Updating

```bash
docker compose pull
docker compose up -d
```

(Images updated; bind-mounted data persists.)

### Verifying Services

Check container states:

```bash
docker compose ps
```

Tail logs for a specific service (e.g., BookLore) until you see startup complete:

```bash
docker compose logs -f booklore
```

MariaDB health should show `healthy`:

```bash
docker inspect -f '{{.State.Health.Status}}' mariadb
```

### File & Folder Permissions

All bind-mounted paths should be writable by the user ID in `.env` (`PUID`/`PGID`). If issues:

```bash
sudo chown -R $(id -u):$(id -g) configs data media downloads ingest bookdrop
```

### Ingestion Smoke Test

1. Place a test EPUB into `ingest/booklore/` – BookLore should import shortly.
2. For downloader workflow, request a book via Book Downloader UI and confirm file appears in BookLore library.

### Updating a Single Service

```bash
docker compose pull booklore
docker compose up -d booklore
```

### Stopping / Removing

```bash
docker compose down        # stop containers
docker compose down -v     # (CAUTION) also remove anonymous volumes if any
```

### Disk Usage Overview

```bash
du -sh media/* data/* configs/* 2>/dev/null | sort -h
```

### Health & Logs Batch Snapshot

```bash
docker compose ps --status running
docker compose logs --tail=50 --timestamps | grep -iE 'error|warn' || true
```

### Common Recovery Steps

- Stuck migrations (BookLore): restart `booklore` after confirming DB healthy.
- Corrupted MariaDB (rare): stop stack, back up `data/mariadb`, then remove `aria_log*` inside and restart.
- qBittorrent password lost: remove (or edit) `configs/qbittorrent/qBittorrent.conf` WebUI line and restart container to reset.

### Minimal Reverse Proxy Hint

If later fronted by Traefik/Caddy, add labels to each service with host rules based on `BASE_DOMAIN` and ensure WebSocket support for AudiobookShelf. Keep ports internal by removing host `ports:` mappings (switch to `expose:`) once proxy handles external access.

## Customization

- Disable a service: comment/remove its block in `docker-compose.yml`.
- Add profiles: attach `profiles: [name]` to services and run `docker compose --profile name up -d`.
- Reverse proxy: add labels (Traefik/Caddy) and ensure websockets for AudiobookShelf.

## Security TODO (Future)

- Move DB credentials to Docker secrets
- Add fail2ban / auth hardening via reverse proxy
- Optional Tor profile for Downloader (`docker-compose.tor.yml` variant not yet added)

## Troubleshooting

- Permissions: ensure host folders owned by PUID:PGID (`chown -R 1000:1000 .`).
- MariaDB not healthy: check `docker logs mariadb`; verify passwords match `.env`.
- qBittorrent WebUI password rotates: set a new one immediately after first login.

## License

Configuration authored for portability; underlying images retain their own licenses.
