# Portable Digital Library Makefile

start:
	docker compose up -d

stop:
	docker compose down

backup:
	mkdir -p backups
	tar -czf backups/portable-library-$(shell date +%Y-%m-%d-%H%M).tar.gz docker-compose.yml .env Makefile README.md library/

restore:
	@echo "Manual restore: untar backup into project folder."

logs:
	docker compose logs -f

clean:
	docker compose down -v
	rm -rf portable-library/*/

.PHONY: start stop backup restore logs clean
delete the current files and fo