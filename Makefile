run:
	@echo "\e[34m[#] Killing old docker processes\e[0m"
	@docker-compose rm -fs || exit 1

	@echo "\e[34m[#] Building docker container\e[0m"
	@docker-compose up --build -d || exit 1

	@echo "\e[32m[#] Fastly-Tempo container is now running!\e[0m"